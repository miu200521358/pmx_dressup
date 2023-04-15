import os
from typing import Any, Optional

import wx

from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.service.form.base_frame import BaseFrame
from mlib.pmx.pmx_collection import PmxModel
from mlib.utils.file_utils import save_histories
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame
from service.form.panel.config_panel import ConfigPanel
from service.form.panel.file_panel import FilePanel
from service.worker.load_worker import LoadWorker
from service.worker.load_motion_worker import LoadMotionWorker

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
        self.model_motion: Optional[VmdMotion] = None
        self.dress_motion: Optional[VmdMotion] = None

        # 設定タブ
        self.config_panel = ConfigPanel(self, 1)
        self.notebook.AddPage(self.config_panel, __("設定"), False)

        self.worker = LoadWorker(self.file_panel, self.on_result)
        self.motion_worker = LoadMotionWorker(self.file_panel, self.on_motion_result)

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
                if not self.file_panel.model_ctrl.data or not self.file_panel.dress_ctrl.data:
                    # 設定タブにうつった時に読み込む
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.worker.start()
                elif not self.file_panel.motion_ctrl.data:
                    # モーションだけ変わった場合、設定はそのままでモーションだけ変更する
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.motion_worker.start()
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
            self.on_sound()
            return

        data1, data2, data3 = data
        model: PmxModel = data1
        dress: PmxModel = data2
        motion: VmdMotion = data3
        self.file_panel.model_ctrl.data = model
        self.file_panel.dress_ctrl.data = dress
        self.file_panel.motion_ctrl.data = motion

        # モデルとドレスのボーンの縮尺を合わせる
        self.model_motion = motion
        self.dress_motion = motion.copy()

        # 衣装モーションにモーフを適用
        self.set_dress_motion_morphs()

        # 材質の選択肢を入れ替える
        self.config_panel.model_material_ctrl.initialize(model.materials.names)
        self.config_panel.dress_material_ctrl.initialize(dress.materials.names)

        # キーフレを戻す
        self.config_panel.fno = 0

        try:
            self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, self.model_motion)
            self.config_panel.canvas.append_model_set(self.file_panel.dress_ctrl.data, self.dress_motion)
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except:
            logger.critical("モデル描画初期化処理失敗")

        self.on_sound()

    def on_motion_result(self, result: bool, data: Optional[Any], elapsed_time: str):
        self.file_panel.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            self.on_sound()
            return

        motion: VmdMotion = data
        self.file_panel.motion_ctrl.data = motion

        # モデルとドレスのボーンの縮尺を合わせる
        self.model_motion = motion
        self.dress_motion = motion.copy()

        # 既存のモーフを適用
        self.set_model_motion_morphs(self.config_panel.model_material_ctrl.alphas)
        self.set_dress_motion_morphs({}, self.config_panel.dress_material_ctrl.alphas)
        # キーフレを戻す
        self.config_panel.fno = 0

        try:
            self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, self.model_motion)
            self.config_panel.canvas.append_model_set(self.file_panel.dress_ctrl.data, self.dress_motion)
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except:
            logger.critical("モデル描画初期化処理失敗")

        self.on_sound()

    def set_model_motion_morphs(self, material_alphas: dict[str, float] = {}):
        if self.model_motion is None:
            return

        model: PmxModel = self.file_panel.model_ctrl.data

        for material in model.materials:
            mf = VmdMorphFrame(0, f"{material.name}TR")
            mf.ratio = abs(material_alphas.get(material.name, 1.0) - 1)
            self.model_motion.morphs[mf.name].append(mf)

    def set_dress_motion_morphs(self, axis_scale_sets: dict[str, MVector3D] = {}, material_alphas: dict[str, float] = {}):
        if self.dress_motion is None:
            return

        model: PmxModel = self.file_panel.model_ctrl.data
        dress: PmxModel = self.file_panel.dress_ctrl.data

        self.dress_motion.path = "fit motion"

        # ボーンスケールモーフは常に適用
        bmf = VmdMorphFrame(0, "BoneScale")
        bmf.ratio = 1
        self.dress_motion.morphs[bmf.name].append(bmf)

        for material in dress.materials:
            mf = VmdMorphFrame(0, f"{material.name}TR")
            mf.ratio = abs(material_alphas.get(material.name, 1.0) - 1)
            self.dress_motion.morphs[mf.name].append(mf)

        for dress_bone in dress.bones:
            if dress_bone.name in model.bones and dress.bones[dress_bone.parent_index].name in model.bones:
                # スケールをモーフで加味する
                axis_scale: MVector3D = axis_scale_sets.get(dress_bone.name, MVector3D()) + axis_scale_sets.get("ALL", MVector3D())
                xmf = VmdMorphFrame(0, f"{dress_bone.name}SX")
                xmf.ratio = axis_scale.x
                self.dress_motion.morphs[xmf.name].append(xmf)

                ymf = VmdMorphFrame(0, f"{dress_bone.name}SY")
                ymf.ratio = axis_scale.y
                self.dress_motion.morphs[ymf.name].append(ymf)

                zmf = VmdMorphFrame(0, f"{dress_bone.name}SZ")
                zmf.ratio = axis_scale.z
                self.dress_motion.morphs[zmf.name].append(zmf)

    def fit_model_motion(self, bone_alpha: float = 1.0):
        self.config_panel.canvas.model_sets[0].motion = self.model_motion
        self.config_panel.canvas.model_sets[0].bone_alpha = bone_alpha
        self.config_panel.canvas.change_motion(wx.SpinEvent())

    def fit_dress_motion(self, bone_alpha: float = 1.0):
        self.config_panel.canvas.model_sets[1].motion = self.dress_motion
        self.config_panel.canvas.model_sets[1].bone_alpha = bone_alpha
        self.config_panel.canvas.change_motion(wx.SpinEvent())
