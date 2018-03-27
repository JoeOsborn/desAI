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

    while (True):

        ret, frame = video.read()

        #make sure initial values checkout
        if currF is None:
            currF = frame
        if prevF is None:
            prevF = frame

        #increment frameCount
        frameC+=1

        #update the currFrame
        currF = frame

        #get the two boxes in the current frame that we're looking at
        if frameC > 0 and currF is not None:

            #recieve an array of all the box tuples we found due to a difference in two frames
            boxes = findBoxes(prevF, currF, frameC, trackID)

            #print( "boxes " + str(boxes) )

        #iterate through the live objects we have
        # If a live box has identical/mostly identical pixels in current frame and prev frame, add it to boxes
        for l in live:

            #print("l in live : " + str(l))

            lastSeen = live[l][1][-1] #[currKey][1]

            #print("last seen box " + str(lastSeen) )

            #make sure we should keep
            if keepBox (lastSeen, boxes, prevF, currF):

                #
                boxes.append(lastSeen)

        #take in live and the boxes we found this screen and perform bipartite matching on them
        match = biMatch(live, boxes)

        # update live{} with content from boxes using bipartite matching
        # ^ add new tracks to live and move from live to dead any track that didn’t get matched with a box in boxes
        # new wasnt seen before
        # new - continuation
        # was new, delete now

        for ind, box in enumerate(boxes):

            key = "after"+str(ind)

            pair = match[key] #now

            if "created" in pair:
                live[trackID] = (frameC, [box])
                trackID+=1

            else:
                #get the trackID
                newId = int(pair[6:])

                #
                live[newId][1].append(box)

        for obj in list(live.keys()):

            #if these objects were seen before the current frame
            if live[obj][0] < frameC:

                key = "before{}".format(obj)

                #was old thing matched with new thing
                if key not in match:

                    dead[obj] = live[obj] #add entry to dead
                    del live[obj] #remove from live

        #show the frame ... if it exists
        if ret:

            #visualise(currF, live)

            #cv2.imshow("Object Paths", currF)

            cv2.imshow("Object Paths", visualise(currF, live) )

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            #update the previous frame reference
            prevF = currF
        else:
            break


    #print("live contents after everything... " + str(live))
    #print("dead contents after everything... " + str(dead))
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

            results.append( (x,y,w,h) )

    return results

#checks if the main loop should continue
def keepBox(oldB, newB, prevF, currF):

    amount = 100

    #compares the x,y,w,h values
    for box in newB:

        #print("oldB" + str(oldB) )

        #print ("box" + str(box) )

        #print("newB" + str(newB) )

        #print("box" + str(box[currKey][1][0]))

        #get the distance between old Box and new Box
        dist = np.linalg.norm( np.subtract((box[0], box[1]), (oldB[0], oldB[1]))  )

        if  dist <= 4:
            return True

    #compares content of the pixels
    (x,y,w,h) = oldB
    oldPix = prevF[y:y+h, x:x+w]
    newPix = currF[y:y+h, x:x+w]

    if cv2.absdiff(newPix, oldPix).sum() < amount:
        return True

    return False

#bipartite matching function
def biMatch (live, boxes):

    sigma = 8.0
    min_gate = 5.0

    #print("live contains : " + str(live) )

    #print("boxes contains : " + str(boxes) )

    def weight(orig, post, R):

        #print ("weight()'s orig : " + str( orig[currKey][1] ))

        #print ("weight()'s post : " + str( post[currKey][1] ))

        beforeRect = np.array(orig[1][-1] )

        postRect = np.array(post)

        distance = np.linalg.norm(postRect - beforeRect)

        return scipy.stats.norm(0, R).pdf(distance)

    # in some loop, which ends with live = after_objects before continuing around and in whose first iteration live is empty.
    B = nx.Graph()

    #print("length of live :" + str( len(live) ) )

    for oi in live:

        #print ("for oi in range(len(live)): " + str(oi))

        B.add_node("before{}".format(oi))

    for pi in range(len(boxes)): # already augmented with the “stay” objects

        B.add_node("created{}".format(pi))

        B.add_node("after{}".format(pi))

        B.add_edge("created{}".format(pi), "after{}".format(pi), weight=scipy.stats.norm(0, sigma).pdf(min_gate * sigma))

    for oi, o in live.items():

      for pi, p in enumerate(boxes):

        B.add_edge("before{}".format(oi), "after{}".format(pi), weight=weight(o, p, 8.0) )

    match = matching.max_weight_matching(B)

    #print ("match contents " + str(match) )

    return match

#visualise(currFrame to draw on, values found in live - iterate, give unique color, onnect the dots )
def visualise(frame, points):

    lineFrame = frame

    #thing in live
    for thing in points:
        #print ("thing in points is " + str( points[thing][1][iterate through here] ) )
        for ind, coord in enumerate(points[thing][1]):

            #print("index " + str(ind) )
            #print("coord " + str(coord) )

            #if are not looking at the first element in the array
            #also ouch, my eyes
            if ind!=0:
                cv2.line(lineFrame, points[thing][1][ind-1][:2], points[thing][1][ind-1][:2], (255,0,0), 5 )

    return lineFrame

#function calls
main()

cv2.destroyAllWindows()

# use code in emails to match up the old rectangles with thew new rectangles
