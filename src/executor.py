import argparse
from multiprocessing import freeze_support
import numpy as np
import wx
from mlib.utils.file_utils import get_path, get_root_dir
from form.main_frame import MainFrame
from mlib.base.logger import MLogger
from mlib.base.logger import LoggingMode

VERSION_NAME = "ver1.00.00_β01"

# 指数表記なし、有効小数点桁数6、30を超えると省略あり、一行の文字数200
np.set_printoptions(suppress=True, precision=6, threshold=30, linewidth=200)

# Windowsマルチプロセス対策
freeze_support()

if __name__ == "__main__":
    # 引数の取得
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", default=20, type=int)
    parser.add_argument("--log_mode", default=0, type=int)
    parser.add_argument("--out_log", default=0, type=int)
    parser.add_argument("--is_saving", default=1, type=int)
    parser.add_argument("--lang", default="ja_JP", type=str)
    args = parser.parse_args()

    # ロガーの初期化
    MLogger.initialize(args.lang, get_root_dir(), LoggingMode(args.log_mode), level=args.verbose)

    # アプリの起動
    app = wx.App(False)
    icon = wx.Icon(get_path("resources/pmx_dressup.ico"), wx.BITMAP_TYPE_ICO)
    frame = MainFrame(app, f"PmxDressup {VERSION_NAME}", wx.Size(600, 700))
    frame.SetIcon(icon)
    frame.Show(True)
    app.MainLoop()
