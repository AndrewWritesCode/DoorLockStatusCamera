from datetime import datetime
import os
import sys


def byte_unit_converter(value, in_unit, out_unit):
    byte_unit = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
    if (in_unit in byte_unit) and (out_unit in byte_unit):
        value *= (byte_unit[in_unit] / byte_unit[out_unit])
        return value
    else:
        print('Byte conversion error')


def dir_size(path, units="GB"):
    byte_count = 0
    for path, dirs, files in os.walk(path):
        for file in files:
            filepath = os.path.join(path, file)
            byte_count += os.path.getsize(filepath)
    return byte_unit_converter(byte_count, "B", units)


def file_size(filepath, units="GB"):
    return byte_unit_converter(os.path.getsize(filepath), "B", units)


class FileManager:
    def __init__(self, config):
        cap_dir = os.path.join(os.getcwd(), 'captures')
        if not os.path.exists(cap_dir):
            try:
                os.mkdir(cap_dir)
            except OSError:
                print(f'Could not create {cap_dir} as data_directory...')
                print('Terminating program...')
                sys.exit()
        else:
            print('Using existing data directory...')

        self.root_dir = os.getcwd()
        self.cap_dir = cap_dir
        self.cap_size = dir_size(self.cap_dir, config.storage_units)
        self.max_cap_size = config.max_cap_storage
        print(f'{round(self.cap_size, 4)}{config.storage_units} of images are already saved to Sentry Storage...')
        self.current_date = None
        self.date_string = None
        self.today_dir = None
        self.create_today_dir()
        print(f'Saving images to {self.today_dir}')
        self.storage_units = config.storage_units
        self.today_size = dir_size(self.today_dir, self.storage_units)
        print(f'Daily directory size initializing at {round(self.today_size, 4)}{config.storage_units}')
        self.time_last_cap = None

    def update_today_size(self):
        self.today_size = dir_size(self.today_dir, self.storage_units)

    def update_cap_size(self):
        self.cap_size = dir_size(self.cap_dir, self.storage_units)

    def create_today_dir(self):
        self.current_date = datetime.now()
        self.date_string = f'{self.current_date.month}m{self.current_date.day}d{self.current_date.year}y'
        self.today_dir = os.path.join(self.cap_dir, self.date_string)
        if not os.path.exists(self.today_dir):
            os.mkdir(self.today_dir)

    def is_storage_full(self):
        if self.max_cap_size < self.cap_size:
            # First recalibrate cap_size
            self.update_cap_size()
            # Now check again if past max storage
            if self.max_cap_size < self.cap_size:
                print('Capture Storage has reached limit: now terminating program...')
                print(f'Clear disk space in {self.cap_dir}')
