from typing import Optional
from mlib.base.collection import BaseIndexNameDictModel
from mlib.base.math import MVector3D
from mlib.base.part import BaseIndexNameModel
from mlib.pmx.bone_setting import BoneFlg
from mlib.pmx.pmx_part import Bone, Ik


class DressBone(BaseIndexNameModel):
    def __init__(self, index: int, name: str, bone: Bone, is_dress: bool, is_weight: bool, position: Optional[MVector3D] = None) -> None:
        super().__init__()

        self.bone = bone
        self.is_dress = is_dress
        self.is_weight = is_weight

        self.index = index
        self.name = name
        self.position = position
        self.parent_index = -1
        self.layer = 0
        self.bone_flg = BoneFlg.NONE
        self.tail_position: Optional[MVector3D] = None
        self.tail_index = -1
        self.effect_index = -1
        self.effect_factor = 0.0
        self.fixed_axis: Optional[MVector3D] = None
        self.local_x_vector: Optional[MVector3D] = None
        self.local_z_vector: Optional[MVector3D] = None
        self.external_key = -1
        self.ik: Ik = Ik()

    def get_bone(self) -> Bone:
        new_bone = Bone(self.index, self.name, self.english_name or self.bone.english_name)
        new_bone.position = self.position or self.bone.position
        new_bone.parent_index = self.parent_index
        new_bone.layer = self.layer
        new_bone.bone_flg = self.bone_flg | self.bone.bone_flg
        new_bone.tail_position = self.tail_position or self.bone.tail_position
        new_bone.tail_index = self.tail_index
        new_bone.effect_index = self.effect_index
        new_bone.effect_factor = self.effect_factor or self.bone.effect_factor
        new_bone.fixed_axis = self.fixed_axis or self.bone.fixed_axis
        new_bone.local_x_vector = self.local_x_vector or self.bone.local_x_vector
        new_bone.local_z_vector = self.local_z_vector or self.bone.local_z_vector
        new_bone.external_key = self.external_key
        new_bone.ik = self.ik

        return new_bone


class DressBones(BaseIndexNameDictModel[DressBone]):
    def __init__(self) -> None:
        super().__init__()
        self.model_map: dict[int, int] = {}
        self.dress_map: dict[int, int] = {}

    def append(self, bone: Bone, is_dress: bool, is_weight: bool, position: Optional[MVector3D] = None) -> None:
        # 人物もしくは準標準の場合、そのまま。それ以外は衣装用に名前を変える
        dress_bone_name = bone.name if not is_dress or bone.is_standard or bone.is_standard_extend else f"Cos:{bone.name}"

        if dress_bone_name in self:
            if is_dress:
                # 衣装にもある場合は、INDEX対応表だけ保持して終了
                self.dress_map[bone.index] = self[dress_bone_name].index
                return
            # 同じモデルの場合、名前にサフィックスを付ける
            suffix = 1
            while f"{dress_bone_name}{suffix}" not in self and suffix < 10:
                suffix += 1
            dress_bone_name = f"{dress_bone_name}{suffix}"

        dress_bone = DressBone(len(self.data), dress_bone_name, bone, is_dress, is_weight, position)

        self.data[dress_bone.index] = dress_bone

        if dress_bone_name not in self._names:
            # 名前は先勝ちで保持
            self._names[dress_bone_name] = dress_bone.index

        # 対応表を保持
        if is_dress:
            self.dress_map[bone.index] = dress_bone.index
        else:
            self.model_map[bone.index] = dress_bone.index

    def get_index_by_map(self, index: int, is_dress: bool) -> int:
        """衣装もしくは人物のマップに沿ってINDEXを取得する"""
        if is_dress:
            return self.dress_map.get(index, -1)
        return self.model_map.get(index, -1)
