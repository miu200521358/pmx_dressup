import os
import shutil

import numpy as np

from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import (
    STANDARD_BONE_NAMES,
    Bone,
    DisplaySlot,
    DisplaySlotReference,
    DisplayType,
    Face,
    Material,
    SphereMode,
    Texture,
    ToonSharing,
    Vertex,
)
from mlib.pmx.pmx_writer import PmxWriter
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class SaveUsecase:
    def save(
        self,
        model: PmxModel,
        dress: PmxModel,
        output_path: str,
        model_material_alphas: dict[str, float],
        dress_material_alphas: dict[str, float],
        dress_scales: dict[str, MVector3D],
        dress_degrees: dict[str, MVector3D],
        dress_positions: dict[str, MVector3D],
    ):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        motion = VmdMotion()

        # フィッティングモーフは常に適用
        bmf = VmdMorphFrame(0, "BoneFitting")
        bmf.ratio = 1
        motion.morphs[bmf.name].append(bmf)

        dress_model = PmxModel(output_path)
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

        for bone_type_name, scale, degree, position in zip(dress_scales.keys(), dress_scales.values(), dress_degrees.values(), dress_positions.values()):
            for ratio, axis_name, origin in (
                (scale.x, "SX", 1),
                (scale.y, "SY", 1),
                (scale.z, "SZ", 1),
                (degree.x, "RX", 0),
                (degree.y, "RY", 0),
                (degree.z, "RZ", 0),
                (position.x, "MX", 0),
                (position.y, "MY", 0),
                (position.z, "MZ", 0),
            ):
                mf = VmdMorphFrame(0, f"{__('調整')}:{__(bone_type_name)}:{axis_name}")
                mf.ratio = ratio - origin
                motion.morphs[mf.name].append(mf)
            dress_model.comment += __("  {b}: 縮尺{s}, 回転{r}, 移動{p}", b=bone_type_name, s=scale, r=degree, p=position) + "\r\n"

        logger.info("出力準備", decoration=MLogger.Decoration.LINE)

        # 変形結果
        dress_matrixes = motion.animate_bone(0, dress)

        logger.info("人物材質選り分け")
        model_vertices = model.get_vertices_by_bone()
        active_model_vertices = set(
            [
                vertex_index
                for material_index, vertices in model.get_vertices_by_material().items()
                if 1 == model_material_alphas[model.materials[material_index].name]
                for vertex_index in vertices
            ]
        )

        logger.info("衣装材質選り分け")
        dress_vertices = dress.get_vertices_by_bone()
        active_dress_vertices = set(
            [
                vertex_index
                for material_index, vertices in dress.get_vertices_by_material().items()
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

        model_bone_map: dict[int, int] = {-1: -1}
        dress_bone_map: dict[int, int] = {-1: -1}

        logger.info("ボーン出力", decoration=MLogger.Decoration.LINE)

        for bone in model.bones.writable():
            if bone.name in dress_model.bones:
                continue
            if bone.name not in STANDARD_BONE_NAMES and bone.index in model_vertices and not set(model_vertices[bone.index]) & active_model_vertices:
                # 準標準ではなく、元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                continue

            for dress_bone in dress.bones.writable():
                if 0 <= dress_bone.tail_index and dress_bone.name not in model.bones and dress.bones[dress_bone.tail_index].name == bone.name:
                    # 衣装だけのボーンが表示先が人物のボーンに繋がってる場合、その前に追加しておく
                    dress_prev_copy_bone: Bone = dress_bone.copy()
                    dress_prev_copy_bone.index = len(dress_model.bones.writable())
                    bone_map[dress_prev_copy_bone.index] = {
                        "parent": [dress.bones[dress_bone.parent_index].name],
                        "tail": [dress.bones[dress_bone.tail_index].name],
                        "effect": [dress.bones[dress_bone.effect_index].name],
                        "ik_target": [dress.bones[dress_bone.ik.bone_index].name if dress_bone.ik else Bone.SYSTEM_ROOT_NAME],
                        "ik_link": [dress.bones[link.bone_index].name for link in dress_bone.ik.links] if dress_bone.ik else [],
                    }
                    dress_model.bones.append(dress_prev_copy_bone, is_sort=False)
                    dress_bone_map[dress_bone.index] = dress_prev_copy_bone.index

                    # 表示枠
                    for display_slot in dress.display_slots:
                        for reference in display_slot.references:
                            if reference.display_type == DisplayType.BONE and reference.display_index == bone.index:
                                if display_slot.name not in dress_model.display_slots:
                                    dress_model.display_slots.append(DisplaySlot(name=display_slot.name, english_name=display_slot.english_name))
                                dress_model.display_slots[display_slot.name].references.append(
                                    DisplaySlotReference(display_type=DisplayType.BONE, display_index=dress_prev_copy_bone.index)
                                )
                                break

                    if not len(dress_model.bones) % 100:
                        logger.info("-- ボーン出力: {s}", s=len(dress_model.bones))

            model_copy_bone: Bone = bone.copy()
            model_copy_bone.index = len(dress_model.bones.writable())
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
                                dress_model.display_slots.append(DisplaySlot(name=display_slot.name, english_name=display_slot.english_name))
                            dress_model.display_slots[display_slot.name].references.append(
                                DisplaySlotReference(display_type=DisplayType.BONE, display_index=model_copy_bone.index)
                            )
                            break

            if not len(dress_model.bones) % 100:
                logger.info("-- ボーン出力: {s}", s=len(dress_model.bones))

        for bone in dress.bones.writable():
            if bone.name in dress_model.bones:
                # 既に登録済みのボーンは追加しない
                dress_bone_map[bone.index] = dress_model.bones[bone.name].index
                continue
            if bone.name not in STANDARD_BONE_NAMES and bone.index in dress_vertices and not set(dress_vertices[bone.index]) & active_dress_vertices:
                # 準標準ではなく、元々ウェイトを持っていて、かつ出力先にウェイトが乗ってる頂点が無い場合、スルー
                continue

            dress_copy_bone: Bone = bone.copy()
            dress_copy_bone.index = len(dress_model.bones.writable())
            # 変形後の位置にボーンを配置する
            dress_copy_bone.position = dress_matrixes[0, bone.name].matrix * dress_copy_bone.position
            bone_map[dress_copy_bone.index] = {
                "parent": [dress.bones[bone.parent_index].name],
                "tail": [dress.bones[bone.tail_index].name],
                "effect": [dress.bones[bone.effect_index].name],
                "ik_target": [dress.bones[bone.ik.bone_index].name if bone.ik else Bone.SYSTEM_ROOT_NAME],
                "ik_link": [dress.bones[link.bone_index].name for link in bone.ik.links] if bone.ik else [],
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
                for n in range(len(bone.ik.links)):
                    bone.ik.links[n].bone_index = dress_model.bones[bone_setting["ik_link"][n]].index

            if 0 < bone.index and not bone.index % 100:
                logger.info("-- ボーン定義再設定: {s}", s=bone.index)

        # ---------------------------------

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
            copy_material: Material = material.copy()
            copy_material.index = len(dress_model.materials)

            if 0 <= material.texture_index:
                copy_texture = self.copy_texture(dress_model, model.textures[material.texture_index], model.path)
                copy_material.texture_index = copy_texture.index

            if material.toon_sharing_flg == ToonSharing.INDIVIDUAL and 0 <= material.toon_texture_index:
                copy_texture = self.copy_texture(dress_model, model.textures[material.toon_texture_index], model.path)
                copy_material.toon_texture_index = copy_texture.index

            if material.sphere_mode != SphereMode.INVALID and 0 < material.sphere_texture_index:
                copy_texture = self.copy_texture(dress_model, model.textures[material.sphere_texture_index], model.path)
                copy_material.sphere_texture_index = copy_texture.index

            dress_model.materials.append(copy_material, is_sort=False)
            model_material_map[material.index] = copy_material.index

            for face_index in range(prev_faces_count, prev_faces_count + copy_material.vertices_count // 3):
                faces = []
                for vertex_index in model.faces[face_index].vertices:
                    if vertex_index not in model_vertex_map:
                        copy_vertex: Vertex = model.vertices[vertex_index].copy()
                        copy_vertex.index = -1
                        copy_vertex.deform.indexes = np.vectorize(model_bone_map.get)(copy_vertex.deform.indexes)
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
                copy_texture = self.copy_texture(dress_model, dress.textures[material.texture_index], dress.path)
                copy_material.texture_index = copy_texture.index

            if material.toon_sharing_flg == ToonSharing.INDIVIDUAL and 0 <= material.toon_texture_index:
                copy_texture = self.copy_texture(dress_model, dress.textures[material.toon_texture_index], dress.path)
                copy_material.toon_texture_index = copy_texture.index

            if material.sphere_mode != SphereMode.INVALID and 0 < material.sphere_texture_index:
                copy_texture = self.copy_texture(dress_model, dress.textures[material.sphere_texture_index], dress.path)
                copy_material.sphere_texture_index = copy_texture.index

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
                            mat += dress_matrixes[0, dress.bones[bone_index].name].matrix.vector * bone_weight
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

        PmxWriter(dress_model, output_path).save()

    def copy_texture(self, dest_model: PmxModel, texture: Texture, src_model_path: str) -> Texture:
        copy_texture: Texture = texture.copy()
        copy_texture.index = len(dest_model.textures)
        texture_path = os.path.abspath(os.path.join(os.path.dirname(src_model_path), copy_texture.name))
        if copy_texture.name and os.path.exists(texture_path) and os.path.isfile(texture_path):
            new_texture_path = os.path.join(os.path.dirname(dest_model.path), copy_texture.name)
            os.makedirs(os.path.dirname(new_texture_path), exist_ok=True)
            shutil.copyfile(texture_path, new_texture_path)
        copy_texture.index = len(dest_model.textures)
        dest_model.textures.append(copy_texture, is_sort=False)

        return copy_texture
