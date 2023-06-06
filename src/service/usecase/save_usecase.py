import os
import shutil
from typing import Optional

import numpy as np

from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import (
    STANDARD_BONE_NAMES,
    Bone,
    BoneMorphOffset,
    DisplaySlot,
    DisplaySlotReference,
    DisplayType,
    Face,
    GroupMorphOffset,
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
        dress_material_alphas: dict[str, float],
        dress_scales: dict[str, MVector3D],
        dress_degrees: dict[str, MVector3D],
        dress_positions: dict[str, MVector3D],
    ) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        model_motion = VmdMotion("model fit motion")
        if model_config_motion:
            model_motion.morphs = model_config_motion.morphs.copy()

        dress_motion = VmdMotion("dress fit motion")
        if dress_config_motion:
            dress_motion.morphs = dress_config_motion.morphs.copy()

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
            dress_model.comment += message + "\r\n"
            fitting_messages.append(message)

        logger.info(
            "人物モデル: {m} ({p})\n衣装モデル: {d} ({q})\n個別フィッティング:\n{f}",
            m=model.name,
            p=os.path.basename(model.path),
            d=dress.name,
            q=os.path.basename(dress.path),
            f="\n".join(fitting_messages),
        )

        logger.info("出力準備", decoration=MLogger.Decoration.LINE)

        # 変形結果
        model_original_matrixes = VmdMotion().animate_bone([0], model)
        model_matrixes = model_motion.animate_bone([0], model)
        dress_original_matrixes = VmdMotion().animate_bone([0], dress)
        dress_matrixes = dress_motion.animate_bone([0], dress)

        logger.info("人物材質選り分け")
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

        logger.info("衣装材質選り分け")
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

        bone_map: dict[int, dict[str, list[str]]] = {}

        # 最初にルートを追加する
        root_bone = Bone(name=Bone.SYSTEM_ROOT_NAME, index=-1)
        root_bone.parent_index = -9
        root_bone.is_system = True
        dress_model.bones.append(root_bone, is_positive_index=False)
        bone_map[-1] = {
            "parent": [Bone.SYSTEM_ROOT_NAME],
            "tail": [Bone.SYSTEM_ROOT_NAME],
            "effect": [Bone.SYSTEM_ROOT_NAME],
            "ik_target": [Bone.SYSTEM_ROOT_NAME],
            "ik_link": [],
        }

        # キー: 元々のINDEX、値: コピー先INDEX
        model_bone_map: dict[int, int] = {-1: -1}
        dress_bone_map: dict[int, int] = {-1: -1}

        logger.info("ボーン出力", decoration=MLogger.Decoration.LINE)

        for bone in model.bones.writable():
            if bone.name in dress_model.bones:
                continue
            if (
                bone.name not in STANDARD_BONE_NAMES
                and bone.index in model.vertices_by_bones
                and not set(model.vertices_by_bones[bone.index]) & active_model_vertices
            ):
                # 準標準ではなく、元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                continue
            if (
                bone.name not in STANDARD_BONE_NAMES
                and not bone.is_visible
                and bone.parent_index in model.vertices_by_bones
                and not set(model.vertices_by_bones[bone.parent_index]) & active_model_vertices
            ):
                # 準標準ではなく、非表示ボーンで、親ボーンが元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                continue

            for dress_bone in dress.bones.writable():
                if (
                    0 <= dress_bone.tail_index
                    and dress_bone.name not in model.bones
                    and dress.bones[dress_bone.tail_index].name == bone.name
                ):
                    # 衣装だけのボーンが表示先が人物のボーンに繋がってる場合、その前に追加しておく
                    dress_prev_copy_bone = dress_bone.copy()
                    dress_prev_copy_bone.index = len(dress_model.bones.writable())
                    bone_map[dress_prev_copy_bone.index] = {
                        "parent": [
                            dress.bones[dress_bone.parent_index].name
                            if dress.bones[dress_bone.parent_index].is_standard or dress.bones[dress_bone.parent_index].is_system
                            else f"Cos:{dress.bones[dress_bone.parent_index].name}"
                        ],
                        "tail": [
                            dress.bones[dress_bone.tail_index].name
                            if dress.bones[dress_bone.tail_index].is_standard or dress.bones[dress_bone.tail_index].is_system
                            else f"Cos:{dress.bones[dress_bone.tail_index].name}"
                        ],
                        "effect": [
                            dress.bones[dress_bone.effect_index].name
                            if dress.bones[dress_bone.effect_index].is_standard or dress.bones[dress_bone.effect_index].is_system
                            else f"Cos:{dress.bones[dress_bone.effect_index].name}"
                        ],
                        "ik_target": [
                            (
                                dress.bones[dress_bone.ik.bone_index].name
                                if dress.bones[dress_bone.ik.bone_index].is_standard or dress.bones[dress_bone.ik.bone_index].is_system
                                else f"Cos:{dress.bones[dress_bone.ik.bone_index].name}"
                            )
                            if dress_bone.ik
                            else Bone.SYSTEM_ROOT_NAME
                        ],
                        "ik_link": [
                            (
                                dress.bones[link.bone_index].name
                                if dress.bones[link.bone_index].is_standard or dress.bones[link.bone_index].is_system
                                else f"Cos:{dress.bones[link.bone_index].name}"
                            )
                            for link in dress_bone.ik.links
                        ]
                        if dress_bone.ik
                        else [],
                    }

                    dress_model.bones.append(dress_prev_copy_bone, is_sort=False)
                    dress_bone_map[dress_bone.index] = dress_prev_copy_bone.index

                    # 表示枠
                    for display_slot in dress.display_slots:
                        for reference in display_slot.references:
                            if reference.display_type == DisplayType.BONE and reference.display_index == dress_bone.index:
                                if display_slot.name not in dress_model.display_slots:
                                    dress_model.display_slots.append(
                                        DisplaySlot(name=display_slot.name, english_name=display_slot.english_name)
                                    )
                                dress_model.display_slots[display_slot.name].references.append(
                                    DisplaySlotReference(display_type=DisplayType.BONE, display_index=dress_prev_copy_bone.index)
                                )
                                break

                    if not len(dress_model.bones) % 100:
                        logger.info("-- ボーン出力: {s}", s=len(dress_model.bones))

            model_copy_bone = bone.copy()
            model_copy_bone.index = len(dress_model.bones.writable())
            # 変形後の位置にボーンを配置する
            model_copy_bone.position = model_matrixes[0, bone.name].local_matrix * model_copy_bone.position
            bone_map[model_copy_bone.index] = {
                "parent": [model.bones[bone.parent_index].name],
                "tail": [model.bones[bone.tail_index].name],
                "effect": [model.bones[bone.effect_index].name],
                "ik_target": [model.bones[bone.ik.bone_index].name if bone.ik else Bone.SYSTEM_ROOT_NAME],
                "ik_link": [model.bones[link.bone_index].name for link in bone.ik.links] if bone.ik else [],
            }
            dress_model.bones.append(model_copy_bone, is_sort=False)
            model_bone_map[bone.index] = model_copy_bone.index

            # 表示枠
            if 0 == model_copy_bone.index:
                dress_model.display_slots["Root"].references.append(DisplaySlotReference(display_index=model_copy_bone.index))
            else:
                for display_slot in model.display_slots:
                    for reference in display_slot.references:
                        if reference.display_type == DisplayType.BONE and reference.display_index == bone.index:
                            if display_slot.name not in dress_model.display_slots:
                                dress_model.display_slots.append(
                                    DisplaySlot(name=display_slot.name, english_name=display_slot.english_name)
                                )
                            dress_model.display_slots[display_slot.name].references.append(
                                DisplaySlotReference(display_type=DisplayType.BONE, display_index=model_copy_bone.index)
                            )
                            break

            if not len(dress_model.bones) % 100:
                logger.info("-- ボーン出力: {s}", s=len(dress_model.bones))

        for bone in dress.bones.writable():
            if bone.is_standard and bone.name in dress_model.bones:
                # 既に登録済みの準標準ボーンは追加しない
                dress_bone_map[bone.index] = dress_model.bones[bone.name].index
                continue
            if (
                bone.name not in STANDARD_BONE_NAMES
                and bone.index in dress.vertices_by_bones
                and not set(dress.vertices_by_bones[bone.index]) & active_dress_vertices
            ):
                # 準標準ではなく、元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                continue
            if (
                bone.name not in STANDARD_BONE_NAMES
                and not bone.is_visible
                and bone.parent_index in dress.vertices_by_bones
                and not set(dress.vertices_by_bones[bone.parent_index]) & active_dress_vertices
            ):
                # 準標準ではなく、非表示ボーンで、親ボーンが元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                continue

            dress_copy_bone = bone.copy()
            if not bone.is_standard:
                # 準標準ではない場合、ボーン名をちょっと変える
                dress_copy_bone.name = f"Cos:{bone.name}"
            dress_copy_bone.index = len(dress_model.bones.writable())
            # 変形後の位置にボーンを配置する
            dress_copy_bone.position = dress_matrixes[0, bone.name].local_matrix * dress_copy_bone.position
            bone_map[dress_copy_bone.index] = {
                "parent": [
                    dress.bones[bone.parent_index].name
                    if dress.bones[bone.parent_index].is_standard or dress.bones[bone.parent_index].is_system
                    else f"Cos:{dress.bones[bone.parent_index].name}"
                ],
                "tail": [
                    dress.bones[bone.tail_index].name
                    if dress.bones[bone.tail_index].is_standard or dress.bones[bone.tail_index].is_system
                    else f"Cos:{dress.bones[bone.tail_index].name}"
                ],
                "effect": [
                    dress.bones[bone.effect_index].name
                    if dress.bones[bone.effect_index].is_standard or dress.bones[bone.effect_index].is_system
                    else f"Cos:{dress.bones[bone.effect_index].name}"
                ],
                "ik_target": [
                    (
                        dress.bones[bone.ik.bone_index].name
                        if dress.bones[bone.ik.bone_index].is_standard or dress.bones[bone.ik.bone_index].is_system
                        else f"Cos:{dress.bones[bone.ik.bone_index].name}"
                    )
                    if bone.ik
                    else Bone.SYSTEM_ROOT_NAME
                ],
                "ik_link": [
                    (
                        dress.bones[link.bone_index].name
                        if dress.bones[link.bone_index].is_standard or dress.bones[link.bone_index].is_system
                        else f"Cos:{dress.bones[link.bone_index].name}"
                    )
                    for link in bone.ik.links
                ]
                if bone.ik
                else [],
            }
            dress_model.bones.append(dress_copy_bone, is_sort=False)
            dress_bone_map[bone.index] = dress_copy_bone.index

            # 表示枠
            for display_slot in dress.display_slots:
                for reference in display_slot.references:
                    if reference.display_type == DisplayType.BONE and reference.display_index == bone.index:
                        if display_slot.name not in dress_model.display_slots:
                            dress_model.display_slots.append(DisplaySlot(name=display_slot.name, english_name=display_slot.english_name))
                        dress_model.display_slots[display_slot.name].references.append(
                            DisplaySlotReference(display_type=DisplayType.BONE, display_index=dress_copy_bone.index)
                        )
                        break

            if not len(dress_model.bones) % 100:
                logger.info("-- ボーン出力: {s}", s=len(dress_model.bones))

        logger.info("ボーン定義再設定", decoration=MLogger.Decoration.LINE)

        for bone in dress_model.bones:
            bone_setting = bone_map[bone.index]
            bone.parent_index = dress_model.bones[bone_setting["parent"][0]].index
            bone.tail_index = dress_model.bones[bone_setting["tail"][0]].index
            bone.effect_index = dress_model.bones[bone_setting["effect"][0]].index
            if bone.is_ik and bone.ik:
                bone.ik.bone_index = dress_model.bones[bone_setting["ik_target"][0]].index
                if 0 <= bone.ik.bone_index and dress_matrixes.exists(0, bone_setting["ik_target"][0]):
                    # IKターゲットとその位置を修正
                    bone.position = dress_matrixes[0, bone_setting["ik_target"][0]].position.copy()
                    dress_model.bones[bone.ik.bone_index].position = dress_matrixes[0, bone_setting["ik_target"][0]].position.copy()
                for n in range(len(bone.ik.links)):
                    bone.ik.links[n].bone_index = dress_model.bones[bone_setting["ik_link"][n]].index

            if 0 < bone.index and not bone.index % 100:
                logger.info("-- ボーン定義再設定: {s}", s=bone.index)

        # ---------------------------------

        # キー: 元々のINDEX、値: コピー先INDEX
        model_vertex_map: dict[int, int] = {-1: -1}
        dress_vertex_map: dict[int, int] = {-1: -1}

        model_material_map: dict[int, int] = {-1: -1}
        dress_material_map: dict[int, int] = {-1: -1}

        logger.info("材質出力", decoration=MLogger.Decoration.LINE)

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

            for face_index in range(prev_faces_count, prev_faces_count + material.vertices_count // 3):
                faces = []
                for vertex_index in model.faces[face_index].vertices:
                    if vertex_index not in model_vertex_map:
                        copy_vertex = model.vertices[vertex_index].copy()
                        copy_vertex.index = -1
                        copy_vertex.deform.indexes = np.vectorize(model_bone_map.get)(copy_vertex.deform.indexes)

                        # 変形後の位置に頂点を配置する
                        mat = np.zeros((4, 4))
                        for n in range(copy_vertex.deform.count):
                            bone_index = model.vertices[vertex_index].deform.indexes[n]
                            bone_weight = model.vertices[vertex_index].deform.weights[n]
                            mat += model_matrixes[0, model.bones[bone_index].name].local_matrix.vector * bone_weight
                        copy_vertex.position = MMatrix4x4(*mat.flatten()) * copy_vertex.position

                        faces.append(len(dress_model.vertices))
                        model_vertex_map[vertex_index] = len(dress_model.vertices)
                        dress_model.vertices.append(copy_vertex, is_sort=False)
                    else:
                        faces.append(model_vertex_map[vertex_index])
                dress_model.faces.append(Face(vertex_index0=faces[0], vertex_index1=faces[1], vertex_index2=faces[2]), is_sort=False)

            prev_faces_count += material.vertices_count // 3

            if not len(dress_model.materials) % 10:
                logger.info("-- 材質出力: {s}", s=len(dress_model.materials))

        prev_faces_count = 0
        for material in dress.materials:
            if 1 > dress_material_alphas[material.name]:
                prev_faces_count += material.vertices_count // 3
                continue
            copy_material = material.copy()
            copy_material.name = f"Cos:{copy_material.name}"
            copy_material.index = len(dress_model.materials)

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
                        copy_vertex.deform.indexes = np.vectorize(dress_bone_map.get)(copy_vertex.deform.indexes)

                        # 変形後の位置に頂点を配置する
                        mat = np.zeros((4, 4))
                        for n in range(copy_vertex.deform.count):
                            bone_index = dress.vertices[vertex_index].deform.indexes[n]
                            bone_weight = dress.vertices[vertex_index].deform.weights[n]
                            mat += dress_matrixes[0, dress.bones[bone_index].name].local_matrix.vector * bone_weight
                        copy_vertex.position = MMatrix4x4(*mat.flatten()) * copy_vertex.position

                        faces.append(len(dress_model.vertices))
                        dress_vertex_map[vertex_index] = len(dress_model.vertices)
                        dress_model.vertices.append(copy_vertex, is_sort=False)
                    else:
                        faces.append(dress_vertex_map[vertex_index])
                dress_model.faces.append(Face(vertex_index0=faces[0], vertex_index1=faces[1], vertex_index2=faces[2]), is_sort=False)

            prev_faces_count += material.vertices_count // 3

            if not len(dress_model.materials) % 10:
                logger.info("-- 材質出力: {s}", s=len(dress_model.materials))

        # ---------------------------------

        logger.info("モーフ出力", decoration=MLogger.Decoration.LINE)

        # キー: 元々のINDEX、値: コピー先INDEX
        model_morph_map: dict[int, int] = {-1: -1}
        dress_morph_map: dict[int, int] = {-1: -1}

        for morph in model.morphs:
            if morph.is_system:
                continue

            copy_morph, model_vertex_map = self.copy_morph(morph, model_bone_map, model_vertex_map, model_material_map, model_morph_map)

            if copy_morph.offsets:
                copy_morph.index = len(dress_model.morphs)
                model_morph_map[morph.index] = len(dress_model.morphs)
                dress_model.morphs.append(copy_morph)

                for display_slot in model.display_slots:
                    for reference in display_slot.references:
                        if reference.display_type == DisplayType.MORPH and reference.display_index == morph.index:
                            if display_slot.name not in dress_model.display_slots:
                                dress_model.display_slots.append(
                                    DisplaySlot(name=display_slot.name, english_name=display_slot.english_name)
                                )
                            dress_model.display_slots[display_slot.name].references.append(
                                DisplaySlotReference(display_type=DisplayType.MORPH, display_index=copy_morph.index)
                            )
                            break

            if not len(dress_model.morphs) % 50:
                logger.info("-- モーフ出力: {s}", s=len(dress_model.morphs))

        for morph in dress.morphs:
            if morph.is_system:
                continue

            copy_morph, dress_vertex_map = self.copy_morph(morph, dress_bone_map, dress_vertex_map, dress_material_map, dress_morph_map)
            copy_morph.name = f"Cos:{copy_morph.name}"

            if copy_morph.offsets:
                copy_morph.index = len(dress_model.morphs)
                dress_morph_map[morph.index] = len(dress_model.morphs)
                dress_model.morphs.append(copy_morph)

                for display_slot in dress.display_slots:
                    for reference in display_slot.references:
                        if reference.display_type == DisplayType.MORPH and reference.display_index == morph.index:
                            if display_slot.name not in dress_model.display_slots:
                                dress_model.display_slots.append(
                                    DisplaySlot(name=display_slot.name, english_name=display_slot.english_name)
                                )
                            dress_model.display_slots[display_slot.name].references.append(
                                DisplaySlotReference(display_type=DisplayType.MORPH, display_index=copy_morph.index)
                            )
                            break

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
                or rigidbody.bone_index not in model_bone_map
                or model.bones[rigidbody.bone_index].name not in dress_model.bones
            ):
                continue

            model_copy_rigidbody = rigidbody.copy()
            model_copy_rigidbody.index = len(dress_model.rigidbodies)
            model_copy_rigidbody.bone_index = model_bone_map[rigidbody.bone_index]

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
                or rigidbody.bone_index not in dress_bone_map
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
                continue

            dress_copy_rigidbody = rigidbody.copy()
            dress_copy_rigidbody.name = f"Cos:{rigidbody.name}"
            dress_copy_rigidbody.index = len(dress_model.rigidbodies)
            dress_copy_rigidbody.bone_index = dress_bone_map[rigidbody.bone_index]

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

        logger.info("モデル出力", decoration=MLogger.Decoration.LINE)

        PmxWriter(dress_model, output_path).save()

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
        model_morph_map: dict[int, int],
    ) -> tuple[Morph, dict[int, int]]:
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
                if material_offset.material_index in model_vertex_map:
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
        elif morph.morph_type == MorphType.GROUP:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.GROUP
            for offset in morph.offsets:
                group_offset: GroupMorphOffset = offset
                if group_offset.morph_index in model_morph_map:
                    copy_morph.offsets.append(GroupMorphOffset(model_morph_map[group_offset.morph_index], group_offset.morph_factor))

        return copy_morph, model_vertex_map
