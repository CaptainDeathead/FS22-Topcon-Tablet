import pyray as pr

from time import time

class Button:
    def __init__(self, image: pr.Texture, x: int, y: int, bg_color: pr.Color, bg_color_pressed: pr.Color, onclick: object) -> None:
        self.image = image

        self.x = x
        self.y = y
        self.width = self.image.width
        self.height = self.image.height

        self.bg_color = bg_color
        self.bg_color_pressed = bg_color_pressed

        self.hidden = False

        self.onclick = onclick

    def update(self, draw_background: bool = False) -> None:
        if self.hidden: return

        self.draw(draw_background)

        if not pr.is_mouse_button_pressed(0): return

        pos = pr.get_mouse_position()
        if pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.width:
            self.onclick()

    def draw(self, draw_background: bool) -> None:
        if draw_background:
            pr.draw_rectangle(self.x, self.y, self.width, self.height, self.bg_color)

        pr.draw_texture(self.image, self.x, self.y, pr.WHITE)

class InfoBox:
    DURATION = 5
    AUDIO_DELAY = 1 # Delay before playing audio

    WIDTH = 800
    HEIGHT = 100

    FONT_SIZE = 40

    def __init__(self, text: str, info_type: str, remove_infobox: object) -> None:
        self.screen_width = pr.get_screen_width()
        self.screen_height = pr.get_screen_height()

        self.text = text
        self.start_time = time()

        self.remove_infobox = remove_infobox
        self.sound = pr.load_sound("assets/sounds/gpsAlert.ogg")
        self.played_sound = False

        self.info_type = info_type

        if info_type == 'info':
            self.color = pr.GREEN
        elif info_type == 'warning':
            self.color = pr.ORANGE
        elif info_type == 'error':
            self.color = pr.RED
        else:
            print("Error when making infobox! Error: No valid info_type specified.")
            self.color = pr.PURPLE

        self.text_width = pr.measure_text(self.text, self.FONT_SIZE)

    def update(self) -> None:
        if time() - self.start_time >= self.DURATION:
            self.remove_infobox(self)
            return
        elif time() - self.start_time >= self.AUDIO_DELAY and not self.played_sound:
            pr.play_sound(self.sound)
            self.played_sound = True
        
        pr.draw_rectangle(int(self.screen_width / 2 - self.WIDTH / 2), 0, self.WIDTH, self.HEIGHT, self.color)
        pr.draw_text(self.text, int(self.screen_width / 2 - self.text_width / 2), 30, self.FONT_SIZE, pr.WHITE)

class Sidebar:
    ITEMS = ["paddock", "A", "nudge", "save", "zoom-in", "zoom-out", "settings", "wheel"]

    BUTTON_WIDTH = 60
    BUTTON_HEIGHT = 60

    PADDING = 5

    def __init__(self, is_autosteer_enabled: object, set_autosteer: object, reset_paint: object, set_ab: object, nudge_runlines: object, save: object, zoom_in: object, zoom_out: object) -> None:
        self.screen_width = pr.get_screen_width()
        self.screen_height = pr.get_screen_height()

        self.is_autosteer_enabled = is_autosteer_enabled
        self.set_autosteer = set_autosteer
        self.reset_paint = reset_paint
        self.set_ab = set_ab
        self.nudge_runlines = nudge_runlines
        self.save = save

        self.a_pressed = False

        self.zoom_in = zoom_in
        self.zoom_out = zoom_out

        self.buttons: list[Button] = []

        self.bg_color = pr.Color(100, 100, 100, 255)

        w = self.BUTTON_WIDTH + self.PADDING
        h = self.BUTTON_HEIGHT + self.PADDING

        for y, item in enumerate(self.ITEMS):
            img = pr.load_image(f"assets/{item}.png")
            pr.image_resize(img, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)

            tex = pr.load_texture_from_image(img)

            if y == len(self.ITEMS) - 1:
                ry = self.screen_height - h
            elif y == len(self.ITEMS) - 2:
                ry = self.screen_height - h * 2
            else:
                ry = y*h

            self.buttons.append(
                Button(tex, self.screen_width - w, ry, self.bg_color, self.bg_color, lambda item=item: self.on_button_click(item))
            )

            pr.unload_image(img)

    def on_button_click(self, item: str) -> None:
        print(f"Button: {item} clicked!")

        match item:
            case "paddock": self.reset_paint()
            case "A":
                self.a_pressed = not self.a_pressed

                if self.a_pressed:
                    img = pr.load_image("assets/flag.png")
                    pr.image_resize(img, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
                else:
                    img = pr.load_image("assets/A.png")
                    pr.image_resize(img, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)

                tex = pr.load_texture_from_image(img)
                self.buttons[self.ITEMS.index("A")].image = tex

                self.set_ab()

            case "nudge": self.nudge_runlines()
            case "save": self.save()
            case "zoom-in": self.zoom_in()
            case "zoom-out": self.zoom_out()
            case "settings": ...
            case "wheel": self.set_autosteer(not self.is_autosteer_enabled())

    def get_wheel_connected_color(self) -> pr.Color:
        if self.is_autosteer_enabled(): return pr.GREEN
        else: return pr.RED

    def update(self) -> None:
        pr.draw_rectangle(self.screen_width - self.BUTTON_WIDTH - self.PADDING * 2, 0, self.BUTTON_WIDTH + self.PADDING * 2, self.screen_height, self.bg_color)

        for button in self.buttons:
            if self.buttons.index(button) == len(self.buttons) - 1:
                # Is wheel
                button.bg_color = self.get_wheel_connected_color()
                button.update(True)
            else:
                button.update(False)