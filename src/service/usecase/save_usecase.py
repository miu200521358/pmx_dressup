from PIL import Image
from datetime import datetime
from itertools import product
import os
import shutil
from typing import Optional

import numpy as np

from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MVector3D, MVectorDict
from mlib.base.part import Switch
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import (
    BoneMorphOffset,
    DisplaySlot,
    DisplaySlotReference,
    DisplayType,
    Face,
    GroupMorphOffset,
    Material,
    MaterialMorphOffset,
    Morph,
    MorphType,
    SphereMode,
    Texture,
    ToonSharing,
    UvMorphOffset,
    VertexMorphOffset,
)
from mlib.pmx.pmx_writer import PmxWriter
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame
from service.usecase.dress_bone import DressBones

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class SaveUsecase:
    def save(
        self,
        model: PmxModel,
        dress: PmxModel,
        model_config_motion: Optional[VmdMotion],
        dress_config_motion: Optional[VmdMotion],
        output_path: str,
        model_material_alphas: dict[str, float],
        model_skin_materials: dict[str, bool],
        dress_material_alphas: dict[str, float],
        dress_skin_materials: dict[str, bool],
        dress_scales: dict[str, MVector3D],
        dress_degrees: dict[str, MVector3D],
        dress_positions: dict[str, MVector3D],
        bone_target_dress: dict[str, bool],
    ) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        model_motion = VmdMotion("model fit motion")
        if model_config_motion:
            model_motion.morphs = model_config_motion.morphs.copy()

        dress_motion = VmdMotion("dress fit motion")
        if dress_config_motion:
            dress_motion.morphs = dress_config_motion.morphs.copy()

        # 接地Yを取得する
        root_ground_y = self.get_dress_ground(
            dress,
            dress_motion,
        )

        mmf = VmdMorphFrame(0, "Root:Adjust")
        mmf.ratio = root_ground_y
        model_motion.morphs[mmf.name].append(mmf)

        dmf = VmdMorphFrame(0, "Root:Adjust")
        dmf.ratio = root_ground_y
        dress_motion.morphs[dmf.name].append(dmf)

        dress_model = PmxModel(output_path)
        dress_model.model_name = model.name + "(" + dress.name + ")"
        dress_model.english_name = model.english_name + "(" + dress.english_name + ")"
        dress_model.extended_uv_count = max(model.extended_uv_count, dress.extended_uv_count)
        dress_model.comment = (
            __("人物モデル")
            + "\r\n"
            + model.comment
            + "\r\n\r\n------------------\r\n\r\n"
            + __("衣装モデル")
            + "\r\n"
            + dress.comment
            + "\r\n\r\n------------------\r\n\r\n"
        )
        dress_model.english_name = (
            __("人物モデル")
            + "\r\n"
            + model.english_comment
            + "\r\n\r\n------------------\r\n\r\n"
            + __("衣装モデル")
            + "\r\n"
            + dress.english_comment
            + "\r\n\r\n------------------\r\n\r\n"
        )

        fitting_messages = []
        for bone_type_name, scale, degree, position in zip(
            dress_scales.keys(), dress_scales.values(), dress_degrees.values(), dress_positions.values()
        ):
            message = __("  {b}: 縮尺{s}, 回転{r}, 移動{p}", b=bone_type_name, s=scale, r=degree, p=position)
            fitting_messages.append(message)

        model_output_material_names = [
            material_name
            for (material_name, alpha) in model_material_alphas.items()
            if alpha == 1.0 and material_name not in [__("ボーンライン"), __("全材質")]
        ]

        dress_output_material_names = [
            material_name
            for (material_name, alpha) in dress_material_alphas.items()
            if alpha == 1.0 and material_name not in [__("ボーンライン"), __("全材質")]
        ]

        with open(os.path.join(os.path.dirname(output_path), f"settings_{datetime.now():%Y%m%d_%H%M%S}.txt"), "w", encoding="utf-8") as f:
            f.write(__("人物モデル") + "\n")
            f.write(model.path + "\n")
            f.write("\n")
            f.write(__("人物モデル：出力対象材質") + "\n    ")
            f.write(", ".join(model_output_material_names))
            f.write("\n")
            f.write(__("衣装モデル") + "\n")
            f.write(dress.path + "\n")
            f.write("\n")
            f.write(__("衣装モデル：出力対象材質") + "\n    ")
            f.write(", ".join(dress_output_material_names))
            f.write("\n")
            f.write(__("個別フィッティング") + "\n")
            f.write("\n".join(fitting_messages))

        logger.info(
            "人物モデル: {m} ({p})\n  出力材質: {mm}\n衣装モデル: {d} ({q})\n  出力材質: {dm}\n個別フィッティング:\n  {f}",
            m=model.name,
            p=os.path.basename(model.path),
            mm=", ".join(model_output_material_names),
            d=dress.name,
            q=os.path.basename(dress.path),
            dm=", ".join(dress_output_material_names),
            f="\n".join(fitting_messages),
        )

        logger.info("出力準備", decoration=MLogger.Decoration.LINE)

        # 衣装側の位置に合わせるボーンINDEXリスト
        dress_offset_bone_names = [
            dress.bones[offset.bone_index].name
            for (morph_name, active) in bone_target_dress.items()
            if active
            for offset in dress.morphs[f"調整:{__(morph_name)}:SX"].offsets
        ]
        dress_fit_bone_indexes = [
            bone_index
            for bone_tree in dress.bone_trees
            for offset_bone_name in dress_offset_bone_names
            if offset_bone_name in bone_tree.names
            for bone_index in bone_tree.filter(start_bone_name=offset_bone_name).indexes
        ]

        # 変形結果
        logger.info("人物：変形確定")
        model_original_matrixes = VmdMotion().animate_bone([0], model, append_ik=False)
        model_matrixes = model_motion.animate_bone([0], model, append_ik=False)
        logger.info("衣装：変形確定")
        dress_original_matrixes = VmdMotion().animate_bone([0], dress, append_ik=False)
        dress_matrixes = dress_motion.animate_bone([0], dress, append_ik=False)

        logger.info("人物：材質選り分け")
        model.update_vertices_by_bone()
        model.update_vertices_by_material()

        active_model_vertices = set(
            [
                vertex_index
                for material_index, vertices in model.vertices_by_materials.items()
                if 1 == model_material_alphas[model.materials[material_index].name]
                for vertex_index in vertices
            ]
        )

        logger.info("衣装：材質選り分け")
        dress.update_vertices_by_bone()
        dress.update_vertices_by_material()

        active_dress_vertices = set(
            [
                vertex_index
                for material_index, vertices in dress.vertices_by_materials.items()
                if 1 == dress_material_alphas[dress.materials[material_index].name]
                for vertex_index in vertices
            ]
        )

        # ---------------------------------

        dress_model.initialize_display_slots()

        dress_model_bones = DressBones()
        logger.info("ボーン出力", decoration=MLogger.Decoration.LINE)

        for bone in model.bones.writable():
            if not (model.bone_trees.is_in_standard(bone.name) or bone.is_standard_extend):
                # 準標準ではない場合、登録可否チェック

                if bone.index in model.vertices_by_bones and not set(model.vertices_by_bones[bone.index]) & active_model_vertices:
                    # 元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                    continue
                if (
                    bone.index not in model.vertices_by_bones
                    and bone.parent_index in model.vertices_by_bones
                    and not set(model.vertices_by_bones[bone.parent_index]) & active_model_vertices
                ):
                    # 自身はウェイトを持っておらず、親ボーンが元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                    continue
                if bone.is_ik and not (
                    0 <= dress_model_bones.get_index_by_map(bone.ik.bone_index, False)
                    or set(model.vertices_by_bones.get(bone.ik.bone_index, [])) & active_model_vertices
                    or [
                        link_bone_index
                        for link in bone.ik.links
                        for link_bone_index in set(model.vertices_by_bones.get(link.bone_index, [])) & active_model_vertices
                    ]
                    or [link.bone_index for link in bone.ik.links if 0 <= dress_model_bones.get_index_by_map(link.bone_index, False)]
                ):
                    # IKボーンで、かつ出力先にリンクやターゲットボーンのウェイトが乗ってる頂点が無い場合、スルー
                    # またIKのリンクやターゲットが既に出力対象である場合、IKボーンも出力する
                    continue
                if (
                    (bone.is_external_translation or bone.is_external_rotation)
                    and bone.effect_index in model.vertices_by_bones
                    and not set(model.vertices_by_bones[bone.effect_index]) & active_model_vertices
                ):
                    # 自身はウェイトを持っておらず、付与親ボーンが元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                    continue

            if bone.parent_index not in dress_model_bones.model_map and not bone.is_standard:
                # 人物側の親ボーンが登録されていない場合、子ボーンも登録しない
                continue

            # for dress_bone in dress.bones.writable():
            #     if (
            #         0 <= dress_bone.tail_index
            #         and dress_bone.name not in model.bones
            #         and dress.bones[dress_bone.tail_index].name == bone.name
            #         and dress_bone.index in dress.vertices_by_bones
            #     ):
            #         # ウェイトを持っている衣装だけのボーンの表示先が人物のボーンに繋がってる場合、その前に追加しておく
            #         dress_model_bones.append(dress_bone, is_dress=True, is_weight=True)

            #         if not len(dress_model_bones) % 100:
            #             logger.info("-- ボーン出力: {s}", s=len(dress_model_bones))

            is_weight = bool(bone.index in model.vertices_by_bones and set(model.vertices_by_bones[bone.index]) & active_model_vertices)

            # 変形後の位置にボーンを配置する
            dress_model_bones.append(bone, is_dress=False, is_weight=is_weight, position=model_matrixes[0, bone.name].position.copy())

            if not len(dress_model_bones) % 100:
                logger.info("-- ボーン出力: {s}", s=len(dress_model_bones))

        for bone in dress.bones.writable():
            if (bone.is_standard or bone.is_standard_extend) and bone.name in dress_model_bones:
                # 既に登録済みの準標準ボーンは追加しない
                dress_model_bones.dress_map[bone.index] = dress_model_bones[bone.name].index

                if not dress_model_bones[bone.name].is_weight or bone.index in dress_fit_bone_indexes:
                    # 人物側にウェイトが乗っていない場合、変形後の位置にボーンを配置する
                    # もしくは衣装側に合わせる、と指示したボーンは衣装側の変形後の位置に配置
                    dress_model_bones[bone.name].position = dress_matrixes[0, bone.name].position.copy()

                    if (
                        not bone.is_tail_bone
                        and dress_model_bones[bone.name].bone.is_tail_bone
                        and 0 <= dress_model_bones[bone.name].bone.tail_index
                        and model.bones[model.bones[bone.name].tail_index].name in dress_model_bones
                    ):
                        # 衣装側が表示先がなくて、人物側に表示先がある場合、表示先ボーンの位置を変形後の位置に合わせる
                        dress_model_bones[model.bones[model.bones[bone.name].tail_index].name].position = (
                            dress_matrixes[0, bone.name].global_matrix * bone.tail_position
                        )

                    for parent_bone_name in reversed(model.bone_trees[bone.name].names[:-1]):
                        if dress_model_bones[parent_bone_name].bone.is_standard or parent_bone_name in dress.bones:
                            break
                        # 親が準標準ではなく、衣装側にない場合、親は子（対象）の変形後の位置からみた相対位置にボーンを配置する
                        dress_model_bones[parent_bone_name].position = dress_matrixes[0, bone.name].global_matrix * (
                            model_matrixes[0, parent_bone_name].position - model_matrixes[0, bone.name].position
                        )

                continue

            if not (dress.bone_trees.is_in_standard(bone.name) or bone.is_standard_extend):
                # 準標準ではない場合、登録可否チェック

                if bone.index in dress.vertices_by_bones and not set(dress.vertices_by_bones[bone.index]) & active_dress_vertices:
                    # 元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                    continue
                if (
                    bone.index not in dress.vertices_by_bones
                    and bone.parent_index in dress.vertices_by_bones
                    and not set(dress.vertices_by_bones[bone.parent_index]) & active_dress_vertices
                ):
                    # 自身はウェイトを持っておらず、親ボーンが元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                    continue
                if bone.is_ik and not (
                    set(dress.vertices_by_bones.get(bone.ik.bone_index, [])) & active_dress_vertices
                    or [
                        vertex_index
                        for link in bone.ik.links
                        for vertex_index in set(dress.vertices_by_bones.get(link.bone_index, [])) & active_dress_vertices
                    ]
                ):
                    # IKボーンで、かつ出力先にリンクやターゲットボーンのウェイトが乗ってる頂点が無い場合、スルー
                    continue
                if (
                    (bone.is_external_translation or bone.is_external_rotation)
                    and bone.effect_index in dress.vertices_by_bones
                    and not set(dress.vertices_by_bones[bone.effect_index]) & active_dress_vertices
                ):
                    # 自身はウェイトを持っておらず、付与親ボーンが元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                    continue

            if bone.parent_index not in dress_model_bones.dress_map and not bone.is_standard:
                # 親ボーンが登録されていない場合、子ボーンも登録しない
                continue

            # 変形後の位置にボーンを配置する
            if bone.child_bone_indexes and dress.bones[bone.child_bone_indexes[0]].name in dress_model_bones:
                # 自分の子どもが既に登録されている場合、自分の子ボーンのひとつ前に挿入する
                child_bone = dress_model_bones[dress.bones[bone.child_bone_indexes[0]].name]

                dress_model_bones.append(
                    bone,
                    is_dress=True,
                    is_weight=True,
                    position=dress_matrixes[0, bone.name].local_matrix * bone.position,
                    bone_index=child_bone.index,
                )
            elif bone.child_bone_indexes and dress.bone_trees.is_in_standard(dress.bones[bone.child_bone_indexes[0]].name):
                # 準標準の中の順標準外の場合、子どもの準標準ボーンのひとつ前に挿入する
                child_bones = [b for b in dress.bones if bone.child_bone_indexes[0] in b.relative_bone_indexes and b.is_standard]
                child_bone_index = dress_model_bones[child_bones[0].name].index if child_bones else -1

                dress_model_bones.append(
                    bone,
                    is_dress=True,
                    is_weight=True,
                    position=dress_matrixes[0, bone.name].local_matrix * bone.position,
                    bone_index=child_bone_index,
                )

                if child_bones:
                    # 子ボーンを置き換えた場合、子ボーンは衣装側のボーンを参照する
                    child_name = child_bones[0].name
                    dress_model_bones[child_name].is_dress = True
                    dress_model_bones[child_name].bone = dress.bones[child_name].copy()
            else:
                # そのまま追加する
                dress_model_bones.append(
                    bone, is_dress=True, is_weight=True, position=dress_matrixes[0, bone.name].local_matrix * bone.position
                )

            if not len(dress_model_bones) % 100:
                logger.info("-- ボーン出力: {s}", s=len(dress_model_bones))

        logger.info("ボーン定義再設定", decoration=MLogger.Decoration.LINE)

        local_y_vector = MVector3D(0, -1, 0)
        for dress_model_bone in dress_model_bones:
            dress_model_bone.parent_index = dress_model_bones.get_index_by_map(
                dress_model_bone.bone.parent_index, dress_model_bone.is_dress
            )
            dress_model_bone.tail_index = dress_model_bones.get_index_by_map(dress_model_bone.bone.tail_index, dress_model_bone.is_dress)
            dress_model_bone.effect_index = dress_model_bones.get_index_by_map(
                dress_model_bone.bone.effect_index, dress_model_bone.is_dress
            )

            dress_model_bone.layer = max(
                dress_model_bone.bone.layer,
                (dress_model_bones[dress_model_bone.parent_index].layer if 0 < dress_model_bone.parent_index else 0),
                (dress_model_bones[dress_model_bone.effect_index].layer if 0 <= dress_model_bone.effect_index else 0),
            )

            dress_model_bone.external_key = dress_model_bone.bone.external_key
            dress_model_bone.fixed_axis = dress_model_bone.bone.fixed_axis
            dress_model_bone.local_x_vector = dress_model_bone.bone.local_x_vector
            dress_model_bone.local_z_vector = dress_model_bone.bone.local_z_vector

            if dress_model_bone.bone.is_ik and dress_model_bone.bone.ik:
                dress_model_bone.ik.bone_index = dress_model_bones.get_index_by_map(
                    dress_model_bone.bone.ik.bone_index, dress_model_bone.is_dress
                )
                dress_model_bone.ik.loop_count = dress_model_bone.bone.ik.loop_count
                dress_model_bone.ik.unit_rotation = dress_model_bone.bone.ik.unit_rotation
                if 0 <= dress_model_bone.bone.ik.bone_index and dress_matrixes.exists(0, dress_model_bone.bone.name):
                    # IKターゲットとその位置を修正
                    dress_model_bone.position = dress_matrixes[0, dress_model_bone.bone.name].position.copy()
                    dress_model_bones[dress_model_bone.ik.bone_index].position = dress_matrixes[
                        0, dress_model_bone.bone.name
                    ].position.copy()
                for link in dress_model_bone.bone.ik.links:
                    dress_link = link.copy()
                    dress_link.bone_index = dress_model_bones.get_index_by_map(link.bone_index, dress_model_bone.is_dress)
                    dress_model_bone.ik.links.append(dress_link)

            if bone.is_leg_d and dress_matrixes.exists(0, dress_model_bones[dress_model_bone.effect_index].name):
                # 足Dを足FKに揃える
                dress_model_bones[bone.index].position = dress_matrixes[
                    0, dress_model_bones[dress_model_bone.effect_index].name
                ].position.copy()

            dress_model.bones.append(dress_model_bone.get_bone())

            if 0 < bone.index and not bone.index % 100:
                logger.info("-- ボーン定義再設定: {s}", s=bone.index)

        for bone in dress_model.bones:
            if bone.has_fixed_axis:
                # 軸制限がある場合、合わせる
                fixed_axis = dress_model.bones.get_tail_relative_position(bone.index).normalized()
                if 0 != fixed_axis.dot(bone.fixed_axis):
                    # 元々のローカル軸と大きく違いすぎてる場合は判定結果を入れない
                    bone.fixed_axis = fixed_axis

            if bone.has_local_coordinate:
                # ローカル軸も合わせる
                local_z_vector = dress_model.bones.get_tail_relative_position(bone.index).normalized()
                if 0 != local_z_vector.dot(bone.local_z_vector):
                    # 元々のローカル軸と大きく違いすぎてる場合は判定結果を入れない
                    bone.local_z_vector = local_z_vector
                    bone.local_x_vector = local_y_vector.cross(bone.local_z_vector).normalized()

            # if (bone.is_external_rotation or bone.is_external_translation) and bone.effect_index in dress_model.bones:
            #     external_bone = dress_model.bones[bone.effect_index]
            #     if bone.layer < external_bone.layer or (bone.layer == external_bone.layer and bone.index < external_bone.index):
            #         # 変形階層が正しく無い場合、修正する
            #         new_layer = max(bone.layer, external_bone.layer) + 1
            #         logger.info(
            #             "-- 変形階層が正しくないため、修正を試みます ボーン名={b}, 変形階層=[{l1} -> {l2}]",
            #             b=bone.name,
            #             l1=bone.layer,
            #             l2=new_layer,
            #         )
            #         bone.layer = new_layer

            if 0 < bone.index and not bone.index % 100:
                logger.info("-- ボーン軸定義再設定: {s}", s=bone.index)

        model_all_bone_map: dict[int, int] = dict([(bone.index, dress_model_bones.model_map.get(bone.index, 0)) for bone in model.bones])
        dress_all_bone_map: dict[int, int] = dict([(bone.index, dress_model_bones.dress_map.get(bone.index, 0)) for bone in dress.bones])

        # ---------------------------------

        # キー: 元々のINDEX、値: コピー先INDEX
        model_vertex_map: dict[int, int] = {-1: -1}
        dress_vertex_map: dict[int, int] = {-1: -1}

        model_material_map: dict[int, int] = {-1: -1}
        dress_material_map: dict[int, int] = {-1: -1}

        logger.info("材質出力", decoration=MLogger.Decoration.LINE)
        model.update_vertices_by_material()

        model_skin_vertex_positions: dict[str, MVectorDict] = {}
        prev_faces_count = 0
        for material in model.materials:
            if 1 > model_material_alphas[material.name]:
                prev_faces_count += material.vertices_count // 3
                continue
            copy_material = material.copy()
            copy_material.index = len(dress_model.materials)

            if 0 <= material.texture_index:
                copy_texture = self.copy_texture(dress_model, model.textures[material.texture_index], model.path, is_dress=False)
                copy_material.texture_index = copy_texture.index if copy_texture else -1

            if material.toon_sharing_flg == ToonSharing.INDIVIDUAL and 0 <= material.toon_texture_index:
                copy_texture = self.copy_texture(dress_model, model.textures[material.toon_texture_index], model.path, is_dress=False)
                copy_material.toon_texture_index = copy_texture.index if copy_texture else -1

            if material.sphere_mode != SphereMode.INVALID and 0 <= material.sphere_texture_index:
                copy_texture = self.copy_texture(dress_model, model.textures[material.sphere_texture_index], model.path, is_dress=False)
                copy_material.sphere_texture_index = copy_texture.index if copy_texture else -1

            dress_model.materials.append(copy_material, is_sort=False)
            model_material_map[material.index] = copy_material.index
            if model_skin_materials[material.name]:
                model_skin_vertex_positions[material.name] = MVectorDict()

            for face_index in range(prev_faces_count, prev_faces_count + material.vertices_count // 3):
                faces = []
                for vertex_index in model.faces[face_index].vertices:
                    if vertex_index not in model_vertex_map:
                        copy_vertex = model.vertices[vertex_index].copy()
                        copy_vertex.index = -1
                        copy_vertex.deform.indexes = np.vectorize(model_all_bone_map.get)(copy_vertex.deform.indexes)

                        # 変形後の位置に頂点を配置する
                        mat = np.zeros((4, 4))
                        for n in range(copy_vertex.deform.count):
                            bone_index = model.vertices[vertex_index].deform.indexes[n]
                            bone_weight = model.vertices[vertex_index].deform.weights[n]
                            mat += model_matrixes[0, model.bones[bone_index].name].local_matrix.vector * bone_weight
                        copy_vertex.position = MMatrix4x4(*mat.flatten()) * copy_vertex.position
                        if model_skin_materials[material.name]:
                            model_skin_vertex_positions[material.name].append(vertex_index, copy_vertex.position.copy())

                        faces.append(len(dress_model.vertices))
                        model_vertex_map[vertex_index] = len(dress_model.vertices)
                        dress_model.vertices.append(copy_vertex, is_sort=False)
                    else:
                        faces.append(model_vertex_map[vertex_index])
                dress_model.faces.append(Face(vertex_index0=faces[0], vertex_index1=faces[1], vertex_index2=faces[2]), is_sort=False)

            prev_faces_count += material.vertices_count // 3

            if not len(dress_model.materials) % 10:
                logger.info("-- 材質出力: {s}", s=len(dress_model.materials))

        model_skin_positions = MVectorDict()
        for model_material_name, is_model_skin_material in model_skin_materials.items():
            if is_model_skin_material and model_skin_vertex_positions[model_material_name].keys():
                model_skin_positions.append(
                    model.materials[model_material_name].index,
                    MVector3D(*model_skin_vertex_positions[model_material_name].mean_value()),
                )

        dress_skin_vertex_positions: dict[str, MVectorDict] = {}
        prev_faces_count = 0
        for material in dress.materials:
            if 1 > dress_material_alphas[material.name]:
                prev_faces_count += material.vertices_count // 3
                continue
            copy_material = material.copy()
            copy_material.name = f"Cos:{copy_material.name}"
            copy_material.index = len(dress_model.materials)
            if dress_skin_materials[material.name]:
                dress_skin_vertex_positions[material.name] = MVectorDict()

            if 0 <= material.texture_index:
                copy_texture = self.copy_texture(dress_model, dress.textures[material.texture_index], dress.path, is_dress=True)
                copy_material.texture_index = copy_texture.index if copy_texture else -1

            if material.toon_sharing_flg == ToonSharing.INDIVIDUAL and 0 <= material.toon_texture_index:
                copy_texture = self.copy_texture(dress_model, dress.textures[material.toon_texture_index], dress.path, is_dress=True)
                copy_material.toon_texture_index = copy_texture.index if copy_texture else -1

            if material.sphere_mode != SphereMode.INVALID and 0 < material.sphere_texture_index:
                copy_texture = self.copy_texture(dress_model, dress.textures[material.sphere_texture_index], dress.path, is_dress=True)
                copy_material.sphere_texture_index = copy_texture.index if copy_texture else -1

            dress_model.materials.append(copy_material, is_sort=False)
            dress_material_map[material.index] = copy_material.index

            for face_index in range(prev_faces_count, prev_faces_count + copy_material.vertices_count // 3):
                faces = []
                for vertex_index in dress.faces[face_index].vertices:
                    if vertex_index not in dress_vertex_map:
                        copy_vertex = dress.vertices[vertex_index].copy()
                        copy_vertex.index = -1
                        copy_vertex.deform.indexes = np.vectorize(dress_all_bone_map.get)(copy_vertex.deform.indexes)

                        # 変形後の位置に頂点を配置する
                        mat = np.zeros((4, 4))
                        for n in range(copy_vertex.deform.count):
                            bone_index = dress.vertices[vertex_index].deform.indexes[n]
                            bone_weight = dress.vertices[vertex_index].deform.weights[n]
                            mat += dress_matrixes[0, dress.bones[bone_index].name].local_matrix.vector * bone_weight
                        copy_vertex.position = MMatrix4x4(*mat.flatten()) * copy_vertex.position
                        if dress_skin_materials[material.name]:
                            dress_skin_vertex_positions[material.name].append(vertex_index, copy_vertex.position.copy())

                        faces.append(len(dress_model.vertices))
                        dress_vertex_map[vertex_index] = len(dress_model.vertices)
                        dress_model.vertices.append(copy_vertex, is_sort=False)
                    else:
                        faces.append(dress_vertex_map[vertex_index])
                dress_model.faces.append(Face(vertex_index0=faces[0], vertex_index1=faces[1], vertex_index2=faces[2]), is_sort=False)

            prev_faces_count += material.vertices_count // 3

            if dress_skin_materials[material.name]:
                # 肌材質の場合、人物側の肌材質から最も近い距離の材質の設定をコピーする
                dress_mean_skin_position = MVector3D(*dress_skin_vertex_positions[material.name].mean_value())
                model_skin_material_index = model_skin_positions.nearest_key(dress_mean_skin_position)

                model_skin_material = dress_model.materials[model.materials[model_skin_material_index].name]
                copy_material.diffuse = model_skin_material.diffuse.copy()
                copy_material.specular = model_skin_material.specular.copy()
                copy_material.specular_factor = model_skin_material.specular_factor
                copy_material.ambient = model_skin_material.ambient.copy()
                copy_material.draw_flg = model_skin_material.draw_flg
                copy_material.edge_color = model_skin_material.edge_color.copy()
                copy_material.edge_size = model_skin_material.edge_size
                # texture_index はコピーしない
                copy_material.sphere_texture_index = model_skin_material.sphere_texture_index
                copy_material.sphere_mode = model_skin_material.sphere_mode
                copy_material.toon_sharing_flg = model_skin_material.toon_sharing_flg
                copy_material.toon_texture_index = model_skin_material.toon_texture_index

                # テクスチャの色を補正
                if 0 <= copy_material.texture_index and 0 <= model.materials[model_skin_material_index].texture_index:
                    self.correct_texture(model, dress_model, model.materials[model_skin_material_index], copy_material)

            if not len(dress_model.materials) % 10:
                logger.info("-- 材質出力: {s}", s=len(dress_model.materials))

        # ---------------------------------

        logger.info("モーフ出力", decoration=MLogger.Decoration.LINE)

        # キー: 元々のINDEX、値: コピー先INDEX
        model_morph_map: dict[int, int] = {-1: -1}
        dress_morph_map: dict[int, int] = {-1: -1}

        for is_group in (False, True):
            for morph in model.morphs:
                if (
                    morph.is_system
                    or (not is_group and morph.morph_type == MorphType.GROUP)
                    or (is_group and morph.morph_type != MorphType.GROUP)
                ):
                    continue

                if is_group:
                    copy_morph = self.copy_group_morph(morph, model_morph_map)
                else:
                    copy_morph = self.copy_morph(morph, model_all_bone_map, model_vertex_map, model_material_map)

                if copy_morph.offsets:
                    copy_morph.index = len(dress_model.morphs)
                    model_morph_map[morph.index] = len(dress_model.morphs)
                    dress_model.morphs.append(copy_morph)

                if not len(dress_model.morphs) % 50:
                    logger.info("-- モーフ出力: {s}", s=len(dress_model.morphs))

        for is_group in (False, True):
            for morph in dress.morphs:
                if (
                    morph.is_system
                    or (not is_group and morph.morph_type == MorphType.GROUP)
                    or (is_group and morph.morph_type != MorphType.GROUP)
                ):
                    continue

                if is_group:
                    copy_morph = self.copy_group_morph(morph, dress_morph_map)
                else:
                    copy_morph = self.copy_morph(morph, dress_all_bone_map, dress_vertex_map, dress_material_map)

                copy_morph.name = f"Cos:{copy_morph.name}"

                if copy_morph.offsets:
                    copy_morph.index = len(dress_model.morphs)
                    dress_morph_map[morph.index] = len(dress_model.morphs)
                    dress_model.morphs.append(copy_morph)

                if not len(dress_model.morphs) % 50:
                    logger.info("-- モーフ出力: {s}", s=len(dress_model.morphs))

        # ---------------------------------

        logger.info("剛体出力", decoration=MLogger.Decoration.LINE)

        # キー: 元々のINDEX、値: コピー先INDEX
        model_rigidbody_map: dict[int, int] = {-1: -1}
        dress_rigidbody_map: dict[int, int] = {-1: -1}

        for rigidbody in model.rigidbodies:
            if (
                rigidbody.is_system
                or 0 > rigidbody.bone_index
                or rigidbody.bone_index not in dress_model_bones.model_map
                or model.bones[rigidbody.bone_index].name not in dress_model.bones
            ):
                continue

            model_copy_rigidbody = rigidbody.copy()
            model_copy_rigidbody.index = len(dress_model.rigidbodies)
            model_copy_rigidbody.bone_index = model_all_bone_map[rigidbody.bone_index]

            # ボーンと剛体の位置関係から剛体位置を求め直す
            model_bone_name = model.bones[rigidbody.bone_index].name
            rigidbody_local_position = model_original_matrixes[0, model_bone_name].global_matrix.inverse() * rigidbody.shape_position
            rigidbody_copy_position = model_matrixes[0, model_bone_name].global_matrix * rigidbody_local_position
            rigidbody_copy_scale = MVector3D(
                model_matrixes[0, model_bone_name].global_matrix[0, 0],
                model_matrixes[0, model_bone_name].global_matrix[1, 1],
                model_matrixes[0, model_bone_name].global_matrix[2, 2],
            )

            model_copy_rigidbody.shape_position = rigidbody_copy_position
            model_copy_rigidbody.shape_size *= rigidbody_copy_scale

            model_rigidbody_map[rigidbody.index] = len(dress_model.rigidbodies)
            dress_model.rigidbodies.append(model_copy_rigidbody)

            if not len(dress_model.rigidbodies) % 50:
                logger.info("-- 剛体出力: {s}", s=len(dress_model.rigidbodies))

        for rigidbody in dress.rigidbodies:
            if (
                rigidbody.is_system
                or 0 > rigidbody.bone_index
                or rigidbody.bone_index not in dress_model_bones.dress_map
                or (
                    not dress.bones[rigidbody.bone_index].is_standard
                    and f"Cos:{dress.bones[rigidbody.bone_index].name}" not in dress_model.bones
                )
            ):
                continue
            if (
                rigidbody.name in dress_model.rigidbodies
                and dress_model.bones[dress_model.rigidbodies[rigidbody.name].bone_index].is_standard
            ):
                # 既に同名の準標準ボーンに繋がる剛体がある場合、INDEXだけ保持してスルー
                dress_rigidbody_map[rigidbody.index] = dress_model.rigidbodies[rigidbody.name].index

                # 位置とサイズは衣装に合わせる
                dress_bone_name = dress.bones[rigidbody.bone_index].name
                rigidbody_local_position = dress_original_matrixes[0, dress_bone_name].global_matrix.inverse() * rigidbody.shape_position
                rigidbody_copy_position = dress_matrixes[0, dress_bone_name].global_matrix * rigidbody_local_position
                rigidbody_copy_scale = MVector3D(
                    dress_matrixes[0, dress_bone_name].global_matrix[0, 0],
                    dress_matrixes[0, dress_bone_name].global_matrix[1, 1],
                    dress_matrixes[0, dress_bone_name].global_matrix[2, 2],
                )

                dress_model.rigidbodies[rigidbody.name].shape_position = rigidbody_copy_position
                dress_model.rigidbodies[rigidbody.name].shape_size = dress.rigidbodies[rigidbody.name].shape_size * rigidbody_copy_scale

                continue

            dress_copy_rigidbody = rigidbody.copy()
            dress_copy_rigidbody.name = f"Cos:{rigidbody.name}"
            dress_copy_rigidbody.index = len(dress_model.rigidbodies)
            dress_copy_rigidbody.bone_index = dress_all_bone_map[rigidbody.bone_index]

            # ボーンと剛体の位置関係から剛体位置を求め直す
            dress_bone_name = dress.bones[rigidbody.bone_index].name
            rigidbody_local_position = dress_original_matrixes[0, dress_bone_name].global_matrix.inverse() * rigidbody.shape_position
            rigidbody_copy_position = dress_matrixes[0, dress_bone_name].global_matrix * rigidbody_local_position
            rigidbody_copy_scale = MVector3D(
                dress_matrixes[0, dress_bone_name].global_matrix[0, 0],
                dress_matrixes[0, dress_bone_name].global_matrix[1, 1],
                dress_matrixes[0, dress_bone_name].global_matrix[2, 2],
            )

            dress_copy_rigidbody.shape_position = rigidbody_copy_position
            dress_copy_rigidbody.shape_size *= rigidbody_copy_scale

            dress_rigidbody_map[rigidbody.index] = len(dress_model.rigidbodies)
            dress_model.rigidbodies.append(dress_copy_rigidbody)

            if not len(dress_model.rigidbodies) % 50:
                logger.info("-- 剛体出力: {s}", s=len(dress_model.rigidbodies))

        # ---------------------------------

        logger.info("ジョイント出力", decoration=MLogger.Decoration.LINE)

        for joint in model.joints:
            if joint.is_system:
                continue
            if not (joint.rigidbody_index_a in model_rigidbody_map and joint.rigidbody_index_b in model_rigidbody_map):
                continue

            rigidbody_a = dress_model.rigidbodies[model_rigidbody_map[joint.rigidbody_index_a]]
            rigidbody_b = dress_model.rigidbodies[model_rigidbody_map[joint.rigidbody_index_b]]

            model_copy_joint = joint.copy()
            model_copy_joint.index = len(dress_model.joints)
            model_copy_joint.rigidbody_index_a = rigidbody_a.index
            model_copy_joint.rigidbody_index_b = rigidbody_b.index

            model_bone_a = model.bones[model.rigidbodies[joint.rigidbody_index_a].bone_index]
            model_bone_b = model.bones[model.rigidbodies[joint.rigidbody_index_b].bone_index]

            joint_a_local_position = model_original_matrixes[0, model_bone_a.name].global_matrix.inverse() * joint.position
            joint_b_local_position = model_original_matrixes[0, model_bone_b.name].global_matrix.inverse() * joint.position
            joint_a_copy_position = model_matrixes[0, model_bone_a.name].global_matrix * joint_a_local_position
            joint_b_copy_position = model_matrixes[0, model_bone_b.name].global_matrix * joint_b_local_position

            model_copy_joint.position = (joint_a_copy_position + joint_b_copy_position) / 2

            dress_model.joints.append(model_copy_joint)

            if not len(dress_model.joints) % 50:
                logger.info("-- ジョイント出力: {s}", s=len(dress_model.joints))

        for joint in dress.joints:
            if joint.is_system:
                continue
            if not (joint.rigidbody_index_a in dress_rigidbody_map and joint.rigidbody_index_b in dress_rigidbody_map):
                continue

            rigidbody_a = dress_model.rigidbodies[dress_rigidbody_map[joint.rigidbody_index_a]]
            rigidbody_b = dress_model.rigidbodies[dress_rigidbody_map[joint.rigidbody_index_b]]

            dress_copy_joint = joint.copy()
            dress_copy_joint.name = f"Cos:{joint.name}"
            dress_copy_joint.index = len(dress_model.joints)
            dress_copy_joint.rigidbody_index_a = rigidbody_a.index
            dress_copy_joint.rigidbody_index_b = rigidbody_b.index

            dress_bone_a = dress.bones[dress.rigidbodies[joint.rigidbody_index_a].bone_index]
            dress_bone_b = dress.bones[dress.rigidbodies[joint.rigidbody_index_b].bone_index]

            joint_a_local_position = dress_original_matrixes[0, dress_bone_a.name].global_matrix.inverse() * joint.position
            joint_b_local_position = dress_original_matrixes[0, dress_bone_b.name].global_matrix.inverse() * joint.position
            joint_a_copy_position = dress_matrixes[0, dress_bone_a.name].global_matrix * joint_a_local_position
            joint_b_copy_position = dress_matrixes[0, dress_bone_b.name].global_matrix * joint_b_local_position

            dress_copy_joint.index = len(dress_model.joints)
            dress_copy_joint.position = (joint_a_copy_position + joint_b_copy_position) / 2

            dress_model.joints.append(dress_copy_joint)

            if not len(dress_model.joints) % 50:
                logger.info("-- ジョイント出力: {s}", s=len(dress_model.joints))

        # ---------------------------------

        logger.info("表示枠出力", decoration=MLogger.Decoration.LINE)

        # まずは人物側の表情を表情順に入れる
        morph_cnt = 0
        for morph in model.morphs:
            if morph.name not in dress_model.morphs:
                continue
            if [
                reference
                for reference in model.display_slots["表情"].references
                if reference.display_type == DisplayType.MORPH and reference.display_index == morph.index
            ]:
                dress_model.display_slots["表情"].references.append(
                    DisplaySlotReference(display_type=DisplayType.MORPH, display_index=dress_model.morphs[morph.name].index)
                )

                morph_cnt += 1
                if morph_cnt % 100 == 0:
                    logger.info("-- モーフ表示枠出力: {s}", s=morph_cnt)

        # その後、衣装側の表情を入れる
        for morph in dress.morphs:
            if morph.name not in dress_model.morphs:
                continue
            if [
                reference
                for reference in dress.display_slots["表情"].references
                if reference.display_type == DisplayType.MORPH and reference.display_index == morph.index
            ]:
                display_index = (
                    dress_model.morphs[morph.name].index
                    if morph.name in dress_model.morphs
                    else dress_model.morphs[f"Cos:{morph.name}"].index
                )
                dress_model.display_slots["表情"].references.append(
                    DisplaySlotReference(display_type=DisplayType.MORPH, display_index=display_index)
                )

                morph_cnt += 1
                if morph_cnt % 100 == 0:
                    logger.info("-- モーフ表示枠出力: {s}", s=morph_cnt)

        dress_display_slot_indexes: dict[int, int] = {}

        for bone in dress_model.bones:
            if 0 == bone.index:
                # 全親は単品で追加
                dress_model.display_slots["Root"].references.append(
                    DisplaySlotReference(display_type=DisplayType.BONE, display_index=bone.index)
                )
                continue
            # 表示枠
            if not bone.is_visible:
                # 非表示ボーンはスルー
                continue
            # 人物側の表示枠に基本的には合わせる
            display_slot_name = ""
            display_slot_english_name = ""
            for model_display_slot in model.display_slots:
                if model_display_slot.special_flg == Switch.ON:
                    continue
                for model_reference in model_display_slot.references:
                    if model_reference.display_type == DisplayType.MORPH:
                        continue
                    if model.bones[model_reference.display_index].name == bone.name:
                        # 同じ名前のとこに入れる
                        display_slot_name = model_display_slot.name
                        display_slot_english_name = model_display_slot.english_name
                        break
                if display_slot_name:
                    break

            if not display_slot_name:
                # 人物側に表示枠が見つからなかった場合、衣装側を確認する
                for dress_display_slot in dress.display_slots:
                    if dress_display_slot.special_flg == Switch.ON:
                        continue
                    for dress_reference in dress_display_slot.references:
                        if dress_reference.display_type == DisplayType.MORPH:
                            continue
                        if dress.bones[dress_reference.display_index].name == bone.name:
                            # 同じ名前のとこに入れる
                            display_slot_name = dress_display_slot.name
                            display_slot_english_name = dress_display_slot.english_name
                            break
                    if display_slot_name:
                        break

            if not display_slot_name:
                # それでも見つからなければ、親の表示枠に入れる
                for tree_index in reversed(dress_model.bone_trees[bone.name].indexes):
                    if tree_index in dress_display_slot_indexes:
                        display_slot_name = dress_model.display_slots[dress_display_slot_indexes[tree_index]].name
                        display_slot_english_name = dress_model.display_slots[dress_display_slot_indexes[tree_index]].english_name
                        break

            if display_slot_name:
                # 既存の表示枠がある場合はそこに追加
                if display_slot_name not in dress_model.display_slots:
                    dress_model.display_slots.append(DisplaySlot(name=display_slot_name, english_name=display_slot_english_name))
                dress_model.display_slots[display_slot_name].references.append(
                    DisplaySlotReference(display_type=DisplayType.BONE, display_index=bone.index)
                )
                dress_display_slot_indexes[bone.index] = dress_model.display_slots[display_slot_name].index
            else:
                # なければ新規作成
                dress_model.display_slots.append(DisplaySlot(name=bone.name, english_name=bone.english_name))
                dress_model.display_slots[bone.name].references.append(
                    DisplaySlotReference(display_type=DisplayType.BONE, display_index=bone.index)
                )
                dress_display_slot_indexes[bone.index] = dress_model.display_slots[bone.name].index

            if not bone.index % 100:
                logger.info("-- ボーン表示枠出力: {s}", s=bone.index)

        for bone in dress_model.bones:
            if bone.is_ik and 0 > bone.ik.bone_index:
                # IKターゲットが無い場合、出力対象外にする
                dress_model.remove_bone(bone.name)
                continue

        logger.info("モデル出力", decoration=MLogger.Decoration.LINE)

        PmxWriter(dress_model, output_path).save()

    def correct_texture(self, model: PmxModel, dress: PmxModel, model_material: Material, dress_material: Material):
        logger.info("肌テクスチャ色補正", decoration=MLogger.Decoration.LINE)
        dress.update_vertices_by_material()

        model_texture = model.textures[model_material.texture_index]
        dress_texture = dress.textures[dress_material.texture_index]

        logger.info("人物(補正元)材質: {m} -> 衣装(補正先)材質: {d}", m=model_material.name, d=dress_material.name)

        model_image = np.array(model_texture.image, np.float64)
        dress_image = np.copy(np.array(dress_texture.image, np.float64))
        # 補正衣装画像
        corrected_dress_image = np.asarray(np.copy(dress_image))

        # 人物の指定材質に割り当てられた頂点INDEXリスト
        model_vertex_indexes = model.vertices_by_materials[model_material.index]
        # 衣装の指定材質に割り当てられた頂点INDEXリスト
        dress_vertex_indexes = dress.vertices_by_materials[dress_material.index]

        # 人物の指定材質に割り当てられた面INDEXリスト
        model_face_indexes = model.faces_by_materials[model_material.index]
        # 衣装の指定材質に割り当てられた面INDEXリスト
        dress_face_indexes = dress.faces_by_materials[dress_material.index]

        logger.info("人物: 近似頂点選別")

        # 人物の頂点に紐付く面の構成頂点INDEXがmodel_vertex_indexesの何番目に存在しているかのリスト
        model_near_vertices: dict[int, list[int]] = {}
        for i, model_face_index in enumerate(model_face_indexes):
            logger.count("人物: 近似頂点選別", i, len(model_face_indexes), display_block=100)

            for vertex_index in model.faces[model_face_index].vertices:
                if vertex_index not in model_near_vertices:
                    model_near_vertices[vertex_index] = []
                for near_vertex_index in model.faces[model_face_index].vertices:
                    if near_vertex_index in model_vertex_indexes:
                        model_near_vertices[vertex_index].append(
                            [vi for (vi, vidx) in enumerate(model_vertex_indexes) if vidx == near_vertex_index][0]
                        )

        logger.info("衣装: 近似頂点選別")

        # 衣装の頂点に紐付く面の構成頂点INDEXがdress_vertex_indexesの何番目に存在しているかのリスト
        dress_near_vertices: dict[int, list[int]] = {}
        for i, dress_face_index in enumerate(dress_face_indexes):
            logger.count("衣装: 近似頂点選別", i, len(dress_face_indexes), display_block=100)

            for vertex_index in dress.faces[dress_face_index].vertices:
                if vertex_index not in dress_near_vertices:
                    dress_near_vertices[vertex_index] = []
                for near_vertex_index in dress.faces[dress_face_index].vertices:
                    if near_vertex_index in dress_vertex_indexes:
                        dress_near_vertices[vertex_index].append(
                            [vi for (vi, vidx) in enumerate(dress_vertex_indexes) if vidx == near_vertex_index][0]
                        )

        # 人物の指定材質に割り当てられた頂点INDEXが配置されている3次元頂点の位置
        model_vertex_positions = MVectorDict()
        for model_vertex_index in model_vertex_indexes:
            model_vertex_positions.append(model_vertex_index, model.vertices[model_vertex_index].position)

        # 衣装の指定材質に割り当てられた頂点INDEXが配置されている3次元頂点の位置
        dress_vertex_positions = MVectorDict()
        for dress_vertex_index in dress_vertex_indexes:
            dress_vertex_positions.append(dress_vertex_index, dress.vertices[dress_vertex_index].position)

        # 衣装の指定材質に割り当てられた頂点INDEXが配置されている3次元頂点の位置に最も近い人物頂点を見つける
        model_vertex_uv_list: list[np.ndarray] = []
        dress_vertex_uv_list: list[np.ndarray] = []

        # 面を構成している頂点（近似頂点）のリスト
        model_vertices_by_face: list[list[int]] = []
        dress_vertices_by_face: list[list[int]] = []

        # 材質に割り当てられたテクスチャの色のRGBだけを取り出す
        model_image_colors = np.copy(model_image[..., :3])
        dress_image_colors = np.copy(dress_image[..., :3])

        logger.info("近似テクスチャUV取得")

        for i, dress_vertex_index in enumerate(dress_vertex_indexes):
            logger.count("近似テクスチャUV取得", i, len(dress_vertex_indexes), display_block=500)

            nearest_model_vertex_index = model_vertex_positions.nearest_key(dress.vertices[dress_vertex_index].position)
            nearest_model_vertex = model.vertices[nearest_model_vertex_index]
            # 人物の指定頂点に割り当てられたテクスチャとUVから、テクスチャの該当位置を取得する
            model_vertex_uv_list.append(
                np.array([int(nearest_model_vertex.uv.x * model_image.shape[0]), int(nearest_model_vertex.uv.y * model_image.shape[1])])
            )
            # 面を構成している頂点（近似頂点）を求めておく
            model_vertices_by_face.append(model_near_vertices[nearest_model_vertex_index])

            # 衣装の指定頂点に割り当てられたテクスチャとUVから、テクスチャの該当位置を取得する
            dress_vertex = dress.vertices[dress_vertex_index]
            dress_vertex_uv_list.append(
                np.array([int(dress_vertex.uv.x * dress_image.shape[0]), int(dress_vertex.uv.y * dress_image.shape[1])])
            )
            dress_vertices_by_face.append(dress_near_vertices[dress_vertex_index])

        model_vertex_uvs = np.array(model_vertex_uv_list)
        dress_vertex_uvs = np.array(dress_vertex_uv_list)

        filled_dress_image = np.zeros(dress_image.shape)

        logger.info("肌テクスチャ色補正")

        for fidx, (model_near_vertices_by_face, dress_near_vertices_by_face) in enumerate(
            zip(model_vertices_by_face, dress_vertices_by_face)
        ):
            logger.count("肌テクスチャ色補正", fidx, len(model_vertices_by_face), display_block=500)

            model_near_vertex_uvs = model_vertex_uvs[np.array(model_near_vertices_by_face)]
            model_near_vertex_uvs[:, 0] = np.clip(model_near_vertex_uvs[:, 0], 0, model_image_colors.shape[0] - 1)
            model_near_vertex_uvs[:, 1] = np.clip(model_near_vertex_uvs[:, 1], 0, model_image_colors.shape[1] - 1)

            model_vertex_mean_color = np.mean(model_image_colors[model_near_vertex_uvs[:, 0], model_near_vertex_uvs[:, 1], :], axis=0)

            dress_near_vertex_uvs = dress_vertex_uvs[np.array(dress_near_vertices_by_face)]
            dress_near_vertex_uvs[:, 0] = np.clip(dress_near_vertex_uvs[:, 0], 0, dress_image_colors.shape[0] - 1)
            dress_near_vertex_uvs[:, 1] = np.clip(dress_near_vertex_uvs[:, 1], 0, dress_image_colors.shape[1] - 1)

            dress_vertex_mean_color = np.mean(dress_image_colors[dress_near_vertex_uvs[:, 0], dress_near_vertex_uvs[:, 1], :], axis=0)

            dress_min_uv = np.min(dress_near_vertex_uvs, axis=0)
            dress_max_uv = np.max(dress_near_vertex_uvs, axis=0)

            # 人物と衣装の該当UV位置にある色の差分を取得する
            color_difference = model_vertex_mean_color - dress_vertex_mean_color

            # テクスチャの処理対象領域内でまだ補正されていない箇所だけ補正する
            for u, v in product(
                [u for u in range(dress_min_uv[1], (dress_max_uv[1] + 1))], [v for v in range(dress_min_uv[0], (dress_max_uv[0] + 1))]
            ):
                if np.sum(filled_dress_image[u, v]) == 0:
                    corrected_dress_image[u, v, :3] += color_difference
                    filled_dress_image[u, v, :3] = np.where(color_difference == 0, 1, color_difference)

        # 補正後の色が0未満または255を超える場合、範囲内にクリップする
        corrected_dress_image = np.clip(corrected_dress_image, 0, 255)

        # 補正後のテクスチャを保存する
        corrected_dress_output = Image.fromarray(corrected_dress_image.astype(np.uint8))
        corrected_dress_output.save(os.path.abspath(os.path.join(os.path.dirname(dress.path), dress_texture.name)))

    def copy_texture(self, dest_model: PmxModel, texture: Texture, src_model_path: str, is_dress: bool) -> Optional[Texture]:
        copy_texture_name = os.path.join("Costume", texture.name) if is_dress else texture.name

        if copy_texture_name in dest_model.textures:
            # 既に同じテクスチャが定義されている場合、そのINDEXを返す
            return dest_model.textures[copy_texture_name]

        copy_texture = texture.copy()
        copy_texture.index = len(dest_model.textures)
        texture_path = os.path.abspath(os.path.join(os.path.dirname(src_model_path), copy_texture.name))
        if copy_texture.name and os.path.exists(texture_path) and os.path.isfile(texture_path):
            if is_dress:
                copy_texture.name = copy_texture_name
                new_texture_path = os.path.join(os.path.dirname(dest_model.path), copy_texture_name)
            else:
                new_texture_path = os.path.join(os.path.dirname(dest_model.path), texture.name)
            os.makedirs(os.path.dirname(new_texture_path), exist_ok=True)
            shutil.copyfile(texture_path, new_texture_path)
        else:
            return None
        copy_texture.index = len(dest_model.textures)
        dest_model.textures.append(copy_texture, is_sort=False)

        return copy_texture

    def copy_morph(
        self,
        morph: Morph,
        model_bone_map: dict[int, int],
        model_vertex_map: dict[int, int],
        model_material_map: dict[int, int],
    ) -> Morph:
        copy_morph = Morph(name=morph.name, english_name=morph.english_name)
        if morph.morph_type == MorphType.VERTEX:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.VERTEX
            for offset in morph.offsets:
                vertex_offset: VertexMorphOffset = offset
                if vertex_offset.vertex_index in model_vertex_map:
                    copy_morph.offsets.append(
                        VertexMorphOffset(model_vertex_map[vertex_offset.vertex_index], vertex_offset.position.copy())
                    )
        elif morph.morph_type == MorphType.UV:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.UV
            for offset in morph.offsets:
                uv_offset: UvMorphOffset = offset
                if uv_offset.vertex_index in model_vertex_map:
                    copy_morph.offsets.append(UvMorphOffset(model_vertex_map[uv_offset.vertex_index], uv_offset.uv.copy()))
        elif morph.morph_type == MorphType.EXTENDED_UV1:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.EXTENDED_UV1
            for offset in morph.offsets:
                extend_uv1_offset: UvMorphOffset = offset
                if extend_uv1_offset.vertex_index in model_vertex_map:
                    copy_morph.offsets.append(UvMorphOffset(model_vertex_map[extend_uv1_offset.vertex_index], extend_uv1_offset.uv.copy()))
        elif morph.morph_type == MorphType.EXTENDED_UV2:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.EXTENDED_UV2
            for offset in morph.offsets:
                extend_uv2_offset: UvMorphOffset = offset
                if extend_uv2_offset.vertex_index in model_vertex_map:
                    copy_morph.offsets.append(UvMorphOffset(model_vertex_map[extend_uv2_offset.vertex_index], extend_uv2_offset.uv.copy()))
        elif morph.morph_type == MorphType.EXTENDED_UV3:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.EXTENDED_UV3
            for offset in morph.offsets:
                extend_uv3_offset: UvMorphOffset = offset
                if extend_uv3_offset.vertex_index in model_vertex_map:
                    copy_morph.offsets.append(UvMorphOffset(model_vertex_map[extend_uv3_offset.vertex_index], extend_uv3_offset.uv.copy()))
        elif morph.morph_type == MorphType.EXTENDED_UV4:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.EXTENDED_UV4
            for offset in morph.offsets:
                extend_uv4_offset: UvMorphOffset = offset
                if extend_uv4_offset.vertex_index in model_vertex_map:
                    copy_morph.offsets.append(UvMorphOffset(model_vertex_map[extend_uv4_offset.vertex_index], extend_uv4_offset.uv.copy()))
        elif morph.morph_type == MorphType.MATERIAL:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.MATERIAL
            for offset in morph.offsets:
                material_offset: MaterialMorphOffset = offset
                if material_offset.material_index in model_material_map:
                    copy_morph.offsets.append(
                        MaterialMorphOffset(
                            model_material_map[material_offset.material_index],
                            material_offset.calc_mode,
                            material_offset.diffuse.copy(),
                            material_offset.specular.copy(),
                            material_offset.specular_factor,
                            material_offset.ambient.copy(),
                            material_offset.edge_color.copy(),
                            material_offset.edge_size,
                            material_offset.texture_factor.copy(),
                            material_offset.sphere_texture_factor.copy(),
                            material_offset.toon_texture_factor.copy(),
                        )
                    )
        elif morph.morph_type == MorphType.BONE:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.BONE
            for offset in morph.offsets:
                bone_offset: BoneMorphOffset = offset
                if bone_offset.bone_index in model_bone_map:
                    copy_morph.offsets.append(
                        BoneMorphOffset(
                            model_bone_map[bone_offset.bone_index],
                            bone_offset.position.copy(),
                            bone_offset.rotation.qq.copy(),
                            bone_offset.scale.copy(),
                            bone_offset.local_position.copy(),
                            bone_offset.local_rotation.qq.copy(),
                            bone_offset.local_scale.copy(),
                        )
                    )

        return copy_morph

    def copy_group_morph(
        self,
        morph: Morph,
        model_morph_map: dict[int, int],
    ) -> Morph:
        copy_morph = Morph(name=morph.name, english_name=morph.english_name)

        if morph.morph_type == MorphType.GROUP:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.GROUP
            for offset in morph.offsets:
                group_offset: GroupMorphOffset = offset
                if group_offset.morph_index in model_morph_map:
                    copy_morph.offsets.append(GroupMorphOffset(model_morph_map[group_offset.morph_index], group_offset.morph_factor))

        return copy_morph

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
