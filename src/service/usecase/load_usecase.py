import os
from typing import Iterable, Optional

import numpy as np

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MQuaternion, MVector3D, MVector4D, calc_local_positions
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import (
    STANDARD_BONE_NAMES,
    Bone,
    BoneMorphOffset,
    BoneSetting,
    MaterialMorphCalcMode,
    MaterialMorphOffset,
    Morph,
    MorphType,
)
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_tree import VmdBoneFrameTrees

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class LoadUsecase:
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

    def add_mismatch_bones(self, model: PmxModel, dress: PmxModel) -> None:
        """準標準ボーンの不足分を追加"""
        # 必ず追加するボーン
        add_bone_names = {"全ての親", "上半身2", "右腕捩", "左腕捩", "右手捩", "左手捩", "右足D", "左足D", "右ひざD", "左ひざD", "右足首D", "左足首D", "右足先EX", "左足先EX"}

        # 準標準ボーンで足りないボーン名を抽出
        short_model_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(model.bones.names)
        short_dress_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(dress.bones.names)

        # 両方の片方にしかないボーン名を抽出
        mismatch_bone_names = (short_model_bone_names ^ short_dress_bone_names) | add_bone_names

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

        logger.info("-- 人物: 初期姿勢計算")

        # 人物の初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone([0], model)

        model_inserted_bone_names = []
        for bone_name in STANDARD_BONE_NAMES.keys():
            if bone_name in short_mismatch_model_bone_names:
                if model.insert_standard_bone(bone_name, model_matrixes):
                    model_inserted_bone_names.append(bone_name)
                    logger.info("-- -- 人物: 準標準ボーン追加: {b}", b=bone_name)

        if model_inserted_bone_names:
            model.setup()
            model.update_vertices_by_bone()
            model.replace_standard_weights(model_inserted_bone_names)
            logger.info("人物: 再セットアップ")
        else:
            model.update_vertices_by_bone()

        logger.info("-- 衣装: 初期姿勢計算")

        # 衣装の初期姿勢を求める
        dress_matrixes = VmdMotion().animate_bone([0], dress)

        dress_inserted_bone_names = []
        for bone_name in STANDARD_BONE_NAMES.keys():
            if bone_name in short_mismatch_dress_bone_names:
                if dress.insert_standard_bone(bone_name, dress_matrixes):
                    dress_inserted_bone_names.append(bone_name)
                    logger.info("-- -- 衣装: 準標準ボーン追加: {b}", b=bone_name)

        if dress_inserted_bone_names:
            dress.setup()
            dress.update_vertices_by_bone()
            dress.replace_standard_weights(dress_inserted_bone_names)

            logger.info("衣装: 再セットアップ")
        else:
            dress.update_vertices_by_bone()

    def create_material_transparent_morphs(self, model: PmxModel) -> None:
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

    def create_dress_individual_bone_morphs(self, model: PmxModel, dress: PmxModel):
        """衣装個別フィッティング用ボーンモーフを作成"""

        for morph_name, _, refit_bone_names in FIT_INDIVIDUAL_BONE_NAMES:
            # 再調整用のモーフ追加
            morph = Morph(name=f"調整:{morph_name}:Refit")
            morph.is_system = True
            morph.morph_type = MorphType.BONE
            for bone_name in refit_bone_names:
                if bone_name in dress.bones:
                    morph.offsets.append(BoneMorphOffset(dress.bones[bone_name].index, MVector3D(), MQuaternion()))
            dress.morphs.append(morph)

        for morph_name, target_bone_names, refit_bone_names in FIT_INDIVIDUAL_BONE_NAMES:
            for axis_name, position, qq, local_scale in (
                ("SX", MVector3D(), MQuaternion(), MVector3D(1, 0, 0)),
                ("SY", MVector3D(), MQuaternion(), MVector3D(0, 1, 0)),
                ("SZ", MVector3D(), MQuaternion(), MVector3D(0, 0, 1)),
                ("RX", MVector3D(), MQuaternion.from_euler_degrees(0, 0, 10), MVector3D()),
                ("RY", MVector3D(), MQuaternion.from_euler_degrees(0, 10, 0), MVector3D()),
                ("RZ", MVector3D(), MQuaternion.from_euler_degrees(10, 0, 0), MVector3D()),
                ("MX", MVector3D(1, 0, 0), MQuaternion(), MVector3D()),
                ("MY", MVector3D(0, 1, 0), MQuaternion(), MVector3D()),
                ("MZ", MVector3D(0, 0, 1), MQuaternion(), MVector3D()),
            ):
                morph = Morph(name=f"調整:{morph_name}:{axis_name}")
                morph.is_system = True
                morph.morph_type = MorphType.BONE

                scale = MVector3D()
                if morph_name in ("足首", "頭", "胸"):
                    # 末端系はグローバルスケールで動かす
                    scale = local_scale.copy()
                    local_scale = MVector3D()

                for bone_name in target_bone_names:
                    if bone_name in dress.bones:
                        if axis_name in ["MX", "RX", "RZ"]:
                            offset_position = position * (-1 if "右" in bone_name else 1)
                            offset_qq = qq.inverse() if "右" in bone_name else qq
                        else:
                            offset_position = position
                            offset_qq = qq
                        morph.offsets.append(
                            BoneMorphOffset(
                                dress.bones[bone_name].index,
                                offset_position,
                                MQuaternion(),
                                scale=scale,
                                local_qq=offset_qq,
                                local_scale=local_scale,
                            )
                        )
                dress.morphs.append(morph)

            # logger.info("-- 個別調整ボーンモーフ [{m}]", m=__(morph_name))

    def refit_dress_morphs(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_morph_motion: VmdMotion,
        refit_bone_name: str,
    ) -> PmxModel:
        """再度フィットさせる位置調整用"""
        morph = dress.morphs[f"調整:{refit_bone_name}:Refit"]

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone([0], model)
        # 衣装は変形を加味する
        dress_matrixes = dress_morph_motion.animate_bone([0], dress)

        for offset in morph.offsets:
            bone_offset: BoneMorphOffset = offset
            dress_bone = dress.bones[bone_offset.bone_index]
            if dress_bone.is_ik:
                # IK系はFKの位置に合わせる
                fk_dress_bone = dress.bones[dress_bone.ik.bone_index]
                if dress_matrixes.exists(0, fk_dress_bone.name):
                    bone_offset.position = dress_matrixes[0, fk_dress_bone.name].position - dress_matrixes[0, dress_bone.name].position
            else:
                if model_matrixes.exists(0, dress_bone.name) and dress_matrixes.exists(0, dress_bone.name):
                    bone_offset.position = model_matrixes[0, dress_bone.name].position - dress_matrixes[0, dress_bone.name].position
        return dress

    def get_dress_ground(
        self,
        dress: PmxModel,
        dress_morph_motion: VmdMotion,
    ) -> float:
        """接地処理"""
        ankle_under_bone_names: list[str] = []
        # 足首より下のボーンから頂点位置を取得する
        for bone_tree in dress.bone_trees:
            for ankle_bone_name in ("右足首", "左足首", "右足首D", "左足首D"):
                if ankle_bone_name in bone_tree.names:
                    for bone in bone_tree.filter(ankle_bone_name):
                        ankle_under_bone_names.append(bone.name)

        # モーフだけを引き継いで行列位置を取得する
        dress_matrixes = dress_morph_motion.animate_bone([0], dress)

        ankle_under_vertex_indexes = set(
            [
                vertex_index
                for bone_name in ankle_under_bone_names
                for vertex_index in dress.vertices_by_bones.get(dress.bones[bone_name].index, [])
            ]
        )

        if not ankle_under_vertex_indexes:
            # 足首から下の頂点が無い場合、スルー
            return 0.0

        ankle_vertex_positions: list[np.ndarray] = []
        for vertex_index in ankle_under_vertex_indexes:
            vertex = dress.vertices[vertex_index]
            # 変形後の位置
            mat = np.zeros((4, 4))
            for n in range(vertex.deform.count):
                bone_index = vertex.deform.indexes[n]
                bone_weight = vertex.deform.weights[n]
                mat += dress_matrixes[0, dress.bones[bone_index].name].local_matrix.vector * bone_weight
            ankle_vertex_positions.append(mat @ np.append(vertex.position.vector, 1))

        # 最も地面に近い頂点を基準に接地位置を求める
        min_position = np.min(ankle_vertex_positions, axis=0)

        return -min_position[1]

    def create_dress_fit_bone_morphs(self, model: PmxModel, dress: PmxModel):
        """衣装フィッティング用ボーンモーフを作成"""

        # ルート調整用ボーンモーフ追加
        model_root_morph = Morph(name="Root:Adjust")
        model_root_morph.is_system = True
        model_root_morph.morph_type = MorphType.BONE
        model_root_morph.offsets.append(BoneMorphOffset(model.bones["全ての親"].index, MVector3D(0, 1, 0), MQuaternion()))
        model.morphs.append(model_root_morph)

        dress_root_morph = Morph(name="Root:Adjust")
        dress_root_morph.is_system = True
        dress_root_morph.morph_type = MorphType.BONE
        dress_root_morph.offsets.append(BoneMorphOffset(dress.bones["全ての親"].index, MVector3D(0, 1, 0), MQuaternion()))
        dress.morphs.append(dress_root_morph)

        dress_bone_fitting_morph = Morph(name="BoneFitting")
        dress_bone_fitting_morph.is_system = True
        dress_bone_fitting_morph.morph_type = MorphType.BONE

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone([0], model)

        logger.info("フィッティンググローバルスケール計算", decoration=MLogger.Decoration.LINE)
        dress_offset_scales, dress_fit_scales = self.get_dress_scale_offsets(model, dress, model_matrixes)

        logger.info("フィッティングオフセット計算", decoration=MLogger.Decoration.LINE)
        dress_offset_positions, dress_offset_qqs = self.get_dress_global_offsets(model, dress, dress_offset_scales, model_matrixes)

        logger.info("フィッティングローカルスケール計算", decoration=MLogger.Decoration.LINE)
        dress_offset_local_scales = self.get_dress_local_scale_offsets(
            model, dress, dress_offset_positions, dress_offset_qqs, dress_offset_scales, model_matrixes
        )
        dress_offset_local_scales = {}

        logger.info("フィッティングボーンモーフ追加", decoration=MLogger.Decoration.LINE)

        for dress_bone in dress.bones:
            if not (
                dress_bone.index in dress_offset_positions
                or dress_bone.index in dress_offset_qqs
                or dress_bone.index in dress_offset_scales
                or dress_bone.index in dress_offset_local_scales
            ):
                continue

            dress_offset_position = dress_offset_positions.get(dress_bone.index, MVector3D())
            dress_offset_qq = dress_offset_qqs.get(dress_bone.index, MQuaternion())
            dress_fit_scale = dress_fit_scales.get(dress_bone.index, MVector3D(1, 1, 1))
            dress_offset_scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1))
            dress_offset_local_scale = dress_offset_local_scales.get(dress_bone.index, MVector3D(1, 1, 1))

            dress_bone_fitting_morph.offsets.append(
                BoneMorphOffset(
                    dress_bone.index,
                    position=dress_offset_position,
                    qq=dress_offset_qq,
                    scale=(dress_offset_scale - 1),
                    local_scale=(dress_offset_local_scale - 1),
                )
            )

            logger.info(
                "-- ボーンモーフ [{b}][移動={p}][回転={q}][縮尺:{s}][ローカル縮尺:{l}]",
                b=dress_bone.name,
                p=dress_offset_position,
                q=dress_offset_qq.to_euler_degrees(),
                s=dress_fit_scale,
                l=dress_offset_local_scale,
            )

        dress.morphs.append(dress_bone_fitting_morph)

    def get_dress_scale_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        model_matrixes: VmdBoneFrameTrees,
    ) -> tuple[dict[int, MVector3D], dict[int, MVector3D]]:
        dress_standard_count = len(STANDARD_BONE_NAMES)

        # 衣装の初期姿勢を求める
        dress_matrixes = VmdMotion().animate_bone([0], dress, append_ik=False)

        dress_offset_scales: dict[int, MVector3D] = {}
        dress_fit_scales: dict[int, MVector3D] = {}

        for i, (bone_name, bone_setting) in enumerate(list(STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones and bone_name in model.bones):
                # 人物と衣装の両方にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]
            model_bone = model.bones[dress_bone.name]

            if not dress_bone.is_scalable_standard:
                continue

            logger.count(
                "-- グローバルスケール計算",
                index=i,
                total_index_count=dress_standard_count,
                display_block=50,
            )

            model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                model, model_bone, bone_setting, matrixes=model_matrixes
            )
            dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                dress, dress_bone, bone_setting, matrixes=dress_matrixes
            )

            if bone_name == "下半身":
                # 下半身は地面からのY距離で決める
                dress_fit_length_scale = model_bone_position.y / dress_bone_position.y
            elif bone_name == "上半身":
                # 上半身は首根元までのY距離で決める
                dress_fit_length_scale = (model_matrixes[0, "首根元"].position.y - model_bone_position.y) / (
                    dress_matrixes[0, "首根元"].position.y - dress_bone_position.y
                )
            else:
                dress_fit_length_scale = (model_tail_position - model_bone_position).length() / (
                    dress_tail_position - dress_bone_position
                ).length()

            dress_fit_scale = MVector3D(dress_fit_length_scale, dress_fit_length_scale, dress_fit_length_scale)

            # 親をキャンセルしていく
            dress_offset_scale = dress_fit_scale.copy()
            for parent_index in dress.bone_trees[bone_name].indexes[:-1]:
                if parent_index in dress_offset_scales:
                    dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales.get(parent_index, MVector3D(1, 1, 1))

            dress_fit_scales[dress_bone.index] = dress_fit_scale
            dress_offset_scales[dress_bone.index] = dress_offset_scale

            logger.debug("-- -- グローバルスケール [{b}][{f:.3f}({o:.3f})]", b=bone_name, f=dress_fit_scale.x, o=dress_offset_scale.x)

        return dress_offset_scales, dress_fit_scales

    def get_dress_global_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_offset_scales: dict[int, MVector3D],
        model_matrixes: VmdBoneFrameTrees,
    ) -> tuple[dict[int, MVector3D], dict[int, MQuaternion]]:
        dress_standard_count = len(STANDARD_BONE_NAMES)

        dress_motion = VmdMotion()
        dress_offset_positions: dict[int, MVector3D] = {}
        dress_offset_qqs: dict[int, MQuaternion] = {}

        for i, (bone_name, bone_setting) in enumerate(list(STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones and bone_name in model.bones):
                # 人物と衣装の両方にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]
            model_bone = model.bones[bone_name]

            if dress_bone.is_system and bone_name not in ("足中心", "首根元"):
                # システムボーンはスルー
                continue

            logger.count(
                "-- オフセット計算",
                index=i,
                total_index_count=dress_standard_count,
                display_block=50,
            )

            # 移動計算 ------------------
            model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                model, model_bone, bone_setting, matrixes=model_matrixes
            )
            dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
            )

            dress_offset_position = model_bone_position - dress_bone_position

            # キーフレとして追加
            mbf = dress_motion.bones[dress_bone.name][0]
            mbf.position = dress_offset_position
            dress_motion.bones[dress_bone.name].append(mbf)

            dress_offset_positions[dress_bone.index] = dress_offset_position

            logger.debug(
                f"-- -- 移動オフセット[{dress_bone.name}][{dress_offset_position}][model={model_bone_position}][dress={dress_bone_position}]"
            )

            if not (dress_bone.can_translate or dress_bone.is_ankle):
                # 回転計算 ------------------

                model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                    model, model_bone, bone_setting, matrixes=model_matrixes
                )
                dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                    dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
                )

                model_local_matrix = (model_tail_position - model_bone_position).to_local_matrix4x4()
                dress_local_matrix = (dress_tail_position - dress_bone_position).to_local_matrix4x4()

                # モデルのボーンの向きに衣装を合わせる
                dress_offset_qq = (model_local_matrix @ dress_local_matrix.inverse()).to_quaternion()

                dress_offset_qqs[dress_bone.index] = dress_offset_qq

                # キーフレとして追加
                qbf = dress_motion.bones[dress_bone.name][0]
                qbf.rotation = dress_offset_qq
                dress_motion.bones[dress_bone.name].append(qbf)

                logger.debug(
                    f"-- -- 回転オフセット[{dress_bone.name}][{dress_offset_qq.to_euler_degrees()}]"
                    + f"[model={model_bone_position}][dress={dress_bone_position}]"
                )

            # キーフレとしてスケーリング追加
            sbf = dress_motion.bones[dress_bone.name][0]
            sbf.scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            dress_motion.bones[dress_bone.name].append(sbf)

        for dress_other_bone in dress.bones:
            for parent_bone_index in (dress.bones["上半身"].index, dress.bones["下半身"].index):
                if dress_other_bone.parent_index == parent_bone_index and not dress.bone_trees.is_in_standard(dress_other_bone.name):
                    # 親ボーンが体幹かつ準標準ボーンの範囲外の場合、体幹の回転を打ち消した回転を持つ
                    dress_fit_qq = dress_offset_qqs.get(parent_bone_index, MQuaternion()).inverse()
                    if dress_fit_qq:
                        dress_offset_qqs[dress_other_bone.index] = dress_fit_qq

                        # キーフレとして追加
                        bf = dress_motion.bones[dress_other_bone.name][0]
                        bf.rotation = dress_fit_qq
                        dress_motion.bones[dress_other_bone.name].append(bf)

                        logger.debug(f"-- -- 回転オフセット(順標準外)[{dress_other_bone.name}][{dress_fit_qq.to_euler_degrees()}]")

        return dress_offset_positions, dress_offset_qqs

    def get_dress_local_scale_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_offset_positions: dict[int, MVector3D],
        dress_offset_qqs: dict[int, MQuaternion],
        dress_offset_scales: dict[int, MVector3D],
        model_matrixes: VmdBoneFrameTrees,
    ) -> dict[int, MVector3D]:
        dress_standard_count = len(STANDARD_BONE_NAMES)

        dress_motion = VmdMotion()
        dress_offset_local_scales: dict[int, MVector3D] = {}

        for dress_bone in dress.bones:
            bf = dress_motion.bones[dress_bone.name][0]
            bf.position = dress_offset_positions.get(dress_bone.index, MVector3D())
            bf.rotation = dress_offset_qqs.get(dress_bone.index, MQuaternion())
            bf.scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            dress_motion.bones[dress_bone.name].append(bf)

        # 衣装の初期姿勢を求める
        dress_matrixes = dress_motion.animate_bone([0], dress)

        for i, (bone_name, bone_setting) in enumerate(list(STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones and bone_name in model.bones):
                # 人物と衣装の両方にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]
            model_bone = model.bones[dress_bone.name]

            if not dress_bone.is_scalable_standard:
                # スケーリング対象外の場合、スルー
                continue

            logger.count(
                "-- ローカルスケール計算",
                index=i,
                total_index_count=dress_standard_count,
                display_block=50,
            )

            dress_vertices: set[int] = set([])
            model_vertices: set[int] = set([])

            for weight_bone_name in bone_setting.weight_names:
                if weight_bone_name in dress.bones:
                    dress_vertices |= set(dress.vertices_by_bones.get(dress.bones[weight_bone_name].index, []))
                if weight_bone_name in model.bones:
                    model_vertices |= set(model.vertices_by_bones.get(model.bones[weight_bone_name].index, []))

            if not (dress_vertices and model_vertices):
                continue

            model_deformed_local_positions = self.get_deformed_positions(model, model_bone, bone_setting, model_vertices, model_matrixes)
            dress_deformed_local_positions = self.get_deformed_positions(dress, dress_bone, bone_setting, dress_vertices, dress_matrixes)

            model_local_positions = MVector3D(*np.max(np.abs(model_deformed_local_positions), axis=0))
            dress_local_positions = MVector3D(*np.max(np.abs(dress_deformed_local_positions), axis=0))

            # ローカルX軸方向はローカルスケール対象外
            dress_offset_local_scale = (model_local_positions / dress_local_positions).one()
            dress_offset_local_scale.x = 1

            dress_offset_local_scales[dress_bone.index] = dress_offset_local_scale

            logger.debug(
                f"-- -- ローカルスケール[{dress_bone.name}][{dress_offset_local_scale}]"
                + f"[model={model_local_positions}][dress={dress_local_positions}]"
            )

        return dress_offset_local_scales

    def get_deformed_positions(
        self,
        model: PmxModel,
        bone: Bone,
        bone_setting: BoneSetting,
        model_vertices: set[int],
        matrixes: VmdBoneFrameTrees,
    ) -> np.ndarray:
        model_deformed_vertices: list[np.ndarray] = []
        for vertex_index in model_vertices:
            mat = np.zeros((4, 4))
            vertex = model.vertices[vertex_index]
            for n in range(vertex.deform.count):
                bone_index = vertex.deform.indexes[n]
                bone_weight = vertex.deform.weights[n]
                mat += matrixes[0, model.bones[bone_index].name].local_matrix.vector * bone_weight
            model_deformed_vertices.append(mat @ vertex.position.vector4)

        model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(model, bone, bone_setting, matrixes=matrixes)

        if bone.name in ("左足首", "右足首"):
            model_tail_position = model_bone_position + MVector3D(0, 0, -1)

        model_local_positions = calc_local_positions(
            np.array(model_deformed_vertices),
            model_bone_position,
            model_tail_position,
        )

        # 中央値と標準偏差を計算
        median_standard_values = np.median(model_local_positions, axis=0)
        std_standard_values = np.std(model_local_positions, axis=0)

        # 中央値から標準偏差の一定範囲までの値を取得
        filtered_standard_values = model_local_positions[
            (np.all(model_local_positions >= median_standard_values - (std_standard_values * 2), axis=1))
            & (np.all(model_local_positions <= median_standard_values + (std_standard_values * 2), axis=1))
        ]

        return filtered_standard_values

    def get_tail_position(
        self,
        model: PmxModel,
        bone: Bone,
        bone_setting: BoneSetting,
        motion: Optional[VmdMotion] = None,
        matrixes: Optional[VmdBoneFrameTrees] = None,
        append_ik: bool = True,
    ) -> tuple[MMatrix4x4, MVector3D, MVector3D]:
        """
        末端位置を取得

        Parameters
        ----------
        bone_index : int
            ボーンINDEX

        Returns
        -------
        ボーンの末端位置（グローバル位置）
        """

        if isinstance(bone_setting.relatives, Iterable):
            # 表示先ボーンが指定されており、いずれかある場合、そのまま使用
            for tail_bone_name in bone_setting.relatives:
                if tail_bone_name in model.bones:
                    if motion is not None:
                        matrixes = motion.animate_bone([0], model, [tail_bone_name], append_ik=append_ik)
                    if matrixes is not None:
                        return (
                            matrixes[0, bone.name].global_matrix,
                            matrixes[0, bone.name].position,
                            matrixes[0, tail_bone_name].position,
                        )

        # 表示先が相対位置の場合はボーンまでの位置＋末端
        if motion is not None:
            matrixes = motion.animate_bone([0], model, [bone.name], append_ik=append_ik)
        if matrixes is not None:
            return (
                matrixes[0, bone.name].global_matrix,
                matrixes[0, bone.name].position,
                matrixes[0, bone.name].global_matrix * bone_setting.relatives,
            )
        return MMatrix4x4(), MVector3D(), MVector3D()


FIT_ROOT_BONE_NAMES = [
    ("足中心", "首根元"),
]

FIT_TRUNK_BONE_NAMES = [
    ("上半身", "首根元"),
    ("下半身", "足中心"),
]

FIT_EXTREMITIES_BONE_NAMES = [
    ("左腕", (("左腕", "左ひじ"), ("左ひじ", "左手首"))),
    ("左足", (("左足", "左ひざ"), ("左ひざ", "左足首"))),
    ("右腕", (("右腕", "右ひじ"), ("右ひじ", "右手首"))),
    ("右足", (("右足", "右ひざ"), ("右ひざ", "右足首"))),
]

FIT_FINGER_BONE_NAMES = [
    ("左親指１", (("左親指１", "左親指２"),)),
    ("左人指１", (("左人指１", "左人指２"), ("左人指２", "左人指３"))),
    ("左中指１", (("左中指１", "左中指２"), ("左中指２", "左中指３"))),
    ("左薬指１", (("左薬指１", "左薬指２"), ("左薬指２", "左薬指３"))),
    ("左小指１", (("左小指１", "左小指２"), ("左小指２", "左小指３"))),
    ("右親指１", (("右親指１", "右親指２"),)),
    ("右人指１", (("右人指１", "右人指２"), ("右人指２", "右人指３"))),
    ("右中指１", (("右中指１", "右中指２"), ("右中指２", "右中指３"))),
    ("右薬指１", (("右薬指１", "右薬指２"), ("右薬指２", "右薬指３"))),
    ("右小指１", (("右小指１", "右小指２"), ("右小指２", "右小指３"))),
]

# IKはFKの後に指定する事
FIT_INDIVIDUAL_BONE_NAMES = [
    (__("下半身"), ("下半身",), ("足中心",)),
    (__("上半身"), ("上半身",), ("上半身2",)),
    (__("上半身2"), ("上半身2", "上半身3"), ("首根元",)),
    (__("胸"), ("左胸", "右胸"), []),
    (__("首"), ("首",), ("頭",)),
    (__("頭"), ("頭",), []),
    (__("肩"), ("右肩", "左肩"), ("右肩C", "左肩C", "右腕", "左腕")),
    (__("腕"), ("右腕", "左腕"), ("右腕捩", "左腕捩", "右腕捩1", "左腕捩1", "右腕捩2", "左腕捩2", "右腕捩3", "左腕捩3", "右腕捩4", "左腕捩4", "右ひじ", "左ひじ")),
    (__("ひじ"), ("右ひじ", "左ひじ"), ("右手捩", "左手捩", "右手捩1", "左手捩1", "右手捩2", "左手捩2", "右手捩3", "左手捩3", "右手捩4", "左手捩4", "右手首", "左手首")),
    (__("手のひら"), ("右手首", "左手首"), []),
    (__("足"), ("右足", "左足", "右足D", "左足D"), ("右ひざ", "左ひざ", "右ひざD", "左ひざD")),
    (__("ひざ"), ("右ひざ", "左ひざ", "右ひざD", "左ひざD"), ("右足首", "左足首", "右足首D", "左足首D")),
    (__("足首"), ("右足首", "左足首", "右足首D", "左足首D"), ("右足ＩＫ", "右つま先ＩＫ", "左足ＩＫ", "左つま先ＩＫ", "右足IK親", "左足IK親")),
]
