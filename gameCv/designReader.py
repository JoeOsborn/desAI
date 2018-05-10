"""

A look at computer vision & video games

Background subtraction in video games

"""
import math
import io
import numpy as np
from PIL import Image
import cv2
import image_slicer
import networkx as nx
from networkx.algorithms import matching
import scipy.stats
import random

#for the visualisation function
objects = []
colors = []

"""
Main functionality of the program
"""
def main():

    #live = { trackID : (frame first seen, [array of box tuples] ) }
    #dead = { trackID : (frame, [array of box tuples] ) }
    live  = {}
    dead = {}

    lastSeen = None

    prevEdge = None
    currEdge = None

    #values check these specific pixel values in the image
    currPix = []
    prevPix = []

    #video source files
    #video = cv2.VideoCapture("./video/mario.mov")
    video = cv2.VideoCapture("./video/zelda.mov")

    #frameCount
    frameC = 0

    #trackID number
    trackID = 0

    prevF = None
    currF = None

    scrollX = 0
    scrollY = 0

    netX = 0
    netY = 0

    slicedFrame = None

    movedBy = 0

    #offset dictionary
    offVals = {}

    while (True):

        ret, frame = video.read()

        #make sure initial values checkout
        if currF is None:
            currF = frame
        if prevF is None:
            prevF = frame

        #increment frameCount
        frameC+=1

        if (frameC < 500):
            continue
        elif (frameC >700):
            break

        #checks the first screen
        if (frameC>50 + 16 and frameC<482):
            assert len(live)==1, "frameCount"+ str(frameC) + " counts " + str( len(live) )
            assert len(dead)==0, "frameCount"+ str(frameC) + " counts " + str( len(live) )

        #once we're past the weird scrolling
        elif (frameC>500):
            assert len(live)>=1, "frameCount"+ str(frameC) + " counts " + str( len(live) )

        slicedFrame = slice(lastSeen, frame)

        #update the currFrame
        currF = frame

        #get the two boxes in the current frame that we're looking at
        if frameC > 0 and currF is not None:

            #recieve an array of all the box tuples we found due to a difference in two frames
            boxes = findBoxes(prevF, currF, frameC, trackID, scrollX, scrollY)

            #print( "boxes " + str(boxes) )

        #if ( frameC == 67 ):
        #    print ( "we have this many new boxes "+ str(boxes) )

        #iterate through the live objects we have
        # If a live box has identical/mostly identical pixels in current frame and prev frame, add it to boxes
        for l in live:

            #print("l in live : " + str(l))

            lastSeen = live[l][1][-1] #[currKey][1]

            #print("last seen box " + str(lastSeen) )

            #make sure we should keep
            if keepBox (lastSeen, boxes, prevF, currF, scrollX, scrollY):

                #
                boxes.append(lastSeen)

        #if ( frameC == 67 ):
            #print ( "we have this many boxes total "+ str(boxes) )

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

                #print("this current trackID" + str(trackID))

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

            #print( "live" + str(live) )

            newFrame = visualise(np.copy(frame), live)

            #cv2.imshow("Object Paths", newFrame )

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            #perform edge detection and return the pixel values
            currEdge = getEdgeFrame(frame)
            currPix = getCurrPix(currEdge)

            #TODO get a neighboring bounds from the list of pixels we could use try to register a color field
            #work on new and color colors based on edges
            #pick from edges and compare colors instead of edges
            #opencv template match for the neighborhood image (slightly larger than the color field area) (add x and sub y a bit)
            #sum up the color field to a big result that replaces the offset dictionary with bias towards the original
            #replace the comparePixels, slice to get template, and slice to get bigger area
            #for y,x in currPix
            #template += templatematch results

            #compare it to the prevPix if we have that then do the thing (see bottom)
            if ( prevEdge is not None):

                offVals = comparePixels(prevEdge, currPix)

                #print ("offVals " + str(offVals) )
                #scrollY, scrollX = offVals

                #offVals was a tuple
                #scrollX, scrollY = offVals

                #netX += offVals[0]
                #netY += offVals[1]

                #print ( "netX  " + str(netX) + "  netY  " + str(netY) )

                #sliceFrame(currF)

                movedBy = matchIt(currPix, prevF, currF)

            #update the previous pixel values
            prevPix = currPix

            #update the previous edge frame
            prevEdge = currEdge

            #update the previous frame reference
            prevF = currF

        else:

            break


    #print("live contents after everything... " + str(live))
    #print("dead contents after everything... " + str(dead))
