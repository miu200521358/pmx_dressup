from enum import Enum

from mlib.pmx.bone_setting import BoneSetting, BoneSettings


class DressBoneSetting(BoneSetting):
    """ボーン設定"""

    def __init__(
        self,
        setting: BoneSetting,
        category: str,
        translatable: bool = False,
        rotatable: bool = False,
        local_scalable: bool = False,
        local_x_scalable: bool = False,
        global_scalable: bool = False,
        rotate_cancel: bool = False,
    ) -> None:
        """
        category : 種類名
        translatable: 移動可能か
        rotatable: 回転可能か
        local_x_scalable=ローカルX方向のスケーリング可能か
        local_scalable: ローカルスケーリング可能か
        global_scalable: グローバルスケール可能か
        """
        self.name = setting.name
        self.parents = setting.parents
        self.display_tail = setting.display_tail
        self.tails = setting.tails
        self.flag = setting.flag
        self.category = category
        self.translatable = translatable
        self.rotatable = rotatable
        self.local_x_scalable = local_x_scalable
        self.local_scalable = local_scalable
        self.global_scalable = global_scalable
        self.rotate_cancel = rotate_cancel


class DressBoneSettings(Enum):
    """衣装用準標準ボーン設定一覧"""

    ROOT = DressBoneSetting(
        setting=BoneSettings.ROOT.value,
        category="全ての親",
    )
    CENTER = DressBoneSetting(
        setting=BoneSettings.CENTER.value,
        category="センター",
        translatable=True,
    )
    GROOVE = DressBoneSetting(
        setting=BoneSettings.GROOVE.value,
        category="グルーブ",
        translatable=True,
    )
    WAIST = DressBoneSetting(
        setting=BoneSettings.WAIST.value,
        category="体幹",
        translatable=True,
    )
    LOWER = DressBoneSetting(
        setting=BoneSettings.LOWER.value,
        category="体幹",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEG_CENTER = DressBoneSetting(
        setting=BoneSettings.LEG_CENTER.value,
        category="体幹",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    UPPER = DressBoneSetting(
        setting=BoneSettings.UPPER.value,
        category="体幹",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    UPPER2 = DressBoneSetting(
        setting=BoneSettings.UPPER2.value,
        category="体幹",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    NECK = DressBoneSetting(
        setting=BoneSettings.NECK.value,
        category="首",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    HEAD = DressBoneSetting(
        setting=BoneSettings.HEAD.value,
        category="頭",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    EYES = DressBoneSetting(
        setting=BoneSettings.EYES.value,
        category="頭",
    )
    LEFT_EYE = DressBoneSetting(
        setting=BoneSettings.LEFT_EYE.value,
        category="頭",
    )
    RIGHT_EYE = DressBoneSetting(
        setting=BoneSettings.RIGHT_EYE.value,
        category="頭",
    )

    RIGHT_BUST = DressBoneSetting(
        setting=BoneSettings.RIGHT_BUST.value,
        category="胸",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    RIGHT_SHOULDER_ROOT = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER_ROOT.value,
        category="肩",
        translatable=True,
    )
    RIGHT_SHOULDER_P = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER_P.value,
        category="肩",
        translatable=True,
    )
    RIGHT_SHOULDER = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER.value,
        category="肩",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_SHOULDER_C = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER_C.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    RIGHT_ARM = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_ARM_TWIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_ARM_TWIST1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST1.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    RIGHT_ARM_TWIST2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST2.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    RIGHT_ARM_TWIST3 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST3.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    RIGHT_ELBOW = DressBoneSetting(
        setting=BoneSettings.RIGHT_ELBOW.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_HAND_TWIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_HAND_TWIST1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST1.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    RIGHT_HAND_TWIST2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST2.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    RIGHT_HAND_TWIST3 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST3.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    RIGHT_WRIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_WRIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_THUMB0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_THUMB1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_THUMB2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_THUMB_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_INDEX0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_INDEX1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_INDEX2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_INDEX_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_MIDDLE0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_MIDDLE1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_MIDDLE2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_MIDDLE_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_RING0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_RING1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_RING2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_RING_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_PINKY0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_PINKY1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_PINKY2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_PINKY_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_WAIST_CANCEL = DressBoneSetting(
        setting=BoneSettings.RIGHT_WAIST_CANCEL.value,
        category="足",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    RIGHT_LEG = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_KNEE = DressBoneSetting(
        setting=BoneSettings.RIGHT_KNEE.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_ANKLE = DressBoneSetting(
        setting=BoneSettings.RIGHT_ANKLE.value,
        category="足首",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_x_scalable=True,
    )
    RIGHT_TOE = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE.value,
        category="足首",
        translatable=True,
    )
    RIGHT_LEG_D = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_D.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_KNEE_D = DressBoneSetting(
        setting=BoneSettings.RIGHT_KNEE_D.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_ANKLE_D = DressBoneSetting(
        setting=BoneSettings.RIGHT_ANKLE_D.value,
        category="足首",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_x_scalable=True,
    )
    RIGHT_TOE_EX = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE_EX.value,
        category="足首",
    )
    RIGHT_LEG_IK_PARENT = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_IK_PARENT.value,
        category="足IK親",
        translatable=True,
    )
    RIGHT_LEG_IK = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_IK.value,
        category="足ＩＫ",
        translatable=True,
        local_x_scalable=True,
    )
    RIGHT_TOE_IK = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE_IK.value,
        category="つま先ＩＫ",
        translatable=True,
        local_x_scalable=True,
    )

    LEFT_BUST = DressBoneSetting(
        setting=BoneSettings.LEFT_BUST.value,
        category="胸",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    LEFT_SHOULDER_ROOT = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER_ROOT.value,
        category="肩",
        translatable=True,
    )
    LEFT_SHOULDER_P = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER_P.value,
        category="肩",
        translatable=True,
    )
    LEFT_SHOULDER = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER.value,
        category="肩",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_SHOULDER_C = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER_C.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    LEFT_ARM = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_ARM_TWIST = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_ARM_TWIST1 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST1.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    LEFT_ARM_TWIST2 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST2.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    LEFT_ARM_TWIST3 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST3.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    LEFT_ELBOW = DressBoneSetting(
        setting=BoneSettings.LEFT_ELBOW.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_HAND_TWIST = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_HAND_TWIST1 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST1.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    LEFT_HAND_TWIST2 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST2.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    LEFT_HAND_TWIST3 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST3.value,
        category="腕",
        translatable=True,
        local_scalable=True,
    )
    LEFT_WRIST = DressBoneSetting(
        setting=BoneSettings.LEFT_WRIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_THUMB0 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_THUMB1 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_THUMB2 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_THUMB_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_INDEX0 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_INDEX1 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_INDEX2 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_INDEX_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_MIDDLE0 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_MIDDLE1 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_MIDDLE2 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_MIDDLE_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_RING0 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_RING1 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_RING2 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_RING_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_RING_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_PINKY0 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY0.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_PINKY1 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY1.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_PINKY2 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY2.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_PINKY_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY_TAIL.value,
        category="指",
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_WAIST_CANCEL = DressBoneSetting(
        setting=BoneSettings.LEFT_WAIST_CANCEL.value,
        category="足",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
    )
    LEFT_LEG = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_KNEE = DressBoneSetting(
        setting=BoneSettings.LEFT_KNEE.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_ANKLE = DressBoneSetting(
        setting=BoneSettings.LEFT_ANKLE.value,
        category="足首",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_x_scalable=True,
    )
    LEFT_TOE = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE.value,
        category="足首",
        translatable=True,
    )
    LEFT_LEG_D = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_D.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_KNEE_D = DressBoneSetting(
        setting=BoneSettings.LEFT_KNEE_D.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_ANKLE_D = DressBoneSetting(
        setting=BoneSettings.LEFT_ANKLE_D.value,
        category="足首",
        translatable=True,
        rotatable=True,
        rotate_cancel=True,
        local_x_scalable=True,
    )
    LEFT_TOE_EX = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE_EX.value,
        category="足首",
    )
    LEFT_LEG_IK_PARENT = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_IK_PARENT.value,
        category="足IK親",
        translatable=True,
    )
    LEFT_LEG_IK = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_IK.value,
        category="足ＩＫ",
        translatable=True,
        local_x_scalable=True,
    )
    LEFT_TOE_IK = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE_IK.value,
        category="つま先ＩＫ",
        translatable=True,
        local_x_scalable=True,
    )


DRESS_BONE_FITTING_NAME = "BoneFitting"
"""衣装フィッティング用ボーン"""

DRESS_STANDARD_BONE_NAMES: dict[str, DressBoneSetting] = dict([(bs.value.name, bs.value) for bs in DressBoneSettings])
"""衣装用準標準ボーン名前とEnumのキーの辞書"""


class FitMorphSetting:
    def __init__(
        self,
        name: str,
        target_bone_names: list[str],
        move_target_bone_names: list[str],
        child_move_morph_names: list[str],
        child_rotation_morph_names: list[str],
        child_scale_morph_names: list[str],
        attend_weight_bone_names: list[str],
    ) -> None:
        """
        name: モーフ名
        target_bone_names: 処理対象ボーン名
        move_target_bone_names: 移動対象ボーン名
        child_move_morph_names: 一緒に移動するボーン名
        child_rotation_morph_names: 一緒に回転するモーフ名
        child_scale_morph_names: 一緒にスケーリングするモーフ名
        attend_weight_bone_names: 付随して表示するボーン名
        """
        self.name = name
        self.target_bone_names = target_bone_names
        self.move_target_bone_names = move_target_bone_names
        self.child_move_morph_names = child_move_morph_names
        self.child_rotation_morph_names = child_rotation_morph_names
        self.child_scale_morph_names = child_scale_morph_names
        self.attend_weight_bone_names = attend_weight_bone_names


class FitMorphSettings(Enum):
    """個別フィッティング用ボーン設定"""

    WAIST = FitMorphSetting(
        name="腰",
        target_bone_names=["腰"],
        move_target_bone_names=[],
        child_move_morph_names=["下半身", "上半身", "上半身2"],
        child_rotation_morph_names=[],
        child_scale_morph_names=["下半身", "上半身", "上半身2"],
        attend_weight_bone_names=[],
    )

    LOWER = FitMorphSetting(
        name="下半身",
        target_bone_names=["下半身"],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )

    UPPER = FitMorphSetting(
        name="上半身",
        target_bone_names=["上半身"],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=["上半身2"],
        attend_weight_bone_names=[],
    )

    UPPER2 = FitMorphSetting(
        name="上半身2",
        target_bone_names=["上半身2"],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )

    BUST = FitMorphSetting(
        name="胸",
        target_bone_names=["右胸", "左胸"],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )

    NECK = FitMorphSetting(
        name="首",
        target_bone_names=["首"],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )

    HEAD = FitMorphSetting(
        name="頭",
        target_bone_names=["頭"],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )

    SHOULDER = FitMorphSetting(
        name="肩",
        target_bone_names=["右肩", "左肩"],
        move_target_bone_names=["右肩P", "左肩P"],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )

    ARM = FitMorphSetting(
        name="腕",
        target_bone_names=["右腕", "左腕"],
        move_target_bone_names=[
            "右肩C",
            "左肩C",
            "左腕捩",
            "左腕捩1",
            "左腕捩2",
            "左腕捩3",
            "右腕捩",
            "右腕捩1",
            "右腕捩2",
            "右腕捩3",
        ],
        child_move_morph_names=["ひじ", "手首", "指"],
        child_rotation_morph_names=["ひじ", "手首", "指"],
        child_scale_morph_names=["ひじ", "手首", "指"],
        attend_weight_bone_names=[],
    )

    ELBOW = FitMorphSetting(
        name="ひじ",
        target_bone_names=["右ひじ", "左ひじ"],
        move_target_bone_names=[
            "左手捩",
            "左手捩1",
            "左手捩2",
            "左手捩3",
            "右手捩",
            "右手捩1",
            "右手捩2",
            "右手捩3",
        ],
        child_move_morph_names=["手首", "指"],
        child_rotation_morph_names=["手首", "指"],
        child_scale_morph_names=["手首", "指"],
        attend_weight_bone_names=[],
    )

    WRIST = FitMorphSetting(
        name="手首",
        target_bone_names=["右手首", "左手首"],
        move_target_bone_names=[],
        child_move_morph_names=["指"],
        child_scale_morph_names=["指"],
        child_rotation_morph_names=["指"],
        attend_weight_bone_names=[],
    )

    FINGER = FitMorphSetting(
        name="指",
        target_bone_names=[
            "左親指０",
            "左親指１",
            "左親指２",
            "左親指先",
            "左人指１",
            "左人指２",
            "左人指３",
            "左人指先",
            "左中指１",
            "左中指２",
            "左中指３",
            "左中指先",
            "左薬指１",
            "左薬指２",
            "左薬指３",
            "左薬指先",
            "左小指１",
            "左小指２",
            "左小指３",
            "左小指先",
            "右親指０",
            "右親指１",
            "右親指２",
            "右親指先",
            "右人指１",
            "右人指２",
            "右人指３",
            "右人指先",
            "右中指１",
            "右中指２",
            "右中指３",
            "右中指先",
            "右薬指１",
            "右薬指２",
            "右薬指３",
            "右薬指先",
            "右小指１",
            "右小指２",
            "右小指３",
            "右小指先",
        ],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_scale_morph_names=[],
        child_rotation_morph_names=[],
        attend_weight_bone_names=[],
    )

    LEG = FitMorphSetting(
        name="足",
        target_bone_names=["右足", "左足", "右足D", "左足D"],
        move_target_bone_names=["腰キャンセル左", "腰キャンセル右"],
        child_move_morph_names=["ひざ"],
        child_rotation_morph_names=["ひざ"],
        child_scale_morph_names=["ひざ"],
        attend_weight_bone_names=[],
    )

    KNEE = FitMorphSetting(
        name="ひざ",
        target_bone_names=["右ひざ", "左ひざ", "右ひざD", "左ひざD"],
        move_target_bone_names=[],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )

    ANKLE = FitMorphSetting(
        name="足首",
        target_bone_names=["右足首", "左足首", "右足首D", "左足首D"],
        move_target_bone_names=["右足先EX", "左足先EX"],
        child_move_morph_names=[],
        child_rotation_morph_names=[],
        child_scale_morph_names=[],
        attend_weight_bone_names=[],
    )


FIT_INDIVIDUAL_MORPH_NAMES: dict[str, FitMorphSetting] = dict([(bs.value.name, bs.value) for bs in FitMorphSettings])
"""個別調整用モーフ名とEnumのキーの辞書"""
