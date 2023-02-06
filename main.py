import sys
import cv2
import os
import time
from setup import Config
from email_handler import EmailHandler
from file_manager import FileManager, file_size
from datetime import datetime

# TODO: Motion Sensing, Multiple Cameras, Video Streaming (vs frames), User-Defined save dir


def main():
    conf = Config()
    email_handler = EmailHandler(conf)
    file_manager = FileManager(conf)

    email_handler.send_email('Door Sentry Activated', 'Door Sentry is initializing')

    # initializes the time for fps calculations
    file_manager.time_last_cap = time.time()

    # checks if the camera feed is opened
    try:
        print('Accessing Camera...')
        cap = cv2.VideoCapture(conf.camera_port, cv2.CAP_DSHOW)  # takes the first available camera on computer
    except ConnectionRefusedError:
        print('System Exiting: Unable to establish video link')
        sys.exit()

    def terminate_program():
        cap.release()
        cv2.destroyAllWindows()
        sys.exit()

    sent_daily_warning_email = False
    capture_image = True

    if cap.isOpened():
        print('Camera Accessed...')
    print(file_manager.today_dir)
    while cap.isOpened():
        # captures a frame each loop
        ret, frame = cap.read()
        if ret:
            # displays the current frame (if enabled in environment.json)
            if conf.use_live_video_viewer:
                cv2.imshow(f'VideoStream Camera: {conf.camera_port}', frame)

            # Press 'q' on keyboard to break loop and end program
            if cv2.waitKey(25) & 0xFF == ord('q'):  # TODO: add exit option without video window
                print(f'System Exiting: {file_manager.cap_size}{conf.storage_units} of '
                      f'{conf.max_cap_storage}{conf.storage_units} '
                      f'allotted storage used')
                email_handler.send_email('Ending Sentry Session',
                                         'Sentry has been manually shutdown: now terminating program.')
                terminate_program()
        else:
            print('System Exiting: Unable to establish connection with camera...')
            terminate_program()

        time_now = time.time()
        current_date = datetime.now()  # The current date for the frame

        if conf.warn_cap_storage < file_manager.cap_size:
            # Recalculate sentry storage before proceeding with warning
            file_manager.update_cap_size()
            if conf.warn_cap_storage < file_manager.cap_size:
                if not sent_daily_warning_email:
                    sent_daily_warning_email = True
                    print('RUNNING OUT OF STORAGE SENDING WARNING EMAIL')
                    print(f'{round(file_manager.cap_size, 4)}{conf.storage_units}/'
                          f'{conf.max_cap_storage}{conf.storage_units} used')
                    email_handler.send_email('Door Sentry Running Out of Disk Space',
                                             f'30% DISK SPACE REMAINING: {file_manager.cap_dir} is currently using '
                                             f'{round(file_manager.cap_size, 4)}{conf.storage_units} of'
                                             f' {conf.max_cap_storage}{conf.storage_units} available storage in '
                                             f'{file_manager.cap_dir}')

        # Handles camera saving capture/image
        if (time_now - file_manager.time_last_cap) > conf.fps_step:
            capture_image = True
        if capture_image:
            file_num = len(os.listdir(file_manager.today_dir))
            date_string = f'{current_date.month}m{current_date.day}d{current_date.year}y'
            time_string = f'{current_date.hour}h{current_date.minute}m{current_date.second}s'
            filename = f'id{file_num}_{time_string}-{date_string}-sentry_cameraNum{conf.camera_port}.jpeg'
            filepath = os.path.join(file_manager.today_dir, filename)
            cv2.imwrite(filepath, frame)
            file_manager.today_size += file_size(filepath)
            file_manager.cap_size += file_size(filepath)
            if file_num % conf.file_upload_notification_freq == 0:
                print(f'Saving {filename}, Daily Session Size = {round(file_manager.today_size, 4)}{conf.storage_units}, '
                      f'All Sessions Size = {round(file_manager.cap_size, 4)}{conf.storage_units}, '
                      f'TO END: press \'q\' on VideoStream')
            file_manager.time_last_cap = time_now
            capture_image = False

        # Checks to see if the day the frame was taken matches the day the session began
        if current_date.day - file_manager.current_date.day != 0:
            print(f'Day complete, saved {file_manager.today_size}{file_manager.storage_units} for day...')
            print(f'Calculating {file_manager.storage_units} saved to {file_manager.cap_dir} ...')
            # The following code recalibrates the sentryStorage size in case previous days' captures have been deleted
            file_manager.update_cap_size()
            print(f'{round(file_manager.cap_size, 4)}{file_manager.storage_units} saved for all days')

            try:
                file_manager.create_today_dir()
                print('Successfully created new directory...')
                print(f'Now saving images to {os.getcwd()}')
                # updates the day the sessions began
                start_day = current_date.day
                sent_daily_warning_email = False
            except OSError:
                print('System Exiting: Unable to create directory for next day')
                terminate_program()

    if file_manager.is_storage_full():
        email_handler.send_email('Out of Disk Space', f'Capture Storage has reached limit: now terminating program. '
                                                      f'Clear disk space in {file_manager.cap_dir}')
        print('System Exiting: Out of Disk Space...')
        terminate_program()

    terminate_program()


if __name__ == '__main__':
    main()
