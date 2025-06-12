import pygame as pg
import json
import socket

from math import atan2, sin, cos, radians, degrees
from vehicle_trailer_simulation import Vehicle, Trailer
from threading import Thread

pg.init()

HOST = '0.0.0.0'
PORT = 5001

class Client:
    def __init__(self) -> None:
        ...

    def run(self) -> None:
        self.data = {}

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Connected")
            s.sendall(b"Connected")

            while 1:
                try:
                    data = s.recv(1024)
                    if not data:
                        break

                    try:
                        self.data = json.loads(data.decode())
                    except Exception as e:
                        print(e)

                    s.sendall(b"Here")
                except Exception as e:
                    print(e)

class Toggle:
    def __init__(self, screen: pg.Surface, x: int, y: int, text: str, on: bool) -> None:
        self.screen = screen
        self.x = x
        self.y = y
        self.text = text

        self.on = on

        font = pg.font.SysFont(None, 40)
        self.font_surface = font.render(self.text, True, (255, 255, 255))

        self.rect = pg.Rect(self.x, self.y, self.font_surface.width + 40, 20)

    def toggle(self) -> None:
        self.on = not self.on

    def draw(self) -> None:
        self.screen.blit(self.font_surface, (self.x, self.y))
        
        if self.on:
            pg.draw.rect(self.screen, (0, 255, 0), (self.x + self.font_surface.width, 0, 40, 20))
            pg.draw.rect(self.screen, (0, 0, 255), (self.x + self.font_surface.width + 35, 0, 10, 20))
        else:
            pg.draw.rect(self.screen, (255, 0, 0), (self.x + self.font_surface.width, 0, 40, 20))
            pg.draw.rect(self.screen, (0, 0, 255), (self.x + self.font_surface.width - 5, 0, 10, 20))

