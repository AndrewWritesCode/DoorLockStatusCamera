import sys

import cv2
import os
import json
import smtplib
from email.message import EmailMessage
import time
import datetime
import numpy as np

debug = False

# Start of environment loading
with open(r'./environment.json', encoding="utf-8") as json_file:
    environment = json.load(json_file)
root_directory = environment["root_directory"]
if (root_directory == '') or (not os.path.exists(root_directory)):
    root_directory = os.getcwd()
data_directory = environment["data_directory"]
camera_directory = environment["camera_directory"]
camera_port = int(environment["camera_port"])
to_email = environment["to_email"]
from_email = environment["from_email"]
from_email_pass = environment["from_email_pass"]
send_emails = environment["send_emails"]
use_live_video_viewer = environment["use_live_video_viewer"]
startup = environment["mode"]
temp_max_sentry_storage = float(environment["max_sentry_storage"])
storage_units = environment["storage_units"].upper()
fps = float(environment["fps"])
use_force_capture = environment["use_force_capture"]
force_capture_interval_seconds = float(environment["force_capture_interval_seconds"])
file_upload_notification_freq = int(environment["notification_freq"])
if file_upload_notification_freq < 1:
    # [int] Every 1/x file that is uploaded will be announce on terminal. 0 disables announcements
    file_upload_notification_freq = pow(10, 100)
motion_sensitivity = float(environment["motion_sensitivity"])
motion_sensing_persistence = float(environment["motion_sensing_persistence"])
use_motion_detection = environment["use_motion_detection"]
if not use_motion_detection:
    motion_detected = True

unitConv = 1
if storage_units == "GB":
    unitConv = 1024
elif storage_units == "MB":
    unitConv = 1
else:
    print("Error with storageUnits in environment.json, defaulting to MB")

max_sentry_storage = temp_max_sentry_storage * unitConv  # (once this is reached oldest images will be deleted)
warn_sentry_storage = .7 * max_sentry_storage  # [in MB] (once this limit is reached a daily email is sent)

# End of environment loading


# Calculates the disk space taken from a given FPS value and file size
def daily_space_consumption(single_file_size_estimate, fps):
    daily_space_cons = single_file_size_estimate * 86400 * fps
    return daily_space_cons


# Calculates the max FPS from disk space and file size
def fps_from_daily_space_allowance(single_file_size_estimate, daily_space_allow):
    fps_estimate = daily_space_allow / (single_file_size_estimate * 86400)
    return fps_estimate


# get the start time in ms (webcams do not support cv2 FPS API)
def FPS_step(fps):
    fps_step = 1 / fps  # number of ms between frames
    return fps_step


# Detects if there is motion between two frames
def motion_detect(prev_frame, next_frame, sensitivity):
    motion_detected = False
    diff = cv2.absdiff(next_frame, prev_frame)
    g = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    score_array_cols = np.mean(g, axis=0)
    for ColScore in range(0, score_array_cols.size):
        # This scans each column, and detects motion if the avg gray value is greater than sensitivity (set in json)
        if abs(score_array_cols[ColScore]) > sensitivity:
            motion_detected = True
            break
        # prevScoreArrayCols[ColScore] = score_array_cols[ColScore]
    if motion_detected == False:
        score_array_rows = np.mean(g, axis=1)
        for RowScore in range(0, score_array_rows.size):
            # This scans each row, and detects motion if the avg gray value is greater than sensitivity (set in json)
            if abs(score_array_rows[RowScore]) > sensitivity:
                motion_detected = True
                break
    return motion_detected


# Sets/Creates the directory
def directory_setup():
    try:
        os.chdir(root_directory)
    except OSError:
        print(f'Could not change to root directory: {root_directory}')
        print('Terminating program...')
        sys.exit()
    current_date = datetime.datetime.now()
    date_string = f'{current_date.month}m{current_date.day}d{current_date.year}y'
    sentry_storage = 0.0

    if not os.path.exists(data_directory):
        try:
            os.mkdir(data_directory)
        except OSError:
            print(f'Could not create {data_directory} as data_directory...')
            print('Terminating program...')
            sys.exit()
    else:
        print('Using existing data directory...')

    if not os.path.exists(os.path.join(data_directory, camera_directory)):
        try:
            os.mkdir(os.path.join(data_directory, camera_directory))
        except OSError:
            print(f'Could not create {camera_directory} as camera_directory...')
            print('Terminating program...')
            sys.exit()
    else:
        print('existing camera_directory...')
    sentry_storage_root = os.path.join(data_directory, camera_directory)

    folder_num = len(os.listdir(sentry_storage_root)) + 1
    for path, dirs, files in os.walk(sentry_storage_root):
        for file in files:
            filepath = os.path.join(path, file)
            sentry_storage = sentry_storage + os.path.getsize(filepath)
            # This calculates the disk space given in bytes of the images already stored sentry storage

    if not os.path.exists(os.path.join(sentry_storage_root, date_string)):
        try:
            os.mkdir(os.path.join(sentry_storage_root, date_string))
        except OSError:
            print('Could not create date_directory...')
            print('Terminating program...')
            sys.exit()
    else:
        print("Using existing date_string directory...")
        folder_num = len(os.listdir(sentry_storage_root)) + 1
    current_storage_directory = os.path.abspath(os.path.join(sentry_storage_root, date_string))
    os.chdir(current_storage_directory)  # BE SURE TO LOOK OVER CODE THAT RELIED ON THIS

    return folder_num, sentry_storage, sentry_storage_root, current_storage_directory


