import os
from typing import Any, Optional

import wx

from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.base_frame import BaseFrame
from mlib.utils.file_utils import save_histories
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame
from service.form.panel.config_panel import ConfigPanel
from service.form.panel.file_panel import FilePanel
from service.worker.load_motion_worker import LoadMotionWorker
from service.worker.load_worker import LoadWorker
from service.worker.save_worker import SaveWorker

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
        self.save_worker = SaveWorker(self.file_panel, self.on_save_result)

    def on_change_tab(self, event: wx.Event):
        if self.notebook.GetSelection() == self.config_panel.tab_idx:
            self.notebook.ChangeSelection(self.file_panel.tab_idx)
            if not self.worker.started:
                if not self.file_panel.model_ctrl.valid():
                    self.file_panel.exec_btn_ctrl.Enable(False)
                    logger.warning("人物モデル欄に有効なパスが設定されていない為、タブ遷移を中断します。")
                    return
                if not self.file_panel.dress_ctrl.valid():
                    self.file_panel.exec_btn_ctrl.Enable(False)
                    logger.warning("衣装モデル欄に有効なパスが設定されていない為、タブ遷移を中断します。")
                    return
                if not self.file_panel.model_ctrl.data or not self.file_panel.dress_ctrl.data:
                    # 設定タブにうつった時に読み込む
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.file_panel.Enable(False)
                    self.worker.start()
                elif self.file_panel.motion_ctrl.path and not self.file_panel.motion_ctrl.data:
                    self.file_panel.exec_btn_ctrl.Enable(False)
                    # モーションだけ変わった場合、設定はそのままでモーションだけ変更する
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.file_panel.Enable(False)
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

        logger.info("描画準備開始", decoration=MLogger.Decoration.BOX)

        data1, data2, data3 = data
        model: PmxModel = data1
        dress: PmxModel = data2
        motion: VmdMotion = data3
        self.file_panel.model_ctrl.set_data(model)
        self.file_panel.dress_ctrl.set_data(dress)
        self.file_panel.motion_ctrl.set_data(motion)
        self.file_panel.exec_btn_ctrl.Enable(True)

        if not (self.file_panel.model_ctrl.data and self.file_panel.dress_ctrl.data and self.file_panel.motion_ctrl.data):
            return

        # モデルとドレスのボーンの縮尺を合わせる
        self.model_motion = motion
        self.dress_motion = motion.copy()

        # 衣装モーションにモーフを適用
        self.set_dress_motion_morphs()

        # 材質の選択肢を入れ替える
        self.config_panel.model_material_ctrl.initialize(model.materials.names)
        self.config_panel.dress_material_ctrl.initialize(dress.materials.names)
        # ボーン調整の選択肢を入れ替える
        self.config_panel.dress_bone_ctrl.initialize()

        # キーフレを戻す
        self.config_panel.fno = 0

        try:
            logger.info("人物モデル描画準備")
            self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, self.model_motion, bone_alpha=0.5)
            logger.info("衣装モデル描画準備")
            self.config_panel.canvas.append_model_set(self.file_panel.dress_ctrl.data, self.dress_motion, bone_alpha=0.5)
            logger.info("モデル描画")
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except:
            logger.critical("モデル描画初期化処理失敗")

        self.file_panel.Enable(True)
        self.on_sound()

    def on_motion_result(self, result: bool, data: Optional[Any], elapsed_time: str):
        self.file_panel.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            self.on_sound()
            return

        motion: VmdMotion = data
        self.file_panel.motion_ctrl.data = motion
        self.file_panel.exec_btn_ctrl.Enable(True)

        # モデルとドレスのボーンの縮尺を合わせる
        self.model_motion = motion
        self.dress_motion = motion.copy()

        # 既存のモーフを適用
        self.set_model_motion_morphs(self.config_panel.model_material_ctrl.alphas)
        self.set_dress_motion_morphs(
            self.config_panel.dress_material_ctrl.alphas,
            self.config_panel.dress_bone_ctrl.scales,
            self.config_panel.dress_bone_ctrl.degrees,
            self.config_panel.dress_bone_ctrl.positions,
        )
        # キーフレを戻す
        self.config_panel.fno = 0

        try:
            logger.info("人物モデル描画準備")
            self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, self.model_motion, bone_alpha=0.5)
            logger.info("衣装モデル描画準備")
            self.config_panel.canvas.append_model_set(self.file_panel.dress_ctrl.data, self.dress_motion, bone_alpha=0.5)
            logger.info("モデル描画")
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except:
            logger.critical("モデル描画初期化処理失敗")

        self.file_panel.Enable(True)
        self.on_sound()

    def on_exec(self):
        self.save_worker.start()

    def on_save_result(self, result: bool, data: Optional[Any], elapsed_time: str):
        self.on_sound()

    def set_model_motion_morphs(self, material_alphas: dict[str, float] = {}):
        if self.model_motion is None:
            return

        model: PmxModel = self.file_panel.model_ctrl.data

        for material in model.materials:
            mf = VmdMorphFrame(0, f"{material.name}TR")
            mf.ratio = abs(material_alphas.get(material.name, 1.0) - 1)
            self.model_motion.morphs[mf.name].append(mf)

        mf = VmdMorphFrame(0, "全材質TR")
        mf.ratio = abs(material_alphas.get(__("全材質"), 1.0) - 1)
        self.model_motion.morphs[mf.name].append(mf)

    def set_dress_motion_morphs(
        self,
        material_alphas: dict[str, float] = {},
        bone_scales: dict[str, MVector3D] = {},
        bone_degrees: dict[str, MVector3D] = {},
        bone_positions: dict[str, MVector3D] = {},
    ):
        if self.dress_motion is None:
            return

        # model: PmxModel = self.file_panel.model_ctrl.data
        dress: PmxModel = self.file_panel.dress_ctrl.data

        self.dress_motion.path = "fit motion"

        # フィッティングモーフは常に適用
        bmf = VmdMorphFrame(0, "BoneFitting")
        bmf.ratio = 1
        self.dress_motion.morphs[bmf.name].append(bmf)

        for material in dress.materials:
            mf = VmdMorphFrame(0, f"{material.name}TR")
            mf.ratio = abs(material_alphas.get(material.name, 1.0) - 1)
            self.dress_motion.morphs[mf.name].append(mf)

        mf = VmdMorphFrame(0, "全材質TR")
        mf.ratio = abs(material_alphas.get(__("全材質"), 1.0) - 1)
        self.dress_motion.morphs[mf.name].append(mf)

        for bone_type_name, scale, degree, position in zip(bone_scales.keys(), bone_scales.values(), bone_degrees.values(), bone_positions.values()):
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
                self.dress_motion.morphs[mf.name].append(mf)

    def fit_model_motion(self, bone_alpha: float = 1.0, is_bone_deform: bool = True):
        self.config_panel.canvas.model_sets[0].motion = self.model_motion
        self.config_panel.canvas.model_sets[0].bone_alpha = bone_alpha
        self.config_panel.canvas.change_motion(wx.SpinEvent(), is_bone_deform)

    def fit_dress_motion(self, bone_alpha: float = 1.0, is_bone_deform: bool = True):
        self.config_panel.canvas.model_sets[1].motion = self.dress_motion
        self.config_panel.canvas.model_sets[1].bone_alpha = bone_alpha
        self.config_panel.canvas.change_motion(wx.SpinEvent(), is_bone_deform)
