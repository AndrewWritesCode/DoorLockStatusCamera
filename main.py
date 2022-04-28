
import cv2
import os
import json
import smtplib
from email.message import EmailMessage
import time
import datetime

import numpy as np

debug = False

with open(r'./environment.json', encoding="utf-8") as json_file:
    environment = json.load(json_file)
cameraPort = int(environment["cameraPort"])
to_email = environment["to_email"]
from_email = environment["from_email"]
from_email_pass = environment["from_email_pass"]
sendEmailsStr = environment["sendEmails"]
if sendEmailsStr.upper() == "true".upper(): #cannot cast from json to bool (Not sure why)
    sendEmails = True
else:
    sendEmails = False
useVideoStreamViewerStr = environment["useVideoStreamViewer"]
if useVideoStreamViewerStr.upper() == "true".upper(): #cannot cast from json to bool (Not sure why)
    useVideoStreamViewer = True
else:
    useVideoStreamViewer = False
startup = environment["mode"]
tempMaxSentryStorage = float(environment["maxSentryStorage"])
storageUnits = environment["storageUnits"].upper()
fps = float(environment["fps"])
useForceCaptureStr = environment["useForceCapture"]
if useForceCaptureStr.upper() == "true".upper(): #cannot cast from json to bool (Not sure why)
    useForceCapture = True
else:
    useForceCapture = False
forceCaptureIntervalSeconds = float(environment["force_capture_interval_seconds"])
fileUploadNotificationFreq = int(environment["notification_freq"])
useRelativeMotionSensStr = environment["useRelativeMotionSensitivity"]
motion_sensitivity = float(environment["motion_sensitivity"])
relative_motion_sensitivity = float(environment["relative_motion_sensitivity"])
if useRelativeMotionSensStr.upper() == "true".upper(): #cannot cast from json to bool (Not sure why)
    useRelativeMotionSens = True
else:
    useRelativeMotionSens = False
useMotionDetectionStr = environment["useMotionDetection"]
if useMotionDetectionStr.upper() == "true".upper(): #cannot cast from json to bool (Not sure why)
    useMotionDetection = True
else:
    useMotionDetection = False
    motion_detected = True

if fileUploadNotificationFreq < 1: #[int] Every 1/x file that is uploaded will be announce on terminal. 0 disables announcements
    fileUploadNotificationFreq = pow(10,100)

unitConv = 1
if storageUnits == "GB":
    unitConv = 1024
elif storageUnits == "MB":
    unitConv = 1
else:
    print("Error with storageUnits in environment.json, defaulting to MB")

maxSentryStorage = tempMaxSentryStorage * unitConv #(onces this is reached oldest images will be deleted)
warnSentryStorage = .7 * maxSentryStorage #[in MB] (once this limit is reached a daily email is sent)


if sendEmails:
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
    except:
        print("email credentials not accepted")
        print("Failed to send email with subject: " + msg['Subject'])


def CollectionMode2Name(coll): #Replace this with match statement when updating to Python 3.10
        if coll == "S":
            return "Sentry"
        elif coll == "T":
            return  "Training"
        elif coll == "L":
            return "Locked"
        else:
            return "Unlocked"

#Calculates the disk space taken from a given FPS value and file size
def DailySpaceConsumption(singleFileSizeEstimate, fps):
    dailySpaceCons = singleFileSizeEstimate*86400*fps
    return dailySpaceCons

#Calculates the max FPS from disk space and file size
def FPSfromDailySpaceAllowance(singleFileSizeEstimate, DailySpaceAllow):
    fpsEstimate = DailySpaceAllow/(singleFileSizeEstimate*86400)
    return fpsEstimate

#get the start time in ms (webcams do not support cv2 FPS API)
def FPS_step(fps):
    fps_step = 1/fps #number of ms between frames
    return fps_step

