import os

import numpy as np

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import (
    MMatrix4x4,
    MQuaternion,
    MVector3D,
    MVector4D,
    MVectorDict,
    calc_local_positions,
    align_triangle,
    filter_values,
    transform_lattice,
)
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import (
    Bdef1,
    Bdef2,
    Bone,
    BoneMorphOffset,
    MaterialMorphCalcMode,
    MaterialMorphOffset,
    Morph,
    MorphType,
    VertexMorphOffset,
)
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdBoneFrame, VmdMorphFrame
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from service.usecase.dress_bone_setting import (
    DRESS_STANDARD_BONE_NAMES,
    DRESS_BONE_FITTING_NAME,
    DRESS_VERTEX_FITTING_NAME,
    DressBoneSetting,
    FIT_INDIVIDUAL_MORPH_NAMES,
)

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

    def insert_mismatch_bones(self, model: PmxModel, dress: PmxModel) -> None:
        """準標準ボーンの不足分を追加"""
        # 必ず追加するボーン
        add_bone_names = {
            "全ての親",
            "グルーブ",
            "腰",
            "上半身2",
            "左肩P",
            "右肩P",
            "右腕捩",
            "左腕捩",
            "右手捩",
            "左手捩",
            "右足D",
            "左足D",
            "右ひざD",
            "左ひざD",
            "右足首D",
            "左足首D",
            "右足先EX",
            "左足先EX",
        }

        not_target_bone_names = {
            "右目",
            "左目",
            "両目",
            "左親指０",
            "左親指１",
            "左親指２",
            "左親指先",
            "左人指１",
            "左人指２",
            "左人指３",
            "左人指先",
            "左中指１",
            "左中指２",
            "左中指３",
            "左中指先",
            "左薬指１",
            "左薬指２",
            "左薬指３",
            "左薬指先",
            "左小指１",
            "左小指２",
            "左小指３",
            "左小指先",
            "右親指０",
            "右親指１",
            "右親指２",
            "右親指先",
            "右人指１",
            "右人指２",
            "右人指３",
            "右人指先",
            "右中指１",
            "右中指２",
            "右中指３",
            "右中指先",
            "右薬指１",
            "右薬指２",
            "右薬指３",
            "右薬指先",
            "右小指１",
            "右小指２",
            "右小指３",
            "右小指先",
        }

        # 準標準ボーンで足りないボーン名を抽出
        short_model_bone_names = set(list(DRESS_STANDARD_BONE_NAMES.keys())) - set(model.bones.names) - not_target_bone_names
        short_dress_bone_names = set(list(DRESS_STANDARD_BONE_NAMES.keys())) - set(dress.bones.names) - not_target_bone_names

        # 両方の片方にしかないボーン名を抽出
        mismatch_bone_names = (short_model_bone_names ^ short_dress_bone_names) | add_bone_names

        # ミスマッチボーンで追加する必要のあるボーン名を抽出(順番を保持する)
        short_mismatch_model_bone_names = [
            bname for bname in DRESS_STANDARD_BONE_NAMES.keys() if bname in (mismatch_bone_names - set(model.bones.names))
        ]
        short_mismatch_dress_bone_names = [
            bname for bname in DRESS_STANDARD_BONE_NAMES.keys() if bname in (mismatch_bone_names - set(dress.bones.names))
        ]

        logger.info("人物: 追加候補ボーン: {b}", b=", ".join(short_mismatch_model_bone_names))
        logger.info("衣装: 追加候補ボーン: {b}", b=", ".join(short_mismatch_dress_bone_names))

        if not (short_model_bone_names or short_dress_bone_names):
            return

        logger.info("人物: 初期姿勢計算")

        # 人物の初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone([0], model)

        model.update_vertices_by_bone()

        model_inserted_bone_names = []
        for bone_name in DRESS_STANDARD_BONE_NAMES.keys():
            # 準標準ボーンの追加
            if bone_name in short_mismatch_model_bone_names and model.insert_standard_bone(bone_name, model_matrixes):
                model_inserted_bone_names.append(bone_name)
                logger.info("-- 人物: ボーン追加: {b}", b=bone_name)

        if model_inserted_bone_names:
            model.setup()
            model.replace_standard_weights(model_inserted_bone_names)
            logger.info("人物: 再セットアップ")

        model.update_vertices_by_bone()

        model_inserted_bust_bone_names = []
        for bone_name in ("左胸", "右胸"):
            # 胸ボーンの追加
            if bone_name in short_mismatch_model_bone_names and self.insert_bust(model, bone_name):
                logger.info("-- 人物: ボーン追加: {b}", b=bone_name)
                model_inserted_bust_bone_names.append(bone_name)

        if model_inserted_bust_bone_names:
            model.setup()
            model.replace_standard_weights(model_inserted_bust_bone_names)
            logger.info("人物: 再セットアップ")

            model.update_vertices_by_bone()

        # ------------------------------------------------------
        logger.info("衣装: 初期姿勢計算")

        # 衣装の初期姿勢を求める
        dress_matrixes = VmdMotion().animate_bone([0], dress)

        dress.update_vertices_by_bone()

        dress_inserted_bone_names = []
        for bone_name in DRESS_STANDARD_BONE_NAMES.keys():
            # 準標準ボーンの追加
            if bone_name in short_mismatch_dress_bone_names and dress.insert_standard_bone(bone_name, dress_matrixes):
                dress_inserted_bone_names.append(bone_name)
                logger.info("-- 衣装: ボーン追加: {b}", b=bone_name)

        if dress_inserted_bone_names:
            dress.setup()
            dress.replace_standard_weights(dress_inserted_bone_names)
            logger.info("衣装: 再セットアップ")

        dress.update_vertices_by_bone()

        dress_inserted_bust_bone_names = []
        for bone_name in ("左胸", "右胸"):
            # 胸ボーンの追加
            if bone_name in short_mismatch_dress_bone_names and self.insert_bust(dress, bone_name):
                logger.info("-- 衣装: ボーン追加: {b}", b=bone_name)
                dress_inserted_bust_bone_names.append(bone_name)

        if dress_inserted_bust_bone_names:
            dress.setup()
            dress.replace_standard_weights(dress_inserted_bust_bone_names)
            logger.info("衣装: 再セットアップ")

            dress.update_vertices_by_bone()

    def replace_bust_weights(self, model: PmxModel, bone_names: list[str]) -> None:
        """胸ウェイトの置き換え"""

        # 既に胸にウェイトが乗っている場合、一旦上半身2に乗せ直す
        upper_vertex_indexes = [bone.index for bone in model.bones if "上半身" in bone.name]

        for bust_bone_name in ("右胸", "左胸"):
            if bust_bone_name not in model.bones:
                continue

            bust_bone = model.bones[bust_bone_name]

            bust_upper_position = bust_bone.position + (model.bones["左肩根元"].position - model.bones["上半身"].position) * 0.5
            bust_upper_position.z = 0
            bust_lower_position = bust_bone.position + (model.bones["左肩根元"].position - model.bones["上半身"].position) * -0.3
            bust_lower_position.z = 0

            # 胸ウェイトを乗せる頂点範囲
            bust_start_z = model.bones[bust_bone.parent_index].position.z + (
                (bust_bone.position.z - model.bones[bust_bone.parent_index].position.z) / 2
            )

            # 胸のウェイトを乗せる半径(Zは潰す)
            bust_upper_radius = bust_upper_position.distance(bust_bone.position)
            bust_lower_radius = bust_lower_position.distance(bust_bone.position)

            # 胸の位置
            bust_pos = bust_bone.position.copy()
            bust_pos.z = 0

            bust_vertex_indexes: list[int] = []
            for vertex_index in set(
                (model.vertices_by_bones.get(model.bones["上半身"].index, []) if "上半身" in model.bones else [])
                + (model.vertices_by_bones.get(model.bones["上半身2"].index, []) if "上半身2" in model.bones else [])
                + (model.vertices_by_bones.get(model.bones["上半身3"].index, []) if "上半身3" in model.bones else [])
            ):
                # 左右に分けて胸に割り当てる頂点を取得
                if (
                    (
                        ("左" in bust_bone_name and -bust_bone.position.x / 2 < model.vertices[vertex_index].position.x)
                        or ("右" in bust_bone_name and -bust_bone.position.x / 2 > model.vertices[vertex_index].position.x)
                    )
                    and bust_lower_position.y <= model.vertices[vertex_index].position.y <= bust_upper_position.y
                    and bust_start_z > model.vertices[vertex_index].position.z
                ):
                    bust_vertex_indexes.append(vertex_index)

            for vertex_index in bust_vertex_indexes:
                v = model.vertices[vertex_index]
                v.deform.normalize(align=True)

                vpos = v.position.copy()
                vpos.z = 0

                # Zを潰した距離
                bust_distance = vpos.distance(bust_pos)
                bust_ratio = 1 - bust_distance / (bust_upper_radius if vpos.y >= bust_pos.y else bust_lower_radius)

                if 0 > bust_ratio:
                    # 半径を超えるのはそのまま上半身系に割り当てる
                    continue

                upper_matches = np.array([i in upper_vertex_indexes for i in v.deform.indexes])
                original_weight = np.sum(v.deform.weights[upper_matches])
                separate_weight = original_weight * bust_ratio / (np.count_nonzero(upper_matches) or 1)
                # 元ボーンは分割先ボーンの残り
                v.deform.weights = np.where(upper_matches, (v.deform.weights * (1 - bust_ratio)) - separate_weight, v.deform.weights)
                v.deform.weights[0.01 > v.deform.weights] = 0
                v.deform.weights = np.append(v.deform.weights, separate_weight)
                v.deform.indexes = np.append(v.deform.indexes, bust_bone.index)
                # 一旦最大値で正規化
                v.deform.count = 4
                v.deform.normalize(align=True)
                if np.count_nonzero(v.deform.weights) == 0:
                    # 念のためウェイトが割り当てられなかったら、元ボーンを割り当てとく
                    v.deform = Bdef1(bust_bone.parent_index)
                elif np.count_nonzero(v.deform.weights) == 1:
                    # Bdef1で再定義
                    v.deform = Bdef1(v.deform.indexes[np.argmax(v.deform.weights)])
                elif np.count_nonzero(v.deform.weights) == 2:
                    # Bdef2で再定義
                    v.deform = Bdef2(
                        v.deform.indexes[np.argsort(v.deform.weights)[-1]],
                        v.deform.indexes[np.argsort(v.deform.weights)[-2]],
                        float(np.max(v.deform.weights)),
                    )
                v.deform.normalize(align=True)

    def replace_neck_root_weights(self, model: PmxModel) -> None:
        """首根元に上半身の一部を割り振る"""
        if "首根元" not in model.bones:
            return

        model.update_vertices_by_bone()
        parent_bone = model.bones[model.bones["首根元"].parent_index]
        to_tail_y = model.bones["首根元"].position.y - parent_bone.position.y
        model.separate_weights(parent_bone.name, "首根元", "首", 0.3, 0.0, (parent_bone.name,), to_tail_pos=MVector3D(0, to_tail_y, 0))

    def insert_bust(self, model: PmxModel, bust_bone_name: str) -> bool:
        """胸ボーンの追加"""
        # 上半身1, 2, 3 のウェイト位置取得
        upper_vertices: list[int] = []
        parent_upper_name: str = ""
        for upper_bone_name in ("上半身", "上半身2", "上半身3"):
            if upper_bone_name not in model.bones:
                break
            upper_vertices += model.vertices_by_bones.get(model.bones[upper_bone_name].index, [])
            parent_upper_name = upper_bone_name

        if not parent_upper_name or not upper_vertices:
            # 登録対象となりうる親ボーンが見つからなかった場合、スルー
            return False

        upper_vertex_positions: list[np.ndarray] = []
        for vertex_index in upper_vertices:
            # 左右に分けて前方向の位置を取得
            if (
                ("左" in bust_bone_name and 0 > model.vertices[vertex_index].position.x)
                or ("右" in bust_bone_name and 0 < model.vertices[vertex_index].position.x)
                or 0 < model.vertices[vertex_index].position.z
            ):
                continue
            upper_vertex_positions.append(model.vertices[vertex_index].position.vector)

        if not upper_vertex_positions:
            # 登録対象となりうる親ボーンが見つからなかった場合、スルー
            return False

        upper_mean_position = np.mean(upper_vertex_positions, axis=0)

        # 胸ボーンの追加
        bust_bone = Bone(name=bust_bone_name, english_name=bust_bone_name)
        bust_bone_setting = DRESS_STANDARD_BONE_NAMES[bust_bone_name]
        bust_bone.bone_flg = bust_bone_setting.flag
        bust_bone.tail_position = bust_bone_setting.axis.copy()
        bust_bone.position = MVector3D(upper_mean_position[0], upper_mean_position[1], upper_mean_position[2])
        bust_bone.parent_index = model.bones[parent_upper_name].index
        bust_bone.layer = model.bones[parent_upper_name].layer
        bust_bone.index = bust_bone.parent_index + 1

        model.insert_bone(bust_bone)

        return True

    def replace_lower(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """下半身のボーン置き換え"""
        replace_bone_names = ("足中心", "頭", "下半身")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names, is_fix_x_zero=True)

        return ["下半身"] if is_add else []

    def replace_upper(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """上半身のボーン置き換え"""
        replace_bone_names = ("足中心", "頭", "上半身")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names, is_fix_x_zero=True)

        return ["上半身"] if is_add else []

    def replace_upper2(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """上半身2のボーン置き換え"""
        replace_bone_names = ("上半身", "頭", "上半身2")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names, is_fix_x_zero=True)

        return ["上半身2"] if is_add else []

    def replace_bust(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """胸系のボーン置き換え"""
        bust_added_bone_names: list[str] = []
        for bust_bone_name in ("右胸", "左胸"):
            replace_bone_names = ("上半身2", "頭", bust_bone_name)
            if model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names):
                is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names, is_fix_x_zero=True)
                if is_add:
                    logger.info("-- 衣装: {b}位置調整", b=bust_bone_name)
                    bust_added_bone_names.append(bust_bone_name)

        return bust_added_bone_names

    def replace_neck(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """首のボーン置き換え"""
        replace_bone_names = ("上半身2", "頭", "首")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names, is_fix_x_zero=True)

        return ["首"] if is_add else []

    def replace_shoulder_arm(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """肩と腕のボーン置き換え"""
        replace_bone_names = ("上半身2", "右肩", "左肩", "右腕", "左腕", "右ひじ", "左ひじ")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        model_upper_pos = model.bones["上半身2"].position.copy()
        model_right_shoulder_pos = model.bones["右肩"].position.copy()
        model_left_shoulder_pos = model.bones["左肩"].position.copy()
        model_right_arm_pos = model.bones["右腕"].position.copy()
        model_left_arm_pos = model.bones["左腕"].position.copy()
        model_right_elbow_pos = model.bones["右ひじ"].position.copy()
        model_left_elbow_pos = model.bones["左ひじ"].position.copy()

        dress_upper_pos = dress.bones["上半身2"].position.copy()
        dress_right_shoulder_pos = dress.bones["右肩"].position.copy()
        dress_left_shoulder_pos = dress.bones["左肩"].position.copy()
        dress_right_arm_pos = dress.bones["右腕"].position.copy()
        dress_left_arm_pos = dress.bones["左腕"].position.copy()
        dress_right_elbow_pos = dress.bones["右ひじ"].position.copy()
        dress_left_elbow_pos = dress.bones["左ひじ"].position.copy()

        # 元ボーン-置換ボーン ベースで求めた時の肩の位置 ---------------

        dress_right_shoulder_new_pos = align_triangle(
            model_upper_pos, model_right_arm_pos, model_right_shoulder_pos, dress_upper_pos, dress_right_arm_pos
        )
        dress_left_shoulder_new_pos = align_triangle(
            model_upper_pos, model_left_arm_pos, model_left_shoulder_pos, dress_upper_pos, dress_left_arm_pos
        )

        # 衣装の置換ボーンの位置を求め直す
        dress_replace_right_shoulder_new_pos = (
            (dress_right_shoulder_new_pos.abs() + dress_left_shoulder_new_pos.abs())
            / 2
            * MVector3D(*np.sign(dress_right_shoulder_new_pos.vector))
        )
        dress_replace_right_shoulder_diff_pos = dress_replace_right_shoulder_new_pos - dress_right_shoulder_pos

        dress.bones["右肩"].position = dress_replace_right_shoulder_new_pos
        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r="右肩",
            u=dress_right_shoulder_pos,
            p=dress_replace_right_shoulder_new_pos,
            d=dress_replace_right_shoulder_diff_pos,
        )

        dress_replace_left_shoulder_new_pos = (
            (dress_right_shoulder_new_pos.abs() + dress_left_shoulder_new_pos.abs())
            / 2
            * MVector3D(*np.sign(dress_left_shoulder_new_pos.vector))
        )
        dress_replace_left_shoulder_diff_pos = dress_replace_left_shoulder_new_pos - dress_left_shoulder_pos

        dress.bones["左肩"].position = dress_replace_left_shoulder_new_pos
        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r="左肩",
            u=dress_left_shoulder_pos,
            p=dress_replace_left_shoulder_new_pos,
            d=dress_replace_left_shoulder_diff_pos,
        )

        replaced_bone_names = ["右肩", "左肩"]

        if "右肩P" in dress.bones:
            dress.bones["右肩P"].position = dress.bones["右肩"].position.copy()
            replaced_bone_names.append("右肩P")

        if "左肩P" in dress.bones:
            dress.bones["左肩P"].position = dress.bones["左肩"].position.copy()
            replaced_bone_names.append("左肩P")

        # 元ボーン-置換ボーン ベースで求めた時の腕の位置 ---------------
        # 肩は再計算した位置を使用する

        dress_right_arm_new_pos = align_triangle(
            model_right_shoulder_pos,
            model_right_elbow_pos,
            model_right_arm_pos,
            dress_replace_right_shoulder_new_pos,
            dress_right_elbow_pos,
        )
        dress_left_arm_new_pos = align_triangle(
            model_left_shoulder_pos,
            model_left_elbow_pos,
            model_left_arm_pos,
            dress_replace_left_shoulder_new_pos,
            dress_left_elbow_pos,
        )

        # 衣装の置換ボーンの位置を求め直す
        dress_replace_right_arm_new_pos = (
            (dress_right_arm_new_pos.abs() + dress_left_arm_new_pos.abs()) / 2 * MVector3D(*np.sign(dress_right_arm_new_pos.vector))
        )
        dress_replace_right_arm_diff_pos = dress_replace_right_arm_new_pos - dress_right_arm_pos

        dress.bones["右腕"].position = dress_replace_right_arm_new_pos

        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r="右腕",
            u=dress_right_arm_pos,
            p=dress_replace_right_arm_new_pos,
            d=dress_replace_right_arm_diff_pos,
        )

        dress_replace_left_arm_new_pos = (
            (dress_right_arm_new_pos.abs() + dress_left_arm_new_pos.abs()) / 2 * MVector3D(*np.sign(dress_left_arm_new_pos.vector))
        )
        dress_replace_left_arm_diff_pos = dress_replace_left_arm_new_pos - dress_left_arm_pos

        dress.bones["左腕"].position = dress_replace_left_arm_new_pos

        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r="左腕",
            u=dress_left_arm_pos,
            p=dress_replace_left_arm_new_pos,
            d=dress_replace_left_arm_diff_pos,
        )

        replaced_bone_names.append("右腕")
        replaced_bone_names.append("左腕")

        if "右肩C" in dress.bones:
            dress.bones["右肩C"].position = dress.bones["右腕"].position.copy()
            replaced_bone_names.append("右肩C")

        if "左肩C" in dress.bones:
            dress.bones["左肩C"].position = dress.bones["左腕"].position.copy()
            replaced_bone_names.append("左肩C")

        return replaced_bone_names

    def replace_toe_ex(self, model: PmxModel, dress: PmxModel, direction: str) -> list[str]:
        """足先EXのボーン置き換え"""
        replace_bone_names = (f"{direction}足首", f"{direction}つま先ＩＫ", f"{direction}足先EX")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        from_name = f"{direction}足首"
        replace_name = f"{direction}足先EX"
        model_to_name = model.bones[model.bones[f"{direction}つま先ＩＫ"].ik.bone_index].name
        dress_to_name = dress.bones[dress.bones[f"{direction}つま先ＩＫ"].ik.bone_index].name

        model_from_pos = model.bones[from_name].position.copy()
        model_replace_pos = model.bones[replace_name].position.copy()
        model_to_pos = model.bones[model_to_name].position.copy()
        dress_from_pos = dress.bones[from_name].position.copy()
        dress_replace_pos = dress.bones[replace_name].position.copy()
        dress_to_pos = dress.bones[dress_to_name].position.copy()

        # 元ボーン-置換ボーン ベースで求めた時の位置 ---------------

        # 衣装の置換ボーンの位置を求め直す
        dress_replace_new_pos = align_triangle(model_from_pos, model_to_pos, model_replace_pos, dress_from_pos, dress_to_pos)
        dress_replace_diff_pos = dress_replace_new_pos - dress_replace_pos

        dress.bones[replace_name].position += dress_replace_diff_pos
        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r=replace_name,
            u=dress_replace_pos,
            p=dress_replace_new_pos,
            d=dress_replace_diff_pos,
        )

        return [f"{direction}足先EX"]

    def replace_twist(self, model: PmxModel, dress: PmxModel, replaced_bone_names: list[str]) -> list[str]:
        """腕捩・手捩のボーン置き換え"""

        replace_bone_set = (
            ("右腕", "右ひじ", "右腕捩"),
            ("右ひじ", "右手首", "右手捩"),
            ("左腕", "左ひじ", "左腕捩"),
            ("左ひじ", "左手首", "左手捩"),
        )

        for from_name, to_name, replace_name in replace_bone_set:
            # 捩りボーンそのもの
            is_add = self.replace_bone_position(model, dress, from_name, to_name, replace_name)
            if is_add:
                replaced_bone_names.append(replace_name)

            # 分散の付与ボーン
            for no in range(1, 5):
                is_add = self.replace_bone_position(model, dress, from_name, to_name, f"{replace_name}{no}")
                if is_add:
                    replaced_bone_names.append(replace_name)

        return replaced_bone_names

    def replace_bone_position(
        self, model: PmxModel, dress: PmxModel, from_name: str, to_name: str, replace_name: str, is_fix_x_zero: bool = False
    ) -> tuple[bool, MVector3D]:
        """
        衣装のボーン位置を人物ボーン位置に合わせて配置を変える
        """
        if not (model.bones.exists([from_name, to_name, replace_name]) and dress.bones.exists([from_name, to_name, replace_name])):
            # ボーンが足りなかったら追加しない
            return False, MVector3D()

        model_from_pos = model.bones[from_name].position.copy()
        model_replace_pos = model.bones[replace_name].position.copy()
        model_to_pos = model.bones[to_name].position.copy()
        dress_from_pos = dress.bones[from_name].position.copy()
        dress_replace_pos = dress.bones[replace_name].position.copy()
        dress_to_pos = dress.bones[to_name].position.copy()

        # 元ボーン-置換ボーン ベースで求めた時の位置 ---------------

        # 衣装の置換ボーンの位置を求め直す
        dress_replace_new_pos = align_triangle(model_from_pos, model_to_pos, model_replace_pos, dress_from_pos, dress_to_pos)
        dress_replace_diff_pos = dress_replace_new_pos - dress_replace_pos
        if is_fix_x_zero:
            dress_replace_diff_pos.x = 0

        dress.bones[replace_name].position = dress_replace_new_pos
        logger.info(
            "衣装: {r}: 位置再計算: {u} → {p} ({d})",
            r=replace_name,
            u=dress_replace_pos,
            p=dress_replace_new_pos,
            d=dress_replace_diff_pos,
        )

        return True, dress_replace_diff_pos

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

    def create_dress_individual_bone_morphs(self, dress: PmxModel) -> tuple[list[str], list[list[int]]]:
        """衣装個別フィッティング用ボーンモーフを作成"""

        logger.info("個別調整ボーンモーフ追加")

        individual_morph_names: list[str] = []
        individual_target_bone_indexes: list[list[int]] = []

        for morph_name, fitBoneSetting in FIT_INDIVIDUAL_MORPH_NAMES.items():
            if not [bone_name for bone_name in fitBoneSetting.target_bone_names if bone_name in dress.bones]:
                # 処理対象ボーンがなければスルー
                continue

            target_bone_indexes: list[int] = []

            # 子どものスケーリング対象もモーフに入れる
            child_scale_bone_names = list(
                set(
                    [
                        child_bone_name
                        for child_morph_name in fitBoneSetting.child_scale_morph_names
                        for child_bone_name in FIT_INDIVIDUAL_MORPH_NAMES[child_morph_name].target_bone_names
                        if child_bone_name in dress.bones
                    ]
                )
            )

            child_rotation_bone_names = list(
                set(
                    [
                        child_bone_name
                        for child_morph_name in fitBoneSetting.child_rotation_morph_names
                        for child_bone_name in FIT_INDIVIDUAL_MORPH_NAMES[child_morph_name].target_bone_names
                        if child_bone_name in dress.bones
                    ]
                )
            )

            # X軸：横方向, Y軸：進行方向、Z軸：奥行き方向
            for axis_name, position, local_qq, local_scale in (
                ("SX", MVector3D(), MQuaternion(), MVector3D(0, 1, 0)),
                ("SY", MVector3D(), MQuaternion(), MVector3D(1, 0, 0)),
                ("SZ", MVector3D(), MQuaternion(), MVector3D(0, 0, 1)),
                ("RX", MVector3D(), MQuaternion.from_euler_degrees(2, 2, 0), MVector3D()),
                ("RY", MVector3D(), MQuaternion.from_euler_degrees(2, 0, 0), MVector3D()),
                ("RZ", MVector3D(), MQuaternion.from_euler_degrees(0, 0, -2), MVector3D()),
                ("MX", MVector3D(1, 0, 0), MQuaternion(), MVector3D()),
                ("MY", MVector3D(0, 1, 0), MQuaternion(), MVector3D()),
                ("MZ", MVector3D(0, 0, 1), MQuaternion(), MVector3D()),
            ):
                morph = Morph(name=f"調整:{__(morph_name)}:{axis_name}")
                morph.is_system = True
                morph.morph_type = MorphType.BONE

                target_all_bone_names = fitBoneSetting.target_bone_names
                if "S" in axis_name:
                    # スケールの時だけ子どもを加味する
                    target_all_bone_names = fitBoneSetting.target_bone_names + child_scale_bone_names
                elif "M" in axis_name:
                    # 移動の場合はP系列も動かす
                    target_all_bone_names = fitBoneSetting.target_bone_names + fitBoneSetting.move_target_bone_names

                for bone_name in target_all_bone_names:
                    if bone_name in dress.bones:
                        if axis_name in ("MX", "RY", "RZ"):
                            offset_position = position * (-1 if "右" in bone_name else 1)
                            offset_local_qq = local_qq.inverse() if "左" in bone_name else local_qq
                        else:
                            offset_position = position
                            offset_local_qq = local_qq

                        if bone_name in ("頭", "左胸", "右胸", "左足首D", "右足首D", "左足首", "右足首"):
                            # 末端だけはグローバルスケールで動かす（Z方向にまっすぐ伸ばすため）
                            # ただし、画面指定上はローカルと同じ操作感にする
                            if bone_name in ("頭",):
                                scale = (
                                    MVector3D(1, 0, 0)
                                    if "SX" == axis_name
                                    else MVector3D(0, 1, 0)
                                    if "SY" == axis_name
                                    else MVector3D(0, 0, 1)
                                    if "SZ" == axis_name
                                    else MVector3D(0, 0, 0)
                                )
                            else:
                                scale = (
                                    MVector3D(1, 0, 0)
                                    if "SX" == axis_name
                                    else MVector3D(0, 1, 0)
                                    if "SY" == axis_name
                                    else MVector3D(0, 0, 2)
                                    if "SZ" == axis_name
                                    else MVector3D(0, 0, 0)
                                )

                            morph.offsets.append(
                                BoneMorphOffset(
                                    dress.bones[bone_name].index,
                                    position=offset_position,
                                    qq=offset_local_qq,
                                    scale=scale,
                                )
                            )
                        else:
                            morph.offsets.append(
                                BoneMorphOffset(
                                    dress.bones[bone_name].index,
                                    position=offset_position,
                                    local_qq=offset_local_qq,
                                    local_scale=local_scale,
                                )
                            )

                        target_bone_indexes.append(dress.bones[bone_name].index)

                if "R" in axis_name:
                    for bone_name in child_rotation_bone_names:
                        if axis_name in ("RY", "RZ"):
                            offset_local_qq = local_qq.inverse() if "左" in bone_name else local_qq
                        else:
                            offset_local_qq = local_qq

                        morph.offsets.append(
                            BoneMorphOffset(
                                dress.bones[bone_name].index,
                                local_qq=offset_local_qq,
                            )
                        )

                        target_bone_indexes.append(dress.bones[bone_name].index)

                if len(morph.offsets):
                    dress.morphs.append(morph)
                    if __(morph_name) not in individual_morph_names:
                        individual_morph_names.append(__(morph_name))

            if target_bone_indexes:
                individual_target_bone_indexes.append(list(set(target_bone_indexes)))

        for dress_bone in dress.bones:
            if (
                dress_bone.is_standard
                or dress_bone.is_standard_extend
                or not dress.bones[dress_bone.parent_index].is_standard
                or "操作中心" == dress_bone.name
                or "胸" in dress_bone.name
                or "握" in dress_bone.name
                or "拡散" in dress_bone.name
            ):
                continue

            individual_morph_names.append(dress_bone.name)

            # 自分とその子どもの準標準外ボーンのINDEXリストを保持
            target_bone_indexes = [bone_tree.last_index for bone_tree in dress.bone_trees if dress_bone.name in bone_tree.names]

            # 準標準を親に持つ準標準外のルートボーンの調整モーフを追加する
            for axis_name, position, local_qq, local_scale in (
                ("SX", MVector3D(), MQuaternion(), MVector3D(0, 1, 0)),
                ("SY", MVector3D(), MQuaternion(), MVector3D(1, 0, 0)),
                ("SZ", MVector3D(), MQuaternion(), MVector3D(0, 0, 1)),
                ("RX", MVector3D(), MQuaternion.from_euler_degrees(2, 2, 0), MVector3D()),
                ("RY", MVector3D(), MQuaternion.from_euler_degrees(2, 0, 0), MVector3D()),
                ("RZ", MVector3D(), MQuaternion.from_euler_degrees(0, 0, 2), MVector3D()),
                ("MX", MVector3D(1, 0, 0), MQuaternion(), MVector3D()),
                ("MY", MVector3D(0, 1, 0), MQuaternion(), MVector3D()),
                ("MZ", MVector3D(0, 0, 1), MQuaternion(), MVector3D()),
            ):
                morph = Morph(name=f"調整:{dress_bone.name}:{axis_name}")
                morph.is_system = True
                morph.morph_type = MorphType.BONE

                morph.offsets.append(
                    BoneMorphOffset(
                        dress_bone.index,
                        position=position,
                        local_qq=local_qq,
                        local_scale=local_scale,
                    )
                )

                for child_bone_index in target_bone_indexes:
                    morph.offsets.append(
                        BoneMorphOffset(
                            child_bone_index,
                            local_qq=local_qq,
                            local_scale=local_scale,
                        )
                    )

                dress.morphs.append(morph)

            individual_target_bone_indexes.append(target_bone_indexes)

        return individual_morph_names, individual_target_bone_indexes

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

        dress_bone_fitting_morph = Morph(name=DRESS_BONE_FITTING_NAME)
        dress_bone_fitting_morph.is_system = True
        dress_bone_fitting_morph.morph_type = MorphType.BONE
        dress.morphs.append(dress_bone_fitting_morph)

        dress_vertex_fitting_morph = Morph(name=DRESS_VERTEX_FITTING_NAME)
        dress_vertex_fitting_morph.is_system = True
        dress_vertex_fitting_morph.morph_type = MorphType.AFTER_VERTEX
        dress.morphs.append(dress_vertex_fitting_morph)

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone([0], model)

        logger.info("ボーンフィッティング", decoration=MLogger.Decoration.LINE)
        dress_local_scales, dress_global_scales, dress_offset_positions, dress_offset_qqs = self.fit_dress_bone_morph(
            model, dress, model_matrixes
        )

        dress_part_offset_positions: dict[str, list[np.ndarray]] = {}
        dress_part_offset_degrees: dict[str, list[np.ndarray]] = {}
        dress_part_local_scales: dict[str, list[np.ndarray]] = {}
        dress_part_global_scales: dict[str, list[np.ndarray]] = {}

        dress_fixed_length_local_scales: dict[int, MVector3D] = {}
        dress_fixed_depth_local_scales: dict[int, MVector3D] = {}
        dress_fixed_offset_positions: dict[str, MVector3D] = {}
        dress_fixed_offset_qqs: dict[str, MQuaternion] = {}

        # 一旦クリア
        dress.morphs[DRESS_BONE_FITTING_NAME].offsets = []

        logger.info("ボーンフィッティング設定", decoration=MLogger.Decoration.LINE)

        for dress_bone in dress.bones:
            if not (dress_bone.is_standard and ("左" in dress_bone.name or "右" in dress_bone.name)):
                # 準標準ボーンかつ左右のみ対象
                continue
            if not (dress_bone.index in dress_offset_positions or dress_bone.index in dress_offset_qqs):
                # オフセットが無い場合スルー
                continue

            dress_offset_position = dress_offset_positions.get(dress_bone.index, MVector3D())
            dress_offset_qq = dress_offset_qqs.get(dress_bone.index, MQuaternion())
            dress_local_scale = dress_local_scales.get(dress_bone.index, MVector3D())
            dress_global_scale = dress_global_scales.get(dress_bone.index, MVector3D())

            part_name = dress_bone.name[1:]

            if part_name not in dress_part_offset_positions:
                dress_part_offset_positions[part_name] = []
                dress_part_offset_degrees[part_name] = []
                dress_part_local_scales[part_name] = []
                dress_part_global_scales[part_name] = []

            dress_part_offset_positions[part_name].append(dress_offset_position.abs().vector)
            dress_part_offset_degrees[part_name].append(dress_offset_qq.to_euler_degrees().abs().vector)
            dress_part_local_scales[part_name].append(dress_local_scale.vector)
            dress_part_global_scales[part_name].append(dress_global_scale.vector)

        for dress_bone in dress.bones:
            if not (
                dress_bone.index in dress_offset_positions
                or dress_bone.index in dress_offset_qqs
                or dress_bone.index in dress_local_scales
                or dress_bone.index in dress_global_scales
            ):
                continue

            dress_local_scale = dress_local_scales.get(dress_bone.index, MVector3D())
            dress_global_scale = dress_global_scales.get(dress_bone.index, MVector3D())
            dress_offset_position = dress_offset_positions.get(dress_bone.index, MVector3D())
            dress_offset_qq = dress_offset_qqs.get(dress_bone.index, MQuaternion())

            if dress_bone.name[1:] in dress_part_offset_positions and dress_offset_position:
                # 左右の場合、平均値を採用する
                dress_offset_position.vector = np.mean(dress_part_offset_positions[dress_bone.name[1:]], axis=0) * np.sign(
                    dress_offset_position.vector
                )

            if dress_bone.name[1:] in dress_part_offset_degrees and dress_offset_qq:
                dress_offset_qq = MQuaternion.from_euler_degrees(
                    *np.mean(dress_part_offset_degrees[dress_bone.name[1:]], axis=0) * np.sign(dress_offset_qq.to_euler_degrees().vector)
                )

            if dress_bone.name[1:] in dress_part_local_scales and dress_local_scale:
                dress_local_scale.vector = np.mean(dress_part_local_scales[dress_bone.name[1:]], axis=0)

            if dress_bone.name[1:] in dress_part_global_scales and dress_global_scale:
                dress_global_scale.vector = np.mean(dress_part_global_scales[dress_bone.name[1:]], axis=0)

            dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
                BoneMorphOffset(
                    dress_bone.index,
                    position=dress_offset_position,
                    qq=dress_offset_qq,
                    scale=dress_global_scale,
                    local_scale=dress_local_scale,
                )
            )

            dress_fixed_length_local_scales[dress_bone.index] = MVector3D(dress_local_scale.x, 0, 0)
            dress_fixed_depth_local_scales[dress_bone.index] = MVector3D(0, dress_local_scale.y, dress_local_scale.z)
            dress_fixed_offset_positions[dress_bone.index] = dress_offset_position
            dress_fixed_offset_qqs[dress_bone.index] = dress_offset_qq

            logger.info(
                "-- [{b}][移動={p}][回転={q}][縮尺:{s}][ローカル縮尺:{l}]",
                b=dress_bone.name,
                p=dress_offset_position,
                q=dress_offset_qq.to_euler_degrees(),
                s=dress_global_scale + MVector3D(1, 1, 1),
                l=dress_local_scale + MVector3D(1, 1, 1),
            )

        # logger.info("頂点フィッティング", decoration=MLogger.Decoration.LINE)
        # self.fit_dress_vertex_morph(
        #     model,
        #     dress,
        #     dress_fixed_length_local_scales,
        #     dress_fixed_depth_local_scales,
        #     dress_fixed_offset_positions,
        #     dress_fixed_offset_qqs,
        # )

    def fit_dress_vertex_morph(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_length_local_scales: dict[int, MVector3D],
        dress_depth_local_scales: dict[int, MVector3D],
        dress_offset_positions: dict[str, MVector3D],
        dress_offset_qqs: dict[str, MQuaternion],
    ) -> None:
        # ボーンフィッティングモーフを適用
        dress_motion = VmdMotion("dress fit motion")
        dress_motion.morphs[DRESS_BONE_FITTING_NAME][0] = VmdMorphFrame(0, DRESS_BONE_FITTING_NAME, ratio=1.0)

        dress_matrixes = dress_motion.animate_bone([0], dress, append_ik=True)

        vertex_positions = []
        vertex_total_count = len(dress.vertices)
        for vertex in dress.vertices:
            logger.count("頂点位置", vertex.index, vertex_total_count, display_block=10000)
            vertex_positions.append(vertex.position.vector)

        bone_positions = MVectorDict()
        bone_total_count = len(dress.bones)
        bone_lattice_vertex_positions: np.ndarray = np.zeros((bone_total_count, vertex_total_count, 3))
        for bone in dress.bones:
            logger.count("ボーン位置", bone.index, bone_total_count, display_block=10)

            # 単一のローカルスケールで調整した場合の行列を求める
            bone_motion = VmdMotion("bone scale motion")
            for in_bone in dress.bones:
                bf = VmdBoneFrame(0, in_bone.name)
                # 長さはボーンそのもののスケールを使い、厚みは計算元ボーンの厚みで統一した場合でローカルスケールを計算する
                local_scale = MVector3D()
                if in_bone.is_standard and DRESS_STANDARD_BONE_NAMES[in_bone.name].local_x_scalable:
                    local_scale += dress_length_local_scales.get(in_bone.index, MVector3D())
                if in_bone.is_standard and DRESS_STANDARD_BONE_NAMES[in_bone.name].local_scalable:
                    local_scale += dress_depth_local_scales.get(bone.index, MVector3D())
                bf.local_scale = local_scale
                # 移動と回転はそのまま付与
                bf.position = dress_offset_positions.get(in_bone.index, MVector3D())
                bf.rotation = dress_offset_qqs.get(in_bone.index, MQuaternion())
                bone_motion.bones[in_bone.name].append(bf)

            bone_matrixes = bone_motion.animate_bone([0], dress, append_ik=False)

            # ラティス変形させた結果を保持
            bone_lattice_vertex_positions[bone.index] = transform_lattice(
                np.array(vertex_positions), bone_matrixes[0, bone.name].local_matrix.vector[:3, :]
            )

            # # ラティス変形させた結果を保持
            # bone_lattice_vertex_positions[bone.index] = transform_lattice(
            #     np.array(vertex_positions), dress_matrixes[0, bone.name].local_matrix.vector[:3, :]
            # )

            # ボーンの位置
            bone_positions.append(bone.index, bone.position)

        vertex_total_count = len(dress.vertices)
        for vertex in dress.vertices:
            logger.count("頂点フィッティング", vertex.index, vertex_total_count, display_block=500)

            # ボーンフィッティングによる変形後の頂点位置を求める
            mat = np.zeros((4, 4))
            for n in range(vertex.deform.count):
                bone_index = vertex.deform.indexes[n]
                bone_weight = vertex.deform.weights[n]
                mat += dress_matrixes[0, dress.bones[bone_index].name].local_matrix.vector * bone_weight
            deformed_vertex_position = MMatrix4x4(*mat.flatten()) * vertex.position

            # # 距離が近いボーンをリストアップする
            # near_bone_positions = bone_positions.sorted_near_values(vertex.position, 2)
            # near_bone_distances = near_bone_positions.distances(vertex.position)
            # # 距離から重みを求める
            # near_bone_weights = near_bone_distances / near_bone_distances.sum(axis=0, keepdims=True)

            # # ラティス変形に合わせた理想頂点位置
            # near_lattice_vertex_positions = bone_lattice_vertex_positions[
            #     np.asarray(near_bone_positions.keys(), dtype=np.int32), vertex.index
            # ]
            # # lattice_vertex_position = MVector3D(*np.average(near_lattice_vertex_positions, axis=0, weights=near_bone_weights))
            # lattice_vertex_position = MVector3D(*np.mean(near_lattice_vertex_positions, axis=0))

            # 有効なウェイトボーンをリストアップする
            weights_bone_positions = MVectorDict()
            (
                bone_index1,
                bone_index2,
                bone_index3,
                bone_index4,
                bone_weight1,
                bone_weight2,
                bone_weight3,
                bone_weight4,
            ) = vertex.deform.normalized_deform()

            if 0 < bone_weight1:
                weights_bone_positions.append(bone_index1, dress.bones[bone_index1].position)

            if 0 < bone_weight2:
                weights_bone_positions.append(bone_index2, dress.bones[bone_index2].position)

            if 0 < bone_weight3:
                weights_bone_positions.append(bone_index3, dress.bones[bone_index3].position)

            if 0 < bone_weight4:
                weights_bone_positions.append(bone_index4, dress.bones[bone_index4].position)

            weight_bone_distances = weights_bone_positions.distances(vertex.position)
            # 距離から重みを求める
            weight_bone_weights = weight_bone_distances / weight_bone_distances.sum(axis=0, keepdims=True)

            # ラティス変形に合わせた理想頂点位置
            near_lattice_vertex_positions = bone_lattice_vertex_positions[
                np.asarray(weights_bone_positions.keys(), dtype=np.int32), vertex.index
            ]
            lattice_vertex_position = MVector3D(*np.average(near_lattice_vertex_positions, axis=0, weights=weight_bone_weights))
            # lattice_vertex_position = MVector3D(*np.mean(near_lattice_vertex_positions, axis=0))

            vertex_offset_position = lattice_vertex_position - deformed_vertex_position

            dress.morphs[DRESS_VERTEX_FITTING_NAME].offsets.append(VertexMorphOffset(vertex.index, vertex_offset_position))

            if 0.5 < vertex_offset_position.length():
                logger.debug(
                    f"頂点オフセット vertex[{vertex.index}] pos[{vertex.position}] bone_deform[{deformed_vertex_position}] "
                    + f"lattice_deform[{lattice_vertex_position}], offset[{vertex_offset_position}]"
                )

        # ----- 変形結果 -------------
        dress_motion.morphs[DRESS_VERTEX_FITTING_NAME][0] = VmdMorphFrame(0, DRESS_VERTEX_FITTING_NAME, ratio=1.0)

        from datetime import datetime
        from service.usecase.save_usecase import SaveUsecase

        SaveUsecase().save(
            model,
            dress,
            VmdMotion(),
            dress_motion,
            os.path.join("E:/MMD/Dressup/output", f"{datetime.now():%Y%m%d_%H%M%S}_dress_vertex_deform.pmx"),
            dict([(m.name, 0.0) for m in model.materials]),
            dict([(m.name, False) for m in model.materials]),
            dict([(m.name, 1.0) for m in dress.materials]),
            dict([(m.name, False) for m in dress.materials]),
            {},
            {},
            {},
            {},
        )
        # ----- 変形結果 -------------

    def fit_dress_bone_morph(
        self, model: PmxModel, dress: PmxModel, model_matrixes: VmdBoneFrameTrees
    ) -> tuple[dict[int, MVector3D], dict[int, MVector3D], dict[int, MVector3D], dict[int, MQuaternion]]:
        """衣装との距離比率を元に、X方向のローカルスケーリングを行う"""

        # 衣装の初期姿勢を求める
        logger.info("衣装初期姿勢計算")

        # 衣装フィッティングモーション生成
        dress_motion = VmdMotion("dress fit motion")
        dress_motion.morphs[DRESS_BONE_FITTING_NAME][0] = VmdMorphFrame(0, DRESS_BONE_FITTING_NAME, ratio=1.0)

        dress_bone_count = len(dress.bones)
        dress_local_scales: dict[int, MVector3D] = {}
        dress_global_scales: dict[int, MVector3D] = {}
        dress_offset_positions: dict[int, MVector3D] = {}
        dress_offset_qqs: dict[int, MQuaternion] = {}

        model_local_positions: dict[str, dict[str, np.ndarray]] = {}
        dress_local_positions: dict[str, dict[str, np.ndarray]] = {}
        dress_category_local_x_scales: dict[str, list[float]] = {}

        logger.info("ボーン距離比率")

        for i, dress_bone in enumerate(dress.bones):
            logger.count(
                "ボーン距離比率",
                index=i,
                total_index_count=dress_bone_count,
                display_block=10,
            )

            if dress_bone.is_standard:
                dress_matrixes = dress_motion.animate_bone([0], dress, append_ik=False)

                bone_setting = DRESS_STANDARD_BONE_NAMES[dress_bone.name]
                if bone_setting.local_x_scalable and dress_bone.name in model.bones:
                    # X方向のスケーリングがOKで、人物に同名ボーンがある場合、比率を測る
                    model_bone = model.bones[dress_bone.name]

                    if bone_setting.category == "足ＩＫ":
                        # 足IKの比率は足ボーンから足IKボーンまでの直線距離とする
                        dress_fit_length_scale = (model_bone.position - model.bones[f"{dress_bone.name[0]}足"].position).length() / (
                            (dress_bone.position - dress.bones[f"{dress_bone.name[0]}足"].position).length() or 1
                        )
                    elif bone_setting.category == "つま先ＩＫ":
                        # つま先IKの比率はグローバルZ方向だけ合わせる
                        dress_fit_length_scale = (model_bone.position - model.bones[f"{dress_bone.name[0]}足ＩＫ"].position).length() / (
                            (dress_bone.position - dress.bones[f"{dress_bone.name[0]}足ＩＫ"].position).length() or 1
                        )
                    elif bone_setting.category == "足首":
                        dress_fit_length_scale = (
                            model_bone.position - model.bones[model.bones[f"{dress_bone.name[0]}つま先ＩＫ"].ik.bone_index].position
                        ).length() / (
                            (dress_bone.position - dress.bones[dress.bones[f"{dress_bone.name[0]}つま先ＩＫ"].ik.bone_index].position).length()
                            or 1
                        )
                    # elif dress_bone.name == "上半身2" and "上半身3" not in dress.bones:
                    #     # 上半身2はウェイトを全体的に覆ってるので、肩までの高さとする
                    #     if model.bones.exists(("左肩", "右肩")) and dress.bones.exists(("左肩", "右肩")):
                    #         dress_fit_length_scale = (
                    #             (((model.bones["左肩"].position + model.bones["右肩"].position) / 2) - model_bone.position).y
                    #         ) / ((((dress.bones["左肩"].position + dress.bones["右肩"].position) / 2) - dress_bone.position).y or 1)
                    #     else:
                    #         dress_fit_length_scale = 1.0
                    elif "手首" in dress_bone.name:
                        # 手首の比率は手首ボーンから各指１ボーンまでの直線距離の最小とする
                        finger_lengths: list[float] = []
                        for finger_name in ("親指０", "人指１", "中指１", "薬指１", "小指１"):
                            finger_bone_name = f"{dress_bone.name[0]}{finger_name}"
                            if finger_bone_name in model.bones and finger_bone_name in dress.bones:
                                finger_lengths.append(
                                    (model_bone.position - model.bones[finger_bone_name].position).length()
                                    / ((dress_bone.position - dress.bones[finger_bone_name].position).length() or 1)
                                )

                        dress_fit_length_scale = 1.0 if not finger_lengths else np.min(finger_lengths)
                    else:
                        tail_far_bone_names = [
                            tail_bone_name
                            for tail_bone_name in bone_setting.tails
                            if tail_bone_name in dress.bones
                            and tail_bone_name in model.bones
                            and 0.01 < dress.bones[tail_bone_name].position.distance(dress_bone.position)
                        ]

                        if tail_far_bone_names and "指先" not in tail_far_bone_names[0]:
                            model_bone_position = model_matrixes[0, dress_bone.name].position
                            model_tail_position = model_matrixes[0, tail_far_bone_names[0]].position

                            dress_bone_position = dress_matrixes[0, dress_bone.name].position
                            dress_tail_position = dress_matrixes[0, tail_far_bone_names[0]].position

                            dress_fit_length_scale = (model_tail_position - model_bone_position).length() / (
                                (dress_tail_position - dress_bone_position).length() or 1
                            )
                        elif dress_bone.parent_index in dress_local_scales:
                            # 先がボーンが見つからない場合、親ボーンの比率と親ボーンとの長さ比から求め直す
                            dress_parent_fit_length_scale = dress_local_scales[dress_bone.parent_index].x + 1

                            dress_fit_length_scale = (
                                dress_parent_fit_length_scale
                                * dress_bone.tail_relative_position.length()
                                / dress.bones[dress_bone.parent_index].tail_relative_position.length()
                            )

                    if np.isclose(dress_fit_length_scale, 0.0):
                        dress_fit_length_scale = 1.0

                    # ちょっとだけ縮める
                    dress_fit_length_scale *= 0.97

                    if bone_setting.category not in dress_category_local_x_scales:
                        dress_category_local_x_scales[bone_setting.category] = []
                    dress_category_local_x_scales[bone_setting.category].append(dress_fit_length_scale)

                    if bone_setting.global_scalable:
                        dress_global_scales[dress_bone.index] = (
                            MVector3D(dress_fit_length_scale, dress_fit_length_scale, dress_fit_length_scale) - 1
                        )
                    else:
                        dress_local_scales[dress_bone.index] = MVector3D(dress_fit_length_scale - 1, 0, 0)

                    logger.debug(f"ボーン距離比率 [{dress_bone.name}][{dress_fit_length_scale:.3f}]")

                if bone_setting.local_scalable:
                    # 衣装の頂点ローカル位置を計算
                    dress_vertices = set(dress.vertices_by_bones.get(dress_bone.index, []))
                    if dress_vertices:
                        dress_deformed_local_positions = self.get_deformed_local_positions(
                            dress, dress_bone, bone_setting, dress_vertices, dress_matrixes
                        )

                        if dress_deformed_local_positions.any():
                            if bone_setting.category not in dress_local_positions:
                                dress_local_positions[bone_setting.category] = {}

                            dress_local_positions[bone_setting.category][dress_bone.name] = dress_deformed_local_positions

                            logger.debug(f"ボーン厚み比率 [{dress_bone.name}][{dress_deformed_local_positions[0]}]")

                    # 人物の頂点ローカル位置を計算
                    if dress_bone.name in model.bones:
                        model_bone = model.bones[dress_bone.name]

                        model_vertices = set(model.vertices_by_bones.get(model_bone.index, []))
                        if model_vertices:
                            model_deformed_local_positions = self.get_deformed_local_positions(
                                model, model_bone, bone_setting, model_vertices, model_matrixes
                            )

                            if bone_setting.category not in model_local_positions:
                                model_local_positions[bone_setting.category] = {}

                            model_local_positions[bone_setting.category][model_bone.name] = model_deformed_local_positions

            else:
                if (
                    0 <= dress_bone.parent_index
                    and dress_bone.parent_index in dress.bones
                    and dress.bones[dress_bone.parent_index].is_standard
                ):
                    # 親ボーンが準標準の場合
                    dress_parent_bone = dress.bones[dress_bone.parent_index]
                    bone_setting = DRESS_STANDARD_BONE_NAMES[dress_parent_bone.name]

                    if bone_setting.local_scalable:
                        dress_matrixes = dress_motion.animate_bone([0], dress, append_ik=False)

                        # 衣装の頂点ローカル位置を計算
                        dress_vertices = set(dress.vertices_by_bones.get(dress_bone.index, []))
                        if dress_vertices:
                            dress_deformed_local_positions = self.get_deformed_local_positions(
                                dress, dress_bone, bone_setting, dress_vertices, dress_matrixes
                            )

                            if dress_deformed_local_positions.any():
                                if bone_setting.category not in dress_local_positions:
                                    dress_local_positions[bone_setting.category] = {}

                                dress_local_positions[bone_setting.category][dress_bone.name] = dress_deformed_local_positions

                                logger.debug(f"ボーン厚み比率 [{dress_bone.name}][{dress_deformed_local_positions[0]}]")

                        # 人物の頂点ローカル位置を計算
                        if dress_bone.name in model.bones:
                            model_bone = model.bones[dress_bone.name]

                            model_vertices = set(model.vertices_by_bones.get(model_bone.index, []))
                            if model_vertices:
                                model_deformed_local_positions = self.get_deformed_local_positions(
                                    model, model_bone, bone_setting, model_vertices, model_matrixes
                                )

                                if bone_setting.category not in model_local_positions:
                                    model_local_positions[bone_setting.category] = {}

                                model_local_positions[bone_setting.category][model_bone.name] = model_deformed_local_positions

        # # dress_category_global_scales: dict[str, MVector3D] = {}
        dress_category_local_scales: dict[str, MVector3D] = {}

        logger.info("厚み比率")

        for category in dress_local_positions.keys():
            if category not in model_local_positions:
                continue

            model_category_local_positions = model_local_positions[category]
            dress_category_local_positions = dress_local_positions[category]

            category_local_scales: list[np.ndarray] = []
            for bone_name, dress_bone_local_positions in dress_category_local_positions.items():
                if bone_name in model_category_local_positions:
                    model_filtered_local_positions = filter_values(model_category_local_positions[bone_name])
                    dress_filtered_local_positions = filter_values(dress_bone_local_positions)

                    model_local_distance = np.max(model_filtered_local_positions, axis=0) - np.min(model_filtered_local_positions, axis=0)
                    dress_local_distance = np.max(dress_filtered_local_positions, axis=0) - np.min(dress_filtered_local_positions, axis=0)

                    category_local_scale = MVector3D(*model_local_distance).one() / MVector3D(*dress_local_distance).one()
                    category_local_scales.append(category_local_scale.vector)

            local_scale = np.ones(3) if not category_local_scales else np.mean(category_local_scales, axis=0)
            # Xスケール±αより大きくはしない
            avg_x_scale = np.mean([np.max(dress_category_local_x_scales[category]), np.mean(dress_category_local_x_scales[category])])
            if "指" == category:
                # 指はあんまり太くしない
                avg_x_scale *= 0.6

            if category in ("体幹", "首根元"):
                # 体幹系はYZ別々にスケーリングする
                local_scale_y = max(min(local_scale[1], avg_x_scale * 1.2), avg_x_scale * 0.9) - 1
                local_scale_z = max(min(local_scale[2], avg_x_scale * 1.2), avg_x_scale * 0.9) - 1
                dress_category_local_scales[category] = MVector3D(0, local_scale_y, local_scale_z)
                logger.info("-- 厚み比率 [{b}][y={y:.3f})][z={z:.3f})]", b=category, y=(local_scale_y + 1), z=(local_scale_z + 1))
            else:
                local_scale_value = max(min(np.mean([local_scale[1], local_scale[2]]), avg_x_scale * 1.2), avg_x_scale * 0.9) - 1
                dress_category_local_scales[category] = MVector3D(0, local_scale_value, local_scale_value)
                logger.info("-- 厚み比率 [{b}][y={s:.3f})][z={s:.3f})]", b=category, s=(local_scale_value + 1))

            if "腕" == category and "肩" not in dress_category_local_scales:
                # 腕だけ比率が分かってて、肩が無い場合、腕の比率をコピーする
                dress_category_local_scales["肩"] = MVector3D(0, local_scale_value, local_scale_value)

        logger.info("ボーンフィッティング")

        # つま先IKの親を辿って足IK計算を先に済ませる
        for tail_bone_name in ("右つま先ＩＫ", "左つま先ＩＫ"):
            if tail_bone_name in dress.bones:
                for bone_name in dress.bone_trees[tail_bone_name].names:
                    dress_bone = dress.bones[bone_name]
                    if dress_bone.index in dress_offset_positions or not model_matrixes.exists(0, bone_name):
                        continue

                    dress_matrixes = dress_motion.animate_bone([0], dress, [tail_bone_name], append_ik=False)

                    dress_bone_fit_position = model_matrixes[0, bone_name].position
                    dress_bone_position = dress_matrixes[0, bone_name].position

                    if "つま先ＩＫ" in dress_bone.name:
                        # つま先ＩＫは Y=0 に固定する
                        dress_bone_fit_position.y = 0

                    dress_offset_position = dress_bone_fit_position - dress_bone_position
                    dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
                        BoneMorphOffset(
                            dress_bone.index,
                            position=dress_offset_position,
                        )
                    )
                    dress_offset_positions[dress_bone.index] = dress_offset_position

                    logger.debug(
                        f"-- -- 移動オフセット[{dress_bone.name}][{dress_offset_position}]"
                        + f"[fit={dress_bone_fit_position}][dress={dress_bone_position}]"
                    )

                    if bone_setting.local_scalable:
                        # ローカルスケール自体はひとまとめにしたもの
                        dress_local_thick_scale = dress_category_local_scales.get(bone_setting.category, MVector3D())
                        dress_local_scale = dress_local_scales.get(dress_bone.index, MVector3D())
                        dress_local_scales[dress_bone.index] = dress_local_scale + dress_local_thick_scale

                        dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
                            BoneMorphOffset(
                                dress_bone.index,
                                local_scale=dress_local_scale,
                            )
                        )

        # 変形順序に合わせて、フィッティングを行う
        for i, dress_bone_index in enumerate(dress.bones.bone_link_indexes):
            logger.count(
                "ボーンフィッティング",
                index=i,
                total_index_count=dress_bone_count,
                display_block=10,
            )

            dress_bone = dress.bones[dress_bone_index]
            bone_name = dress_bone.name

            if dress_bone.index in dress_offset_positions or dress_bone.index in dress_offset_qqs:
                # 既に計算済みの場合、スルー
                continue

            # 自分までのボーンツリーの中で準標準である最後のボーン
            parent_standard_bones = [
                b for b in dress.bone_trees[bone_name].get_standard() if b.name in model.bones and b.index != dress_bone.index
            ]

            if not parent_standard_bones:
                # 準標準にまったく紐付いてない場合スルー
                continue

            dress_parent_standard_bone = parent_standard_bones[-1]
            dress_parent_bone_setting = DRESS_STANDARD_BONE_NAMES[dress_parent_standard_bone.name]

            # dress_bone_parent_scale = MVector3D()

            # 準標準の子ボーン名
            standard_child_names = [b.name for b in dress.bone_trees.get_standard_children(dress_bone.name) if b.name in model.bones]

            # if not dress_bone.is_standard and not standard_child_names:
            #     # 準標準では無く、子どもに準標準がいない場合、親のスケールをそのまま流用
            #     dress_local_thick_scale_value = dress_category_local_scales.get(dress_parent_bone_setting.category, 0.0)

            #     # ローカルスケール自体はひとまとめにしたもの
            #     dress_local_scale = dress_local_scales.get(dress_bone.index, MVector3D())
            #     dress_local_scale.y = dress_local_thick_scale_value
            #     dress_local_scale.z = dress_local_thick_scale_value
            #     dress_local_scales[dress_bone.index] = dress_local_scale

            #     # ローカルスケールYZだけ付与（ローカルXは距離比率時に与えている）
            #     dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
            #         BoneMorphOffset(
            #             dress_bone.index,
            #             local_scale=MVector3D(0, dress_local_thick_scale_value, dress_local_thick_scale_value),
            #         )
            #     )

            if dress_bone.is_standard and bone_name in dress.bones and bone_name in model.bones:
                # 現在の衣装ボーン位置を求める
                dress_matrixes = dress_motion.animate_bone([0], dress, append_ik=False)

                # 準標準かつ人物・衣装の両方にボーンがある場合、準標準フィッティング
                bone_setting = DRESS_STANDARD_BONE_NAMES[bone_name]
                model_bone = model.bones[bone_name]

                tail_far_bone_names = [
                    tail_bone_name
                    for tail_bone_name in bone_setting.tails
                    if tail_bone_name in dress.bones
                    and tail_bone_name in model.bones
                    and 0.01 < dress.bones[tail_bone_name].position.distance(dress_bone.position)
                ]

                # parent_far_bone_names = [
                #     parent_bone_name
                #     for parent_bone_name in bone_setting.parents
                #     if parent_bone_name in dress.bones
                #     and parent_bone_name in model.bones
                #     and 0.01 < dress.bones[parent_bone_name].position.distance(dress_bone.position)
                # ]

                if bone_setting.translatable:
                    # 移動計算 ------------------

                    if "ひざ" in bone_name:
                        leg_bone_name = f"{bone_name[0]}足"
                        leg_ik_bone_name = f"{bone_name[0]}足ＩＫ"

                        model_leg_position = model_matrixes[0, leg_bone_name].position
                        model_knee_position = model_matrixes[0, bone_name].position
                        model_ankle_position = model_matrixes[0, leg_ik_bone_name].position

                        dress_leg_position = dress_matrixes[0, leg_bone_name].position
                        dress_knee_position = dress_matrixes[0, bone_name].position
                        dress_leg_ik_position = dress_matrixes[0, leg_ik_bone_name].position

                        knee_new_position = align_triangle(
                            model_leg_position,
                            model_ankle_position,
                            model_knee_position,
                            dress_leg_position,
                            dress_leg_ik_position,
                        )

                        # # XY位置は人物側のひざ位置に合わせる
                        # knee_new_position.y = model.bones[bone_name].position.y

                        # # Z位置は少し手前に出す
                        # knee_new_position.z -= dress_leg_position.distance(dress_leg_ik_position) * 0.03

                        dress_bone_fit_position = knee_new_position
                        dress_bone_position = dress_knee_position
                    elif "足首" in bone_name:
                        leg_ik_bone_name = f"{bone_name[0]}足ＩＫ"

                        dress_bone_fit_position = dress_matrixes[0, leg_ik_bone_name].position
                        dress_bone_position = dress_matrixes[0, bone_name].position
                    elif "足先EX" in bone_name:
                        leg_ik_bone_name = f"{bone_name[0]}足ＩＫ"
                        toe_ik_bone_name = f"{bone_name[0]}つま先ＩＫ"

                        dress_leg_ik_position = dress_matrixes[0, leg_ik_bone_name].position
                        dress_toe_ik_position = dress_matrixes[0, toe_ik_bone_name].position
                        dress_bone_position = dress_matrixes[0, bone_name].position

                        dress_bone_fit_position = align_triangle(
                            dress.bones[leg_ik_bone_name].position,
                            dress.bones[toe_ik_bone_name].position,
                            dress.bones[bone_name].position,
                            dress_leg_ik_position,
                            dress_toe_ik_position,
                        )

                    elif "つま先" in bone_name:
                        toe_ik_bone_name = f"{bone_name[0]}つま先ＩＫ"

                        dress_bone_fit_position = dress_matrixes[0, toe_ik_bone_name].position
                        dress_bone_position = dress_matrixes[0, bone_name].position
                    elif bone_name in ("右肩", "左肩"):
                        dress_bone_fit_position = dress_matrixes[0, f"{bone_name}P"].position
                        dress_bone_position = dress_matrixes[0, bone_name].position
                    elif bone_name in ("右腕", "左腕"):
                        dress_bone_fit_position = dress_matrixes[0, f"{bone_name[0]}肩C"].position
                        dress_bone_position = dress_matrixes[0, bone_name].position
                    # elif parent_far_bone_names and tail_far_bone_names:
                    #     tail_bone_name = tail_far_bone_names[0]
                    #     parent_bone_name = parent_far_bone_names[0]

                    #     model_tail_position = model_matrixes[0, tail_bone_name].position
                    #     model_target_position = model_matrixes[0, bone_name].position
                    #     model_parent_position = model_matrixes[0, parent_bone_name].position

                    #     dress_bone_position = dress_matrixes[0, bone_name].position
                    #     dress_parent_position = dress_matrixes[0, parent_bone_name].position

                    #     dress_bone_fit_position = align_triangle(
                    #         model_tail_position,
                    #         model_parent_position,
                    #         model_target_position,
                    #         model_tail_position,
                    #         dress_parent_position,
                    #     )
                    else:
                        dress_bone_fit_position = model_matrixes[0, bone_name].position
                        dress_bone_position = dress_matrixes[0, bone_name].position
                        # dress_bone_fit_position = (
                        #     dress_matrixes[0, bone_name].global_matrix.inverse() * model_matrixes[0, bone_name].position
                        # )
                        # dress_bone_position = MVector3D()

                    dress_offset_position = dress_bone_fit_position - dress_bone_position
                    dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
                        BoneMorphOffset(
                            dress_bone.index,
                            position=dress_offset_position,
                        )
                    )
                    dress_offset_positions[dress_bone.index] = dress_offset_position

                    logger.debug(
                        f"-- -- 移動オフセット[{dress_bone.name}][{dress_offset_position}]"
                        + f"[fit={dress_bone_fit_position}][dress={dress_bone_position}]"
                    )

                if bone_setting.rotatable:
                    # 回転計算 ------------------
                    # if bone_name in ("右腕", "左腕") and f"{bone_name[0]}手首" in dress.bones and f"{bone_name[0]}手首" in model.bones:
                    #     # 腕だけは手首を参照する（直線角度を測る）
                    #     tail_far_bone_names = [f"{bone_name[0]}手首"]

                    dress_offset_qq = MQuaternion()

                    # モデルのボーンの向きに衣装を合わせる
                    if not bone_setting.rotate_cancel:
                        # キャンセルしない場合、角度差を補正する
                        dress_matrixes = dress_motion.animate_bone([0], dress, append_ik=False)

                        model_bone_position = model_matrixes[0, bone_name].position
                        dress_bone_position = dress_matrixes[0, bone_name].position

                        if tail_far_bone_names:
                            dress_tail_offset_qqs: list[MQuaternion] = []

                            for i, tail_bone_name in enumerate(tail_far_bone_names):
                                model_tail_vector = model_matrixes[0, tail_bone_name].position - model_bone_position
                                dress_tail_vector = dress_matrixes[0, tail_bone_name].position - dress_bone_position

                                if 0 < model_tail_vector.length() and 0 < dress_tail_vector.length():
                                    # 衣装：自分の方向
                                    dress_slope_qq = dress_tail_vector.to_local_matrix4x4().to_quaternion()

                                    # 人物：自分の方向
                                    model_slope_qq = model_tail_vector.to_local_matrix4x4().to_quaternion()

                                    dress_offset_qq = model_slope_qq * dress_slope_qq.inverse()

                                    _, _, _, dress_offset_yz_qq = dress_offset_qq.separate_by_axis(dress_bone.local_axis)

                                    # X軸（捩り）成分を除去した値のみ保持
                                    dress_tail_offset_qqs.append(dress_offset_yz_qq)

                                    if "手首" not in bone_name:
                                        # 手首以外は最初の一件だけで終了
                                        break

                            if dress_tail_offset_qqs:
                                dress_offset_qq = dress_tail_offset_qqs[0]
                                for qq in dress_tail_offset_qqs[1:]:
                                    dress_offset_qq = MQuaternion.slerp(dress_offset_qq, qq, 0.5)

                        # if tail_far_bone_names:
                        #     dress_bone_position = dress_matrixes[0, bone_name].position

                        #     if "手首" in bone_name:
                        #         dress_tail_offset_qqs: list[MQuaternion] = []

                        #         for tail_bone_name in tail_far_bone_names:
                        #             model_tail_position = model_matrixes[0, tail_bone_name].position
                        #             dress_tail_position = dress_matrixes[0, tail_bone_name].position

                        #             model_tail_vector = model_tail_position - model_bone_position
                        #             dress_tail_vector = dress_tail_position - dress_bone_position

                        #             if 0 < model_tail_vector.length() and 0 < dress_tail_vector.length():
                        #                 # 衣装：自分の方向
                        #                 dress_slope_qq = (dress_tail_position - dress_bone_position).to_local_matrix4x4().to_quaternion()

                        #                 # 人物：自分の方向
                        #                 model_slope_qq = (model_tail_position - model_bone_position).to_local_matrix4x4().to_quaternion()

                        #                 dress_offset_qq = model_slope_qq * dress_slope_qq.inverse()

                        #                 dress_tail_offset_qqs.append(dress_offset_qq)

                        #         if dress_tail_offset_qqs:
                        #             dress_offset_qq = dress_tail_offset_qqs[0]
                        #             for qq in dress_tail_offset_qqs[1:]:
                        #                 dress_offset_qq = MQuaternion.slerp(dress_offset_qq, qq, 0.5)
                        #     else:
                        #         model_tail_position = model_matrixes[0, tail_far_bone_names[0]].position
                        #         dress_tail_position = dress_matrixes[0, tail_far_bone_names[0]].position
                        # else:
                        #     dress_bone_position = dress_matrixes[0, bone_name].position
                        #     dress_tail_position = dress_matrixes[0, bone_name].global_matrix * dress_bone.tail_relative_position

                        #     model_tail_position = model_matrixes[0, bone_name].global_matrix * model_bone.tail_relative_position

                        # model_tail_vector = model_tail_position - model_bone_position
                        # dress_tail_vector = dress_tail_position - dress_bone_position

                        # if 0 < model_tail_vector.length() and 0 < dress_tail_vector.length():
                        #     # 衣装：自分の方向
                        #     dress_slope_qq = (dress_tail_position - dress_bone_position).to_local_matrix4x4().to_quaternion()

                        #     # 人物：自分の方向
                        #     model_slope_qq = (model_tail_position - model_bone_position).to_local_matrix4x4().to_quaternion()

                        #     dress_offset_qq = model_slope_qq * dress_slope_qq.inverse()

                    # for tree_bone_index in reversed(dress.bone_trees[bone_name].indexes[:-1]):
                    #     # 自分より親は逆回転させる
                    #     dress_offset_qq *= dress_offset_qqs.get(tree_bone_index, MQuaternion()).inverse()

                    dress_offset_qqs[dress_bone.index] = dress_offset_qq

                    dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
                        BoneMorphOffset(
                            dress_bone.index,
                            qq=dress_offset_qq,
                        )
                    )

                    logger.debug(f"-- -- 回転オフセット[{dress_bone.name}][{dress_offset_qq.to_euler_degrees()}]")

                if bone_setting.local_scalable:
                    dress_local_thick_scale = dress_category_local_scales.get(bone_setting.category, MVector3D())

                    if bone_setting.category == "指":
                        # 指は厚みと同じだけの長さスケールにする
                        dress_local_scale = MVector3D(dress_local_thick_scale.y, dress_local_thick_scale.y, dress_local_thick_scale.y)
                    else:
                        # ローカルスケール自体はひとまとめにしたもの
                        dress_local_scale = dress_local_scales.get(dress_bone.index, MVector3D()) + dress_local_thick_scale
                    dress_local_scales[dress_bone.index] = dress_local_scale

                    dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
                        BoneMorphOffset(
                            dress_bone.index,
                            local_scale=dress_local_scale,
                        )
                    )

            else:
                # 準標準外、もしくは準標準でもボーンが揃ってない場合、準標準外フィッティング
                dress_offset_position = MVector3D()
                dress_offset_qq = MQuaternion()

                # 現在の衣装ボーン位置を求める
                dress_matrixes = dress_motion.animate_bone([0], dress, append_ik=False)

                # 子ボーン
                tail_far_bone_names = (
                    [
                        tail_bone_name
                        for tail_bone_name in dress_parent_bone_setting.tails
                        if tail_bone_name in dress.bones and tail_bone_name in model.bones
                    ]
                    if not standard_child_names
                    else standard_child_names
                )

                dress_parent_bone_position = dress_matrixes[0, dress_parent_standard_bone.name].position
                model_parent_bone_position = model_matrixes[0, dress_parent_standard_bone.name].position

                dress_bone_position = dress_matrixes[0, dress_bone.name].position
                dress_relative_position = dress_bone_position - dress_parent_bone_position

                # 人物で親ボーンを基準として相対位置からどこにあるべきかを求め直す
                model_deformed_position = model_matrixes[0, dress_parent_standard_bone.name].global_matrix * dress_relative_position

                if tail_far_bone_names:
                    model_tail_position = model_matrixes[0, tail_far_bone_names[0]].position
                    dress_tail_position = dress_matrixes[0, tail_far_bone_names[0]].position
                else:
                    model_tail_position = model_matrixes[0, dress_parent_standard_bone.name].global_matrix * dress_relative_position
                    dress_tail_position = dress_matrixes[0, dress_parent_standard_bone.name].global_matrix * dress_relative_position

                dress_bone_fit_position = align_triangle(
                    dress_parent_bone_position,
                    dress_tail_position,
                    dress_bone_position,
                    model_parent_bone_position,
                    model_tail_position,
                )

                dress_offset_position = dress_bone_fit_position - model_deformed_position

                if dress_parent_bone_setting.category not in ("上半身", "下半身", "体幹", "首", "頭"):
                    # 体幹以外は子ボーンの位置を合わせるよう回転させる
                    original_slope_vector = dress_bone_fit_position - dress_parent_bone_position
                    deformed_slope_vector = model_deformed_position - dress_parent_bone_position

                    if 0 < original_slope_vector.length() and 0 < deformed_slope_vector.length():
                        # 子ボーンとの距離がある場合のみ、回転補正
                        original_slope_qq = original_slope_vector.to_local_matrix4x4().to_quaternion()
                        deformed_slope_qq = deformed_slope_vector.to_local_matrix4x4().to_quaternion()
                        dress_offset_qq = original_slope_qq * deformed_slope_qq.inverse()
                else:
                    # 角度は元々の向きと同じにする
                    for tree_bone_index in reversed(dress.bone_trees[dress_bone.name].indexes[:-1]):
                        dress_offset_qq *= dress_offset_qqs.get(tree_bone_index, MQuaternion()).inverse()

                logger.debug(
                    f"-- -- 移動オフセット[{dress_bone.name}][{dress_offset_position}]"
                    + f"[fit={dress_bone_fit_position}][dress={model_deformed_position}]"
                )
                logger.debug(f"-- -- 回転オフセット[{dress_bone.name}][{dress_offset_qq.to_euler_degrees()}]")

                dress_offset_positions[dress_bone.index] = dress_offset_position
                dress_offset_qqs[dress_bone.index] = dress_offset_qq
                # dress_local_scales[dress_bone.index] = dress_bone_parent_scale

                dress.morphs[DRESS_BONE_FITTING_NAME].offsets.append(
                    BoneMorphOffset(
                        dress_bone.index,
                        position=dress_offset_position,
                        qq=dress_offset_qq,
                    )
                )

        # ----- 変形結果 -------------
        from datetime import datetime
        from service.usecase.save_usecase import SaveUsecase

        SaveUsecase().save(
            model,
            dress,
            VmdMotion(),
            dress_motion,
            os.path.join("E:/MMD/Dressup/output", f"{datetime.now():%Y%m%d_%H%M%S}_dress_bone_deform.pmx"),
            dict([(m.name, 0.0) for m in model.materials]),
            dict([(m.name, False) for m in model.materials]),
            dict([(m.name, 1.0) for m in dress.materials]),
            dict([(m.name, False) for m in dress.materials]),
            {},
            {},
            {},
            {},
        )
        # ----- 変形結果 -------------

        return dress_local_scales, dress_global_scales, dress_offset_positions, dress_offset_qqs

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
        bone_setting: DressBoneSetting,
        model_vertices: set[int],
        matrixes: VmdBoneFrameTrees,
        is_filter: bool = False,
        is_z_positive: bool = False,
    ) -> np.ndarray:
        model_deformed_vertices = self.get_deformed_positions(model, model_vertices, matrixes)

        if is_z_positive:
            # Z方向が＋のもののみ対象とする場合、抽出
            model_deformed_vertices = model_deformed_vertices[model_deformed_vertices[..., 2] >= 0]

        model_bone_position = matrixes[0, bone.name].position
        model_tail_position = matrixes[0, bone.name].global_matrix * bone.tail_relative_position

        if bone.name in (
            "右胸",
            "左胸",
            "左足首",
            "右足首",
            "左足首D",
            "右足首D",
            "左足先EX",
            "右足先EX",
        ):
            model_tail_position = model_bone_position + MVector3D(0, 0, -1)

        model_local_positions = calc_local_positions(
            model_deformed_vertices,
            model_bone_position,
            model_tail_position,
        )

        if is_filter:
            return filter_values(model_local_positions)

        return model_local_positions
