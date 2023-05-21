import os

import numpy as np

from mlib.base.base import VecAxis
from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import MQuaternion, MVector3D, MVector4D, intersect_line_plane
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import STANDARD_BONE_NAMES, BoneMorphOffset, MaterialMorphCalcMode, MaterialMorphOffset, Morph, MorphType
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

    def add_mismatch_bones(self, model: PmxModel, dress: PmxModel):
        """準標準ボーンの不足分を追加"""
        # 必ず追加するボーン
        add_bone_names = {"全ての親", "上半身2", "右腕捩", "左腕捩", "右手捩", "左手捩", "右足D", "左足D", "右ひざD", "左ひざD", "右足首D", "左足首D", "右足先EX", "左足先EX"}

        # 準標準ボーンで足りないボーン名を抽出
        short_model_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(model.bones.names) | add_bone_names
        short_dress_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(dress.bones.names) | add_bone_names

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

        # 人物の初期姿勢を求める
        model_matrixes = VmdMotion().bones.get_matrix_by_indexes([0], model.bones.tail_bone_names, model)

        model_inserted_bone_names = []
        for bone_name in STANDARD_BONE_NAMES.keys():
            if bone_name in short_mismatch_model_bone_names:
                if model.insert_standard_bone(bone_name, model_matrixes):
                    model_inserted_bone_names.append(bone_name)
                    logger.info("-- -- 人物: 準標準ボーン追加: {b}", b=bone_name)

        if model_inserted_bone_names:
            model.setup()
            model.replace_standard_weights(model_inserted_bone_names)
            logger.info("-- 人物: 再セットアップ")

        # 衣装の初期姿勢を求める
        dress_matrixes = VmdMotion().bones.get_matrix_by_indexes([0], dress.bones.tail_bone_names, dress)

        dress_inserted_bone_names = []
        for bone_name in STANDARD_BONE_NAMES.keys():
            if bone_name in short_mismatch_dress_bone_names:
                if dress.insert_standard_bone(bone_name, dress_matrixes):
                    dress_inserted_bone_names.append(bone_name)
                    logger.info("-- -- 衣装: 準標準ボーン追加: {b}", b=bone_name)

        # if "頭" in dress.bones:
        #     # 頭ボーンがある場合、頭部装飾ボーンを追加する
        #     head_accessory_bone = Bone(name="頭部装飾", index=dress.bones["頭"].index + 1)
        #     head_accessory_bone.parent_index = dress.bones["頭"].index
        #     head_accessory_bone.position = dress.bones["頭"].position
        #     head_accessory_bone.bone_flg = BoneFlg.CAN_MANIPULATE | BoneFlg.CAN_ROTATE | BoneFlg.CAN_TRANSLATE | BoneFlg.IS_VISIBLE
        #     dress.insert_bone(head_accessory_bone)
        #     dress_inserted_bone_names.append("頭部装飾")
        #     dress.setup_bone(dress.bones["頭"])
        #     dress.setup_bone(head_accessory_bone)

        # if dress_inserted_bone_names:
        #     dress.setup()
        #     dress.replace_standard_weights(dress_inserted_bone_names)
        #     if "頭部装飾" in dress_inserted_bone_names:
        #         logger.info("フィッティング用ウェイト別頂点取得（衣装:頭部装飾）")
        #         dress_vertices_by_bones = dress.get_vertices_by_bone()
        #         replaced_bone_map = dict([(b.index, b.index) for b in dress.bones])
        #         replaced_bone_map[dress.bones["頭"].index] = dress.bones["頭部装飾"].index
        #         for vidx in dress_vertices_by_bones.get("頭", []):
        #             v = dress.vertices[vidx]
        #             v.deform.indexes = np.vectorize(replaced_bone_map.get)(v.deform.indexes)

        #     logger.info("-- 衣装: 再セットアップ")

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

    def replace_upper2(self, model: PmxModel, dress: PmxModel):
        """上半身2のボーン置き換え"""
        replace_bone_names = ["上半身", "首根元", "上半身2"]
        if not (model.bones.exists(replace_bone_names) and model.bones.exists(replace_bone_names)):
            return model, dress, []

        logger.info("フィッティング用ウェイト別頂点取得（衣装）")
        dress_vertices_by_bones = dress.get_vertices_by_bone()

        # 一旦衣装の置き換えウェイトを元ボーンに置き換える
        replaced_bone_map = dict([(b.index, b.index) for b in dress.bones])
        replaced_bone_map[dress.bones["上半身2"].index] = dress.bones["上半身"].index
        for vidx in dress_vertices_by_bones.get("上半身2", []):
            v = dress.vertices[vidx]
            v.deform.indexes = np.vectorize(replaced_bone_map.get)(v.deform.indexes)

        model, dress, is_add = self.replace_bone_position_y(model, dress, *replace_bone_names)

        return model, dress, (["上半身2"] if is_add else [])

    def replace_neck(self, model: PmxModel, dress: PmxModel):
        """首のボーン置き換え"""
        replace_bone_names = ["上半身2", "頭", "首"]
        if not (model.bones.exists(replace_bone_names) and model.bones.exists(replace_bone_names)):
            return model, dress, []

        model, dress, is_add = self.replace_bone_position_y(model, dress, *replace_bone_names)

        return model, dress, (["首"] if is_add else [])

    def replace_shoulder(self, model: PmxModel, dress: PmxModel, direction: str):
        """肩のボーン置き換え"""
        replace_bone_names = ["首根元", "腕", f"{direction}肩"]
        if not (model.bones.exists(replace_bone_names) and model.bones.exists(replace_bone_names)):
            return model, dress, []

        model, dress, is_add = self.replace_bone_position_y(model, dress, *replace_bone_names)

        if is_add:
            if f"{direction}肩P" in dress.bones:
                dress.bones[f"{direction}肩P"].position = dress.bones[f"{direction}肩"].position.copy()

        return model, dress, ([f"{direction}肩"] if is_add else [])

    def replace_bone_position_y(self, model: PmxModel, dress: PmxModel, from_name: str, to_name: str, replace_name: str):
        """
        衣装のボーン位置を人物ボーン位置に合わせて配置を変える
        """
        if not (model.bones.exists([from_name, to_name, replace_name]) and dress.bones.exists([from_name, to_name, replace_name])):
            # ボーンが足りなかったら追加しない
            return model, dress, False

        model_from_pos = model.bones[from_name].position
        model_replace_pos = model.bones[replace_name].position
        model_to_pos = model.bones[to_name].position
        dress_from_pos = dress.bones[from_name].position
        dress_replace_pos = dress.bones[replace_name].position
        dress_to_pos = dress.bones[to_name].position

        # 元ボーン-置換ボーン ベースで求めた時の位置 ---------------

        # 元ボーン-置換ボーン:Y軸の縮尺
        from_replace_scale = ((model_replace_pos.y - model_from_pos.y) / (model_to_pos.y - model_from_pos.y)) / (
            (dress_replace_pos.y - dress_from_pos.y) / (dress_to_pos.y - dress_from_pos.y)
        )

        # 衣装の置換ボーンが配置されうる縮尺Yに合わせたXZ平面
        dress_from_new_replace_plane = MVector3D(
            dress_replace_pos.x,
            dress_from_pos.y + ((dress_replace_pos.y - dress_from_pos.y) * from_replace_scale),
            dress_replace_pos.z,
        )

        # 衣装の置換ボーンの位置を求め直す
        dress_from_new_replace_pos = intersect_line_plane(
            dress_from_pos,
            dress_from_pos + (model_replace_pos - model_from_pos).normalized(),
            dress_from_new_replace_plane,
            MVector3D(0, 1, 0),
        )

        # 先ボーン-置換ボーン ベースで求めた時の位置 ---------------

        # Y軸の縮尺
        to_replace_scale = ((model_replace_pos.y - model_to_pos.y) / (model_from_pos.y - model_to_pos.y)) / (
            (dress_replace_pos.y - dress_to_pos.y) / (dress_from_pos.y - dress_to_pos.y)
        )

        # 衣装の置換ボーンが配置されうる縮尺Yに合わせたXZ平面
        dress_to_new_replace_plane = MVector3D(
            dress_replace_pos.x,
            dress_to_pos.y + ((dress_replace_pos.y - dress_to_pos.y) * to_replace_scale),
            dress_replace_pos.z,
        )

        # 衣装の置換ボーンの位置を求め直す
        dress_to_new_replace_pos = intersect_line_plane(
            dress_to_pos,
            (model_replace_pos - model_to_pos).normalized(),
            dress_to_new_replace_plane,
            MVector3D(0, -1, 0),
        )

        # 最終的な置換ボーンは元ボーン-置換ボーン,先ボーン-置換ボーンの中間とする
        dress.bones[replace_name].position = (dress_from_new_replace_pos + dress_to_new_replace_pos) / 2
        logger.info("衣装: {r}: 位置再計算: {u} → {p}", r=replace_name, u=dress_replace_pos, p=dress.bones[replace_name].position)

        return model, dress, True

    def replace_twist(self, model: PmxModel, dress: PmxModel, replaced_bone_names: list[str]):
        """腕捩・手捩のボーン置き換え"""

        replace_bone_names = [
            "右腕",
            "右ひじ",
            "右腕捩",
            "右腕捩1",
            "右腕捩2",
            "右腕捩3",
            "右手首",
            "右手捩",
            "右手捩1",
            "右手捩2",
            "右手捩3",
            "左腕",
            "左ひじ",
            "左腕捩",
            "左腕捩1",
            "左腕捩2",
            "左腕捩3",
            "左手首",
            "左手捩",
            "左手捩1",
            "左手捩2",
            "左手捩3",
        ]
        if not (model.bones.exists(replace_bone_names) and model.bones.exists(replace_bone_names)):
            return model, dress, []

        logger.info("フィッティング用ウェイト別頂点取得（衣装）")
        dress_vertices_by_bones = dress.get_vertices_by_bone()

        replace_bone_set = (
            ("右腕", "右ひじ", "右腕捩"),
            ("右ひじ", "右手首", "右手捩"),
            ("左腕", "左ひじ", "左腕捩"),
            ("左ひじ", "左手首", "左手捩"),
        )

        # 一旦衣装の置き換えウェイトを元ボーンに置き換える
        replaced_bone_map = dict([(b.index, b.index) for b in dress.bones])
        for from_name, to_name, replace_name in replace_bone_set:
            if replace_name in dress.bones and from_name and dress.bones:
                replaced_bone_map[dress.bones[replace_name].index] = dress.bones[from_name].index
            for no in range(1, 5):
                replace_twist_name = f"{replace_name}{no}"
                if replace_twist_name in dress.bones and replace_twist_name and dress.bones:
                    replaced_bone_map[dress.bones[replace_twist_name].index] = dress.bones[from_name].index

        # 捩り系の頂点リストを取得する
        dress_vertex_indexes = set([])
        for bone_name in [
            "右腕捩",
            "右腕捩1",
            "右腕捩2",
            "右腕捩3",
            "右手捩",
            "右手捩1",
            "右手捩2",
            "右手捩3",
            "左腕捩",
            "左腕捩1",
            "左腕捩2",
            "左腕捩3",
            "左手捩",
            "左手捩1",
            "左手捩2",
            "左手捩3",
        ]:
            dress_vertex_indexes |= set(dress_vertices_by_bones.get(bone_name, []))

        # 捩りにウェイトが乗っているのを元ボーンに置き換える
        for vidx in list(dress_vertex_indexes):
            v = dress.vertices[vidx]
            v.deform.indexes = np.vectorize(replaced_bone_map.get)(v.deform.indexes)

        for from_name, to_name, replace_name in replace_bone_set:
            # 捩りボーンそのもの
            model, dress, is_add = self.replace_bone_position_twist(model, dress, from_name, to_name, replace_name)
            if is_add:
                replaced_bone_names.append(replace_name)

            # 分散の付与ボーン
            for no in range(1, 5):
                model, dress, is_add = self.replace_bone_position_twist(model, dress, from_name, to_name, f"{replace_name}{no}")
                if is_add:
                    replaced_bone_names.append(replace_name)

        return model, dress, replaced_bone_names

    def replace_bone_position_twist(self, model: PmxModel, dress: PmxModel, from_name: str, to_name: str, replace_name: str):
        """
        衣装のボーン位置を人物ボーン位置に合わせて配置を変える(斜め)
        """
        if not (model.bones.exists([from_name, to_name, replace_name]) and dress.bones.exists([from_name, to_name, replace_name])):
            # ボーンが足りなかったら追加しない
            return model, dress, False

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
        dress_new_twist_pos = dress_from_pos + ((dress_replace_pos - dress_from_pos) * from_replace_scale)

        # 最終的な置換ボーンは元ボーン-置換ボーン,先ボーン-置換ボーンの中間とする
        dress.bones[replace_name].position = dress_new_twist_pos
        logger.info("衣装: {r}: 位置再計算: {u} → {p}", r=replace_name, u=dress_replace_pos, p=dress_new_twist_pos)

        return model, dress, True

    def create_dress_individual_bone_morphs(self, model: PmxModel, dress: PmxModel) -> PmxModel:
        """衣装個別フィッティング用ボーンモーフを作成"""

        for morph_name, _, refit_bone_names in FIT_INDIVIDUAL_BONE_NAMES:
            # 再調整用のモーフ追加
            morph = Morph(name=f"{__('調整')}:{__(morph_name)}:Refit")
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
                morph = Morph(name=f"{__('調整')}:{__(morph_name)}:{axis_name}")
                morph.is_system = True
                morph.morph_type = MorphType.BONE
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
                                local_qq=offset_qq,
                                local_scale=local_scale,
                            )
                        )
                dress.morphs.append(morph)

            logger.info("-- 個別調整ボーンモーフ [{m}]", m=morph_name)

        return dress

    def create_dress_fit_bone_morphs(self, model: PmxModel, dress: PmxModel) -> PmxModel:
        """衣装フィッティング用ボーンモーフを作成"""
        bone_fitting_morph = Morph(name="BoneFitting")
        bone_fitting_morph.is_system = True
        bone_fitting_morph.morph_type = MorphType.BONE
        bone_fitting_offsets: dict[int, BoneMorphOffset] = {}

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().bones.get_matrix_by_indexes([0], model.bones.tail_bone_names, model)

        logger.info("フィッティングスケール計算", decoration=MLogger.Decoration.LINE)
        dress_offset_scales, dress_fit_scales = self.get_dress_offset_scales(model, dress, model_matrixes)

        # dress_offset_scales: dict[int, MVector3D] = {}
        # dress_fit_scales: dict[int, MVector3D] = {}

        logger.info("フィッティングオフセット計算", decoration=MLogger.Decoration.LINE)
        dress, dress_offset_positions, dress_offset_qqs, dress_offset_scales = self.get_dress_offsets(
            model, dress, model_matrixes, dress_fit_scales, dress_offset_scales
        )

        # dress_offset_positions: dict[int, MVector3D] = {}
        # dress_offset_qqs: dict[int, MQuaternion] = {}

        logger.info("フィッティングボーンモーフ追加", decoration=MLogger.Decoration.LINE)

        for i, dress_bone in enumerate(dress.bones):
            if not (
                0 <= dress_bone.index
                and (dress_bone.index in dress_offset_positions or dress_bone.index in dress_offset_qqs or dress_bone.index in dress_offset_scales)
            ):
                continue
            dress_offset_position = dress_offset_positions.get(dress_bone.index, MVector3D())
            dress_offset_qq = dress_offset_qqs.get(dress_bone.index, MQuaternion())
            dress_offset_scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - MVector3D(1, 1, 1)
            dress_fit_scale = dress_fit_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - MVector3D(1, 1, 1)

            logger.info(
                "-- ボーンモーフ [{b}][移動={p}][回転={q}][縮尺:{o:.3f}({f:.3f})]",
                b=dress_bone.name,
                p=dress_offset_position,
                q=dress_offset_qq.to_euler_degrees(),
                o=dress_offset_scale.x,
                f=dress_fit_scale.x,
            )

            bone_fitting_offsets[dress_bone.index] = BoneMorphOffset(dress_bone.index, dress_offset_position, dress_offset_qq, dress_offset_scale)

            # if dress_bone.name in model.bones:
            #     # ローカル軸を合わせておく
            #     dress_bone.tail_relative_position = model.bones[dress_bone.name].tail_relative_position.copy()
            #     dress_bone.local_axis = model.bones[dress_bone.name].local_axis.copy()

        bone_fitting_morph.offsets = list(bone_fitting_offsets.values())
        dress.morphs.append(bone_fitting_morph)

        return dress

    def get_dress_offset_scales(self, model: PmxModel, dress: PmxModel, model_matrixes: VmdBoneFrameTrees) -> tuple[dict[int, MVector3D], dict[int, MVector3D]]:
        """衣装スケール計算"""
        dress_motion = VmdMotion()
        dress_offset_scales: dict[int, MVector3D] = {}
        dress_fit_scales: dict[int, MVector3D] = {}

        dress_trunk_fit_scales: list[float] = []
        for from_name, to_name in FIT_ROOT_BONE_NAMES + FIT_TRUNK_BONE_NAMES:
            if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                continue

            model_relative_position = (model_matrixes[0, to_name].position - model_matrixes[0, from_name].position).effective(rtol=0.05, atol=0.05).abs()
            dress_relative_position = (dress.bones[to_name].position - dress.bones[from_name].position).effective(rtol=0.05, atol=0.05).abs()

            dress_trunk_scale = model_relative_position.y / dress_relative_position.y
            dress_trunk_fit_scales.append(dress_trunk_scale)

        # スケール計算: 体幹
        dress_trunk_mean_scale = np.mean(dress_trunk_fit_scales)
        dress_trunk_fit_scale = MVector3D(dress_trunk_mean_scale, dress_trunk_mean_scale, dress_trunk_mean_scale)

        for from_name, to_name in FIT_TRUNK_BONE_NAMES:
            if not (from_name in dress.bones and from_name in model.bones):
                continue

            bf = dress_motion.bones[from_name][0]
            bf.scale = dress_trunk_fit_scale - MVector3D(1, 1, 1)
            dress_motion.bones[from_name].append(bf)

            dress_fit_scales[dress.bones[from_name].index] = dress_trunk_fit_scale
            dress_offset_scales[dress.bones[from_name].index] = dress_trunk_fit_scale.copy()

            logger.info("-- -- スケールオフセット [{b}][{s:.3f}]", b=from_name, s=dress_trunk_mean_scale)

        for scale_bone_name, scale_axis, measure_bone_names in FIT_EXTREMITIES_BONE_NAMES:
            dress_extremities_fit_scales: list[float] = []
            for from_name, to_name in measure_bone_names:
                if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                    continue

                # 親までをフィッティングさせた上で改めてボーン位置を求める
                dress_motion.bones.clear()
                dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [to_name], dress, append_ik=False)

                model_relative_position = (
                    (model_matrixes[0, from_name].matrix.inverse() * model_matrixes[0, to_name].position).effective(rtol=0.05, atol=0.05).abs()
                )
                dress_relative_position = (
                    (dress_matrixes[0, from_name].matrix.inverse() * dress_matrixes[0, to_name].position).effective(rtol=0.05, atol=0.05).abs()
                )

                # 計測対象軸を対象とする
                dress_extremities_fit_scales.append((model_relative_position / dress_relative_position).vector[scale_axis])

            if not dress_extremities_fit_scales:
                continue

            dress_min_scale = np.min(dress_extremities_fit_scales)
            dress_fit_scale = MVector3D(dress_min_scale, dress_min_scale, dress_min_scale)

            for from_name, to_name in measure_bone_names:
                if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                    continue

            # 親をキャンセルしていく
            dress_offset_scale = dress_fit_scale.copy()
            for parent_index in dress.bone_trees[to_name].indexes[:-1]:
                if parent_index in dress_offset_scales:
                    dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales[parent_index]

            bf = dress_motion.bones[scale_bone_name][0]
            bf.scale = dress_offset_scale - MVector3D(1, 1, 1)
            dress_motion.bones[scale_bone_name].append(bf)

            dress_fit_scales[dress.bones[scale_bone_name].index] = dress_fit_scale
            dress_offset_scales[dress.bones[scale_bone_name].index] = dress_offset_scale

            logger.info("-- -- スケールオフセット [{b}][{s:.3f}({o:.3f})]", b=scale_bone_name, s=dress_fit_scale.x, o=dress_offset_scale.x)

        # 足Dは足をコピーする
        for leg_d_name, leg_fk_name in (("左足D", "左足"), ("右足D", "右足")):
            if not (leg_d_name in dress.bones and leg_fk_name in dress.bones):
                continue

            leg_d_bone = dress.bones[leg_d_name]
            leg_fk_bone = dress.bones[leg_fk_name]

            dress_offset_scales[leg_d_bone.index] = dress_offset_scales[leg_fk_bone.index].copy()
            dress_fit_scales[leg_d_bone.index] = dress_fit_scales[leg_fk_bone.index].copy()

            bf = dress_motion.bones[leg_d_bone.name][0]
            bf.scale = dress_offset_scales[leg_d_bone.index] - MVector3D(1, 1, 1)
            dress_motion.bones[leg_d_bone.name].append(bf)

            logger.info("-- -- スケールオフセット [{b}][{s:.3f}({o:.3f})]", b=leg_d_name, s=dress_fit_scale.x, o=dress_offset_scale.x)

        return dress_offset_scales, dress_fit_scales

    def get_dress_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        model_matrixes: VmdBoneFrameTrees,
        dress_fit_scales: dict[int, MVector3D],
        dress_offset_scales: dict[int, MVector3D],
    ) -> tuple[PmxModel, dict[int, MVector3D], dict[int, MQuaternion], dict[int, MVector3D]]:
        dress_standard_count = len(STANDARD_BONE_NAMES)

        dress_motion = VmdMotion()
        dress_offset_qqs: dict[int, MQuaternion] = {}
        dress_offset_positions: dict[int, MVector3D] = {}

        z_direction = MVector3D(0, 0, -1)
        for i, (bone_name, bone_setting) in enumerate(list(STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones and bone_name in model.bones):
                # 人物と衣装のいずれかにボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]
            model_bone = model.bones[dress_bone.name]

            if dress_bone.is_system and bone_name not in ("足中心", "首根元"):
                # システムボーンはスルー
                continue

            logger.count(
                "-- オフセット計算",
                index=i,
                total_index_count=dress_standard_count,
                display_block=50,
            )

            tail_bone_names = [bname for bname in bone_setting.tails if bname in dress.bones and bname in model.bones]
            tail_bone_name = tail_bone_names[0] if tail_bone_names else None

            # 移動計算 ------------------

            dress_motion.bones.clear()
            dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [dress_bone.name], dress, append_ik=False)

            if dress_bone.is_ik:
                # IK系はFKの位置に合わせる
                fk_dress_bone = dress.bones[dress_bone.ik.bone_index]
                fk_dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [fk_dress_bone.name], dress, append_ik=False)

                dress_offset_position = dress_matrixes[0, dress_bone.name].matrix.inverse() * fk_dress_matrixes[0, fk_dress_bone.name].position
            elif dress_bone.is_leg_d:
                # 足D系列はFKの位置に合わせる
                if "D" == dress_bone.name[-1]:
                    fk_dress_bone = dress.bones[dress_bone.name[:-1]]
                    fk_dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [fk_dress_bone.name], dress, append_ik=False)
                    dress_offset_position = dress_matrixes[0, dress_bone.name].matrix.inverse() * fk_dress_matrixes[0, fk_dress_bone.name].position
                elif "足先EX" in dress_bone.name:
                    # 足先EXは動かさない
                    dress_offset_position = MVector3D()
            elif "つま先" in dress_bone.name:
                dress_offset_position = MVector3D()
            else:
                dress_offset_position = dress_matrixes[0, dress_bone.name].matrix.inverse() * model_matrixes[0, dress_bone.name].position

            # キーフレとして追加
            mbf = dress_motion.bones[dress_bone.name][0]
            mbf.position = dress_offset_position
            dress_motion.bones[dress_bone.name].append(mbf)

            dress_offset_positions[dress_bone.index] = dress_offset_position

            logger.debug(
                f"-- -- 移動オフセット[{dress_bone.name}][{dress_offset_position}]"
                + f"[m={model_matrixes[0, dress_bone.name].position}][d={dress_matrixes[0, dress_bone.name].position}]"
            )

            if not (dress_bone.can_translate or dress_bone.has_fixed_axis or dress_bone.is_ik or dress_bone.is_shoulder_p or dress_bone.is_ankle):
                # 移動可能、軸制限あり、IK、肩P系列、足首から先は回転スルー

                if isinstance(bone_setting.relative, list) and tail_bone_name and tail_bone_name in dress.bones and tail_bone_name in model.bones:
                    # ボーン設定が相対位置、末端ボーンがない、末端ボーンが衣装・人物のいずれかに無い場合、スルー

                    # 回転計算 ------------------

                    dress_motion.bones.clear()
                    dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [tail_bone_name], dress, append_ik=False)

                    # 衣装：自分の方向
                    dress_x_direction = (dress_matrixes[0, dress_bone.name].matrix.inverse() * dress_matrixes[0, tail_bone_name].position).normalized()
                    dress_y_direction = dress_x_direction.cross(z_direction)
                    dress_slope_qq = MQuaternion.from_direction(dress_x_direction, dress_y_direction)

                    # 人物：自分の方向
                    model_x_direction = (model_matrixes[0, model_bone.name].matrix.inverse() * model_matrixes[0, tail_bone_name].position).normalized()
                    model_y_direction = model_x_direction.cross(z_direction)
                    model_slope_qq = MQuaternion.from_direction(model_x_direction, model_y_direction)

                    # モデルのボーンの向きに衣装を合わせる
                    dress_fit_qq = model_slope_qq * dress_slope_qq.inverse()

                    for tree_bone_name in reversed(dress.bone_trees[bone_name].names[:-1]):
                        # 自分より親は逆回転させる
                        dress_fit_qq *= dress_offset_qqs.get(dress.bones[tree_bone_name].index, MQuaternion()).inverse()

                    dress_offset_qqs[dress_bone.index] = dress_fit_qq

                    # キーフレとして追加
                    bf = dress_motion.bones[dress_bone.name][0]
                    bf.rotation = dress_fit_qq
                    dress_motion.bones[dress_bone.name].append(bf)

                    logger.debug(f"-- -- 回転オフセット[{dress_bone.name}][{dress_fit_qq.to_euler_degrees()}]")

            dress_fit_scale = dress_fit_scales.get(dress_bone.index, MVector3D(1, 1, 1))
            dress_offset_scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1))

            # 事前計算していたスケールをキーフレとして追加
            bf = dress_motion.bones[dress_bone.name][0]
            bf.scale = dress_offset_scale - MVector3D(1, 1, 1)
            dress_motion.bones[dress_bone.name].append(bf)

            logger.debug(f"-- -- スケールオフセット[{dress_bone.name}][f={dress_fit_scale}][o={dress_offset_scale}]")

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

        return dress, dress_offset_positions, dress_offset_qqs, dress_offset_scales

    def refit_dress_morphs(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_morph_motion: VmdMotion,
        refit_bone_name: str,
    ) -> PmxModel:
        morph = dress.morphs[f"{__('調整')}:{__(refit_bone_name)}:Refit"]

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone(0, model)
        # 衣装は変形を加味する
        dress_matrixes = dress_morph_motion.animate_bone(0, dress)

        for offset in morph.offsets:
            bone_offset: BoneMorphOffset = offset
            dress_bone = dress.bones[bone_offset.bone_index]
            if dress_bone.is_ik:
                # IK系はFKの位置に合わせる
                fk_dress_bone = dress.bones[dress_bone.ik.bone_index]
                if dress_matrixes.exists(0, fk_dress_bone.name):
                    bone_offset.position2 = dress_matrixes[0, fk_dress_bone.name].position - dress_matrixes[0, dress_bone.name].position
            else:
                if model_matrixes.exists(0, dress_bone.name) and dress_matrixes.exists(0, dress_bone.name):
                    bone_offset.position2 = model_matrixes[0, dress_bone.name].position - dress_matrixes[0, dress_bone.name].position

        return dress


