import os
from datetime import datetime

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.console_ctrl import ConsoleCtrl
from mlib.service.form.widgets.file_ctrl import MPmxFilePickerCtrl, MVmdFilePickerCtrl
from mlib.utils.file_utils import separate_path

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class FilePanel(BasePanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, *args, **kw)

        self._initialize_ui()

    def _initialize_ui(self):
        self.model_ctrl = MPmxFilePickerCtrl(
            self.frame,
            self,
            key="model_pmx",
            title="人物モデル",
            is_show_name=True,
            name_spacer=20,
            is_save=False,
            tooltip="お着替えさせたい対象の人物モデルを指定してください。",
            file_change_event=self.on_change_model_pmx,
        )
        self.model_ctrl.set_parent_sizer(self.root_sizer)

        self.dress_ctrl = MPmxFilePickerCtrl(
            self.frame,
            self,
            key="dress_pmx",
            title="衣装モデル",
            is_show_name=True,
            name_spacer=20,
            is_save=False,
            tooltip="お着替えしたい衣装モデルを指定してください。",
            file_change_event=self.on_change_dress_pmx,
        )
        self.dress_ctrl.set_parent_sizer(self.root_sizer)

        self.motion_ctrl = MVmdFilePickerCtrl(
            self.frame,
            self,
            key="motion_vmd",
            title="表示モーション",
            is_show_name=True,
            name_spacer=20,
            is_save=False,
            tooltip="任意でVMDモーションデータを指定する事ができます。\n空欄の場合、人物と衣装は初期状態で表示します。",
            file_change_event=self.on_change_motion,
        )
        self.motion_ctrl.set_parent_sizer(self.root_sizer)

        self.output_pmx_ctrl = MPmxFilePickerCtrl(
            self.frame,
            self,
            title="お着替え後モデル出力先",
            is_show_name=False,
            is_save=True,
            tooltip="お着替え後のモデルの出力ファイルパスです。\n任意の値に変更可能です。",
        )
        self.output_pmx_ctrl.set_parent_sizer(self.root_sizer)

        self.console_ctrl = ConsoleCtrl(self.frame, self, rows=300)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

        self.root_sizer.Add(wx.StaticLine(self, wx.ID_ANY), wx.GROW)
        self.fit()

    def on_change_model_pmx(self, event: wx.Event):
        self.model_ctrl.unwrap()
        if self.model_ctrl.read_name():
            self.model_ctrl.read_digest()
            self.create_output_path()

    def on_change_dress_pmx(self, event: wx.Event):
        self.dress_ctrl.unwrap()
        if self.dress_ctrl.read_name():
            self.dress_ctrl.read_digest()
            self.create_output_path()

    def on_change_motion(self, event: wx.Event):
        self.motion_ctrl.unwrap()
        if self.motion_ctrl.read_name():
            self.motion_ctrl.read_digest()

    def create_output_path(self):
        if self.model_ctrl.valid() and self.dress_ctrl.valid():
            model_dir_path, model_file_name, model_file_ext = separate_path(self.model_ctrl.path)
            dress_dir_path, dress_file_name, dress_file_ext = separate_path(self.dress_ctrl.path)
            self.output_pmx_ctrl.path = os.path.join(
                model_dir_path, dress_file_name, f"{model_file_name}_{dress_file_name}_{datetime.now():%Y%m%d_%H%M%S}{model_file_ext}"
            )

    def Enable(self, enable: bool):
        self.model_ctrl.Enable(enable)
        self.dress_ctrl.Enable(enable)
        self.motion_ctrl.Enable(enable)
        self.output_pmx_ctrl.Enable(enable)
