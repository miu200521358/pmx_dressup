import wx

from form.panel.file_panel import FilePanel
from mlib.form.base_panel import BasePanel
from mlib.form.base_worker import BaseWorker


class LoadWorker(BaseWorker):
    def __init__(self, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.panel

        self.result_data = (
            file_panel.pmx_reader.read_by_filepath(file_panel.model_ctrl.path),
            file_panel.pmx_reader.read_by_filepath(file_panel.dress_ctrl.path),
            file_panel.vmd_reader.read_by_filepath(file_panel.motion_ctrl.path),
        )