class GPS:
    WIDTH = 1280
    HEIGHT = 800

    WORKING_WIDTH_SCALE = 2.3 # Divide tool working width (m) by this to get scaled

    def __init__(self) -> None:
        self.client = Client()
        Thread(target=self.client.run, daemon=True).start()

        self.screen = pg.display.set_mode((self.WIDTH, self.HEIGHT)) 
        pg.display.set_caption("TopConX35")

        self.clock = pg.time.Clock()

        self.vehicle = Vehicle((0, 0), 0, 10)
        self.trailer = Trailer(self.vehicle, (0, 40), 0, 0)

        self.paint_surface = pg.Surface((16000, 16000)).convert()
        self.paint_surface.fill((120, 120, 120))

        self.working_width = 2.5

        self.zoom_in_img = pg.transform.smoothscale_by(pg.image.load("zoom-in.png"), 0.5).convert_alpha()
        self.zoom_in_rect = pg.Rect(self.WIDTH - 200, 0, self.zoom_in_img.width, self.zoom_in_img.height)

        self.zoom_out_img = pg.transform.smoothscale_by(pg.image.load("zoom-out.png"), 0.5).convert_alpha()
        self.zoom_out_rect = pg.Rect(self.WIDTH - 200 - self.zoom_out_img.width - 20, 0, self.zoom_in_img.width, self.zoom_in_img.height)

        self.set_working_width_btn = pg.font.SysFont(None, 60).render("<->", True, (0, 0, 0), (200, 200, 200))
        self.set_working_width_rect = pg.Rect(20, 0, self.set_working_width_btn.width, self.set_working_width_btn.height)

        self.lower_required_toggle = Toggle(self.screen, 200, 0, "Lower Required: ", True)
        self.on_required_toggle = Toggle(self.screen, 500, 0, "Active Required: ", True)

        self.zoom = 5

        self.buffer = pg.Surface((self.WIDTH, self.HEIGHT)).convert()
        self.buffer_rotate = pg.Surface((self.WIDTH, self.HEIGHT)).convert()

        self.main()

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

    def rotate_image_centered(self, image: pg.Surface, angle: float, x: float, y: float) -> tuple[pg.Surface, pg.Rect]:
        rotated_image = pg.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center=(x, y))

        return rotated_image, new_rect

    def get_working(self) -> bool:
        on = self.client.data.get('on', False)
        lowered = self.client.data.get('lowered', True)

        if self.on_required_toggle.on == on and self.lower_required_toggle.on == lowered:
            return True
        else:
            return False

    def get_working_color(self) -> pg.Color:
        working = self.get_working()

        if working: return (0, 255, 0)
        else: return (255, 0, 0)

    def zoom_in(self) -> None:
        self.zoom = min(8, self.zoom + 1)
    
    def zoom_out(self) -> None:
        self.zoom = max(1, self.zoom - 1)

    def show_set_working_width_popup(self) -> None:
        width_font = pg.font.SysFont(None, 40)
        width_text = "0"
        width_text_height = 100

        numpad_font = pg.font.SysFont(None, 30)
        button_rect = pg.Rect(0, 0, 60, 40)
        numpad = [['7', '8', '9'],
                  ['4', '5', '6'],
                  ['1', '2', '3'],
                  ['CLR', '0', 'OK'],
                  ['-', '.', '-']]

        numpad_rect = pg.Rect(0, 0, button_rect.w * len(numpad[0]), button_rect.h * len(numpad))

        popup_width = 20 + numpad_rect.w + 20
        popup_height = 20 + width_text_height + numpad_rect.h + 20
        popup_rect = pg.Rect(self.WIDTH // 2 - popup_width / 2, self.HEIGHT // 2 - popup_height // 2, popup_width, popup_height)

        button_rects = [[pg.Rect(popup_rect.x + 20 + x * (button_rect.w + 5), popup_rect.y + y * (button_rect.h + 5), button_rect.w, button_rect.h) for x in range(len(numpad[0]))] for y in range(len(numpad))]

        while 1:
            dt = self.clock.tick(60)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()

                elif event.type == pg.MOUSEBUTTONDOWN:
                    for y in range(len(numpad)):
                        for x in range(len(numpad[y])):
                            button_rect = button_rects[y][x].copy()
                            button_rect.y += width_text_height

                            if button_rect.collidepoint(event.pos):
                                if numpad[y][x] == 'CLR':
                                    width_text = "0"
                                elif numpad[y][x] == 'OK':
                                    try:
                                        self.working_width = float(width_text) / self.WORKING_WIDTH_SCALE
                                        return
                                    except:
                                        width_text = "0"
                                elif numpad[y][x] == '-': continue
                                else:
                                    if width_text == "0":
                                        width_text = numpad[y][x]
                                    else:
                                        width_text += numpad[y][x]

            pg.draw.rect(self.screen, (200, 200, 200), popup_rect)

            width_view = width_font.render(width_text, True, (0, 0, 0))
            self.screen.blit(width_view, (popup_rect.centerx - width_view.width / 2, popup_rect.y + 20))

            for y in range(len(numpad)):
                for x in range(len(numpad[y])):
                    if numpad[y][x] == "-": continue

                    button_rect = button_rects[y][x].copy()
                    button_rect.y += width_text_height

                    pg.draw.rect(self.screen, (255, 255, 255), button_rect)
                    self.screen.blit(numpad_font.render(numpad[y][x], True, (0, 0, 0)), button_rect)

            pg.display.update(popup_rect)

    def main(self) -> None:
        while 1:
            dt = self.clock.tick(30)
            self.screen.fill((120, 120, 120))
            self.buffer_rotate.fill((120, 120, 120))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if self.zoom_in_rect.collidepoint(event.pos):
                        self.zoom_in()
                    elif self.zoom_out_rect.collidepoint(event.pos):
                        self.zoom_out()
                    elif self.set_working_width_rect.collidepoint(event.pos):
                        self.show_set_working_width_popup()

                    elif self.lower_required_toggle.rect.collidepoint(event.pos):
                        self.lower_required_toggle.toggle()
                    elif self.on_required_toggle.rect.collidepoint(event.pos):
                        self.on_required_toggle.toggle()

            self.update_vt_positions()

            self.buffer.blit(self.paint_surface, (-self.vehicle.x + self.WIDTH / 2, - self.vehicle.y + self.HEIGHT / 2))
            new_buffer = pg.transform.smoothscale_by(self.buffer, self.zoom)

            self.buffer_rotate.blit(new_buffer, (self.WIDTH / 2 - new_buffer.width / 2, self.HEIGHT / 2 - new_buffer.height / 2))

            poly_left = self.rotate((self.WIDTH / 2, self.HEIGHT / 2), (self.WIDTH / 2 - 2 * self.zoom, self.HEIGHT / 2 + 3 * self.zoom), radians(self.vehicle.rotation))
            poly_top = self.rotate((self.WIDTH / 2, self.HEIGHT / 2), (self.WIDTH / 2, self.HEIGHT / 2 - 3 * self.zoom), radians(self.vehicle.rotation))
            poly_right = self.rotate((self.WIDTH / 2, self.HEIGHT / 2), (self.WIDTH / 2 + 2 * self.zoom, self.HEIGHT / 2 + 3 * self.zoom), radians(self.vehicle.rotation))

            pg.draw.polygon(self.buffer_rotate, (0, 255, 0), [poly_left, poly_top, poly_right])

            origin = self.rotate((self.WIDTH / 2, self.HEIGHT / 2), (self.WIDTH / 2, self.HEIGHT / 2 + 3 * self.zoom), radians(self.vehicle.rotation))

            relative_rotation = self.trailer.rotation

            trailer_left = self.rotate(origin, (origin[0] - self.working_width * self.zoom, origin[1] + 3 * self.zoom), radians(relative_rotation))
            trailer_right = self.rotate(origin, (origin[0] + self.working_width * self.zoom, origin[1] + 3 * self.zoom), radians(relative_rotation))

            pg.draw.line(self.buffer_rotate, (0, 0, 0), origin, ((trailer_left[0] + trailer_right[0])/2, (trailer_left[1] + trailer_right[1])/2))
            pg.draw.line(self.buffer_rotate, self.get_working_color(), trailer_left, trailer_right)

            if self.get_working():
                real_origin = self.trailer.position
                real_trailer_left = self.rotate(real_origin, (real_origin[0] - self.working_width, real_origin[1]), radians(self.trailer.rotation))
                real_trailer_right = self.rotate(real_origin, (real_origin[0] + self.working_width, real_origin[1]), radians(self.trailer.rotation))

                pg.draw.line(self.paint_surface, self.get_working_color(), real_trailer_left, real_trailer_right, width=5)

            img, rect = self.rotate_image_centered(self.buffer_rotate, self.vehicle.rotation, self.WIDTH / 2, self.HEIGHT / 2)
            self.screen.blit(img, rect)

            self.screen.blit(self.zoom_in_img, self.zoom_in_rect)
            self.screen.blit(self.zoom_out_img, self.zoom_out_rect)
            self.screen.blit(self.set_working_width_btn, self.set_working_width_rect)

            self.lower_required_toggle.draw()
            self.on_required_toggle.draw()

            pg.display.set_caption(str(self.clock.get_fps()))

            pg.display.flip()

if __name__ == "__main__":
    GPS()