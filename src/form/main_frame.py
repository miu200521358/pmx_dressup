import os
from typing import Any, Optional

import wx

from form.load_worker import LoadWorker
from form.panel.config_panel import ConfigPanel
from form.panel.file_panel import FilePanel
from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.form.base_frame import BaseFrame
from mlib.pmx.canvas import MotionSet
from mlib.pmx.pmx_collection import PmxModel
from mlib.utils.file_utils import save_histories
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MainFrame(BaseFrame):
    def __init__(self, app: wx.App, title: str, size: wx.Size, *args, **kw):
        super().__init__(
            app,
            history_keys=["model_pmx", "dress_pmx", "motion_vmd"],
            title=title,
            size=size,
        )
        # ファイルタブ
        self.file_panel = FilePanel(self, 0)
        self.notebook.AddPage(self.file_panel, __("ファイル"), False)

        # 設定タブ
        self.config_panel = ConfigPanel(self, 1)
        self.notebook.AddPage(self.config_panel, __("設定"), False)

        self.worker = LoadWorker(self.file_panel, self.on_result)

    def on_change_tab(self, event: wx.Event):
        if self.notebook.GetSelection() == self.config_panel.tab_idx:
            self.notebook.ChangeSelection(self.file_panel.tab_idx)
            if not self.worker.started:
                if not self.file_panel.model_ctrl.valid():
                    logger.warning("人物モデル欄に有効なパスが設定されていない為、タブ遷移を中断します。")
                    return
                if not self.file_panel.dress_ctrl.valid():
                    logger.warning("衣装モデル欄に有効なパスが設定されていない為、タブ遷移を中断します。")
                    return
                if not self.file_panel.model_ctrl.data or not self.file_panel.dress_ctrl.data or not self.file_panel.motion_ctrl.data:
                    # 設定タブにうつった時に読み込む
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.worker.start()
                else:
                    # 既に読み取りが完了していたらそのまま表示
                    self.notebook.ChangeSelection(self.config_panel.tab_idx)

    def save_histories(self):
        self.file_panel.model_ctrl.save_path()
        self.file_panel.dress_ctrl.save_path()
        self.file_panel.motion_ctrl.save_path()

        save_histories(self.histories)

    def on_result(self, result: bool, data: Optional[Any], elapsed_time: str):
        self.file_panel.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            return

        data1, data2, data3 = data
        model: PmxModel = data1
        dress: PmxModel = data2
        motion: VmdMotion = data3
        self.file_panel.model_ctrl.data = model
        self.file_panel.dress_ctrl.data = dress
        self.file_panel.motion_ctrl.data = motion

        # モデルとドレスのボーンの縮尺を合わせる
        dress_motion = self.create_dress_motion()

        try:
            self.config_panel.canvas.set_context()
            self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, motion)
            self.config_panel.canvas.append_model_set(self.file_panel.dress_ctrl.data, dress_motion)
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except:
            logger.critical(__("モデル描画初期化処理失敗"))

    def create_dress_motion(self, axis_scale_sets: dict[str, MVector3D] = {}) -> VmdMotion:
        model: PmxModel = self.file_panel.model_ctrl.data
        dress: PmxModel = self.file_panel.dress_ctrl.data
        motion: VmdMotion = self.file_panel.motion_ctrl.data.copy()

        motion.path = "fit motion"

        # ボーンスケールモーフは常に適用
        bmf = VmdMorphFrame(0, "BoneScale")
        bmf.ratio = 1
        motion.morphs[bmf.name].append(bmf)

        for dress_bone in dress.bones:
            if dress_bone.name in model.bones and dress.bones[dress_bone.parent_index].name in model.bones:
                # スケールをモーフで加味する
                axis_scale: MVector3D = axis_scale_sets.get(dress_bone.name, MVector3D()) + axis_scale_sets.get("ALL", MVector3D())
                xmf = VmdMorphFrame(0, f"{dress_bone.name}X")
                xmf.ratio = axis_scale.x
                motion.morphs[xmf.name].append(xmf)

                ymf = VmdMorphFrame(0, f"{dress_bone.name}Y")
                ymf.ratio = axis_scale.y
                motion.morphs[ymf.name].append(ymf)

                zmf = VmdMorphFrame(0, f"{dress_bone.name}Z")
                zmf.ratio = axis_scale.z
                motion.morphs[zmf.name].append(zmf)

        return motion

    def fit_dress_motion(self, dress_motion: VmdMotion):
        animations: list[MotionSet] = [
            MotionSet(self.config_panel.canvas.model_sets[0].model, VmdMotion(), 0),
            MotionSet(self.config_panel.canvas.model_sets[1].model, dress_motion, 0),
        ]
        self.config_panel.canvas.animations = animations
        self.config_panel.canvas.Refresh()
