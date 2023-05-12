import os
from turtle import position

import numpy as np

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import MQuaternion, MVector3D, MVector4D, align_triangle
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import Bone, BoneMorphOffset, MaterialMorphCalcMode, MaterialMorphOffset, Morph, MorphType, STANDARD_BONE_NAMES
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from mlib.base.base import VecAxis

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
        # 準標準ボーンで足りないボーン名を抽出
        short_model_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(model.bones.names) | {"全ての親", "上半身2"}
        short_dress_bone_names = set(list(STANDARD_BONE_NAMES.keys())) - set({"右目", "左目", "両目"}) - set(dress.bones.names) | {"全ての親", "上半身2"}

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

        if dress_inserted_bone_names:
            dress.setup()
            dress.replace_standard_weights(dress_inserted_bone_names)
            logger.info("-- 衣装: 再セットアップ")

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
        """
        上半身2の配置を変える
        """

        logger.info("-- フィッティング用ウェイト別頂点取得（衣装）")
        dress_vertices_by_bones = dress.get_vertices_by_bone()

        # 一旦衣装の上半身2ウェイトを上半身に置き換える
        replaced_bone_map = dict([(b.index, b.index) for b in dress.bones])
        replaced_bone_map[dress.bones["上半身2"].index] = dress.bones["上半身"].index
        for vidx in dress_vertices_by_bones.get("上半身2", []):
            v = dress.vertices[vidx]
            v.deform.indexes = np.vectorize(replaced_bone_map.get)(v.deform.indexes)

        model_upper_pos = model.bones["上半身"].position
        model_upper2_pos = model.bones["上半身2"].position
        model_neck_pos = model.bones["首根元"].position
        dress_upper_pos = dress.bones["上半身"].position
        dress_upper2_pos = dress.bones["上半身2"].position
        dress_neck_pos = dress.bones["首根元"].position

        # 衣装の上半身2の位置を求め直す
        dress_new_upper2_pos = align_triangle(model_neck_pos, model_upper_pos, model_upper2_pos, dress_neck_pos, dress_upper_pos)
        dress.bones["上半身2"].position = dress_new_upper2_pos
        logger.info("-- 衣装: 上半身2再計算位置: {u} → {p}", u=dress_upper2_pos, p=dress_new_upper2_pos)

        # 上半身のウェイトを上半身2にも振り分ける
        dress.separate_weights(
            "上半身",
            "上半身2",
            VecAxis.Y,
            0.2,
            list(set(dress_vertices_by_bones.get(dress.bones["上半身"].index, [])) | set(dress_vertices_by_bones.get(dress.bones["上半身2"].index, []))),
        )

        return model, dress

    def create_dress_fit_bone_morphs(self, model: PmxModel, dress: PmxModel) -> PmxModel:
        """衣装フィッティング用ボーンモーフを作成"""
        bone_fitting_morph = Morph(name="BoneFitting")
        bone_fitting_morph.is_system = True
        bone_fitting_morph.morph_type = MorphType.BONE
        bone_fitting_offsets: dict[int, BoneMorphOffset] = {}

        # モデルの初期姿勢を求める
        model_matrixes = VmdMotion().bones.get_matrix_by_indexes([0], model.bones.tail_bone_names, model)
        dress_motion = VmdMotion()

        logger.info("-- フィッティングスケール計算")
        dress_offset_scales, dress_fit_scales = self.get_dress_offset_scales(model, dress, dress_motion, model_matrixes)

        logger.info("-- フィッティング移動回転計算")
        dress_offset_qqs, dress_offset_positions = self.get_dress_offsets(model, dress, dress_motion, model_matrixes, dress_offset_scales, dress_fit_scales)

        # dress_offset_qqs: dict[int, MQuaternion] = {}
        # dress_offset_positions: dict[int, MVector3D] = {}

        # # dress_fit_scales: dict[int, MVector3D] = {}
        # # dress_offset_scales: dict[int, MVector3D] = {}

        # logger.info("-- フィッティング回転計算")
        # # dress_offset_qqs = self.get_dress_offset_qqs(model, dress, dress_motion, model_matrixes)

        # logger.info("-- フィッティング移動計算")
        # # dress_offset_positions = self.get_dress_offset_positions(model, dress, dress_motion, model_matrixes, dress_offset_qqs)

        logger.info("-- フィッティングボーンモーフ追加")

        dress_bone_count = len(dress.bones)
        for i, dress_bone in enumerate(dress.bones):
            if not (
                0 <= dress_bone.index
                and (dress_bone.index in dress_offset_positions or dress_bone.index in dress_offset_qqs or dress_bone.index in dress_offset_scales)
            ):
                continue
            dress_offset_position = dress_offset_positions.get(dress_bone.index, MVector3D())
            dress_offset_qq = dress_offset_qqs.get(dress_bone.index, MQuaternion())
            dress_offset_scale = dress_offset_scales.get(dress_bone.index, MVector3D(1, 1, 1))
            dress_fit_scale = dress_fit_scales.get(dress_bone.index, MVector3D(1, 1, 1))

            logger.debug(
                "-- -- ボーンモーフ [{b}][scale={o:.3f}({f:.3f})][pos={p}][qq={q}]",
                b=dress_bone.name,
                p=dress_offset_position,
                q=dress_offset_qq.to_euler_degrees(),
                o=dress_offset_scale.x,
                f=dress_fit_scale.x,
            )

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

    def get_dress_offsets(
        self,
        model: PmxModel,
        dress: PmxModel,
        dress_motion: VmdMotion,
        model_matrixes: VmdBoneFrameTrees,
        dress_offset_scales: dict[int, MVector3D],
        dress_fit_scales: dict[int, MVector3D],
    ) -> tuple[dict[int, MQuaternion], dict[int, MVector3D]]:
        """衣装オフセット計算"""
        dress_offset_qqs: dict[int, MQuaternion] = {}
        dress_offset_positions: dict[int, MVector3D] = {}

        z_direction = MVector3D(0, 0, -1)
        for i, (bone_name, bone_setting) in enumerate(list(STANDARD_BONE_NAMES.items())[1:7]):
            if not (bone_name in dress.bones and bone_name in model.bones):
                # 人物と衣装のいずれかにボーンがなければスルー
                continue

            dress_bone = dress.bones[bone_name]
            model_bone = model.bones[dress_bone.name]
            tail_bone_names = [bname for bname in bone_setting.tails if bname in dress.bones and bname in model.bones]
            tail_bone_name = tail_bone_names[0] if tail_bone_names else bone_name

            # 親までをフィッティングさせた上で改めてボーン位置を求める
            dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [tail_bone_name], dress, append_ik=False)

            dress_fit_position = dress_matrixes[0, dress_bone.name].matrix.inverse() * model_matrixes[0, dress_bone.name].position

            # dress_diff_position = dress_matrixes[0, dress.bones[dress_bone.parent_index].name].matrix.inverse() * dress_matrixes[0, dress_bone.name].position
            # model_diff_position = dress_matrixes[0, dress.bones[dress_bone.parent_index].name].matrix.inverse() * model_matrixes[0, dress_bone.name].position
            # dress_fit_position = model_diff_position - dress_diff_position

            # dress_fit_position = model_matrixes[0, dress_bone.name].position - dress_matrixes[0, dress_bone.name].position

            # 移動にスケールを加味する
            dress_offset_position = dress_fit_position  # / dress_offset_scales.get(dress_bone.parent_index, MVector3D(1, 1, 1))

            # キーフレとして追加
            mbf = dress_motion.bones[dress_bone.name][0]
            mbf.position = dress_offset_position
            dress_motion.bones[dress_bone.name].append(mbf)

            dress_offset_positions[dress_bone.index] = dress_offset_position

            if not dress_bone.is_tail_bone:
                # 表示先が位置の場合、そのまま加算
                dress_bone.tail_position += dress_offset_position

            logger.debug(
                f"移動オフセット[{dress_bone.name}][f:{dress_offset_position}({dress_fit_position})]"
                + f"[d:{dress_matrixes[0, dress_bone.name].position}][m:{model_matrixes[0, dress_bone.name].position}]"
            )

            if dress_bone.name in ["全ての親", "センター", "グルーブ", "腰", Bone.SYSTEM_ROOT_NAME]:
                # 特定の名前のボーンはスルー
                continue
            if dress_bone.has_fixed_axis or dress_bone.is_ik:
                # 軸制限あり、IKはスルー
                continue

            dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [tail_bone_name], dress, append_ik=False)

            # 衣装：自分の方向
            if isinstance(bone_setting.relative, MVector3D):
                dress_x_direction = bone_setting.relative
            elif 0 > dress_bone.tail_index:
                dress_x_direction = MVector3D(1, 0, 0)
            else:
                dress_x_direction = dress_matrixes[0, dress_bone.name].matrix.inverse() * dress_matrixes[0, tail_bone_name].position
            dress_x_direction.normalize()

            dress_y_direction = dress_x_direction.cross(z_direction)
            dress_slope_qq = MQuaternion.from_direction(dress_x_direction, dress_y_direction)

            # 人物：自分の方向
            if isinstance(bone_setting.relative, MVector3D):
                model_x_direction = bone_setting.relative
            elif 0 > model_bone.tail_index:
                model_x_direction = MVector3D(1, 0, 0)
            else:
                model_x_direction = model_matrixes[0, model_bone.name].matrix.inverse() * model_matrixes[0, tail_bone_name].position
            model_x_direction.normalize()

            model_y_direction = model_x_direction.cross(z_direction)
            model_slope_qq = MQuaternion.from_direction(model_x_direction, model_y_direction)

            # モデルのボーンの向きに衣装を合わせる
            dress_fit_qq = model_slope_qq * dress_slope_qq.inverse()

            for tree_bone_name in reversed(dress.bone_trees[bone_name].names[:-1]):
                # 自分より親は逆回転させる
                dress_fit_qq *= dress_offset_qqs.get(dress.bones[tree_bone_name].index, MQuaternion()).inverse()

            dress_offset_qqs[dress_bone.index] = dress_fit_qq

            # キーフレとして追加
            rbf = dress_motion.bones[dress_bone.name][0]
            rbf.rotation = dress_fit_qq
            dress_motion.bones[dress_bone.name].append(rbf)

            logger.debug(
                f"回転オフセット[{dress_bone.name}][f:{dress_fit_qq.to_euler_degrees()}]"
                + f"[d:{dress_slope_qq.to_euler_degrees()}][m:{model_slope_qq.to_euler_degrees()}]"
            )

            logger.count(
                "-- オフセット移動回転計算",
                index=i,
                total_index_count=len(STANDARD_BONE_NAMES),
                display_block=50,
            )

        return dress_offset_qqs, dress_offset_positions

    # def get_dress_offset_qqs(self, model: PmxModel, dress: PmxModel, dress_motion: VmdMotion, model_matrixes: VmdBoneFrameTrees) -> dict[int, MQuaternion]:
    #     dress_bone_tree_count = len(dress.bone_trees)
    #     dress_offset_qqs: dict[int, MQuaternion] = {}

    #     z_direction = MVector3D(0, 0, -1)
    #     for i, (bone_name, bone_setting) in enumerate(STANDARD_BONE_NAMES.items()):
    #         if not (bone_name in dress.bones and bone_name in model.bones):
    #             # 人物と衣装のいずれかにボーンがなければスルー
    #             continue
    #         dress_bone = dress.bones[bone_name]
    #         if dress_bone.name in ["全ての親", "センター", "グルーブ", "腰", Bone.SYSTEM_ROOT_NAME]:
    #             # 特定の名前のボーンはスルー
    #             continue
    #         if dress_bone.can_translate or dress_bone.has_fixed_axis or dress_bone.is_ik:
    #             # 移動可能、軸制限あり、IKはスルー
    #             continue

    #         # 衣装：自分の方向
    #         dress_x_direction = dress_bone.tail_relative_position.normalized()
    #         dress_y_direction = dress_x_direction.cross(z_direction)
    #         dress_slope_qq = MQuaternion.from_direction(dress_x_direction, dress_y_direction)

    #         # 人物：自分の方向
    #         if 0 > model.bones[dress_bone.name].tail_index:
    #             model_x_direction = dress_x_direction.copy()
    #         elif isinstance(bone_setting.relative, MVector3D):
    #             model_x_direction = bone_setting.relative
    #         else:
    #             model_x_direction = (
    #                 model_matrixes[0, model.bones[model.bones[dress_bone.name].tail_index].name].position - model_matrixes[0, dress_bone.name].position
    #             )
    #             model_x_direction.normalize()
    #         model_y_direction = model_x_direction.cross(z_direction)
    #         model_slope_qq = MQuaternion.from_direction(model_x_direction, model_y_direction)

    #         # モデルのボーンの向きに衣装を合わせる
    #         dress_fit_qq = model_slope_qq * dress_slope_qq.inverse()

    #         for tree_bone_name in reversed(dress.bone_trees[bone_name].names[:-1]):
    #             # 自分より親は逆回転させる
    #             dress_fit_qq *= dress_offset_qqs.get(dress.bones[tree_bone_name].index, MQuaternion()).inverse()

    #         dress_offset_qqs[dress_bone.index] = dress_fit_qq

    #         # キーフレとして追加
    #         bf = dress_motion.bones[dress_bone.name][0]
    #         bf.rotation = dress_fit_qq
    #         dress_motion.bones[dress_bone.name].append(bf)

    #         logger.debug(f"回転オフセット[{dress_bone.name}][{dress_fit_qq.to_euler_degrees()}]")

    #         logger.count(
    #             "-- 回転計算",
    #             index=i,
    #             total_index_count=dress_bone_tree_count,
    #             display_block=50,
    #         )

    #     for dress_bone in dress.bones:
    #         for parent_bone_index in (dress.bones["上半身"].index, dress.bones["下半身"].index):
    #             if dress_bone.parent_index == parent_bone_index and not dress.bone_trees.is_in_standard(dress_bone.name):
    #                 # 親ボーンが体幹かつ準標準ボーンの範囲外の場合、体幹の回転を打ち消した回転を持つ
    #                 dress_fit_qq = dress_offset_qqs.get(parent_bone_index, MQuaternion()).inverse()
    #                 dress_offset_qqs[dress_bone.index] = dress_fit_qq

    #                 # キーフレとして追加
    #                 bf = dress_motion.bones[dress_bone.name][0]
    #                 bf.rotation = dress_fit_qq
    #                 dress_motion.bones[dress_bone.name].append(bf)

    #                 logger.debug(f"回転オフセット[{dress_bone.name}][{dress_fit_qq.to_euler_degrees()}]")

    #     return dress_offset_qqs

    def get_dress_offset_scales(
        self, model: PmxModel, dress: PmxModel, dress_motion: VmdMotion, model_matrixes: VmdBoneFrameTrees
    ) -> tuple[dict[int, MVector3D], dict[int, MVector3D]]:
        """衣装スケール計算"""
        dress_offset_scales: dict[int, MVector3D] = {}
        dress_fit_scales: dict[int, MVector3D] = {}

        dress_trunk_fit_scales: list[float] = []
        for from_name, to_name in FIT_ROOT_BONE_NAMES + FIT_TRUNK_BONE_NAMES:
            if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                continue

            model_relative_position = (model_matrixes[0, to_name].position - model_matrixes[0, from_name].position).effective(rtol=0.05, atol=0.05).abs()
            dress_relative_position = (dress.bones[to_name].position - dress.bones[from_name].position).effective(rtol=0.05, atol=0.05).abs()

            dress_trunk_scale = model_relative_position.length() / dress_relative_position.length()
            dress_trunk_fit_scales.append(dress_trunk_scale)

        # スケール計算: 体幹
        dress_trunk_mean_scale = np.min(dress_trunk_fit_scales)
        dress_trunk_fit_scale = MVector3D(dress_trunk_mean_scale, dress_trunk_mean_scale, dress_trunk_mean_scale)
        logger.debug("-- -- スケールオフセット [{b}][{s:.3f}]", b="体幹", s=dress_trunk_mean_scale)

        for from_name, to_name in FIT_TRUNK_BONE_NAMES:
            if not (from_name in dress.bones and from_name in model.bones):
                continue

            bf = dress_motion.bones[from_name][0]
            bf.scale = dress_trunk_fit_scale
            dress_motion.bones[from_name].append(bf)

            dress_fit_scales[dress.bones[from_name].index] = dress_trunk_fit_scale
            dress_offset_scales[dress.bones[from_name].index] = dress_trunk_fit_scale.copy()

            logger.debug(f"-- -- スケールオフセット [{from_name}][{dress_trunk_mean_scale:.5f}]")

        for scale_bone_name, scale_axis, measure_bone_names in FIT_EXTREMITIES_BONE_NAMES:
            dress_extremities_fit_scales: list[float] = []
            for from_name, to_name in measure_bone_names:
                if not (from_name in dress.bones and to_name in dress.bones and from_name in model.bones and to_name in model.bones):
                    continue

                # 親までをフィッティングさせた上で改めてボーン位置を求める
                dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [to_name], dress, append_ik=False)

                model_relative_position = (
                    (model_matrixes[0, from_name].matrix.inverse() * model_matrixes[0, to_name].position).effective(rtol=0.05, atol=0.05).abs()
                )
                dress_relative_position = (
                    (dress_matrixes[0, from_name].matrix.inverse() * dress_matrixes[0, to_name].position).effective(rtol=0.05, atol=0.05).abs()
                )

                # 計測対象軸を対象とする
                dress_extremities_fit_scales.append((model_relative_position / dress_relative_position).vector[scale_axis])
            # 全計測対象の最小値をスケール値とする（後は移動で伸ばす）
            dress_min_scale = np.min(dress_extremities_fit_scales)
            dress_fit_scale = MVector3D(dress_min_scale, dress_min_scale, dress_min_scale)

            # 親をキャンセルしていく
            dress_offset_scale = dress_fit_scale.copy()
            for parent_index in dress.bone_trees[to_name].indexes[:-1]:
                if parent_index in dress_offset_scales:
                    dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales[parent_index]

            bf = dress_motion.bones[scale_bone_name][0]
            bf.scale = dress_offset_scale
            dress_motion.bones[scale_bone_name].append(bf)

            dress_fit_scales[dress.bones[scale_bone_name].index] = dress_fit_scale
            dress_offset_scales[dress.bones[scale_bone_name].index] = dress_offset_scale

            logger.debug("-- -- スケールオフセット [{b}][{f:.3f}][{o:.3f}]", b=scale_bone_name, f=dress_fit_scale.x, o=dress_offset_scale.x)

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

        if "頭" in model.bones and "頭" in dress.bones:
            logger.info("-- -- フィッティング用ウェイト別頂点取得（人物）")
            model_vertices_by_bones = model.get_vertices_by_bone()

            logger.info("-- -- フィッティング用ウェイト別頂点取得（衣装）")
            dress_vertices_by_bones = dress.get_vertices_by_bone()

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

                model_head_size = np.mean(max_model_head_vertex_poses - mean_model_head_vertex_poses)
                dress_head_size = np.mean(max_dress_head_vertex_poses - mean_dress_head_vertex_poses)

                if model_head_size * dress_trunk_mean_scale * 0.5 < dress_head_size:
                    # 衣装の頭ウェイト頂点から計算したサイズが、スケーリングした頭部の半分以上である場合のみ縮尺対象とする
                    # 球体の中心から最大までのスケールの平均値で全体を縮尺させる
                    dress_fit_scale = MVector3D(
                        *((max_model_head_vertex_poses - mean_model_head_vertex_poses) / (max_dress_head_vertex_poses - mean_dress_head_vertex_poses))
                    )

                    # 親をキャンセルしていく
                    dress_offset_scale = dress_fit_scale.copy()
                    for parent_index in dress.bone_trees["頭"].indexes[:-1]:
                        if parent_index in dress_offset_scales:
                            dress_offset_scale *= MVector3D(1, 1, 1) / dress_offset_scales[parent_index]

                    bf = dress_motion.bones["頭"][0]
                    bf.scale = dress_offset_scale
                    dress_motion.bones["頭"].append(bf)

                    dress_offset_scales[dress.bones["頭"].index] = dress_offset_scale
                    dress_fit_scales[dress.bones["頭"].index] = dress_offset_scale

                    logger.debug("-- -- スケールオフセット [{b}][{o:.3f}][{f:.3f}]", b="頭", o=dress_offset_scale.x, f=dress_fit_scale.x)

        return dress_offset_scales, dress_fit_scales

    # def get_dress_offset_positions(
    #     self,
    #     model: PmxModel,
    #     dress: PmxModel,
    #     dress_motion: VmdMotion,
    #     model_matrixes: VmdBoneFrameTrees,
    #     dress_offset_qqs: dict[int, MQuaternion],
    # ) -> dict[int, MVector3D]:
    #     """衣装移動計算"""
    #     dress_offset_positions: dict[int, MVector3D] = {}
    #     dress_bone_tree_count = len(dress.bone_trees)

    #     for i, bone_name in enumerate(list(STANDARD_BONE_NAMES.keys())[1:]):
    #         # for i, bone_name in enumerate(("センター", "グルーブ", "腰", "上半身", "下半身", "上半身2")):
    #         if not (bone_name in dress.bones and bone_name in model.bones):
    #             # 人物と衣装のいずれかにボーンがなければスルー
    #             continue
    #         dress_bone = dress.bones[bone_name]

    #         # 親までをフィッティングさせた上で改めてボーン位置を求める
    #         dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], [dress_bone.name], dress, append_ik=False)

    #         # model_local_position = dress_matrixes[0, dress.bones[dress_bone.parent_index].name].matrix.inverse() * model_matrixes[0, dress_bone.name].position
    #         # dress_local_position = dress_matrixes[0, dress.bones[dress_bone.parent_index].name].matrix.inverse() * dress_matrixes[0, dress_bone.name].position
    #         # dress_offset_position = model_local_position - dress_local_position
    #         # dress_offset_position = model_matrixes[0, dress_bone.name].position - dress_matrixes[0, dress_bone.name].position

    #         # mat = MMatrix4x4()
    #         # # 親ボーン位置に移動
    #         # mat.translate(dress_matrixes[0, dress.bones[dress.bones[dress_bone.name].parent_index].name].position)
    #         # # 向きを合わせる
    #         # mat.rotate(dress_offset_qqs.get(dress_bone.index, MQuaternion()))

    #         # dress_offset_position = mat.inverse() * model_matrixes[0, dress_bone.name].position

    #         # dress_offset_position = dress_matrixes[0, dress_bone.name].matrix.inverse() * model_matrixes[0, dress_bone.name].position

    #         dress_offset_position = model_matrixes[0, dress_bone.name].position - dress_matrixes[0, dress_bone.name].position

    #         # キーフレとして追加
    #         bf = dress_motion.bones[dress_bone.name][0]
    #         bf.position = dress_offset_position
    #         dress_motion.bones[dress_bone.name].append(bf)

    #         dress_offset_positions[dress_bone.index] = dress_offset_position

    #         logger.debug(
    #             f"移動オフセット[{dress_bone.name}][{dress_offset_position}]"
    #             + f"[m={model_matrixes[0, dress_bone.name].position}][d={dress_matrixes[0, dress_bone.name].position}]"
    #         )

    #         logger.count(
    #             "-- 移動計算",
    #             index=i,
    #             total_index_count=dress_bone_tree_count,
    #             display_block=50,
    #         )

    #     return dress_offset_positions


FIT_ROOT_BONE_NAMES = [
    ("全ての親", "上半身"),
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
