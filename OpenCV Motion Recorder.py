# import the necessary packages
import copy

from keyclip.keyclipwriter import KeyClipWriter
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", required=True,
	help="path to output directory")
ap.add_argument("-p", "--picamera", type=int, default=-1,
	help="whether or not the Raspberry Pi camera should be used")
ap.add_argument("-f", "--fps", type=int, default=25,
	help="FPS of output video")
ap.add_argument("-c", "--codec", type=str, default="MJPG",
	help="codec of output video")
ap.add_argument("-b", "--buffer-size", type=int, default=32,
	help="buffer size of video clip writer")
args = vars(ap.parse_args())

# initialize the video stream
vs = cv2.VideoCapture(r"\Compiled.mp4")
time.sleep(0.5)


# initialize key clip writer and the consecutive number of
# frames that have *not* contained any action
kcw = KeyClipWriter(bufSize=20)
consecFrames = 0


MOGsub = cv2.createBackgroundSubtractorMOG2(varThreshold=200, detectShadows=True)

# keep looping
while (vs.isOpened() == True):
	# grab the current frame, resize it, and initialize a
	# boolean used to indicate if the consecutive frames
	# counter should be updated
	ret, frame = vs.read()
	if ret == False:
		break
	if ret == True:
		frame = imutils.resize(frame, width=600)
		updateConsecFrames = True
		mogsub = MOGsub.apply(frame[100:600, 0:600])

		# blur the frame
		blurred = cv2.GaussianBlur(mogsub, (21, 21), 0)

		# perform
		# a series of dilations and erosions to remove any small
		# blobs left in the mask

		mask = cv2.erode(blurred, None, iterations=2)
		mask = cv2.dilate(mask, None, iterations=2)

		framecount = vs.get(cv2.CAP_PROP_POS_FRAMES)
		seconds = int(framecount // 25)
		minutes = int(seconds // 60)
		text1 = f"{minutes} minutes, {seconds%60} seconds"
		text2 = f"{framecount} frames"
		cv2.rectangle(frame, (0, 0), (600, 50), (255, 255, 255), -1)
		cv2.putText(frame, text1, (15, 15),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))
		cv2.putText(frame, text2, (295, 15),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))

		cv2.imshow("MOGsub", mask)


		# find contours in the mask
		cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)


		# only proceed if at least one contour was found
		if len(cnts) > 0:
			# find the largest contour in the mask
			c = max(cnts, key=cv2.contourArea)
			big = cv2.contourArea(c)
			# print(big)
			# only proceed if the area meets a minimum size
			if big > 15000:
				print(big)
				# reset the number of consecutive frames with
				# *no* action to zero and draw the circle
				# surrounding the object
				consecFrames = 0
				# cv2.drawContours(frame,c,-1,(0,0,255),1)

				# if we are not already recording, start recording
				if not kcw.recording:
					timestamp = datetime.datetime.now()
					p = "{}/{}.mp4".format(args["output"],
						timestamp.strftime("%Y%m%d-%H%M%S"))
					kcw.start(p, cv2.VideoWriter_fourcc(*'MP4V'),
						args["fps"])

		# otherwise, no action has taken place in this frame, so
		# increment the number of consecutive frames that contain
		# no action
		if updateConsecFrames:
			consecFrames += 1
		# update the key frame clip buffer
		kcw.update(frame)
		# if we are recording and reached a threshold on consecutive
		# number of frames with no action, stop recording the clip
		if kcw.recording and consecFrames == args["buffer_size"]:
			kcw.finish()
		# show the frame
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
		# if the `q` key was pressed, break from the loop
		if key == ord("q"):
			break

# if we are in the middle of recording a clip, wrap it up
if kcw.recording:
	kcw.finish()
# do a bit of cleanup

cv2.destroyAllWindows()
#python save_key_events_front.py --output output
