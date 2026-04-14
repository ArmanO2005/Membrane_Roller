from motor_control.TMCM1111_utils import TMCM1111Controller
import time



class ClampController(TMCM1111Controller):
    def __init__(self, config):
        super().__init__(config)
    
    def home(self):
        print(f"[{self.name}] Homing started...")

        self.motor.rotate(self.config.get("home_search_velocity"))
        start_time = time.time()
        while True:
            not_triggered = self.motor.get_axis_parameter(self.AP.HomeSwitch) # 0: triggered, 1: not_triggered
            if not not_triggered:
                time.sleep(self.config.get("home_centering_time"))
                self.motor.stop()
                print(f"[{self.name}] Switch triggered.")
                break
            if time.time() - start_time > self.config.get("home_timeout"):
                self.motor.stop()
                raise TimeoutError(f"[{self.name}] Homing timed out")
            time.sleep(0.01)


        self.motor.set_axis_parameter(self.AP.ActualPosition, 0)
        print(f"[{self.name}] Homing complete. Position zeroed.")

    def clamp(self):
        self.motor.rotate(-self.config.get("velocity"))
        while True:
            triggered = self.motor.get_axis_parameter(self.AP.LeftEndstop) # 1: triggered, 0: not_triggered
            if triggered:
                time.sleep(0.3)
                self.motor.stop()
                print(f"[{self.name}] Clamp position reached.")
                break

    def test_switch(self):
        import time
        print("Monitoring switch input — block/unblock the slot...")
        for _ in range(50):
            val = self.motor.get_axis_parameter(self.AP.LeftEndstop)
            print(f"Input 0: {val}")
            time.sleep(0.05)
