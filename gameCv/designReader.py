#A look at background subtraction in video games
#playing around with sample tracker code

#TODO group things by contour size
#TODO store a data array in the method that joseph recommended

import math
import io
import numpy as np
from PIL import Image
import cv2
import image_slicer
import networkx as nx
from networkx.algorithms import matching


"""
Main functionality of the program
"""
def main():

    #live = { trackID : (frame first seen, [array of box tuples] ) }
    #dead = { trackID : (frame, [array of box tuples] ) }
    live  = {}
    dead = {}

    #video source files
    #video = cv2.VideoCapture("./video/mario.mov")
    video = cv2.VideoCapture("./video/zelda.mov")

    #frameCount
    frameC = 0

    prevF = None
    currF = None

    #initial frameRead
    ret, frame = video.read()

    #initial frame setting
    prevF = frame
    currF = frame

    while ret:

        #print("frameCount " + str(frameC))

        ret, frame = video.read()

        #increment frameCount
        frameC+=1

        #update the currFrame
        currF = frame

        #get the two boxes in the current frame that we're looking at
        if frameC > 0 and currF is not None:

            #recieve an array of all the box tuples we found due to a difference in two frames
            boxes = findBoxes(prevF, currF)

            print( "boxes " + str(boxes) )

        #iterate through the live objects we have
        # If a live box has identical/mostly identical pixels in current frame and prev frame, add it to boxes
        for l in live:

            lastSeen = l[1][-1]

            #print("last seen " + str(lastSeen) )

            #make sure we should keep
            if keepBox (lastSeen, results, prevF, currF):

                #
                boxes.append(lastSeen)


        #take in live and the boxes we found this screen and perform bipartite matching on them
        match = biMatch(live, boxes)

        # update live{} with content from boxes using bipartite matching
        # ^ add new tracks to live and move from live to dead any track that didn’t get matched with a box in boxes

        #update the previous frame reference
        prevF = currF

"""
Handles the initial video movement detection via frame differences
"""
def findBoxes(frame1, frame2):

    firstImg = cv2.bilateralFilter(frame1, 5, 175, 175)

    firstEdge = cv2.Canny(firstImg, 75, 200)

    #our frame after Canny and edge detection
    prevFrame = firstEdge

    #results from the contour
    results = []

    #bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()
    bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()

    #smooths the image with sharper edges - better for detailed super metroid
    #slightly heavier on performance
    bilateral_filtered_image = cv2.bilateralFilter(frame2, 5, 175, 175)

    #cv2.imshow('Bilateral', bilateral_filtered_image)

    #find the 'strong' edges of the image
    edge_detected_image = cv2.Canny(bilateral_filtered_image, 75, 200)

    #cv2.imshow('Edge', edge_detected_image)

    #find difference
    deltaF = cv2.absdiff(prevFrame, edge_detected_image)

    # dilate the delta
    # find contours
    deltaF = cv2.dilate(deltaF, None, iterations=2)

    #cv2.imshow("frame difference", deltaF)

    # https://docs.opencv.org/2.4/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html?highlight=findcontours#findcontours
    # findContours(image, retrieval mode, contour approximation)
    _, conts, _ = cv2.findContours(deltaF, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # example of c in conts - [ [[357 298]] [[357 302]] [[361 302]] [[361 298]] ] or vector<vector<Point>>
    for c in conts:
        #area of the contour
        contSize = cv2.contourArea(c)

        #make sure contours fall within a certain size
        if (500 <= contSize < 1500):

            #apply a bounding box over everything moving
            (x, y, w, h) = cv2.boundingRect(c)

            results.append( (x,y,w,h) )

    return results

#checks if the main loop should continue
def keepBox(oldB, newB, prevF, currF):

    amount = 100

    #compares the x,y,w,h values
    for oldB in newB:
        if oldB-10 <= newB <= oldB+10:
            return False

    #(x,y,w,h contains oldB)

    #compares content of the pixels
    oldPix = prevF [y:y+h, x:x+w]
    newPix = currF [y:y+h, x:x+w]

    if cv2.absdiff(newPix, oldPix) > amount:
        return True

    return False

#bipartite matching function
def biMatch (live, boxes):

    #print("live contains : " + str(live) )

    #print("boxes contains : " + str(boxes) )

    sigma = 8.0
    min_gate = 5.0


    def weight(orig, post, R):
        beforeRect = np.array(orig) # assuming orig is a 4-tuple of xywh, you can use whatever transformation makes sense here
        postRect = np.array(post) # assuming post is a 4-tuple of xywh, you can use whatever transformation makes sense here

        distance = np.linalg.norm(postRect - origRect)
        return scipy.stats.norm(0, R).pdf(distance)

    # in some loop, which ends with live = after_objects before continuing around and in whose first iteration live is empty.
    B = nx.Graph()

    for oi in range(len(live)):
        B.add_node("before{}".format(oi))
        for pi in range(len(boxes)): # already augmented with the “stay” objects
            B.add_node("created{}".format(pi))
            B.add_node("after{}".format(pi))
            B.add_edge("created{}".format(oi), "after{}".format(pi), weight=scipy.stats.norm(0, sigma).pdf(min_gate * sigma))
    for oi, o in enumerate(live):
      for pi,p in enumerate(boxes):
        B.add_edge("before{}".format(oi), "after{}".format(pi), weight=weight(o, p, 8.0) )

    match = matching.max_weight_matching(B)

    just_deleted = set()
    just_created = set()

    for pi,p in enumerate(boxes):
      oi_node = match["after{}".format(pi)]
      if "start" in oi_node:
        just_created.add("after{}".format(pi))
        runs.push(p) # add a new run here
      else:
        oi = int(oi_node[5:])
        o = live[o]
        runs[o] = o # update the corresponding run here.  You need a way to connect live to runs.  It might make sense to even just use runs _as_ live, filtering for only runs that have not ended.  Or have separate live_runs and old_runs arrays.

    to_delete = set()

    for oi,o in enumerate(live):
      if "before{}".format(oi) not in match:
        pass
          # maybe move the run corresponding to this object into old_runs
          # or otherwise deal with the fact this object is not around anymore.
          # “coasting” could be used here to give objects a grace period before killing them from runs.

    return match

#function calls
main()

#cv2.destroyAllWindows()

# use code in emails to match up the old rectangles with thew new rectangles
