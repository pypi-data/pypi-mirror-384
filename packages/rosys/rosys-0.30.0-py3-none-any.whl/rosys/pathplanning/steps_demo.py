#!/usr/bin/env python
import time

import numpy as np
import pylab as pl
from nicegui import ui

from rosys.pathplanning import plot_tools as pt
from rosys.pathplanning.grid import Grid
from rosys.pathplanning.obstacle_map import ObstacleMap
from rosys.pathplanning.robot_renderer import RobotRenderer
from rosys.pathplanning.steps import Path, Step

grid = Grid((30, 40, 36), (0, 0, 4.0, 3.0))
obstacles = [
    [0.0, 1.0, 2.5, 0.2],
    [1.5, 2.0, 2.5, 0.2],
]
robot_renderer = RobotRenderer.from_size(0.77, 1.21, 0.445)
obstacle_map = ObstacleMap.from_list(grid, obstacles, robot_renderer)

path = Path.from_poses([
    [0.7, 0.4, np.deg2rad(5)],
    [1.2, 0.5, 0],
    [1.7, 0.4, np.deg2rad(-15)],
    [2.2, 0.5, 0],
    [2.8, 0.7, np.deg2rad(45)],
    [3.2, 1.0, np.deg2rad(0)],
])

robot_renderer = RobotRenderer.from_size(0.77, 1.21, 0.445)

with ui.pyplot():
    pt.show_obstacle_map(obstacle_map)
    pl.autoscale(False)
    for step in path:
        pt.plot_robot(robot_renderer, step.target)
    pt.plot_path(path, 'C0', lw=3)

    t = time.time()
    path.smooth(obstacle_map, control_dist=0.2)
    print(f'{(time.time() - t) * 1000:.3f} ms')

    pt.plot_path(path, 'C2', lw=3)

    step0 = Step((0.5, 2.9, 0))
    for step in [
        Step((1.0, 2.5, 0), step0),
        Step((1.0, 2.0, 0), step0),
        Step((1.0, 1.5, 1), step0),
        Step((0.4, 1.5, 0), step0),
        Step((0.4, 1.5, 0), step0, backward=True),
        Step((0.1, 2.0, 0), step0, backward=True),
        Step((0.1, 2.5, 0), step0, backward=True),
    ]:
        color = 'C2' if step.is_healthy() else 'C3'
        pt.plot_spline(step.spline, color, backward=step.backward)
        print(step.spline, step.spline.max_curvature(), step.is_healthy())

ui.run()
