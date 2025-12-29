import pyray as pr
import re

from time import time

class Button:
    def __init__(self, image: pr.Texture, x: int, y: int, bg_color: pr.Color, bg_color_pressed: pr.Color, onclick: object, text: str = "") -> None:
        self.image = image

        self.x = x
        self.y = y
        self.width = self.image.width
        self.height = self.image.height

        self.bg_color = bg_color
        self.bg_color_pressed = bg_color_pressed

        self.hidden = False
        self.selected = False
        self.hovered = False
        self.force_selected = False # This one cannot be changed by the `Button` class so it can be used to keep the button selected. Useful in button lists.

        self.onclick = onclick

        self.text = text

    def update(self, draw_background: bool = False) -> bool:
        # Returns if it was pressed

        if self.hidden: return False

        self.draw(draw_background)

        self.hovered = False

        pos = pr.get_mouse_position()
        if pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height:
            self.hovered = True
        else:
            self.selected = False

        if not pr.is_mouse_button_pressed(0): return

        if self.hovered:
            self.onclick()
            self.selected = True

        return self.selected

    def draw(self, draw_background: bool) -> None:
        if draw_background:
            bg_color = self.bg_color
            if (self.selected or self.hovered or self.force_selected) and self.bg_color_pressed is not None:
                bg_color = self.bg_color_pressed

            pr.draw_rectangle(self.x, self.y, self.width, self.height, bg_color)

        pr.draw_texture(self.image, self.x, self.y, pr.WHITE)
        pr.draw_text(self.text, self.x + 5, self.y + 5, 15, pr.WHITE)

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

class CreatePaddockBox:
    width = 600
    height = 350

    def __init__(self, x: int, y: int, paddock_manager: object) -> None:
        self.x = x
        self.y = y
        self.paddock_manager = paddock_manager

        self.font = pr.Font()

        self.paddock_name_input = TextInput(self.x + 220, self.y + 100, self.width - 230, 30, "", 30, pr.WHITE, pr.GRAY, pr.LIGHTGRAY)

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

        self.active = False

    def on_cancel(self) -> None:
        self.paddock_name_input.text = ""
        self.active = False

    def on_accept(self) -> None:
        if self.paddock_name_input.text in self.paddock_manager.get_paddock_names():
            self.paddock_name_input.bg_color = pr.RED
            return

        self.paddock_name_input.bg_color = pr.LIGHTGRAY
        self.paddock_manager.create_paddock(self.paddock_name_input.text)

        self.active = False

    def update(self) -> None:
        if not self.active: return

        pr.draw_rectangle(self.x, self.y, self.width, self.height, pr.DARKGRAY)
        pr.draw_rectangle(self.x, self.y, self.width, 60, pr.DARKBLUE)
        pr.draw_text_ex(self.font, "Create Paddock", (self.x+10, self.y+10), 30, 1.0, pr.WHITE)

        pr.draw_text_ex(self.font, "Paddock name:", (self.x+10, self.y + 100), 30, 1.0, pr.WHITE)

        self.paddock_name_input.update()

        self.accept_btn.update()
        self.cancel_btn.update()

class InfoBoxSound:
    def __init__(self):
        # This is a lazy singleton
        # I chose to use this because the infobox sounds can be stopped now so they dont overlap. It cannot be a normal (eager) singleton because that is created at runtime before audio is initialized
        if not hasattr(self.__class__, "sound"):
            self.__class__.sound = pr.load_sound("assets/sounds/gpsAlert.ogg")

    def play(self):
        if pr.is_sound_playing(self.sound):
            pr.stop_sound(self.sound)
        pr.play_sound(self.sound)

class InfoBox:
    DURATION = 5
    AUDIO_DELAY = 1 # Delay before playing audio

    WIDTH = 800
    HEIGHT = 100

    FONT_SIZE = 40

    def __init__(self, text: str, info_type: str, remove_infobox: object) -> None:
        self.screen_width = pr.get_screen_width()
        self.screen_height = pr.get_screen_height()

        self.y = 0

        self.text = text
        self.start_time = time()

        self.remove_infobox = remove_infobox
        self.sound = InfoBoxSound()
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
            self.sound.play()
            self.played_sound = True
        
        pr.draw_rectangle(int(self.screen_width / 2 - self.WIDTH / 2), self.y, self.WIDTH, self.HEIGHT, self.color)
        pr.draw_text(self.text, int(self.screen_width / 2 - self.text_width / 2), self.y + 30, self.FONT_SIZE, pr.WHITE)

