from enum import Enum
from typing import Iterable

from mlib.pmx.bone_setting import BoneSetting, BoneSettings


class DressBoneSetting(BoneSetting):
    """ボーン設定"""

    def __init__(
        self,
        setting: BoneSetting,
        category: str,
        weight_names: Iterable[str],
        translatable: bool,
        rotatable: bool,
        global_scalable: bool,
        local_scalable: bool,
        local_scale_target: bool,
    ) -> None:
        """
        category : 種類名
        weight_names: 同一ウェイトで扱うボーン名リスト
        translatable: 移動可能か
        rotatable: 回転可能か
        global_scalable: グローバルスケール可能か
        local_scalable: ローカルスケーリング可能か
        local_scale_target: ローカルスケーリング用ウェイト計算の対象か
        """
        self.name = setting.name
        self.parents = setting.parents
        self.relatives = setting.relatives
        self.tails = setting.tails
        self.flag = setting.flag
        self.axis = setting.axis
        self.category = category
        self.weight_names = weight_names
        self.translatable = translatable
        self.rotatable = rotatable
        self.global_scalable = global_scalable
        self.local_scalable = local_scalable
        self.local_scale_target = local_scale_target


class DressBoneSettings(Enum):
    """衣装用準標準ボーン設定一覧"""

    ROOT = DressBoneSetting(
        setting=BoneSettings.ROOT.value,
        category="全ての親",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    CENTER = DressBoneSetting(
        setting=BoneSettings.CENTER.value,
        category="センター",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    GROOVE = DressBoneSetting(
        setting=BoneSettings.GROOVE.value,
        category="グルーブ",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    WAIST = DressBoneSetting(
        setting=BoneSettings.WAIST.value,
        category="体幹",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LOWER = DressBoneSetting(
        setting=BoneSettings.LOWER.value,
        category="体幹",
        weight_names=("下半身",),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEG_CENTER = DressBoneSetting(
        setting=BoneSettings.LEG_CENTER.value,
        category="体幹",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    UPPER = DressBoneSetting(
        setting=BoneSettings.UPPER.value,
        category="体幹",
        weight_names=("上半身",),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    UPPER2 = DressBoneSetting(
        setting=BoneSettings.UPPER2.value,
        category="体幹",
        weight_names=("上半身2", "左胸", "右胸", "首根元"),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    UPPER3 = DressBoneSetting(
        setting=BoneSettings.UPPER3.value,
        category="体幹",
        weight_names=("上半身3", "左胸", "右胸", "首根元"),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    ARM_CENTER = DressBoneSetting(
        setting=BoneSettings.ARM_CENTER.value,
        category="体幹",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    NECK = DressBoneSetting(
        setting=BoneSettings.NECK.value,
        category="首",
        weight_names=("首"),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    HEAD = DressBoneSetting(
        setting=BoneSettings.HEAD.value,
        category="頭",
        weight_names=("頭",),
        translatable=True,
        rotatable=True,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )

    RIGHT_BUST = DressBoneSetting(
        setting=BoneSettings.RIGHT_BUST.value,
        category="胸",
        weight_names=("右胸",),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_SHOULDER_P = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER_P.value,
        category="肩",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_SHOULDER = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER.value,
        category="肩",
        weight_names=("右肩",),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_SHOULDER_C = DressBoneSetting(
        setting=BoneSettings.RIGHT_SHOULDER_C.value,
        category="腕",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_ARM = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM.value,
        category="腕",
        weight_names=("右腕", "右腕捩", "右腕捩1", "右腕捩2", "右腕捩3", "右腕捩4", "右腕捩5"),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    RIGHT_ARM_TWIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_ARM_TWIST1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST1.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_ARM_TWIST2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST2.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_ARM_TWIST3 = DressBoneSetting(
        setting=BoneSettings.RIGHT_ARM_TWIST3.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_ELBOW = DressBoneSetting(
        setting=BoneSettings.RIGHT_ELBOW.value,
        category="腕",
        weight_names=("右ひじ", "右手捩", "右手捩1", "右手捩2", "右手捩3", "右手捩4", "右手捩5"),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    RIGHT_HAND_TWIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_HAND_TWIST1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST1.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_HAND_TWIST2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST2.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_HAND_TWIST3 = DressBoneSetting(
        setting=BoneSettings.RIGHT_HAND_TWIST3.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    RIGHT_WRIST = DressBoneSetting(
        setting=BoneSettings.RIGHT_WRIST.value,
        category="手首",
        weight_names=("右手首",),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    RIGHT_THUMB0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB0.value,
        category="指",
        weight_names=("右親指０",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_THUMB1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB1.value,
        category="指",
        weight_names=("右親指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_THUMB2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB2.value,
        category="指",
        weight_names=("右親指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_THUMB_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_THUMB_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_INDEX0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX0.value,
        category="指",
        weight_names=("右人指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_INDEX1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX1.value,
        category="指",
        weight_names=("右人指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_INDEX2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX2.value,
        category="指",
        weight_names=("右人指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_INDEX_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_INDEX_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_MIDDLE0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE0.value,
        category="指",
        weight_names=("右中指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_MIDDLE1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE1.value,
        category="指",
        weight_names=("右中指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_MIDDLE2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE2.value,
        category="指",
        weight_names=("右中指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_MIDDLE_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_MIDDLE_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_RING0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING0.value,
        category="指",
        weight_names=("右薬指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_RING1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING1.value,
        category="指",
        weight_names=("右薬指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_RING2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING2.value,
        category="指",
        weight_names=("右薬指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_RING_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_RING_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_PINKY0 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY0.value,
        category="指",
        weight_names=("右小指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_PINKY1 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY1.value,
        category="指",
        weight_names=("右小指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_PINKY2 = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY2.value,
        category="指",
        weight_names=("右小指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_PINKY_TAIL = DressBoneSetting(
        setting=BoneSettings.RIGHT_PINKY_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_WRIST_CANCEL = DressBoneSetting(
        setting=BoneSettings.RIGHT_WRIST_CANCEL.value,
        category="足",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_LEG = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG.value,
        category="足",
        weight_names=("右足", "右足D", "足中心"),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    RIGHT_KNEE = DressBoneSetting(
        setting=BoneSettings.RIGHT_KNEE.value,
        category="足",
        weight_names=("右ひざ", "右ひざD"),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    RIGHT_ANKLE = DressBoneSetting(
        setting=BoneSettings.RIGHT_ANKLE.value,
        category="足首",
        weight_names=("右足首", "右足首D", "右つま先", "右足先EX"),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_TOE = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE.value,
        category="足首",
        weight_names=("右つま先",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_LEG_IK = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_IK.value,
        category="足",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_TOE_IK = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE_IK.value,
        category="足",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_LEG_D = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_D.value,
        category="足",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    RIGHT_KNEE_D = DressBoneSetting(
        setting=BoneSettings.RIGHT_KNEE_D.value,
        category="足",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    RIGHT_ANKLE_D = DressBoneSetting(
        setting=BoneSettings.RIGHT_ANKLE_D.value,
        category="足首",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_TOE_EX = DressBoneSetting(
        setting=BoneSettings.RIGHT_TOE_EX.value,
        category="足首",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    RIGHT_LEG_IK_PARENT = DressBoneSetting(
        setting=BoneSettings.RIGHT_LEG_IK_PARENT.value,
        category="足首",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )

    LEFT_BUST = DressBoneSetting(
        setting=BoneSettings.LEFT_BUST.value,
        category="胸",
        weight_names=("左胸",),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_SHOULDER_P = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER_P.value,
        category="肩",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_SHOULDER = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER.value,
        category="肩",
        weight_names=("左肩",),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_SHOULDER_C = DressBoneSetting(
        setting=BoneSettings.LEFT_SHOULDER_C.value,
        category="腕",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_ARM = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM.value,
        category="腕",
        weight_names=("左腕", "左腕捩", "左腕捩1", "左腕捩2", "左腕捩3", "左腕捩4", "左腕捩5"),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEFT_ARM_TWIST = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_ARM_TWIST1 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST1.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_ARM_TWIST2 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST2.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_ARM_TWIST3 = DressBoneSetting(
        setting=BoneSettings.LEFT_ARM_TWIST3.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_ELBOW = DressBoneSetting(
        setting=BoneSettings.LEFT_ELBOW.value,
        category="腕",
        weight_names=("左ひじ", "左手捩", "左手捩1", "左手捩2", "左手捩3", "左手捩4", "左手捩5"),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEFT_HAND_TWIST = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_HAND_TWIST1 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST1.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_HAND_TWIST2 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST2.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_HAND_TWIST3 = DressBoneSetting(
        setting=BoneSettings.LEFT_HAND_TWIST3.value,
        category="腕",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=True,
    )
    LEFT_WRIST = DressBoneSetting(
        setting=BoneSettings.LEFT_WRIST.value,
        category="手首",
        weight_names=("左手首",),
        translatable=True,
        rotatable=True,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEFT_THUMB0 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB0.value,
        category="指",
        weight_names=("左親指０",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_THUMB1 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB1.value,
        category="指",
        weight_names=("左親指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_THUMB2 = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB2.value,
        category="指",
        weight_names=("左親指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_THUMB_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_THUMB_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_INDEX0 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX0.value,
        category="指",
        weight_names=("左人指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_INDEX1 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX1.value,
        category="指",
        weight_names=("左人指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_INDEX2 = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX2.value,
        category="指",
        weight_names=("左人指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_INDEX_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_INDEX_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_MIDDLE0 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE0.value,
        category="指",
        weight_names=("左中指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_MIDDLE1 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE1.value,
        category="指",
        weight_names=("左中指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_MIDDLE2 = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE2.value,
        category="指",
        weight_names=("左中指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_MIDDLE_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_MIDDLE_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_RING0 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING0.value,
        category="指",
        weight_names=("左薬指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_RING1 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING1.value,
        category="指",
        weight_names=("左薬指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_RING2 = DressBoneSetting(
        setting=BoneSettings.LEFT_RING2.value,
        category="指",
        weight_names=("左薬指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_RING_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_RING_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_PINKY0 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY0.value,
        category="指",
        weight_names=("左小指１",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_PINKY1 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY1.value,
        category="指",
        weight_names=("左小指２",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_PINKY2 = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY2.value,
        category="指",
        weight_names=("左小指３",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_PINKY_TAIL = DressBoneSetting(
        setting=BoneSettings.LEFT_PINKY_TAIL.value,
        category="指",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_WRIST_CANCEL = DressBoneSetting(
        setting=BoneSettings.LEFT_WRIST_CANCEL.value,
        category="足",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_LEG = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG.value,
        category="足",
        weight_names=("左足", "左足D", "足中心"),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEFT_KNEE = DressBoneSetting(
        setting=BoneSettings.LEFT_KNEE.value,
        category="足",
        weight_names=("左ひざ", "左ひざD"),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEFT_ANKLE = DressBoneSetting(
        setting=BoneSettings.LEFT_ANKLE.value,
        category="足首",
        weight_names=("左足首", "左足首D", "左つま先", "左足先EX"),
        translatable=True,
        rotatable=False,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_TOE = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE.value,
        category="足首",
        weight_names=("左つま先",),
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_LEG_IK = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_IK.value,
        category="足",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_TOE_IK = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE_IK.value,
        category="足",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_LEG_D = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_D.value,
        category="足",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEFT_KNEE_D = DressBoneSetting(
        setting=BoneSettings.LEFT_KNEE_D.value,
        category="足",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=True,
        local_scalable=True,
        local_scale_target=True,
    )
    LEFT_ANKLE_D = DressBoneSetting(
        setting=BoneSettings.LEFT_ANKLE_D.value,
        category="足首",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=True,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_TOE_EX = DressBoneSetting(
        setting=BoneSettings.LEFT_TOE_EX.value,
        category="足首",
        weight_names=[],
        translatable=False,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )
    LEFT_LEG_IK_PARENT = DressBoneSetting(
        setting=BoneSettings.LEFT_LEG_IK_PARENT.value,
        category="足首",
        weight_names=[],
        translatable=True,
        rotatable=False,
        global_scalable=False,
        local_scalable=False,
        local_scale_target=False,
    )


DRESS_STANDARD_BONE_NAMES: dict[str, DressBoneSetting] = dict([(bs.value.name, bs.value) for bs in DressBoneSettings])
"""衣装用準標準ボーン名前とEnumのキーの辞書"""

LOCAL_SCALE_WEIGHT_BONE_NAMES: list[str] = [bs.value.name for bs in DressBoneSettings if bs.value.local_scale_target]
"""衣装用準標準のうち、ローカルスケーリング用ウェイト計算対象ボーン名リスト"""


# IKはFKの後に指定する事
"""個別フィッティング用ボーン設定"""
FIT_INDIVIDUAL_BONE_NAMES = {
    "腰": (("腰",), ("下半身", "上半身", "上半身2", "上半身3"), ("下半身", "上半身"), []),
    "下半身": (("下半身",), [], ("足", "ひざ", "足首"), []),
    "上半身": (("上半身",), [], ("上半身2",), []),
    "上半身2": (("上半身2",), [], ("上半身3",), []),
    "上半身3": (("上半身3",), [], [], []),
    "胸": (("右胸", "左胸"), [], [], []),
    "首": (("首",), [], [], []),
    "頭": (("頭",), [], [], []),
    "肩": (("右肩", "左肩"), ("右肩P", "左肩P"), ("腕", "ひじ", "手のひら"), ("腕", "ひじ", "手のひら")),
    "腕": (("右腕", "左腕"), ("右肩C", "左肩C"), ("ひじ", "手のひら"), ("ひじ", "手のひら")),
    "ひじ": (("右ひじ", "左ひじ"), ("手のひら",), ("手のひら",), ("手のひら",)),
    "手のひら": (("右手首", "左手首"), [], [], []),
    "足": (("右足", "左足", "右足D", "左足D"), [], ("ひざ",), []),
    "ひざ": (("右ひざ", "左ひざ", "右ひざD", "左ひざD"), [], [], []),
    "足首": (("右足首", "左足首", "右足首D", "左足首D"), [], [], []),
}
