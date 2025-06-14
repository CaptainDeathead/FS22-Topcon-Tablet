import time
import json
import socket
import os

from traceback import print_exc
from copy import deepcopy
from threading import Thread
from g29 import Wheel

HOST = '0.0.0.0'
PORT = 5001

class DataManager:
    def __init__(self) -> None:
        self.log_path = "/mnt/HardDrive/SteamLibrary/steamapps/compatdata/1248130/pfx/drive_c/users/steamuser/Documents/My Games/FarmingSimulator2022/log.txt"
        self.gps_keyword = "TopconX35"

        self.curr_data = '{}'

    def parse_data(self, data) -> None:
        vehicle_pos = (data['vx'], data['vz'])
        tool_pos = (data['tx'], data['tz'])
        on, lowered = (data['on'], data['lowered'])
        width = data['width']

        print(vehicle_pos, tool_pos, on, lowered, width)

    def run(self) -> None:
        print("Watching log.txt for GPS updates...\n")

        last_inode = None

        while True:
            try:
                with open(self.log_path, "r") as file:
                    file.seek(0, 2)  # Go to the end of the file
                    last_inode = os.fstat(file.fileno()).st_ino

                    while True:
                        # Check if file was rotated or replaced
                        current_inode = os.stat(self.log_path).st_ino
                        if current_inode != last_inode:
                            print("Log file rotated/replaced. Reopening...")
                            break  # Exit inner loop and reopen

                        line = file.readline()

                        if not line:
                            file.seek(0, 1)  # HACK: force buffer refresh
                            time.sleep(0.1)
                            continue

                        if self.gps_keyword in line:
                            data = "{" + line.split("{", 1)[1].replace("'", '"').replace("nil", "null")
                            self.curr_data = data

            except Exception as e:
                print(f"{e}! Continuing...")
                time.sleep(1)  # Avoid spamming errors

class Server:
    def __init__(self) -> None:
        self.wheel_disconnect = False
        self.send_wheel_connect = False

        self.wheel_supported = False

    def on_wheel_disconnect(self) -> None:
        self.wheel_disconnect = True

    def on_connect_pressed(self) -> None:
        self.send_wheel_connect = True

    def run(self, data_manager) -> None:
        Thread(target=data_manager.run, daemon=True).start()

        try:
            wheel = Wheel(self.on_wheel_disconnect, self.on_connect_pressed)
            self.wheel_supported = True
            print("Wheel support enabled.")

        except Exception as e:
            print(f"Error while initializing G29 support! Error: {e}! Autosteer will no longer be available because of this.")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    try:
                        data = conn.recv(1024)
                    except:
                        return

                    if not data:
                        break

                    try:
                        send_data = deepcopy(json.loads(data_manager.curr_data))
                    except Exception as e:
                        print_exc()
                        print(f"Error while Loading re-transmit data (shown above): {e}")
                        print(f"Offending json:")
                        print(send_data)

                    try:
                        data = json.loads(data.decode())

                        wheel.update()

                        if data.get("recieved_wheel_connect"):
                            self.send_wheel_connect = False
                    
                        if data.get("autosteer_status", False) and self.wheel_supported:
                            desired_rotation = data.get("desired_wheel_rotation", None)

                            if desired_rotation is not None:
                                desired_rotation = min(0.9, max(-0.9, desired_rotation))

                                if not wheel.is_rotating:
                                    Thread(target=lambda: wheel.rotate_to(desired_rotation, 0.4), daemon=True).start()
                        else:
                            self.wheel_disconnect = False
                    
                        send_data["desired_wheel_rotation"] = wheel.get_state()["steering"]

                    except Exception as e:
                        print(f"Error: {e}!")
                        print_exc()

                    send_data["wheel_disconnect"] = self.wheel_disconnect
                    send_data["wheel_connect"] = self.send_wheel_connect

                    conn.sendall(json.dumps(send_data).encode())

if __name__ == "__main__":
    while 1:
        data_manager = DataManager()
        Server().run(data_manager)
        print("restarting...")