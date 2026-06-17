import importlib.util
import platform
import struct
import usb.core
import usb.backend.libusb1
import time
from pathlib import Path


def _find_libusb_dll():
    spec = importlib.util.find_spec('libusb')
    if spec is None or spec.origin is None:
        return None
    arch = 'x86_64' if platform.machine().endswith('64') else 'x86'
    dll = Path(spec.origin).parent / '_platform' / 'windows' / arch / 'libusb-1.0.dll'
    return str(dll) if dll.exists() else None


DLL = _find_libusb_dll()

class LAC:
    # Command bytes
    SET_ACCURACY           = 0x01
    SET_RETRACT_LIMIT      = 0x02
    SET_EXTEND_LIMIT       = 0x03
    SET_MOVEMENT_THRESHOLD = 0x04
    SET_STALL_TIME         = 0x05
    SET_PWM_THRESHOLD      = 0x06
    SET_DERIVATIVE_THRESHOLD = 0x07
    SET_MAX_DERIVATIVE     = 0x08
    SET_MIN_DERIVATIVE     = 0x09
    SET_MAX_PWM_VALUE      = 0x0A
    SET_MIN_PWM_VALUE      = 0x0B
    SET_Kp                 = 0x0C
    SET_Kd                 = 0x0D
    SET_AVERAGE_RC         = 0x0E
    SET_AVERAGE_ADC        = 0x0F
    GET_FEEDBACK           = 0x10
    SET_POSITION           = 0x20
    SET_SPEED              = 0x21
    DISABLE_MANUAL         = 0x30
    RESET                  = 0xFF

    def __init__(self, vendorID=0x04D8, productID=0xFC5F):
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: DLL)
        self.device = usb.core.find(idVendor=vendorID, idProduct=productID, backend=backend)
        if self.device is None:
            raise Exception("LAC board not found. Check connection and driver (run Zadig).")
        self.device.set_configuration()
        print("LAC connected.")

    def send_data(self, function, value=0):
        if not (0 <= value <= 1023):
            raise ValueError(f"Value {value} out of range [0, 1023]")
        # 3-byte packet: [command, low_byte, high_byte]
        data = struct.pack('BBB', function, value & 0xFF, (value >> 8) & 0xFF)
        self.device.write(1, data, timeout=100)
        time.sleep(0.05)
        response = self.device.read(0x81, 3, timeout=100)
        return (response[2] << 8) + response[1]

    def set_position(self, value):
        """Move to position. value = (distance_mm / stroke_mm) * 1023, rounded to int.
        0 = fully retracted, 1023 = fully extended."""
        self.send_data(self.SET_POSITION, value)

    def get_feedback(self):
        """Returns current position as integer [0, 1023]."""
        return self.send_data(self.GET_FEEDBACK)

    def set_speed(self, value):
        """Set max speed. 0 = slowest, 1023 = fastest."""
        self.send_data(self.SET_SPEED, value)

    def set_accuracy(self, value=4):
        """Deadband around target. Lower = more precise but may oscillate."""
        self.send_data(self.SET_ACCURACY, value)

    def set_retract_limit(self, value=0):
        self.send_data(self.SET_RETRACT_LIMIT, value)

    def set_extend_limit(self, value=1023):
        self.send_data(self.SET_EXTEND_LIMIT, value)

    def reset(self):
        """Reset to factory defaults and re-enable potentiometers."""
        self.send_data(self.RESET)

    def disable_manual(self):
        """Save config to EEPROM and disable onboard pots."""
        self.send_data(self.DISABLE_MANUAL)

    def home(self):
        """Move to fully retracted position."""
        self.set_position(0)

    def cut(self):
        """Move to fully extended position."""
        self.set_position(900)
        while self.get_feedback() < 850:
            time.sleep(0.05)
        self.set_position(0)