#Detects if there is motion between two frames
def MotionDetect(prev_frame, next_frame, sensitivity, prevScoreArrayCols, prevScoreArrayRows):
    motionDetected = False
    diff = cv2.absdiff(next_frame, prev_frame)
    g = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    scoreArrayCols = np.mean(g, axis=0)
    for ColScore in range(0,scoreArrayCols.size):
        #This scans each column, and detects motion if the avg gray value is greater than sensitivity (set in json)
        if useRelativeMotionSens:
            scoreDiff = abs(scoreArrayCols[ColScore] - prevScoreArrayCols[ColScore])
            if scoreDiff > abs((relative_motion_sensitivity)*prevScoreArrayCols[ColScore]):
                pass
        else:
            if abs(scoreArrayCols[ColScore] - prevScoreArrayCols[ColScore]) > sensitivity:
                motionDetected = True
        prevScoreArrayCols[ColScore] = scoreArrayCols[ColScore]
    if motion_detected == False:
        scoreArrayRows = np.mean(g, axis=1)
        for RowScore in range(0, scoreArrayRows.size):
            # This scans each row, and detects motion if the avg gray value is greater than sensitivity (set in json)
            if useRelativeMotionSens:
                scoreDiff = abs(scoreArrayRows[RowScore] - prevScoreArrayRows[RowScore])
                if scoreDiff > abs((relative_motion_sensitivity)*prevScoreArrayRows[RowScore]):
                    pass
            else:
                if abs(scoreArrayRows[RowScore] - prevScoreArrayRows[RowScore]) > sensitivity:
                    motionDetected = True
            prevScoreArrayRows[RowScore] = scoreArrayRows[RowScore]
    return prevScoreArrayCols, prevScoreArrayRows, motionDetected

#Sets/Creates the directory
def DirectorySetup():
    cameraMode = ""
    currentDate = datetime.datetime.now()
    dateString = str(currentDate.month) + 'm' + str(currentDate.day) + 'd' + str(currentDate.year) + 'y'
    collection_type = ""
    collection_dir = ''
    sentryStorage = 0.0
    if startup == "sentry":
        collection_type = "S"
        collection_dir = 'doorSentry'
    elif startup == "training":
        while collection_type != "L" or "U":
            collection_type = input("TRAINING TYPE: LOCKED OR UNLOCKED? [L/U]: ")
            collection_type = collection_type.upper()
            if collection_type == "L":
                collection_dir = 'locked_uncleaned'
                print("Initializing Locked State Image Collection...")
                break
            elif collection_type == "U":
                collection_dir = 'unlocked_uncleaned'
                print("Initializing Unlocked Image Data Collection...")
                break
    else:
        while cameraMode != "T" or "S":
            mode = input("TRAINING OR SENTRY [T/S]: ")
            mode = mode.upper()
            if mode == "S":
                collection_type = "S"
                collection_dir = 'doorSentry'
                break
            elif mode == "T" :
                while collection_type != "L" or "U":
                    collection_type = input("TRAINING TYPE: LOCKED OR UNLOCKED? [L/U]: ")
                    collection_type = collection_type.upper()
                    if collection_type == "L":
                        collection_dir = 'locked_uncleaned'
                        print("Initializing Locked State Image Collection...")
                        break
                    elif collection_type == "U":
                        collection_dir = 'unlocked_uncleaned'
                        print("Initializing Unlocked Image Data Collection...")
                        break
            if collection_type == "L" or "U" or "S":
                break

    try:
        os.mkdir('data')
    except:
        print("Using existing data directory...")
    os.chdir('data')

    try:
        os.mkdir('archived_images')
    except:
        print("Using exisiting archived_images directory...")

    try:
        os.mkdir(collection_dir)
    except:
        print("Using existing " + collection_dir + " directory...")
    os.chdir(collection_dir)

    try:
        folderNum = len(os.listdir(os.getcwd())) + 1
        if collection_type == "S":
            for path, dirs, files in os.walk(os.getcwd()):
                for file in files:
                    filepath = os.path.join(path, file)
                    sentryStorage = sentryStorage + os.path.getsize(filepath)
                  #This calculcates the disk space given in bytes of the images already stored sentry storage
        os.mkdir(dateString)

    except:
        folderNum = len(os.listdir(os.getcwd())) + 1
        print("Using existing dateString directory...")
    os.chdir(dateString)

    return collection_type, folderNum, sentryStorage


