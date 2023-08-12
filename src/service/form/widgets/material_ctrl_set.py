import os

import wx

from mlib.core.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl
from mlib.service.form.widgets.image_btn_ctrl import ImageButton

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MaterialCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow, type_name: str) -> None:
        self.parent = parent
        self.window = window
        self.type_name = type_name
        self.is_only: bool = False
        self.is_dropper: bool = False
        self.alphas: dict[str, float] = {}
        self.is_override_colors: dict[str, bool] = {}
        self.override_base_colors: dict[str, list[int]] = {}
        self.override_materials: dict[str, int] = {}
        self.all_material_names: list[str] = []

        self.sizer = wx.StaticBoxSizer(wx.StaticBox(self.window, wx.ID_ANY, __(type_name) + ": " + __("材質非透過度")), orient=wx.VERTICAL)

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
            __(f"スライダーで調整対象となる{type_name}の材質です。\n「ボーンライン」はボーンを表す線を示します。\n非透過度が1でない状態でエクスポートすると、お着替え結果には出力されません\n(ボーンラインは常に出力されません)")
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

        self.only_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            __("単"),
            wx.DefaultPosition,
            wx.Size(30, -1),
        )
        self.only_btn_ctrl.SetToolTip(__(f"{type_name}の材質のみを表示します。もう一回押すと元に戻ります"))
        self.only_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_material_only)
        self.material_sizer.Add(self.only_btn_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.material_sizer, 0, wx.ALL, 3)

        self.slider_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.slider = FloatSliderCtrl(
            parent=self.window,
            value=1,
            min_value=0,
            max_value=1,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(110, -1),
            change_event=self.on_change_morph,
            tooltip=__(f"{type_name}の材質の非透過度を任意の値に変更できます。\n非透過度を1未満にした場合、お着替えモデルには出力されません"),
        )

        self.slider_sizer.Add(self.slider.sizer, 0, wx.ALL, 3)

        self.zero_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "0",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.zero_btn_ctrl.SetToolTip(__(f"{type_name}の材質の非透過度を0.0に設定します"))
        self.zero_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_material_zero)
        self.slider_sizer.Add(self.zero_btn_ctrl, 0, wx.ALL, 3)

        self.half2_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "0.2",
            wx.DefaultPosition,
            wx.Size(30, -1),
        )
        self.half2_btn_ctrl.SetToolTip(__(f"{type_name}の材質の非透過度を0.2に設定します"))
        self.half2_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_material_half2)
        self.slider_sizer.Add(self.half2_btn_ctrl, 0, wx.ALL, 3)

        self.half_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "0.5",
            wx.DefaultPosition,
            wx.Size(30, -1),
        )
        self.half_btn_ctrl.SetToolTip(__(f"{type_name}の材質の非透過度を0.5に設定します"))
        self.half_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_material_half)
        self.slider_sizer.Add(self.half_btn_ctrl, 0, wx.ALL, 3)

        self.one_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "1",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.one_btn_ctrl.SetToolTip(__(f"{type_name}の材質の非透過度を1.0に設定します"))
        self.one_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_material_one)
        self.slider_sizer.Add(self.one_btn_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.slider_sizer, 0, wx.ALL, 3)

        # 色補正ブロック
        self.override_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.override_color_check_ctrl = wx.CheckBox(self.window, wx.ID_ANY, __("色補正あり"), wx.Point(20, -1), wx.DefaultSize, 0)
        self.override_color_check_ctrl.SetToolTip(
            "\n".join(
                [
                    __("このチェックをONにすると指定された色でテクスチャを補正します"),
                    __("補正する色はインクアイコンをクリックした状態でプレビュー画面内を左クリックするか、パレットアイコンから直接定義できます"),
                ]
            )
        )
        self.override_sizer.Add(self.override_color_check_ctrl, 0, wx.ALL, 3)
        self.override_color_check_ctrl.Bind(wx.EVT_CHECKBOX, self.on_change_override_color_check)

        self.dropper_ctrl = ImageButton(
            self.window,
            "resources/icon/color.png",
            wx.Size(15, 15),
            self.on_dropper,
            "\n".join(
                [
                    __("ボタンをクリックした状態でプレビュー画面上で左クリックすると、該当箇所の色を抽出できます"),
                    __("（クリックしたままドラッグして、抽出する色を変える事もできます）"),
                    __("もう一度ボタンをクリックすると、色抽出機能を停止します"),
                ]
            ),
        )
        self.override_sizer.Add(self.dropper_ctrl, 0, wx.ALL, 3)

        self.color_picker_ctrl = wx.ColourPickerCtrl(self.window, wx.ID_ANY, wx.BLACK)
        self.color_picker_ctrl.Bind(wx.EVT_COLOURPICKER_CHANGED, self.picked_override_color)
        self.color_picker_ctrl.SetToolTip(__("色をクリックすると、カラーピッカーから任意の色を定義出来ます"))
        self.override_sizer.Add(self.color_picker_ctrl, 0, wx.ALL, 0)

        # 材質補正ブロック
        self.material_override_ctrl = ImageButton(
            self.window,
            "resources/icon/copy.png",
            wx.Size(15, 15),
            self.on_click_material_override,
            "\n".join(
                [
                    __("他の材質の設定を、選択されている材質の設定に上書きする事ができます"),
                ]
            ),
        )
        self.override_sizer.Add(self.material_override_ctrl, 0, wx.ALL, 3)

        self.copy_material_name_ctrl = wx.TextCtrl(
            self.window,
            wx.ID_ANY,
            "",
            wx.DefaultPosition,
            wx.Size(70, -1),
            wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS,
        )
        self.copy_material_name_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.copy_material_name_ctrl.SetToolTip(__("上書き元の材質名"))
        self.override_sizer.Add(self.copy_material_name_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.override_sizer, 0, wx.ALL, 3)

    def on_click_material_override(self, event: wx.Event):
        with wx.SingleChoiceDialog(
            self.parent,
            __("上書き元の材質を選んでください。先頭の空行を選ぶと、上書き設定をクリアできます。"),
            caption=__("ファイル履歴選択"),
            choices=self.all_material_names,
            style=wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.OK | wx.CANCEL | wx.CENTRE,
        ) as choiceDialog:
            if choiceDialog.ShowModal() == wx.ID_CANCEL:
                return

            self.copy_material_name_ctrl.ChangeValue(choiceDialog.GetStringSelection())

            # 選択した材質INDEXを設定
            material_name = self.material_choice_ctrl.GetStringSelection()
            self.override_materials[material_name] = choiceDialog.GetSelection()

    def on_change_override_color_check(self, event: wx.Event):
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.is_override_colors[material_name] = self.override_color_check_ctrl.GetValue()

    def on_dropper(self, event: wx.Event):
        if not self.is_dropper:
            self.dropper_ctrl.SetBackgroundColour(self.parent.active_background_color)
            self.override_color_check_ctrl.SetValue(True)
            self.on_change_override_color_check(event)
        else:
            self.dropper_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.is_dropper = not self.is_dropper

    def picked_override_color(self, event: wx.Event):
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.override_base_colors[material_name] = [
            self.color_picker_ctrl.GetColour().GetRed(),
            self.color_picker_ctrl.GetColour().GetGreen(),
            self.color_picker_ctrl.GetColour().GetBlue(),
        ]
        self.override_color_check_ctrl.SetValue(True)
        self.on_change_override_color_check(event)

    def initialize(self, material_names: list[str], all_material_names: list[str]) -> None:
        self.material_choice_ctrl.Clear()
        self.all_material_names = all_material_names
        self.alphas = {}
        for material_name in material_names:
            self.material_choice_ctrl.Append(material_name)
            self.alphas[material_name] = 1.0
            self.is_override_colors[material_name] = False
            self.override_base_colors[material_name] = [0, 0, 0]
            self.override_materials[material_name] = 0
        # ボーンの非透過度も調整出来るようにしておく
        self.material_choice_ctrl.Append(__("ボーンライン"))
        self.alphas[__("ボーンライン")] = 0.5
        self.is_override_colors[__("ボーンライン")] = False
        self.override_base_colors[__("ボーンライン")] = [0, 0, 0]
        self.override_materials[__("ボーンライン")] = 0
        # 全材質の非透過度も調整出来るようにしておく
        self.material_choice_ctrl.Append(__("全材質"))
        self.alphas[__("全材質")] = 1.0
        self.is_override_colors[__("全材質")] = False
        self.override_base_colors[__("全材質")] = [0, 0, 0]
        self.override_materials[__("全材質")] = 0
        self.material_choice_ctrl.SetSelection(0)
        self.slider.ChangeValue(1.0)

    def on_change_material(self, event: wx.Event) -> None:
        if self.is_only:
            self.on_change_morph(event)
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.slider.ChangeValue(self.alphas[material_name])
        self.override_color_check_ctrl.SetValue(self.is_override_colors[material_name])
        self.color_picker_ctrl.SetColour(wx.Colour(*self.override_base_colors[material_name]))
        self.color_picker_ctrl.Refresh()
        if self.is_dropper:
            # 抽出モードになっていたら解除
            self.on_dropper(event)
        self.copy_material_name_ctrl.ChangeValue(self.all_material_names[self.override_materials[material_name]])

    def on_change_morph(self, event: wx.Event) -> None:
        self.is_only = False
        alpha = self.slider.GetValue()
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.alphas[material_name] = float(alpha)

        self.parent.Enable(False)
        self.parent.on_change_morph()
        self.parent.Enable(True)

    def on_change_material_only(self, event: wx.Event) -> None:
        material_name = self.material_choice_ctrl.GetStringSelection()

        if material_name in (__("ボーンライン"), __("全材質")):
            return

        self.parent.Enable(False)

        self.is_only = not self.is_only
        if self.is_only:
            self.parent.show_only_material(self.type_name, material_name)
        else:
            self.parent.on_change_morph()

        self.parent.Enable(True)

    def on_change_material_half2(self, event: wx.Event) -> None:
        self.slider.SetValue(0.2)
        self.on_change_morph(event)

    def on_change_material_half(self, event: wx.Event) -> None:
        self.slider.SetValue(0.5)
        self.on_change_morph(event)

    def on_change_material_zero(self, event: wx.Event) -> None:
        self.slider.SetValue(0.0)
        self.on_change_morph(event)

    def on_change_material_one(self, event: wx.Event) -> None:
        self.slider.SetValue(1.0)
        self.on_change_morph(event)

    def on_change_material_right(self, event: wx.Event) -> None:
        selection = self.material_choice_ctrl.GetSelection()
        if selection == len(self.alphas) - 1:
            selection = -1
        self.material_choice_ctrl.SetSelection(selection + 1)
        self.on_change_material(event)

    def on_change_material_left(self, event: wx.Event) -> None:
        selection = self.material_choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.alphas)
        self.material_choice_ctrl.SetSelection(selection - 1)
        self.on_change_material(event)

    def Enable(self, enable: bool) -> None:
        self.material_choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.slider.Enable(enable)
        self.half2_btn_ctrl.Enable(enable)
        self.half_btn_ctrl.Enable(enable)
        self.zero_btn_ctrl.Enable(enable)
        self.one_btn_ctrl.Enable(enable)
        self.only_btn_ctrl.Enable(enable)
        self.override_color_check_ctrl.Enable(enable)
        self.dropper_ctrl.Enable(enable)
        self.color_picker_ctrl.Enable(enable)
        self.material_override_ctrl.Enable(enable)
