import os

import numpy as np

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MQuaternion, MVector3D, MVector4D, calc_local_positions, align_triangle, filter_values
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
)
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from service.usecase.dress_bone_setting import (
    DRESS_STANDARD_BONE_NAMES,
    FIT_INDIVIDUAL_BONE_NAMES,
    LOCAL_SCALE_WEIGHT_BONE_NAMES,
    DressBoneSetting,
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

    def add_mismatch_bones(self, model: PmxModel, dress: PmxModel) -> None:
        """準標準ボーンの不足分を追加"""
        # 必ず追加するボーン
        add_bone_names = {
            "全ての親",
            "グルーブ",
            "腰",
            "上半身2",
            "左肩P",
            "左肩C",
            "右肩P",
            "右肩C",
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

        # 準標準ボーンで足りないボーン名を抽出
        short_model_bone_names = set(list(DRESS_STANDARD_BONE_NAMES.keys())) - set(model.bones.names)
        short_dress_bone_names = set(list(DRESS_STANDARD_BONE_NAMES.keys())) - set(dress.bones.names)

        # 両方の片方にしかないボーン名を抽出
        mismatch_bone_names = (short_model_bone_names ^ short_dress_bone_names) | add_bone_names

        # ミスマッチボーンで追加する必要のあるボーン名を抽出(順番を保持する)
        short_mismatch_model_bone_names = [
            bname for bname in DRESS_STANDARD_BONE_NAMES.keys() if bname in (mismatch_bone_names - set(model.bones.names))
        ]
        short_mismatch_dress_bone_names = [
            bname for bname in DRESS_STANDARD_BONE_NAMES.keys() if bname in (mismatch_bone_names - set(dress.bones.names))
        ]

        logger.info("人物: 追加対象ボーン: {b}", b=", ".join(short_mismatch_model_bone_names))
        logger.info("衣装: 追加対象ボーン: {b}", b=", ".join(short_mismatch_dress_bone_names))

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

        for bone_name in ("左胸", "右胸"):
            # 胸ボーンの追加
            if bone_name in short_mismatch_model_bone_names and self.insert_bust(model, bone_name):
                logger.info("-- 人物: ボーン追加: {b}", b=bone_name)

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

        for bone_name in ("左胸", "右胸"):
            # 胸ボーンの追加
            if bone_name in short_mismatch_dress_bone_names and self.insert_bust(dress, bone_name):
                logger.info("-- 衣装: ボーン追加: {b}", b=bone_name)

    def replace_bust_weights(self, model: PmxModel, bone_names: list[str]) -> None:
        """胸ウェイトの置き換え"""

        # 既に胸にウェイトが乗っている場合、一旦上半身2に乗せ直す
        upper_vertex_indexes = [bone.index for bone in model.bones if "上半身" in bone.name]

        for bust_bone_name in ("右胸", "左胸"):
            if bust_bone_name not in model.bones:
                continue

            bust_bone = model.bones[bust_bone_name]

            bust_upper_position = bust_bone.position + (model.bones["首根元"].position - model.bones["上半身"].position) * 0.5
            bust_upper_position.z = 0
            bust_lower_position = bust_bone.position + (model.bones["首根元"].position - model.bones["上半身"].position) * -0.3
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
        replace_bone_names = ("首根元", "頭", "上半身")
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

    def replace_upper3(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """上半身3のボーン置き換え"""
        replace_bone_names = ("上半身", "頭", "上半身3")
        if not (model.bones.exists(replace_bone_names) and dress.bones.exists(replace_bone_names)):
            return []

        is_add, diff = self.replace_bone_position(model, dress, *replace_bone_names, is_fix_x_zero=True)

        return ["上半身3"] if is_add else []

    def replace_bust(self, model: PmxModel, dress: PmxModel) -> list[str]:
        """胸系のボーン置き換え"""
        bust_added_bone_names: list[str] = []
        for bust_bone_name in ("右胸", "左胸"):
            replace_bone_names = ("上半身", "頭", bust_bone_name)
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

        model_from_pos = model.bones[from_name].position
        model_replace_pos = model.bones[replace_name].position
        model_to_pos = model.bones[to_name].position
        dress_from_pos = dress.bones[from_name].position
        dress_replace_pos = dress.bones[replace_name].position
        dress_to_pos = dress.bones[to_name].position

        # 元ボーン-置換ボーン ベースで求めた時の位置 ---------------

        # 衣装の置換ボーンの位置を求め直す
        dress_replace_new_pos = align_triangle(model_from_pos, model_to_pos, model_replace_pos, dress_from_pos, dress_to_pos)
        dress_replace_diff_pos = dress_replace_new_pos - dress_replace_pos
        if is_fix_x_zero:
            dress_replace_diff_pos.x = 0

        dress.bones[replace_name].position += dress_replace_diff_pos
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

        for morph_name, (
            target_bone_names,
            move_target_bone_names,
            child_scale_morph_names,
            child_rotation_morph_names,
        ) in FIT_INDIVIDUAL_BONE_NAMES.items():
            if not [bone_name for bone_name in target_bone_names if bone_name in dress.bones]:
                # 処理対象ボーンがなければスルー
                continue

            target_bone_indexes: list[int] = []

            # 子どものスケーリング対象もモーフに入れる
            child_scale_bone_names = list(
                set(
                    [
                        child_bone_name
                        for child_morph_name in child_scale_morph_names
                        for child_bone_name in FIT_INDIVIDUAL_BONE_NAMES[child_morph_name][0]
                        if child_bone_name in dress.bones
                    ]
                )
            )

            child_rotation_bone_names = list(
                set(
                    [
                        child_bone_name
                        for child_morph_name in child_rotation_morph_names
                        for child_bone_name in FIT_INDIVIDUAL_BONE_NAMES[child_morph_name][0]
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

                target_all_bone_names = list(target_bone_names)
                if "S" in axis_name:
                    # スケールの時だけ子どもを加味する
                    target_all_bone_names = list(target_bone_names) + child_scale_bone_names
                elif "M" in axis_name:
                    # 移動の場合はP系列も動かす
                    target_all_bone_names = list(target_bone_names) + list(move_target_bone_names)

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

        dress_bone_fitting_morph = Morph(name="BoneFitting")
        dress_bone_fitting_morph.is_system = True
        dress_bone_fitting_morph.morph_type = MorphType.BONE

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().animate_bone([0], model)

        logger.info("フィッティングボーンモーフ：グローバルスケール計算", decoration=MLogger.Decoration.LINE)
        dress_offset_scales, dress_fit_scales, dress_category_scale_values = self.get_dress_global_bone_scale_offsets(
            model, dress, model_matrixes
        )
        # dress_offset_scales = {}
        # dress_fit_scales = {}

        logger.info("フィッティングボーンモーフ：ローカルスケール計算", decoration=MLogger.Decoration.LINE)
        dress_offset_local_scales = self.get_dress_bone_local_scale_offsets(
            model, dress, dress_offset_scales, dress_category_scale_values, model_matrixes
        )
        # dress_offset_local_scales = {}

        logger.info("フィッティングボーンモーフ：オフセット計算", decoration=MLogger.Decoration.LINE)
        dress_offset_positions, dress_offset_qqs = self.get_dress_global_bone_offsets(
            model, dress, dress_offset_scales, dress_offset_local_scales, model_matrixes
        )
        # dress_offset_positions = {}
        # dress_offset_qqs = {}

        dress_part_offset_positions: dict[str, list[np.ndarray]] = {}
        dress_part_offset_degrees: dict[str, list[np.ndarray]] = {}

        for dress_bone in dress.bones:
            if not (dress_bone.is_standard and ("左" in dress_bone.name or "右" in dress_bone.name)):
                # 準標準ボーンかつ左右のみ対象
                continue
            if not (dress_bone.index in dress_offset_positions or dress_bone.index in dress_offset_qqs):
                # オフセットが無い場合スルー
                continue

            dress_offset_position = dress_offset_positions.get(dress_bone.index, MVector3D())
            dress_offset_qq = dress_offset_qqs.get(dress_bone.index, MQuaternion())

            part_name = dress_bone.name[1:]

            if part_name not in dress_part_offset_positions:
                dress_part_offset_positions[part_name] = []
                dress_part_offset_degrees[part_name] = []

            dress_part_offset_positions[part_name].append(dress_offset_position.abs().vector)
            dress_part_offset_degrees[part_name].append(dress_offset_qq.to_euler_degrees().abs().vector)

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

            if dress_bone.name[1:] in dress_part_offset_positions and dress_offset_position:
                # 左右の場合、平均値を採用する
                dress_offset_position.vector = np.mean(dress_part_offset_positions[dress_bone.name[1:]], axis=0) * np.sign(
                    dress_offset_position.vector
                )

                if "左" in dress_bone.name:
                    dress_offset_position.x = abs(dress_offset_position.x)
                else:
                    dress_offset_position.x = -abs(dress_offset_position.x)

            if dress_bone.name[1:] in dress_part_offset_degrees and dress_offset_qq:
                dress_offset_qq = MQuaternion.from_euler_degrees(
                    *np.mean(dress_part_offset_degrees[dress_bone.name[1:]], axis=0) * np.sign(dress_offset_qq.to_euler_degrees().vector)
                )

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

    def get_dress_global_bone_scale_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        model_matrixes: VmdBoneFrameTrees,
    ) -> tuple[dict[int, MVector3D], dict[int, MVector3D], dict[str, float]]:
        dress_standard_count = len(DRESS_STANDARD_BONE_NAMES)

        # 衣装の初期姿勢を求める
        logger.info("-- 衣装初期姿勢計算")
        dress_matrixes = VmdMotion().animate_bone([0], dress, append_ik=False)

        dress_scale_values: dict[str, list[float]] = {}

        for i, (bone_name, bone_setting) in enumerate(list(DRESS_STANDARD_BONE_NAMES.items())):
            logger.count(
                "グローバルスケール計算",
                index=i,
                total_index_count=dress_standard_count,
                display_block=50,
            )

            if not (bone_name in dress.bones and bone_name in model.bones):
                # 人物と衣装の両方にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]
            model_bone = model.bones[dress_bone.name]

            if not bone_setting.global_scalable:
                continue

            if bone_setting.category == "足ＩＫ":
                # 足IKの比率は足ボーンから足IKボーンまでの直線距離とする
                dress_fit_length_scale = (model_bone.position - model.bones[bone_name[:2]].position).length() / (
                    (dress_bone.position - dress.bones[bone_name[:2]].position).length() or 1
                )
            elif bone_setting.category == "つま先ＩＫ":
                # つま先IKの比率はグローバルZ方向だけ合わせる
                dress_fit_length_scale = (model_bone.position - model.bones[bone_name[:4]].position).z / (
                    (dress_bone.position - dress.bones[bone_name[:4]].position).z or 1
                )
            else:
                model_bone_position = model_matrixes[0, bone_name].position
                model_tail_position = model_matrixes[0, bone_name].global_matrix * model_bone.tail_relative_position

                dress_bone_position = dress_matrixes[0, bone_name].position
                dress_tail_position = dress_matrixes[0, bone_name].global_matrix * dress_bone.tail_relative_position

                dress_fit_length_scale = (model_tail_position - model_bone_position).length() / (
                    (dress_tail_position - dress_bone_position).length() or 1
                )

            if bone_setting.category not in dress_scale_values:
                dress_scale_values[bone_setting.category] = []
            dress_scale_values[bone_setting.category].append(dress_fit_length_scale)

        # 胸はスケールキャンセルだけ入れる
        if "胸" not in dress_scale_values:
            dress_scale_values["胸"] = []
        dress_scale_values["胸"].append(1.0)

        dress_category_scale_values: dict[str, float] = {}
        for category, dress_scale_values_by_category in dress_scale_values.items():
            dress_category_scale_values[category] = float(np.min(dress_scale_values_by_category))

            logger.debug(
                f"グローバルスケール [{category}][{np.round(dress_scale_values_by_category, decimals=3)}]"
                + f"[{dress_category_scale_values[category]:.3f}]"
            )

        dress_offset_scales: dict[int, MVector3D] = {}
        dress_fit_scales: dict[int, MVector3D] = {}

        for i, (bone_name, bone_setting) in enumerate(list(DRESS_STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones):
                # 衣装にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]

            if not bone_setting.global_scalable:
                continue

            dress_fit_length_scale = dress_category_scale_values[bone_setting.category]
            dress_fit_scale = MVector3D(dress_fit_length_scale, dress_fit_length_scale, dress_fit_length_scale)

            # 親をキャンセルしていく
            dress_offset_scale = dress_fit_scale.copy()
            for tree_bone_index in reversed(dress.bone_trees[bone_name].indexes[:-1]):
                dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales.get(tree_bone_index, MVector3D(1, 1, 1))

            dress_fit_scales[dress_bone.index] = dress_fit_scale
            dress_offset_scales[dress_bone.index] = dress_offset_scale

            logger.info("-- グローバルスケール [{b}][{f:.3f}({o:.3f})]", b=bone_name, f=dress_fit_scale.x, o=dress_offset_scale.x)

        for dress_bone in dress.bones:
            # 準標準外のボーンは直近準標準ボーンのスケールを適用する
            if dress_bone.is_standard:
                continue

            dress_fit_scale = MVector3D(1.0, 1.0, 1.0)
            for bone_name in reversed(dress.bone_trees[dress_bone.name].get_standard().names):
                if bone_name in DRESS_STANDARD_BONE_NAMES and DRESS_STANDARD_BONE_NAMES[bone_name].category in dress_category_scale_values:
                    s = dress_category_scale_values[DRESS_STANDARD_BONE_NAMES[bone_name].category]
                    dress_fit_scale = MVector3D(s, s, s)
                    break

            # 親をキャンセルしていく
            dress_offset_scale = dress_fit_scale.copy()
            for tree_bone_index in reversed(dress.bone_trees[dress_bone.name].indexes[:-1]):
                dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales.get(tree_bone_index, MVector3D(1, 1, 1))

            dress_fit_scales[dress_bone.index] = dress_fit_scale
            dress_offset_scales[dress_bone.index] = dress_offset_scale

            logger.debug(f"-- グローバルスケール [{dress_bone.name}][{dress_fit_scale.x:.3f}]")

        return dress_offset_scales, dress_fit_scales, dress_category_scale_values

    def get_dress_global_bone_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_offset_scales: dict[int, MVector3D],
        dress_offset_local_scales: dict[int, MVector3D],
        model_matrixes: VmdBoneFrameTrees,
    ) -> tuple[dict[int, MVector3D], dict[int, MQuaternion]]:
        dress_standard_count = len(DRESS_STANDARD_BONE_NAMES)

        dress_motion = VmdMotion()

        dress_offset_positions: dict[int, MVector3D] = {}
        dress_fit_qqs: dict[int, MQuaternion] = {}
        dress_offset_qqs: dict[int, MQuaternion] = {}

        # z_direction = MVector3D(0, 0, -1)
        for i, (bone_name, bone_setting) in enumerate(list(DRESS_STANDARD_BONE_NAMES.items())):
            logger.count(
                "オフセット計算",
                index=i,
                total_index_count=dress_standard_count,
                display_block=5,
            )

            if not (bone_name in dress.bones and bone_name in model.bones):
                # 人物と衣装の両方にボーンがなければスルー
                continue

            dress_bone = dress.bones[bone_name]
            model_bone = model.bones[bone_name]

            if bone_setting.translatable:
                # 移動計算 ------------------

                model_bone_position = model_matrixes[0, bone_name].position

                dress_matrixes = dress_motion.animate_bone([0], dress, [bone_name], append_ik=False)
                dress_bone_position = dress_matrixes[0, bone_name].position

                dress_offset_position = model_bone_position - dress_bone_position
                dress_offset_positions[dress_bone.index] = dress_offset_position

                # キーフレとして追加
                mbf = dress_motion.bones[dress_bone.name][0]
                mbf.position = dress_offset_position
                dress_motion.bones[dress_bone.name].append(mbf)

                logger.debug(
                    f"-- -- 移動オフセット[{dress_bone.name}][{dress_offset_position}]"
                    + f"[model={model_bone_position}][dress={dress_bone_position}]"
                )

                if f"{bone_name}D" in dress.bones and "足" in bone_setting.category:
                    # 足Dがある場合、そっちにもコピー
                    d_dress_bone = dress.bones[f"{bone_name}D"]
                    dress_offset_positions[d_dress_bone.index] = dress_offset_position.copy()

                    # キーフレとして追加
                    mbf = dress_motion.bones[d_dress_bone.name][0]
                    mbf.position = dress_offset_position.copy()
                    dress_motion.bones[d_dress_bone.name].append(mbf)

                    logger.debug(
                        f"-- -- 移動オフセット[{d_dress_bone.name}][{dress_offset_position}]"
                        + f"[model={model_bone_position}][dress={dress_bone_position}]"
                    )

            if bone_setting.rotatable:
                # 回転計算 ------------------

                # モデルのボーンの向きに衣装を合わせる
                if dress_bone.name in ("頭", "左胸", "右胸", "左足首D", "右足首D", "左足首", "右足首"):
                    # 末端は親のキャンセルだけ行う
                    dress_offset_qq = MQuaternion()
                else:
                    model_bone_position = model_matrixes[0, bone_name].position
                    model_tail_position = model_matrixes[0, bone_name].global_matrix * model_bone.tail_relative_position

                    dress_matrixes = dress_motion.animate_bone([0], dress, [bone_name], append_ik=False)
                    dress_bone_position = dress_matrixes[0, bone_name].position
                    dress_tail_position = dress_matrixes[0, bone_name].global_matrix * dress_bone.tail_relative_position

                    # 衣装：自分の方向
                    dress_slope_qq = (dress_tail_position - dress_bone_position).to_local_matrix4x4().to_quaternion()

                    # 人物：自分の方向
                    model_slope_qq = (model_tail_position - model_bone_position).to_local_matrix4x4().to_quaternion()

                    dress_offset_qq = model_slope_qq * dress_slope_qq.inverse()
                    dress_fit_qqs[dress_bone.index] = dress_offset_qq.copy()

                for tree_bone_index in reversed(dress.bone_trees[bone_name].indexes[:-1]):
                    # 自分より親は逆回転させる
                    dress_offset_qq *= dress_offset_qqs.get(tree_bone_index, MQuaternion()).inverse()

                dress_offset_qqs[dress_bone.index] = dress_offset_qq

                # キーフレとして追加
                qbf = dress_motion.bones[dress_bone.name][0]
                qbf.rotation = dress_offset_qq
                dress_motion.bones[dress_bone.name].append(qbf)

                logger.debug(
                    f"-- -- 回転オフセット[{dress_bone.name}][{dress_offset_qq.to_euler_degrees()}]"
                    + f"[model={model_bone_position}][dress={dress_bone_position}]"
                )

                if f"{bone_name}D" in dress.bones and "足" in bone_setting.category:
                    # 足Dがある場合、そっちにもコピー
                    d_dress_bone = dress.bones[f"{bone_name}D"]
                    dress_offset_qqs[d_dress_bone.index] = dress_offset_qq.copy()

                    # キーフレとして追加
                    qbf = dress_motion.bones[d_dress_bone.name][0]
                    qbf.rotation = dress_offset_qq.copy()
                    dress_motion.bones[d_dress_bone.name].append(qbf)

                    logger.debug(
                        f"-- -- 回転オフセット[{d_dress_bone.name}][{dress_offset_qq.to_euler_degrees()}]"
                        + f"[model={model_bone_position}][dress={dress_bone_position}]"
                    )

            # キーフレとしてスケーリング追加
            sbf = dress_motion.bones[dress_bone.name][0]
            sbf.scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            sbf.local_scale = dress_offset_local_scales.get(dress_bone.index, MVector3D(1, 1, 1)) - 1
            dress_motion.bones[dress_bone.name].append(sbf)

        for dress_other_bone in dress.bones:
            if not (
                0 <= dress_other_bone.parent_index
                and dress_other_bone.parent_index in dress.bones
                and dress.bones[dress_other_bone.parent_index].is_standard
                and not dress.bone_trees.is_in_standard(dress_other_bone.name)
            ):
                continue

            # 親ボーンが準標準、かつ自身が準標準外の場合
            dress_offset_position = MVector3D()
            dress_offset_qq = MQuaternion()
            dress_parent_bone = dress.bones[dress_other_bone.parent_index]
            if DRESS_STANDARD_BONE_NAMES[dress_parent_bone.name].category in ("肩", "腕", "手首", "指"):
                # 腕系は親の変形を引き継ぐ
                original_parent_position = dress_parent_bone.position
                original_bone_position = dress_other_bone.position
                original_tail_position = dress_other_bone.position + dress_other_bone.tail_relative_position

                original_bone_slope_qq = (original_bone_position - original_parent_position).to_local_matrix4x4().to_quaternion()

                dress_matrixes = dress_motion.animate_bone([0], dress, [dress_other_bone.name], append_ik=False)

                # 変形後の位置
                deformed_parent_position = dress_matrixes[0, dress_parent_bone.name].position
                deformed_bone_position = dress_matrixes[0, dress_other_bone.name].position
                deformed_tail_position = dress_matrixes[0, dress_other_bone.name].global_matrix * dress_other_bone.tail_relative_position

                deformed_bone_slope_qq = (deformed_bone_position - deformed_parent_position).to_local_matrix4x4().to_quaternion()

                # 変形後にあるべき位置
                original_offset_slope_qq = deformed_bone_slope_qq * original_bone_slope_qq.inverse()

                dress_offset_mat = MMatrix4x4()
                dress_offset_mat.translate(original_parent_position)
                dress_offset_mat.rotate(original_offset_slope_qq)
                original_new_bone_position = dress_offset_mat * (original_bone_position - original_parent_position)

                dress_offset_position = original_new_bone_position - original_bone_position

                # キーフレとして追加
                mbf = dress_motion.bones[dress_other_bone.name][0]
                mbf.position = dress_offset_position.copy()
                dress_motion.bones[dress_other_bone.name].append(mbf)

                # 変形後の回転
                dress_matrixes = dress_motion.animate_bone([0], dress, [dress_other_bone.name], append_ik=False)

                # 変形後の位置
                deformed_parent_position = dress_matrixes[0, dress_parent_bone.name].position
                deformed_bone_position = dress_matrixes[0, dress_other_bone.name].position
                deformed_tail_position = dress_matrixes[0, dress_other_bone.name].global_matrix * dress_other_bone.tail_relative_position

                original_slope_qq = (original_tail_position - original_bone_position).to_local_matrix4x4().to_quaternion()
                deformed_slope_qq = (deformed_tail_position - deformed_bone_position).to_local_matrix4x4().to_quaternion()

                # 変形後の角度
                dress_offset_qq = deformed_slope_qq * original_slope_qq.inverse()

                for tree_bone_index in reversed(dress.bone_trees[dress_other_bone.name].indexes[:-1]):
                    # 自分より親は逆回転させる
                    dress_offset_qq *= dress_offset_qqs.get(tree_bone_index, MQuaternion()).inverse()

                # キーフレとして追加
                qbf = dress_motion.bones[dress_other_bone.name][0]
                qbf.rotation = dress_offset_qq.copy()
                dress_motion.bones[dress_other_bone.name].append(qbf)
            else:
                # 腕系以外は親のキャンセルだけ行う
                for tree_bone_index in reversed(dress.bone_trees[dress_other_bone.name].indexes[:-1]):
                    # 自分より親は逆回転させる
                    dress_offset_qq *= dress_offset_qqs.get(tree_bone_index, MQuaternion()).inverse()

            dress_offset_qqs[dress_other_bone.index] = dress_offset_qq
            dress_offset_positions[dress_other_bone.index] = dress_offset_position

            logger.debug(f"-- -- 準標準外オフセット[{dress_other_bone.name}][pos={dress_offset_position}][qq={dress_offset_qq.to_euler_degrees()}]")

        return dress_offset_positions, dress_offset_qqs

    def get_dress_bone_local_scale_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_offset_scales: dict[int, MVector3D],
        dress_category_scale_values: dict[str, float],
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
        logger.info("-- 衣装初期姿勢計算")
        dress_matrixes = dress_motion.animate_bone([0], dress)

        dress_local_positions: dict[str, np.ndarray] = {}
        model_local_positions: dict[str, np.ndarray] = {}
        for n, bone_name in enumerate(LOCAL_SCALE_WEIGHT_BONE_NAMES):
            bone_setting = DRESS_STANDARD_BONE_NAMES[bone_name]

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

            logger.count(
                "ローカル距離計算",
                index=n,
                total_index_count=len(LOCAL_SCALE_WEIGHT_BONE_NAMES),
                display_block=20,
            )

        dress_local_scales: dict[str, MVector3D] = {}
        for category in dress_local_positions.keys():
            if category not in model_local_positions:
                continue

            # フィルタした値
            model_filtered_local_positions = filter_values(model_local_positions[category])
            dress_filtered_local_positions = filter_values(dress_local_positions[category])

            model_local_distances = np.max(model_filtered_local_positions, axis=0) - np.min(model_filtered_local_positions, axis=0)
            dress_local_distances = np.max(dress_filtered_local_positions, axis=0) - np.min(dress_filtered_local_positions, axis=0)

            local_scale = MVector3D(*model_local_distances).one() / MVector3D(*dress_local_distances).one()

            if category in ("胸",):
                local_scale_value = max(1, np.mean([local_scale.x, local_scale.z]))
                dress_local_scales[category] = MVector3D(local_scale_value, 1.0, local_scale_value)
            else:
                local_scale_value = max(1, np.mean([local_scale.y, local_scale.z]))
                dress_local_scales[category] = MVector3D(1.0, local_scale_value, local_scale_value)

            logger.debug(
                f"ローカルスケール [{category}][{dress_local_scales[category]}][model={model_local_distances}]"
                + f"[dress={dress_local_distances}][scale={local_scale}]"
            )

            logger.info("-- ローカルスケール [{b}][{s})]", b=category, s=dress_local_scales[category])

        for i, (bone_name, bone_setting) in enumerate(list(DRESS_STANDARD_BONE_NAMES.items())):
            if not (bone_name in dress.bones):
                # 衣装にボーンがなければスルー
                continue
            dress_bone = dress.bones[bone_name]

            if not bone_setting.local_scalable or bone_setting.category not in dress_local_scales or "足首" in dress_bone.name:
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