FIT_ROOT_BONE_NAMES = [
    ("足中心", "首根元"),
]

FIT_TRUNK_BONE_NAMES = [
    ("上半身", "首根元"),
    ("下半身", "足中心"),
]

FIT_EXTREMITIES_BONE_NAMES = [
    ("左腕", VecAxis.X, (("左腕", "左ひじ"), ("左ひじ", "左手首"))),
    ("左足", VecAxis.Y, (("左足", "左ひざ"), ("左ひざ", "左足首"))),
    ("右腕", VecAxis.X, (("右腕", "右ひじ"), ("右ひじ", "右手首"))),
    ("右足", VecAxis.Y, (("右足", "右ひざ"), ("右ひざ", "右足首"))),
]

FIT_FINGER_BONE_NAMES = [
    ("左親指１", VecAxis.X, (("左親指１", "左親指２"),)),
    ("左人指１", VecAxis.X, (("左人指１", "左人指２"), ("左人指２", "左人指３"))),
    ("左中指１", VecAxis.X, (("左中指１", "左中指２"), ("左中指２", "左中指３"))),
    ("左薬指１", VecAxis.X, (("左薬指１", "左薬指２"), ("左薬指２", "左薬指３"))),
    ("左小指１", VecAxis.X, (("左小指１", "左小指２"), ("左小指２", "左小指３"))),
    ("右親指１", VecAxis.X, (("右親指１", "右親指２"),)),
    ("右人指１", VecAxis.X, (("右人指１", "右人指２"), ("右人指２", "右人指３"))),
    ("右中指１", VecAxis.X, (("右中指１", "右中指２"), ("右中指２", "右中指３"))),
    ("右薬指１", VecAxis.X, (("右薬指１", "右薬指２"), ("右薬指２", "右薬指３"))),
    ("右小指１", VecAxis.X, (("右小指１", "右小指２"), ("右小指２", "右小指３"))),
]

