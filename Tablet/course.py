import pyray as pr
import json
import math

from UI import Button
from math import atan2, degrees, cos, sin, radians

class CourseManager:
    def __init__(self, get_working_width: object) -> None:
        self.get_working_width = get_working_width

        self.run_dir = 0.0
        self.run_offset = 0.0

        self.autosteer_enabled = False
        self.desired_wheel_rotation = None

        self.a_point = None

    @property
    def working_width(self) -> float: return self.get_working_width()

    def set_ab(self, x: float, y: float) -> None:
        if self.a_point is not None:
            raw_run_dir = degrees(atan2(y - self.a_point[1], x - self.a_point[0]))

            if raw_run_dir < 0: self.run_dir = (360 + raw_run_dir) % 180
            else: self.run_dir = raw_run_dir % 180

            self.a_point = None
            print(f"Set {self.run_dir:.2f} degrees runlines.")
        else:
            self.a_point = (x, y)

    def nudge_runlines(self, vehicle_pos: pr.Vector2) -> None:
        run_rad = math.radians(self.run_dir)

        # Direction vector of the runline (D) and its perpendicular normal (N)
        dir_vec = pr.Vector2(math.cos(run_rad), math.sin(run_rad))
        normal_vec = pr.Vector2(-dir_vec.y, dir_vec.x)

        # Project vehicle position onto the normal (how far the vehicle is offset from runline origin)
        offset_from_origin = vehicle_pos.x * normal_vec.x + vehicle_pos.y * normal_vec.y

        self.run_offset = offset_from_origin

    def get_closest_runline_position(self, vehicle_pos: pr.Vector2, working_width: float) -> pr.Vector2:
        # 1. Convert run_dir (degrees) to radians
        run_rad = math.radians(self.run_dir)

        # 2. Direction vector of the runline (D) and its perpendicular normal (N)
        dir_vec = pr.Vector2(math.cos(run_rad), math.sin(run_rad))  # D
        normal_vec = pr.Vector2(-dir_vec.y, dir_vec.x)              # N = perpendicular to D

        # 3. Project vehicle position onto normal to find offset from central line
        offset_from_origin = vehicle_pos.x * normal_vec.x + vehicle_pos.y * normal_vec.y

        # 4. Snap to nearest multiple of working width
        snapped_offset = round(offset_from_origin / working_width) * working_width

        # 5. Compute the position of the closest runline:
        #    - Keep the projection along D
        #    - Move to the snapped position along N
        distance_along_dir = vehicle_pos.x * dir_vec.x + vehicle_pos.y * dir_vec.y
        closest_x = dir_vec.x * distance_along_dir + normal_vec.x * snapped_offset
        closest_y = dir_vec.y * distance_along_dir + normal_vec.y * snapped_offset

        return pr.Vector2(closest_x, closest_y)
    
    def get_rotation_angle_0_180(self, vehicle_rotation_rad, run_dir_deg):
        run_dir_rad = math.radians(run_dir_deg)
        runline_vec = (math.cos(run_dir_rad), math.sin(run_dir_rad))
        perp_runline_vec = (-runline_vec[1], runline_vec[0])
        vehicle_vec = (math.cos(vehicle_rotation_rad), math.sin(vehicle_rotation_rad))
        dot = vehicle_vec[0]*runline_vec[0] + vehicle_vec[1]*runline_vec[1]
        dot = max(min(dot, 1.0), -1.0)
        angle_diff = math.acos(dot)
        cross = perp_runline_vec[0]*vehicle_vec[1] - perp_runline_vec[1]*vehicle_vec[0]
        angle_diff_deg = math.degrees(angle_diff) - 90
        return angle_diff_deg

    def get_dir_to_run(self, vehicle_pos: pr.Vector2, closest_runline: pr.Vector2, vehicle_rotation_rad: float):
        # Vector from vehicle to runline
        to_run_x = closest_runline.x - vehicle_pos.x
        to_run_y = closest_runline.y - vehicle_pos.y

        # Normalize to_run vector
        length = math.hypot(to_run_x, to_run_y)
        if length == 0:
            return 0.0
        to_run_x /= length
        to_run_y /= length

        # Vehicle heading vector
        vehicle_vec_x = math.cos(vehicle_rotation_rad)
        vehicle_vec_y = math.sin(vehicle_rotation_rad)

        # Compute signed angle difference using atan2(cross, dot)
        dot = vehicle_vec_x * to_run_x + vehicle_vec_y * to_run_y
        cross = vehicle_vec_x * to_run_y - vehicle_vec_y * to_run_x

        angle_rad = math.atan2(cross, dot)
        angle_deg = math.degrees(angle_rad) - 180

        if angle_deg < 180:
            angle_deg += 180

        return angle_deg 

    def get_desired_rotation(self, wheel_rotation: float, vehicle_pos: pr.Vector2, vehicle_rotation: float, working_width: float) -> None:
        vr = vehicle_rotation

        align_steer = self.get_rotation_angle_0_180(vehicle_rotation - math.pi, self.run_dir)
        closest_runline = self.get_closest_runline_position(vehicle_pos, working_width)

        dx = closest_runline.x - vehicle_pos.x
        dy = closest_runline.y - vehicle_pos.y

        dist = math.hypot(dx, dy)
        dir_to_run = atan2(dy, dx) / (math.pi / 2) * (dist / self.working_width)
 
        rel_rot = degrees(vr) - self.run_dir - 90
        if rel_rot < 0: rel_rot += 360

        if 90 < rel_rot < 270:
            rel_rot = -1
        else:
            rel_rot = 1

        dir_to_run *= rel_rot
        align_steer /= 90 * rel_rot

        self.desired_wheel_rotation = (dir_to_run + align_steer)

    def update(self, wheel_rotation: float, vehicle_pos: pr.Vector2, vehicle_rotation: float, working_width: float) -> None:
        if self.autosteer_enabled:
            self.get_desired_rotation(wheel_rotation, vehicle_pos, vehicle_rotation, working_width)
        else:
            self.desired_wheel_rotation = None