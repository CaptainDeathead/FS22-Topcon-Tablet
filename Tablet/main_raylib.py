import pyray as pr
import json
import socket

from course import CourseManager

from UI import Sidebar, Button
from math import atan2, sin, cos, radians, degrees, dist, sqrt
from threading import Thread
from time import sleep

HOST = '0.0.0.0'
PORT = 5001

class Client:
    def __init__(self, is_autosteer_engaged: object, get_desired_wheel_rotation: float | None) -> None:
        self.is_autosteer_engaged = is_autosteer_engaged
        self.get_desired_wheel_rotation = get_desired_wheel_rotation

    def run(self) -> None:
        self.data = {}

        sleep(1)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Connected")
            s.sendall(b'{}')

            while 1:
                try:
                    data = s.recv(1024)
                    if not data:
                        print("No data, leaving")
                        break

                    try:
                        self.data = json.loads(data.decode())
                    except Exception as e:
                        print(f"Inner client try error: {e}")

                    send_data = {
                        "autosteer_status": self.is_autosteer_engaged(),
                        "desired_wheel_rotation": self.get_desired_wheel_rotation()
                    }

                    s.sendall(json.dumps(send_data).encode())

                except Exception as e:
                    print(f"Outer client try error: {e}")

class Vehicle:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.rotation = 0.0
    
    @property
    def rad(self) -> float:
        return radians(self.rotation)

class Trailer:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.rotation = 0.0

    @property
    def rad(self) -> float:
        return radians(self.rotation)

