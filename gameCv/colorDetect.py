from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import math
import utils
import cv2
import colorsys

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

plt.figure()
plt.axis("off")
plt.imshow(bar)
plt.show()

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
	h,s,v = colorsys.rgb_to_hsv(rgbVal[0]/255., rgbVal[1]/255., rgbVal[2]/255.)

	#opencv's hue range is from 0 - 180, sat 0-255, val 0-255

	#used for checking detected values from previous steps
	unHSV = (360 * h, 100 * s, 100 * v)
	#print(unHSV)

	scale = 255/100
	newH = math.ceil(h * 180)
	newS = math.ceil(unHSV[1] * scale)
	newV = math.ceil(unHSV[2] * scale)

	print ("newHSV   " + str( (newH, newS, newV) ))

	#apply a mask that will only seek out this one color in the image
	if newH - 10 < 0:
		mask = cv2.inRange(hsv, (0, 100, 100), (newH+10, 255, 255))
	else:
		mask = cv2.inRange(hsv, (newH-10, 100, 100), (newH+10, 255, 255))

	res = cv2.bitwise_and(hsv,hsv, mask= mask)

	cv2.imshow('res', res)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
