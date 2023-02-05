import json
import os
import shutil
import sys


def FPS_step(fps):
    fps_step = 1 / fps  # number of ms between frames
    return fps_step


class Config:
    def __init__(self):
        if os.path.exists('./environment.json'):
            print('Loading settings from environment.json')
        elif os.path.exists('./default_environment.json'):
            shutil.copyfile('./default_environment.json', './environment.json')
            print(f'environment.json has been initialized in {os.getcwd()}')
            with open("README.txt", "r") as read_me:
                for line in read_me:
                    print(line, end="")
        else:
            print("environment_default.json missing")

        if os.path.exists('./environment.json'):
            with open(r'./environment.json', encoding="utf-8") as json_file:
                environment = json.load(json_file)
            self.camera_port = int(environment["camera_port"])
            self.to_email = environment["to_email"]
            self.from_email = environment["from_email"]
            self.from_email_pass = environment["from_email_pass"]
            self.send_emails = environment["send_emails"]
            self.use_live_video_viewer = environment["use_live_video_viewer"]
            self.storage_units = environment["storage_units"].upper()
            if self.storage_units not in ["B", "MB", "KB", "GB"]:
                print(f'System Exiting: Error with storageUnits in environment.json')
                sys.exit()

            self.max_cap_storage = float(environment["max_capture_storage"])
            self.warn_cap_storage = .7 * self.max_cap_storage
            self.fps = float(environment["fps"])
            self.fps_step = FPS_step(self.fps)
            self.file_upload_notification_freq = int(environment["notification_freq"])
            if self.file_upload_notification_freq < 1:
                # [int] Every 1/x file that is uploaded will be announce on terminal. 0 disables announcements
                self.file_upload_notification_freq = sys.maxsize

        else:
            print('System Exiting: Error loading environment.json')
            sys.exit()
