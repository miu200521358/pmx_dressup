import os
from typing import Optional

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from mlib.service.base_worker import BaseWorker
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
