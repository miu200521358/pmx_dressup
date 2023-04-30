import logging
import os
import re
from typing import Optional

import numpy as np
import wx

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MQuaternion, MVector3D, MVector4D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import Bone, BoneMorphOffset, MaterialMorphCalcMode, MaterialMorphOffset, Morph, MorphType
from mlib.pmx.pmx_writer import PmxWriter
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_panel import BasePanel
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.file_panel import FilePanel

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
            logger.info("人物モデル追加セットアップ：材質透過モーフ追加")
            model = self.create_material_transparent_morphs(model)

            is_model_change = True
        elif file_panel.model_ctrl.data:
            model = file_panel.model_ctrl.data
        else:
            model = PmxModel()

        if file_panel.dress_ctrl.valid() and (is_model_change or not file_panel.dress_ctrl.data):
            dress = file_panel.dress_ctrl.reader.read_by_filepath(file_panel.dress_ctrl.path)

            self.valid_model(dress, "衣装")

            # 衣装に材質透明モーフを入れる
            logger.info("衣装モデル追加セットアップ：材質透過モーフ追加")
            dress = self.create_material_transparent_morphs(dress)

            # 衣装にフィッティングボーンモーフを入れる
            logger.info("衣装モデル追加セットアップ：フィッティングボーンモーフ追加")
            dress = self.create_dress_fit_bone_morphs(model, dress)

            # # 衣装にフィッティング頂点モーフを入れる
            # logger.info("衣装モデル追加セットアップ：フィッティング頂点モーフ追加")
            # dress = self.create_dress_fit_vertex_morphs(model, dress, dress_fit_matrixes)

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

    def output_log(self):
        file_panel: FilePanel = self.panel
        output_log_path = re.sub(r"\.pmx$", ".log", file_panel.output_pmx_ctrl.path)

        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)

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

    def create_material_transparent_morphs(self, model: PmxModel) -> PmxModel:
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
                    MVector4D(0.0, 0.0, 0.0, -1.0),
                    MVector3D(0.0, 0.0, 0.0),
                    0.0,
                    MVector3D(0.0, 0.0, 0.0),
                    MVector4D(0.0, 0.0, 0.0, 0.0),
                    0.0,
                    MVector4D(0.0, 0.0, 0.0, 0.0),
                    MVector4D(0.0, 0.0, 0.0, 0.0),
                    MVector4D(0.0, 0.0, 0.0, 0.0),
                )
            ]
            morph.offsets = offsets
            model.morphs.append(morph)
        return model

    def get_exist_parent_index(self, dress: PmxModel, bone: Bone, dress_fit_matrixes: dict[int, MMatrix4x4]) -> int:
        if 0 > bone.parent_index or bone.parent_index in dress_fit_matrixes:
            return bone.parent_index
        return self.get_exist_parent_index(dress, dress.bones[bone.parent_index].parent_index, dress_fit_matrixes)

    def create_dress_fit_bone_morphs(self, model: PmxModel, dress: PmxModel) -> PmxModel:
        """衣装フィッティング用ボーンモーフを作成"""
        bone_fitting_morph = Morph(name="BoneFitting")
        bone_fitting_morph.is_system = True
        bone_fitting_morph.morph_type = MorphType.BONE
        bone_fitting_offsets: dict[int, BoneMorphOffset] = {}
        model_bone_positions: dict[int, MVector3D] = {-1: MVector3D()}
        model_bone_tail_relative_positions: dict[int, MVector3D] = {-1: MVector3D()}
        dress_offset_qqs: dict[int, MQuaternion] = {}
        dress_offset_scales: dict[int, MVector3D] = {}
        dress_offset_positions: dict[int, MVector3D] = {}
        dress_motion = VmdMotion()

        logger.info("-- フィッティング用事前計算")

        dress_bone_tree_count = len(dress.bone_trees)
        for i, dress_bone_tree in enumerate(dress.bone_trees):
            for dress_bone in dress_bone_tree:
                model_bone_positions, model_bone_tail_relative_positions = self.get_model_position(
                    model,
                    dress,
                    dress_bone.name,
                    model_bone_positions,
                    model_bone_tail_relative_positions,
                )

            logger.count(
                "-- 事前計算",
                index=i,
                total_index_count=dress_bone_tree_count,
                display_block=100,
            )

        logger.info("-- フィッティング縮尺計算")

        dress_standard_scales: dict[int, float] = {0: 1}
        dress_bone_count = len(dress.bones)
        for i, dress_bone in enumerate(dress.bones):
            if dress_bone.name in model.bones and dress.bone_trees.is_in_standard(dress_bone.name):
                # 人物と衣装の両方にある準標準ボーンの場合、縮尺計算
                dress_length = dress_bone.tail_relative_position.length()
                model_length = model.bones[dress_bone.name].tail_relative_position.length()
                scale = model_length / dress_length
                if scale != 1.0:
                    dress_standard_scales[dress_bone.index] = scale

            logger.count(
                "-- 縮尺計算",
                index=i,
                total_index_count=dress_bone_count,
                display_block=1000,
            )

        np_dress_standard_scales = np.array(list(dress_standard_scales.values()))
        median_dress_standard_scales = np.median(np_dress_standard_scales)
        std_dress_standard_scales = np.std(np_dress_standard_scales)

        # 中央値から標準偏差の1.5倍までの値を取得
        filtered_dress_standard_scales = np_dress_standard_scales[
            (np_dress_standard_scales >= median_dress_standard_scales - 1.5 * std_dress_standard_scales)
            & (np_dress_standard_scales <= median_dress_standard_scales + 1.5 * std_dress_standard_scales)
        ]

        dress_standard_scale = np.mean(filtered_dress_standard_scales)
        logger.info("-- 準標準ボーンスケール: {s:.3f}", s=dress_standard_scale)

        for dress_bone in dress.bones:
            if 0 <= dress_bone.parent_index:
                continue
            # ルートボーンにスケールキーフレとして追加
            dress_offset_scale = MVector3D(dress_standard_scale, dress_standard_scale, dress_standard_scale)
            bf = dress_motion.bones[dress_bone.name][0]
            bf.scale = dress_offset_scale
            dress_motion.bones[dress_bone.name].append(bf)
            dress_offset_scales[dress_bone.index] = dress_offset_scale

        logger.info("-- フィッティング回転計算")

        z_direction = MVector3D(0, 0, -1)
        for i, dress_bone_tree in enumerate(dress.bone_trees):
            for n, dress_bone in enumerate(dress_bone_tree):
                if (
                    dress_bone.name not in model.bones
                    or not dress.bone_trees.is_in_standard(dress_bone.name)
                    or dress_bone.is_ik
                    or dress_bone.has_fixed_axis
                    or dress_bone.is_leg_d
                    or dress_bone.name in ["全ての親", "センター", "グルーブ"]
                ):
                    # 人物に同じボーンがない、IKボーン、捩ボーン、足D系列、準標準までに含まれない場合、角度は計算しない
                    dress_offset_qqs[dress_bone.index] = MQuaternion()
                    continue

                # 人物：自分の方向
                model_x_direction = model_bone_tail_relative_positions[dress_bone.index].normalized()
                model_y_direction = model_x_direction.cross(z_direction)
                model_slope_qq = MQuaternion.from_direction(model_x_direction, model_y_direction)

                # 衣装：自分の方向
                dress_x_direction = dress_bone.tail_relative_position.normalized()
                dress_y_direction = dress_x_direction.cross(z_direction)
                dress_slope_qq = MQuaternion.from_direction(dress_x_direction, dress_y_direction)

                # モデルのボーンの向きに衣装を合わせる
                dress_fit_qq = model_slope_qq * dress_slope_qq.inverse()

                for tree_bone_name in reversed(dress_bone_tree.names[:n]):
                    # 自分より親は逆回転させる
                    dress_fit_qq *= dress_offset_qqs.get(dress.bones[tree_bone_name].index, MQuaternion()).inverse()

                dress_offset_qqs[dress_bone.index] = dress_fit_qq

                # キーフレとして追加
                bf = dress_motion.bones[dress_bone.name][0]
                bf.rotation = dress_fit_qq
                dress_motion.bones[dress_bone.name].append(bf)

            logger.count(
                "-- 回転計算",
                index=i,
                total_index_count=dress_bone_tree_count,
                display_block=100,
            )

        logger.info("-- フィッティング移動計算")

        for i, dress_bone_tree in enumerate(dress.bone_trees):
            for n, dress_bone in enumerate(dress_bone_tree):
                if dress_bone.index in dress_offset_positions or 0 == n:
                    continue

                dress_offset_position = MVector3D()

                # 親までをフィッティングさせた上で改めてボーン位置を求める
                dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], dress.bone_trees.filter(dress_bone.name), dress, append_ik=False)

                if dress_bone.name in model.bones and dress.bone_trees.is_in_standard(dress_bone.name):
                    dress_offset_position = model_bone_positions[dress_bone.index] - dress_matrixes[0][dress_bone.name].position

                # キーフレとして追加
                bf = dress_motion.bones[dress_bone.name][0]
                bf.position = dress_offset_position
                dress_motion.bones[dress_bone.name].append(bf)

                dress_offset_positions[dress_bone.index] = dress_offset_position

            logger.count(
                "-- 移動計算",
                index=i,
                total_index_count=dress_bone_tree_count,
                display_block=100,
            )

        logger.info("-- フィッティングボーンモーフ追加")

        dress_bone_count = len(dress.bones)
        for i, dress_bone in enumerate(dress.bones):
            dress_offset_position = dress_offset_positions.get(dress_bone.index, MVector3D())
            dress_offset_qq = dress_offset_qqs.get(dress_bone.index, MQuaternion())
            dress_offset_scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1))

            bone_fitting_offsets[dress_bone.index] = BoneMorphOffset(dress_bone.index, dress_offset_position, dress_offset_qq, dress_offset_scale)
            logger.count(
                "-- ボーンモーフ追加",
                index=i,
                total_index_count=dress_bone_count,
                display_block=100,
            )

        bone_fitting_morph.offsets = list(bone_fitting_offsets.values())
        dress.morphs.append(bone_fitting_morph)

        return dress

    def get_model_position(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_bone_name: str,
        model_bone_positions: dict[int, MVector3D],
        model_bone_tail_relative_positions: dict[int, MVector3D],
    ) -> tuple[dict[int, MVector3D], dict[int, MVector3D]]:
        """衣装モデルのボーン名に相当する人物モデルのボーン位置を取得する"""
        dress_bone = dress.bones[dress_bone_name]

        if dress_bone.index in model_bone_positions and dress_bone.index in model_bone_tail_relative_positions:
            return model_bone_positions, model_bone_tail_relative_positions

        if dress_bone.name in model.bones:
            model_bone_positions[dress_bone.index] = model.bones[dress_bone.name].position
            model_bone_tail_relative_positions[dress_bone.index] = model.bones[dress_bone.name].tail_relative_position
            return model_bone_positions, model_bone_tail_relative_positions

        dress_fit_scale = 1.0
        # まだ仮登録されていない場合、計算する
        parent_name = self.get_parent_name(model, dress, dress_bone)
        child_names = self.get_child_names(model, dress, dress_bone)
        if parent_name and child_names:
            dress_child_mean_pos = MVector3D(*np.mean([dress.bones[cname].position.vector for cname in child_names], axis=0))
            model_child_mean_pos = MVector3D(*np.mean([model.bones[cname].position.vector for cname in child_names], axis=0))
            # 人物にない衣装ボーンの縮尺
            dress_fit_scale = (dress_bone.position - dress.bones[parent_name].position) / (
                (dress_child_mean_pos - dress_bone.position) + (dress_bone.position - dress.bones[parent_name].position)
            )
            # 人物モデルに縮尺を当てはめる
            model_fake_bone_position = model.bones[parent_name].position + (model_child_mean_pos - model.bones[parent_name].position) * dress_fit_scale
            model_bone_positions[dress_bone.index] = model_fake_bone_position
        elif parent_name and not child_names:
            # 同じボーンがまったく人物モデルに無い場合、人物の親ボーンにそのまま紐付ける
            model_bone_positions[dress_bone.index] = model.bones[parent_name].position + (dress_bone.position - dress.bones[parent_name].position)
        else:
            model_bone_positions[dress_bone.index] = MVector3D()

        if 0 <= dress_bone.tail_index:
            # 末端ボーンがある場合、再計算して返す
            model_bone_positions, model_bone_tail_relative_positions = self.get_model_position(
                model, dress, dress_bone.tail_index, model_bone_positions, model_bone_tail_relative_positions
            )
            model_bone_tail_relative_positions[dress_bone.index] = model_bone_positions[dress_bone.tail_index]
        else:
            # 相対位置の場合はそのまま計算して返す
            model_bone_tail_relative_positions[dress_bone.index] = dress_bone.tail_relative_position * dress_fit_scale

        return model_bone_positions, model_bone_tail_relative_positions

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
