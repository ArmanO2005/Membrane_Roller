import time
import threading
import logging
import usb.core
import usb.util

#slop code, usb connection to the board doesnt get detected by my computer so this on hold for now

VENDOR_ID  = 0x04D8
PRODUCT_ID = 0xFC5F


CMD_SET_ACCURACY   = 0x01
CMD_SET_SPEED      = 0x21
CMD_GET_FEEDBACK   = 0x10
CMD_SET_POSITION   = 0x20
CMD_DISABLE_MANUAL = 0x30
CMD_RESET          = 0xFF


class ActuonixLAC:
    def __init__(self, stroke_mm: float, logger: logging.Logger = None):
        self.stroke_mm   = stroke_mm
        self.logger      = logger or logging.getLogger("ActuonixLAC")
        self._device     = None
        self._ep_out     = None
        self._ep_in      = None
        self._connected  = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        try:
            dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
            if dev is None:
                self.logger.error("LAC device not found")
                return False

            usb.util.dispose_resources(dev)  # release any stale handle
            dev.reset()
            time.sleep(0.5)

            dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
            dev.set_configuration()
            intf = dev.get_active_configuration()[(0, 0)]

            ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                             == usb.util.ENDPOINT_OUT,
            )
            ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                             == usb.util.ENDPOINT_IN,
            )

            if ep_out is None or ep_in is None:
                self.logger.error("Could not find USB endpoints")
                return False

            self._device    = dev
            self._ep_out    = ep_out
            self._ep_in     = ep_in
            self._connected = True
            self.logger.info("Connected to LAC device")
            return True

        except Exception as e:
            self.logger.error(f"connect() failed: {e}")
            return False

    def disconnect(self) -> None:
        if self._device is not None:
            usb.util.dispose_resources(self._device)
        self._device    = None
        self._ep_out    = None
        self._ep_in     = None
        self._connected = False
        self.logger.info("Disconnected from LAC device")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    # ------------------------------------------------------------------
    # Low-level packet
    # ------------------------------------------------------------------

    def _send(self, command: int, data: int = 0):
        if not self._connected:
            raise RuntimeError("Device not connected")
        data = max(0, min(1023, data))
        packet = [command, data & 0xFF, (data >> 8) & 0xFF]
        self._ep_out.write(packet, timeout=1000)
        return bytes(self._ep_in.read(3, timeout=1000))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_position(self, position_mm: float) -> bool:
        units = int((position_mm / self.stroke_mm) * 1023)
        try:
            self._send(CMD_SET_POSITION, units)
            return True
        except Exception as e:
            self.logger.error(f"set_position failed: {e}")
            return False

    def get_position(self) -> float:
        resp = self._send(CMD_GET_FEEDBACK)
        units = resp[1] | (resp[2] << 8)
        return (units / 1023.0) * self.stroke_mm

    def set_speed(self, speed_percent: float) -> bool:
        units = int((speed_percent / 100.0) * 1023)
        try:
            self._send(CMD_SET_SPEED, units)
            return True
        except Exception as e:
            self.logger.error(f"set_speed failed: {e}")
            return False

    def set_accuracy(self, accuracy_mm: float) -> bool:
        units = max(1, int((accuracy_mm / self.stroke_mm) * 1024))
        try:
            self._send(CMD_SET_ACCURACY, units)
            return True
        except Exception as e:
            self.logger.error(f"set_accuracy failed: {e}")
            return False

    def disable_manual(self) -> bool:
        try:
            self._send(CMD_DISABLE_MANUAL)
            return True
        except Exception as e:
            self.logger.error(f"disable_manual failed: {e}")
            return False

    def reset(self) -> bool:
        try:
            self._send(CMD_RESET)
            return True
        except Exception as e:
            self.logger.error(f"reset failed: {e}")
            return False

    def move_to_position(
        self,
        position_mm: float,
        timeout_s: float = 10.0,
        accuracy_mm: float = 1.0,
        on_done=None,
        on_error=None,
    ) -> None:
        """
        Non-blocking move. Polls until within accuracy_mm or timeout.
        Calls on_done(position) or on_error() when finished.
        """
        if not self.set_position(position_mm):
            if on_error:
                on_error()
            return

        def _poll():
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                pos = self.get_position()
                if abs(pos - position_mm) <= accuracy_mm:
                    self.logger.info(f"Position reached: {pos:.2f} mm")
                    if on_done:
                        on_done(pos)
                    return
                time.sleep(0.05)
            self.logger.warning(f"move_to_position timed out after {timeout_s}s")
            if on_error:
                on_error()

        threading.Thread(target=_poll, daemon=True).start()

    def move_to_position_blocking(
        self,
        position_mm: float,
        timeout_s: float = 10.0,
        accuracy_mm: float = 1.0,
    ) -> bool:
        """Blocking version — returns True if position reached, False on timeout."""
        if not self.set_position(position_mm):
            return False
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if abs(self.get_position() - position_mm) <= accuracy_mm:
                return True
            time.sleep(0.05)
        return False


# ----------------------------------------------------------------------
# Quick smoke-test
# ----------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    STROKE_MM = 50.0  # adjust to match your actuator

    with ActuonixLAC(stroke_mm=STROKE_MM) as lac:
        print(f"Connected: {lac._connected}")
        print(f"Current position: {lac.get_position():.2f} mm")

        print("Moving to 10 mm …")
        ok = lac.move_to_position_blocking(10.0, timeout_s=15.0)
        print(f"  reached: {ok}  pos={lac.get_position():.2f} mm")

        print("Moving to 40 mm …")
        ok = lac.move_to_position_blocking(40.0, timeout_s=15.0)
        print(f"  reached: {ok}  pos={lac.get_position():.2f} mm")

        print("Retracting to 0 mm …")
        ok = lac.move_to_position_blocking(0.0, timeout_s=15.0)
        print(f"  reached: {ok}  pos={lac.get_position():.2f} mm")