def sentry_storage_calibration(sentry_storage_root):
    sentry_storage = 0
    for path, dirs, files in os.walk(sentry_storage_root):
        for file in files:
            filepath = os.path.join(path, file)
            sentry_storage = sentry_storage + os.path.getsize(filepath)
    return sentry_storage


######################################

if send_emails:
    print("Sending initialization email...")
    msg = EmailMessage()
    msg['Subject'] = 'Door Sentry Activated'
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content('Door Sentry is initializing')
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(from_email, from_email_pass)
            smtp.send_message(msg)
    except Warning:
        print("email credentials not accepted")
        print("Failed to send email with subject: " + msg['Subject'])

folder_num, sentry_storage, sentry_storage_root, current_storage_directory = directory_setup()

print(f'{round(sentry_storage / pow(1024, 2), 4)}MB of images are already saved to Sentry Storage...')
print(f'Saving images to {current_storage_directory}')
# The number of bytes that have been saved in the current session
daily_session_size = 0

for file in os.listdir(os.getcwd()):
    daily_session_size = daily_session_size + os.path.getsize(file)
    # This sums the file sizes in the current day's directory
print(f'Daily directory size initializing at {round(daily_session_size / pow(1024, 2), 4)}MB')
time_last_capture = time.time()
# initializes the time for fps calculations
fps_step = FPS_step(fps)

try:
    cap = cv2.VideoCapture(camera_port, cv2.CAP_DSHOW)  # takes the first available camera on computer
except ConnectionRefusedError:
    print('ERROR: Unable to establish video link')
    print('Terminating program...')
    sys.exit()

# checks if the camera feed is opened
print('Accessing Camera...')
start_day = datetime.datetime.now().day  # The day that recording starts
sent_daily_warning_email = False
# prev_ms = 0