class Sidebar:
    ITEMS = ["paddock", "A", "nudge", "save", "zoom-in", "zoom-out", "settings", "wheel"]

    BUTTON_WIDTH = 60
    BUTTON_HEIGHT = 60

    PADDING = 5

    def __init__(self, settings: dict[str, any], is_autosteer_enabled: object, set_autosteer: object, paddock_manager: object, set_ab: object, nudge_runlines: object, save: object, zoom_in: object, zoom_out: object) -> None:
        self.screen_width = pr.get_screen_width()
        self.screen_height = pr.get_screen_height()

        self.settings = settings

        self.is_autosteer_enabled = is_autosteer_enabled
        self.set_autosteer = set_autosteer
        self.set_ab = set_ab
        self.nudge_runlines = nudge_runlines
        self.save = save

        self.paddock_manager = paddock_manager

        self.select_paddock = self.paddock_manager.load_paddock
        self.reset_paint = self.paddock_manager.reset_paint
        self.create_paddock = self.paddock_manager.create_paddock
        self.delete_paddock = self.paddock_manager.delete_paddock
        self.toggle_boundary_outline = self.paddock_manager.toggle_marking_boundary_outline
        self.toggle_obstacle_outline = self.paddock_manager.toggle_marking_obstacle_outline
        self.toggle_outline_side = self.paddock_manager.toggle_outline_side

        self.a_pressed = False

        self.zoom_in = zoom_in
        self.zoom_out = zoom_out

        self.buttons: list[Button] = []

        self.bg_color = pr.Color(100, 100, 100, 255)

        w = self.BUTTON_WIDTH + self.PADDING
        h = self.BUTTON_HEIGHT + self.PADDING

        self.click_sound = pr.load_sound("assets/sounds/BtnRelease.wav")

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

            hover_color = pr.DARKGRAY

            if item == "wheel":
                hover_color = None

            self.buttons.append(
                Button(tex, self.screen_width - w, ry, self.bg_color, hover_color, lambda item=item: self.on_button_click(item))
            )

            pr.unload_image(img)

        paddock_sidebar_x = self.screen_width - (self.BUTTON_WIDTH + self.PADDING * 2) * 2
        paddock_sidebar_y = self.buttons[self.ITEMS.index("paddock")].y

        self.paddock_dropdown_x = self.screen_width - (self.BUTTON_WIDTH + self.PADDING * 2) * 2 - (PaddockDropdownSidebar.BUTTON_WIDTH + self.PADDING * 2)
        self.paddock_dropdown_y = self.buttons[self.ITEMS.index("paddock")].y

        self.paddock_sidebar = PaddockSidebar(paddock_sidebar_x, paddock_sidebar_y, self.on_button_click)
        self.paddock_dropdown = None

        self.create_paddock_box = CreatePaddockBox(self.screen_width // 2 - CreatePaddockBox.width // 2, self.screen_height // 2 - CreatePaddockBox.height // 2, self.paddock_manager)
        self.settings_box = SettingsBox(self.screen_width // 2 - SettingsBox.width // 2, self.screen_height // 2 - SettingsBox.height // 2, self.settings["ip_client"], self.settings["port_client"])

    def on_paddock_dropdown_close(self, on_finish_func: object) -> None:
        self.paddock_dropdown = None
        self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("select_paddock")].force_selected = False
        self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("delete_paddock")].force_selected = False

        on_finish_func()

    def show_paddock_dropdown(self, on_finish: object) -> None:
        if len(self.paddock_manager.get_paddock_names()) == 0: return

        self.paddock_dropdown = PaddockDropdownSidebar(self.paddock_dropdown_x, self.paddock_dropdown_y, self.paddock_manager, lambda paddock_name: self.on_paddock_dropdown_close(lambda: on_finish(paddock_name)))

    def on_button_click(self, item: str) -> None:
        print(f"Button: {item} clicked!")

        if pr.is_sound_playing(self.click_sound):
            pr.stop_sound(self.click_sound)

        pr.play_sound(self.click_sound)

        if self.paddock_dropdown is not None and item != "delete_paddock":
            self.paddock_dropdown = None
            self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("delete_paddock")].force_selected = False

        if self.paddock_dropdown is not None and item != "select_paddock":
            self.paddock_dropdown = None
            self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("select_paddock")].force_selected = False

        match item:
            case "paddock":
                if self.paddock_dropdown is not None:
                    self.paddock_dropdown = None
                    self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("select_paddock")].force_selected = False
                    self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("delete_paddock")].force_selected = False

                if self.paddock_sidebar.hidden:
                    self.buttons[self.ITEMS.index("paddock")].force_selected = True
                else:
                    self.buttons[self.ITEMS.index("paddock")].force_selected = False

                self.paddock_sidebar.toggle_hidden()

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

            case "select_paddock":
                if self.paddock_dropdown is not None:
                    self.paddock_dropdown = None
                    self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("select_paddock")].force_selected = False
                    return
                
                self.paddock_dropdown_y = self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("select_paddock")].y
                self.show_paddock_dropdown(self.select_paddock)

                if self.paddock_dropdown is not None:
                    self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("select_paddock")].force_selected = True

            case "reset_paint": self.reset_paint()
            case "create_paddock": self.create_paddock_box.active = not self.create_paddock_box.active
            case "delete_paddock":
                if self.paddock_dropdown is not None:
                    self.paddock_dropdown = None
                    self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("delete_paddock")].force_selected = False
                    return

                self.paddock_dropdown_y = self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("delete_paddock")].y
                self.show_paddock_dropdown(self.delete_paddock)

                if self.paddock_dropdown is not None:
                    self.paddock_sidebar.buttons[self.paddock_sidebar.items.index("delete_paddock")].force_selected = True

            case "toggle_boundary_outline": self.toggle_boundary_outline
            case "toggle_obstacle_outline": self.toggle_obstacle_outline
            case "toggle_outline_side": self.toggle_outline_side

    def send_key_typing(self, char: str | None) -> None:
        if self.settings_box.active:
            if self.settings_box.ip_addr_input.focused:
                if char is None:
                    self.settings_box.ip_addr_input.text = self.settings_box.ip_addr_input.text[:-1]
                elif len(self.settings_box.ip_addr_input.text) <= 15:
                    self.settings_box.ip_addr_input.text += char

            elif self.settings_box.port_input.focused:
                if char is None:
                    self.settings_box.port_input.text = self.settings_box.port_input.text[:-1]
                elif len(self.settings_box.port_input.text) <= 10:
                    if char.isdigit():
                        self.settings_box.port_input.text += char

        elif self.create_paddock_box.active:
            if self.create_paddock_box.paddock_name_input.focused:
                if char is None:
                    self.create_paddock_box.paddock_name_input.text = self.create_paddock_box.paddock_name_input.text[:-1]
                elif not re.compile(r'^[A-Za-z0-9_]+$').match(char): # A-Z, a-z, 0-9, _
                    pass
                elif len(self.create_paddock_box.paddock_name_input.text) <= 20:
                    self.create_paddock_box.paddock_name_input.text += char

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
                button.update(True)

        self.paddock_sidebar.update()

        if self.paddock_dropdown is not None:
            self.paddock_dropdown.update()

        self.settings_box.update()
        self.create_paddock_box.update()

        if not self.settings_box.active:
            self.settings["ip_client"] = self.settings_box.ip
            self.settings["port_client"] = self.settings_box.port

