import os

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl
from mlib.base.math import MVector3D

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class BoneCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow, sizer: wx.Sizer) -> None:
        self.sizer = sizer
        self.parent = parent
        self.window = window
        self.scales: dict[str, MVector3D] = {}
        self.degrees: dict[str, MVector3D] = {}
        self.positions: dict[str, MVector3D] = {}

        self.bone_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.left_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "<",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.left_btn_ctrl.SetToolTip(__("ボーンプルダウンの選択肢を上方向に移動できます。"))
        self.left_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_bone_left)
        self.bone_sizer.Add(self.left_btn_ctrl, 0, wx.ALL, 3)

        self.bone_choice_ctrl = wx.Choice(
            self.window,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(210, -1),
            choices=[],
        )
        self.bone_choice_ctrl.SetToolTip(__("スライダーで調整対象となる衣装のボーンです。\n左右は一括で調整できます。"))
        self.bone_choice_ctrl.Bind(wx.EVT_CHOICE, self.on_change_bone)
        self.bone_sizer.Add(self.bone_choice_ctrl, 1, wx.EXPAND | wx.ALL, 3)

        self.right_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            ">",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.right_btn_ctrl.SetToolTip(__("ボーンプルダウンの選択肢を下方向に移動できます。"))
        self.right_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_bone_right)
        self.bone_sizer.Add(self.right_btn_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.bone_sizer, 0, wx.ALL, 3)

        self.grid_sizer = wx.FlexGridSizer(0, 2, 0, 0)

        self.scale_x_label = wx.StaticText(self.window, wx.ID_ANY, __("縮尺X"))
        self.grid_sizer.Add(self.scale_x_label, 0, wx.ALL, 3)

        self.scale_x_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-1,
            max_value=1,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_scale_x_slider,
            tooltip=__("選択されたボーンのX軸方向の縮尺を調整できます"),
        )
        self.grid_sizer.Add(self.scale_x_slider.sizer, 0, wx.ALL, 3)

        self.scale_y_label = wx.StaticText(self.window, wx.ID_ANY, __("縮尺Y"))
        self.grid_sizer.Add(self.scale_y_label, 0, wx.ALL, 3)

        self.scale_y_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-1,
            max_value=1,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_scale_y_slider,
            tooltip=__("選択されたボーンのY軸方向の縮尺を調整できます"),
        )
        self.grid_sizer.Add(self.scale_y_slider.sizer, 0, wx.ALL, 3)

        self.scale_z_label = wx.StaticText(self.window, wx.ID_ANY, __("縮尺Z"))
        self.grid_sizer.Add(self.scale_z_label, 0, wx.ALL, 3)

        self.scale_z_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-1,
            max_value=1,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_scale_z_slider,
            tooltip=__("選択されたボーンのZ軸方向の縮尺を調整できます"),
        )
        self.grid_sizer.Add(self.scale_z_slider.sizer, 0, wx.ALL, 3)

        self.degree_x_label = wx.StaticText(self.window, wx.ID_ANY, __("回転X"))
        self.grid_sizer.Add(self.degree_x_label, 0, wx.ALL, 3)

        self.degree_x_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-2,
            max_value=2,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_degree_x_slider,
            tooltip=__("選択されたボーンのX軸方向の回転を調整できます"),
        )
        self.grid_sizer.Add(self.degree_x_slider.sizer, 0, wx.ALL, 3)

        self.degree_y_label = wx.StaticText(self.window, wx.ID_ANY, __("回転Y"))
        self.grid_sizer.Add(self.degree_y_label, 0, wx.ALL, 3)

        self.degree_y_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-2,
            max_value=2,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_degree_y_slider,
            tooltip=__("選択されたボーンのY軸方向の回転を調整できます"),
        )
        self.grid_sizer.Add(self.degree_y_slider.sizer, 0, wx.ALL, 3)

        self.degree_z_label = wx.StaticText(self.window, wx.ID_ANY, __("回転Z"))
        self.grid_sizer.Add(self.degree_z_label, 0, wx.ALL, 3)

        self.degree_z_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-2,
            max_value=2,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_degree_z_slider,
            tooltip=__("選択されたボーンのZ軸方向の回転を調整できます"),
        )
        self.grid_sizer.Add(self.degree_z_slider.sizer, 0, wx.ALL, 3)

        self.position_x_label = wx.StaticText(self.window, wx.ID_ANY, __("移動X"))
        self.grid_sizer.Add(self.position_x_label, 0, wx.ALL, 3)

        self.position_x_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-2,
            max_value=2,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_position_x_slider,
            tooltip=__("選択されたボーンのX軸方向の移動を調整できます"),
        )
        self.grid_sizer.Add(self.position_x_slider.sizer, 0, wx.ALL, 3)

        self.position_y_label = wx.StaticText(self.window, wx.ID_ANY, __("移動Y"))
        self.grid_sizer.Add(self.position_y_label, 0, wx.ALL, 3)

        self.position_y_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-2,
            max_value=2,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_position_y_slider,
            tooltip=__("選択されたボーンのY軸方向の移動を調整できます"),
        )
        self.grid_sizer.Add(self.position_y_slider.sizer, 0, wx.ALL, 3)

        self.position_z_label = wx.StaticText(self.window, wx.ID_ANY, __("移動Z"))
        self.grid_sizer.Add(self.position_z_label, 0, wx.ALL, 3)

        self.position_z_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-2,
            max_value=2,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_position_z_slider,
            tooltip=__("選択されたボーンのZ軸方向の移動を調整できます"),
        )
        self.grid_sizer.Add(self.position_z_slider.sizer, 0, wx.ALL, 3)

        self.sizer.Add(self.grid_sizer, 0, wx.ALL, 0)

    def initialize(self):
        self.bone_choice_ctrl.Clear()
        for bone_name in ("体幹", "下半身", "上半身", "上半身2", "首", "頭", "頭部装飾", "肩", "腕", "ひじ", "手のひら", "足", "ひざ", "足の甲"):
            self.bone_choice_ctrl.Append(__(bone_name))
            self.scales[__(bone_name)] = MVector3D()
            self.degrees[__(bone_name)] = MVector3D()
            self.positions[__(bone_name)] = MVector3D()
        self.bone_choice_ctrl.SetSelection(0)
        self.scale_x_slider.ChangeValue(0.0)
        self.scale_y_slider.ChangeValue(0.0)
        self.scale_z_slider.ChangeValue(0.0)
        self.degree_x_slider.ChangeValue(0.0)
        self.degree_y_slider.ChangeValue(0.0)
        self.degree_z_slider.ChangeValue(0.0)
        self.position_x_slider.ChangeValue(0.0)
        self.position_y_slider.ChangeValue(0.0)
        self.position_z_slider.ChangeValue(0.0)

    def on_change_bone(self, event: wx.Event):
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.scale_x_slider.ChangeValue(self.scales[bone_name].x)
        self.scale_y_slider.ChangeValue(self.scales[bone_name].y)
        self.scale_z_slider.ChangeValue(self.scales[bone_name].z)
        self.degree_x_slider.ChangeValue(self.degrees[bone_name].x)
        self.degree_y_slider.ChangeValue(self.degrees[bone_name].y)
        self.degree_z_slider.ChangeValue(self.degrees[bone_name].z)
        self.position_x_slider.ChangeValue(self.positions[bone_name].x)
        self.position_y_slider.ChangeValue(self.positions[bone_name].y)
        self.position_z_slider.ChangeValue(self.positions[bone_name].z)

    def on_change_scale_x_slider(self, event: wx.Event):
        scale_x = self.scale_x_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.scales[bone_name].x = float(scale_x)
        self.parent.on_change(event)

    def on_change_scale_y_slider(self, event: wx.Event):
        scale_y = self.scale_y_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.scales[bone_name].y = float(scale_y)
        self.parent.on_change(event)

    def on_change_scale_z_slider(self, event: wx.Event):
        scale_z = self.scale_z_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.scales[bone_name].z = float(scale_z)
        self.parent.on_change(event)

    def on_change_degree_x_slider(self, event: wx.Event):
        degree_x = self.degree_x_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.degrees[bone_name].x = float(degree_x)
        self.parent.on_change(event)

    def on_change_degree_y_slider(self, event: wx.Event):
        degree_y = self.degree_y_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.degrees[bone_name].y = float(degree_y)
        self.parent.on_change(event)

    def on_change_degree_z_slider(self, event: wx.Event):
        degree_z = self.degree_z_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.degrees[bone_name].z = float(degree_z)
        self.parent.on_change(event)

    def on_change_position_x_slider(self, event: wx.Event):
        position_x = self.position_x_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.positions[bone_name].x = float(position_x)
        self.parent.on_change(event)

    def on_change_position_y_slider(self, event: wx.Event):
        position_y = self.position_y_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.positions[bone_name].y = float(position_y)
        self.parent.on_change(event)

    def on_change_position_z_slider(self, event: wx.Event):
        position_z = self.position_z_slider.GetValue()
        bone_name = self.bone_choice_ctrl.GetStringSelection()
        self.positions[bone_name].z = float(position_z)
        self.parent.on_change(event)

    def on_change_bone_right(self, event: wx.Event):
        selection = self.bone_choice_ctrl.GetSelection()
        if selection == len(self.scales) - 1:
            selection = -1
        self.bone_choice_ctrl.SetSelection(selection + 1)
        self.on_change_bone(event)

    def on_change_bone_left(self, event: wx.Event):
        selection = self.bone_choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.scales)
        self.bone_choice_ctrl.SetSelection(selection - 1)
        self.on_change_bone(event)

    def enable(self, enable: bool):
        self.bone_choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.scale_x_slider.enable(enable)
        self.scale_y_slider.enable(enable)
        self.scale_z_slider.enable(enable)
        self.degree_x_slider.enable(enable)
        self.degree_y_slider.enable(enable)
        self.degree_z_slider.enable(enable)
        self.position_x_slider.enable(enable)
        self.position_y_slider.enable(enable)
        self.position_z_slider.enable(enable)