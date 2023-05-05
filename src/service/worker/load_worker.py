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
from mlib.pmx.pmx_part import Bone, BoneMorphOffset, MaterialMorphCalcMode, MaterialMorphOffset, Morph, MorphType, STANDARD_BONE_NAMES
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
        elif file_panel.model_ctrl.original_data:
            model = file_panel.model_ctrl.original_data
        else:
            model = PmxModel()

        if file_panel.dress_ctrl.valid() and (is_model_change or not file_panel.dress_ctrl.data):
            dress = file_panel.dress_ctrl.reader.read_by_filepath(file_panel.dress_ctrl.path)

            self.valid_model(dress, "衣装")

            model, dress = self.add_mismatch_bones(model, dress)

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
        elif file_panel.dress_ctrl.original_data:
            dress = file_panel.dress_ctrl.original_data
        else:
            dress = PmxModel()

        if file_panel.motion_ctrl.valid() and (not file_panel.motion_ctrl.data or is_model_change or is_dress_change):
            motion = file_panel.motion_ctrl.reader.read_by_filepath(file_panel.motion_ctrl.path)
        elif file_panel.motion_ctrl.original_data:
            motion = file_panel.motion_ctrl.original_data
        else:
            motion = VmdMotion("empty")

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

    def add_mismatch_bones(self, model: PmxModel, dress: PmxModel):
        """準標準ボーンの不足分を追加"""
        # 準標準ボーンで足りないボーン名を抽出
        short_model_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(model.bones.names)
        short_dress_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(dress.bones.names)

        # 両方の片方にしかないボーン名を抽出
        mismatch_bone_names = short_model_bone_names ^ short_dress_bone_names

        # ミスマッチボーンで追加する必要のあるボーン名を抽出(ログ用にソートする)
        short_mismatch_model_bone_names = sorted(list(mismatch_bone_names - set(model.bones.names)))
        short_mismatch_dress_bone_names = sorted(list(mismatch_bone_names - set(dress.bones.names)))

        logger.info(
            "-- 人物モデルの追加対象準標準ボーン: {b}",
            b=", ".join(short_mismatch_model_bone_names),
        )
        logger.info(
            "-- 衣装モデルの追加対象準標準ボーン: {b}",
            b=", ".join(short_mismatch_dress_bone_names),
        )

        model_inserted_bone_names = []
        for bone_name in STANDARD_BONE_NAMES.keys():
            if bone_name in short_mismatch_model_bone_names:
                if model.insert_standard_bone(bone_name):
                    model_inserted_bone_names.append(bone_name)
                    logger.info("-- -- 人物: 準標準ボーン追加: {b}", b=bone_name)

        model.replace_standard_weights(list(short_mismatch_model_bone_names))
        logger.info("-- 人物: ウェイト置換")

        if model_inserted_bone_names:
            model.bone_trees = model.bones.create_bone_trees()
            model.replace_standard_weights(model_inserted_bone_names)
            logger.info("-- 人物: ウェイト置換")

        dress_inserted_bone_names = []
        for bone_name in STANDARD_BONE_NAMES.keys():
            if bone_name in short_mismatch_dress_bone_names:
                if dress.insert_standard_bone(bone_name):
                    dress_inserted_bone_names.append(bone_name)
                    logger.info("-- -- 衣装: 準標準ボーン追加: {b}", b=bone_name)

        if dress_inserted_bone_names:
            dress.bone_trees = dress.bones.create_bone_trees()
            dress.replace_standard_weights(dress_inserted_bone_names)
            logger.info("-- 衣装: ウェイト置換")

        return model, dress

    def create_material_transparent_morphs(self, model: PmxModel) -> PmxModel:
        """材質OFFモーフ追加"""
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

        # 全材質透明化
        morph = Morph(name="全材質TR")
        morph.is_system = True
        morph.morph_type = MorphType.MATERIAL
        offsets = [
            MaterialMorphOffset(
                -1,
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
        FIT_BONE_NAMES = [
            ("左腕", "左手首"),
            ("右腕", "右手首"),
            ("左足", "左足首"),
            ("右足", "右足首"),
        ]

        FIT_TRUNK_BONE_NAMES = [
            ("上半身", "首"),
            ("下半身", "足中心"),
        ]

        FIT_FINGER_BONE_NAMES = [
            ("左親指１", "左親指２"),
            ("左人指１", "左人指３"),
            ("左中指１", "左中指３"),
            ("左薬指１", "左薬指３"),
            ("左小指１", "左小指３"),
            ("右親指１", "右親指２"),
            ("右人指１", "右人指３"),
            ("右中指１", "右中指３"),
            ("右薬指１", "右薬指３"),
            ("右小指１", "右小指３"),
        ]

        bone_fitting_morph = Morph(name="BoneFitting")
        bone_fitting_morph.is_system = True
        bone_fitting_morph.morph_type = MorphType.BONE
        bone_fitting_offsets: dict[int, BoneMorphOffset] = {}
        # model_bone_positions: dict[int, MVector3D] = {-1: MVector3D()}
        # model_bone_tail_relative_positions: dict[int, MVector3D] = {-1: MVector3D()}
        dress_offset_qqs: dict[int, MQuaternion] = {}
        dress_offset_scales: dict[int, MVector3D] = {}
        dress_fit_scales: dict[int, MVector3D] = {}
        dress_offset_positions: dict[int, MVector3D] = {}
        dress_motion = VmdMotion()

        logger.info("-- フィッティング用事前計算")

        dress_bone_tree_count = len(dress.bone_trees)
        # for i, dress_bone_tree in enumerate(dress.bone_trees):
        #     for dress_bone in dress_bone_tree:
        #         model_bone_positions, model_bone_tail_relative_positions = self.get_model_position(
        #             model,
        #             dress,
        #             dress_bone.name,
        #             model_bone_positions,
        #             model_bone_tail_relative_positions,
        #         )

        #     logger.count(
        #         "-- 事前計算",
        #         index=i,
        #         total_index_count=dress_bone_tree_count,
        #         display_block=100,
        #     )

        logger.info("-- フィッティング用ウェイト別頂点取得（人物）")
        model_vertices_by_bones = model.get_vertices_by_bone()

        logger.info("-- フィッティング用ウェイト別頂点取得（衣装）")
        dress_vertices_by_bones = dress.get_vertices_by_bone()

        logger.info("-- フィッティング回転計算")

        z_direction = MVector3D(0, 0, -1)
        for i, dress_bone_tree in enumerate(dress.bone_trees):
            for n, dress_bone in enumerate(dress_bone_tree):
                if dress_bone.index in dress_offset_qqs or 0 == n:
                    continue
                if (
                    dress_bone.name not in model.bones
                    or not dress.bone_trees.is_in_standard(dress_bone.name)
                    or dress_bone.is_ik
                    or dress_bone.has_fixed_axis
                    or dress_bone.name in ["全ての親", "センター", "グルーブ", "腰", Bone.SYSTEM_ROOT_NAME]
                ):
                    # 人物に同じボーンがない、IKボーン、捩ボーン、準標準までに含まれない場合、角度は計算しない
                    dress_offset_qqs[dress_bone.index] = MQuaternion()
                    continue

                # 人物：自分の方向
                model_x_direction = model.bones[dress_bone.name].tail_relative_position.normalized()
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

                logger.debug(f"回転オフセット[{dress_bone.name}][{dress_fit_qq.to_euler_degrees()}]")

            logger.count(
                "-- 回転計算",
                index=i,
                total_index_count=dress_bone_tree_count,
                display_block=100,
            )

        logger.info("-- フィッティングスケール計算")

        dress_standard_scales: list[MVector3D] = []
        for from_name, to_name in FIT_BONE_NAMES + FIT_TRUNK_BONE_NAMES:
            if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                continue

            # 親までをフィッティングさせた上で改めてボーン位置を求める
            dress_to_matrixes = dress_motion.bones.get_matrix_by_indexes([0], dress.bone_trees.filter(to_name), dress, append_ik=False)

            model_relative_position = (model.bones[to_name].position - model.bones[from_name].position).effective(rtol=0.05, atol=0.05).abs()
            dress_relative_position = (
                (dress_to_matrixes[0][from_name].global_matrix.inverse() * dress_to_matrixes[0][to_name].position).effective(rtol=0.05, atol=0.05).abs()
            )

            scale = model_relative_position / dress_relative_position
            if scale and scale.length() != 1:
                dress_standard_scales.append(scale)

        dress_root_scale = np.max(MVector3D.std_mean(dress_standard_scales).vector) if dress_standard_scales else 1
        dress_offset_root_scale = MVector3D(dress_root_scale, dress_root_scale, dress_root_scale)

        for dress_bone in dress.bones:
            if 0 <= dress_bone.parent_index:
                continue
            # ルートボーンにスケールキーフレとして追加
            bf = dress_motion.bones[dress_bone.name][0]
            bf.scale = dress_offset_root_scale
            dress_motion.bones[dress_bone.name].append(bf)
            dress_offset_scales[dress_bone.index] = dress_offset_root_scale
            dress_fit_scales[dress_bone.index] = dress_offset_root_scale

        logger.info("-- -- スケール計算 [全身][{s}]", s=dress_offset_root_scale)

        dress_trunc_fit_scales: dict[str, float] = {}
        for from_name, to_name in FIT_TRUNK_BONE_NAMES:
            if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                continue

            # 親までをフィッティングさせた上で改めてボーン位置を求める
            dress_to_matrixes = dress_motion.bones.get_matrix_by_indexes([0], dress.bone_trees.filter(to_name), dress, append_ik=False)

            model_relative_position = (model.bones[to_name].position - model.bones[from_name].position).effective(rtol=0.05, atol=0.05).abs()
            dress_relative_position = (
                (dress_to_matrixes[0][from_name].global_matrix.inverse() * dress_to_matrixes[0][to_name].position).effective(rtol=0.05, atol=0.05).abs()
            )

            dress_scale = np.max(model_relative_position.vector) / np.max(dress_relative_position.vector)
            dress_trunc_fit_scales[from_name] = dress_scale

        # スケール計算: 体幹
        dress_trunc_fit_scale = np.mean(list(dress_trunc_fit_scales.values()))
        dress_trunc_fit_scale_vec = MVector3D(dress_trunc_fit_scale, dress_trunc_fit_scale, dress_trunc_fit_scale)

        # 親をキャンセルしていく
        dress_offset_scale = dress_trunc_fit_scale_vec.copy()
        for parent_index in dress.bone_trees[FIT_TRUNK_BONE_NAMES[0][0]].indexes[:-1]:
            if parent_index in dress_offset_scales:
                dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales[parent_index]

        for from_name, to_name in FIT_TRUNK_BONE_NAMES:
            if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                continue

            bf = dress_motion.bones[from_name][0]
            bf.scale = dress_offset_scale
            dress_motion.bones[from_name].append(bf)
            dress_offset_scales[dress.bones[from_name].index] = dress_offset_scale
            dress_fit_scales[dress.bones[from_name].index] = dress_trunc_fit_scale_vec.copy()

            logger.info("-- -- スケール計算 [{b}][{s}]", b=from_name, s=dress_trunc_fit_scale_vec)

        for from_name, to_name in FIT_BONE_NAMES + FIT_FINGER_BONE_NAMES:
            if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                continue

            # 親までをフィッティングさせた上で改めてボーン位置を求める
            dress_to_matrixes = dress_motion.bones.get_matrix_by_indexes([0], dress.bone_trees.filter(to_name), dress, append_ik=False)

            model_relative_position = (model.bones[to_name].position - model.bones[from_name].position).effective(rtol=0.05, atol=0.05).abs()
            dress_relative_position = (
                (dress_to_matrixes[0][from_name].global_matrix.inverse() * dress_to_matrixes[0][to_name].position).effective(rtol=0.05, atol=0.05).abs()
            )

            dress_scale = np.max(model_relative_position.vector) / np.max(dress_relative_position.vector)
            dress_fit_scale = MVector3D(dress_scale, dress_scale, dress_scale)

            # 親をキャンセルしていく
            dress_offset_scale = dress_fit_scale.copy()
            for parent_index in dress.bone_trees[to_name].indexes[:-1]:
                if parent_index in dress_offset_scales:
                    dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales[parent_index]

            bf = dress_motion.bones[from_name][0]
            bf.scale = dress_offset_scale
            dress_motion.bones[from_name].append(bf)
            dress_offset_scales[dress.bones[from_name].index] = dress_offset_scale
            dress_fit_scales[dress.bones[from_name].index] = dress_fit_scale

            logger.info("-- -- スケール計算 [{b}][{s}]", b=from_name, s=dress_fit_scale)

        # upper_bone = dress.bones["上半身"]
        # lower_bone = dress.bones["下半身"]
        # dress_offset_scales[lower_bone.index] = dress_offset_scales[upper_bone.index].copy()
        # dress_fit_scales[lower_bone.index] = dress_fit_scales[upper_bone.index].copy()

        # bf = dress_motion.bones[lower_bone.name][0]
        # bf.scale = dress_offset_scales[lower_bone.index]
        # dress_motion.bones[lower_bone.name].append(bf)

        # logger.info("-- -- スケール計算 [{b}][{s}]", b=lower_bone.name, s=dress_fit_scales[lower_bone.index])

        # 足Dは足をコピーする
        for leg_d_name, leg_fk_name in (("左足D", "左足"), ("右足D", "右足")):
            if not (leg_d_name in dress.bones and leg_fk_name in dress.bones):
                continue

            leg_d_bone = dress.bones[leg_d_name]
            leg_fk_bone = dress.bones[leg_fk_name]

            dress_offset_scales[leg_d_bone.index] = dress_offset_scales[leg_fk_bone.index].copy()
            dress_fit_scales[leg_d_bone.index] = dress_fit_scales[leg_fk_bone.index].copy()

            bf = dress_motion.bones[leg_d_bone.name][0]
            bf.scale = dress_offset_scales[leg_d_bone.index]
            dress_motion.bones[leg_d_bone.name].append(bf)

            logger.info("-- -- スケール計算 [{b}][{s}]", b=leg_d_bone.name, s=dress_fit_scales[leg_d_bone.index])

        if "頭" in model.bones and "頭" in dress.bones:
            # 頭のスケーリングは頭部の頂点から求める
            model_head_vertex_poses: list[np.ndarray] = []
            for vertex_index in model_vertices_by_bones.get(model.bones["頭"].index, []):
                model_head_vertex_poses.append(model.vertices[vertex_index].position.vector)

            dress_head_vertex_poses: list[np.ndarray] = []
            for vertex_index in dress_vertices_by_bones.get(dress.bones["頭"].index, []):
                dress_head_vertex_poses.append(dress.vertices[vertex_index].position.vector)

            if model_head_vertex_poses and dress_head_vertex_poses:
                mean_model_head_vertex_poses = np.mean(model_head_vertex_poses, axis=0)
                max_model_head_vertex_poses = np.max(model_head_vertex_poses, axis=0)

                mean_dress_head_vertex_poses = np.mean(dress_head_vertex_poses, axis=0)
                max_dress_head_vertex_poses = np.max(dress_head_vertex_poses, axis=0)

                model_head_size = MVector3D(*(max_model_head_vertex_poses - mean_model_head_vertex_poses)).length()
                dress_head_size = MVector3D(*(max_dress_head_vertex_poses - mean_dress_head_vertex_poses)).length()

                if model_head_size * dress_root_scale * 0.5 < dress_head_size:
                    # 衣装の頭ウェイト頂点から計算したサイズが、スケーリングした頭部の半分以上である場合のみ縮尺対象とする
                    # 球体の中心から最大までのスケールの平均値で全体を縮尺させる
                    head_fit_scale = MVector3D(
                        *((max_model_head_vertex_poses - mean_model_head_vertex_poses) / (max_dress_head_vertex_poses - mean_dress_head_vertex_poses))
                    )
                    dress_head_scale = np.mean(head_fit_scale.vector)
                    dress_fit_scale = MVector3D(dress_head_scale, dress_head_scale, dress_head_scale)
                    dress_offset_scale = (MVector3D(1, 1, 1) / dress_offset_root_scale) * (MVector3D(1, 1, 1) / dress_offset_scales[0]) * dress_fit_scale

                    bf = dress_motion.bones["頭"][0]
                    bf.scale = dress_offset_scale
                    dress_motion.bones["頭"].append(bf)
                    dress_offset_scales[dress.bones["頭"].index] = dress_offset_scale
                    dress_fit_scales[dress.bones["頭"].index] = dress_fit_scale

                    logger.info("-- -- スケール計算 [{b}][{s}]", b="頭", s=dress_fit_scale)

        logger.info("-- フィッティング移動計算")

        for i, dress_bone_tree in enumerate(dress.bone_trees):
            for n, dress_bone in enumerate(dress_bone_tree):
                if dress_bone.index in dress_offset_positions or 0 == n:
                    continue

                if dress.bone_trees.is_in_standard(dress_bone.name) and dress_bone.name in model.bones:
                    # 親までをフィッティングさせた上で改めてボーン位置を求める
                    dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], dress.bone_trees.filter(dress_bone.name), dress, append_ik=False)
                    dress_offset_position = dress_matrixes[0][dress_bone.name].global_matrix.inverse() * model.bones[dress_bone.name].position

                    # キーフレとして追加
                    bf = dress_motion.bones[dress_bone.name][0]
                    bf.position = dress_offset_position
                    dress_motion.bones[dress_bone.name].append(bf)

                    dress_offset_positions[dress_bone.index] = dress_offset_position

                    logger.debug(f"移動オフセット[{dress_bone.name}][{dress_offset_position}]")

            logger.count(
                "-- 移動計算",
                index=i,
                total_index_count=dress_bone_tree_count,
                display_block=100,
            )

        logger.info("-- フィッティングボーンモーフ追加")

        dress_bone_count = len(dress.bones)
        for i, dress_bone in enumerate(dress.bones):
            if not (
                0 <= dress_bone.index
                and (dress_bone.index in dress_offset_positions or dress_bone.index in dress_offset_qqs or dress_bone.index in dress_offset_scales)
            ):
                continue
            # if dress_bone.name not in dress.bone_trees["左手首"].names:
            #     continue
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

    # def get_model_position(
    #     self,
    #     model: PmxModel,
    #     dress: PmxModel,
    #     dress_bone_name: str,
    #     model_bone_positions: dict[int, MVector3D],
    #     model_bone_tail_relative_positions: dict[int, MVector3D],
    # ) -> tuple[dict[int, MVector3D], dict[int, MVector3D]]:
    #     """衣装モデルのボーン名に相当する人物モデルのボーン位置を取得する"""
    #     dress_bone = dress.bones[dress_bone_name]

    #     if dress_bone.index in model_bone_positions and dress_bone.index in model_bone_tail_relative_positions:
    #         return model_bone_positions, model_bone_tail_relative_positions

    #     if dress_bone.name in model.bones:
    #         model_bone_positions[dress_bone.index] = model.bones[dress_bone.name].position
    #         model_bone_tail_relative_positions[dress_bone.index] = model.bones[dress_bone.name].tail_relative_position
    #         return model_bone_positions, model_bone_tail_relative_positions

    #     dress_fit_scale = 1.0
    #     # まだ仮登録されていない場合、計算する
    #     parent_name = self.get_parent_name(model, dress, dress_bone)
    #     child_names = self.get_child_names(model, dress, dress_bone)
    #     if parent_name and child_names:
    #         dress_child_mean_pos = MVector3D(*np.mean([dress.bones[cname].position.vector for cname in child_names], axis=0))
    #         model_child_mean_pos = MVector3D(*np.mean([model.bones[cname].position.vector for cname in child_names], axis=0))
    #         # 人物にない衣装ボーンの縮尺
    #         dress_fit_scale = (dress_bone.position - dress.bones[parent_name].position) / (
    #             (dress_child_mean_pos - dress_bone.position) + (dress_bone.position - dress.bones[parent_name].position)
    #         )
    #         # 人物モデルに縮尺を当てはめる
    #         model_fake_bone_position = model.bones[parent_name].position + (model_child_mean_pos - model.bones[parent_name].position) * dress_fit_scale
    #         model_bone_positions[dress_bone.index] = model_fake_bone_position
    #     elif dress_bone.is_leg_d:
    #         # 衣装側にだけ足D系列がある場合
    #         if "D" == dress_bone.name[-1]:
    #             # 足D系はFKをコピーする
    #             model_bone_positions[dress_bone.index] = model.bones[dress_bone.name[:-1]].position.copy()
    #         else:
    #             # 足先EXはつま先と足首の縮尺から求める
    #             ankle_name = f"{dress_bone.name[0]}足首"
    #             model_ankle_pos = model.bones[ankle_name].position
    #             dress_ankle_pos = dress.bones[ankle_name].position
    #             # つま先はつま先ＩＫのターゲット
    #             toe_ik_name = f"{dress_bone.name[0]}つま先ＩＫ"
    #             model_toe_pos = model.bones[model.bones[toe_ik_name].ik.bone_index].position
    #             dress_toe_pos = dress.bones[dress.bones[toe_ik_name].ik.bone_index].position
    #             dress_ex_scale = (dress_bone.position - dress_ankle_pos) / (dress_toe_pos - dress_ankle_pos)
    #             model_bone_positions[dress_bone.index] = model_ankle_pos + (model_toe_pos - model_ankle_pos) * dress_ex_scale
    #     elif parent_name and not child_names:
    #         # 同じボーンがまったく人物モデルに無い場合、人物の親ボーンにそのまま紐付ける
    #         model_bone_positions[dress_bone.index] = model.bones[parent_name].position + (dress_bone.position - dress.bones[parent_name].position)
    #     else:
    #         model_bone_positions[dress_bone.index] = MVector3D()

    #     if 0 <= dress_bone.tail_index:
    #         # 末端ボーンがある場合、再計算して返す
    #         model_bone_positions, model_bone_tail_relative_positions = self.get_model_position(
    #             model, dress, dress_bone.tail_index, model_bone_positions, model_bone_tail_relative_positions
    #         )
    #         model_bone_tail_relative_positions[dress_bone.index] = model_bone_positions[dress_bone.tail_index]
    #     else:
    #         # 相対位置の場合はそのまま計算して返す
    #         model_bone_tail_relative_positions[dress_bone.index] = dress_bone.tail_relative_position * dress_fit_scale

    #     return model_bone_positions, model_bone_tail_relative_positions

    # def get_parent_name(self, model: PmxModel, dress: PmxModel, bone: Bone) -> str:
    #     if bone.parent_index < 0:
    #         # ルートはスルー
    #         return ""
    #     # 親ボーンがモデル側にもあればそのまま返す
    #     if dress.bones[bone.parent_index].name in model.bones:
    #         return dress.bones[bone.parent_index].name
    #     # なければ遡る
    #     return self.get_parent_name(model, dress, dress.bones[bone.parent_index])

    # def get_child_names(self, model: PmxModel, dress: PmxModel, bone: Bone) -> list[str]:
    #     child_names: list[str] = []
    #     # 子ボーンリストを取得する
    #     for bname in dress.bones.names:
    #         if dress.bones[bname].parent_index == bone.index and bname in model.bones:
    #             child_names.append(bname)
    #     # なければ終了
    #     return child_names

    # def get_mean_scale(self, model: PmxModel, dress: PmxModel, from_to_names: list[tuple[str, str]]) -> MVector3D:
    #     """指定されたボーンの組み合わせのスケールを取得する"""
    #     dress_scales: dict[int, MVector3D] = {}
    #     for from_bone_name, to_bone_name in from_to_names:
    #         if not (from_bone_name in dress.bones and to_bone_name in dress.bones and from_bone_name in model.bones and to_bone_name in model.bones):
    #             continue
    #         # 人物と衣装の両方にある準標準ボーンの場合、縮尺計算
    #         model_relative_poses = (model.bones[to_bone_name].position - model.bones[from_bone_name].position).effective()
    #         dress_relative_poses = (dress.bones[to_bone_name].position - dress.bones[from_bone_name].position).effective()
    #         scales = model_relative_poses / dress_relative_poses
    #         dress_scales[model.bones[to_bone_name].index] = scales

    #     if not dress_scales:
    #         return MVector3D(1, 1, 1)

    #     return MVector3D.std_mean(list(dress_scales.values()))
