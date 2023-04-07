import os
import wx

from mlib.base.logger import MLogger
from mlib.form.base_frame import BaseFrame
from mlib.form.base_panel import BasePanel
from mlib.pmx.canvas import PmxCanvas

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ConfigPanel(BasePanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw):
        global logger
        logger = MLogger(os.path.basename(__file__))
        global __
        __ = logger.get_text

        super().__init__(frame, tab_idx, *args, **kw)

        self._initialize_ui()
        self._initialize_event()

    def _initialize_ui(self):
        self.config_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.canvas = PmxCanvas(self, 500, 800)
        self.config_sizer.Add(self.canvas, 0, wx.EXPAND | wx.ALL, 0)

        self.btn_sizer = wx.BoxSizer(wx.VERTICAL)

        # キーフレ
        self.btn_sizer.Add(self.canvas.frame_ctrl, 0, wx.ALL, 5)

        # 再生
        self.play_btn = wx.Button(self, wx.ID_ANY, "Play", wx.DefaultPosition, wx.Size(100, 50))
        self.btn_sizer.Add(self.play_btn, 0, wx.ALL, 5)

        self.config_sizer.Add(self.btn_sizer, 0, wx.ALL, 0)
        self.root_sizer.Add(self.config_sizer, 0, wx.ALL, 0)

        self.fit()

    def _initialize_event(self):
        self.play_btn.Bind(wx.EVT_BUTTON, self.on_play)

    def on_play(self, event: wx.Event):
        self.canvas.on_play(event)
        self.play_btn.SetLabelText("Stop" if self.canvas.playing else "Play")
