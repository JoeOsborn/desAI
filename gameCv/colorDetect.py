from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import utils
import cv2

#
foundColors = []

image = cv2.imread("./images/image.png",cv2.IMREAD_COLOR)

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

# show our colors
"""
plt.figure()
plt.axis("off")
plt.imshow(bar)
plt.show()
"""
#
# Go through the colors and blob detect
# int(round(x))
#
for datcolor in zip(clt.cluster_centers_):

    #for tuple in datcolor[0]:

    actualTuple = ( int(round(datcolor[0][0])), int(round(datcolor[0][1])), int(round(datcolor[0][2])) )

    foundColors.append(actualTuple)

print(foundColors)
