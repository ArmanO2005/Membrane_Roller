from c_motor_control.TMC4671_utils import TMC4671Controller
from c_motor_control.TMCM1111_utils import TMCM1111Controller
from c_motor_control.Clamp_utils import ClampController
from c_motor_control.Staker_utils import StakerController
from c_motor_control.Feeder_utils import FeederController
from c_motor_control.Spindle_utils import SpindleController
from c_motor_control.Actuonix_LAC_utils import LAC
import time
import yaml


class MembraneRoller:
    def __init__(self, config):
        self.clamp_motor  = self._try("Clamp",   ClampController,   config['clamp'])
        self.staker_motor = self._try("Staker",  StakerController,  config['staker'])
        self.spindle_motor= self._try("Spindle", SpindleController, config['spindle'])
        self.feeder_motor = self._try("Feeder",  FeederController,  config['feeder'])
        self.lac          = self._try_lac()

    def _try(self, name, cls, config):
        try:
            return cls(config)
        except Exception as e:
            print(f"[{name}] Connection failed: {e}")
            return None

    def _try_lac(self):
        try:
            return LAC()
        except Exception as e:
            print(f"[LAC] Connection failed: {e}")
            return None
        
    def tensionless_rotation(self, paired_velocity=-3):
        self.spindle_motor.full_rotation()
        self.feeder_motor.rotate(paired_velocity)
        notch_pos = self.spindle_motor.config.get("notch_position")
        time.sleep(2)
        while True:
            current_position = self.spindle_motor.motor.get_axis_parameter(self.spindle_motor.AP.ActualPosition)
            if current_position in range(notch_pos - 1000, notch_pos + 1000):
                self.feeder_motor.stop()
                break
            time.sleep(0.01)

    def close(self):
        for motor in (self.clamp_motor, self.staker_motor, self.spindle_motor, self.feeder_motor):
            if motor is not None:
                try:
                    motor.close()
                except Exception:
                    pass

    def initialize(self):
        if self.staker_motor:  self.staker_motor.enable_heater()
        if self.clamp_motor:   self.clamp_motor.home()
        if self.staker_motor:  self.staker_motor.home()
        if self.spindle_motor: self.spindle_motor.home()
        if self.spindle_motor: time.sleep(2)
        if self.spindle_motor: self.spindle_motor.move_to_notch()
        if self.lac:           self.lac.home()

    def roll(self, stake1_time=3, stake1_point=310000, stake2_time=5, stake2_point=310000, rotations_after=1.0, paired_velocity=30):
        if self.clamp_motor:   self.clamp_motor.clamp()
        if self.feeder_motor:  self.feeder_motor.reach_tip(rotations_after)
        if self.staker_motor:  self.staker_motor.stake_one(stake1_time, stake1_point)
        if self.spindle_motor: self.tensionless_rotation(paired_velocity)
        if self.staker_motor:  self.staker_motor.stake_two(stake2_time, stake2_point)
        if self.lac:           self.lac.cut()
        if self.clamp_motor:   self.clamp_motor.home()
        if self.feeder_motor:  self.feeder_motor.pull_back()

    def off(self):
        if self.staker_motor:  self.staker_motor.disable_heater()
        if self.clamp_motor:   self.clamp_motor.home()
        if self.staker_motor:  self.staker_motor.home()
        if self.spindle_motor: self.spindle_motor.home()
        if self.lac:           self.lac.home()
