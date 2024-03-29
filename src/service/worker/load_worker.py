import logging
import os
from typing import Optional

import wx

from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_writer import PmxWriter
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_frame import BaseFrame
from mlib.utils.file_utils import get_root_dir
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.file_panel import FilePanel
from service.usecase.load_usecase import LoadUsecase

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class LoadWorker(BaseWorker):
    def __init__(self, frame: BaseFrame, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.frame.file_panel
        model: Optional[PmxModel] = None
        dress: Optional[PmxModel] = None
        motion: Optional[VmdMotion] = None
        individual_morph_names: list[str] = []

        is_model_change = False
        is_dress_change = False
        usecase = LoadUsecase()

        logger.info("お着替えモデル読み込み開始", decoration=MLogger.Decoration.BOX)

        if file_panel.model_ctrl.valid() and not file_panel.model_ctrl.data:
            logger.info("人物: 読み込み開始", decoration=MLogger.Decoration.BOX)

            original_model = file_panel.model_ctrl.reader.read_by_filepath(file_panel.model_ctrl.path)

            usecase.valid_model(original_model, "人物")

            model = original_model.copy()

            # 首根元にウェイトを振る
            usecase.replace_neck_root_weights(model)
            model.update_vertices_by_bone()

            # 人物に材質透明モーフを入れる
            logger.info("人物: 追加セットアップ: 材質透過モーフ追加")
            usecase.create_material_transparent_morphs(model)

            is_model_change = True
        elif file_panel.model_ctrl.original_data:
            original_model = file_panel.model_ctrl.original_data
            model = file_panel.model_ctrl.data
        else:
            original_model = PmxModel()
            model = PmxModel()

        if model and isinstance(model, PmxModel) and file_panel.dress_ctrl.valid() and (is_model_change or not file_panel.dress_ctrl.data):
            logger.info("衣装: 読み込み開始", decoration=MLogger.Decoration.BOX)

            original_dress = file_panel.dress_ctrl.reader.read_by_filepath(file_panel.dress_ctrl.path)

            usecase.valid_model(original_dress, "衣装")

            dress = original_dress.copy()
            dress.update_vertices_by_bone()

            logger.info("衣装: ボーン調整", decoration=MLogger.Decoration.BOX)

            # 不足ボーン追加
            logger.info("衣装: 不足ボーン調整", decoration=MLogger.Decoration.LINE)
            usecase.insert_mismatch_bones(model, dress)

            model_standard_positions, model_out_standard_positions = usecase.get_bone_positions(model)
            dress_standard_positions, dress_out_standard_positions = usecase.get_bone_positions(dress)

            replaced_bone_names: list[str] = []

            logger.info("衣装: 位置調整", decoration=MLogger.Decoration.LINE)

            # 上半身の再設定
            replaced_bone_names += usecase.replace_upper(model, dress)

            # 上半身2の再設定
            replaced_bone_names += usecase.replace_upper2(model, dress)

            # 上半身3の再設定
            replaced_bone_names += usecase.replace_upper3(model, dress)

            # # 胸の再設定
            # replaced_bust_bone_names = usecase.replace_bust(model, dress)

            # 首の再設定
            usecase.replace_neck(model, dress)

            # 肩と腕の再設定
            usecase.replace_shoulder_arm(model, dress)

            # 捩りの再設定
            usecase.replace_twist(model, dress, replaced_bone_names)

            # 下半身の再設定
            replaced_bone_names += usecase.replace_lower(model, dress)

            logger.info("衣装: ウェイト調整", decoration=MLogger.Decoration.LINE)

            # if replaced_bust_bone_names:
            #     dress.setup()
            #     usecase.replace_bust_weights(dress, replaced_bust_bone_names)

            if replaced_bone_names:
                dress.setup()
                dress.replace_standard_weights(replaced_bone_names)

            # 首根元にウェイトを振る
            usecase.replace_neck_root_weights(dress)
            dress.update_vertices_by_bone()

            # 衣装に材質透明モーフを入れる
            logger.info("衣装: 追加セットアップ: 材質透過モーフ追加", decoration=MLogger.Decoration.BOX)
            usecase.create_material_transparent_morphs(dress)

            # 個別調整用モーフ追加
            logger.info("衣装: 追加セットアップ: 個別調整ボーンモーフ追加", decoration=MLogger.Decoration.BOX)
            individual_morph_names, individual_target_bone_indexes = usecase.create_dress_individual_bone_morphs(dress)

            # 衣装にフィッティングボーンモーフを入れる
            logger.info("衣装: 追加セットアップ: フィッティングモーフ追加", decoration=MLogger.Decoration.BOX)
            usecase.create_dress_fit_morphs(
                model, dress, model_standard_positions, model_out_standard_positions, dress_standard_positions, dress_out_standard_positions
            )

            is_dress_change = True
        elif file_panel.dress_ctrl.original_data:
            original_dress = file_panel.dress_ctrl.original_data
            dress = file_panel.dress_ctrl.data
        else:
            original_dress = PmxModel()
            dress = PmxModel()

        if file_panel.motion_ctrl.valid() and (not file_panel.motion_ctrl.data or is_model_change or is_dress_change):
            logger.info("モーション読み込み開始", decoration=MLogger.Decoration.BOX)

            motion = file_panel.motion_ctrl.reader.read_by_filepath(file_panel.motion_ctrl.path)
        elif file_panel.motion_ctrl.original_data:
            motion = file_panel.motion_ctrl.original_data
        else:
            motion = VmdMotion("empty")

        if logger.total_level <= logging.DEBUG:
            # デバッグモードの時だけ変形モーフ付き衣装: データ保存
            from datetime import datetime

            out_path = os.path.join(os.path.dirname(file_panel.output_pmx_ctrl.path), f"{model.name}_{datetime.now():%Y%m%d_%H%M%S}.pmx")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            PmxWriter(model, out_path, include_system=True).save()
            logger.debug(f"人物: 出力: {out_path}")

            out_path = os.path.join(os.path.dirname(file_panel.output_pmx_ctrl.path), f"{dress.name}_{datetime.now():%Y%m%d_%H%M%S}.pmx")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            PmxWriter(dress, out_path, include_system=True).save()
            logger.debug(f"変形モーフ付き衣装: 出力: {out_path}")

        self.result_data = (original_model, model, original_dress, dress, motion, individual_morph_names, individual_target_bone_indexes)

        logger.info("お着替えモデル読み込み完了", decoration=MLogger.Decoration.BOX)

    def output_log(self):
        file_panel: FilePanel = self.frame.file_panel
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(file_panel.output_pmx_ctrl.path)}.log")
        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
