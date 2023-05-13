import os

import wx

from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrlDouble

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class AxisCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow, sizer: wx.Sizer, type_name: str) -> None:
        self.sizer = sizer
        self.parent = parent
        self.window = window

        self.title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __(type_name), wx.DefaultPosition, wx.DefaultSize, 0)
        self.title_ctrl.SetToolTip(__(f"{type_name}の追加縮尺をXYZ別に設定することができます"))
        self.sizer.Add(self.title_ctrl, 0, wx.ALL, 3)

        self.x_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, "X", wx.DefaultPosition, wx.DefaultSize, 0)
        self.x_title_ctrl.SetToolTip(__(f"{type_name}X軸方向に追加でどの程度伸縮させるかを設定できます"))
        self.sizer.Add(self.x_title_ctrl, 0, wx.ALL, 3)

        self.x_ctrl = WheelSpinCtrlDouble(self.window, initial=0, min=-10, max=10, size=wx.Size(70, -1), inc=0.1, change_event=self.parent.on_change)
        self.sizer.Add(self.x_ctrl, 0, wx.ALL, 3)

        self.y_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, "Y", wx.DefaultPosition, wx.DefaultSize, 0)
        self.y_title_ctrl.SetToolTip(__(f"{type_name}Y軸方向に追加でどの程度伸縮させるかを設定できます"))
        self.sizer.Add(self.y_title_ctrl, 0, wx.ALL, 3)

        self.y_ctrl = WheelSpinCtrlDouble(self.window, initial=0, min=-10, max=10, size=wx.Size(70, -1), inc=0.1, change_event=self.parent.on_change)
        self.sizer.Add(self.y_ctrl, 0, wx.ALL, 3)

        self.z_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, "Z", wx.DefaultPosition, wx.DefaultSize, 0)
        self.z_title_ctrl.SetToolTip(__(f"{type_name}Z軸方向に追加でどの程度伸縮させるかを設定できます"))
        self.sizer.Add(self.z_title_ctrl, 0, wx.ALL, 3)

        self.z_ctrl = WheelSpinCtrlDouble(self.window, initial=0, min=-10, max=10, size=wx.Size(70, -1), inc=0.1, change_event=self.parent.on_change)
        self.sizer.Add(self.z_ctrl, 0, wx.ALL, 3)

    def get_scale(self) -> MVector3D:
        return MVector3D(self.x_ctrl.GetValue(), self.y_ctrl.GetValue(), self.z_ctrl.GetValue())
