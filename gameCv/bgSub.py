#A look at background subtraction in video games
import numpy as np
import cv2

#used for finding colors in the image
video = cv2.VideoCapture("./video/test.mov")

#bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()
bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()

prevFrame = None

#separate values from video into usable chunks
ret, frame = video.read()

#case for first frame - in which we do not need to check for fram changes
if prevFrame is None:

    firstImage = cv2.bilateralFilter(frame, 5, 175, 175)

    firstEdge = cv2.Canny(firstImage, 75, 200)

    prevFrame = firstEdge

#background object needed for the MOG
while(1):

    #separate values from video into usable chunks
    ret, frame = video.read()

    bilateral_filtered_image = cv2.bilateralFilter(frame, 5, 175, 175)
    #cv2.imshow('Bilateral', bilateral_filtered_image)

    edge_detected_image = cv2.Canny(bilateral_filtered_image, 75, 200)
    #cv2.imshow('Edge', edge_detected_image)

    #find difference
    deltaF = cv2.absdiff(prevFrame, edge_detected_image)

    # dilate the delta
    # find contours
    deltaF = cv2.dilate(deltaF, None, iterations=2)
    _, conts, _ = cv2.findContours(deltaF, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in conts:

        #apply a bounding box over everything moving
    	(x, y, w, h) = cv2.boundingRect(c)
    	cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    #cv2.imshow('delta', deltaF)
    cv2.imshow('frame', frame)

    #update the last frame for comparison with the next current frame
    prevFrame = edge_detected_image

    k = cv2.waitKey(30) & 0xff

    if k == 27:

        break

cap.release()

cv2.destroyAllWindows()
