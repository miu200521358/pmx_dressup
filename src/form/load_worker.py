import os
from typing import Optional

import wx

from form.panel.file_panel import FilePanel
from mlib.base.logger import MLogger
from mlib.base.math import MQuaternion, MVector3D
from mlib.form.base_panel import BasePanel
from mlib.form.base_worker import BaseWorker
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import BoneMorphOffset, Morph, MorphType, VertexMorphOffset
from mlib.vmd.vmd_collection import VmdMotion

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class LoadWorker(BaseWorker):
    def __init__(self, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.panel
        model: Optional[PmxModel] = None
        dress: Optional[PmxModel] = None
        motion: Optional[VmdMotion] = None

        if not file_panel.model_ctrl.data and file_panel.model_ctrl.valid():
            model = file_panel.model_ctrl.reader.read_by_filepath(file_panel.model_ctrl.path)
        elif file_panel.model_ctrl.data:
            model = file_panel.model_ctrl.data
        else:
            model = PmxModel()

        if not file_panel.dress_ctrl.data and file_panel.dress_ctrl.valid():
            dress = file_panel.dress_ctrl.reader.read_by_filepath(file_panel.dress_ctrl.path)

            # ドレスに拡大縮小モーフを入れる
            logger.info("衣装モデル追加セットアップ：スケールモーフ追加")
            dress = self.create_dress_scale_morphs(model, dress)

        elif file_panel.dress_ctrl.data:
            dress = file_panel.dress_ctrl.data
        else:
            dress = PmxModel()

        if not file_panel.motion_ctrl.data and file_panel.motion_ctrl.valid():
            motion = file_panel.motion_ctrl.reader.read_by_filepath(file_panel.motion_ctrl.path)
        elif file_panel.motion_ctrl.data:
            motion = file_panel.motion_ctrl.data
        else:
            motion = VmdMotion()

        self.result_data = (model, dress, motion)

    def create_dress_scale_morphs(self, model: PmxModel, dress: PmxModel) -> PmxModel:
        # ウェイト頂点の法線に基づいたスケールを取得
        weighted_vertex_scale = dress.get_weighted_vertex_scale()

        # 変形用スケールモーフを追加
        bone_scale_morph = Morph(name="BoneScale")
        bone_scale_morph.morph_type = MorphType.BONE
        bone_scale_offsets: list[BoneMorphOffset] = []

        for bone in dress.bones:
            if 0 <= bone.parent_index and bone.name in model.bones and dress.bones[bone.parent_index].name in model.bones:
                # 親ボーンがある場合、親ボーンとのスケールモーフを追加
                parent_name = dress.bones[bone.parent_index].name
                bone_scale = (model.bones[bone.name].position - model.bones[parent_name].position) - (bone.position - dress.bones[parent_name].position)
                bone_scale_offsets.append(BoneMorphOffset(bone.index, bone_scale, MQuaternion()))

            for axis in ["X", "Y", "Z"]:
                morph = Morph(name=f"{bone.name}{axis}")
                morph.morph_type = MorphType.VERTEX
                offsets: list[VertexMorphOffset] = []
                bone_weighted_vertices: dict[int, MVector3D] = weighted_vertex_scale.get(bone.index, {})
                for vertex_index, scale in bone_weighted_vertices.items():
                    axis_scale = MVector3D()
                    match axis:
                        case "X":
                            axis_scale.x = scale.x
                        case "Y":
                            axis_scale.y = scale.y
                        case "Z":
                            axis_scale.z = scale.z
                    offsets.append(VertexMorphOffset(vertex_index=vertex_index, position_offset=axis_scale))
                morph.offsets = offsets

                dress.morphs.append(morph)

            logger.count(
                "衣装モデル追加セットアップ：スケールモーフ追加",
                index=bone.index,
                total_index_count=len(dress.bones),
                display_block=100,
            )

        bone_scale_morph.offsets = bone_scale_offsets
        dress.morphs.append(bone_scale_morph)

        return dress
