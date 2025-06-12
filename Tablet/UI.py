import pyray as pr

class Button:
    def __init__(self, image: pr.Texture, x: int, y: int, bg_color: pr.Color, bg_color_pressed: pr.Color, onclick: object) -> None:
        self.image = image

        self.x = x
        self.y = y
        self.width = self.image.width
        self.height = self.image.height

        self.bg_color = bg_color
        self.bg_color_pressed = bg_color_pressed

        self.onclick = onclick

    def update(self, draw_background: bool = False) -> None:
        self.draw(draw_background)

        if not pr.is_mouse_button_pressed(0): return

        pos = pr.get_mouse_position()
        if pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.width:
            self.onclick()

    def draw(self, draw_background: bool) -> None:
        if draw_background:
            pr.draw_rectangle(self.x, self.y, self.width, self.height, self.bg_color)

        pr.draw_texture(self.image, self.x, self.y, pr.WHITE)

class Sidebar:
    ITEMS = ["paddock", "runline_select", "AB", "nudge", "runline_save", "zoom-in", "zoom-out", "wheel"]

    BUTTON_WIDTH = 60
    BUTTON_HEIGHT = 60

    PADDING = 5

    def __init__(self, is_autosteer_enabled: object, set_autosteer: object, set_ab: object, zoom_in: object, zoom_out: object) -> None:
        self.screen_width = pr.get_screen_width()
        self.screen_height = pr.get_screen_height()

        self.is_autosteer_enabled = is_autosteer_enabled
        self.set_autosteer = set_autosteer
        self.set_ab = set_ab

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
            else:
                ry = y*h

            self.buttons.append(
                Button(tex, self.screen_width - w, ry, self.bg_color, self.bg_color, lambda item=item: self.on_button_click(item))
            )

            pr.unload_image(img)

    def on_button_click(self, item: str) -> None:
        print(f"Button: {item} clicked!")

        match item:
            case "AB": self.set_ab()
            case "zoom-in": self.zoom_in()
            case "zoom-out": self.zoom_out()
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