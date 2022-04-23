import logging
import cv2
import os
import time
import datetime

debug = False

#Calculates the disk space taken from a given FPS value and file size
def DailySpaceConsumption(singleFileSizeEstimate, fps):
    dailySpaceCons = singleFileSizeEstimate*86400*fps
    return dailySpaceCons

#Calculates the max FPS from disk space and file size
def FPSfromDailySpaceAllowance(singleFileSizeEstimate, DailySpaceAllow):
    fpsEstimate = DailySpaceAllow/(singleFileSizeEstimate*86400)
    return fpsEstimate

def CollectionDebug(collection_type):
    logging.debug("Collection Type set to " + collection_type)

#get the start time in ms (webcams do not support cv2 FPS API)
def FPS_step(fps):
    fps_step = 1/fps #number of ms between frames
    return fps_step

#Sets/Creates the directory
def DirectorySetup():
    currentDate = datetime.datetime.now()
    dateString = str(currentDate.month) + 'm' + str(currentDate.day) + 'd' + str(currentDate.year) + 'y'
    cameraMode = ""
    collection_type = ""
    collection_dir = ''
    while cameraMode != "T" or "S":
        mode = input("TRAINING OR SENTRY [T/S]: ")
        mode = mode.upper()
        if mode == "S":
            collection_type = "S"
            collection_dir = 'doorSentry'
            break
        elif mode == "T" :
            while collection_type != "L" or "U" or "S":
                collection_type = input("TRAINING TYPE: LOCKED OR UNLOCKED? [L/U]: ")
                collection_type = collection_type.upper()
                if collection_type == "L":
                    collection_dir = 'locked_uncleaned'
                    print("Initializing Locked State Image Collection...")
                    if debug:
                        CollectionDebug(collection_type)
                    break
                elif collection_type == "U":
                    collection_dir = 'unlocked_uncleaned'
                    print("Initializing Unlocked Image Data Collection...")
                    if debug:
                        CollectionDebug(collection_type)
                    break
                break

    try:
        os.mkdir('data')
    except:
        logging.debug('Using existing data directory')
    os.chdir('data')

    try:
        os.mkdir(collection_dir)
    except:
        logging.debug('Using existing ' + collection_dir + ' directory')
    os.chdir(collection_dir)

    try:
        folderNum = len(os.listdir(os.getcwd())) + 1
        os.mkdir(dateString)
    except:
        folderNum = len(os.listdir(os.getcwd())) + 1
        logging.debug('Using existing dateString directory')
    os.chdir(dateString)

    return collection_type, folderNum


######################################


collection_type, folderNum = DirectorySetup()
print("Saving images to " + str(os.getcwd()))
#The number of bytes that have been saved in the current session
session_size = 0
for file in os.listdir(os.getcwd()):
    session_size = session_size + os.path.getsize(file)
    #This sums the file sizes in the current day's directory
print("Session size intializing at " + str(session_size / pow(10,6)) + "MB")
time_lastCapture = time.time()
#initializes the time for fps calcs
fps = 1.5 #Accepts a float
fps_step = FPS_step(fps)
cameraPort = 0
try:
    cap = cv2.VideoCapture(cameraPort, cv2.CAP_DSHOW) #takes the first avaialble camera on computer
except:
    logging.ERROR('Unable to establish video link')

#checks if the camerafeed is opened
print("Accessing Camera...")
startDay = datetime.datetime.now().day #The day that recording starts
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
    if (time_now - time_lastCapture) > fps_step:
        fileNum = len(os.listdir(os.getcwd()))
        dateString = str(currentDate.month) + 'm' + str(currentDate.day) + 'd' + str(currentDate.year) + 'y'
        timeString = str(currentDate.hour) + "h" + str(currentDate.minute) + "m" + str(currentDate.second) + "s"
        filename = collection_type + '_ses' + str(folderNum) + '_num_' + str(fileNum) + '-' + str(fps) + 'FPS_' + \
                   dateString + '-' + timeString +  '.jpeg'
        cv2.imwrite(filename, frame)
        session_size = session_size + os.path.getsize(filename)
        print('Saving ' + str(filename) + ', Total Session Size = ' + str(session_size/pow(10,6)) + 'MB')
        time_lastCapture = time_now
    #Checks to see if the day the frame was taken matches the day the session began
    if currentDate.day - startDay != 0:
        print("Day complete, saved " + str(session_size) + "MB for day, moving to new directory...")
        os.chdir('..')
        try:
            dateString = str(currentDate.month) + 'm' + str(currentDate.day) + 'd' + str(currentDate.year) + 'y'
            os.mkdir(dateString)
            folderNum = folderNum + 1
            print("Successfully created new directory...")
            os.chdir(dateString)
            print("Now saving images to " + str(os.getcwd()))
            startDay = currentDate.day #updates the day the sessions began
        except:
            logging.WARN("Unable to create directory for next day")

#cv2 cleanup
cap.release()
cv2.destroyAllWindows()