class GPS:
    WIDTH = 1280
    HEIGHT = 800

    WORKING_WIDTH_SCALE = 2.3 # Divide tool working width (m) by this to get scaled

    def __init__(self) -> None:
        self.client = Client(self.is_autosteer_enabled, self.get_desired_wheel_rotation)
        Thread(target=self.client.run, daemon=True).start()

        pr.init_window(self.WIDTH, self.HEIGHT, "TopconX35")
        pr.set_target_fps(60)

        self.camera = pr.Camera2D()
        self.camera.zoom = 1.0
        self.camera.rotation = 0.0

        self.paint_tex = pr.load_render_texture(16000, 16000)

        self.vehicle = Vehicle()
        self.trailer = Trailer()

        self.working_width = 6

        self.zoom = 8.0
        #self.zoom = 1.0

        self.course_manager = CourseManager(self.get_working_width)

        self.sidebar = Sidebar(self.is_autosteer_enabled, self.set_autosteer, self.set_ab, self.zoom_in, self.zoom_out)

        self.main()

        pr.close_window()

    def get_working_width(self) -> float:
        return self.working_width

    def is_autosteer_enabled(self) -> bool:
        return self.course_manager.autosteer_enabled

    def set_autosteer(self, enabled: bool) -> None:
        self.course_manager.autosteer_enabled = enabled

    def get_desired_wheel_rotation(self) -> float | None:
        return self.course_manager.desired_wheel_rotation

    def set_ab(self) -> None:
        self.course_manager.set_ab(self.vehicle.x, self.vehicle.y)

    def update_vt_positions(self) -> None:
        self.vehicle.x = self.client.data.get('vx', 0) + 8000
        self.vehicle.y = self.client.data.get('vz', 0) + 8000
        self.vehicle.rotation = self.client.data.get('vry', 0)

        self.trailer.x = self.client.data.get('tx', 0) + 8000
        self.trailer.y = self.client.data.get('tz', 0) + 8000
        self.trailer.rotation = self.client.data.get('try', 0)

    def rotate(self, origin, point, angle):
        """
        Rotate a point counterclockwise by a given angle around a given origin.

        The angle should be given in radians.
        """
        ox, oy = origin
        px, py = point

        qx = ox + cos(angle) * (px - ox) - sin(angle) * (py - oy)
        qy = oy + sin(angle) * (px - ox) + cos(angle) * (py - oy)
        return qx, qy

    def get_working(self) -> bool:
        on = self.client.data.get('on', False)
        lowered = self.client.data.get('lowered', True)

        if on and lowered:
            return True
        else:
            return False

    def get_working_color(self) -> pr.Color:
        working = self.get_working()

        if working: return pr.Color(0, 150, 0, 128)
        else: return pr.Color(255, 0, 0, 255)

    def zoom_in(self) -> None:
        self.zoom = min(16, self.zoom * 1.5)
    
    def zoom_out(self) -> None:
        self.zoom = max(0.3, self.zoom / 1.5)

    def draw_rotated_line(self, start: pr.Vector2, length: float, angle_deg: float, thickness: float, color, offset: float = 0.0) -> None:
        angle_rad = radians(angle_deg)

        # Perpendicular offset (rotate angle 90° counter-clockwise for left)
        offset_x = -sin(angle_rad) * offset
        offset_y = cos(angle_rad) * offset

        # Apply offset to the start position
        offset_start = pr.Vector2(start.x + offset_x, start.y + offset_y)

        end = pr.Vector2(
            offset_start.x + cos(angle_rad) * length,
            offset_start.y + sin(angle_rad) * length
        )

        pr.draw_line_ex(offset_start, end, thickness, color)

    def is_multiple(self, x: int, y: float, epsilon: float = 0.1) -> bool:
        remainder = x % y
        return remainder < epsilon or abs(remainder - y) < epsilon

    def draw_runlines(self) -> None:
        vehicle_pos = pr.Vector2(self.vehicle.x, self.vehicle.y)
        run_dir = self.course_manager.run_dir
        offset = self.course_manager.run_offset

        # Convert angle to radians and get driving direction vector
        angle_rad = radians(run_dir)
        dir_vec = (cos(angle_rad), sin(angle_rad))
        
        # Get perpendicular vector (line direction)
        line_vec = (-dir_vec[1], dir_vec[0])

        # Project vehicle position onto line direction to find its offset
        vehicle_offset = vehicle_pos.x * line_vec[0] + vehicle_pos.y * line_vec[1]

        # Compute index of closest runline to the vehicle
        rel_offset = vehicle_offset - offset
        closest_line_index = round(rel_offset / self.working_width)

        #num_lines = 50
        num_lines = int((self.WIDTH / self.working_width) / 2) + 5

        # Draw 3 runlines: closest, one before, one after
        for i in range(closest_line_index - num_lines + 1, closest_line_index + num_lines):
            runline_offset = offset + i * self.working_width
            x = line_vec[0] * runline_offset
            y = line_vec[1] * runline_offset

            # Generate long line along driving direction
            length = 100000
            dx = dir_vec[0] * length
            dy = dir_vec[1] * length

            start = (x - dx, y - dy)
            end = (x + dx, y + dy)

            w = 0.04
            color = pr.Color(255, 0, 0, 255)

            if i != closest_line_index:
                w = 0.02
                color = pr.Color(200, 0, 0, 128)

            pr.draw_line_ex(start, end, w * self.zoom, color)

    def main(self) -> None:
        while not pr.window_should_close():
            pr.begin_drawing()
            pr.clear_background((50, 50, 50))

            self.update_vt_positions()

            pr.draw_texture(self.paint_tex.texture, 0, 0, pr.GREEN)

            self.camera.target = pr.Vector2(self.vehicle.x, self.vehicle.y)  # World coords to follow
            self.camera.offset = pr.Vector2(self.WIDTH / 2, self.HEIGHT / 2 + self.HEIGHT / 4)  # Keep centered on screen
            self.camera.zoom = self.zoom
            self.camera.rotation = -self.vehicle.rotation

            pr.begin_mode_2d(self.camera)

            pr.draw_texture(self.paint_tex.texture, 0, 0, pr.GREEN)

            self.draw_runlines()

            poly_left = self.rotate((self.vehicle.x, self.vehicle.y), (self.vehicle.x - 2.5, self.vehicle.y), self.vehicle.rad)
            poly_top = self.rotate((self.vehicle.x, self.vehicle.y), (self.vehicle.x, self.vehicle.y - 5), self.vehicle.rad)
            poly_right = self.rotate((self.vehicle.x, self.vehicle.y), (self.vehicle.x + 2.5, self.vehicle.y), self.vehicle.rad)

            pr.draw_triangle(
                pr.Vector2(poly_left[0], poly_left[1]),
                pr.Vector2(poly_right[0], poly_right[1]),
                pr.Vector2(poly_top[0], poly_top[1]),
                pr.GREEN
            )

            origin = (self.vehicle.x, self.vehicle.y + dist((self.vehicle.x, self.vehicle.y), (self.trailer.x, self.trailer.y)) / 2)
            origin_front = (self.vehicle.x, self.vehicle.y - 10)

            rot_origin = self.rotate((self.vehicle.x, self.vehicle.y), origin, self.vehicle.rad)
            rot_origin_front = self.rotate((self.vehicle.x, self.vehicle.y), origin_front, self.vehicle.rad)

            trailer_left = self.rotate(rot_origin, (rot_origin[0] - self.working_width / 2, rot_origin[1]), self.trailer.rad)
            trailer_right = self.rotate(rot_origin, (rot_origin[0] + self.working_width / 2, rot_origin[1]), self.trailer.rad)

            # Blue guideline
            #pr.draw_line_ex((self.vehicle.x, self.vehicle.y), rot_origin_front, 1, pr.DARKBLUE)

            pr.draw_line_ex((self.vehicle.x, self.vehicle.y), (rot_origin[0], rot_origin[1]), 0.5, pr.BLACK)

            color = self.get_working_color()
            color.a = 255
            pr.draw_line_ex((int(trailer_left[0]), int(trailer_left[1])), (int(trailer_right[0]), int(trailer_right[1])), 1.5, color)

            if self.get_working():
                pr.begin_texture_mode(self.paint_tex)
                pr.draw_line_ex((int(trailer_left[0]), 16000 - int(trailer_left[1])), (int(trailer_right[0]), 16000 - int(trailer_right[1])), 1.5, self.get_working_color())
                pr.end_texture_mode()

            pr.end_mode_2d()

            self.sidebar.update()

            pr.end_drawing()

            if self.client.data.get("wheel_disconnect", False):
                print("Recieved wheel disconnect...")
                self.set_autosteer(False)

            self.course_manager.update(self.client.data.get("wheel_rot", 0.0), pr.Vector2(self.vehicle.x, self.vehicle.y), self.vehicle.rad, self.working_width)

if __name__ == "__main__":
    GPS()