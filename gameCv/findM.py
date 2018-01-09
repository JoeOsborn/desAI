#Adapted example from https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_template_matching/py_template_matching.html
#finds mario

import cv2
import numpy as np
from matplotlib import pyplot as plt

#load an image exported from libadapter, with mario in...
img = cv2.imread('../libAdapter/images/240.bmp',0)

#get image height and width
img_h, img_w = img.shape[::-1]

#output the dimension sizes
print("height of the input image : " + img_h)
print("width of the input image : " + img_w)

#make a reference to the screenshot
img2 = img.copy()

#load mario sprite to read
template = cv2.imread('./templates/mario.png',0)

#get size of mario image
temp_w, temp_h = template.shape[::-1]

# All the 6 methods for comparison in a list
methods = ['cv2.TM_SQDIFF_NORMED']

img = img2.copy()

#use this message of image recognition
method = cv2.TM_SQDIFF_NORMED

# Apply template Matching
res = cv2.matchTemplate(img,template,method)

min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

# If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
    top_left = min_loc
else:
    top_left = max_loc
bottom_right = (top_left[0] + temp_w, top_left[1] + temp_h)

cv2.rectangle(img,top_left, bottom_right, 255, 2)

plt.subplot(121),plt.imshow(res,cmap = 'gray')
plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
plt.subplot(122),plt.imshow(img,cmap = 'gray')
plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
plt.suptitle('cv2.TM_SQDIFF_NORMED')

plt.show()
