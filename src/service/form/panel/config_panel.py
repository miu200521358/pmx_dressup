import os

import wx

from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.pmx.canvas import CanvasPanel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl
from service.form.widgets.axis_ctrl_set import AxisCtrlSet
from service.form.widgets.material_ctrl_set import MaterialCtrlSet

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ConfigPanel(CanvasPanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, 630, 800, *args, **kw)

        self._initialize_ui()
        self._initialize_event()

    def _initialize_ui(self):
        self.config_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # 左にビューワー
        self.config_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        # --------------
        # 右に設定
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

        self.play_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.frame_title_ctrl = wx.StaticText(self, wx.ID_ANY, __("モーション"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.frame_title_ctrl.SetToolTip(__("モーションを指定している場合、任意のキーフレの結果の表示や再生ができます"))
        self.play_sizer.Add(self.frame_title_ctrl, 0, wx.ALL, 3)

        self.frame_ctrl = WheelSpinCtrl(self, initial=0, min=0, max=10000, size=wx.Size(70, -1), change_event=self.on_frame_change)
        self.frame_title_ctrl.SetToolTip(__("モーションを指定している場合、任意のキーフレの結果を表示することができます"))
        self.play_sizer.Add(self.frame_ctrl, 0, wx.ALL, 3)

        self.play_ctrl = wx.Button(self, wx.ID_ANY, "Play", wx.DefaultPosition, wx.Size(80, -1))
        self.play_ctrl.SetToolTip(__("モーションを指定している場合、再生することができます"))
        self.play_sizer.Add(self.play_ctrl, 0, wx.ALL, 3)

        self.header_sizer.Add(self.play_sizer, 0, wx.ALL, 3)
        self.right_sizer.Add(self.play_sizer, 0, wx.ALL, 0)

        # --------------

        self.scrolled_window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.ALWAYS_SHOW_SB,
        )
        self.scrolled_window.SetScrollRate(5, 5)

        self.window_sizer = wx.BoxSizer(wx.VERTICAL)

        # --------------
        # 材質表示

        self.material_sizer = wx.StaticBoxSizer(wx.StaticBox(self.scrolled_window, wx.ID_ANY, __("材質透過度")), orient=wx.VERTICAL)

        self.model_material_ctrl = MaterialCtrlSet(self, self.scrolled_window, self.material_sizer, "人物")
        self.dress_material_ctrl = MaterialCtrlSet(self, self.scrolled_window, self.material_sizer, "衣装")

        self.window_sizer.Add(self.material_sizer, 0, wx.ALL, 3)

        # --------------
        # 追加縮尺

        self.scale_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scale_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("追加縮尺"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.scale_title_ctrl.SetToolTip(__("全体やボーンごとに追加でどの程度伸縮させるかを、XYZ別に設定することができます"))
        self.scale_sizer.Add(self.scale_title_ctrl, 0, wx.ALL, 3)

        self.grid_sizer = wx.FlexGridSizer(rows=1, cols=7, vgap=0, hgap=0)

        # 全体
        self.all_axis_set = AxisCtrlSet(self, self.scrolled_window, self.grid_sizer, "全体")

        # 衣装ボーン別

        self.scale_sizer.Add(self.grid_sizer, 0, wx.ALL, 3)
        self.window_sizer.Add(self.scale_sizer, 0, wx.ALL, 3)

        # --------------

        self.scrolled_window.SetSizer(self.window_sizer)
        self.right_sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

        self.config_sizer.Add(self.right_sizer, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 0)
        self.root_sizer.Add(self.config_sizer, 0, wx.ALL, 0)

        self.fit()

    def fit(self):
        self.scrolled_window.Layout()
        self.SetSizer(self.root_sizer)
        self.Layout()

    def _initialize_event(self):
        self.play_ctrl.Bind(wx.EVT_BUTTON, self.on_play)
        # self.model_material_choice_ctrl.Bind(wx.EVT_LISTBOX, self.on_change)
        # self.dress_material_choice_ctrl.Bind(wx.EVT_LISTBOX, self.on_change)

    def on_play(self, event: wx.Event):
        self.canvas.on_play(event)
        self.play_ctrl.SetLabelText("Stop" if self.canvas.playing else "Play")

    @property
    def fno(self):
        return self.frame_ctrl.GetValue()

    @fno.setter
    def fno(self, v: int):
        self.frame_ctrl.SetValue(v)

    def stop_play(self):
        self.play_ctrl.SetLabelText(__("再生"))
        self.enable(True)

    def start_play(self):
        self.play_ctrl.SetLabelText(__("停止"))
        self.enable(False)

    def enable(self, enable: bool):
        self.model_material_ctrl.enable(enable)
        self.dress_material_ctrl.enable(enable)

    def on_frame_change(self, event: wx.Event):
        self.frame.fit_model_motion(self.model_material_ctrl.alphas.get(__("ボーンライン"), 0.5))
        self.frame.fit_dress_motion(self.dress_material_ctrl.alphas.get(__("ボーンライン"), 0.5))

    def on_change_alpha(self, event: wx.Event):
        self.change_motion(False)

    def on_change(self, event: wx.Event):
        self.change_motion(True)

    def change_motion(self, is_bone_deform: bool):
        axis_scale_sets: dict[str, MVector3D] = {}
        axis_scale_sets["ALL"] = self.all_axis_set.get_scale()

        self.frame.set_model_motion_morphs(self.model_material_ctrl.alphas)
        self.frame.fit_model_motion(self.model_material_ctrl.alphas.get(__("ボーンライン"), 0.5), is_bone_deform)

        self.frame.set_dress_motion_morphs(axis_scale_sets, self.dress_material_ctrl.alphas)
        self.frame.fit_dress_motion(self.dress_material_ctrl.alphas.get(__("ボーンライン"), 0.5), is_bone_deform)
