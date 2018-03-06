#A look at background subtraction in video games

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

    #case for first frame - in which we do not need to check for fram changes
    if prevFrame is None:

        firstImage = cv2.bilateralFilter(frame, 5, 175, 175)

        firstEdge = cv2.Canny(firstImage, 75, 200)

        prevFrame = firstEdge

    #while(1):

    while ret:

        #separate values from video into usable chunks
        ret, frame = video.read()

        if (frame is None ):
            break

        else:

            #save the current frame
#            if (i%10==0):
#                cv2.imwrite("./images/"+ str(i)+ ".jpg", frame)

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

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    #print("rectangle frame size : " + str( (x+w, y+h)) )
                    #print("current contour size : " + str(contSize) )
                    #print("current center : " + str( (x+w/2, y+h/2) ))

                    if contSize in objects:

                        print("already contains in the dictionary")

                        data[ round(contSize, 3)  ].append ( (x,y,w,h) )

                    else:

                        data[ round(contSize, 3) ] = [ (x,y,w,h) ]

                    #extra - build templates
                    croppedFrame = frame[x:(x+int(x/2)), y:(y+int(y/2))]
                    cv2.imshow("cropped" , croppedFrame)
                    #cv2.waitKey(0)

            cv2.imshow("frame", frame)

            #update the last frame for comparison with the next current frame
            prevFrame = edge_detected_image

            i+=1

            k = cv2.waitKey(30) & 0xff

            if k == 27:

                break

    video.release()

"""
Attempts to sort/ associate vector positions that are relative to one object
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

#extract ROI to build template
#def leROIJenkins():


#function calls
detectDiff()

#print("stuffff" + str(data) )

groupObjects()

print("object dict " + str(objects["obj0"]) )
#print("data " + str(len(data)))

#cv2.destroyAllWindows()

#where is everything persistence

# use code in emails to match up the old rectangles with thew new rectangles
