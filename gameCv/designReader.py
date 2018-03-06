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

"""
Handles the initial video movement detection via frame differences
"""
def detectDiff():

    #player tracker
    tracker = cv2.TrackerMIL_create()

    #used for finding colors in the image
    #video = cv2.VideoCapture("./video/mario.mov")
    video = cv2.VideoCapture("./video/zelda.mov")

    #bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()
    bgObj = cv2.bgsegm.createBackgroundSubtractorMOG()

    prevFrame = None

    #separate values from video into usable chunks
    ret, frame = video.read()

    #gets the width and height of the frame
    #srcW, srcH = frame.shape[:-1]

    #a list to store all the frames
    allFrames = []

    #dimensions of the pieces we want to split
    #splitDim = (srcW/32, srcH/30)

    #print("size of each block " + str(splitDim))

    i = 0 #for tracking frames

    #boundBox of ROI at first
    boundBox = None

    #case for first frame - in which we do not need to check for fram changes
    if prevFrame is None:

        firstImage = cv2.bilateralFilter(frame, 5, 175, 175)

        firstEdge = cv2.Canny(firstImage, 75, 200)

        prevFrame = firstEdge

    while ret:

        #separate values from video into usable chunks
        ret, frame = video.read()

        if (frame is None ):
            break

        else:

            #save the current frame
            #if (i%10==0):
                #cv2.imwrite("./images/"+ str(i)+ ".jpg", frame)

            #store a list of actual image file dirs
            allFrames.append("./images/"+ str(i)+ ".jpg")

            #smooths the image with sharper edges - better for detailed super metroid
            #slightly heavier on performance
            bilateral_filtered_image = cv2.bilateralFilter(frame, 5, 175, 175)

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
                if (contSize > 500):

                    #apply a bounding box over everything moving
                    (x, y, w, h) = cv2.boundingRect(c)

                    #print(w,h)

                    if boundBox is None:

                        boundBox = (x, y, w, h)

                        #initiate the tracker
                        ret = tracker.init(frame, boundBox)

                    #find region of interest
                    roi = frame[y:y+h, x:x+w]

                    boundBox = (x, y, w, h)

                    #save roi
                    if i%5==0:
                        cv2.imwrite("./templates/"+ str(i)+ ".jpg", roi)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    #print("rectangle frame size : " + str( (x+w, y+h)) )
                    #print("current contour size : " + str(contSize) )
                    #print("current center : " + str( (x+w/2, y+h/2) ))

                    if contSize in objects:

                        print("already contains in the dictionary")

                        data[ round(contSize, 3)  ].append ( (x,y,w,h) )

                    else:

                        data [ round(contSize, 3) ] = [ (x,y,w,h) ]

                    #extra - build templates
                    #cv2.imshow("ROI" , roi)
                    #cv2.waitKey(0)


            if boundBox is not None:

                 # Update tracker
                ret, boundBox = tracker.update(frame)

                if ret:
                    p1 = (int(boundBox[0]), int(boundBox[1]))
                    p2 = (int(boundBox[0] + boundBox[2]), int(boundBox[1] + boundBox[3]))
                    cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
                else:
                    print("Mission failed...")

            cv2.imshow("frame", frame)

            #update the last frame for comparison with the next current frame
            prevFrame = edge_detected_image

            i+=1

            k = cv2.waitKey(30) & 0xff

            if k == 27:

                break

    video.release()

#Find still objects that we've seen
#def findStills():


"""

Attempts to group (x,y,w,h) values within contour range

"""

def groupObjects():

    trigCt = 0

    objC = 0
    objName = "obj"+str(objC)

    innerDone = False

    #loop through the previous dictionary constructed by detectDiff()
    for size, tuples in data.items():

        innerDone = False

        #it contains contour sizes as keys, and tuple with positional/dimensional values
        #check if the contour size exists in any of the new dictionary's value values, yeah nested values - "contours"
        if len(objects) > 0:

            for keys in list(objects):

                #print("the keys in objects is ... " + str(objects) )

                #print("objects[keys][contours]" + str(objects[keys]["contours"]) )

                #loop through the contour sizes of current key...
                for values in objects[keys]["contours"]:

                    #this size was seen before...
                    if size in objects[keys]["contours"]:

                        print("added something we've seen before ")
                        trigCt +=1

                        #well add it to the object
                        objects[keys]["contours"].append(size)

                        #center = (objects[keys][0].br() + objects[keys][0].tl())*0.5;

                        innerDone = True

                    #contour is in range
                    elif ( (values*0.95) <= size < (values+170*1.05) ):

                        trigCt +=1

                        objects[keys]["contours"].append( size )
                        objects[keys]["tuples"].append(tuples)

                        innerDone = True

                        break

                    #this wasn't found within range
                    elif size not in objects[keys]["contours"]:

                        trigCt +=1

                        #print("making a new entry")

                        objC+=1

                        objName = "obj"+str(objC)

                        objects[objName] = {"tuples" : [tuples], "contours": [ size ] }

                        innerDone = True

                        break

                #break out of the inner loop
                if innerDone:
                    break

        #looks like we don't have anything to compare it to..
        else:
            objects[objName] = {"tuples" : [tuples], "contours": [ size ] }
            objC+=1
            #print("object dict " + str(objects) )

        #print("groupObjects() has ran " + str(trigCt))

#function calls
detectDiff()

groupObjects()

print("object dict " + str(objects["obj0"]) )
#print("data " + str(len(data)))

#cv2.destroyAllWindows()

#where is everything persistence

# use code in emails to match up the old rectangles with thew new rectangles

"""
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
