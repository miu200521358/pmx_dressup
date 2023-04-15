import os

import wx

from mlib.base.logger import MLogger
from mlib.base.math import MVector3D
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.parts.spin_ctrl import WheelSpinCtrl, WheelSpinCtrlDouble
from mlib.pmx.canvas import CanvasPanel
from mlib.service.form.parts.float_slider_ctrl import FloatSliderCtrl

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

    def play_stop(self):
        self.play_ctrl.SetLabelText("Play")

    def on_frame_change(self, event: wx.Event):
        self.frame.fit_model_motion(self.model_material_ctrl.alphas.get(__("ボーンライン"), 1.0))
        self.frame.fit_dress_motion(self.dress_material_ctrl.alphas.get(__("ボーンライン"), 1.0))

    def on_change(self, event: wx.Event):
        axis_scale_sets: dict[str, MVector3D] = {}
        axis_scale_sets["ALL"] = self.all_axis_set.get_scale()

        self.frame.set_model_motion_morphs(self.model_material_ctrl.alphas)
        self.frame.fit_model_motion(self.model_material_ctrl.alphas.get(__("ボーンライン"), 1.0))

        self.frame.set_dress_motion_morphs(axis_scale_sets, self.dress_material_ctrl.alphas)
        self.frame.fit_dress_motion(self.dress_material_ctrl.alphas.get(__("ボーンライン"), 1.0))


class MaterialCtrlSet:
    def __init__(self, parent: ConfigPanel, window: wx.ScrolledWindow, sizer: wx.Sizer, type_name: str) -> None:
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
            __(f"スライダーで調整対象となる{type_name}の材質です。\n「ボーンライン」はボーンを表す線を示します。\n透過度0の状態でエクスポートすると、お着替え結果には出力されません\n(ボーンラインは常に出力されません)")
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
            change_event=self.on_change_alpha,
        )
        self.sizer.Add(self.slider.sizer, 0, wx.ALL, 3)

    def initialize(self, material_names: list[str]):
        self.material_choice_ctrl.Clear()
        for material_name in material_names:
            self.material_choice_ctrl.Append(material_name)
            self.alphas[material_name] = 1.0
        # 最後にボーンの透過度も調整出来るようにしておく
        self.material_choice_ctrl.Append(__("ボーンライン"))
        self.alphas[__("ボーンライン")] = 1.0
        self.material_choice_ctrl.SetSelection(0)
        self.slider.SetValue(1.0)

    def on_change_material(self, event: wx.Event):
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.slider.SetValue(self.alphas[material_name])

    def on_change_alpha(self, event: wx.Event):
        alpha = self.slider.GetValue()
        material_name = self.material_choice_ctrl.GetStringSelection()
        self.alphas[material_name] = float(alpha)
        self.parent.on_change(event)

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


class AxisCtrlSet:
    def __init__(self, parent: ConfigPanel, window: wx.ScrolledWindow, sizer: wx.Sizer, type_name: str) -> None:
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
