import wx
from mlib.form.base_frame import BaseFrame
from form.panel.file_panel import FilePanel
from mlib.base.logger import MLogger
from form.panel.setting_panel import SettingPanel

logger = MLogger(__name__)
_ = logger.get_text


class MainFrame(BaseFrame):
    def __init__(self, app: wx.App, title: str, size: wx.Size, *args, **kw):
        super().__init__(app, title, size, *args, **kw)

        self._initialize_ui()

    def _initialize_ui(self):
        self.file_panel = FilePanel(self, 0)
        self.notebook.AddPage(self.file_panel, _("ファイル"))

        self.setting_panel = SettingPanel(self, 1)
        self.notebook.AddPage(self.setting_panel, _("設定"))
