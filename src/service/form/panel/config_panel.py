import os
from typing import Optional

import wx

from mlib.base.logger import MLogger
from mlib.pmx.canvas import CanvasPanel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl
from service.form.widgets.bone_ctrl_set import BoneCtrlSet
from service.form.widgets.material_ctrl_set import MaterialCtrlSet

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ConfigPanel(CanvasPanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 0.6, 1.0, *args, **kw)

        self._initialize_ui()
        self._initialize_event()

    def _initialize_ui(self) -> None:
        self.config_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # 左にビューワー
        self.config_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        # --------------
        # 右に設定
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)

        # --------------

        self.scrolled_window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL,
        )
        self.scrolled_window.SetScrollRate(5, 5)

        self.window_sizer = wx.BoxSizer(wx.VERTICAL)

        # --------------
        # 再生

        self.play_sizer = wx.BoxSizer(wx.HORIZONTAL)

        frame_tooltip = __("モーションを指定している場合、任意のキーフレの結果の表示や再生ができます")

        self.frame_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("モーション"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.frame_title_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.frame_title_ctrl, 0, wx.ALL, 3)

        self.frame_ctrl = WheelSpinCtrl(
            self.scrolled_window, initial=0, min=0, max=10000, size=wx.Size(70, -1), change_event=self.on_frame_change
        )
        self.frame_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.frame_ctrl, 0, wx.ALL, 3)

        self.play_ctrl = wx.Button(self.scrolled_window, wx.ID_ANY, __("再生"), wx.DefaultPosition, wx.Size(80, -1))
        self.play_ctrl.SetToolTip(__("モーションを指定している場合、再生することができます"))
        self.play_sizer.Add(self.play_ctrl, 0, wx.ALL, 3)

        self.window_sizer.Add(self.play_sizer, 0, wx.ALL, 3)

        # --------------
        # 材質非透過度

        self.model_material_ctrl = MaterialCtrlSet(self, self.scrolled_window, "人物")
        self.window_sizer.Add(self.model_material_ctrl.sizer, 0, wx.ALL, 3)

        self.dress_material_ctrl = MaterialCtrlSet(self, self.scrolled_window, "衣装")
        self.window_sizer.Add(self.dress_material_ctrl.sizer, 0, wx.ALL, 3)

        self.canvas.color_changed_event = self.on_change_color

        # --------------
        # ボーン調整

        self.dress_bone_sizer = wx.StaticBoxSizer(wx.StaticBox(self.scrolled_window, wx.ID_ANY, __("衣装:ボーン別調整")), orient=wx.VERTICAL)

        self.dress_bone_ctrl = BoneCtrlSet(self, self.scrolled_window, self.dress_bone_sizer)

        self.window_sizer.Add(self.dress_bone_sizer, 1, wx.ALL, 3)

        self.dress_bone_sizer.SetMinSize((self.scrolled_window.GetSize()[0], -1))
        self.dress_bone_sizer.Fit(self.scrolled_window)
        self.dress_bone_sizer.SetSizeHints(self.scrolled_window)

        # --------------

        self.scrolled_window.SetSizer(self.window_sizer)
        self.right_sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

        self.config_sizer.Add(self.right_sizer, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 0)
        self.root_sizer.Add(self.config_sizer, 0, wx.ALL, 0)

        self.SetSizer(self.root_sizer)
        self.fit()

    def fit(self) -> None:
        self.scrolled_window.Layout()
        self.Layout()
        self.frame.fit()

    def _initialize_event(self) -> None:
        self.play_ctrl.Bind(wx.EVT_BUTTON, self.on_play)
        # self.model_material_choice_ctrl.Bind(wx.EVT_LISTBOX, self.on_change)
        # self.dress_material_choice_ctrl.Bind(wx.EVT_LISTBOX, self.on_change)

    def on_play(self, event: wx.Event) -> None:
        if self.canvas.playing:
            self.stop_play()
        else:
            self.start_play()
        self.canvas.on_play(event)

    def on_change_color(self):
        if self.dress_material_ctrl.is_dropper:
            # 衣装の色抽出中のみピックアップ
            self.dress_material_ctrl.color_picker_ctrl.SetColour(wx.Colour(*self.canvas.color))
            self.dress_material_ctrl.color_picker_ctrl.Refresh()
            self.dress_material_ctrl.picked_override_color(wx.EVT_COLOUR_CHANGED)
        elif self.model_material_ctrl.is_dropper:
            # 人物の色抽出中のみピックアップ
            self.model_material_ctrl.color_picker_ctrl.SetColour(wx.Colour(*self.canvas.color))
            self.model_material_ctrl.color_picker_ctrl.Refresh()
            self.model_material_ctrl.picked_override_color(wx.EVT_COLOUR_CHANGED)

    @property
    def fno(self) -> int:
        return self.frame_ctrl.GetValue()

    @fno.setter
    def fno(self, v: int) -> None:
        self.frame_ctrl.SetValue(v)

    def stop_play(self) -> None:
        self.play_ctrl.SetLabelText(__("再生"))
        self.Enable(True)

    def start_play(self) -> None:
        self.play_ctrl.SetLabelText(__("停止"))
        self.Enable(False)
        # 停止ボタンだけは有効
        self.play_ctrl.Enable(True)

    def on_resize(self) -> None:
        frame_w, frame_h = self.frame.GetClientSize()
        self.scrolled_window.SetPosition(wx.Point(self.canvas.size.width, 0))
        self.scrolled_window.SetSize(wx.Size(frame_w - self.canvas.size.width, frame_h))
        self.fit()

    def Enable(self, enable: bool):
        self.frame_ctrl.Enable(enable)
        self.play_ctrl.Enable(enable)
        self.model_material_ctrl.Enable(enable)
        self.dress_material_ctrl.Enable(enable)
        self.dress_bone_ctrl.Enable(enable)

    def on_frame_change(self, event: wx.Event) -> None:
        self.frame.fit_model_motion(self.model_material_ctrl.alphas.get(__("ボーンライン"), 0.5))
        self.frame.fit_dress_motion(self.dress_material_ctrl.alphas.get(__("ボーンライン"), 0.5))

    def on_change_morph(self, target_bone_name: Optional[str] = None) -> None:
        self.change_motion(False, target_bone_name)

    def on_change(self, target_bone_name: Optional[str] = None, is_clear: bool = False) -> None:
        self.change_motion(True, target_bone_name)

    def show_bone_weight(self, is_show_bone_weight: bool) -> None:
        # 人物側も薄くする
        model_bone_ratio = 0.2 if is_show_bone_weight else 0.5
        if is_show_bone_weight:
            self.frame.set_model_motion_morphs({__("全材質"): 0.3})
        else:
            self.frame.clear_model_opacity()

        self.frame.fit_model_motion(bone_alpha=model_bone_ratio, is_bone_deform=False)

        self.frame.show_bone_weight(is_show_bone_weight)

    def change_bone(self, selected_bone_indexes: list[int]) -> None:
        self.frame.change_bone(selected_bone_indexes)

    def change_motion(self, is_bone_deform: bool, target_bone_name: Optional[str] = None) -> None:
        self.frame.set_model_motion_morphs(self.model_material_ctrl.alphas)
        self.frame.fit_model_motion(self.model_material_ctrl.alphas.get(__("ボーンライン"), 0.5), is_bone_deform)

        self.frame.set_dress_motion_morphs(
            self.dress_material_ctrl.alphas,
            self.dress_bone_ctrl.scales,
            self.dress_bone_ctrl.degrees,
            self.dress_bone_ctrl.positions,
        )
        # self.frame.clear_refit()
        # if target_bone_name:
        #     self.frame.refit(target_bone_name)
        self.frame.fit_dress_motion(self.dress_material_ctrl.alphas.get(__("ボーンライン"), 0.5), is_bone_deform)

    def show_only_material(self, type_name: str, material_name: str) -> None:
        model_material_alphas: dict[str, float] = {}
        for model_material_name in self.model_material_ctrl.alphas.keys():
            if type_name == "人物" and material_name == model_material_name:
                model_material_alphas[model_material_name] = 1.0
            elif model_material_name in (__("全材質"), __("ボーンライン")):
                model_material_alphas[model_material_name] = self.model_material_ctrl.alphas.get(model_material_name, 1.0)
            else:
                model_material_alphas[model_material_name] = 0.0

        self.frame.set_model_motion_morphs(model_material_alphas)
        self.frame.fit_model_motion(self.model_material_ctrl.alphas.get(__("ボーンライン"), 0.5), False)

        dress_material_alphas: dict[str, float] = {}
        for dress_material_name in self.dress_material_ctrl.alphas.keys():
            if type_name == "衣装" and material_name == dress_material_name:
                dress_material_alphas[dress_material_name] = 1.0
            elif dress_material_name in (__("全材質"), __("ボーンライン")):
                dress_material_alphas[dress_material_name] = self.dress_material_ctrl.alphas.get(dress_material_name, 1.0)
            else:
                dress_material_alphas[dress_material_name] = 0.0

        self.frame.set_dress_motion_morphs(
            dress_material_alphas,
            self.dress_bone_ctrl.scales,
            self.dress_bone_ctrl.degrees,
            self.dress_bone_ctrl.positions,
        )
        self.frame.fit_dress_motion(self.dress_material_ctrl.alphas.get(__("ボーンライン"), 0.5), False)
