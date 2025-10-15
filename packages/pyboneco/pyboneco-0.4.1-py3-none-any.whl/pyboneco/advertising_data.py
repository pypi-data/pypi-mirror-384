from datetime import datetime, timezone

from .constants import BONECO_MANUFACTER_ID, BONECO_DATA_MARKER
from .utils import build_software_version


class BonecoAdvertisingData:
    is_boneco_device: bool
    company_id_1: int
    company_id_2: int
    _spare: int
    software_version: str
    build_date: datetime
    pairing_active: bool
    is_user_mode: bool
    is_service_mode: bool

    def __init__(self, manufacturer_id: int, data: bytes) -> None:
        self.is_boneco_device = (
            manufacturer_id == BONECO_MANUFACTER_ID and data[0] == BONECO_DATA_MARKER
        )
        self.company_id_1 = manufacturer_id
        self.company_id_2 = data[0]
        if not self.is_boneco_device:
            return
        self._spare = data[1]
        self.software_version = build_software_version(data[3], data[2])
        self.build_date = datetime(
            year=int.from_bytes(data[4:6], byteorder="little"),
            month=data[6],
            day=data[7],
            tzinfo=timezone.utc,
        ).astimezone()
        flag = data[8]
        self.pairing_active = flag & 1 == 1
        self.is_service_mode = (flag >> 1) & 1 == 1
        self.is_user_mode = not self.is_service_mode
