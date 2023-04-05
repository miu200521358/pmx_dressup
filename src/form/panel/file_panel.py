from mlib.form.base_panel import BasePanel
from mlib.form.base_frame import BaseFrame


class FilePanel(BasePanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, *args, **kw)
