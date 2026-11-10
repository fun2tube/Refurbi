"""QC checklist template for smartphones. `critical` items must pass for the device to pass QC.
Items/labels are placeholders pending the founder's final grade definitions."""

from typing import NamedTuple


class Item(NamedTuple):
    key: str
    label: str
    critical: bool


SMARTPHONE_TEMPLATE: tuple[Item, ...] = (
    Item("display", "Display: no dead pixels / burn-in", True),
    Item("touch", "Touch response across full screen", True),
    Item("battery_charging", "Charges and holds charge", True),
    Item("camera_rear", "Rear camera(s) work", True),
    Item("camera_front", "Front camera works", True),
    Item("speaker_mic", "Speaker, earpiece and microphone", True),
    Item("wifi_bluetooth", "Wi-Fi and Bluetooth", True),
    Item("cellular", "SIM detection and calls/data", True),
    Item("biometrics", "Fingerprint / Face unlock", False),
    Item("buttons", "Power, volume and silent buttons", True),
    Item("charging_port", "Charging port", True),
    Item("sensors", "Proximity, gyro, compass", False),
    Item("account_lock_removed", "No activation / account lock", True),
    Item("liquid_damage", "No liquid damage indicator tripped", True),
    Item("body_condition", "Body: frame, back glass, scratches", False),
)
RESULTS = ("pass", "fail", "na")
