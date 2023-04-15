import logging
import os
from typing import Optional

import numpy as np
import wx

from mlib.base.logger import MLogger
from mlib.base.math import MQuaternion, MVector3D
from mlib.service.form.base_panel import BasePanel
from mlib.service.base_worker import BaseWorker
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import BoneMorphOffset, Morph, MorphType, VertexMorphOffset
from mlib.vmd.vmd_collection import VmdMotion
from mlib.pmx.pmx_writer import PmxWriter
from service.form.panel.file_panel import FilePanel
from mlib.pmx.pmx_part import Bone
from mlib.base.exception import MApplicationException
from mlib.base.math import MVector4D
from mlib.pmx.pmx_part import MaterialMorphCalcMode, MaterialMorphOffset
from mlib.base.math import MMatrix4x4

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class LoadWorker(BaseWorker):
    def __init__(self, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.panel
        model: Optional[PmxModel] = None
        dress: Optional[PmxModel] = None
        motion: Optional[VmdMotion] = None
        is_model_change = False
        is_dress_change = False

        if file_panel.model_ctrl.valid() and not file_panel.model_ctrl.data:
            model = file_panel.model_ctrl.reader.read_by_filepath(file_panel.model_ctrl.path)

            self.valid_model(model, "人物")

            # 人物に材質透明モーフを入れる
            logger.info("人物モデル追加セットアップ：材質OFFモーフ追加")
            model = self.create_material_off_morphs(model)

            is_model_change = True
        elif file_panel.model_ctrl.data:
            model = file_panel.model_ctrl.data
        else:
            model = PmxModel()

        if file_panel.dress_ctrl.valid() and (is_model_change or not file_panel.dress_ctrl.data):
            dress = file_panel.dress_ctrl.reader.read_by_filepath(file_panel.dress_ctrl.path)

            self.valid_model(dress, "衣装")

            # ドレスに材質透明モーフを入れる
            logger.info("衣装モデル追加セットアップ：材質OFFモーフ追加")
            dress = self.create_material_off_morphs(dress)

            # ドレスに拡大縮小モーフを入れる
            logger.info("衣装モデル追加セットアップ：スケールモーフ追加")
            dress = self.create_dress_scale_morphs(model, dress)

            is_dress_change = True
        elif file_panel.dress_ctrl.data:
            dress = file_panel.dress_ctrl.data
        else:
            dress = PmxModel()

        if file_panel.motion_ctrl.valid() and (not file_panel.motion_ctrl.data or is_model_change or is_dress_change):
            motion = file_panel.motion_ctrl.reader.read_by_filepath(file_panel.motion_ctrl.path)
        elif file_panel.motion_ctrl.data:
            motion = file_panel.motion_ctrl.data
        else:
            motion = VmdMotion()

        if logger.total_level <= logging.DEBUG:
            # デバッグモードの時だけ変形モーフ付き衣装モデルデータ保存
            from datetime import datetime

            out_path = os.path.join(os.path.dirname(file_panel.output_pmx_ctrl.path), f"{dress.name}_{datetime.now():%Y%m%d_%H%M%S}.pmx")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            PmxWriter(dress, out_path, include_system=True).save()
            logger.info(f"変形モーフ付き衣装モデル出力: {out_path}")

        self.result_data = (model, dress, motion)

    def valid_model(self, model: PmxModel, type_name: str) -> None:
        """フィッティングに最低限必要なボーンで不足しているボーンリストを取得する"""
        required_bone_names = {"センター", "上半身", "下半身", "首", "頭", "右肩", "左肩", "右手首", "左手首", "右足", "左足", "右足首", "左足首"}
        missing_bone_names = sorted(list(required_bone_names - set(model.bones.names)))
        if missing_bone_names:
            raise MApplicationException(
                type_name + "モデルのフィッティングに必要なボーンが不足しています。\n不足ボーン: {b}",
                b=", ".join(missing_bone_names),
            )

    def create_material_off_morphs(self, model: PmxModel) -> PmxModel:
        """材質OFFモーフ追加"""
        # vertices_by_material = model.get_vertices_by_material()
        for material in model.materials:
            morph = Morph(name=f"{material.name}TR")
            morph.is_system = True
            morph.morph_type = MorphType.MATERIAL
            offsets: list[MaterialMorphOffset] = [
                MaterialMorphOffset(
                    material.index,
                    MaterialMorphCalcMode.ADDITION,
                    MVector4D(-1.0, -1.0, -1.0, -1.0),
                    MVector3D(-1.0, -1.0, -1.0),
                    -1.0,
                    MVector3D(-1.0, -1.0, -1.0),
                    MVector4D(-1.0, -1.0, -1.0, -1.0),
                    -1.0,
                    MVector4D(-1.0, -1.0, -1.0, -1.0),
                    MVector4D(-1.0, -1.0, -1.0, -1.0),
                    MVector4D(-1.0, -1.0, -1.0, -1.0),
                )
            ]
            morph.offsets = offsets
            model.morphs.append(morph)
        return model

    def create_dress_scale_morphs(self, model: PmxModel, dress: PmxModel) -> PmxModel:
        """衣装フィッティング用ボーンモーフを作成"""
        bone_scale_morph = Morph(name="BoneScale")
        bone_scale_morph.is_system = True
        bone_scale_morph.morph_type = MorphType.BONE
        bone_scale_offsets: dict[int, BoneMorphOffset] = {}
        model_bone_positions: dict[int, MVector3D] = {-1: MVector3D()}
        dress_fit_qqs: dict[int, MQuaternion] = {}

        for dress_bone in dress.bones:
            _, model_bone_positions = self.get_model_position(model, dress, dress_bone, model_bone_positions)

        for dress_bone in dress.bones:
            if dress_bone.name not in model.bones:
                continue
            model_start_bone_position = model_bone_positions[dress_bone.far_parent_index]
            model_end_bone_position = model_bone_positions[dress_bone.index]

            model_x_direction = (model_end_bone_position - model_start_bone_position).normalized()
            model_y_direction = MVector3D(0, 0, -1) if np.isclose(abs(model_x_direction.x), 1) else MVector3D(1, 0, 0)
            model_z_direction = model_x_direction.cross(model_y_direction)
            model_slope_qq = MQuaternion.from_direction(model_z_direction, model_x_direction)

            dress_x_direction = (dress_bone.position - dress.bones[dress_bone.far_parent_index].position).normalized() or model_x_direction.copy()
            dress_y_direction = MVector3D(0, 0, -1) if np.isclose(abs(dress_x_direction.x), 1) else MVector3D(1, 0, 0)
            dress_z_direction = dress_x_direction.cross(dress_y_direction)
            dress_slope_qq = MQuaternion.from_direction(dress_z_direction, dress_x_direction)

            # 衣装のボーン角度をモデルのボーン角度に合わせる
            dress_fit_qqs[dress_bone.index] = model_slope_qq * dress_slope_qq.inverse()

        leg_bone_names: list[str] = []
        for dress_bone in dress.bones:
            bone_tree = dress.bone_trees[dress_bone.name]
            # 足系ボーンが含まれている場合
            tree_leg_bone_names = [bname for bname in bone_tree.names if bname in ["右足IK親", "右足ＩＫ", "右ひざ", "右足先EX", "左足IK親", "左足ＩＫ", "左ひざ", "左足先EX"]]
            for lname in tree_leg_bone_names:
                for filtered_lname in dress.bone_trees[dress_bone.name].filter(lname, dress_bone.name).names:
                    # 足系ボーンを追加する
                    if filtered_lname not in leg_bone_names:
                        leg_bone_names.append(filtered_lname)

        for dress_bone in dress.bones:
            if dress_bone.name in leg_bone_names:
                # 足の末端系のボーンがある場合、相対位置の計算からは除外
                continue
            dress_bone_tree = dress.bone_trees[dress_bone.name]
            dress_fit_qq = MQuaternion()
            for tree_bone_name in reversed(dress_bone_tree.names):
                tree_bone = dress.bones[tree_bone_name]
                if tree_bone.name == dress_bone.name:
                    # 初回はそのまま設定
                    dress_fit_qq = dress_fit_qqs.get(tree_bone.index, MQuaternion())
                else:
                    # 自分より親は逆回転させる
                    dress_fit_qq *= dress_fit_qqs.get(tree_bone.index, MQuaternion()).inverse()

            if dress_bone.index not in bone_scale_offsets:
                bone_scale_offsets[dress_bone.index] = BoneMorphOffset(dress_bone.index, MVector3D(), dress_fit_qq)

            dress_mat = MMatrix4x4()
            for tree_bone_name in dress_bone_tree.names[:-1]:
                tree_bone = dress.bones[tree_bone_name]

                tree_model_parent_pos = model_bone_positions[tree_bone.parent_index]
                tree_model_pos = model_bone_positions[tree_bone.index]

                # 角度をモデルのボーンに合わせる
                dress_fit_qq = dress_fit_qqs.get(tree_bone.index, MQuaternion())
                dress_mat.rotate(dress_fit_qq)

                local_tree_model_parent_pos = dress_mat.inverse() * tree_model_parent_pos
                local_tree_model_pos = dress_mat.inverse() * tree_model_pos
                local_tree_model_offset = local_tree_model_pos - local_tree_model_parent_pos

                tree_dress_parent_pos = dress.bones[tree_bone.parent_index].position
                tree_dress_pos = tree_bone.position

                local_tree_dress_parent_pos = dress_mat.inverse() * tree_dress_parent_pos
                local_tree_dress_pos = dress_mat.inverse() * tree_dress_pos
                local_tree_dress_offset = local_tree_dress_pos - local_tree_dress_parent_pos

                # モデルのボーンに合わせて移動させる
                dress_mat.translate(local_tree_model_pos)

            # 末端（計算対象）ボーンの位置
            model_parent_pos = model_bone_positions[dress_bone.parent_index]
            model_pos = model_bone_positions[dress_bone.index]

            # 角度をモデルのボーンに合わせる
            dress_fit_qq = dress_fit_qqs.get(dress_bone.index, MQuaternion())
            dress_mat.rotate(dress_fit_qq)

            model_parent_relative_pos = model_pos - model_parent_pos
            local_model_parent_pos = dress_mat.inverse() * model_parent_pos
            local_model_pos = dress_mat.inverse() * model_pos
            local_model_offset = local_model_pos - local_model_parent_pos

            dress_parent_pos = dress.bones[dress_bone.parent_index].position
            dress_pos = dress_bone.position

            dress_parent_relative_pos = dress_pos - dress_parent_pos
            dress_mat_pos = dress_mat * dress_parent_relative_pos
            local_dress_parent_pos = dress_mat.inverse() * dress_parent_pos
            local_dress_pos = dress_mat.inverse() * dress_pos
            local_dress_offset = local_dress_pos - local_dress_parent_pos

            # モデルのボーンに合わせて移動させる
            local_offset_pos = local_model_pos - dress_parent_relative_pos

            if dress_bone.index not in bone_scale_offsets:
                bone_scale_offsets[dress_bone.index] = BoneMorphOffset(dress_bone.index, local_offset_pos, MQuaternion())
            else:
                bone_scale_offsets[dress_bone.index].position = local_offset_pos

        bone_scale_morph.offsets = list(bone_scale_offsets.values())
        dress.morphs.append(bone_scale_morph)

        return dress

    def get_model_position(self, model: PmxModel, dress: PmxModel, bone: Bone, model_bone_positions: dict[int, MVector3D]):
        """衣装モデルのボーン名に相当する人物モデルのボーン位置を取得する"""
        if bone.name in model.bones:
            model_bone_positions[bone.index] = model.bones[bone.name].position
            return model.bones[bone.name].position, model_bone_positions
        if bone.name in model_bone_positions:
            return model_bone_positions[bone.index], model_bone_positions
        # まだ仮登録されていない場合、計算する
        parent_name = self.get_parent_name(model, dress, bone)
        child_names = self.get_child_names(model, dress, bone)
        if not child_names:
            # 子どもが居ない場合、親ボーンの子どもから求め直す
            child_names = [b.name for b in model.bones if model.bones[parent_name].index == b.parent_index and b.name in dress.bones]
        if parent_name and child_names:
            dress_child_mean_pos = MVector3D(*np.mean([dress.bones[cname].position.vector for cname in child_names], axis=0))
            model_child_mean_pos = MVector3D(*np.mean([model.bones[cname].position.vector for cname in child_names], axis=0))
            # 人物にない衣装ボーンの縮尺
            dress_wrap_scale = (bone.position - dress.bones[parent_name].position).abs() / (
                (dress_child_mean_pos - bone.position).abs() + (bone.position - dress.bones[parent_name].position).abs()
            )
            # 人物モデルに縮尺を当てはめる
            model_fake_bone_position = model.bones[parent_name].position + (model_child_mean_pos - model.bones[parent_name].position) * dress_wrap_scale
            model_bone_positions[bone.index] = model_fake_bone_position

            return model_fake_bone_position, model_bone_positions
        if parent_name and not child_names:
            # 同じボーンがまったく人物モデルに無い場合、その親の縮尺を反映させる
            parent_parent_name = self.get_parent_name(model, dress, dress.bones[parent_name])
            model_parent_parent_pos = model_bone_positions.get(dress.bones[parent_parent_name].index, MVector3D())
            model_parent_pos = model_bone_positions.get(dress.bones[parent_name].index, MVector3D())
            dress_parent_parent_pos = dress.bones[parent_parent_name].position
            dress_parent_pos = dress.bones[parent_name].position
            model_fake_bone_position = model_parent_pos + ((bone.position - dress_parent_pos) / (dress_parent_pos - dress_parent_parent_pos)) * (
                model_parent_pos - model_parent_parent_pos
            )
            model_bone_positions[bone.index] = model_fake_bone_position

            return model_fake_bone_position, model_bone_positions

        return MVector3D(), model_bone_positions

    def create_dress_scale_morphs2(self, model: PmxModel, dress: PmxModel) -> PmxModel:
        # ウェイト頂点の法線に基づいたスケールを取得
        weighted_vertex_scale = dress.get_weighted_vertex_scale()

        # 変形用スケールモーフを追加
        bone_scale_morph = Morph(name="BoneScale")
        bone_scale_morph.is_system = True
        bone_scale_morph.morph_type = MorphType.BONE
        bone_scale_offsets: list[BoneMorphOffset] = []
        model_fake_bone_positions: dict[int, MVector3D] = {}

        for bone in dress.bones:
            if 0 == bone.index and 0 > bone.parent_index:
                # ルートで親がない場合、グローバル座標の差分を取る
                bone_scale = model.bones[0].position - bone.position
                bone_scale_offsets.append(BoneMorphOffset(bone.index, bone_scale, MQuaternion()))
            else:
                if bone.name in model.bones and dress.bones[bone.parent_index].name == model.bones[model.bones[bone.name].parent_index].name:
                    # 自身と同じボーンで同じ親子関係の場合、親ボーンとのスケールモーフを追加
                    bone_scale = model.bones[bone.name].parent_relative_position - bone.parent_relative_position
                    bone_scale_offsets.append(BoneMorphOffset(bone.index, bone_scale, MQuaternion()))
                elif bone.name in model.bones and bone.parent_index in model_fake_bone_positions:
                    # 同じボーンがモデル側にある場合（親ボーンがない場合）、モデル側の仮ボーン位置で計算する
                    model_parent_fake_bone_position = model_fake_bone_positions[bone.parent_index]
                    bone_scale = (model.bones[bone.name].position - model_parent_fake_bone_position) - bone.parent_relative_position
                    bone_scale_offsets.append(BoneMorphOffset(bone.index, bone_scale, MQuaternion()))
                else:
                    # 同じボーンがモデル側に無い場合、相対位置で求める
                    parent_name = self.get_parent_name(model, dress, bone)
                    child_names = self.get_child_names(model, dress, bone)
                    if parent_name and child_names:
                        dress_child_mean_pos = MVector3D(*np.mean([dress.bones[cname].position.vector for cname in child_names], axis=0))
                        model_child_mean_pos = MVector3D(*np.mean([model.bones[cname].position.vector for cname in child_names], axis=0))
                        # 人物にない衣装ボーンの縮尺
                        dress_wrap_scale = (bone.position - dress.bones[parent_name].position) / (dress_child_mean_pos - dress.bones[parent_name].position)
                        # 人物モデルに縮尺を当てはめる
                        model_fake_bone_position = (
                            model.bones[parent_name].position + (model_child_mean_pos - model.bones[parent_name].position) * dress_wrap_scale
                        )
                        bone_scale = (model_fake_bone_position - model.bones[parent_name].position) - bone.parent_relative_position
                        bone_scale_offsets.append(BoneMorphOffset(bone.index, bone_scale, MQuaternion()))
                        model_fake_bone_positions[bone.index] = model_fake_bone_position

            for axis in ["X", "Y", "Z"]:
                scale_morph = Morph(name=f"{bone.name}S{axis}")
                scale_morph.is_system = True
                scale_morph.morph_type = MorphType.VERTEX
                offsets: list[VertexMorphOffset] = []
                bone_weighted_vertices: dict[int, MVector3D] = weighted_vertex_scale.get(bone.index, {})
                for vertex_index, scale in bone_weighted_vertices.items():
                    axis_scale = MVector3D()
                    match axis:
                        case "X":
                            axis_scale.x = scale.x
                        case "Y":
                            axis_scale.y = scale.y
                        case "Z":
                            axis_scale.z = scale.z
                    offsets.append(VertexMorphOffset(vertex_index=vertex_index, position_offset=axis_scale))
                if offsets:
                    scale_morph.offsets = offsets
                    dress.morphs.append(scale_morph)

            logger.count(
                "衣装モデル追加セットアップ：スケールモーフ追加",
                index=bone.index,
                total_index_count=len(dress.bones),
                display_block=100,
            )

        bone_scale_morph.offsets = bone_scale_offsets
        dress.morphs.append(bone_scale_morph)

        return dress

    def get_parent_name(self, model: PmxModel, dress: PmxModel, bone: Bone) -> str:
        if bone.parent_index < 0:
            # ルートはスルー
            return ""
        # 親ボーンがモデル側にもあればそのまま返す
        if dress.bones[bone.parent_index].name in model.bones:
            return dress.bones[bone.parent_index].name
        # なければ遡る
        return self.get_parent_name(model, dress, dress.bones[bone.parent_index])

    def get_child_names(self, model: PmxModel, dress: PmxModel, bone: Bone) -> list[str]:
        child_names: list[str] = []
        # 子ボーンリストを取得する
        for bname in dress.bones.names:
            if dress.bones[bname].parent_index == bone.index and bname in model.bones:
                child_names.append(bname)
        # なければ終了
        return child_names
