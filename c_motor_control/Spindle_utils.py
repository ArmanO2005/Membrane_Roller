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

        self.motor.set_axis_parameter(self.AP.ActualPosition, 0)

    def move_to_notch(self):
        self.move_to(self.config.get("notch_position"), velocity=self.config.get("velocity"))

    def full_rotation(self):
        self.move_by(self.config.get("full_rotation_steps"), velocity=self.config.get("velocity"))


    # def full_rotation(self):
    #     self.motor.rotate(self.config.get("velocity"))
    #     time.sleep(2)
    #     start_time = time.time()
    #     while True:
    #         not_triggered = self.motor.get_axis_parameter(self.AP.HomeSwitch)
    #         if not not_triggered:
    #             time.sleep(self.config.get("home_centering_time"))
    #             time.sleep(self.config.get("notch_time"))
    #             self.motor.stop()
    #             break
    #         if time.time() - start_time > self.config.get("home_timeout"):
    #             self.motor.stop()
    #             raise TimeoutError(f"[{self.name}] Homing timed out")
    #         time.sleep(0.01)