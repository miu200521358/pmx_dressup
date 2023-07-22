from datetime import datetime
import os

import wx

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_frame import BaseFrame
from mlib.utils.file_utils import get_root_dir, separate_path
from service.form.panel.config_panel import ConfigPanel
from service.form.panel.file_panel import FilePanel
from service.usecase.save_usecase import SaveUsecase

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class SaveWorker(BaseWorker):
    def __init__(self, frame: BaseFrame, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.frame.file_panel
        config_panel: ConfigPanel = self.frame.config_panel

        if not file_panel.model_ctrl.data:
            raise MApplicationException("人物モデルデータが読み込まれていません")

        if not file_panel.dress_ctrl.data:
            raise MApplicationException("衣装モデルデータが読み込まれていません")

        if not file_panel.output_pmx_ctrl.path or not os.path.exists(os.path.dirname(file_panel.output_pmx_ctrl.path)):
            logger.warning("出力ファイルパスが有効なパスではないため、デフォルトの出力ファイルパスを再設定します。")
            model_dir_path, model_file_name, model_file_ext = separate_path(file_panel.model_ctrl.path)
            dress_dir_path, dress_file_name, dress_file_ext = separate_path(file_panel.dress_ctrl.path)
            file_panel.output_pmx_ctrl.path = os.path.join(
                model_dir_path,
                dress_file_name,
                os.path.join(
                    model_dir_path,
                    f"{dress_file_name}_{datetime.now():%Y%m%d_%H%M%S}",
                    f"{file_panel.model_ctrl.name_ctrl.GetValue()[1:-1]}_{file_panel.dress_ctrl.name_ctrl.GetValue()[1:-1]}"
                    + model_file_ext,
                ),
            )

            os.makedirs(os.path.dirname(file_panel.output_pmx_ctrl.path), exist_ok=True)

        if not SaveUsecase().valid_output_path(
            file_panel.model_ctrl.data,
            file_panel.dress_ctrl.data,
            file_panel.output_pmx_ctrl.path,
        ):
            raise MApplicationException("お着替えモデル出力結果が元モデルデータを上書きする危険性があるため、出力を中断します\nお着替えモデル出力ファイルパスを変更してください")

        logger.info("お着替えモデル出力開始", decoration=MLogger.Decoration.BOX)

        SaveUsecase().save(
            file_panel.model_ctrl.data,
            file_panel.dress_ctrl.data,
            self.frame.model_motion,
            self.frame.dress_motion,
            file_panel.output_pmx_ctrl.path,
            config_panel.model_material_ctrl.alphas,
            config_panel.model_material_ctrl.is_override_colors,
            config_panel.model_material_ctrl.override_base_colors,
            config_panel.model_material_ctrl.override_materials,
            config_panel.dress_material_ctrl.alphas,
            config_panel.dress_material_ctrl.is_override_colors,
            config_panel.dress_material_ctrl.override_base_colors,
            config_panel.dress_material_ctrl.override_materials,
            config_panel.dress_bone_ctrl.scales,
            config_panel.dress_bone_ctrl.degrees,
            config_panel.dress_bone_ctrl.positions,
            config_panel.dress_bone_ctrl.bone_target_dress,
        )

        logger.info("*** お着替えモデル出力成功 ***\n出力先: {f}", f=file_panel.output_pmx_ctrl.path, decoration=MLogger.Decoration.BOX)

    def output_log(self):
        file_panel: FilePanel = self.frame.file_panel
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(file_panel.output_pmx_ctrl.path)}.log")

        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
