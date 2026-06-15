from c_motor_control.TMCM1111_utils import TMCM1111Controller
import time

class SpindleController(TMCM1111Controller):
    def __init__(self, config):
        super().__init__(config)
    
    def home(self):
        if self.motor.get_axis_parameter(self.AP.HomeSwitch) == 0:
            self.motor.rotate(self.config.get("velocity"))
            time.sleep(2)
            self.motor.stop()

        super().home()


    def full_rotation(self):
        self.motor.rotate(self.config.get("velocity"))
        time.sleep(2)
        start_time = time.time()
        while True:
            not_triggered = self.motor.get_axis_parameter(self.AP.HomeSwitch)
            if not not_triggered:
                time.sleep(0.7)
                self.motor.stop()
                print(f"[{self.name}] Switch triggered.")
                break
            if time.time() - start_time > self.config.get("home_timeout"):
                self.motor.stop()
                raise TimeoutError(f"[{self.name}] Homing timed out")
            time.sleep(0.01)


        self.motor.set_axis_parameter(self.AP.ActualPosition, 0)