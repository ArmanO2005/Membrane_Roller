# from motor_control.Clamp_utils import ClampController
# from motor_control.Staker_utils import StakerController
# from motor_control.Feeder_utils import FeederController
# from motor_control.Spindle_utils import SpindleController
# from motor_control.Actuonix_LAC_utils import ActuonixLAC
# import time
# import yaml
# import logging

# with open('config/motor_config.yaml', 'r') as file:
#     motor_config = yaml.safe_load(file)


# clamp_motor = ClampController(motor_config['clamp'])
# staker_motor = StakerController(motor_config['staker'])
# spindle_motor = SpindleController(motor_config['spindle'])
# feeder_motor = FeederController(motor_config['feeder'])

# # staker_motor.go_to_stake()
# staker_motor.exit_stake()
# clamp_motor.home()



from robot_control.membrane_roller import MembraneRoller
import yaml
import time


with open('config/motor_config.yaml', 'r') as file:
    motor_config = yaml.safe_load(file)

roller = MembraneRoller(motor_config)
roller.initialize()
roller.roll()
roller.off()