"""
Handles the initial video movement detection via frame differences
offset new contours by scrollx, scrolly
"""
def findBoxes(frame1, frame2, frameC, trackID, dx, dy):

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

    #print ("contour count " + str(len(conts)) )

    # example of c in conts - [ [[357 298]] [[357 302]] [[361 302]] [[361 298]] ] or vector<vector<Point>>
    for c in conts:

        #area of the contour
        contSize = cv2.contourArea(c)

        #print ("size of the contSize " + str(contSize) )

        #make sure contours fall within a certain size
        if (750 <= contSize < 3000):

            #apply a bounding box over everything moving
            (x, y, w, h) = cv2.boundingRect(c)

            results.append( (x-dx,y-dy,w,h) )

    return results

#checks if the main loop should continue
def keepBox(oldB, newB, prevF, currF, dx, dy):

    amount = 25500

    #compares the x,y,w,h values
    for box in newB:

        #print("box" + str(box[currKey][1][0]))

        #get the distance between old Box and new Box
        dist = np.linalg.norm( np.subtract((box[0], box[1]), (oldB[0], oldB[1]))  )

        #print("oldB[1] " + str(oldB[1]) + "dist " + str(dist) )

        #
        if  dist <= (abs(dx)+abs(dy)):
            return False

    #compares content of the pixels
    (x,y,w,h) = oldB
    oldPix = prevF[y:y+h, x:x+w] #
    newPix = currF[y:y+h, x:x+w] #

    #print("cv2.absdiff(newPix, oldPix).sum() : " + str(cv2.absdiff(newPix, oldPix).sum()) )

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



#TODO ignore the bush object
#TODO use simm to compare the screen and if a threshold value falls below x


#thing corresponds to the key, 0, 1, 2, 3 , 4, etc
# points[thing] contains (frame first seen, all points we have for now)
# points[thing][1] contains all the points we have
#visualise(currFrame to draw on, values found in live - iterate, give unique color, connect the dots )
def visualise(frame, points):

    thisFrame = frame

    #thing in live
    for objCount, thing in enumerate(points):

        #this object is a new unique one, add it to a list
        if thing not in objects:
            #print("thing not in objects")
            objects.append(thing)
            colors.append( ( random.randint(0, 255),random.randint(0, 255),random.randint(0, 255) ) )

        for ind, pt in enumerate(points[thing][1]) :
            cv2.rectangle(thisFrame, pt[:2], ( pt[2]+ pt[0] ,pt[3]+pt[1]), colors[objCount] , 3 )

    return thisFrame

# - make sure the monster is lost when the player kills the monster

# - for the scrolling tracking, do contour detection/edge detecter (then pick random pixels)
# on the whole scene (not a difference between scenes) see if
# a lot of contours have moved (check if it's negative or positive).
# Eventually, the goal is to have to understand that the world is a whole map,
# there is an offset between the first area and the next area
# before a frame for loop is updated, call a function that will do edge detection
# picks x amount of pixels, then see what kind of x/y offesets occurred during to see what direction pixels
# have moved
# if the image is scrolling up, use slicing to cut away image parts that don't overlap, that is don't compare
# pieces of the image that wasn't originally in the old image frame

#creates and returns an edge frame
def getEdgeFrame(frame):

    #smooths the image with sharper edges - better for detailed super metroid
    #filtered = cv2.bilateralFilter(frame, 5, 175, 175)

    #find the 'strong' edges of the image
    #edgy = cv2.Canny(filtered, 75, 200)
    edgy = cv2.Canny(frame, 75, 200)
    #
    #print ("pixelValues   ::" + str(pixelValues))

    cv2.imshow("edge detected image", edgy)

    return edgy

#takes an edge frame and then picks different pixel values
def getCurrPix(edge):

    z=0

    pixNum = 500

    bounds=50

    #
    pixelValues = []

    #find the pieces that are white colored
    y,x = np.where(edge == 255) #coordinate in the matrix

    #length of # x
    #print ("len(x) " + str(len(x)))

    #picks ten random white pixel within a certain area
    while z<pixNum:

        i = np.random.randint(len(x))
        if bounds < x[i] < edge.shape[1]-bounds and bounds < y[i] < edge.shape[0]-bounds:
            pixelValues.append( (x[i],y[i]) )
            #print ( "pixel coords " + str( (y[i],x[i]) ) )
            z+=1

    #print ("pixelValues " + str(pixelValues) )

    return pixelValues

