Add your email to the environment.json file to receive daily warning emails when sentry storage is over 70% (You will also need to add an app password (NOT your email login!), this can be done in the security settings of your gmail account).

To exit the application, click on the video window, and press 'q'

You can also run the script in a cloud directory (such as a desktop dropbox folder) to remotely view recent frames. Be sure to turn down the frame rate if you do this however, because rapidly creating files can create issues with the syncing of your desktop cloud folder in my experience (most likely due to files being created faster than they can be uploaded).


BREAKDOWN OF .json FILE:
{
	"root_directory': "",  # leave this as an empty string for now, it is supposed to let you define the root of where data is stored but is broken for now
	"data_directory": "data",  # this is the folder name that all files will be saved to. Folder is located in the same directory as the script
	"camera_directory": "securityCamera", # This is the name of the folder generated when the mode is set to sentry (or put into sentry mode thorugh the terminal mode)
	"camera_port": "0",  # if you are using 1 camera, this will be set to 0. If you have several cameras, set this to a different number (try 1, 2, etc) until the correct camera is being used (currently only support for 1 camera, you can run the script twice in different directories for 2+)
	"mode": "sentry",  # DEPRECATED will be deleted in future update
	"use_live_video_viewer": true,  # disables the VideoStream window. This also means there is no windows to press 'q' on to safely close the program. Only recommended changing to 'false' for use case where program is not stopped until reboot
	"send_emails": false,  # [false/true] Determines whether emails should be sent using credentials at start of .json
	"from_email": "your FROM (bot) email goes here",
	"from_email_pass": "your FROM (bot) email password goes here (the app password, not login, see README)", # For gmail go to your google acct seeting, then Security, and App passwords (select app [Custom], select device [Tested on Windows, should work on Mac])
	"to_email": "your TO email goes here",
	"max_sentry_storage": "10",   The max amount of disk space allocaed for sentry images (excluding the training folders)
	"storage_units": "GB",   the untis of disk space allocated. Can be in MB or GB
	"fps": "60",   The Frame/second that captures are taken in sentry mode (This value does not affect motion_sensing) You can use a float or int here (e.g 1.5 or 1). This is max fps, if your camera or computer cannot run at this fps, it will run at max fps
	"use_force_capture": true,  # Enables force capture (see next line for details)
	"force_capture_interval_seconds": "300",  # The max interval between two frames in seconds
	"notification_freq": "10",  # The save notifications will play 1/x, where x is the notificatiuon_freq value. A value of zero or below will result in no save notifications
	"use_motion_detection": true,  #[false/true] determines if motion sensing is enabled or not. If disabled, an image will be captured every frame determined by "fps" setting
	"motion_sensitivity": "5",  # changes the offset of gray value need to trigger the motion sensing (lower value is higher sensitvivity)
	"motion_sensing_persistence": "5"  # this is the number of seconds that captures are saved since motion was detected. Set to 0 to disable

}
