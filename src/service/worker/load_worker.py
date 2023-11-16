import logging
import os
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, as_completed, wait

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

        logger.info("お着替えモデル読み込み開始", decoration=MLogger.Decoration.BOX)

        # まずは読み込み
        (
            model,
            original_model,
            dress,
            original_dress,
            motion,
        ) = self.load()

        # フィッティング
        usecase = LoadUsecase()
        individual_morph_names, individual_target_bone_indexes = usecase.fit(
            model, dress
        )

        # individual_morph_names, individual_target_bone_indexes, motion = self.fit(
        #     model, dress, motion
        # )

        if logger.total_level <= logging.DEBUG:
            # デバッグモードの時だけ変形モーフ付き衣装: データ保存
            from datetime import datetime

            out_path = os.path.join(
                os.path.dirname(file_panel.output_pmx_ctrl.path),
                f"{model.name}_{datetime.now():%Y%m%d_%H%M%S}.pmx",
            )
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            PmxWriter(model, out_path, include_system=True).save()
            logger.debug(f"人物: 出力: {out_path}")

            out_path = os.path.join(
                os.path.dirname(file_panel.output_pmx_ctrl.path),
                f"{dress.name}_{datetime.now():%Y%m%d_%H%M%S}.pmx",
            )
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            PmxWriter(dress, out_path, include_system=True).save()
            logger.debug(f"変形モーフ付き衣装: 出力: {out_path}")

        self.result_data = (
            original_model,
            model,
            original_dress,
            dress,
            motion,
            individual_morph_names,
            individual_target_bone_indexes,
        )

        logger.info("お着替えモデル読み込み完了", decoration=MLogger.Decoration.BOX)

    def output_log(self):
        file_panel: FilePanel = self.frame.file_panel
        output_log_path = os.path.join(
            get_root_dir(), f"{os.path.basename(file_panel.output_pmx_ctrl.path)}.log"
        )
        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)

    def load(
        self,
    ) -> tuple[PmxModel, PmxModel, PmxModel, PmxModel, VmdMotion]:
        """データ読み込み"""
        usecase = LoadUsecase()
        file_panel: FilePanel = self.frame.file_panel

        with ThreadPoolExecutor(
            thread_name_prefix="load", max_workers=self.max_worker
        ) as executor:
            model_future = executor.submit(
                usecase.load_model,
                file_panel.model_ctrl.valid() and not file_panel.model_ctrl.data,
                file_panel.model_ctrl.path,
                True,
            )

            dress_future = executor.submit(
                usecase.load_model,
                file_panel.dress_ctrl.valid() and not file_panel.dress_ctrl.data,
                file_panel.dress_ctrl.path,
                False,
            )

            motion_future = executor.submit(
                usecase.load_motion,
                file_panel.motion_ctrl.valid() and not file_panel.motion_ctrl.data,
                file_panel.motion_ctrl.path,
            )

        wait([model_future, dress_future, motion_future], return_when=FIRST_EXCEPTION)

        if as_completed(model_future):
            if model_future.exception():
                raise model_future.exception()
            model, original_model = model_future.result()

        if as_completed(dress_future):
            if dress_future.exception():
                raise dress_future.exception()
            dress, original_dress = dress_future.result()

        if as_completed(motion_future):
            if motion_future.exception():
                raise motion_future.exception()
            motion = motion_future.result()

        return model, original_model, dress, original_dress, motion

    def fit(
        self, model: PmxModel, dress: PmxModel, motion: VmdMotion
    ) -> tuple[list[str], list[list[int]], VmdMotion]:
        usecase = LoadUsecase()

        with ThreadPoolExecutor(
            thread_name_prefix="load", max_workers=self.max_worker
        ) as executor:
            model_future = executor.submit(usecase.fit, model, dress)

            ik_target_bone_names = [
                bone.name for bone in model.bones if bone.ik_target_indexes
            ]

            motion_future = executor.submit(
                motion.animate_bone,
                [
                    fno
                    for fno in range(
                        0, motion.max_fno, (10 if self.max_worker == 1 else 5)
                    )
                ],
                model,
                ik_target_bone_names,
                out_fno_log=True,
                description=__("IK事前計算"),
            )

        wait([model_future, motion_future], return_when=FIRST_EXCEPTION)

        if as_completed(model_future):
            if model_future.exception():
                raise model_future.exception()
            (
                individual_morph_names,
                individual_target_bone_indexes,
            ) = model_future.result()

        if as_completed(motion_future):
            if motion_future.exception():
                raise motion_future.exception()
            motion_future.result()

        return individual_morph_names, individual_target_bone_indexes, motion
