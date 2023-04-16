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

logger = MLogger(os.path.basename(__file__), level=1)
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
            logger.debug(f"変形モーフ付き衣装モデル出力: {out_path}")

        self.result_data = (model, dress, motion)

    def valid_model(self, model: PmxModel, type_name: str) -> None:
        """フィッティングに最低限必要なボーンで不足しているボーンリストを取得する"""
        required_bone_names = {
            "センター",
            "上半身",
            "下半身",
        }
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

        leg_bone_names: list[str] = []
        for dress_bone in dress.bones:
            bone_tree = dress.bone_trees[dress_bone.name]
            # 足系ボーンの除外起点が含まれている場合
            tree_leg_bone_names = [bname for bname in bone_tree.names if bname in ["右足IK親", "右足ＩＫ", "右ひざ", "右足D", "左足IK親", "左足ＩＫ", "左ひざ", "左足D"]]
            for lname in tree_leg_bone_names:
                for filtered_lname in dress.bone_trees[dress_bone.name].filter(lname, dress_bone.name).names:
                    # 足系ボーンを追加する
                    if filtered_lname not in leg_bone_names:
                        leg_bone_names.append(filtered_lname)

        for dress_bone in dress.bones:
            _, model_bone_positions = self.get_model_position(model, dress, dress_bone, model_bone_positions)

        for dress_bone in dress.bones:
            if dress_bone.name not in model.bones:
                continue

            model_start_bone_position = model_bone_positions[dress_bone.far_parent_index]
            model_end_bone_position = model_bone_positions[dress_bone.index]

            if (
                np.isclose(np.abs(model_end_bone_position.vector), 0, atol=0.01, rtol=0.01).any()
                or np.isclose(np.abs(dress_bone.position.vector), 0, atol=0.01, rtol=0.01).any()
            ):
                # ほぼ原点の場合、角度はなし
                dress_fit_qqs[dress_bone.index] = MQuaternion()
                continue

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

        for dress_bone in dress.bones:
            if dress_bone.name in leg_bone_names:
                # 足の末端系のボーンがある場合、相対位置の計算からは除外
                continue
            if not dress.bone_trees.is_in_standard(dress_bone.name):
                # 準標準ボーンに含まれない場合、相対位置計算除外
                continue
            if dress_bone.index in bone_scale_offsets:
                # 計算済みはスルー
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

        dress_fit_mats: dict[int, MMatrix4x4] = {-1: MMatrix4x4()}
        for dress_bone_tree in dress.bone_trees:
            if not dress_bone_tree.last_name:
                continue

            dress_bone = dress.bones[dress_bone_tree.last_name]

            if dress_bone.name in leg_bone_names:
                # 足の末端系のボーンがある場合、相対位置の計算からは除外
                continue
            if not dress.bone_trees.is_in_standard(dress_bone.name):
                # 準標準ボーンに含まれない場合、相対位置計算除外
                continue

            dress_mat = MMatrix4x4()

            if dress_bone.parent_index in dress_fit_mats:
                # 既に計算済みの場合、行列を保持して次へ
                dress_mat = dress_fit_mats[dress_bone.parent_index].copy()
            else:
                # 未計算の場合、末端までのボーン変形を計算する
                for tree_bone_name in dress_bone_tree.names[:-1]:
                    tree_bone = dress.bones[tree_bone_name]

                    tree_model_pos = model_bone_positions[tree_bone.index]

                    # 角度をモデルのボーンに合わせる
                    dress_fit_qq = dress_fit_qqs.get(tree_bone.index, MQuaternion())
                    dress_mat.rotate(dress_fit_qq)

                    local_tree_model_pos = dress_mat.inverse() * tree_model_pos

                    # モデルのボーンに合わせて移動させる
                    dress_mat.translate(local_tree_model_pos)

            # 末端（計算対象）ボーンの位置
            model_pos = model_bone_positions[dress_bone.index]

            # 角度をモデルのボーンに合わせる
            dress_fit_qq = dress_fit_qqs.get(dress_bone.index, MQuaternion())
            dress_mat.rotate(dress_fit_qq)

            # 合わせたいボーンの位置
            dress_fit_pos = dress_mat.inverse() * model_pos

            # モデルのボーンに合わせて移動させる
            dress_local_offset_pos = dress_fit_pos - dress_bone.parent_relative_position

            if dress_bone.index not in bone_scale_offsets:
                bone_scale_offsets[dress_bone.index] = BoneMorphOffset(dress_bone.index, dress_local_offset_pos, MQuaternion())
            else:
                bone_scale_offsets[dress_bone.index].position = dress_local_offset_pos

            dress_mat.translate(dress_fit_pos)

            # 行列を保存
            dress_fit_mats[dress_bone.index] = dress_mat.copy()

        # ひざと足首の調整
        for leg_bone_name, knee_bone_name, ankle_bone_name, leg_ik_bone_name, toe_ik_bone_name, leg_ik_parent_bone_name, ex_bone_name in [
            ("右足", "右ひざ", "右足首", "右足ＩＫ", "右つま先ＩＫ", "右足IK親", "右足先EX"),
            ("左足", "左ひざ", "左足首", "左足ＩＫ", "左つま先ＩＫ", "左足IK親", "左足先EX"),
        ]:
            if (
                leg_bone_name in dress.bones
                and knee_bone_name in dress.bones
                and ankle_bone_name in dress.bones
                and leg_ik_bone_name in dress.bones
                and toe_ik_bone_name in dress.bones
                and dress.bones[leg_ik_bone_name].ik
                and dress.bones[toe_ik_bone_name].ik
            ):
                # 足位置は揃ってるはず
                model_leg_pos = model_bone_positions[dress.bones[leg_bone_name].index]
                dress_leg_mat = dress_fit_mats[dress.bones[leg_bone_name].index]

                # ひざ
                model_knee_pos = model_bone_positions[dress.bones[knee_bone_name].index]

                # 足首
                model_ankle_pos = model_bone_positions[dress.bones[ankle_bone_name].index]
                dress_ankle_original_pos = dress.bones[ankle_bone_name].position
                dress_ankle_scale_pos: MVector3D = dress_leg_mat * (dress.bones[ankle_bone_name].position - dress.bones[leg_bone_name].position)

                # 踵
                model_sole_fit_pos = MVector3D(model_ankle_pos.x, 0, model_ankle_pos.z)
                dress_sole_scale_pos: MVector3D = dress_leg_mat * (
                    MVector3D(dress_ankle_scale_pos.x, 0, dress_ankle_scale_pos.z) - dress.bones[leg_bone_name].position
                )
                dress_sole_fit_pos = MVector3D(dress_sole_scale_pos.x, 0, dress_sole_scale_pos.z)

                # つま先
                model_toe_pos = model.bones[model.bones[toe_ik_bone_name].ik.bone_index].position
                model_toe_fit_pos = MVector3D(model_toe_pos.x, 0, model_toe_pos.z)
                dress_toe_original_pos: MVector3D = dress.bones[dress.bones[toe_ik_bone_name].ik.bone_index].position
                dress_toe_scale_pos: MVector3D = dress_leg_mat * (
                    dress.bones[dress.bones[toe_ik_bone_name].ik.bone_index].position - dress.bones[leg_bone_name].position
                )

                # 足底の長さの縮尺で靴のサイズを調整
                sole_scale = (model_toe_fit_pos - model_sole_fit_pos).length() / (
                    MVector3D(dress_toe_scale_pos.x, 0, dress_toe_scale_pos.z) - dress_sole_fit_pos
                ).length()

                # ひざ
                model_knee_scale = (model_sole_fit_pos - model_knee_pos) / ((model_sole_fit_pos - model_knee_pos) + (model_knee_pos - model_leg_pos))
                dress_knee_fit_pos = model_sole_fit_pos - ((model_sole_fit_pos - model_knee_pos) + (model_knee_pos - model_leg_pos)) * model_knee_scale
                local_dress_knee_pos = dress_leg_mat.inverse() * dress_knee_fit_pos
                global_dress_knee_scale_pos = dress_leg_mat * (dress.bones[knee_bone_name].position - dress.bones[leg_bone_name].position)

                local_knee_offset_pos = dress_knee_fit_pos - global_dress_knee_scale_pos
                bone_scale_offsets[dress.bones[knee_bone_name].index] = BoneMorphOffset(dress.bones[knee_bone_name].index, local_knee_offset_pos, MQuaternion())

                dress_knee_mat = dress_leg_mat.copy()
                dress_knee_mat.translate(local_dress_knee_pos)
                dress_fit_mats[dress.bones[knee_bone_name].index] = dress_knee_mat

                # 足首
                dress_ankle_scale_pos = dress_knee_mat * (dress.bones[ankle_bone_name].position - dress.bones[knee_bone_name].position)
                dress_ankle_fit_pos = MVector3D(model_ankle_pos.x, dress.bones[ankle_bone_name].position.y * sole_scale, model_ankle_pos.z)
                local_dress_ankle_pos = dress_knee_mat.inverse() * dress_ankle_fit_pos
                global_dress_ankle_scale_pos = dress_knee_mat * (dress.bones[ankle_bone_name].position - dress.bones[knee_bone_name].position)

                local_ankle_offset_pos = dress_ankle_fit_pos - global_dress_ankle_scale_pos
                bone_scale_offsets[dress.bones[ankle_bone_name].index] = BoneMorphOffset(
                    dress.bones[ankle_bone_name].index, local_ankle_offset_pos, MQuaternion()
                )

                dress_ankle_mat = dress_knee_mat.copy()
                dress_ankle_mat.translate(local_dress_ankle_pos)
                dress_fit_mats[dress.bones[ankle_bone_name].index] = dress_ankle_mat

                # つま先
                toe_bone_name = dress.bones[dress.bones[toe_ik_bone_name].ik.bone_index].name
                dress_toe_scale_pos = dress_ankle_mat * (dress.bones[toe_bone_name].position - dress.bones[ankle_bone_name].position)
                dress_toe_fit_pos = MVector3D(model_toe_pos.x, dress.bones[toe_bone_name].position.y * sole_scale, model_toe_pos.z)
                local_dress_toe_pos = dress_ankle_mat.inverse() * dress_toe_fit_pos
                global_dress_toe_scale_pos = dress_ankle_mat * (dress.bones[toe_bone_name].position - dress.bones[ankle_bone_name].position)

                local_toe_offset_pos = dress_toe_fit_pos - global_dress_toe_scale_pos
                bone_scale_offsets[dress.bones[toe_bone_name].index] = BoneMorphOffset(dress.bones[toe_bone_name].index, local_toe_offset_pos, MQuaternion())

                dress_toe_mat = dress_ankle_mat.copy()
                dress_toe_mat.translate(local_dress_toe_pos)
                dress_fit_mats[dress.bones[toe_bone_name].index] = dress_toe_mat

                # IK親
                if leg_ik_parent_bone_name in dress.bones:
                    leg_ik_parent_mat = dress_fit_mats[dress.bones[leg_ik_parent_bone_name].parent_index].copy()

                    leg_ik_parent_bone_index = dress.bones[leg_ik_parent_bone_name].index
                    leg_ik_parent_fit_pos = MVector3D(dress_ankle_fit_pos.x, 0, dress_ankle_fit_pos.z)
                    global_dress_leg_ik_parent_scale_pos = leg_ik_parent_mat * (
                        dress.bones[leg_ik_parent_bone_name].position - dress.bones[dress.bones[leg_ik_parent_bone_name].parent_index].position
                    )

                    local_leg_ik_parent_pos = leg_ik_parent_mat.inverse() * leg_ik_parent_fit_pos
                    local_leg_ik_parent_offset_pos = leg_ik_parent_fit_pos - global_dress_leg_ik_parent_scale_pos
                    bone_scale_offsets[leg_ik_parent_bone_index] = BoneMorphOffset(leg_ik_parent_bone_index, local_leg_ik_parent_offset_pos, MQuaternion())

                    leg_ik_parent_mat.translate(local_leg_ik_parent_pos)
                    dress_fit_mats[leg_ik_parent_bone_index] = leg_ik_parent_mat
                else:
                    # IK親が無い場合、親ボーンの位置を親とする
                    leg_ik_parent_bone_index = dress.bones[leg_ik_bone_name].parent_index
                    leg_ik_parent_mat = dress_fit_mats[leg_ik_parent_bone_index]
                    leg_ik_parent_fit_pos = dress.bones[leg_ik_parent_bone_index].position

                # 足ＩＫ
                local_dress_leg_ik_fit_pos = leg_ik_parent_mat.inverse() * dress_ankle_fit_pos
                global_dress_leg_ik_scale_pos = leg_ik_parent_mat * (dress.bones[leg_ik_bone_name].position - dress.bones[leg_ik_parent_bone_index].position)
                local_leg_ik_offset_pos = dress_ankle_fit_pos - global_dress_leg_ik_scale_pos

                bone_scale_offsets[dress.bones[leg_ik_bone_name].index] = BoneMorphOffset(
                    dress.bones[leg_ik_bone_name].index, local_leg_ik_offset_pos, MQuaternion()
                )

                leg_ik_mat = leg_ik_parent_mat.copy()
                leg_ik_mat.translate(local_dress_leg_ik_fit_pos)
                dress_fit_mats[dress.bones[leg_ik_bone_name].index] = leg_ik_mat

                # つま先ＩＫ
                local_dress_toe_ik_fit_pos = leg_ik_mat.inverse() * dress_toe_fit_pos
                global_dress_toe_ik_scale_pos = leg_ik_mat * (dress.bones[toe_ik_bone_name].position - dress.bones[leg_ik_bone_name].position)
                local_toe_ik_offset_pos = dress_toe_fit_pos - global_dress_toe_ik_scale_pos

                bone_scale_offsets[dress.bones[toe_ik_bone_name].index] = BoneMorphOffset(
                    dress.bones[toe_ik_bone_name].index, local_toe_ik_offset_pos, MQuaternion()
                )

                toe_ik_mat = leg_ik_mat.copy()
                toe_ik_mat.translate(local_dress_toe_ik_fit_pos)
                dress_fit_mats[dress.bones[toe_ik_bone_name].index] = toe_ik_mat

                # 足D
                if f"{leg_bone_name}D" in dress.bones:
                    dress_leg_d_bone_index = dress.bones[f"{leg_bone_name}D"].index
                    bone_scale_offsets[dress_leg_d_bone_index] = BoneMorphOffset(
                        dress_leg_d_bone_index,
                        bone_scale_offsets[dress.bones[leg_bone_name].index].position,
                        bone_scale_offsets[dress.bones[leg_bone_name].index].rotation.qq,
                    )
                    dress_fit_mats[dress_leg_d_bone_index] = dress_leg_mat.copy()

                # ひざD
                if f"{knee_bone_name}D" in dress.bones:
                    dress_knee_d_bone_index = dress.bones[f"{knee_bone_name}D"].index
                    bone_scale_offsets[dress_knee_d_bone_index] = BoneMorphOffset(
                        dress_knee_d_bone_index,
                        bone_scale_offsets[dress.bones[knee_bone_name].index].position,
                        bone_scale_offsets[dress.bones[knee_bone_name].index].rotation.qq,
                    )
                    dress_fit_mats[dress_knee_d_bone_index] = dress_knee_mat.copy()

                # 足首D
                if f"{ankle_bone_name}D" in dress.bones:
                    dress_ankle_d_bone_index = dress.bones[f"{ankle_bone_name}D"].index
                    bone_scale_offsets[dress_ankle_d_bone_index] = BoneMorphOffset(
                        dress_ankle_d_bone_index,
                        bone_scale_offsets[dress.bones[ankle_bone_name].index].position,
                        bone_scale_offsets[dress.bones[ankle_bone_name].index].rotation.qq,
                    )
                    dress_fit_mats[dress_ankle_d_bone_index] = dress_ankle_mat.copy()

                # 足先EX
                if ex_bone_name in dress.bones:
                    dress_ex_original_pos = dress.bones[ex_bone_name].position

                    # 足首とつま先の比率から求める
                    dress_ex_scale = (dress_ex_original_pos - dress_ankle_original_pos) / (dress_toe_original_pos - dress_ankle_original_pos)
                    dress_ex_fit_pos = dress_ankle_fit_pos + (dress_toe_original_pos - dress_ankle_original_pos) * dress_ex_scale

                    dress_ex_scale_pos = dress_ankle_mat * (dress_ex_original_pos - dress_ankle_original_pos)

                    ex_local_offset_pos = dress_ex_scale_pos - dress_ex_fit_pos
                    bone_scale_offsets[dress.bones[ex_bone_name].index] = BoneMorphOffset(dress.bones[ex_bone_name].index, ex_local_offset_pos, MQuaternion())

                    ex_mat = dress_leg_mat.copy()
                    ex_mat.translate((dress_ex_original_pos - dress_ankle_original_pos) + ex_local_offset_pos)
                    dress_fit_mats[dress.bones[ex_bone_name].index] = ex_mat

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
        if parent_name and not child_names:
            # 子どもが居ない場合、親ボーンの子どもから求め直す
            child_names = [b.name for b in model.bones if model.bones[parent_name].index == b.parent_index and b.name in dress.bones]
        if parent_name and child_names:
            dress_child_mean_pos = MVector3D(*np.mean([dress.bones[cname].position.vector for cname in child_names], axis=0))
            model_child_mean_pos = MVector3D(*np.mean([model.bones[cname].position.vector for cname in child_names], axis=0))
            # 人物にない衣装ボーンの縮尺
            dress_wrap_scale = (bone.position - dress.bones[parent_name].position) / (
                (dress_child_mean_pos - bone.position) + (bone.position - dress.bones[parent_name].position)
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

        model_bone_positions[bone.index] = MVector3D()
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
