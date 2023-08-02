import os

import wx

from mlib.core.logger import MLogger
from mlib.core.math import MVector3D
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl
from mlib.service.form.widgets.image_btn_ctrl import ImageButton

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
        self.bone_target_dress: dict[str, bool] = {}
        self.individual_target_bone_indexes: list[list[int]] = []
        self.is_link_scale: bool = False

        self.bone_sizer = wx.BoxSizer(wx.HORIZONTAL)

        bone_weight_tooltip = __("このチェックをONにすると、選択ボーンのウェイト範囲をグラデーションで表示します")
        self.bone_weight_check_ctrl = wx.CheckBox(self.window, wx.ID_ANY, __("ボーンウェイト表示"), wx.Point(20, -1), wx.DefaultSize, 0)
        self.bone_weight_check_ctrl.Bind(wx.EVT_CHECKBOX, self.on_show_bone_weight)
        self.bone_weight_check_ctrl.SetToolTip(bone_weight_tooltip)
        self.sizer.Add(self.bone_weight_check_ctrl, 0, wx.ALL, 3)

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
            wx.Size(230, -1),
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

        self.grid_sizer = wx.FlexGridSizer(0, 3, 0, 0)

        scale_x_tooltip = __("選択されたボーンの横方向の縮尺を調整できます")
        self.scale_x_label = wx.StaticText(self.window, wx.ID_ANY, __("縮尺X"))
        self.scale_x_label.SetToolTip(scale_x_tooltip)
        self.grid_sizer.Add(self.scale_x_label, 0, wx.ALL, 3)

        self.scale_x_slider = FloatSliderCtrl(
            parent=self.window,
            value=1,
            min_value=0.01,
            max_value=5,
            increment=0.01,
            spin_increment=0.05,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_scale_x_slider,
            tooltip=scale_x_tooltip,
        )
        self.grid_sizer.Add(self.scale_x_slider.sizer, 0, wx.ALL, 3)

        self.scale_connect_start_label = wx.StaticText(self.window, wx.ID_ANY, "┐")
        self.grid_sizer.Add(self.scale_connect_start_label, 0, wx.ALL, 3)

        # # 画像を読み込む
        # copy_image = wx.Image(get_path("resources/icon/copy.png"), wx.BITMAP_TYPE_ANY)
        # self.copy_bitmap = wx.StaticBitmap(self.window, wx.ID_ANY, copy_image.Scale(15, 15).ConvertToBitmap())
        # self.grid_sizer.Add(self.copy_bitmap, 0, wx.ALL, 3)

        scale_y_tooltip = __("選択されたボーンの長さ方向の縮尺を調整できます")
        self.scale_y_label = wx.StaticText(self.window, wx.ID_ANY, __("縮尺Y"))
        self.scale_y_label.SetToolTip(scale_y_tooltip)
        self.grid_sizer.Add(self.scale_y_label, 0, wx.ALL, 3)

        self.scale_y_slider = FloatSliderCtrl(
            parent=self.window,
            value=1,
            min_value=0.01,
            max_value=5,
            increment=0.01,
            spin_increment=0.05,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_slider,
            tooltip=scale_y_tooltip,
        )
        self.grid_sizer.Add(self.scale_y_slider.sizer, 0, wx.ALL, 3)

        self.scale_link_ctrl: ImageButton = ImageButton(
            self.window,
            "resources/icon/link_off.png",
            wx.Size(15, 15),
            self.on_link_scale,
            "\n".join(
                [
                    __("ボタンをONにすると、縮尺XとZを同時に操作することができます"),
                    __("（読み込み直後はONになっています）"),
                    __("OFFにすると、縮尺XとZを別々に操作する事ができます"),
                ]
            ),
        )
        self.grid_sizer.Add(self.scale_link_ctrl, 0, wx.ALL, 3)

        # self.scale_link_ctrl = wx.CheckBox(self.window, wx.ID_ANY, "", wx.DefaultPosition, wx.DefaultSize, 0)
        # self.scale_link_ctrl.SetToolTip(__("チェックをONにすると、縮尺XとZを同時に操作することができます"))
        # self.grid_sizer.Add(self.scale_link_ctrl, 0, wx.ALL, 3)

        scale_z_tooltip = __("選択されたボーンの奥行き方向の縮尺を調整できます")
        self.scale_z_label = wx.StaticText(self.window, wx.ID_ANY, __("縮尺Z"))
        self.scale_z_label.SetToolTip(scale_z_tooltip)
        self.grid_sizer.Add(self.scale_z_label, 0, wx.ALL, 3)

        self.scale_z_slider = FloatSliderCtrl(
            parent=self.window,
            value=1,
            min_value=0.01,
            max_value=5,
            increment=0.01,
            spin_increment=0.05,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_scale_z_slider,
            tooltip=scale_z_tooltip,
        )
        self.grid_sizer.Add(self.scale_z_slider.sizer, 0, wx.ALL, 3)

        self.scale_connect_end_label = wx.StaticText(self.window, wx.ID_ANY, "┘")
        self.grid_sizer.Add(self.scale_connect_end_label, 0, wx.ALL, 3)

        degree_x_tooltip = __("選択されたボーンの横方向の回転を調整できます")
        self.degree_x_label = wx.StaticText(self.window, wx.ID_ANY, __("回転X"))
        self.degree_x_label.SetToolTip(degree_x_tooltip)
        self.grid_sizer.Add(self.degree_x_label, 0, wx.ALL, 3)

        self.degree_x_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-45,
            max_value=45,
            increment=0.01,
            spin_increment=1,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_slider,
            tooltip=degree_x_tooltip,
        )
        self.grid_sizer.Add(self.degree_x_slider.sizer, 0, wx.ALL, 3)

        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        degree_y_tooltip = __("選択されたボーンの長さ方向の回転を調整できます")
        self.degree_y_label = wx.StaticText(self.window, wx.ID_ANY, __("回転Y"))
        self.degree_y_label.SetToolTip(degree_y_tooltip)
        self.grid_sizer.Add(self.degree_y_label, 0, wx.ALL, 3)

        self.degree_y_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-45,
            max_value=45,
            increment=0.01,
            spin_increment=1,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_slider,
            tooltip=degree_y_tooltip,
        )
        self.grid_sizer.Add(self.degree_y_slider.sizer, 0, wx.ALL, 3)

        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        degree_z_tooltip = __("選択されたボーンの奥行き方向の回転を調整できます")
        self.degree_z_label = wx.StaticText(self.window, wx.ID_ANY, __("回転Z"))
        self.degree_z_label.SetToolTip(degree_z_tooltip)
        self.grid_sizer.Add(self.degree_z_label, 0, wx.ALL, 3)

        self.degree_z_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-45,
            max_value=45,
            increment=0.01,
            spin_increment=1,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_slider,
            tooltip=degree_z_tooltip,
        )
        self.grid_sizer.Add(self.degree_z_slider.sizer, 0, wx.ALL, 3)

        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        position_x_tooltip = __("選択されたボーンの横方向の移動を調整できます")
        self.position_x_label = wx.StaticText(self.window, wx.ID_ANY, __("移動X"))
        self.position_x_label.SetToolTip(position_x_tooltip)
        self.grid_sizer.Add(self.position_x_label, 0, wx.ALL, 3)

        self.position_x_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-4,
            max_value=4,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_slider,
            tooltip=position_x_tooltip,
        )
        self.grid_sizer.Add(self.position_x_slider.sizer, 0, wx.ALL, 3)

        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        position_y_tooltip = __("選択されたボーンの長さ方向の移動を調整できます")
        self.position_y_label = wx.StaticText(self.window, wx.ID_ANY, __("移動Y"))
        self.position_y_label.SetToolTip(position_y_tooltip)
        self.grid_sizer.Add(self.position_y_label, 0, wx.ALL, 3)

        self.position_y_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-4,
            max_value=4,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_slider,
            tooltip=position_y_tooltip,
        )
        self.grid_sizer.Add(self.position_y_slider.sizer, 0, wx.ALL, 3)

        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        position_z_tooltip = __("選択されたボーンの奥行き方向の移動を調整できます")
        self.position_z_label = wx.StaticText(self.window, wx.ID_ANY, __("移動Z"))
        self.position_z_label.SetToolTip(position_z_tooltip)
        self.grid_sizer.Add(self.position_z_label, 0, wx.ALL, 3)

        self.position_z_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-4,
            max_value=4,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(230, -1),
            change_event=self.on_change_slider,
            tooltip=position_z_tooltip,
        )
        self.grid_sizer.Add(self.position_z_slider.sizer, 0, wx.ALL, 3)

        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        bone_target_dress_tooltip = __("人物と衣装のどちらにもメッシュがある場合には、基本的には人物側のボーン位置で出力します。\n") + __(
            "このチェックをONにすると、指など人物と衣装のボーン位置がずれている場合に衣装側のボーン位置で出力することができます。"
        )
        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        self.bone_target_dress_check_ctrl = wx.CheckBox(
            self.window, wx.ID_ANY, __("ボーン位置を衣装モデルに合わせる"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.bone_target_dress_check_ctrl.Bind(wx.EVT_CHECKBOX, self.on_change_bone_target_dress)
        self.bone_target_dress_check_ctrl.SetToolTip(bone_target_dress_tooltip)
        self.grid_sizer.Add(self.bone_target_dress_check_ctrl, 0, wx.ALL, 3)

        self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, ""), 0, wx.ALL, 3)

        self.sizer.Add(self.grid_sizer, 0, wx.ALL, 0)

        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_sizer.AddStretchSpacer()

        self.clear_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            __("初期化"),
            wx.DefaultPosition,
            wx.Size(80, -1),
        )
        self.clear_btn_ctrl.SetToolTip(__("ボーン調整値をすべて初期化します"))
        self.clear_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_clear)
        self.btn_sizer.Add(self.clear_btn_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(self.btn_sizer, 1, wx.EXPAND, 0)

    def initialize(self, individual_morph_names: list[str], individual_target_bone_indexes: list[list[int]]) -> None:
        self.bone_choice_ctrl.Clear()
        for morph_name in individual_morph_names:
            self.bone_choice_ctrl.Append(morph_name)
            self.scales[morph_name] = MVector3D(1, 1, 1)
            self.degrees[morph_name] = MVector3D()
            self.positions[morph_name] = MVector3D()
            self.bone_target_dress[morph_name] = False
        self.bone_choice_ctrl.SetSelection(0)
        self.scale_x_slider.ChangeValue(1.0)
        self.scale_y_slider.ChangeValue(1.0)
        self.scale_z_slider.ChangeValue(1.0)
        self.degree_x_slider.ChangeValue(0.0)
        self.degree_y_slider.ChangeValue(0.0)
        self.degree_z_slider.ChangeValue(0.0)
        self.position_x_slider.ChangeValue(0.0)
        self.position_y_slider.ChangeValue(0.0)
        self.position_z_slider.ChangeValue(0.0)
        # ボーンハイライトを変更
        self.individual_target_bone_indexes = individual_target_bone_indexes
        # リンクボタンをONに
        self.on_link_scale(wx.EVT_BUTTON)

    def on_link_scale(self, event: wx.Event):
        if not self.is_link_scale:
            self.scale_link_ctrl.SetBackgroundColour(self.parent.active_background_color)
            self.scale_link_ctrl.SetBitmap(self.scale_link_ctrl.create_bitmap("resources/icon/link_on.png"))
        else:
            self.scale_link_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            self.scale_link_ctrl.SetBitmap(self.scale_link_ctrl.create_bitmap("resources/icon/link_off.png"))
        self.is_link_scale = not self.is_link_scale

    def on_change_bone(self, event: wx.Event) -> None:
        morph_name = self.bone_choice_ctrl.GetStringSelection()
        self.scale_x_slider.ChangeValue(self.scales[morph_name].x)
        self.scale_y_slider.ChangeValue(self.scales[morph_name].y)
        self.scale_z_slider.ChangeValue(self.scales[morph_name].z)
        self.degree_x_slider.ChangeValue(self.degrees[morph_name].x)
        self.degree_y_slider.ChangeValue(self.degrees[morph_name].y)
        self.degree_z_slider.ChangeValue(self.degrees[morph_name].z)
        self.position_x_slider.ChangeValue(self.positions[morph_name].x)
        self.position_y_slider.ChangeValue(self.positions[morph_name].y)
        self.position_z_slider.ChangeValue(self.positions[morph_name].z)
        self.bone_target_dress_check_ctrl.SetValue(self.bone_target_dress[morph_name])
        # ボーンハイライトを変更
        self.parent.change_bone(self.individual_target_bone_indexes[self.bone_choice_ctrl.GetSelection()])

    def on_change_bone_right(self, event: wx.Event) -> None:
        selection = self.bone_choice_ctrl.GetSelection()
        if selection == len(self.scales) - 1:
            selection = -1
        self.bone_choice_ctrl.SetSelection(selection + 1)
        self.on_change_bone(event)

    def on_change_bone_left(self, event: wx.Event) -> None:
        selection = self.bone_choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.scales)
        self.bone_choice_ctrl.SetSelection(selection - 1)
        self.on_change_bone(event)

    def on_change_bone_target_dress(self, event: wx.Event) -> None:
        morph_name = self.bone_choice_ctrl.GetStringSelection()
        self.bone_target_dress[morph_name] = self.bone_target_dress_check_ctrl.GetValue()

    def on_change_clear(self, event: wx.Event) -> None:
        for morph_name in self.scales.keys():
            self.scales[morph_name] = MVector3D(1, 1, 1)
            self.degrees[morph_name] = MVector3D()
            self.positions[morph_name] = MVector3D()
            self.bone_target_dress[morph_name] = False
        # self.bone_choice_ctrl.SetSelection(0)
        self.scale_x_slider.ChangeValue(1.0)
        self.scale_y_slider.ChangeValue(1.0)
        self.scale_z_slider.ChangeValue(1.0)
        self.degree_x_slider.ChangeValue(0.0)
        self.degree_y_slider.ChangeValue(0.0)
        self.degree_z_slider.ChangeValue(0.0)
        self.position_x_slider.ChangeValue(0.0)
        self.position_y_slider.ChangeValue(0.0)
        self.position_z_slider.ChangeValue(0.0)
        self.scale_link_ctrl.SetValue(1)
        self.bone_target_dress_check_ctrl.SetValue(0)

        self.parent.Enable(False)
        self.parent.on_change(is_clear=True)
        self.parent.Enable(True)

    def on_change_scale_x_slider(self, event: wx.Event) -> None:
        if self.is_link_scale:
            self.scale_z_slider.ChangeValue(self.scale_x_slider.GetValue())
        self.on_change_slider(event)

    def on_change_scale_z_slider(self, event: wx.Event) -> None:
        if self.is_link_scale:
            self.scale_x_slider.ChangeValue(self.scale_z_slider.GetValue())
        self.on_change_slider(event)

    def on_change_slider(self, event: wx.Event) -> None:
        morph_name = self.bone_choice_ctrl.GetStringSelection()
        self.scales[morph_name].x = self.scale_x_slider.GetValue()
        self.scales[morph_name].y = self.scale_y_slider.GetValue()
        self.scales[morph_name].z = self.scale_z_slider.GetValue()
        self.degrees[morph_name].x = self.degree_x_slider.GetValue()
        self.degrees[morph_name].y = self.degree_y_slider.GetValue()
        self.degrees[morph_name].z = self.degree_z_slider.GetValue()
        self.positions[morph_name].x = self.position_x_slider.GetValue()
        self.positions[morph_name].y = self.position_y_slider.GetValue()
        self.positions[morph_name].z = self.position_z_slider.GetValue()
        self.bone_target_dress[morph_name] = self.bone_target_dress_check_ctrl.GetValue()

        self.parent.Enable(False)
        self.parent.on_change(morph_name)
        # ボーンハイライトを変更
        self.parent.change_bone(self.individual_target_bone_indexes[self.bone_choice_ctrl.GetSelection()])
        self.parent.Enable(True)

    def on_show_bone_weight(self, event: wx.Event) -> None:
        self.parent.Enable(False)
        # ボーンハイライトを変更
        self.parent.show_bone_weight(self.bone_weight_check_ctrl.GetValue())
        self.parent.Enable(True)

    def Enable(self, enable: bool) -> None:
        self.bone_choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.scale_x_slider.Enable(enable)
        self.scale_y_slider.Enable(enable)
        self.scale_z_slider.Enable(enable)
        self.degree_x_slider.Enable(enable)
        self.degree_y_slider.Enable(enable)
        self.degree_z_slider.Enable(enable)
        self.position_x_slider.Enable(enable)
        self.position_y_slider.Enable(enable)
        self.position_z_slider.Enable(enable)
        self.clear_btn_ctrl.Enable(enable)
        self.scale_link_ctrl.Enable(enable)
        self.bone_target_dress_check_ctrl.Enable(enable)
        self.bone_weight_check_ctrl.Enable(enable)
