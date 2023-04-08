import os
from datetime import datetime

import wx

from mlib.base.logger import MLogger
from mlib.form.base_frame import BaseFrame
from mlib.form.base_panel import BasePanel
from mlib.form.parts.console_ctrl import ConsoleCtrl
from mlib.form.parts.file_ctrl import MFilePickerCtrl
from mlib.pmx.pmx_reader import PmxReader
from mlib.utils.file_utils import separate_path
from mlib.vmd.vmd_reader import VmdReader

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class FilePanel(BasePanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, *args, **kw)

        self.pmx_reader = PmxReader()
        self.vmd_reader = VmdReader()

        self._initialize_ui()

    def _initialize_ui(self):
        self.model_ctrl = MFilePickerCtrl(
            self.frame,
            self,
            self.pmx_reader,
            key="model_pmx",
            title="表示モデル",
            is_show_name=True,
            name_spacer=20,
            is_save=False,
            tooltip="PMXモデル",
            event=self.on_change_model_pmx,
        )
        self.model_ctrl.set_parent_sizer(self.root_sizer)

        self.dress_ctrl = MFilePickerCtrl(
            self.frame,
            self,
            self.pmx_reader,
            key="dress_pmx",
            title="衣装モデル",
            is_show_name=True,
            name_spacer=20,
            is_save=False,
            tooltip="PMX衣装モデル",
            event=self.on_change_dress_pmx,
        )
        self.dress_ctrl.set_parent_sizer(self.root_sizer)

        self.motion_ctrl = MFilePickerCtrl(
            self.frame,
            self,
            self.vmd_reader,
            key="motion_vmd",
            title="表示モーション",
            is_show_name=True,
            name_spacer=20,
            is_save=False,
            tooltip="VMDモーションデータ",
            event=self.on_change_motion,
        )
        self.motion_ctrl.set_parent_sizer(self.root_sizer)

        self.output_pmx_ctrl = MFilePickerCtrl(
            self.frame,
            self,
            self.pmx_reader,
            title="出力先",
            is_show_name=False,
            is_save=True,
            tooltip="実際は動いてないよ",
        )
        self.output_pmx_ctrl.set_parent_sizer(self.root_sizer)

        self.console_ctrl = ConsoleCtrl(self.frame, self, rows=300)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

        self.root_sizer.Add(wx.StaticLine(self, wx.ID_ANY), wx.GROW)
        self.fit()

    def on_change_model_pmx(self, event: wx.Event):
        if self.model_ctrl.read_name():
            self.model_ctrl.read_digest()
            dir_path, file_name, file_ext = separate_path(self.model_ctrl.path)
            model_path = os.path.join(dir_path, f"{file_name}_{datetime.now():%Y%m%d_%H%M%S}{file_ext}")
            self.output_pmx_ctrl.path = model_path

    def on_change_dress_pmx(self, event: wx.Event):
        if self.dress_ctrl.read_name():
            self.dress_ctrl.read_digest()

    def on_change_motion(self, event: wx.Event):
        if self.motion_ctrl.read_name():
            self.motion_ctrl.read_digest()
