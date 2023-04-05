import wx
from mlib.form.frame.base_frame import BaseFrame


class MainFrame(BaseFrame):
    def __init__(self, app: wx.App, title: str, size: wx.Size, *args, **kw):
        super().__init__(app, title, size, *args, **kw)
