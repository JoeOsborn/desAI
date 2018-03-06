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

#dictionary for the objects as we try to group

#structure - { contour size : [array of vector tuples by (x,y,w,h)] }
data = {}

# structure -
#              { "objName" : {
#                          "tuples" : [(x,y,w,h)]},
#                          "contours" : [ size1, size2],
#                           }
#              }
objects = {}

#Handles the main loop
def main():

    #video source files
    #video = cv2.VideoCapture("./video/mario.mov")
    video = cv2.VideoCapture("./video/zelda.mov")

    #live = { trackID : (frame first seen, [array of box tuples] ) }
    #dead = { trackID : (frame, [array of box tuples] ) }
    live  = {}
    dead = {}

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

        print("frameCount " + str(frameC))
        #print("frameCount " + str(frame))

        ret, frame = video.read()

        #increment frameCount
        frameC+=1

        #get the two boxes in the current frame that we're looking at
        if frameC > 0:
            #update the currFrame
            currF = frame

            #recieve an array of all the box tuples we found
            boxes = findBoxes(prevF, currF)

            print( boxes )

        for l in live:
            lastSeen = l[1][-1]
            if keepRun (lastSeen, results, prevFrame, frame):
                boxes.append(lastSeen)
                prevF = currF

"""
Handles the initial video movement detection via frame differences
"""
def findBoxes(frame1, frame2):

    firstImg = cv2.bilateralFilter(frame1, 5, 175, 175)

    firstEdge = cv2.Canny(firstImg, 75, 200)

    prevFrame = firstEdge

    #results from the contour
    results = []

    #bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()
    bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()

    #smooths the image with sharper edges - better for detailed super metroid
    #slightly heavier on performance
    bilateral_filtered_image = cv2.bilateralFilter(frame2, 5, 175, 175)

    #cv2.imshow('Bilateral', bilateral_filtered_image)

    #find the 'strong' edges of the iamge
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
    # conts is a vector of points
    _, conts, _ = cv2.findContours(deltaF, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # example of c in conts - [ [[357 298]] [[357 302]] [[361 302]] [[361 298]] ] or vector<vector<Point>>
    for c in conts:

        #print ("this is c in conts : " + str(c) )

        #area of the contour
        contSize = cv2.contourArea(c)

        #make sure it's a certain size
        if (500 <= contSize < 1200):

            #apply a bounding box over everything moving
            (x, y, w, h) = cv2.boundingRect(c)

            results.append( (x,y,w,h) )

            #find region of interest
            #roi = frame1[y:y+h, x:x+w]
            #save roi
            #cv2.imwrite("./templates/"+ "o" + ".jpg", roi)

    return results

#checks if the main loop should continue
def keepRun(oldB, newB, prevF, currF):

    amount = 100

    #compares the x,y,w,h values
    #for oldB in newB:
        #if same oldB-10 <= newB <= oldB+10
    #        return False

    #(x,y,w,h contains oldB)

    #compares content of the pixels
    oldPix = prevF [y:y+h, x:x+w]
    newPix = currF [y:y+h, x:x+w]

    if cv2.absdiff(newPix, oldPix) > amount:
        return True

    return False


#function calls
main()


#cv2.destroyAllWindows()

# use code in emails to match up the old rectangles with thew new rectangles

"""
def biMatch (live, boxes):

import networkx as nx
from networkx.algorithms import matching

sigma = 8.0
min_gate = 5.0

def weight(orig, post, R):
  beforeRect = np.array(orig[0..4]) # assuming post is a 4-tuple of xywh, you can use whatever transformation makes sense here
  postRect = np.array(post[0..4]) # assuming post is a 4-tuple of xywh, you can use whatever transformation makes sense here
  # TODO: maybe figure out a way to use the pixel values in the image as well
  distance = np.linalg.norm(postRect - origRect)
  return scipy.stats.norm(0, R).pdf(distance)

# in some loop, which ends with before_objects = after_objects before continuing around and in whose first iteration before_objects is empty.
B = nx.Graph()
for oi in range(len(before_objects)):
  B.add_node(“before{}”.format(oi))
for pi in range(len(after_objects)): # already augmented with the “stay” objects
  B.add_node(“created{}”.format(pi))
  B.add_node(“after{}”.format(pi))
  B.add_edge(“created{}”.format(oi), “after{}”.format(pi), weight=scipy.stats.norm(0, sigma).pdf(min_gate * sigma)
for oi,o in enumerate(before_objects):
  for pi,p in enumerate(after_objects):
    B.add_edge(“before{}”.format(oi), “after{}”.format(pi), weight=weight(o, p, 8.0)
match = matching.max_weight_matching(B)

just_deleted = set()
just_created = set()
for pi,p in enumerate(after_objects):
  oi_node = match[“after{}”.format(pi)]
  if ‘start’ in oi_node:
    just_created.add(“after{}”.format(pi))
    runs.push(…) # add a new run here
  else:
    oi = int(oi_node[5:])
    o = before_objects[o]
    runs[…]… # update the corresponding run here.  You need a way to connect before_objects to runs.  It might make sense to even just use runs _as_ before_objects, filtering for only runs that have not ended.  Or have separate live_runs and old_runs arrays.
to_delete = set()
for oi,o in enumerate(before_objects):
  if “before{}”.format(oi) not in match:
    pass
      # maybe move the run corresponding to this object into old_runs
      # or otherwise deal with the fact this object is not around anymore.
      # “coasting” could be used here to give objects a grace period before killing them from runs.
"""
