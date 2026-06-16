from c_motor_control.TMCM1111_utils import TMCM1111Controller
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

    def go_to_0(self):
        self.move_to(1000, velocity=self.config.get("home_search_velocity"))

    def stake_one(self, stake_time=3, stake_point=307000):
        self.go_to_0()
        self.move_to(stake_point, velocity=self.config.get("velocity"))
        time.sleep(stake_time)
        self.move_to(200000, velocity=(self.config.get("velocity") * 5))
    
    def stake_two(self, stake_time=5, stake_point=307000):
        self.move_to(stake_point, velocity=self.config.get("velocity"))
        time.sleep(stake_time)
        self.move_to(200000, velocity=(self.config.get("velocity") * 5))
        self.go_to_0()