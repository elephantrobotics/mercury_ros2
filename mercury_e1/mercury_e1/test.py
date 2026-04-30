from pymycobot import MercuryE1
import time

mc = MercuryE1('/dev/ttyUSB0', debug=0)


# mc.set_motor_enabled(254, 1)

print(mc.get_angles(), mc.get_coords())

init_angles = [0.12, 8.84, 0.8, -91.83, 3.42, -71.22, -0.01]
init_coords = [301.0, 11.7, 331.8, 176.48, 8.06, 179.79]