#TODO get a neighboring bounds from the list of pixels we could use try to register a color field
#work on new and color colors based on edges
#pick from edges and compare colors instead of edges
#opencv template match for the neighborhood image (slightly larger than the color field area) (add x and sub y a bit)
#sum up the color field to a big result that replaces the offset dictionary with bias towards the original
#replace the comparePixels, slice to get template, and slice to get bigger area
#for y,x in currPix
#template += templatematch results
#find the min loc from all the matches
def matchIt(pickPix, prevFrame, currFrame):

    size = 4
    winSize = 8
    movedVal = (0,0)
    offset = 4

    #Each position denotes a matching offset
    match = np.zeros(shape=(9,9))

    #for the (y,x) in pixel
    for pixel in pickPix:

        #a piece of the previous Frame
        thisTemp = prevFrame[pixel[1]-size:pixel[1]+size, pixel[0]-size:pixel[0]+size]

        #a piece from the current frame
        window = currFrame[pixel[1]-winSize:pixel[1]+winSize, pixel[0]-winSize:pixel[0]+winSize ]

        match += cv2.matchTemplate(window, thisTemp, cv2.TM_SQDIFF_NORMED)

        #print ("contents of match " + str(match) )

        cv2.imshow("matched", match)

    #get the min_loc of the added up pieces
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)

    #print ("min_val " + str(min_loc))
    #print ("min_loc " + str(min_loc))

    movedVal = (min_loc[0]-offset, min_loc[1]-offset)

    print ( "moved amount" + str(movedVal) )

    #
    return movedVal


#look for an x,y offest that works the best for all of the points
#offset kept by dx, dy
#offset new contours by x,y
#dictionary with offset in 2D { (-2,-2):0, (-2,1):0, (0,0):0 } inside comparePixls
#in keepbox might need to offset the boxes we find by xscroll, yscroll


#takes the previous edge detected frame and the last pixel values we took
#finds the offset with the largest count
def comparePixels(prevEdge, currPix):

    #point being compared at the moment
    checkPoint = None

    #cv2.imshow("passed into comparepixels", prevEdge)
    #

    offset = {}
    for xi in range(-6, 6):
        for yi in range(-6, 6):
            offset[(yi,xi)] = 0

    #
    #print ( "edge " + str(prevEdge) )

    #loop through the points we picked in the current frame and see if there are any neighboring white pixels
    for currPoint in currPix:

        #print ("currpoint" + str(currPoint))

        #loop through the tuple keys in offset dictionary
        for dir in offset:

            checkPoint = np.add(currPoint, dir) #ie point (100,100) gets added by (-2,-2)

            #print ("checkpoint" + str(checkPoint))

            #print ( str(checkPoint) )

            #if the offsetted point is white
            if (prevEdge[ (checkPoint[0], checkPoint[1]) ]) == 255:

                #increment the value inside the dictionary
                offset[dir] +=1

                #break

    maxOff = maxOffset(offset)
    #print ("offset contents" + str(offset))
    #print("maxOff" + str(maxOff) )

    #return dictionary of offset values to check scrolling
    #return offset
    return maxOff

"""
find key with max val
"""
def maxOffset(d):

     #print ("Offset dictionary " + str(d) )

     highest = max(d.values())

     smOffset = None

     #loop through the offset dictionary (k is tuple, v is value)
     for k, v in d.items() :

        #print ("k " + str(k) )

        #
        if v == highest:

            #
            if smOffset is None:

                smOffset = k

            #choose a smaller offset (sum of absolute value of dy and dx) if there's a tie
            elif ( ( abs(k[0])+ abs(k[1]) ) < (abs(smOffset[0])+abs(smOffset[1])) ):

                #print ("( abs(k[0])+ abs(k[1]) " + str( abs(k[0])+ abs(k[1]) ) )
                #print ("( abs(smOffset[0])+abs(smOffset[1]) ) " + str( abs(smOffset[0])+abs(smOffset[1]) ))

                smOffset = k

     print ("smOffset " + str(smOffset) )

     return smOffset


#function calls
main()

cv2.destroyAllWindows()

pass
