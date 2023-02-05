Add your email to the environment.json file to receive daily warning emails when capture storage is over 70% (You will also need to add an app password (NOT your email login!), this can be done in the security settings of your gmail account).
To exit the application, click on the video window, and press 'q'
You can also run the script in a cloud directory (such as a desktop dropbox folder) to remotely view recent frames. Be sure to turn down the frame rate if you do this however, because rapidly creating files can create issues with the syncing of your desktop cloud folder in my experience (most likely due to files being created faster than they can be uploaded).

BREAKDOWN OF environment.json FILE:
{
	"camera_port": "0",  # if you are using 1 camera, this will be set to 0. If you have several cameras, set this to a different number (try 1, 2, etc) until the correct camera is being used (currently only support for 1 camera, you can run the script twice in different directories for 2+)
	"use_live_video_viewer": true,  # disables the VideoStream window. This also means there is no windows to press 'q' on to safely close the program. Only recommended changing to 'false' for use case where program is not stopped until reboot
	"send_emails": false,  # [false/true] Determines whether emails should be sent using credentials at start of .json
	"from_email": "your FROM (bot) email goes here",
	"from_email_pass": "your FROM (bot) email password goes here (the app password, not login, see README)", # For gmail go to your google acct setting, then Security, and App passwords (select app [Custom])
	"to_email": "your TO email goes here",
	"max_capture_storage": "10",   The max amount of disk space allocated for image captures
	"storage_units": "GB",   the units of disk space allocated. Can be in B, KB, MB, or GB
	"fps": "1",  # You can use a float or int here (e.g 1.5 or 1). This is max fps, if your camera or computer cannot run at this fps, it will run at max fps
	"notification_freq": "10",  # Controls how many captures to wait before displaying a message
}
