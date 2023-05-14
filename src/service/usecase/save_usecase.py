import os
import shutil

import numpy as np

from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import (
    Bone,
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

        for bone_type_name, scale, degree, position in zip(dress_scales.keys(), dress_scales.values(), dress_degrees.values(), dress_positions.values()):
            for ratio, axis_name in (
                (scale.x, "SX"),
                (scale.y, "SY"),
                (scale.z, "SZ"),
                (degree.x, "RX"),
                (degree.y, "RY"),
                (degree.z, "RZ"),
                (position.x, "MX"),
                (position.y, "MY"),
                (position.z, "MZ"),
            ):
                mf = VmdMorphFrame(0, f"{__('調整')}:{__(bone_type_name)}:{axis_name}")
                mf.ratio = ratio
                motion.morphs[mf.name].append(mf)

        # 変形結果
        (bone_matrixes, vertex_morph_poses, uv_morph_poses, uv1_morph_poses, material_morphs) = motion.animate(0, dress, is_gl=False)

        # ---------------------------------

        dress_model = PmxModel(output_path)
        dress_model.comment = model.comment + "\n------------------\n" + dress.comment
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

            for dress_bone in dress.bones.writable():
                if 0 <= dress_bone.tail_index and dress_bone.name not in model.bones and dress.bones[dress_bone.tail_index].name == bone.name:
                    # 衣装だけのボーンが表示先が人物のボーンに繋がってる場合、その前に追加しておく
                    copy_bone = dress_bone.copy()
                    copy_bone.index = len(dress_model.bones.writable())
                    bone_map[copy_bone.index] = {
                        "parent": [dress.bones[dress_bone.parent_index].name],
                        "tail": [dress.bones[dress_bone.tail_index].name],
                        "effect": [dress.bones[dress_bone.effect_index].name],
                        "ik_target": [dress.bones[dress_bone.ik.bone_index].name if dress_bone.ik else Bone.SYSTEM_ROOT_NAME],
                        "ik_link": [dress.bones[link.bone_index].name for link in dress_bone.ik.links] if dress_bone.ik else [],
                    }
                    dress_model.bones.append(copy_bone, is_sort=False)
                    dress_bone_map[bone.index] = copy_bone.index

                    if not len(dress_model.bones) % 100:
                        logger.info("-- ボーン出力: {s}", s=len(dress_model.bones))

            copy_bone = bone.copy()
            copy_bone.index = len(dress_model.bones.writable())
            bone_map[copy_bone.index] = {
                "parent": [model.bones[bone.parent_index].name],
                "tail": [model.bones[bone.tail_index].name],
                "effect": [model.bones[bone.effect_index].name],
                "ik_target": [model.bones[bone.ik.bone_index].name if bone.ik else Bone.SYSTEM_ROOT_NAME],
                "ik_link": [model.bones[link.bone_index].name for link in bone.ik.links] if bone.ik else [],
            }
            dress_model.bones.append(copy_bone, is_sort=False)
            model_bone_map[bone.index] = copy_bone.index

            if not len(dress_model.bones) % 100:
                logger.info("-- ボーン出力: {s}", s=len(dress_model.bones))

        for bone in dress.bones.writable():
            if bone.name in dress_model.bones:
                # 既に登録済みのボーンは追加しない
                dress_bone_map[bone.index] = dress_model.bones[bone.name].index
                continue
            copy_bone = bone.copy()
            copy_bone.index = len(dress_model.bones.writable())
            bone_map[copy_bone.index] = {
                "parent": [dress.bones[bone.parent_index].name],
                "tail": [dress.bones[bone.tail_index].name],
                "effect": [dress.bones[bone.effect_index].name],
                "ik_target": [dress.bones[bone.ik.bone_index].name if bone.ik else Bone.SYSTEM_ROOT_NAME],
                "ik_link": [dress.bones[link.bone_index].name for link in bone.ik.links] if bone.ik else [],
            }
            dress_model.bones.append(copy_bone, is_sort=False)
            dress_bone_map[bone.index] = copy_bone.index

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

            if not bone.index % 100:
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
