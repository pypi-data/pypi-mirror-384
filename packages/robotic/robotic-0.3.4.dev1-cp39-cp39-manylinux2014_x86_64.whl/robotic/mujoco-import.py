import robotic as ry
from robotic.src.mujoco_io import *

file = '../../rai-robotModels/kitchens/models/MEDITERRANEAN_ONE_WALL_SMALL.xml'

print('=====================', file)
M = MujocoLoader(file, visualsOnly=True)
M.C.view(True)