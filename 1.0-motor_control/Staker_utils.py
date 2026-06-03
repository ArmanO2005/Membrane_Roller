from motor_control.TMCM1111_utils import TMCM1111Controller
import time



class StakerController(TMCM1111Controller):
    SETPOINT_OK_PIN = 1
    HEATER_PIN = 2

    def __init__(self, config):
        super().__init__(config)

    # Seems like heater max temp is ~240
    def enable_heater(self):
        self.set_digital_output(self.HEATER_PIN)

    def disable_heater(self):
        self.clear_digital_output(self.HEATER_PIN)

    def stake(self):
        self.home()
        time.sleep(0.5)
        self.rotate(self.config.get("velocity"))
        time.sleep(10.5)
        self.stop()
        time.sleep(3)
        self.rotate(-self.config.get("velocity") * 10)
        time.sleep(1.5)
        self.stop()
        self.home()

    def go_to_stake(self):
        self.home()
        time.sleep(0.5)
        self.rotate(self.config.get("velocity"))
        time.sleep(10.55)
        self.stop()

    def exit_stake(self):
        self.rotate(-self.config.get("velocity") * 10)
        time.sleep(1.5)
        self.stop()
        self.home()