first_pass = True
safe_shutdown = False
while (cap.isOpened()):
    # captures a frame each loop
    ret, frame = cap.read()
    if first_pass:
        prev_ms_cols = np.zeros(frame.shape[1])
        prev_ms_rows = np.zeros(frame.shape[0])
        prev_frame = frame
        motion_detected_since_last_capture = True
        time_since_motion = time.time()
        first_pass = False
        print('Camera Accessed...')
    if ret == True:
        # displays the current frame (if enabled in environment.json)
        if use_live_video_viewer == True:
            cv2.imshow('VideoStream', frame)
        # Press 'q' on keyboard to break loop and end program
        if cv2.waitKey(25) & 0xFF == ord('q'):
            safe_shutdown = True
            print('ENDING SESSION:')
            print(f'{str(sentry_storage / pow(1024, 3))}GB of {str(max_sentry_storage / 1024)}GB allotted storage used')
            if send_emails:
                msg = EmailMessage()
                msg['Subject'] = 'Ending Sentry Session'
                msg['From'] = from_email
                msg['To'] = to_email
                msg.set_content('Sentry has been manually shutdown: now terminating program.')
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(from_email, from_email_pass)

                        smtp.send_message(msg)
                except Warning:
                    print("Failed to send email with subject: " + msg['Subject'])
            break
    else:
        break
    # Handles the motion sensing
    if use_motion_detection:
        try:
            motion_detected = motion_detect(prev_frame, frame, motion_sensitivity)
        except:
            print("Initializing Motion Sensing...")

    prev_frame = frame
    # Handles file-naming/saving and fps
    time_now = time.time()
    current_date = datetime.datetime.now()  # The current date for the frame

    if ((time_now - time_last_capture) > force_capture_interval_seconds) and (use_force_capture == True):
        force_capture = True
        # print("Forcing Image Capture...") #FOR DEBUG
    else:
        force_capture = False

    # Handles motion sensing persistence (how long captures last in seconds since last capture)
    if motion_detected:
        time_since_motion = time.time()
        force_capture = True
    if (time_now - time_since_motion) < motion_sensing_persistence:
        force_capture = True
        # print("Persistent Capture") #FOR DEBUG

    if warn_sentry_storage < (sentry_storage / pow(1024, 2)):
        # Recalculate sentry storage before proceeding with warning
        sentry_storage = sentry_storage_calibration(sentry_storage_root)
        if warn_sentry_storage < (sentry_storage / pow(1024, 2)):
            if not sent_daily_warning_email:
                sent_daily_warning_email = True
                print('RUNNING OUT OF STORAGE SENDING WARNING EMAIL')
                print(f'{sentry_storage / pow(1024, 3)}GB/{max_sentry_storage / 1024}GB used')
                if send_emails:
                    msg = EmailMessage()
                    msg['Subject'] = 'Door Sentry Running Out of Disk Space'
                    msg['From'] = from_email
                    msg['To'] = to_email
                    msg.set_content(f'30% DISK SPACE REMAINING: {camera_directory} is currently using '
                                    f'{sentry_storage / pow(1024, 3)}GB of {max_sentry_storage / 1024}GB '
                                    f'available storage in {sentry_storage_root}')

                    try:
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                            smtp.login(from_email, from_email_pass)
                            smtp.send_message(msg)
                    except Warning:
                        print("Failed to send email with subject: " + msg['Subject'])

    if motion_detected_since_last_capture:
        force_capture = True
    # Handles forcing the camera to save a capture/image
    if force_capture:
        if (time_now - time_last_capture) > fps_step:
            file_num = len(os.listdir(os.getcwd()))
            date_string = f'{current_date.month}m{current_date.day}d{current_date.year}y'
            time_string = f'{current_date.hour}h{current_date.minute}m{current_date.second}s'
            filename = f'id{file_num}_{time_string}-{date_string}-sentry_cameraNum{camera_port}.jpeg'
            cv2.imwrite(filename, frame)
            daily_session_size = daily_session_size + os.path.getsize(filename)
            sentry_storage = sentry_storage + os.path.getsize(filename)
            if file_num % file_upload_notification_freq == 0:
                print(f'Saving {filename}, Daily Session Size = {daily_session_size / pow(1024, 2)}MB, '
                      f'All Sessions Size = {sentry_storage / pow(1024, 2)}MB, TO END: press \'q\' on VideoStream')
            time_last_capture = time_now
            motion_detected = False
            motion_detected_since_last_capture = False
    elif motion_detected:
        motion_detected_since_last_capture = True
        # print("motion between captures...") #DEBUG
    # Checks to see if the day the frame was taken matches the day the session began
    if current_date.day - start_day != 0:
        print(f'Day complete, saved {daily_session_size}MB for day, moving to new directory...')
        os.chdir('..')
        print(f'Calculating GB saved to {camera_directory} folder...')
        # The following code recalibrates the sentryStorage size in case previous days' captures have been deleted
        sentry_storage = sentry_storage_calibration(sentry_storage_root)
        print(f'{sentry_storage / pow(1024, 3)}GB saved for all days')

        try:
            date_string = f'{current_date.month}m{current_date.day}d{current_date.year}y'
            os.mkdir(date_string)
            folder_num = folder_num + 1
            print('Successfully created new directory...')
            os.chdir(date_string)
            print(f'Now saving images to {os.getcwd()}')
            # updates the day the sessions began
            start_day = current_date.day
            daily_session_size = 0.0
            sent_daily_warning_email = False
        except OSError:
            print('ERROR: Unable to create directory for next day')

    if max_sentry_storage < (sentry_storage / pow(1024, 2)):
        # First recalibrate sentryStorage
        sentry_storage = sentry_storage_calibration(sentry_storage_root)
        # Now check again if past max storage
        if max_sentry_storage < (sentry_storage / pow(1024, 2)):
            print('Sentry Storage has reached limit: now terminating program...')
            os.chdir('..')
            print("Clear disk space in " + os.getcwd())
            if send_emails:
                msg = EmailMessage()
                msg['Subject'] = 'Door Sentry Out of Disk Space'
                msg['From'] = from_email
                msg['To'] = to_email
                msg.set_content(f'Sentry Storage has reached limit: now terminating program. Clear disk space in'
                                f' {sentry_storage_root}')
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(from_email, from_email_pass)

                        smtp.send_message(msg)
                except Warning:
                    print("Failed to send email with subject: " + msg['Subject'])
            break

if first_pass:
    print('Unable to establish connection with camera...')
    print('Terminating program...')

if (not safe_shutdown) and (not first_pass) and use_live_video_viewer:
    print("Unsafe shutdown...")
    if send_emails:
        msg = EmailMessage()
        msg['Subject'] = 'Door Sentry Unexpected Shutdown'
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content('Sentry has unexpected shutdown, check that camera is operating properly')
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(from_email, from_email_pass)
                smtp.send_message(msg)
        except Warning:
            print("Failed to send email with subject: " + msg['Subject'])

# cv2 cleanup
cap.release()
cv2.destroyAllWindows()
