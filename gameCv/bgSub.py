#A look at background subtraction in video games
import numpy as np
import cv2

#used for finding colors in the image
video = cv2.VideoCapture("./video/test.mov")

bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()

#background object needed for the MOG
while(1):

    ret, frame = video.read()

    fgmask = bgObj.apply(frame)

    cv2.imshow('frame',fgmask)
    cv2.imshow('ret',fgmask)

    k = cv2.waitKey(30) & 0xff

    if k == 27:

        break

cap.release()

cv2.destroyAllWindows()
