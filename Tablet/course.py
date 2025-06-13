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

        self.closest_runline = None

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

    def get_side_of_line(self, A: pr.Vector2, B: pr.Vector2, P: pr.Vector2) -> int:
        AB = pr.Vector2(B.x - A.x, B.y - A.y)
        AP = pr.Vector2(P.x - A.x, P.y - A.y)
        
        cross = AB.x * AP.y - AB.y * AP.x

        if cross > 0:
            return -1
        elif cross < 0:
            return 1
        else:
            return 0

    def get_closest_point_on_line(self, A: pr.Vector2, B: pr.Vector2, P: pr.Vector2) -> pr.Vector2:
        AB = pr.Vector2(B.x - A.x, B.y - A.y)
        AP = pr.Vector2(P.x - A.x, P.y - A.y)

        ab_dot_ab = AB.x * AB.x + AB.y * AB.y
        ap_dot_ab = AP.x * AB.x + AP.y * AB.y

        t = ap_dot_ab / ab_dot_ab

        # Clamp to segment if needed
        # t = max(0, min(1, t))  # Uncomment if you want the closest point on the SEGMENT

        closest = pr.Vector2(A.x + AB.x * t, A.y + AB.y * t)
        return closest

    def get_desired_rotation(self, wheel_rotation: float, vehicle_pos: pr.Vector2, vehicle_rotation: float, working_width: float) -> None:
        if self.closest_runline is None: return

        vr = vehicle_rotation

        align_steer = self.get_rotation_angle_0_180(vehicle_rotation - math.pi, self.run_dir)

        closest_runline_point = self.get_closest_point_on_line(self.closest_runline[0], self.closest_runline[1], vehicle_pos)

        dx = closest_runline_point.x - vehicle_pos.x
        dy = closest_runline_point.y - vehicle_pos.y

        dist = math.hypot(dx, dy)
        side = self.get_side_of_line(self.closest_runline[0], self.closest_runline[1], vehicle_pos)
 
        rel_rot = degrees(vr) - self.run_dir - 90
        if rel_rot < 0: rel_rot += 360

        if 90 < rel_rot < 270:
            rel_rot = -1
        else:
            rel_rot = 1

        side *= rel_rot

        align_steer /= 90 * rel_rot
        dir_to_run = side * (dist / self.working_width)

        self.desired_wheel_rotation = (dir_to_run + align_steer)

    def update(self, wheel_rotation: float, vehicle_pos: pr.Vector2, vehicle_rotation: float, working_width: float) -> None:
        if self.autosteer_enabled:
            self.get_desired_rotation(wheel_rotation, vehicle_pos, vehicle_rotation, working_width)
        else:
            self.desired_wheel_rotation = None