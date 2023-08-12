import os

import wx

from mlib.core.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MorphCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow, type_name: str) -> None:
        self.parent = parent
        self.window = window
        self.type_name = type_name
        self.ratios: dict[str, float] = {}
        self.all_morph_names: list[str] = []

        self.sizer = wx.StaticBoxSizer(wx.StaticBox(self.window, wx.ID_ANY, __(type_name) + ": " + __("モーフ")), orient=wx.VERTICAL)

        self.morph_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.left_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "<",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.left_btn_ctrl.SetToolTip(__(f"{type_name}のモーフプルダウンの選択肢を上方向に移動できます。"))
        self.left_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_left)
        self.morph_sizer.Add(self.left_btn_ctrl, 0, wx.ALL, 3)

        self.morph_choice_ctrl = wx.Choice(
            self.window,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(200, -1),
            choices=[],
        )
        self.morph_choice_ctrl.SetToolTip(__(f"スライダーで調整対象となる{type_name}のモーフです。\nモーフの値が0より大きい状態にすると、お着替え結果に反映されます"))
        self.morph_choice_ctrl.Bind(wx.EVT_CHOICE, self.on_choice_morph)
        self.morph_sizer.Add(self.morph_choice_ctrl, 1, wx.EXPAND | wx.ALL, 3)

        self.right_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            ">",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.right_btn_ctrl.SetToolTip(__(f"{type_name}のモーフプルダウンの選択肢を下方向に移動できます。"))
        self.right_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_right)
        self.morph_sizer.Add(self.right_btn_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.morph_sizer, 0, wx.ALL, 3)

        self.slider_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.slider = FloatSliderCtrl(
            parent=self.window,
            value=1,
            min_value=0,
            max_value=1,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(100, -1),
            change_event=self.on_change_morph,
            tooltip=__(f"{type_name}のモーフを任意の値に変更できます。\nモーフの値が0より大きい状態にすると、お着替え結果に反映されます"),
        )

        self.slider_sizer.Add(self.slider.sizer, 0, wx.ALL, 3)

        self.zero_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "0",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.zero_btn_ctrl.SetToolTip(__(f"{type_name}のモーフの値を0.0に設定します"))
        self.zero_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_zero)
        self.slider_sizer.Add(self.zero_btn_ctrl, 0, wx.ALL, 3)

        self.half_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "0.5",
            wx.DefaultPosition,
            wx.Size(30, -1),
        )
        self.half_btn_ctrl.SetToolTip(__(f"{type_name}のモーフの値を0.5に設定します"))
        self.half_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_half)
        self.slider_sizer.Add(self.half_btn_ctrl, 0, wx.ALL, 3)

        self.one_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "1",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.one_btn_ctrl.SetToolTip(__(f"{type_name}のモーフの値を1.0に設定します"))
        self.one_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_one)
        self.slider_sizer.Add(self.one_btn_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.slider_sizer, 0, wx.ALL, 3)

    def initialize(self, morph_names: list[str]) -> None:
        self.morph_choice_ctrl.Clear()
        self.morph_choice_ctrl.AppendItems(morph_names)
        self.ratios = {}
        for morph_name in morph_names:
            self.ratios[morph_name] = 0.0
        self.morph_choice_ctrl.SetSelection(0)
        self.slider.ChangeValue(0.0)

    def on_choice_morph(self, event: wx.Event) -> None:
        morph_name = self.morph_choice_ctrl.GetStringSelection()
        self.slider.ChangeValue(self.ratios[morph_name])

    def on_change_morph(self, event: wx.Event) -> None:
        ratio = self.slider.GetValue()
        morph_name = self.morph_choice_ctrl.GetStringSelection()
        self.ratios[morph_name] = float(ratio)

        self.parent.Enable(False)
        # ボーンモーフが絡む可能性があるので、ボーン変形ありで動かす
        self.parent.on_change()
        self.parent.Enable(True)

    def on_change_morph_half(self, event: wx.Event) -> None:
        self.slider.SetValue(0.5)
        self.on_change_morph(event)

    def on_change_morph_zero(self, event: wx.Event) -> None:
        self.slider.SetValue(0.0)
        self.on_change_morph(event)

    def on_change_morph_one(self, event: wx.Event) -> None:
        self.slider.SetValue(1.0)
        self.on_change_morph(event)

    def on_change_morph_right(self, event: wx.Event) -> None:
        selection = self.morph_choice_ctrl.GetSelection()
        if selection == len(self.ratios) - 1:
            selection = -1
        self.morph_choice_ctrl.SetSelection(selection + 1)
        self.on_change_morph(event)

    def on_change_morph_left(self, event: wx.Event) -> None:
        selection = self.morph_choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.ratios)
        self.morph_choice_ctrl.SetSelection(selection - 1)
        self.on_change_morph(event)

    def Enable(self, enable: bool) -> None:
        self.morph_choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.slider.Enable(enable)
        self.half_btn_ctrl.Enable(enable)
        self.zero_btn_ctrl.Enable(enable)
        self.one_btn_ctrl.Enable(enable)
