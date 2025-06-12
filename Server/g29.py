from g29py import G29
from time import sleep

class Wheel(G29):
    INTRO_STEER_ACCURACY = 0.01
    STEER_ACCURACY = 0.01 # Percentage of accuracy the rotate functions have (+/-)
    DISCONNECT_DIFF = 0.1 # Percentage limit of how far out dist is from closest_dist is before disconnect

    def __init__(self, on_wheel_disconnect: object) -> None:
        super().__init__()

        self.on_wheel_disconnect = on_wheel_disconnect

        self.listen()

        # Need to move wheel for the script to get data (idk why)
        self.force_constant(0.3)
        sleep(0.2)
        self.force_constant(0.7)
        sleep(0.2)
        self.force_off()

        print("Waiting for wheel...")
        while self.get_state()["steering"] == 0.0:
            sleep(0.1)

        print("Wheel movement detected.")

        self.is_rotating = False

    def rotate_to(self, steer: float, speed: float) -> None:
        speed /= 2

        curr_rot = self.get_state()["steering"]
        dist = abs(steer - curr_rot)

        if dist < self.INTRO_STEER_ACCURACY: return

        closest_dist = dist

        #print(dist, self.INTRO_STEER_ACCURACY)

        self.is_rotating = True

        while dist > self.STEER_ACCURACY:
            curr_rot = self.get_state()["steering"]
            dist = abs(steer - curr_rot)

            if dist < closest_dist:
                closest_dist = dist

            if abs(dist - closest_dist) > self.DISCONNECT_DIFF:
                print("Disconnect")
                self.on_wheel_disconnect()
                break

            curr_speed = max(dist/2, min(speed, 0.125))
            curr_speed = min(max(curr_speed, 0), 0.5)
            #print(curr_speed)

            if steer < curr_rot:
                self.force_constant(0.5 + curr_speed)
            else:
                self.force_constant(0.5 - curr_speed)

        self.force_off()
        self.is_rotating = False

if __name__ == "__main__":
    wheel = Wheel()

    sleep(1)

    wheel.rotate_to(-0.3, 0.5)

    #exit()
    while 1:
        print(wheel.get_state()["steering"])