class SubSidebar:
    BUTTON_WIDTH = 60
    BUTTON_HEIGHT = 60

    PADDING = 5

    bg_color = pr.Color(100, 100, 100, 255)

    def __init__(self, x: int, y: int, buttons: list[Button]) -> None:
        self.x = x
        self.y = y

        self.buttons = buttons

        self.width = self.BUTTON_WIDTH + self.PADDING * 2
        self.height = len(self.buttons) * self.BUTTON_HEIGHT + (len(self.buttons) - 1) * self.PADDING + self.PADDING

        self.hidden = True

    def hide(self) -> None:
        self.hidden = True

    def show(self) -> None:
        self.hidden = False

    def toggle_hidden(self) -> None:
        if self.hidden:
            self.show()
        else:
            self.hide()

    def update(self) -> None:
        if self.hidden: return

        pr.draw_rectangle(self.x, self.y, self.width, self.height, self.bg_color)

        for button in self.buttons:
            button.update(True)

class PaddockSidebar(SubSidebar):
    items = ["select_paddock", "reset_paint", "create_paddock", "delete_paddock", "toggle_boundary_outline", "toggle_obstacle_outline", "toggle_outline_side"]
    img_names = ["select_paddock", "erase", "create_paddock", "delete_paddock", "boundary_outline", "obstacle_outline", "boundary_side"]

    def __init__(self, x: int, y: int, onclick: object) -> None:
        self.onclick = onclick

        buttons = []

        w = self.BUTTON_WIDTH + self.PADDING
        h = self.BUTTON_HEIGHT + self.PADDING

        for by, item in enumerate(self.items):
            img = pr.load_image(f"assets/{self.img_names[by]}.png")
            pr.image_resize(img, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)

            tex = pr.load_texture_from_image(img)
            ry = y + by*h

            buttons.append(
                Button(tex, x + self.PADDING, ry, self.bg_color, pr.DARKGRAY, lambda item=item: onclick(item))
            )

        super().__init__(x, y, buttons)

class PaddockDropdownSidebar(SubSidebar):
    BUTTON_WIDTH = 200
    BUTTON_HEIGHT = 20

    bg_color = pr.DARKGRAY

    def __init__(self, x: int, y: int, paddock_manager: object, on_paddock_select: object) -> None:
        self.paddock_manager = paddock_manager
        self.on_paddock_select = on_paddock_select

        buttons = []

        w = self.BUTTON_WIDTH + self.PADDING
        h = self.BUTTON_HEIGHT + self.PADDING

        for by, paddock_name in enumerate(self.paddock_manager.get_paddock_names()):
            tex = pr.Texture()
            tex.width = self.BUTTON_WIDTH
            tex.height = self.BUTTON_HEIGHT

            ry = y + by*h

            buttons.append(
                Button(tex, x + self.PADDING, ry, self.bg_color, pr.LIGHTGRAY, lambda paddock_name=paddock_name: self.on_paddock_select(paddock_name), text=paddock_name)
            )

        super().__init__(x, y, buttons)

        self.hidden = False