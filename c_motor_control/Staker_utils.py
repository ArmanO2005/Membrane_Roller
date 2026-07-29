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

    # def home(self):
    #     print(f"[{self.name}] Homing started...")

    #     if not self.motor.get_axis_parameter(self.AP.HomeSwitch):
    #         self.motor.rotate(self.config.get("home_search_velocity"))
    #         time.sleep(2)
    #         self.motor.stop()
    #         self.wait_for_stop()

    #     self.motor.rotate(-self.config.get("home_search_velocity"))
    #     start_time = time.time()
    #     while True:
    #         not_triggered = self.motor.get_axis_parameter(self.AP.HomeSwitch) # 0: triggered, 1: not_triggered
    #         if not not_triggered:
    #             self.motor.stop()
    #             self.wait_for_stop()
    #             centering_time = self.config.get("home_centering_time")
    #             if centering_time:
    #                 self.motor.rotate(self.config.get("home_search_velocity"))
    #                 time.sleep(centering_time)
    #                 self.motor.stop()
    #                 self.wait_for_stop()
    #             print(f"[{self.name}] Switch triggered.")
    #             break
    #         if time.time() - start_time > self.config.get("home_timeout"):
    #             self.motor.stop()
    #             raise TimeoutError(f"[{self.name}] Homing timed out")
    #         time.sleep(0.01)

    #     self.motor.set_axis_parameter(self.AP.ActualPosition, 0)
    #     print(f"[{self.name}] Homing complete. Position zeroed.")


    def home(self):
        print(f"[{self.name}] Homing started...")

        if not self.motor.get_axis_parameter(self.AP.HomeSwitch):
            self.motor.rotate(self.config.get("home_search_velocity"))
            time.sleep(2)
            self.motor.stop()
            self.wait_for_stop()

        self.motor.rotate(-self.config.get("home_search_velocity"))
        start_time = time.time()
        while True:
            not_triggered = self.motor.get_axis_parameter(self.AP.HomeSwitch) # 0: triggered, 1: not_triggered
            if not not_triggered:
                self.motor.stop()
                self.wait_for_stop()
                centering_time = self.config.get("home_centering_time")
                if centering_time:
                    self.motor.rotate(-self.config.get("home_search_velocity"))
                    time.sleep(centering_time)
                    self.motor.stop()
                    self.wait_for_stop()
                print(f"[{self.name}] Switch triggered.")
                break
            if time.time() - start_time > self.config.get("home_timeout"):
                self.motor.stop()
                raise TimeoutError(f"[{self.name}] Homing timed out")
            time.sleep(0.01)

        self.motor.set_axis_parameter(self.AP.ActualPosition, 0)
        print(f"[{self.name}] Homing complete. Position zeroed.")

    def stake_one(self, stake_time=3, stake_point=307000):
        self.go_to_0()
        self.move_to(stake_point, velocity=self.config.get("velocity"))
        time.sleep(stake_time)
        self.move_to(200000, velocity=(self.config.get("velocity") * 5))
    
    def stake_two(self, stake_time=5, stake_point=307000):
        self.move_to(stake_point, velocity=self.config.get("velocity"))
        time.sleep(stake_time)
        self.move_to(250000, velocity=self.config.get("velocity"))
        self.move_to(stake_point, velocity=self.config.get("velocity"))
        time.sleep(1)
        self.move_to(200000, velocity=(self.config.get("velocity") * 5))
        self.go_to_0()