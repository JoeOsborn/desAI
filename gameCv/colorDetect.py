from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import utils
import cv2
import colorsys

#https://stackoverflow.com/questions/24152553/hsv-to-rgb-and-back-without-floating-point-math-in-python
def RGB_2_HSV(RGB):
	#Converts an integer RGB tuple (value range from 0 to 255) to an HSV tuple

	# Unpack the tuple for readability
	R, G, B = RGB

	# Compute the H value by finding the maximum of the RGB values
	RGB_Max = max(RGB)
	RGB_Min = min(RGB)

	# Compute the value
	V = RGB_Max;
	if V == 0:
	    H = S = 0
	    return (H,S,V)


	# Compute the saturation value
	S = 255 * (RGB_Max - RGB_Min) // V

	if S == 0:
	    H = 0
	    return (H, S, V)

	# Compute the Hue
	if RGB_Max == R:
	    H = 0 + 43*(G - B)//(RGB_Max - RGB_Min)
	elif RGB_Max == G:
	    H = 85 + 43*(B - R)//(RGB_Max - RGB_Min)
	else: # RGB_MAX == B
	    H = 171 + 43*(R - G)//(RGB_Max - RGB_Min)

	return (H, S, V)

#
foundRGBColors = []

#used for finding colors in the image
image = cv2.imread("./images/image.png",cv2.IMREAD_COLOR)
#used for hsv color detection
image2 = cv2.imread("./images/image.png",cv2.IMREAD_COLOR)

#print (image.shape)

#convery to RGB to display normally
image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

#reshape the image to be a list of pixels
image = image.reshape((image.shape[0] * image.shape[1], 3))

# cluster the pixel intensities
clt = KMeans(7)
clt.fit(image)

# build a histogram of clusters and then create a figure
# representing the number of pixels labeled to each color
hist = utils.centroid_histogram(clt)
bar = utils.plot_colors(hist, clt.cluster_centers_)



#
# Go through the colors and blob detect
# int(round(x))
#
for datcolor in zip(clt.cluster_centers_):

    #for tuple in datcolor[0]:

    actualTuple = ( int(round(datcolor[0][0])), int(round(datcolor[0][1])), int(round(datcolor[0][2])) )

    foundRGBColors.append(actualTuple)

print(foundRGBColors)

#convert the unsused BGR image2 into HSV for easier usage in the image detection
hsv = cv2.cvtColor(image2, cv2.COLOR_BGR2HSV)

#iterate through the rgb, convert to hsv, and search
for rgbVal in foundRGBColors:
    #convert RGB to HSV
    thisHSV = RGB_2_HSV( rgbVal )
    print(thisHSV)

    #apply a mask that will only seek out this one color in the image
    mask = cv2.inRange(hsv, (thisHSV[0]-10, 100, 100), (thisHSV[1]+10, 255, 255))

    res = cv2.bitwise_and(image2,image2, mask= mask)

    cv2.imshow('image2', image2)
    cv2.imshow('mask', mask)
    cv2.imshow('res', res)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
