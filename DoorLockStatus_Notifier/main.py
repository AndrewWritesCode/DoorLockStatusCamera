import logging
import cv2
import os

debug = False

def CollectionDebug(collection_type):
    logging.debug("Collection Type set to " + collection_type)

#Set/Create the directory
collection_type = ""
collection_dir = ''
while collection_type != "L" or "U":
    collection_type = input("TRAINING TYPE: LOCKED OR UNLOCKED? [L/U]: ")
    if collection_type == "L":
        collection_dir = 'locked_uncleaned'
        if debug:
            CollectionDebug(collection_type)
        break
    elif collection_type == "U":
        collection_dir = 'unlocked_uncleaned'
        if debug:
            CollectionDebug(collection_type)
        break
    else:
        collection_dir = 'undefined_uncleaned'
        if debug:
            CollectionDebug(collection_type)

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
    os.mkdir('Session_' + str(folderNum))
except:
    logging.WARN('Unable to create session directory')
os.chdir('Session_' + str(folderNum))

######################################

try:
    cap = cv2.VideoCapture(0)
except:
    logging.ERROR('Unable to establish video link')

while (cap.isOpened()):
    ret, frame = cap.read()
    if ret == True:
        cv2.imshow('VideoStream', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    else:
        break
    #fourcc = cv2.VideoWriter_fourcc(*'XVID')

    fileNum = len(os.listdir(os.getcwd()))
    filename = collection_type + str(fileNum) + '.png'
    cv2.imwrite(filename, frame)

cap.release()
cv2.destroyAllWindows()

