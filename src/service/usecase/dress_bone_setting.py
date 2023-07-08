from enum import Enum

from mlib.pmx.bone_setting import BoneSetting, BoneSettings


class DressBoneSetting(BoneSetting):
    """ボーン設定"""

    def __init__(
        self,
        setting: BoneSetting,
        category: str,
        translatable: bool,
        rotatable: bool,
        local_scalable: bool,
        local_x_scalable: bool,
        global_scalable: bool = False,
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
        self.relatives = setting.relatives
        self.tails = setting.tails
        self.flag = setting.flag
        self.axis = setting.axis
        self.category = category
        self.translatable = translatable
        self.rotatable = rotatable
        self.local_x_scalable = local_x_scalable
        self.local_scalable = local_scalable
        self.global_scalable = global_scalable


class DressBoneSettings(Enum):
    """衣装用準標準ボーン設定一覧"""

    ROOT = DressBoneSetting(
        setting=BoneSettings.ROOT.value,
        category="全ての親",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    CENTER = DressBoneSetting(
        setting=BoneSettings.CENTER.value,
        category="センター",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    GROOVE = DressBoneSetting(
        setting=BoneSettings.GROOVE.value,
        category="グルーブ",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    WAIST = DressBoneSetting(
        setting=BoneSettings.WAIST.value,
        category="体幹",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
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
        # 回転はキャンセル用
        rotatable=True,
        local_scalable=False,
        local_x_scalable=False,
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
    UPPER3 = DressBoneSetting(
        setting=BoneSettings.UPPER3.value,
        category="体幹",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    ARM_CENTER = DressBoneSetting(
        setting=BoneSettings.ARM_CENTER.value,
        category="体幹",
        translatable=True,
        # 回転はキャンセル用
        rotatable=True,
        local_scalable=False,
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
        local_scalable=False,
        local_x_scalable=False,
    )
    EYES = DressBoneSetting(
        setting=BoneSettings.EYES.value,
        category="頭",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_EYE = DressBoneSetting(
        setting=BoneSettings.LEFT_EYE.value,
        category="頭",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_EYE = DressBoneSetting(
        setting=BoneSettings.RIGHT_EYE.value,
        category="頭",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )

    RIGHT_BUST = DressBoneSetting(
        setting=BoneSettings.RIGHT_BUST.value,
        category="胸",
        translatable=False,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=False,
        global_scalable=True,
    )
    RIGHT_SHOULDER_P = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER_P.value,
        category="肩",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_SHOULDER = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER.value,
        category="肩",
        translatable=False,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_SHOULDER_C = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER_C.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_ARM = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM.value,
        category="腕",
        translatable=False,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_ARM_TWIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_ARM_TWIST1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST1.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    RIGHT_ARM_TWIST2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST2.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    RIGHT_ARM_TWIST3 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST3.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    RIGHT_ELBOW = DressBoneSetting(
        setting=BoneSettings.RIGHT_ELBOW.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_HAND_TWIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_HAND_TWIST1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST1.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    RIGHT_HAND_TWIST2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST2.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    RIGHT_HAND_TWIST3 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST3.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    RIGHT_WRIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_WRIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=True,
        global_scalable=True,
    )
    RIGHT_THUMB0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_THUMB1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_THUMB2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_THUMB_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_INDEX0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_INDEX1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_INDEX2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_INDEX_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_MIDDLE0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_MIDDLE1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_MIDDLE2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_MIDDLE_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_RING0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_RING1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_RING2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_RING_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_PINKY0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_PINKY1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_PINKY2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_PINKY_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_WAIST_CANCEL = DressBoneSetting(
        setting=BoneSettings.RIGHT_WAIST_CANCEL.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_LEG = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    RIGHT_LEG_IK_PARENT = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_IK_PARENT.value,
        category="足IK親",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    RIGHT_LEG_IK = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_IK.value,
        category="足ＩＫ",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=True,
    )
    RIGHT_TOE_IK = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE_IK.value,
        category="つま先ＩＫ",
        translatable=True,
        rotatable=False,
        local_scalable=False,
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
        local_scalable=False,
        local_x_scalable=True,
    )
    RIGHT_TOE = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE.value,
        category="足首",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
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
        local_scalable=False,
        local_x_scalable=True,
        global_scalable=True,
    )
    RIGHT_TOE_EX = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE_EX.value,
        category="足首",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )

    LEFT_BUST = DressBoneSetting(
        setting=BoneSettings.LEFT_BUST.value,
        category="胸",
        translatable=False,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=False,
        global_scalable=True,
    )
    LEFT_SHOULDER_P = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER_P.value,
        category="肩",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_SHOULDER = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER.value,
        category="肩",
        translatable=False,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_SHOULDER_C = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER_C.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_ARM = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM.value,
        category="腕",
        translatable=False,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_ARM_TWIST = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_ARM_TWIST1 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST1.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    LEFT_ARM_TWIST2 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST2.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    LEFT_ARM_TWIST3 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST3.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    LEFT_ELBOW = DressBoneSetting(
        setting=BoneSettings.LEFT_ELBOW.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_HAND_TWIST = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_HAND_TWIST1 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST1.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    LEFT_HAND_TWIST2 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST2.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    LEFT_HAND_TWIST3 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST3.value,
        category="腕",
        translatable=True,
        rotatable=False,
        local_scalable=True,
        local_x_scalable=False,
    )
    LEFT_WRIST = DressBoneSetting(
        setting=BoneSettings.LEFT_WRIST.value,
        category="腕",
        translatable=True,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=True,
        global_scalable=True,
    )
    LEFT_THUMB0 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_THUMB1 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_THUMB2 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_THUMB_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_INDEX0 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_INDEX1 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_INDEX2 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_INDEX_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_MIDDLE0 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_MIDDLE1 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_MIDDLE2 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_MIDDLE_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_RING0 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_RING1 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_RING2 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_RING_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_RING_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_PINKY0 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY0.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_PINKY1 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY1.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_PINKY2 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY2.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_PINKY_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY_TAIL.value,
        category="指",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_WAIST_CANCEL = DressBoneSetting(
        setting=BoneSettings.LEFT_WAIST_CANCEL.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_LEG = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG.value,
        category="足",
        translatable=True,
        rotatable=True,
        local_scalable=True,
        local_x_scalable=True,
    )
    LEFT_LEG_IK_PARENT = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_IK_PARENT.value,
        category="足IK親",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )
    LEFT_LEG_IK = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_IK.value,
        category="足ＩＫ",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=True,
    )
    LEFT_TOE_IK = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE_IK.value,
        category="つま先ＩＫ",
        translatable=True,
        rotatable=False,
        local_scalable=False,
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
        local_scalable=False,
        local_x_scalable=True,
    )
    LEFT_TOE = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE.value,
        category="足首",
        translatable=True,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
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
        local_scalable=False,
        local_x_scalable=True,
        global_scalable=True,
    )
    LEFT_TOE_EX = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE_EX.value,
        category="足首",
        translatable=False,
        rotatable=False,
        local_scalable=False,
        local_x_scalable=False,
    )


