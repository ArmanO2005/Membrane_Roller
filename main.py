from c_motor_control.Clamp_utils import ClampController
from c_motor_control.Staker_utils import StakerController
from c_motor_control.Feeder_utils import FeederController
from c_motor_control.Spindle_utils import SpindleController
import time
import yaml
import logging

with open('a_config/motor_config.yaml', 'r') as file:
    motor_config = yaml.safe_load(file)


clamp_motor = ClampController(motor_config['clamp'])
staker_motor = StakerController(motor_config['staker'])
spindle_motor = SpindleController(motor_config['spindle'])
feeder_motor = FeederController(motor_config['feeder'])

# clamp_motor.clamp()
staker_motor.stake(5)
# staker_motor.move_to(0, velocity=30000)
# staker_motor.home()


# from gui import main

# main()