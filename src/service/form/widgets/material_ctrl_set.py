import os

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MaterialCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow, sizer: wx.Sizer, type_name: str) -> None:
        self.sizer = sizer
        self.parent = parent
        self.window = window
        self.alphas: dict[str, float] = {}

        self.title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __(type_name), wx.DefaultPosition, wx.DefaultSize, 0)
        self.title_ctrl.SetToolTip(__(f"{type_name}の材質プルダウンから選択した材質の透過度を下のスライダーで調整できます。"))
        self.sizer.Add(self.title_ctrl, 0, wx.ALL, 3)

        self.material_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.left_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "<",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.left_btn_ctrl.SetToolTip(__(f"{type_name}の材質プルダウンの選択肢を上方向に移動できます。"))
        self.left_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_material_left)
        self.material_sizer.Add(self.left_btn_ctrl, 0, wx.ALL, 3)

        self.material_choice_ctrl = wx.Choice(
            self.window,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(210, -1),
            choices=[],
        )
        self.material_choice_ctrl.SetToolTip(
            __(f"スライダーで調整対象となる{type_name}の材質です。\n「ボーンライン」はボーンを表す線を示します。\n透過度が1でない状態でエクスポートすると、お着替え結果には出力されません\n(ボーンラインは常に出力されません)")
        )
        self.material_choice_ctrl.Bind(wx.EVT_CHOICE, self.on_change_material)
        self.material_sizer.Add(self.material_choice_ctrl, 1, wx.EXPAND | wx.ALL, 3)

        self.right_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            ">",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.right_btn_ctrl.SetToolTip(__(f"{type_name}の材質プルダウンの選択肢を下方向に移動できます。"))
        self.right_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_material_right)
        self.material_sizer.Add(self.right_btn_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.material_sizer, 0, wx.ALL, 3)

        self.slider = FloatSliderCtrl(
            parent=self.window,
            value=1,
            min_value=0,
            max_value=1,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(240, -1),
            change_event=self.on_change_morph,
        )
        self.sizer.Add(self.slider.sizer, 0, wx.ALL, 3)

    def initialize(self, material_names: list[str]):
        self.material_choice_ctrl.Clear()
        for material_name in material_names:
            self.material_choice_ctrl.Append(material_name)
            self.alphas[material_name] = 1.0
        # ボーンの透過度も調整出来るようにしておく
        self.material_choice_ctrl.Append(__("ボーンライン"))
        self.alphas[__("ボーンライン")] = 0.5
        self.material_choice_ctrl.SetSelection(0)
        self.slider.ChangeValue(1.0)
        # 全材質の透過度も調整出来るようにしておく
        self.material_choice_ctrl.Append(__("全材質"))
        self.alphas[__("全材質")] = 1.0
        self.material_choice_ctrl.SetSelection(0)
        self.slider.ChangeValue(1.0)

    def on_change_material(self, event: wx.Event):
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.slider.ChangeValue(self.alphas[material_name])

    def on_change_morph(self, event: wx.Event):
        alpha = self.slider.GetValue()
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.alphas[material_name] = float(alpha)
        self.parent.on_change_morph(event)

    def on_change_material_right(self, event: wx.Event):
        selection = self.material_choice_ctrl.GetSelection()
        if selection == len(self.alphas) - 1:
            selection = -1
        self.material_choice_ctrl.SetSelection(selection + 1)
        self.on_change_material(event)

    def on_change_material_left(self, event: wx.Event):
        selection = self.material_choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.alphas)
        self.material_choice_ctrl.SetSelection(selection - 1)
        self.on_change_material(event)

    def enable(self, enable: bool):
        self.material_choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.slider.enable(enable)