DRESS_BONE_FITTING_NAME = "BoneFitting"
"""衣装フィッティング用ボーン"""

DRESS_STANDARD_BONE_NAMES: dict[str, DressBoneSetting] = dict([(bs.value.name, bs.value) for bs in DressBoneSettings])
"""衣装用準標準ボーン名前とEnumのキーの辞書"""


# IKはFKの後に指定する事
"""個別フィッティング用ボーン設定"""
FIT_INDIVIDUAL_BONE_NAMES = {
    "腰": (("腰",), ("下半身", "上半身", "上半身2", "上半身3"), ("下半身", "上半身", "上半身2", "上半身3"), []),
    "下半身": (("下半身",), [], ("足", "ひざ", "足首"), []),
    "上半身": (("上半身",), [], ("上半身2", "上半身3"), []),
    "上半身2": (("上半身2",), [], ("上半身3",), []),
    "上半身3": (("上半身3",), [], [], []),
    "胸": (("右胸", "左胸"), [], [], []),
    "首": (("首",), [], [], []),
    "頭": (("頭",), [], [], []),
    "肩": (("右肩", "左肩"), ("右肩P", "左肩P"), ("腕", "ひじ", "手のひら"), ("腕", "ひじ", "手のひら")),
    "腕": (("右腕", "左腕"), ("右肩C", "左肩C"), ("ひじ", "手のひら"), ("ひじ", "手のひら")),
    "ひじ": (("右ひじ", "左ひじ"), ("手のひら",), ("手のひら",), ("手のひら",)),
    "手のひら": (("右手首", "左手首"), [], [], []),
    "足": (("右足", "左足", "右足D", "左足D"), ("腰キャンセル左", "腰キャンセル右"), ("ひざ",), []),
    "ひざ": (("右ひざ", "左ひざ", "右ひざD", "左ひざD"), [], [], []),
    "足首": (("右足首", "左足首", "右足首D", "左足首D"), [], [], []),
}