######################################


collection_type, folderNum, sentryStorage = DirectorySetup()
if collection_type == "S":
    print(str(round(sentryStorage / pow(1024,2),4)) + "MB of images are already saved to Sentry Storage...")
print("Saving images to " + str(os.getcwd()))
#The number of bytes that have been saved in the current session
daily_session_size = 0

for file in os.listdir(os.getcwd()):
    daily_session_size = daily_session_size + os.path.getsize(file)
    #This sums the file sizes in the current day's directory
print("Daily directory size initializing at " + str(round(daily_session_size / pow(1024, 2), 4)) + "MB")
time_lastCapture = time.time()
#initializes the time for fps calcs
fps_step = FPS_step(fps)

try:
    cap = cv2.VideoCapture(cameraPort, cv2.CAP_DSHOW) #takes the first avaialble camera on computer
except:
    print("ERROR: Unable to establish video link")

#checks if the camerafeed is opened
print("Accessing Camera...")
startDay = datetime.datetime.now().day #The day that recording starts
sentDailyWarningEmail = False
#prev_ms = 0

firstPass = True
safeShutdown = False
while (cap.isOpened()):
    #captures a frame each loop
    ret, frame = cap.read()
    if firstPass:
        prev_ms_cols = np.zeros(frame.shape[1])
        prev_ms_rows = np.zeros(frame.shape[0])
        prev_frame = frame
        motion_detected_since_last_capture = True
        firstPass = False
        print("Camera Accessed...")
    if ret == True:
        #displays the current frame (if enabled in environment.json)
        if useVideoStreamViewer == True:
            cv2.imshow('VideoStream', frame)
        #Press 'q' on keyboard to break loop and end program
        if cv2.waitKey(25) & 0xFF == ord('q'):
            safeShutdown = True
            print("ENDING SESSION:")
            print(str(sentryStorage / pow(1024,3)) + "GB of " + str(maxSentryStorage / 1024) + "GB allotted storage used")
            if sendEmails:
                msg = EmailMessage()
                msg['Subject'] = 'Ending Sentry Session'
                msg['From'] = from_email
                msg['To'] = to_email
                msg.set_content('Sentry has been manually shutdown: now terminating program.')
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(from_email, from_email_pass)

                        smtp.send_message(msg)
                except:
                    print("Failed to send email with subject: " + msg['Subject'])
            break
    else:
        break
    #Handles the motion sensing
    if useMotionDetection:
        motion_detected = False
        try:
            motion_scores_cols, motion_scores_rows,  motion_detected = MotionDetect(prev_frame, frame, motion_sensitivity, prev_ms_cols, prev_ms_rows)
            prev_ms_cols = motion_scores_cols
            prev_ms_rows = motion_scores_rows
        except:
            print("Initializing Motion Sensing...")
    prev_frame = frame
    #Handles file-naming/saving and fps
    time_now = time.time()
    currentDate = datetime.datetime.now() #The current date for the frame
    if warnSentryStorage < (sentryStorage / pow(1024, 2)):
        if not sentDailyWarningEmail:
            sentDailyWarningEmail = True
            print("RUNNING OUT OF STORAGE SENDING WARNING EMAIL")
            print(str(sentryStorage / pow(1024,3)) + 'GB/' + str(maxSentryStorage / 1024) + 'GB used')
            if sendEmails:
                msg = EmailMessage()
                msg['Subject'] = 'Door Sentry Running Out of Disk Space'
                msg['From'] = from_email
                msg['To'] = to_email
                msg.set_content('Daily Email: DoorSentry is currently using ' + str(sentryStorage / pow(1024,3)) + \
                                'GB of ' + str(maxSentryStorage / 1024) + 'GB available storage')

                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(from_email, from_email_pass)

                        smtp.send_message(msg)
                except:
                    print("Failed to send email with subject: " + msg['Subject'])

    if ((time_now - time_lastCapture) > forceCaptureIntervalSeconds) and (useForceCapture == True):
        forceCapture = True
        #print("Forcing Image Capture...") #FOR DEBUG
    else:
        forceCapture = False

    if (time_now - time_lastCapture) > fps_step:
        if motion_detected or (forceCapture == True) or motion_detected_since_last_capture:
            fileNum = len(os.listdir(os.getcwd()))
            dateString = str(currentDate.month) + 'm' + str(currentDate.day) + 'd' + str(currentDate.year) + 'y'
            timeString = str(currentDate.hour) + "h" + str(currentDate.minute) + "m" + str(currentDate.second) + "s"
            filename = 'id' + str(fileNum) + '_' + timeString + '-' + dateString + '-' + \
                       CollectionMode2Name(collection_type) + '_' +'cameraNum' + str(cameraPort) + '.jpeg'
            cv2.imwrite(filename, frame)
            daily_session_size = daily_session_size + os.path.getsize(filename)
            sentryStorage = sentryStorage + os.path.getsize(filename)
            if fileNum % fileUploadNotificationFreq == 0:
                print('Saving ' + str(filename) + ', Daily Session Size = ' + str(daily_session_size / pow(1024,2)) + \
                      'MB, All Sessions Size = ' + str(sentryStorage / pow(1024,2)) + 'MB, TO END: press \'q\' on VideoStream')
            time_lastCapture = time_now
            motion_detected_since_last_capture = False
    elif motion_detected:
        motion_detected_since_last_capture = True
        print("motion between captures...") #DEBUG
    #Checks to see if the day the frame was taken matches the day the session began
    if currentDate.day - startDay != 0:
        print("Day complete, saved " + str(daily_session_size) + "MB for day, moving to new directory...")
        os.chdir('..')

        try:
            dateString = str(currentDate.month) + 'm' + str(currentDate.day) + 'd' + str(currentDate.year) + 'y'
            os.mkdir(dateString)
            folderNum = folderNum + 1
            print("Successfully created new directory...")
            os.chdir(dateString)
            print("Now saving images to " + str(os.getcwd()))
            startDay = currentDate.day #updates the day the sessions began
            daily_session_size = 0.0
            sentDailyWarningEmail = False
        except:
            print("ERROR: Unable to create directory for next day")



    if maxSentryStorage < (sentryStorage / pow(1024,2)):
        print("Sentry Storage has reached limit: now terminating program...")
        os.chdir('..')
        print("Clear disk space in " + os.getcwd())
        if sendEmails:
            msg = EmailMessage()
            msg['Subject'] = 'Door Sentry Out of Disk Space'
            msg['From'] = from_email
            msg['To'] = to_email
            msg.set_content('Sentry Storage has reached limit: now terminating program. Clear disk space in ' + os.getcwd())
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(from_email, from_email_pass)

                    smtp.send_message(msg)
            except:
                print("Failed to send email with subject: " + msg['Subject'])
        break

if firstPass:
    print("Unable to establish connection with camera...")
    print("Terminating program...")

if (not safeShutdown) and (not firstPass) and useVideoStreamViewer:
    print("Unsafe shutdwon...")
    if sendEmails:
        msg = EmailMessage()
        msg['Subject'] = 'Door Sentry Unexpected Shutdown'
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content('Sentry has unexpected shutdown, check that camera is operating properly')
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(from_email, from_email_pass)

                smtp.send_message(msg)
        except:
            print("Failed to send email with subject: " + msg['Subject'])
#cv2 cleanup
cap.release()
cv2.destroyAllWindows()