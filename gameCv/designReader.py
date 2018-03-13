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
import scipy.stats

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

    #trackID number
    trackID = 0

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
            boxes = findBoxes(prevF, currF, frameC, trackID)

            print( "boxes " + str(boxes) )

        #if live is empty
        if len(live)==0:
            live = boxes

        #current key we have
        keyCount = 0
        currKey = "track"+str(keyCount)

        #iterate through the live objects we have
        # If a live box has identical/mostly identical pixels in current frame and prev frame, add it to boxes
        for l in live:

            #print("l in live : " + str(l))

            lastSeen = l[currKey][1]

            print("last seen " + str(lastSeen) )

            #make sure we should keep
            if keepBox (lastSeen, boxes, prevF, currF, currKey):

                #
                boxes.append(lastSeen)

                keyCount +=1


        #take in live and the boxes we found this screen and perform bipartite matching on them
        match = biMatch(live, boxes, currKey)

        # update live{} with content from boxes using bipartite matching
        # ^ add new tracks to live and move from live to dead any track that didn’t get matched with a box in boxes

        #update the previous frame reference
        prevF = currF

"""
Handles the initial video movement detection via frame differences
"""
def findBoxes(frame1, frame2, frameC, trackID):

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

            results.append( {str("track"+str(trackID)): (frameC, (x,y,w,h))} )

    return results

#checks if the main loop should continue
def keepBox(oldB, newB, prevF, currF, currKey):

    amount = 100

    #compares the x,y,w,h values
    for box in newB:

        #print("oldB" + str(oldB) )

        #print ("box" + str(box) )

        #print("newB" + str(newB) )

        print("box" + str(box[currKey][1][0]))

        #get the distance between old Box and new Box
        dist = np.linalg.norm( np.subtract((box[currKey][1][0], box[currKey][1][1]), (oldB[0], oldB[1]))  )

        if  dist >= 10:
            return False

    print ("prevF" + str(prevF) )
    print ("currF" + str(currF) )
    #compares content of the pixels
    #oldPix = prevF [y:y+h, x:x+w]
    #newPix = currF [y:y+h, x:x+w]
    oldPix = prevF
    newPix = currF

    if cv2.absdiff(newPix, oldPix).sum() > amount:
        return True

    return False

#bipartite matching function
def biMatch (live, boxes, currKey):

    sigma = 8.0
    min_gate = 5.0

    print("live contains : " + str(live) )

    print("boxes contains : " + str(boxes) )

    def weight(orig, post, R):

        print ("weight()'s orig : " + str( orig[currKey][1] ))

        print ("weight()'s post : " + str( post[currKey][1] ))

        beforeRect = np.array(orig[currKey][1] )

        postRect = np.array(post[currKey][1] )

        distance = np.linalg.norm(postRect - beforeRect)

        return scipy.stats.norm(0, R).pdf(distance)

    # in some loop, which ends with live = after_objects before continuing around and in whose first iteration live is empty.
    B = nx.Graph()

    print("length of live :" + str( len(live) ) )

    for oi in range(len(live)):

        print ("for oi in range(len(live)): " + str(oi))

        B.add_node("before{}".format(oi))

        for pi in range(len(boxes)): # already augmented with the “stay” objects

            B.add_node("created{}".format(pi))

            B.add_node("after{}".format(pi))

            B.add_edge("created{}".format(oi), "after{}".format(pi), weight=scipy.stats.norm(0, sigma).pdf(min_gate * sigma))

    for oi, o in enumerate(live):

      for pi,p in enumerate(boxes):

        B.add_edge("before{}".format(oi), "after{}".format(pi), weight=weight(o, p, 8.0) )

    match = matching.max_weight_matching(B)

    print ("match contents " + str(match) )

    just_deleted = set()

    just_created = set()

    for pi, p in enumerate(boxes):

        print ("loop contents : pi " + str(pi) + "  p:   " + str(p) )

        oi_node = match["after{}".format(pi)]

        if "start" in oi_node:

            just_created.add("after{}".format(pi))

            live.update(p)

        else:

            print("match contents " + str(match))

            print( "oi_node " + str(oi_node))

            oi = int(oi_node[5:])

            o = live[o]

            live[o] = o

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
