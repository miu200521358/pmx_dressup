import os

import wx

from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.form.base_frame import BaseFrame
from mlib.form.parts.spin_ctrl import WheelSpinCtrlDouble
from mlib.pmx.canvas import CanvasPanel

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ConfigPanel(CanvasPanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, 650, 800, *args, **kw)

        self._initialize_ui()
        self._initialize_event()

    def _initialize_ui(self):
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        self.config_sizer = wx.BoxSizer(wx.VERTICAL)

        self.title_ctrl = wx.StaticText(self, wx.ID_ANY, __("追加縮尺"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.title_ctrl.SetToolTip(__("全体や各ボーンにおける縮尺をXYZ別に設定することができます"))
        self.config_sizer.Add(self.title_ctrl, 0, wx.ALL, 3)

        self.grid_sizer = wx.FlexGridSizer(rows=1, cols=7, vgap=0, hgap=0)

        # 全体
        self.all_axis_set = AxisCtrlSet(self, self.grid_sizer, "全体")

        self.config_sizer.Add(self.grid_sizer, 0, wx.ALL, 3)

        self.sizer.Add(self.config_sizer, 0, wx.ALL, 3)
        self.root_sizer.Add(self.sizer, 0, wx.ALL, 0)

        self.fit()

    def _initialize_event(self):
        pass

    def on_change(self, event: wx.Event):
        scale_sets: dict[str, MVector3D] = {}
        scale_sets["ALL"] = self.all_axis_set.get_scale()

        dress_motion = self.frame.create_dress_motion(scale_sets)
        self.frame.fit_dress_motion(dress_motion)


class AxisCtrlSet:
    def __init__(self, parent: ConfigPanel, sizer: wx.Sizer, type_name: str) -> None:
        self.sizer = sizer
        self.parent = parent

        self.title_ctrl = wx.StaticText(self.parent, wx.ID_ANY, __(type_name), wx.DefaultPosition, wx.DefaultSize, 0)
        self.title_ctrl.SetToolTip(__(f"{type_name}の追加縮尺をXYZ別に設定することができます"))
        self.sizer.Add(self.title_ctrl, 0, wx.ALL, 3)

        self.x_title_ctrl = wx.StaticText(self.parent, wx.ID_ANY, __("X"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.x_title_ctrl.SetToolTip(__(f"{type_name}X軸方向に追加でどの程度伸縮させるかを設定できます"))
        self.sizer.Add(self.x_title_ctrl, 0, wx.ALL, 3)

        self.x_ctrl = WheelSpinCtrlDouble(self.parent, initial=0, min=0, max=10, size=wx.Size(70, -1), inc=0.01, change_event=self.parent.on_change)
        self.sizer.Add(self.x_ctrl, 0, wx.ALL, 3)

        self.y_title_ctrl = wx.StaticText(self.parent, wx.ID_ANY, __("Y"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.y_title_ctrl.SetToolTip(__(f"{type_name}Y軸方向に追加でどの程度伸縮させるかを設定できます"))
        self.sizer.Add(self.y_title_ctrl, 0, wx.ALL, 3)

        self.y_ctrl = WheelSpinCtrlDouble(self.parent, initial=0, min=0, max=10, size=wx.Size(70, -1), inc=0.01, change_event=self.parent.on_change)
        self.sizer.Add(self.y_ctrl, 0, wx.ALL, 3)

        self.z_title_ctrl = wx.StaticText(self.parent, wx.ID_ANY, __("Z"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.z_title_ctrl.SetToolTip(__(f"{type_name}Z軸方向に追加でどの程度伸縮させるかを設定できます"))
        self.sizer.Add(self.z_title_ctrl, 0, wx.ALL, 3)

        self.z_ctrl = WheelSpinCtrlDouble(self.parent, initial=0, min=0, max=10, size=wx.Size(70, -1), inc=0.01, change_event=self.parent.on_change)
        self.sizer.Add(self.z_ctrl, 0, wx.ALL, 3)

    def get_scale(self) -> MVector3D:
        return MVector3D(self.x_ctrl.GetValue(), self.y_ctrl.GetValue(), self.z_ctrl.GetValue())
