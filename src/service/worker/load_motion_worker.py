import os
import re
from typing import Optional

import wx

from mlib.base.logger import MLogger
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_panel import BasePanel
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.file_panel import FilePanel

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class LoadMotionWorker(BaseWorker):
    def __init__(self, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.panel
        motion: Optional[VmdMotion] = None

        if file_panel.motion_ctrl.valid() and not file_panel.motion_ctrl.data:
            motion = file_panel.motion_ctrl.reader.read_by_filepath(file_panel.motion_ctrl.path)
        elif file_panel.motion_ctrl.data:
            motion = file_panel.motion_ctrl.data
        else:
            motion = VmdMotion()

        self.result_data = motion

    def output_log(self):
        file_panel: FilePanel = self.panel
        output_log_path = re.sub(r"\.pmx$", ".log", file_panel.output_pmx_ctrl.path)

        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
