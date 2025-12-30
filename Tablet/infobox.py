import pyray as pr

from time import time

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

    WIDTH = 1000
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