# IKはFKの後に指定する事
FIT_INDIVIDUAL_BONE_NAMES = [
    (__("体幹"), ("上半身", "下半身"), ("上半身2", "足中心")),
    (__("下半身"), ("下半身",), ("足中心",)),
    (__("上半身"), ("上半身",), ("上半身2",)),
    (__("上半身2"), ("上半身2", "上半身3"), ("首根元",)),
    (__("胸"), ("左胸", "右胸"), []),
    (__("首"), ("首",), ("頭",)),
    (__("頭"), ("頭",), []),
    (__("頭部装飾"), ("頭部装飾",), []),
    (__("肩"), ("右肩", "左肩"), ("右肩C", "左肩C", "右腕", "左腕")),
    (__("腕"), ("右腕", "左腕"), ("右腕捩", "左腕捩", "右腕捩1", "左腕捩1", "右腕捩2", "左腕捩2", "右腕捩3", "左腕捩3", "右腕捩4", "左腕捩4", "右ひじ", "左ひじ")),
    (__("ひじ"), ("右ひじ", "左ひじ"), ("右手捩", "左手捩", "右手捩1", "左手捩1", "右手捩2", "左手捩2", "右手捩3", "左手捩3", "右手捩4", "左手捩4", "右手首", "左手首")),
    (__("手のひら"), ("右手首", "左手首"), []),
    (__("足"), ("右足", "左足", "右足D", "左足D"), ("右ひざ", "左ひざ", "右ひざD", "左ひざD")),
    (__("ひざ"), ("右ひざ", "左ひざ", "右ひざD", "左ひざD"), ("右足首", "左足首", "右足首D", "左足首D")),
    (__("足首"), ("右足首", "左足首", "右足首D", "左足首D"), ("右つま先EX", "左つま先EX", "右つま先", "左つま先", "右足ＩＫ", "右つま先ＩＫ", "左足ＩＫ", "左つま先ＩＫ", "右足IK親", "左足IK親")),
    (__("つま先"), ("右つま先EX", "左つま先EX", "右つま先", "左つま先"), ["右つま先ＩＫ", "左つま先ＩＫ"]),
]
