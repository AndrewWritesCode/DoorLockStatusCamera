Add your email to the environment.json file to receive daily warning emails when sentry storage is over 70% (You will also need to add an app password (NOT your email login!), this can be done in the security settings of your gmail account).

To exit the application, click on the video window, and press 'q'


BREAKDOWN OF .json FILE:
{
	"cameraPort": "0", # if you are using 1 camera, this will be set to 0. If you have several cameras, set this to a different number (try 1, 2, etc) until the correct camera is being used (currently only support for 1 camera, you can run the script twice in different directories for 2+)
	"mode": "sentry", # can be set to "sentry", "training", or "terminal". Sentry acts like a security camera, training allows for "locked" or "unlocked" to be in file name (to save time labelling training data). terminal mode allows you to set mode in temrinal
	"useVideoStreamViewer": "true", # disables the VideoStream window. This also means there is no windows to press 'q' on to safely close the program. Only recommended changing to 'false' for use case where program is not stopped until reboot
	"sendEmails": "false", # [false/true] Determines whether emails should be sent using credentials at start of .json
	"from_email": "your FROM (bot) email goes here",
	"from_email_pass": "your FROM (bot) email password goes here (the app password, not login, see README)", # For gmail go to your google acct seeting, then Security, and App passwords (select app [Custom], select device [Tested on Windows, should work on Mac])
	"to_email": "your TO email goes here",
	"maxSentryStorage": "10", # The max amount of disk space allocaed for sentry images (excluding the training folders)
	"storageUnits": "GB", # the untis of disk space allocated. Can be in MB or GB
	"fps": "60", # The Frame/second that captures are taken in sentry mode (This value does not affect motion_sensing) You can use a float or int here (e.g 1.5 or 1)
	"useForceCapture": "true", # Enables force capture (see next line for details)
	"force_capture_interval_seconds": "300", # The max interval between two frames in seconds
	"notification_freq": "10", # The save notifications will play 1/x, where x is the notificatiuon_freq value. A value of zero or below will result in no save notifications
	"useMotionDetection": "true", #[false/true] determines if motion sensing is enabled or not. If disabled, an image will be captured every frame determined by "fps" setting
	"useRelativeMotionSensitivity": "false", #[false/true] this mode checks if the previous pixel column values differ based on a percentage of the previous frames pixel column value. If this is false, then the frames are compared using a fixed offset
	"motion_sensitivity": "5", # changes the offset of gray value need to trigger the motion sensing (lower value is higher sensitvivity)
	"relative_motion_sensitivity": "0.10" # changes the percentage used for "useRelativeMotionSensitivity"
	
}