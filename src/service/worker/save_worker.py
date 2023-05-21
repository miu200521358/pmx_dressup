import os

import wx

from mlib.base.logger import MLogger
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_panel import BasePanel
from mlib.utils.file_utils import get_root_dir
from service.form.panel.config_panel import ConfigPanel
from service.form.panel.file_panel import FilePanel
from service.usecase.save_usecase import SaveUsecase

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class SaveWorker(BaseWorker):
    def __init__(self, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.panel
        config_panel: ConfigPanel = self.panel.frame.config_panel

        logger.info("お着替えモデル出力開始", decoration=MLogger.Decoration.BOX)

        SaveUsecase().save(
            file_panel.model_ctrl.data,
            file_panel.dress_ctrl.data,
            file_panel.output_pmx_ctrl.path,
            config_panel.model_material_ctrl.alphas,
            config_panel.dress_material_ctrl.alphas,
            config_panel.dress_bone_ctrl.scales,
            config_panel.dress_bone_ctrl.degrees,
            config_panel.dress_bone_ctrl.positions,
        )

        logger.info("*** お着替えモデル出力成功 ***\n出力先: {f}", f=file_panel.output_pmx_ctrl.path, decoration=MLogger.Decoration.BOX)

    def output_log(self):
        file_panel: FilePanel = self.panel
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(file_panel.output_pmx_ctrl.path)}.log")

        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
