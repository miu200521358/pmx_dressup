from multiprocessing import freeze_support
import numpy as np

VERSION_NAME = "ver5.01.09_β01"

# 指数表記なし、有効小数点桁数6、30を超えると省略あり、一行の文字数200
np.set_printoptions(suppress=True, precision=6, threshold=30, linewidth=200)

# Windowsマルチプロセス対策
freeze_support()

if __name__ == "__main__":
    pass
