import pyray as pr
import pygame as pg # Only for window sizing
import json
import socket
import os
import sys

from course import CourseManager
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

from UI import Sidebar, Button, InfoBox
from math import atan2, sin, cos, radians, degrees, dist, sqrt
from threading import Thread
from pynput import keyboard
from time import sleep

pg.init()

class Client:
    HOST = '127.0.0.1'
    PORT = 5060

    def __init__(self, is_autosteer_engaged: object, get_desired_wheel_rotation: float | None) -> None:
        self.is_autosteer_engaged = is_autosteer_engaged
        self.get_desired_wheel_rotation = get_desired_wheel_rotation

        self.connected = False

        self.recieved_wheel_connect = False

    def run(self) -> None:
        while 1:
            try:
                self.data = {}

                sleep(1)

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    print(self.HOST, self.PORT)
                    s.connect((self.HOST, self.PORT))
                    print("Connected")
                    self.connected = True
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
                                "desired_wheel_rotation": self.get_desired_wheel_rotation(),
                                "recieved_wheel_connect": self.recieved_wheel_connect
                            }

                            s.sendall(json.dumps(send_data).encode())

                            self.recieved_wheel_connect = False

                        except Exception as e:
                            print(f"Outer client try error: {e}")

            except Exception as e:
                print(f"Client error: {e}!")
                self.connected = False

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
    INFO = pg.display.Info()
    WIDTH = INFO.current_w
    HEIGHT = INFO.current_h

    DEFAULT_WORK_WIDTH = 6

    PAINT_CYCLES = ((False, False), (True, False), (False, True), (True, True)) # (lowered, on) required
    GRID_SQUARE_SIZE = 100

    def __init__(self) -> None:
        self.client = Client(self.is_autosteer_enabled, self.get_desired_wheel_rotation)
        Thread(target=self.client.run, daemon=True).start()

        pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT)
        pr.init_window(self.WIDTH, self.HEIGHT, "TopconX35")
        pr.set_target_fps(60)
        pr.toggle_fullscreen()

        pr.init_audio_device()

        icon = pr.load_image("logo.png")
        pr.set_window_icon(icon)
        pr.unload_image(icon)

        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.keyboard_listener.setDaemon(True)
        self.keyboard_listener.start()

        self.pressed_keys = []
        self.infoboxes = []

        self.load_settings()

        self.zoom = 2.0
        self.mag = 16

        self.DEFAULT_WORK_WIDTH *= self.mag

        self.working_width = self.DEFAULT_WORK_WIDTH
        self.paint_cycle_index = 3

        self.course_manager = CourseManager(self.get_working_width)
        
        self.autosteer_engage_sound = pr.load_sound("assets/sounds/gpsEngage.mp3")
        self.autosteer_disengage_sound = pr.load_sound("assets/sounds/gpsDisengage.ogg")

        self.camera = pr.Camera2D()
        self.camera.zoom = 1.0
        self.camera.rotation = 0.0

        self.paint_tex = pr.load_render_texture(16000, 16000)
        
        """
        grid_vectors layout:
        {
            -8: {
                -1: {
                    [(..., ...),]
                }
            }
        }
        """
        self.grid_vectors = {}

        self.load_map_information()

        self.vehicle = Vehicle()
        self.trailer = Trailer()

        self.sidebar = Sidebar(self.is_autosteer_enabled, self.set_autosteer, self.reset_paint, self.set_ab, self.nudge_runlines, self.save, self.zoom_in, self.zoom_out)

        self.main()

        pr.close_window()

    def load_settings(self) -> None:
        try:
            with open("settings.json", "r") as f:
                settings = json.loads(f.read())

            self.client.HOST = settings["ip_client"]
            self.client.PORT = int(settings["port_client"])

        except Exception as e:
            print(f"Error while loading settings! Error: {e}.")
            self.infoboxes.append(InfoBox("Error while loading settings!", "error", self.remove_infobox))

    def get_working_width(self) -> float:
        return self.working_width

    def is_autosteer_enabled(self) -> bool:
        return self.course_manager.autosteer_enabled

    def set_autosteer(self, enabled: bool) -> None:
        if self.course_manager.autosteer_enabled and not enabled:
            pr.play_sound(self.autosteer_disengage_sound)
            self.infoboxes.append(InfoBox("Autosteer disengaged.", 'info', self.remove_infobox))
        elif not self.course_manager.autosteer_enabled and enabled:
            pr.play_sound(self.autosteer_engage_sound)
            self.infoboxes.append(InfoBox("Autosteer engaged.", 'info', self.remove_infobox))

        self.course_manager.autosteer_enabled = enabled

    def get_desired_wheel_rotation(self) -> float | None:
        return self.course_manager.desired_wheel_rotation

    def reset_paint(self) -> None:
        self.paint_tex = pr.load_render_texture(16000, 16000)
        self.infoboxes.append(InfoBox("Paint data reset!", 'warning', self.remove_infobox))

    def set_ab(self) -> None:
        self.course_manager.set_ab(self.vehicle.x, self.vehicle.y)

        if self.course_manager.a_point is None:
            self.infoboxes.append(InfoBox("B point set.", 'info', self.remove_infobox))
        else:
            self.infoboxes.append(InfoBox("A point set.", 'info', self.remove_infobox))

    def nudge_runlines(self) -> None:
        self.course_manager.nudge_runlines(pr.Vector2(self.vehicle.x, self.vehicle.y))
        self.infoboxes.append(InfoBox("Runlines nudged to vehicle position.", 'info', self.remove_infobox))

    def remove_infobox(self, infobox: InfoBox) -> None:
        self.infoboxes.remove(infobox)

    def cycle_paint_requirements(self) -> None:
        self.paint_cycle_index = (self.paint_cycle_index + 1) % len(self.PAINT_CYCLES)

        on, lowered = self.PAINT_CYCLES[self.paint_cycle_index]

        if not on and not lowered:
            infobox_text = "always"
        elif not on and lowered:
            infobox_text = "when lowered"
        elif on and not lowered:
            infobox_text = "when on"
        else:
            infobox_text = "when on & lowered"

        self.infoboxes.append(InfoBox(f"Paint requirements: {infobox_text}.", 'info', self.remove_infobox))

    def on_key_press(self, key) -> None:
        # Add key to the set
        self.pressed_keys.append(key)

        # Check for Ctrl + Shift + A
        if (keyboard.Key.ctrl_l in self.pressed_keys or keyboard.Key.ctrl_r in self.pressed_keys) and \
        (keyboard.Key.shift in self.pressed_keys or keyboard.Key.shift_r in self.pressed_keys): 
            if key == keyboard.KeyCode.from_char('A'):
                self.set_ab()
            elif key == keyboard.KeyCode.from_char('N'):
                self.nudge_runlines()
            elif key == keyboard.KeyCode.from_char('R'):
                self.cycle_paint_requirements()
            elif key == keyboard.Key.enter:
                self.set_autosteer(not self.is_autosteer_enabled())

    def on_key_release(self, key) -> None:
        try:
            self.pressed_keys.remove(key)
        except Exception as e:
            print(f"Error when removing keys: {e}!")

    def load_map_information(self) -> None:
        """
        if os.path.isfile("paint.png"):
            image = pr.load_image("paint.png")
            texture = pr.load_texture_from_image(image)
            pr.unload_image(image)

            pr.begin_texture_mode(self.paint_tex)
            pr.draw_texture(texture, 0, 0, pr.GREEN)
            pr.end_texture_mode()
        else:
            print(f"Paint texture (paint.png) file doesn't exist! Previous paint data cleared.")
            self.infoboxes.append(InfoBox("Paint texture file doesn't exist!", 'warning', self.remove_infobox))
        """

        if os.path.isfile("ab.txt"):
            with open("ab.txt", "r") as f:
                ab_dir, ab_offset = f.read().split(",")

                self.course_manager.run_dir = float(ab_dir)
                self.course_manager.run_offset = float(ab_offset)
        else:
            print(f"AB data file (ab.txt) doesn't exist! AB data reset.")
            self.infoboxes.append(InfoBox("AB data file (ab.txt) doesn't exist!", 'warning', self.remove_infobox))

    def save(self) -> None:
        #image = pr.load_image_from_texture(self.paint_tex.texture)
        #pr.export_image(image, "paint.png")

        with open("ab.txt", "w") as f:
            f.write(f"{self.course_manager.run_dir},{self.course_manager.run_offset}")

        self.infoboxes.append(InfoBox("Data save successful!", 'info', self.remove_infobox))

    def update_vt_positions(self) -> None:
        self.vehicle.x = self.client.data.get('vx', 0)*2 + 8000
        self.vehicle.y = self.client.data.get('vz', 0)*2 + 8000
        self.vehicle.rotation = self.client.data.get('vry', 0)

        self.trailer.x = self.client.data.get('tx', 0)*2 + 8000
        self.trailer.y = self.client.data.get('tz', 0)*2 + 8000
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

        on_required, lower_required = self.PAINT_CYCLES[self.paint_cycle_index]

        if (on or not on_required) and (lowered or not lower_required):
            return True
        else:
            return False

    def get_working_color(self) -> pr.Color:
        working = self.get_working()

        if working: return pr.Color(0, 150, 0, 128)
        else: return pr.Color(255, 0, 0, 255)

    def zoom_in(self) -> None:
        self.zoom = min(2*(self.mag/4), self.zoom * 1.5)
    
    def zoom_out(self) -> None:
        self.zoom = max(0.3/(self.mag/4), self.zoom / 1.5)

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

    def get_deep_size(self, obj: object, seen=None):
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        seen.add(obj_id)
        size = sys.getsizeof(obj)

        if isinstance(obj, dict):
            size += sum(self.get_deep_size(k, seen) + self.get_deep_size(v, seen) for k, v in obj.items())
        elif hasattr(obj, '__dict__'):
            size += self.get_deep_size(vars(obj), seen)
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            size += sum(self.get_deep_size(i, seen) for i in obj)

        return size

    def draw_runlines(self) -> None:
        if self.working_width == 0: self.working_width = self.DEFAULT_WORK_WIDTH

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

            pr.draw_line_ex(start, end, w * self.zoom * self.mag, color)

            if i == closest_line_index:
                self.course_manager.closest_runline = (pr.Vector2(start[0], start[1]), pr.Vector2(end[0], end[1]))

    def draw_worked_vectors(self) -> None:
        start_x, start_y = int((self.vehicle.x - self.WIDTH / 2 - 100) // self.GRID_SQUARE_SIZE), int((self.vehicle.y - self.HEIGHT / 2 + 100) // self.GRID_SQUARE_SIZE)
        end_x, end_y = int((self.vehicle.x + self.WIDTH / 2 - 100) // self.GRID_SQUARE_SIZE), int((self.vehicle.y + self.HEIGHT / 2 + 100) // self.GRID_SQUARE_SIZE)

        for x in range(start_x, end_x+1):
            if self.grid_vectors.get(x, None) is None: continue

            for y in range(start_y, end_y+1):
                if self.grid_vectors[x].get(y, None) is None: continue

                for vector in self.grid_vectors[x][y]:
                    pr.draw_line_ex(vector[0], vector[1], 1, pr.GREEN)

    def main(self) -> None:
        while not pr.window_should_close():
            pr.begin_drawing()
            pr.clear_background((50, 50, 50))

            self.update_vt_positions()
            self.working_width = self.client.data.get("work_width" * self.mag, self.working_width)

            self.camera.target = pr.Vector2(self.vehicle.x, self.vehicle.y)  # World coords to follow
            self.camera.offset = pr.Vector2(self.WIDTH / 2, self.HEIGHT / 2 + self.HEIGHT / 4)  # Keep centered on screen
            self.camera.zoom = self.zoom
            self.camera.rotation = -self.vehicle.rotation

            pr.begin_mode_2d(self.camera)

            #self.draw_worked_vectors()
            pr.draw_texture(self.paint_tex.texture, 0, 0, pr.GREEN)

            self.draw_runlines()

            origin = (self.vehicle.x, self.vehicle.y + dist((self.vehicle.x, self.vehicle.y), (self.trailer.x, self.trailer.y)) / 10000)
            origin_front = (self.vehicle.x, self.vehicle.y - self.mag)

            rot_origin = self.rotate((self.vehicle.x, self.vehicle.y), origin, self.vehicle.rad)
            rot_origin_front = self.rotate((self.vehicle.x, self.vehicle.y), origin_front, self.vehicle.rad)

            x, y = rot_origin_front

            poly_left = self.rotate((x, y), (x - 2.5*self.mag/2, y), self.vehicle.rad)
            poly_top = self.rotate((x, y), (x, y - 5*self.mag/2), self.vehicle.rad)
            poly_right = self.rotate((x, y), (x + 2.5*self.mag/2, y), self.vehicle.rad)

            pr.draw_triangle(
                pr.Vector2(poly_left[0], poly_left[1]),
                pr.Vector2(poly_right[0], poly_right[1]),
                pr.Vector2(poly_top[0], poly_top[1]),
                pr.GREEN
            )

            trailer_left = self.rotate(rot_origin, (rot_origin[0] - self.working_width / 2, rot_origin[1]), self.trailer.rad)
            trailer_right = self.rotate(rot_origin, (rot_origin[0] + self.working_width / 2, rot_origin[1]), self.trailer.rad)

            trailer_left = (trailer_left[0], trailer_left[1])
            trailer_right = (trailer_right[0], trailer_right[1])

            # Blue guideline
            #pr.draw_line_ex((self.vehicle.x, self.vehicle.y), rot_origin_front, 1, pr.DARKBLUE)

            pr.draw_line_ex(rot_origin_front, (rot_origin[0], rot_origin[1]), 0.5, pr.BLACK)

            color = self.get_working_color()
            color.a = 255
            pr.draw_line_ex(trailer_left, trailer_right, 1.5*self.mag/2, color)

            if self.get_working():
                gx, gy = int(rot_origin[0] // self.GRID_SQUARE_SIZE), int(rot_origin[1] // self.GRID_SQUARE_SIZE)

                if self.grid_vectors.get(gx, None) is None:
                    self.grid_vectors[gx] = {}

                if self.grid_vectors[gx].get(gy, None) is None:
                    self.grid_vectors[gx][gy] = [] 

                #self.grid_vectors[gx][gy].append((trailer_left, trailer_right))

                pr.begin_texture_mode(self.paint_tex)
                pr.draw_line_ex((int(trailer_left[0]), 16000 - int(trailer_left[1])), (int(trailer_right[0]), 16000 - int(trailer_right[1])), 1.5*self.mag/2, self.get_working_color())
                pr.end_texture_mode()

            pr.end_mode_2d()

            if not self.client.connected and len(self.infoboxes) == 0:
                self.infoboxes.append(InfoBox("No connection!", 'error', self.remove_infobox))

            self.sidebar.update()

            for infobox in self.infoboxes:
                infobox.update()

            pr.draw_fps(10, 10)
            pr.draw_text(f"{(self.get_deep_size(self.grid_vectors) / 1_000_000):.2f}MB vectors", 10, 30, 30, pr.GREEN)

            pr.end_drawing()

            if self.client.data.get("wheel_connect", False):
                self.client.recieved_wheel_connect = True
                self.set_autosteer(True)

            elif self.client.data.get("wheel_disconnect", False):
                print("Recieved wheel disconnect...")
                self.set_autosteer(False)

            self.course_manager.update(self.client.data.get("wheel_rot", 0.0), pr.Vector2(self.vehicle.x, self.vehicle.y), self.vehicle.rad, self.working_width)

        self.save()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        HOST = sys.argv[1]

    GPS()