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
        self.selected = False

        self.onclick = onclick

    def update(self, draw_background: bool = False) -> None:
        if self.hidden: return

        self.draw(draw_background)

        if not pr.is_mouse_button_pressed(0): return

        pos = pr.get_mouse_position()
        if pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height:
            self.onclick()
            self.selected = True
        else:
            self.selected = False

    def draw(self, draw_background: bool) -> None:
        if draw_background:
            bg_color = self.bg_color
            if self.selected:
                bg_color = self.bg_color_pressed

            pr.draw_rectangle(self.x, self.y, self.width, self.height, bg_color)

        pr.draw_texture(self.image, self.x, self.y, pr.WHITE)

class TextInput:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font_size: int, color: pr.Color, bg_color: pr.Color, bg_selected_color: pr.Color) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.font_size = font_size

        self.color = color
        self.bg_color = bg_color
        self.bg_selected_color = bg_selected_color

        tex = pr.Texture()
        tex.width = self.width
        tex.height = self.height
        self.button = Button(tex, self.x, self.y, self.bg_color, self.bg_selected_color, lambda: None)

        self.font = pr.Font()
        self.text = text

    @property
    def focused(self) -> bool:
        return self.button.selected

    def update(self) -> None:
        self.button.update(True)

        pr.draw_text_ex(self.font, self.text, (self.x + 5, self.y), self.font_size, 1.0, self.color)

class SettingsBox:
    width = 400
    height = 350

    def __init__(self, x: int, y: int, default_ip: str, default_port: int) -> None:
        self.x = x
        self.y = y

        self.font = pr.Font()

        self.default_ip = default_ip
        self.default_port = default_port

        self.ip = default_ip
        self.port = default_port

        self.ip_addr_input = TextInput(self.x + 150, self.y + 100, self.width - 160, 30, self.ip, 30, pr.WHITE, pr.GRAY, pr.LIGHTGRAY)
        self.port_input = TextInput(self.x + 150, self.y + 150, self.width - 160, 30, str(self.port), 30, pr.WHITE, pr.GRAY, pr.LIGHTGRAY)

        img = pr.load_image("assets/tick.png")
        pr.image_resize(img, img.width*2, img.height*2)
        tex = pr.load_texture_from_image(img)
        pr.unload_image(img)
        self.accept_btn = Button(tex, self.x + self.width - tex.width, self.y + self.height - tex.height, pr.BLANK, pr.BLANK, self.on_accept)

        img = pr.load_image("assets/cross.png")
        pr.image_resize(img, img.width*2, img.height*2)
        tex = pr.load_texture_from_image(img)
        pr.unload_image(img)
        self.cancel_btn = Button(tex, self.x, self.y + self.height - tex.height, pr.BLANK, pr.BLANK, self.on_cancel)

        self.restart_required = False
        self.active = False

    def on_cancel(self) -> None:
        self.ip = self.default_ip
        self.port = self.default_port

        self.ip_addr_input.text = self.ip
        self.port_input.text = str(self.port)

        self.active = False

    def on_accept(self) -> None:
        self.restart_required = True

        self.active = False

    def update(self) -> None:
        self.ip = self.ip_addr_input.text
        self.port = int(self.port_input.text)

        if not self.active: return

        pr.draw_rectangle(self.x, self.y, self.width, self.height, pr.DARKGRAY)
        pr.draw_rectangle(self.x, self.y, self.width, 60, pr.DARKBLUE)
        pr.draw_text_ex(self.font, "Settings", (self.x+10, self.y+10), 30, 1.0, pr.WHITE)

        pr.draw_text_ex(self.font, "Host (IP):", (self.x+10, self.y + 100), 30, 1.0, pr.WHITE)
        pr.draw_text_ex(self.font, "Port:", (self.x+10, self.y + 150), 30, 1.0, pr.WHITE)

        self.ip_addr_input.update()
        self.port_input.update()

        self.accept_btn.update()
        self.cancel_btn.update()

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

    def __init__(self, settings: dict[str, any], is_autosteer_enabled: object, set_autosteer: object, reset_paint: object, set_ab: object, nudge_runlines: object, save: object, zoom_in: object, zoom_out: object) -> None:
        self.screen_width = pr.get_screen_width()
        self.screen_height = pr.get_screen_height()

        self.settings = settings

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

        self.settings_box = SettingsBox(self.screen_width // 2 - SettingsBox.width // 2, self.screen_height // 2 - SettingsBox.height // 2, self.settings["ip_client"], self.settings["port_client"])

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
            case "settings": self.settings_box.active = not self.settings_box.active
            case "wheel": self.set_autosteer(not self.is_autosteer_enabled())

    def send_key_typing(self, char: str | None) -> None:
        if self.settings_box.active:
            if self.settings_box.ip_addr_input.focused:
                if char is None:
                    self.settings_box.ip_addr_input.text = self.settings_box.ip_addr_input.text[:-1]
                elif len(self.settings_box.ip_addr_input.text) <= 10:
                    self.settings_box.ip_addr_input.text += char

            elif self.settings_box.port_input.focused:
                if char is None:
                    self.settings_box.port_input.text = self.settings_box.port_input.text[:-1]
                elif len(self.settings_box.port_input.text) <= 10:
                    if char.isdigit():
                        self.settings_box.port_input.text += char

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

        self.settings_box.update()

        if not self.settings_box.active:
            self.settings["ip_client"] = self.settings_box.ip
            self.settings["port_client"] = self.settings_box.port