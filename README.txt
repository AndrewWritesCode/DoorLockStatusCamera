Add your email to the environment.json file to receive daily warning emails when sentry storage is over 70% (You will also need to add an app password (NOT your email login!), this can be done in the security settings of your gmail account). The mode in json can be set to "sentry", "training", or "terminal". sendEmails can be set to "True" or "False". maxSentry units can be "MB" or "GB". the fps accpets a float value, the "notification_freq" accepts an int. The save notifications will play 1/x, where x is the notificatiuon_freq value. A value below zero will result in no save notifications

fps, cameraPort, max storage, frequency of image captures, and terminal motification frequency are all defined at the top of main.py


