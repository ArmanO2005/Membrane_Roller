# from pytrinamic.connections import ConnectionManager
# from pytrinamic.modules.TMCM1111 import TMCM1111
# from pytrinamic.evalboards.TMC4671_eval import TMC4671_eval
# from pytrinamic.ic.TMC4671 import TMC4671
# import inspect


from motor_control.TMCM1111_utils import TMCM1111Controller
from motor_control.Clamp_utils import ClampController
import time
import yaml

with open('config/motor_config.yaml', 'r') as file:
    motor_config = yaml.safe_load(file)

# 4 to 1 USB Adaptor
PORT0 = "COM3"
PORT1 = "COM13"  # Clamp
PORT2 = "COM14"  # Staker
PORT3 = "COM15"  # Spindle


clamp_motor = ClampController(motor_config['clamp'])
staker_motor = TMCM1111Controller(motor_config['staker'])
spindle_motor = TMCM1111Controller(motor_config['spindle'])

clamp_motor.clamp()
