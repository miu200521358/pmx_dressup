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
from service.usecase.dress_bone_setting import DRESS_BONE_FITTING_NAME, DRESS_VERTEX_FITTING_NAME
from service.worker.load_motion_worker import LoadMotionWorker
from service.worker.load_worker import LoadWorker
from service.worker.save_worker import SaveWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MainFrame(BaseFrame):
    def __init__(self, app: wx.App, title: str, size: wx.Size, *args, **kw) -> None:
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

        self.load_worker = LoadWorker(self, self.on_result)
        self.motion_load_worker = LoadMotionWorker(self, self.on_motion_result)
        self.save_worker = SaveWorker(self, self.on_save_result)

        self.file_panel.exec_btn_ctrl.exec_worker = self.save_worker

    def on_change_tab(self, event: wx.Event) -> None:
        if self.notebook.GetSelection() == self.config_panel.tab_idx:
            self.notebook.ChangeSelection(self.file_panel.tab_idx)
            if not self.load_worker.started:
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
                    self.load_worker.start()
                elif self.file_panel.motion_ctrl.path and not self.file_panel.motion_ctrl.data:
                    self.file_panel.exec_btn_ctrl.Enable(False)
                    # モーションだけ変わった場合、設定はそのままでモーションだけ変更する
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.file_panel.Enable(False)
                    self.motion_load_worker.start()
                else:
                    # 既に読み取りが完了していたらそのまま表示
                    self.notebook.ChangeSelection(self.config_panel.tab_idx)

    def save_histories(self) -> None:
        self.file_panel.model_ctrl.save_path()
        self.file_panel.dress_ctrl.save_path()
        self.file_panel.motion_ctrl.save_path()

        save_histories(self.histories)

    def on_result(
        self,
        result: bool,
        data: Optional[tuple[PmxModel, PmxModel, PmxModel, PmxModel, VmdMotion, list[str], list[list[int]]]],
        elapsed_time: str,
    ) -> None:
        self.file_panel.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            self.file_panel.Enable(True)
            self.file_panel.exec_btn_ctrl.Enable(False)
            self.on_sound()
            return

        logger.info("描画準備開始", decoration=MLogger.Decoration.BOX)

        original_model, model, original_dress, dress, motion, individual_morph_names, individual_target_bone_indexes = data

        self.file_panel.model_ctrl.original_data = original_model
        self.file_panel.model_ctrl.data = model
        self.file_panel.dress_ctrl.original_data = original_dress
        self.file_panel.dress_ctrl.data = dress
        self.file_panel.motion_ctrl.set_data(motion)
        self.file_panel.exec_btn_ctrl.Enable(True)

        if not (self.file_panel.model_ctrl.data and self.file_panel.dress_ctrl.data and self.file_panel.motion_ctrl.data):
            return

        # モデルとドレスのボーンの縮尺を合わせる
        self.model_motion = motion
        self.dress_motion = motion.copy()

        # 衣装モーションにモーフを適用
        self.set_dress_motion_morphs()

        # 材質名リストを保持する
        all_material_names = (
            [""]
            + [__("人物") + ":" + material_name for material_name in model.materials.names]
            + [__("衣装") + ":" + material_name for material_name in dress.materials.names]
        )

        # 材質の選択肢を入れ替える
        self.config_panel.model_material_ctrl.initialize(model.materials.names, all_material_names)
        self.config_panel.dress_material_ctrl.initialize(dress.materials.names, all_material_names)
        # ボーン調整の選択肢を入れ替える
        self.config_panel.dress_bone_ctrl.initialize(individual_morph_names, individual_target_bone_indexes)

        # キーフレを戻す
        self.config_panel.fno = 0

        try:
            logger.info("人物モデル描画準備")
            self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, self.model_motion, bone_alpha=0.5)
            logger.info("衣装モデル描画準備")
            self.config_panel.canvas.append_model_set(self.file_panel.dress_ctrl.data, self.dress_motion, bone_alpha=0.5)
            # ボーンハイライト
            self.config_panel.canvas.animations[1].selected_bone_indexes = self.config_panel.dress_bone_ctrl.individual_target_bone_indexes[
                0
            ]
            logger.info("モデル描画")
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except:
            logger.critical("モデル描画初期化処理失敗")

        self.file_panel.Enable(True)
        self.on_sound()

    def on_motion_result(self, result: bool, data: Optional[VmdMotion], elapsed_time: str) -> None:
        self.file_panel.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            self.file_panel.Enable(True)
            self.file_panel.exec_btn_ctrl.Enable(False)
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
            # ボーンハイライト
            self.config_panel.canvas.animations[1].selected_bone_indexes = self.config_panel.dress_bone_ctrl.individual_target_bone_indexes[
                0
            ]
            logger.info("モデル描画")
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except:
            logger.critical("モデル描画初期化処理失敗")

        self.file_panel.Enable(True)
        self.on_sound()

    def on_exec(self) -> None:
        self.save_worker.start()

    def on_save_result(self, result: bool, data: Optional[Any], elapsed_time: str) -> None:
        self.file_panel.Enable(True)
        self.on_sound()

    def set_model_motion_morphs(self, material_alphas: dict[str, float] = {}) -> None:
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

        # self.file_panel.create_output_path()

    def clear_model_opacity(self):
        if self.model_motion and self.model_motion.morphs:
            del self.model_motion.morphs["全材質TR"]

    def set_dress_motion_morphs(
        self,
        material_alphas: dict[str, float] = {},
        bone_scales: dict[str, MVector3D] = {},
        bone_degrees: dict[str, MVector3D] = {},
        bone_positions: dict[str, MVector3D] = {},
    ) -> None:
        if self.dress_motion is None:
            return

        # model: PmxModel = self.file_panel.model_ctrl.data
        dress: PmxModel = self.file_panel.dress_ctrl.data

        self.dress_motion.path = "fit motion"

        # フィッティングモーフは常に適用
        bmf = VmdMorphFrame(0, DRESS_BONE_FITTING_NAME)
        bmf.ratio = 1
        self.dress_motion.morphs[bmf.name].append(bmf)

        vmf = VmdMorphFrame(0, DRESS_VERTEX_FITTING_NAME)
        vmf.ratio = 1
        self.dress_motion.morphs[vmf.name].append(vmf)

        for material in dress.materials:
            mf = VmdMorphFrame(0, f"{material.name}TR")
            mf.ratio = abs(material_alphas.get(material.name, 1.0) - 1)
            self.dress_motion.morphs[mf.name].append(mf)

        mf = VmdMorphFrame(0, "全材質TR")
        mf.ratio = abs(material_alphas.get(__("全材質"), 1.0) - 1)
        self.dress_motion.morphs[mf.name].append(mf)

        for morph_name, scale, degree, position in zip(
            bone_scales.keys(), bone_scales.values(), bone_degrees.values(), bone_positions.values()
        ):
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
                mf = VmdMorphFrame(0, f"調整:{morph_name}:{axis_name}")
                mf.ratio = ratio - origin
                self.dress_motion.morphs[mf.name].append(mf)

            # # 再フィットは倍率は常に1（実際に与える値の方で調整する）
            # mf = VmdMorphFrame(0, f"調整:{__(bone_type_name)}:Refit")
            # mf.ratio = 1
            # self.dress_motion.morphs[mf.name].append(mf)

        # self.file_panel.create_output_path()

    def fit_model_motion(self, bone_alpha: float = 1.0, is_bone_deform: bool = True) -> None:
        self.config_panel.canvas.model_sets[0].motion = self.model_motion
        self.config_panel.canvas.model_sets[0].bone_alpha = bone_alpha
        self.config_panel.canvas.change_motion(wx.SpinEvent(), is_bone_deform, 0)

    def fit_dress_motion(self, bone_alpha: float = 1.0, is_bone_deform: bool = True) -> None:
        self.config_panel.canvas.model_sets[1].motion = self.dress_motion
        self.config_panel.canvas.model_sets[1].bone_alpha = bone_alpha
        self.config_panel.canvas.change_motion(wx.SpinEvent(), is_bone_deform, 1)

    def change_bone(self, selected_bone_indexes: list[int]) -> None:
        self.config_panel.canvas.animations[1].selected_bone_indexes = selected_bone_indexes
        self.config_panel.canvas.Refresh()

    def show_bone_weight(self, is_show_bone_weight: bool) -> None:
        self.config_panel.canvas.animations[1].is_show_bone_weight = is_show_bone_weight
        self.config_panel.canvas.Refresh()
