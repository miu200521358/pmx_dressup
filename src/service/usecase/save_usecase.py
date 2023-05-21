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
from mlib.pmx.pmx_part import BoneMorphOffset, GroupMorphOffset, MaterialMorphOffset, MorphType, UvMorphOffset
from mlib.pmx.pmx_part import Morph, VertexMorphOffset
from mlib.pmx.pmx_part import RigidBody
from mlib.pmx.pmx_part import Joint

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
        dress_model.model_name = model.name + "(" + dress.name + ")"
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
        dress_original_matrixes = VmdMotion().animate_bone(0, dress)
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
                                dress_model.display_slots.append(DisplaySlot(name=display_slot.name, english_name=display_slot.english_name))
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
                                dress_model.display_slots.append(DisplaySlot(name=display_slot.name, english_name=display_slot.english_name))
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
            if rigidbody.is_system or rigidbody.bone_index not in model_bone_map or model.bones[rigidbody.bone_index].name not in dress_model.bones:
                continue

            model_copy_rigidbody: RigidBody = rigidbody.copy()
            model_copy_rigidbody.index = len(dress_model.rigidbodies)
            model_copy_rigidbody.bone_index = model_bone_map[rigidbody.bone_index]
            model_rigidbody_map[rigidbody.bone_index] = len(dress_model.rigidbodies)
            dress_model.rigidbodies.append(model_copy_rigidbody)

            if not len(dress_model.rigidbodies) % 50:
                logger.info("-- 剛体出力: {s}", s=len(dress_model.rigidbodies))

        for rigidbody in dress.rigidbodies:
            if rigidbody.is_system or rigidbody.bone_index not in dress_bone_map or dress.bones[rigidbody.bone_index].name not in dress_model.bones:
                continue

            dress_copy_rigidbody: RigidBody = rigidbody.copy()
            dress_copy_rigidbody.index = len(dress_model.rigidbodies)
            dress_copy_rigidbody.bone_index = dress_bone_map[rigidbody.bone_index]
            dress_bone_name = dress.bones[rigidbody.bone_index].name

            if rigidbody.name in model.rigidbodies:
                dress_copy_rigidbody.shape_size = model.rigidbodies[rigidbody.name].shape_size.copy()
                dress_copy_rigidbody.shape_position = model.rigidbodies[rigidbody.name].shape_position.copy()
                dress_copy_rigidbody.shape_rotation = model.rigidbodies[rigidbody.name].shape_rotation.copy()
            else:
                # ボーンと剛体の位置関係から剛体位置を求め直す
                rigidbody_local_position = dress_original_matrixes[0, dress_bone_name].matrix.inverse() * rigidbody.shape_position
                rigidbody_copy_position = dress_matrixes[0, dress_bone_name].matrix * rigidbody_local_position
                rigidbody_copy_scale = MVector3D(
                    dress_matrixes[0, dress_bone_name].matrix[0, 0],
                    dress_matrixes[0, dress_bone_name].matrix[1, 1],
                    dress_matrixes[0, dress_bone_name].matrix[2, 2],
                )

                dress_copy_rigidbody.shape_position = rigidbody_copy_position
                dress_copy_rigidbody.shape_size *= rigidbody_copy_scale
            dress_rigidbody_map[rigidbody.bone_index] = len(dress_model.rigidbodies)
            dress_model.rigidbodies.append(dress_copy_rigidbody)

            if not len(dress_model.rigidbodies) % 50:
                logger.info("-- 剛体出力: {s}", s=len(dress_model.rigidbodies))

        # ---------------------------------

        logger.info("ジョイント出力", decoration=MLogger.Decoration.LINE)

        for joint in model.joints:
            if joint.is_system:
                continue
            bone_a_name = model.bones[model.rigidbodies[joint.rigidbody_index_a].bone_index].name
            bone_b_name = model.bones[model.rigidbodies[joint.rigidbody_index_b].bone_index].name
            rigidbody_a = [rigidbody for rigidbody in dress_model.rigidbodies if dress_model.bones[rigidbody.bone_index].name == bone_a_name]
            rigidbody_b = [rigidbody for rigidbody in dress_model.rigidbodies if dress_model.bones[rigidbody.bone_index].name == bone_b_name]
            if not (rigidbody_a and rigidbody_b):
                continue

            model_copy_joint: Joint = joint.copy()
            model_copy_joint.index = len(dress_model.joints)
            model_copy_joint.rigidbody_index_a = rigidbody_a[0].index
            model_copy_joint.rigidbody_index_b = rigidbody_b[0].index
            dress_model.joints.append(model_copy_joint)

            if not len(dress_model.joints) % 50:
                logger.info("-- ジョイント出力: {s}", s=len(dress_model.joints))

        for joint in dress.joints:
            if joint.is_system:
                continue
            bone_a_name = dress.bones[dress.rigidbodies[joint.rigidbody_index_a].bone_index].name
            bone_b_name = dress.bones[dress.rigidbodies[joint.rigidbody_index_b].bone_index].name
            rigidbody_a = [rigidbody for rigidbody in dress_model.rigidbodies if dress_model.bones[rigidbody.bone_index].name == bone_a_name]
            rigidbody_b = [rigidbody for rigidbody in dress_model.rigidbodies if dress_model.bones[rigidbody.bone_index].name == bone_b_name]
            if not (rigidbody_a and rigidbody_b):
                continue

            joint_a_local_position = dress_original_matrixes[0, bone_a_name].matrix.inverse() * joint.position
            joint_b_local_position = dress_original_matrixes[0, bone_b_name].matrix.inverse() * joint.position
            joint_a_copy_position = dress_matrixes[0, bone_a_name].matrix * joint_a_local_position
            joint_b_copy_position = dress_matrixes[0, bone_b_name].matrix * joint_b_local_position

            dress_copy_joint: Joint = joint.copy()
            dress_copy_joint.index = len(dress_model.joints)
            dress_copy_joint.rigidbody_index_a = rigidbody_a[0].index
            dress_copy_joint.rigidbody_index_b = rigidbody_b[0].index
            dress_copy_joint.position = (joint_a_copy_position + joint_b_copy_position) / 2
            dress_model.joints.append(dress_copy_joint)

            if not len(dress_model.joints) % 50:
                logger.info("-- ジョイント出力: {s}", s=len(dress_model.joints))

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

    def copy_morph(
        self,
        morph: Morph,
        model_bone_map: dict[int, int],
        model_vertex_map: dict[int, int],
        model_material_map: dict[int, int],
        model_morph_map: dict[int, int],
    ):
        copy_morph = Morph(name=morph.name, english_name=morph.english_name)
        if morph.morph_type == MorphType.VERTEX:
            copy_morph.panel = morph.panel
            copy_morph.morph_type = MorphType.VERTEX
            for offset in morph.offsets:
                vertex_offset: VertexMorphOffset = offset
                if vertex_offset.vertex_index in model_vertex_map:
                    copy_morph.offsets.append(VertexMorphOffset(model_vertex_map[vertex_offset.vertex_index], vertex_offset.position_offset.copy()))
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
