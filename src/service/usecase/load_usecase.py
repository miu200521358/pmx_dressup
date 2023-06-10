import os
from typing import Iterable, Optional

import numpy as np

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MQuaternion, MVector3D, MVector4D, calc_local_positions, align_triangle
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
        add_bone_names = {
            "全ての親",
            "上半身2",
            "右腕捩",
            "左腕捩",
            "右手捩",
            "左手捩",
            "右親指先",
            "右人指先",
            "右中指先",
            "右薬指先",
            "右小指先",
            "左親指先",
            "左人指先",
            "左中指先",
            "左薬指先",
            "左小指先",
            "右足D",
            "左足D",
            "右ひざD",
            "左ひざD",
            "右足首D",
            "左足首D",
            "右足先EX",
            "左足先EX",
        }

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
            dress.replace_standard_weights(dress_inserted_bone_names)
            dress.update_vertices_by_bone()

            logger.info("衣装: 再セットアップ")
        else:
            dress.update_vertices_by_bone()

    def replace_upper2(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """上半身2のボーン置き換え"""
        replace_bone_names = ("上半身", "首根元", "上半身2")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names)

        return ["上半身2"] if is_add else []

    def replace_upper3(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """上半身3のボーン置き換え"""
        replace_bone_names = ("上半身2", "首根元", "上半身3")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names)

        return ["上半身3"] if is_add else []

    def replace_neck(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """首のボーン置き換え"""
        replace_bone_names = ("首根元", "頭", "首")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names)

        return ["首"] if is_add else []

    def replace_shoulder(self, model: PmxModel, dress: PmxModel, direction: str) -> list[str]:
        """肩のボーン置き換え"""
        replace_bone_names = ("首根元", f"{direction}腕", f"{direction}肩")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names)
        replaced_bone_names = []

        if is_add:
            replaced_bone_names.append(f"{direction}肩")

            if f"{direction}肩P" in dress.bones:
                dress.bones[f"{direction}肩P"].position = dress.bones[f"{direction}肩"].position.copy()
                replaced_bone_names.append(f"{direction}肩P")

            if f"{direction}腕" in dress.bones:
                dress.bones[f"{direction}腕"].position += diff / 2
                replaced_bone_names.append(f"{direction}腕")

            if f"{direction}肩C" in dress.bones:
                dress.bones[f"{direction}肩C"].position = dress.bones[f"{direction}腕"].position.copy()
                replaced_bone_names.append(f"{direction}肩C")

        return replaced_bone_names

    def replace_bone_position(
        self, model: PmxModel, dress: PmxModel, from_name: str, to_name: str, replace_name: str
    ) -> tuple[bool, MVector3D]:
        """
        衣装のボーン位置を人物ボーン位置に合わせて配置を変える
        """
        if not (model.bones.exists([from_name, to_name, replace_name]) and dress.bones.exists([from_name, to_name, replace_name])):
            # ボーンが足りなかったら追加しない
            return False, MVector3D()

        model_from_pos = model.bones[from_name].position
        model_replace_pos = model.bones[replace_name].position
        model_to_pos = model.bones[to_name].position
        dress_from_pos = dress.bones[from_name].position
        dress_replace_pos = dress.bones[replace_name].position
        dress_to_pos = dress.bones[to_name].position

        # 元ボーン-置換ボーン ベースで求めた時の位置 ---------------

        # 衣装の置換ボーンの位置を求め直す
        dress_replace_new_pos = align_triangle(model_from_pos, model_to_pos, model_replace_pos, dress_from_pos, dress_to_pos)

        dress.bones[replace_name].position = dress_replace_new_pos
        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r=replace_name,
            u=dress_replace_pos,
            p=dress_replace_new_pos,
            d=(dress_replace_new_pos - dress_replace_pos),
        )

        return True, dress_replace_new_pos - dress_replace_pos

    def replace_twist(self, model: PmxModel, dress: PmxModel, replaced_bone_names: list[str]) -> list[str]:
        """腕捩・手捩のボーン置き換え"""

        # replace_bone_names = [
        #     "右腕",
        #     "右ひじ",
        #     "右腕捩",
        #     "右腕捩1",
        #     "右腕捩2",
        #     "右腕捩3",
        #     "右手首",
        #     "右手捩",
        #     "右手捩1",
        #     "右手捩2",
        #     "右手捩3",
        #     "左腕",
        #     "左ひじ",
        #     "左腕捩",
        #     "左腕捩1",
        #     "左腕捩2",
        #     "左腕捩3",
        #     "左手首",
        #     "左手捩",
        #     "左手捩1",
        #     "左手捩2",
        #     "左手捩3",
        # ]
        # if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
        #     return []

        # logger.info("フィッティング用ウェイト別頂点取得（衣装）")
        # dress.update_vertices_by_bone()

        replace_bone_set = (
            ("右腕", "右ひじ", "右腕捩"),
            ("右ひじ", "右手首", "右手捩"),
            ("左腕", "左ひじ", "左腕捩"),
            ("左ひじ", "左手首", "左手捩"),
        )

        # # 一旦衣装の置き換えウェイトを元ボーンに置き換える
        # replaced_bone_map = dict([(b.index, b.index) for b in dress.bones])
        # for from_name, to_name, replace_name in replace_bone_set:
        #     if replace_name in dress.bones and from_name and dress.bones:
        #         replaced_bone_map[dress.bones[replace_name].index] = dress.bones[from_name].index
        #     for no in range(1, 5):
        #         replace_twist_name = f"{replace_name}{no}"
        #         if replace_twist_name in dress.bones and replace_twist_name and dress.bones:
        #             replaced_bone_map[dress.bones[replace_twist_name].index] = dress.bones[from_name].index

        # # 捩り系の頂点リストを取得する
        # dress_vertex_indexes = set([])
        # for bone_name in [
        #     "右腕捩",
        #     "右腕捩1",
        #     "右腕捩2",
        #     "右腕捩3",
        #     "右手捩",
        #     "右手捩1",
        #     "右手捩2",
        #     "右手捩3",
        #     "左腕捩",
        #     "左腕捩1",
        #     "左腕捩2",
        #     "左腕捩3",
        #     "左手捩",
        #     "左手捩1",
        #     "左手捩2",
        #     "左手捩3",
        # ]:
        #     dress_vertex_indexes |= set(dress.vertices_by_bones.get(bone_name, []))

        # # 捩りにウェイトが乗っているのを元ボーンに置き換える
        # for vidx in list(dress_vertex_indexes):
        #     v = dress.vertices[vidx]
        #     v.deform.indexes = np.vectorize(replaced_bone_map.get)(v.deform.indexes)

        for from_name, to_name, replace_name in replace_bone_set:
            # 捩りボーンそのもの
            is_add = self.replace_bone_position_twist(model, dress, from_name, to_name, replace_name)
            if is_add:
                replaced_bone_names.append(replace_name)

            # 分散の付与ボーン
            for no in range(1, 5):
                is_add = self.replace_bone_position_twist(model, dress, from_name, to_name, f"{replace_name}{no}")
                if is_add:
                    replaced_bone_names.append(replace_name)

        return replaced_bone_names

    def replace_bone_position_twist(self, model: PmxModel, dress: PmxModel, from_name: str, to_name: str, replace_name: str) -> bool:
        """
        衣装のボーン位置を人物ボーン位置に合わせて配置を変える(斜め)
        """
        if not (model.bones.exists([from_name, to_name, replace_name]) and dress.bones.exists([from_name, to_name, replace_name])):
            # ボーンが足りなかったら追加しない
            return False

        model_from_pos = model.bones[from_name].position
        model_replace_pos = model.bones[replace_name].position
        model_to_pos = model.bones[to_name].position
        dress_from_pos = dress.bones[from_name].position
        dress_replace_pos = dress.bones[replace_name].position
        dress_to_pos = dress.bones[to_name].position

        # 元ボーン-置換ボーン ベースで求めた時の位置 ---------------

        # 元ボーン-置換ボーン:縮尺
        from_replace_scale = ((model_replace_pos - model_from_pos) / (model_to_pos - model_from_pos)) / (
            (dress_replace_pos - dress_from_pos) / (dress_to_pos - dress_from_pos)
        )

        # 縮尺に合わせた位置
        dress_replace_new_pos = dress_from_pos + ((dress_replace_pos - dress_from_pos) * from_replace_scale)

        # 最終的な置換ボーンは元ボーン-置換ボーン,先ボーン-置換ボーンの中間とする
        dress.bones[replace_name].position = dress_replace_new_pos

        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r=replace_name,
            u=dress_replace_pos,
            p=dress_replace_new_pos,
            d=(dress_replace_new_pos - dress_replace_pos),
        )

        return True

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

        for morph_name, (target_bone_names, child_morph_names, is_refit) in FIT_INDIVIDUAL_BONE_NAMES.items():
            # 子どものスケーリング対象もモーフに入れる
            target_child_bone_names = list(
                set(
                    [
                        child_bone_name
                        for child_morph_name in child_morph_names
                        for child_bone_name in FIT_INDIVIDUAL_BONE_NAMES[child_morph_name][0]
                    ]
                )
            )

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
                morph = Morph(name=f"調整:{__(morph_name)}:{axis_name}")
                morph.is_system = True
                morph.morph_type = MorphType.BONE

                scale = MVector3D()
                if morph_name in ("足首", "頭", "胸"):
                    # 末端系はグローバルスケールで動かす
                    scale = local_scale.copy()
                    local_scale = MVector3D()

                # スケールの時だけ子どもを加味する
                target_all_bone_names = list(target_bone_names) + target_child_bone_names if "S" in axis_name else target_bone_names

                for bone_name in target_all_bone_names:
                    if bone_name in dress.bones:
                        if axis_name in ["MX", "RX", "RY", "RZ"]:
                            offset_position = position * (-1 if "左" in bone_name else 1)
                            offset_local_qq = qq.inverse() if "左" in bone_name else qq
                        else:
                            offset_position = position
                            offset_local_qq = qq

                        offset_qq = MQuaternion()
                        if morph_name in ("足首", "頭", "胸"):
                            offset_qq = offset_local_qq.copy()
                            offset_local_qq = MQuaternion()

                        morph.offsets.append(
                            BoneMorphOffset(
                                dress.bones[bone_name].index,
                                position=offset_position,
                                qq=offset_qq,
                                scale=scale,
                                local_position=MVector3D(),
                                local_qq=offset_local_qq,
                                local_scale=local_scale,
                            )
                        )
                dress.morphs.append(morph)

        logger.info("-- 個別調整ボーンモーフ追加")

        for morph_name, (target_bone_names, child_morph_names, is_refit) in FIT_INDIVIDUAL_BONE_NAMES.items():
            if not is_refit:
                continue

            refit_morph = Morph(name=f"調整:{__(morph_name)}:Refit")
            refit_morph.is_system = True
            refit_morph.morph_type = MorphType.BONE

            refit_child_bone_indexes = set([])
            refit_bone_indexes = set([])
            for target_bone_name in target_bone_names:
                if not (target_bone_name in model.bones and target_bone_name in dress.bones):
                    continue
                dress_bone = dress.bones[target_bone_name]
                refit_bone_indexes |= set(dress_bone.relative_bone_indexes)
                for dress_child_bone in dress.bones:
                    if dress_child_bone.index != dress_bone.index and dress_bone.index in dress_child_bone.relative_bone_indexes:
                        refit_child_bone_indexes |= set(dress_child_bone.relative_bone_indexes)

            for bone_index in sorted(refit_child_bone_indexes - refit_bone_indexes):
                dress_bone = dress.bones[bone_index]

                if not dress_bone.is_standard:
                    continue

                # 再調整用のモーフ追加
                refit_morph.offsets.append(BoneMorphOffset(dress_bone.index, MVector3D(), MQuaternion()))

            dress.morphs.append(refit_morph)

        logger.info("-- 再調整ボーンモーフ追加")

    def refit_dress_morphs(
        self,
        model: PmxModel,
        dress: PmxModel,
        model_morph_motion: VmdMotion,
        dress_morph_motion: VmdMotion,
        translated_morph_bone_name: str,
    ) -> PmxModel:
        """再度フィットさせる位置調整用"""

        # refit_morph_name = f"調整:{translated_morph_bone_name}:Refit"

        # if refit_morph_name not in dress.morphs:
        #     return dress

        # refit_morph = dress.morphs[refit_morph_name]

        # model_matrixes = model_morph_motion.animate_bone([0], model)
        # dress_matrixes = dress_morph_motion.animate_bone([0], dress)

        # for offset in refit_morph.offsets:
        #     bone_offset: BoneMorphOffset = offset
        #     dress_bone = dress.bones[bone_offset.bone_index]
        #     if dress_bone.is_ik:
        #         # IK系はFKの位置に合わせる
        #         fk_dress_bone = dress.bones[dress_bone.ik.bone_index]
        #         if model_matrixes.exists(0, fk_dress_bone.name) and dress_matrixes.exists(0, fk_dress_bone.name):
        #             bone_offset.position = model_matrixes[0, fk_dress_bone.name].position - dress_matrixes[0, fk_dress_bone.name].position

        #             logger.debug(
        #                 f"Refit(IK) [{fk_dress_bone.name}][{bone_offset.position}]"
        #                 + f"[model={model_matrixes[0, fk_dress_bone.name].position}]"
        #                 + f"[dress={dress_matrixes[0, fk_dress_bone.name].position}]"
        #             )
        #     elif dress_bone.is_leg_d:
        #         # 足D系はFKの位置に合わせる
        #         fk_dress_bone = dress.bones[dress_bone.effect_index]
        #         if model_matrixes.exists(0, fk_dress_bone.name) and dress_matrixes.exists(0, fk_dress_bone.name):
        #             bone_offset.position = model_matrixes[0, fk_dress_bone.name].position - dress_matrixes[0, fk_dress_bone.name].position

        #             logger.debug(
        #                 f"Refit(足D) [{fk_dress_bone.name}][{bone_offset.position}]"
        #                 + f"[model={model_matrixes[0, fk_dress_bone.name].position}]"
        #                 + f"[dress={dress_matrixes[0, fk_dress_bone.name].position}]"
        #             )
        #     else:
        #         if model_matrixes.exists(0, dress_bone.name) and dress_matrixes.exists(0, dress_bone.name):
        #             bone_offset.position = model_matrixes[0, dress_bone.name].position - dress_matrixes[0, dress_bone.name].position

        #             logger.debug(
        #                 f"Refit [{dress_bone.name}][{bone_offset.position}]"
        #                 + f"[model={model_matrixes[0, dress_bone.name].position}]"
        #                 + f"[dress={dress_matrixes[0, dress_bone.name].position}]"
        #             )

        return dress

    def create_dress_fit_morphs(self, model: PmxModel, dress: PmxModel):
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

        dress_vertex_fitting_morph = Morph(name="VertexFitting")
        dress_vertex_fitting_morph.is_system = True
        dress_vertex_fitting_morph.morph_type = MorphType.VERTEX

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone([0], model)

        logger.info("フィッティングボーンモーフ：グローバルスケール計算", decoration=MLogger.Decoration.LINE)
        dress_offset_scales, dress_fit_scales = self.get_dress_global_bone_scale_offsets(model, dress, model_matrixes)
        # dress_offset_scales = {}
        # dress_fit_scales = {}

        logger.info("フィッティングボーンモーフ：ローカルスケール計算", decoration=MLogger.Decoration.LINE)
        dress_offset_local_scales = self.get_dress_local_bone_scale_offsets(model, dress, dress_offset_scales, model_matrixes)
        # dress_offset_local_scales = {}

        logger.info("フィッティングボーンモーフ：オフセット計算", decoration=MLogger.Decoration.LINE)
        dress_offset_positions, dress_offset_qqs = self.get_dress_global_bone_offsets(
            model, dress, dress_offset_scales, dress_offset_local_scales, model_matrixes
        )
        # dress_offset_positions = {}
        # dress_offset_qqs = {}

        # logger.info("フィッティング頂点オフセット計算", decoration=MLogger.Decoration.LINE)
        # dress_vertex_offset_positions = self.get_dress_vertex_offsets(
        #     model, dress, dress_offset_positions, dress_offset_qqs, dress_offset_scales, dress_offset_local_scales, model_matrixes
        # )

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

        # logger.info("フィッティング頂点モーフ追加", decoration=MLogger.Decoration.LINE)

        # dress_vertex_count = len(dress.vertices)
        # for dress_vertex in dress.vertices:
        #     if dress_vertex.index not in dress_vertex_offset_positions:
        #         continue

        #     dress_vertex_fitting_morph.offsets.append(
        #         VertexMorphOffset(
        #             dress_vertex.index,
        #             position=dress_vertex_offset_positions[dress_vertex.index],
        #         )
        #     )

        #     logger.count(
        #         "-- 頂点オフセット",
        #         index=dress_vertex.index,
        #         total_index_count=dress_vertex_count,
        #         display_block=100,
        #     )

        #     logger.info(
        #         "-- 頂点モーフ [{v}][移動={p}]",
        #         v=dress_vertex.index,
        #         p=dress_vertex_offset_positions[dress_vertex.index],
        #     )

        # dress.morphs.append(dress_vertex_fitting_morph)

    def get_dress_global_bone_scale_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        model_matrixes: VmdBoneFrameTrees,
    ) -> tuple[dict[int, MVector3D], dict[int, MVector3D]]:
        dress_standard_count = len(STANDARD_BONE_NAMES)

        # 衣装の初期姿勢を求める
        dress_matrixes = VmdMotion().animate_bone([0], dress, append_ik=False)

        dress_scale_values: dict[str, list[float]] = {}

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

            if bone_name == "下半身" or ("足首" in bone_name):
                # 下半身と足首は地面からのY距離で決める
                dress_fit_length_scale = model_bone_position.y / (dress_bone_position.y or 1)
            elif bone_name == "上半身":
                # 上半身は首根元までのY距離で決める
                dress_fit_length_scale = (model_matrixes[0, "首根元"].position.y - model_bone_position.y) / (
                    (dress_matrixes[0, "首根元"].position.y - dress_bone_position.y) or 1
                )
            else:
                dress_fit_length_scale = (model_tail_position - model_bone_position).length() / (
                    (dress_tail_position - dress_bone_position).length() or 1
                )

            if bone_setting.category not in dress_scale_values:
                dress_scale_values[bone_setting.category] = []
            dress_scale_values[bone_setting.category].append(dress_fit_length_scale)

        dress_filtered_scale_values: dict[str, float] = {}
        for category, dress_category_scale_values in dress_scale_values.items():
            # 中央値と標準偏差を計算
            median_local_scales = np.median(dress_category_scale_values)
            std_local_scales = np.std(dress_category_scale_values)

            filtered_scales = np.array(dress_category_scale_values)[
                (dress_category_scale_values >= median_local_scales - (std_local_scales * 1.5))
                & (dress_category_scale_values <= median_local_scales + (std_local_scales * 1.5))
            ]

            dress_filtered_scale_values[category] = np.min(filtered_scales)

            logger.debug(f"グローバルスケール [{category}][{np.round(filtered_scales, decimals=3)}][{dress_filtered_scale_values[category]:.3f}]")

        dress_offset_scales: dict[int, MVector3D] = {}
        dress_fit_scales: dict[int, MVector3D] = {}

        for i, (bone_name, bone_setting) in enumerate(list(STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones):
                # 衣装にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]

            if not dress_bone.is_scalable_standard:
                continue

            dress_fit_length_scale = dress_filtered_scale_values[bone_setting.category]
            dress_fit_scale = MVector3D(dress_fit_length_scale, dress_fit_length_scale, dress_fit_length_scale)

            # 親をキャンセルしていく
            dress_offset_scale = dress_fit_scale.copy()
            for tree_bone_index in reversed(dress.bone_trees[bone_name].indexes[:-1]):
                dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales.get(tree_bone_index, MVector3D(1, 1, 1))

            dress_fit_scales[dress_bone.index] = dress_fit_scale
            dress_offset_scales[dress_bone.index] = dress_offset_scale

            logger.debug("-- -- グローバルスケール [{b}][{f:.3f}({o:.3f})]", b=bone_name, f=dress_fit_scale.x, o=dress_offset_scale.x)

        return dress_offset_scales, dress_fit_scales

    def get_dress_global_bone_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_offset_scales: dict[int, MVector3D],
        dress_offset_local_scales: dict[int, MVector3D],
        model_matrixes: VmdBoneFrameTrees,
    ) -> tuple[dict[int, MVector3D], dict[int, MQuaternion]]:
        dress_standard_count = len(STANDARD_BONE_NAMES)

        dress_motion = VmdMotion()
        dress_offset_positions: dict[int, MVector3D] = {}
        dress_offset_qqs: dict[int, MQuaternion] = {}

        z_direction = MVector3D(0, 0, -1)
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

            # キーフレとしてスケーリング追加
            sbf = dress_motion.bones[dress_bone.name][0]
            sbf.scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            sbf.local_scale = dress_offset_local_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            dress_motion.bones[dress_bone.name].append(sbf)

            if dress_bone.ik_target_indexes:
                # IKリンクボーンの位置を補正する
                dress_ik_bone = dress.bones[dress_bone.ik_target_indexes[0]]
                dress_ik_link_start_bone = dress.bones[dress_ik_bone.ik.links[-1].bone_index]
                dress_ik_target_bone = dress.bones[dress_ik_bone.ik.bone_index]

                for dress_ik_link in dress_ik_bone.ik.links[:-1]:
                    dress_ik_link_bone = dress.bones[dress_ik_link.bone_index]
                    if STANDARD_BONE_NAMES[dress_ik_link_bone.name].translatable:
                        matrixes = dress_motion.animate_bone([0], model, [bone_name], append_ik=False)

                        # 変形後の位置
                        deformed_start_position = matrixes[0, dress_ik_link_start_bone.name].position
                        deformed_link_position = matrixes[0, dress_ik_link_bone.name].position
                        deformed_target_position = matrixes[0, dress_ik_target_bone.name].position
                        # 変形前の位置
                        original_start_position = dress.bones[dress_ik_link_start_bone.name].position
                        original_link_position = dress.bones[dress_ik_link_bone.name].position
                        original_target_position = dress.bones[dress_ik_target_bone.name].position

                        original_link_ratio = (original_link_position - original_start_position).one() / (
                            original_target_position - original_start_position
                        ).one()
                        deformed_refit_link_position = deformed_start_position + (
                            (deformed_target_position - deformed_start_position) * original_link_ratio
                        )

                        offset_link_position = deformed_refit_link_position - deformed_link_position
                        if 0 > offset_link_position.z:
                            # ひざが前に出る方向の補正のみ行う
                            dress_offset_positions[dress_ik_link_bone.index].z += offset_link_position.z / 4

                            # キーフレ更新
                            mbf = dress_motion.bones[dress_ik_link_bone.name][0]
                            mbf.position = dress_offset_positions[dress_ik_link_bone.index].copy()
                            dress_motion.bones[dress_ik_link_bone.name].append(mbf)

                            logger.debug(
                                f"-- -- 移動追加オフセット[{dress_ik_link_bone.name}][{offset_link_position}]"
                                + f"[original={deformed_refit_link_position}][deform={deformed_link_position}]"
                            )
                # matrixes = dress_motion.animate_bone([0], model, [bone_name], append_ik=False)
                # deformed_ik_position = matrixes[0, dress_ik_bone.name].position
                # deformed_target_position = matrixes[0, dress_ik_target_bone.name].position

                # # offset_target_position = deformed_ik_position - deformed_target_position
                # # dress_offset_position += offset_target_position

                # # logger.debug(
                # #     f"-- -- 移動追加オフセット[{dress_ik_target_bone.name}][{offset_link_position}]"
                # #     + f"[ik={deformed_ik_position}][fk={deformed_target_position}]"
                # # )

                # # FKボーンの位置：自分の方向
                # dress_x_direction = (matrixes[0, dress_ik_link_bone.name].global_matrix.inverse() * deformed_target_position).normalized()
                # dress_y_direction = dress_x_direction.cross(z_direction)
                # dress_slope_qq = MQuaternion.from_direction(dress_x_direction, dress_y_direction)

                # # IKボーンの位置：自分の方向
                # model_x_direction = (matrixes[0, dress_ik_link_bone.name].global_matrix.inverse() * deformed_ik_position).normalized()
                # model_y_direction = model_x_direction.cross(z_direction)
                # model_slope_qq = MQuaternion.from_direction(model_x_direction, model_y_direction)

                # dress_offset_qq = model_slope_qq * dress_slope_qq.inverse()

                # for tree_bone_index in reversed(dress.bone_trees[dress_ik_link_bone.name].indexes[:-1]):
                #     # 自分より親は逆回転させる
                #     dress_offset_qq *= dress_offset_qqs.get(tree_bone_index, MQuaternion()).inverse()

                # dress_offset_qqs[dress_ik_link_bone.index] *= dress_offset_qq

                # # キーフレとして追加
                # qbf = dress_motion.bones[dress_ik_link_bone.name][0]
                # qbf.rotation = dress_offset_qqs[dress_ik_link_bone.index].copy()
                # dress_motion.bones[dress_ik_link_bone.name].append(qbf)

                # logger.debug(
                #     f"-- -- 回転補正オフセット[{dress_ik_link_bone.name}][{dress_offset_qqs[dress_ik_link_bone.index].to_euler_degrees()}]"
                #     + f"[ik={deformed_ik_position}][fk={deformed_target_position}]"
                # )

            if dress_bone.is_translatable_standard:
                # 移動計算 ------------------
                # if dress_bone.is_ik:
                #     # IK の場合、FKに合わせる
                #     fk_dress_bone = dress.bones[dress_bone.ik.bone_index]
                #     model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                #         dress, fk_dress_bone, STANDARD_BONE_NAMES[fk_dress_bone.name], motion=dress_motion, append_ik=False
                #     )
                #     dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                #         dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
                #     )
                if dress_bone.is_leg_d:
                    # 足D系列は足FKに揃える
                    fk_dress_bone = dress.bones[dress_bone.effect_index]
                    model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                        dress, fk_dress_bone, STANDARD_BONE_NAMES[fk_dress_bone.name], motion=dress_motion, append_ik=False
                    )
                    dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                        dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
                    )
                else:
                    model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                        model, model_bone, bone_setting, matrixes=model_matrixes
                    )
                    dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                        dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
                    )

                dress_offset_position = model_bone_position - dress_bone_position

                # if dress_bone.is_leg_d:
                #     # 足D系列は足FKに揃える
                #     dress_offset_position = dress_offset_positions[dress_bone.effect_index].copy()

                dress_offset_positions[dress_bone.index] = dress_offset_position

                # キーフレとして追加
                mbf = dress_motion.bones[dress_bone.name][0]
                mbf.position = dress_offset_position
                dress_motion.bones[dress_bone.name].append(mbf)

                logger.debug(
                    f"-- -- 移動オフセット[{dress_bone.name}][{dress_offset_position}][model={model_bone_position}][dress={dress_bone_position}]"
                )

            if dress_bone.is_ik and STANDARD_BONE_NAMES[dress.bones[dress_bone.ik.bone_index].name].translatable:
                # IKの場合、FKターゲットをIKの位置に合わせる
                fk_dress_bone = dress.bones[dress_bone.ik.bone_index]
                model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                    dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
                )
                dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                    dress, fk_dress_bone, STANDARD_BONE_NAMES[fk_dress_bone.name], motion=dress_motion, append_ik=False
                )

                offset_target_position = model_bone_position - dress_bone_position
                dress_offset_positions[fk_dress_bone.index] += offset_target_position

                # キーフレ更新
                mbf = dress_motion.bones[fk_dress_bone.name][0]
                mbf.position = dress_offset_positions[fk_dress_bone.index].copy()
                dress_motion.bones[fk_dress_bone.name].append(mbf)

                logger.debug(
                    f"-- -- 移動追加オフセット[{fk_dress_bone.name}][{offset_target_position}]"
                    + f"[IK={model_bone_position}][FK={dress_bone_position}]"
                )

            if dress_bone.is_rotatable_standard:
                # 回転計算 ------------------

                if dress_bone.is_leg_d:
                    # 足DはFKの向きに合わせる
                    fk_dress_bone = dress.bones[dress_bone.effect_index]
                    model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                        dress,
                        fk_dress_bone,
                        STANDARD_BONE_NAMES[fk_dress_bone.name],
                        motion=dress_motion,
                        append_ik=False,
                    )
                    dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                        dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
                    )
                else:
                    model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(
                        model, model_bone, bone_setting, matrixes=model_matrixes
                    )
                    dress_bone_matrix, dress_bone_position, dress_tail_position = self.get_tail_position(
                        dress, dress_bone, bone_setting, motion=dress_motion, append_ik=False
                    )

                if model_tail_position and dress_tail_position:
                    # 衣装：自分の方向
                    dress_x_direction = (dress_bone_matrix.inverse() * dress_tail_position).normalized()
                    dress_y_direction = dress_x_direction.cross(z_direction)
                    dress_slope_qq = MQuaternion.from_direction(dress_x_direction, dress_y_direction)

                    # 人物：自分の方向
                    model_x_direction = (model_bone_matrix.inverse() * model_tail_position).normalized()
                    model_y_direction = model_x_direction.cross(z_direction)
                    model_slope_qq = MQuaternion.from_direction(model_x_direction, model_y_direction)

                    # モデルのボーンの向きに衣装を合わせる
                    if "足首" in dress_bone.name:
                        # 足首は親のキャンセルだけ行う
                        dress_offset_qq = MQuaternion()
                    else:
                        dress_offset_qq = model_slope_qq * dress_slope_qq.inverse()

                    for tree_bone_index in reversed(dress.bone_trees[bone_name].indexes[:-1]):
                        # 自分より親は逆回転させる
                        dress_offset_qq *= dress_offset_qqs.get(tree_bone_index, MQuaternion()).inverse()

                    # if dress_bone.is_leg_d:
                    #     # 足D系列は足FKに揃える
                    #     dress_offset_qq = dress_offset_qqs[dress.bones[dress_bone.name[:-1]].index].copy()

                    dress_offset_qqs[dress_bone.index] = dress_offset_qq

                    # キーフレとして追加
                    qbf = dress_motion.bones[dress_bone.name][0]
                    qbf.rotation = dress_offset_qq
                    dress_motion.bones[dress_bone.name].append(qbf)

                    logger.debug(
                        f"-- -- 回転オフセット[{dress_bone.name}][{dress_offset_qq.to_euler_degrees()}]"
                        + f"[model={model_bone_position}][dress={dress_bone_position}]"
                    )
            # elif dress_bone.has_fixed_axis:
            #     # 軸固定の場合、軸を再計算する
            #     if dress_bone.name[-1].isdigit():
            #         # 分散ボーンの場合、親をコピー
            #         dress.bones[dress_bone.name].fixed_axis = model.bones[dress_bone.name[-1]].fixed_axis.copy()
            #         dress.bones[dress_bone.name].corrected_fixed_axis = model.bones[dress_bone.name[-1]].corrected_fixed_axis.copy()
            #     else:
            #         # 捩りボーンそのものであれば、そのままコピー
            #         dress.bones[dress_bone.name].fixed_axis = model.bones[dress_bone.name].fixed_axis.copy()
            #         dress.bones[dress_bone.name].corrected_fixed_axis = model.bones[dress_bone.name].corrected_fixed_axis.copy()

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

    def get_dress_local_bone_scale_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_offset_scales: dict[int, MVector3D],
        model_matrixes: VmdBoneFrameTrees,
    ) -> dict[int, MVector3D]:
        dress_motion = VmdMotion()
        dress_offset_local_scales: dict[int, MVector3D] = {}

        # これまでのフィッティングパラを適用したモーションを生成する
        for dress_bone in dress.bones:
            bf = dress_motion.bones[dress_bone.name][0]
            bf.scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            dress_motion.bones[dress_bone.name].append(bf)

        # 衣装の初期姿勢を求める
        dress_matrixes = dress_motion.animate_bone([0], dress)

        dress_local_positions: dict[str, np.ndarray] = {}
        model_local_positions: dict[str, np.ndarray] = {}
        for bone_name in (
            "上半身",
            "上半身2",
            "上半身3",
            "下半身",
            "右腕",
            "右腕捩",
            "右腕捩1",
            "右腕捩2",
            "右腕捩3",
            "右ひじ",
            "右手捩",
            "右手捩1",
            "右手捩2",
            "右手捩3",
            "左腕",
            "左腕捩",
            "左腕捩1",
            "左腕捩2",
            "左腕捩3",
            "左ひじ",
            "左手捩",
            "左手捩1",
            "左手捩2",
            "左手捩3",
            "右足",
            "右足D",
            "右ひざ",
            "右ひざD",
            "左足",
            "左足D",
            "左ひざ",
            "左ひざD",
            "左親指２",
            "左人指２",
            "左人指３",
            "左中指２",
            "左中指３",
            "左薬指２",
            "左薬指３",
            "左小指２",
            "左小指３",
            "右親指２",
            "右人指２",
            "右人指３",
            "右中指２",
            "右中指３",
            "右薬指２",
            "右薬指３",
            "右小指２",
            "右小指３",
        ):
            bone_setting = STANDARD_BONE_NAMES[bone_name]

            if bone_name in model.bones:
                model_bone = model.bones[bone_name]
                model_vertices = set(model.vertices_by_bones.get(model.bones[bone_name].index, []))
                if model_vertices:
                    model_deformed_local_positions = self.get_deformed_local_positions(
                        model, model_bone, bone_setting, model_vertices, model_matrixes
                    )

                    if bone_setting.category not in model_local_positions:
                        model_local_positions[bone_setting.category] = model_deformed_local_positions
                    else:
                        model_local_positions[bone_setting.category] = np.vstack(
                            (model_local_positions[bone_setting.category], model_deformed_local_positions)
                        )

            if bone_name in dress.bones:
                dress_bone = dress.bones[bone_name]
                dress_vertices = set(dress.vertices_by_bones.get(dress.bones[bone_name].index, []))
                if dress_vertices:
                    dress_deformed_local_positions = self.get_deformed_local_positions(
                        dress, dress_bone, bone_setting, dress_vertices, dress_matrixes
                    )

                    if bone_setting.category not in dress_local_positions:
                        dress_local_positions[bone_setting.category] = dress_deformed_local_positions
                    else:
                        dress_local_positions[bone_setting.category] = np.vstack(
                            (dress_local_positions[bone_setting.category], dress_deformed_local_positions)
                        )

        dress_local_scales: dict[str, MVector3D] = {}
        for category in dress_local_positions.keys():
            if category not in model_local_positions:
                continue

            # フィルタした値
            model_filtered_local_positions = self.filter_values(np.abs(model_local_positions[category]))
            dress_filtered_local_positions = self.filter_values(np.abs(dress_local_positions[category]))

            model_local_position = np.median(model_filtered_local_positions, axis=0)
            dress_local_position = np.median(dress_filtered_local_positions, axis=0)

            local_scale = MVector3D(*model_local_position).one() / MVector3D(*dress_local_position).one()
            local_scale_value = np.max([local_scale.y, local_scale.z])

            dress_local_scales[category] = MVector3D(1.0, local_scale_value, local_scale_value)

            logger.debug(
                f"ローカルスケール [{category}][{dress_local_scales[category]}][model={model_local_position}]"
                + f"[dress={dress_local_position}][scale={local_scale}]"
            )

        for i, (bone_name, bone_setting) in enumerate(list(STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones):
                # 衣装にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]

            if not dress_bone.is_scalable_standard or bone_setting.category not in dress_local_scales:
                continue

            dress_offset_local_scales[dress_bone.index] = dress_local_scales[bone_setting.category].copy()

        return dress_offset_local_scales

    def get_deformed_positions(
        self,
        model: PmxModel,
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
            model_deformed_vertices.append((MMatrix4x4(*mat.flatten()) * vertex.position).vector)

        return np.array(model_deformed_vertices)

    def get_deformed_local_positions(
        self,
        model: PmxModel,
        bone: Bone,
        bone_setting: BoneSetting,
        model_vertices: set[int],
        matrixes: VmdBoneFrameTrees,
        is_filter: bool = False,
        is_z_positive: bool = False,
    ) -> np.ndarray:
        model_deformed_vertices = self.get_deformed_positions(model, model_vertices, matrixes)

        if is_z_positive:
            # Z方向が＋のもののみ対象とする場合、抽出
            model_deformed_vertices = model_deformed_vertices[model_deformed_vertices[..., 2] >= 0]

        model_bone_matrix, model_bone_position, model_tail_position = self.get_tail_position(model, bone, bone_setting, matrixes=matrixes)

        if bone.name in ("左胸", "右胸", "左足首", "右足首", "左足首D", "右足首D", "左足先EX", "右足先EX"):
            model_tail_position = model_bone_position + MVector3D(0, 0, -1)

        model_local_positions = calc_local_positions(
            model_deformed_vertices,
            model_bone_position,
            model_tail_position,
        )

        if not is_filter:
            return model_local_positions

        return self.filter_values(model_local_positions)

    def filter_values(self, values: np.ndarray) -> np.ndarray:
        """一定範囲内の値だけ取得する"""

        # 中央値と標準偏差を計算
        median_values = np.median(values, axis=0)
        std_values = np.std(values, axis=0)

        # 中央値から標準偏差の一定範囲までの値を取得
        filtered_values = values[
            (np.all(values >= median_values - (std_values * 2), axis=1)) & (np.all(values <= median_values + (std_values * 2), axis=1))
        ]

        return filtered_values

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
            if isinstance(bone_setting.relatives, Iterable):
                return (
                    matrixes[0, bone.name].global_matrix,
                    matrixes[0, bone.name].position,
                    MVector3D(),
                )

            return (
                matrixes[0, bone.name].global_matrix,
                matrixes[0, bone.name].position,
                matrixes[0, bone.name].global_matrix * bone_setting.relatives,
            )
        return MMatrix4x4(), MVector3D(), MVector3D()

    def get_dress_vertex_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_offset_positions: dict[int, MVector3D],
        dress_offset_qqs: dict[int, MQuaternion],
        dress_offset_scales: dict[int, MVector3D],
        dress_offset_local_scales: dict[int, MVector3D],
        model_matrixes: VmdBoneFrameTrees,
    ):
        dress_motion = VmdMotion()
        dress_vertex_offset_positions: dict[int, MVector3D] = {}

        # これまでのフィッティングパラを適用したモーションを生成する
        for dress_bone in dress.bones:
            bf = dress_motion.bones[dress_bone.name][0]
            bf.position = dress_offset_positions.get(dress_bone.index, MVector3D())
            bf.rotation = dress_offset_qqs.get(dress_bone.index, MQuaternion())
            bf.scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            bf.local_scale = dress_offset_local_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            dress_motion.bones[dress_bone.name].append(bf)

        # 衣装の初期姿勢を求める
        dress_matrixes = dress_motion.animate_bone([0], dress)

        dress_vertices: set[int] = set([])
        model_vertices: set[int] = set([])

        trunk_bone_names = ("上半身", "上半身2", "上半身3", "下半身", "首")

        for bone_name in trunk_bone_names:
            if bone_name in dress.bones:
                dress_vertices |= set(dress.vertices_by_bones.get(dress.bones[bone_name].index, []))
            if bone_name in model.bones:
                model_vertices |= set(model.vertices_by_bones.get(model.bones[bone_name].index, []))

        if not (dress_vertices and model_vertices):
            return

        # 変形適用結果頂点位置
        model_deformed_vertices = self.get_deformed_positions(model, model_vertices, model_matrixes)
        dress_deformed_vertices = self.get_deformed_positions(dress, dress_vertices, dress_matrixes)

        dress_z_distances: dict[int, float] = {}

        for dress_vertex_index, dress_vertex_position in zip(dress_vertices, dress_deformed_vertices):
            # XY平面かつ同じZ方向で近い人物側の頂点を見つける
            model_deformed_sign_vertices = model_deformed_vertices[
                np.sign(model_deformed_vertices[..., 2]) == np.sign(dress_vertex_position[2])
            ]
            dress_xy_distances = np.linalg.norm((model_deformed_sign_vertices[..., :2] - dress_vertex_position[:2]), ord=2, axis=1)
            model_nearest_position = model_deformed_sign_vertices[np.argmin(dress_xy_distances)]
            # Z方向の距離差分を頂点ごとに保持
            dress_z_distances[dress_vertex_index] = model_nearest_position[2] - dress_vertex_position[2]

        dress_bone_z_distances: dict[int, list[float]] = {}
        for bone_name in trunk_bone_names:
            if bone_name not in dress.bones:
                continue
            dress_bone = dress.bones[bone_name]
            # 該当ボーンにウェイトが乗っている頂点INDEXリスト
            dress_bone_vertex_indexes = dress.vertices_by_bones.get(dress_bone.index, [])
            # 該当ボーンとのZ距離差
            dress_bone_z_distances[dress_bone.index] = [
                z_distance for vertex_index, z_distance in dress_z_distances.items() if vertex_index in dress_bone_vertex_indexes
            ]

        # 衣装側のZ方向の調整中央値
        dress_bone_median_z_distances: dict[int, float] = dict(
            [(bone_index, float(np.median(z_distances))) for bone_index, z_distances in dress_bone_z_distances.items()]
        )

        # ウェイトを元にZ方向のフィッティング値を求める
        for vertex_index in dress_vertices:
            dress_vertex = dress.vertices[vertex_index]
            fit_z = 0.0
            for deform_bone_index, deform_bone_weight in zip(dress_vertex.deform.indexes, dress_vertex.deform.weights):
                fit_z += dress_bone_median_z_distances.get(deform_bone_index, 0) * deform_bone_weight
            dress_vertex_offset_positions[vertex_index] = MVector3D(0, 0, fit_z)

        return dress_vertex_offset_positions


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
FIT_INDIVIDUAL_BONE_NAMES = {
    __("下半身"): (("下半身",), [], False),
    __("上半身"): (("上半身",), (__("下半身"), __("上半身2"), __("首")), False),
    __("上半身2"): (("上半身2", "上半身3"), (__("首"),), False),
    __("首"): (("首",), [], False),
    __("頭"): (("頭",), [], False),
    __("肩"): (("右肩", "左肩"), [], False),
    __("腕"): (("右腕", "左腕"), (__("ひじ"), __("手のひら")), False),
    __("ひじ"): (("右ひじ", "左ひじ"), (__("手のひら"),), False),
    __("手のひら"): (
        (
            "右手首",
            "左手首",
            "左親指０",
            "左親指１",
            "左親指２",
            "左人指１",
            "左人指２",
            "左人指３",
            "左中指１",
            "左中指２",
            "左中指３",
            "左薬指１",
            "左薬指２",
            "左薬指３",
            "左小指１",
            "左小指２",
            "左小指３",
            "右親指０",
            "右親指１",
            "右親指２",
            "右人指１",
            "右人指２",
            "右人指３",
            "右中指１",
            "右中指２",
            "右中指３",
            "右薬指１",
            "右薬指２",
            "右薬指３",
            "右小指１",
            "右小指２",
            "右小指３",
        ),
        [],
        False,
    ),
    __("足"): (("右足", "左足", "右足D", "左足D"), (__("ひざ"), __("足首")), True),
    __("ひざ"): (("右ひざ", "左ひざ", "右ひざD", "左ひざD"), (__("足首"),), True),
    __("足首"): (("右足首", "左足首", "右足首D", "左足首D"), [], True),
}
