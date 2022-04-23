
import cv2
import os
import json
import smtplib
from email.message import EmailMessage
import time
import datetime

debug = False


cameraPort = 0
cameraMode = ""

with open(r'./environment.json', encoding="utf-8") as json_file:
    environment = json.load(json_file)
to_email = environment["to_email"]
from_email = environment["from_email"]
from_email_pass = environment["from_email_pass"]
sendEmails = environment["sendEmails"]
startup = environment["mode"]
tempMaxSentryStorage = float(environment["maxSentryStorage"])
storageUnits = environment["storageUnits"].upper()
fps = float(environment["fps"])
fileUploadNotificationFreq = int(environment["notification_freq"])

if fileUploadNotificationFreq < 1: #[int] Every 1/x file that is uploaded will be announce on terminal. 0 diables announcements
    fileUploadNotificationFreq = pow(10,10)

unitConv = 1
if storageUnits == "GB":
    unitConv = pow(10,3)
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

#Sets/Creates the directory
def DirectorySetup(cameraMode):
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


collection_type, folderNum, sentryStorage = DirectorySetup(cameraMode)
if collection_type == "S":
    print(str(sentryStorage / pow(10,6)) + "MB of images are already saved to Sentry Storage...")
print("Saving images to " + str(os.getcwd()))
#The number of bytes that have been saved in the current session
daily_session_size = 0

for file in os.listdir(os.getcwd()):
    daily_session_size = daily_session_size + os.path.getsize(file)
    #This sums the file sizes in the current day's directory
print("Session size intializing at " + str(daily_session_size / pow(10, 6)) + "MB")
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
while (cap.isOpened()):
    #captures a frame each loop
    ret, frame = cap.read()
    if ret == True:
        #displays the current frame
        cv2.imshow('VideoStream', frame)
        #Press 'q' on keyboard to break loop and end program
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    else:
        break

    #Handles file-naming/saving and fps
    time_now = time.time()
    currentDate = datetime.datetime.now() #The current date for the frame
    if warnSentryStorage < (sentryStorage / pow(10, 6)):
        if not sentDailyWarningEmail:
            sentDailyWarningEmail = True
            print("RUNNING OUT OF STORAGE SENDING WARNING EMAIL")
            print(str(sentryStorage / pow(10,9)) + 'GB/' + str(maxSentryStorage / pow(10,3)) + 'GB used')
            if sendEmails:
                msg = EmailMessage()
                msg['Subject'] = 'Door Sentry Running Out of Disk Space'
                msg['From'] = from_email
                msg['To'] = to_email
                msg.set_content('Daily Email: DoorSentry is currently using ' + str(sentryStorage / pow(10,9)) + \
                                'GB of ' + str(maxSentryStorage / pow(10,3)) + 'GB available storage')

                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(from_email, from_email_pass)

                        smtp.send_message(msg)
                except:
                    pass

    if (time_now - time_lastCapture) > fps_step:
        fileNum = len(os.listdir(os.getcwd()))
        dateString = str(currentDate.month) + 'm' + str(currentDate.day) + 'd' + str(currentDate.year) + 'y'
        timeString = str(currentDate.hour) + "h" + str(currentDate.minute) + "m" + str(currentDate.second) + "s"
        filename = collection_type + '_ses' + str(folderNum) + '_num_' + str(fileNum) + '-' + str(fps) + 'FPS_' + \
                   dateString + '-' + timeString +  '.jpeg'
        cv2.imwrite(filename, frame)
        daily_session_size = daily_session_size + os.path.getsize(filename)
        sentryStorage = sentryStorage + os.path.getsize(filename)
        if fileNum % fileUploadNotificationFreq == 0:
            print('Saving ' + str(filename) + ', Daily Session Size = ' + str(daily_session_size / pow(10, 6)) + \
                  'MB, All Sessions Size = ' + str(sentryStorage / pow(10,6)) + 'MB, TO END: press \'q\' on VideoStream')
        time_lastCapture = time_now
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



    if maxSentryStorage < (sentryStorage / pow(10,6)):
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
                pass
        break
#cv2 cleanup
cap.release()
cv2.destroyAllWindows()