#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().system('pip install opencv-python')


# In[2]:


#### PACKAGES ####
import cv2
import os
import pandas as pd
import numpy as np
import random as r
from matplotlib import pyplot as plt
from scipy import stats
import importlib
import sys
import math


# In[3]:





### FUNCTIONS ###

# Does whole contour workflow in a function 
# Currently have erosion commented out because it has not proved useful
# PARAMETERS: cv2 img, er_iter = erosion iterations, dil_iter = dilation iterations
# RETURNS: contours and hierarchy
def get_contours(img, er_iter=1, dil_iter=24):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) # grayscale
    _,thresh = cv2.threshold(gray,140, 255,cv2.THRESH_BINARY_INV) # threshold
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
    # eroded = cv2.erode(thresh, kernel, iterations=er_iter) # erosion
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    dilated = cv2.dilate(thresh,kernel,iterations = dil_iter) # dilate
    contours, hierarchy = cv2.findContours(dilated,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)

    return contours, hierarchy

# constructed a dataframe from contours and hierarchy objects
# PARAMETERS: cv2 image, contours, hierarchy, round is automatically set based on workflow
# crop_round2 function will call this function again with round=2
# RETURNS: contour dataframe
def contour_df(img, cl, hr, round=1):
    c_list = []
    img_height, img_width,_ = img.shape
    img_area = img_height * img_width
    
    for i, c in enumerate(cl):
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cont_x,cont_y,cont_width,cont_height = cv2.boundingRect(box)
        cont_area = cv2.contourArea(c)
        cont_wh_ratio = cont_width/cont_height #ratio of width to height
       
        if round == 1:
            # remove particles
            if ((cont_wh_ratio > 0.9) and (cont_wh_ratio < 1.5) and (cont_area < (img_area*0.1))):
                # print(f"contour {i} was a particle")
                continue
            
            # removes watermark 
            elif (i == 0 or i == 1) and (cont_area < img_area * 0.1):
                # print(f"contour {i} was a watermark ")
                continue
            
            # removes items too close to the edges
            elif (((cont_x < img_width * 0.01) or (cont_x > img_width *0.99)) and (cont_area < img_area*0.2)):
                # print(f"contour {i} was too far into the sides")
                continue 
            
            # remove shadows from scans
            elif ((cont_x > img_width *0.97) and (cont_wh_ratio < 0.75)):
                continue
            
            else:
                c_list.append([i, cont_width,cont_height,cont_x,cont_y, cont_area, cont_wh_ratio])
        else:
            if ((cont_y > img_height*0.975) or (cont_y < img_height*0.025)) and (cont_area < img_area * 0.1):
                continue
            else:
                c_list.append([i, cont_width,cont_height,cont_x,cont_y, cont_area, cont_wh_ratio])

    
        # if ((cont_y > img_height*max_height) or (cont_y < img_height*min_height)) and ((cont_x > img_width*min_width) or (cont_x+cont_width < img_width*0.75)):
        #     continue
        
        # elif ((cont_x+cont_width < (img_width*min_width)) or (cont_x+cont_width > (img_width*max_width))):
        #     continue
        
        # elif ((cont_wh_ratio > 0.9) and (cont_wh_ratio < 1.1) and (cont_area < (img_area*0.2))):
        #     continue
        
    c_df = pd.DataFrame(c_list, columns=["index","width", "height", "x", "y", "area", "wh_ratio"])
    c_df['is_child'] = c_df['index'].apply(lambda i: 0 if hr[0][i][3] == -1 else 1)
    c_df['parent_contour'] = c_df['index'].apply(lambda i: hr[0][i][3] if hr[0][i][3] != -1 else -1)

    return c_df

# finds main bounding box from image
# PARAMETERS: cv2 image, contour dataframe, x_buffer = x-axis buffer, 
#             y_buffer = y-axis buffer, round (automatically set)
# RETURNS: x1 = minimum x-coordinate, x2 = maximum x-coordinate
#          y1 = minimum y-coordinate, y2 = maximum y-coordinate
def main_bbox(image, c_df, x_buffer=20, y_buffer=5, round=1):
        
    if len(c_df) == 1:
        min_x = c_df['x'][0]
        max_x = c_df['x'][0] + c_df['width'][0]
        min_y = c_df['y'][0]
        max_y = c_df['y'][0] + c_df['height'][0]
    
    else:
        largest_contour = c_df[c_df.area == max(c_df['area'])].head(1)# .head() is used to prevent having more than one result
        x_width = largest_contour.width  # creates x-value boundaries based on the dimension of largest contour
        min_x = int(largest_contour.x)
        max_x = int(min_x + x_width)

        # finds contours with smallest and largest y-value
        # y_vals = np.array(c_df['y'])
        # highest_contour = c_df[c_df['y'] == min(y_vals)]
        # min_y = int(highest_contour['y'] + lowest_contour['height'])
        # lowest_contour = c_df[c_df['y'] == max(y_vals)]
        # max_y = int(lowest_contour['y'] + lowest_contour['height'])
        
        # CHANGED THIS FROM ABOVE::
        c_df["bottom"] = c_df.y+c_df.height
        y_vals = np.array(c_df['y'])
        highest_contour = c_df[c_df['y'] == min(y_vals)].head(1)
        lowest_contour = c_df[c_df['bottom'] == c_df.bottom.max()]
        min_y = int(highest_contour['y'].values)
        max_y = int(lowest_contour['y'].values + lowest_contour['height'].values)

    if round == 1:
        # REMOVING LEFT-RIGHT MARGINALIA OR WHITE SPACE
        img_height,img_width,_ = image.shape
        
        mid_pixels = [np.mean(x) for x in np.array(image[min_y:max_y, int(min_x/2-5):int(max_x/2+5)])]
        mid_pixels.sort()
        mid_median = np.mean(mid_pixels)
        # print(mid_median)
        
        right_strip = np.array(image[min_y:max_y, max_x-5:max_x])
        right_pixels = [np.mean(x) for x in right_strip]
        right_pixels.sort()
        right_median = np.mean(right_pixels)
        # print(right_median)
        
        while (right_median > mid_median):
            max_x = max_x - 5
            right_strip = np.array(image[min_y:max_y, max_x-5:max_x])
            right_pixels = [np.mean(x) for x in right_strip]
            right_pixels.sort()
            right_median = np.mean(right_pixels)
            # print(right_median)
            
        left_pixels = [np.mean(x) for x in np.array(image[min_y:max_y, min_x:min_x+5])]
        left_pixels.sort()
        left_median = np.mean(left_pixels)
        # print(left_median)

        while (left_median > mid_median):
            min_x = min_x + 5
            left_pixels = [np.mean(x) for x in np.array(image[min_y:max_y, min_x:min_x+5])]
            left_pixels.sort()
            left_median = np.mean(left_pixels)    
            # print(left_median)

    # returns values with the buffer applied to the x values 
    return min_x-x_buffer, max_x+x_buffer, min_y, max_y

# checks cropped image if marginalia is still present
# usually only an issue with pages with left-hand marginalia 
# PARAMETERS: cropped cv2 image
# RETURNS: Boolean 
def check_for_marginalia(img):
    img_height, img_width, _ = img.shape
    try:
        left_strip = np.mean(np.array(img[:,0:int(img_width*0.05)]))
        right_strip = np.mean(np.array(img[:,img_width-int(img_width*0.05):img_width]))
        mid_strip = np.mean(np.array(img[:,int(img_width/2)-int(img_width*0.025):int(img_width/2)+int(img_width*0.025)]))
    except:
        print(f"there was an issue with {path}")
        plt.imshow(img)
        plt.show()
    # print(f"The left strip has a mean pixel value of {left_strip}")
    # print(f"The right strip has a mean pixel value of {right_strip}")
    if ((left_strip) > (right_strip)) and ((left_strip-right_strip) > (right_strip*0.03)):
        return True
    else:
        return False


# In[4]:



# If cropped image still has marginalia, a different method is called
# removes marginalia from child contours of the largest countour
# PARAMETERS: cv2 image, dil_iter = dilation iterations
# RETURNS: Mean width of the child contours -- used to change x1 value in main function     
def remove_child_marginalia(img, dil_iter=24):  
 gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) # grayscale
 _,thresh = cv2.threshold(gray,140, 255,cv2.THRESH_BINARY_INV) # threshold
 kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
 dilated = cv2.dilate(thresh,kernel,iterations = dil_iter) # dilate
 contours, hierarchy = cv2.findContours(dilated,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
 c_df = contour_df(img, contours, hierarchy, round==2)
 
 # c_df = pd.DataFrame(c_list, columns=["index","width", "height", "x", "y", "area", "wh_ratio"])
 # c_df['is_child'] = c_df['index'].apply(lambda i: 0 if hr[0][i][3] == -1 else 1)
 # c_df['parent_contour'] = c_df['index'].apply(lambda i: hr[0][i][3] if hr[0][i][3] != -1 else -1)
 
 max_area = np.max(c_df['area'])
 largest_contour = c_df[c_df['area'] == max_area].reset_index()
 
 
 children_contours = c_df[c_df['x'] == largest_contour['x'][0]]
 children_contours = children_contours[children_contours['index'] != largest_contour['index'][0]]
 
 if len(children_contours) == 0:
     # LSM: returning the image was causing an array conversion error, i've changed it to return a 0 diff so the process doesnt break
     #return img
     return 0
 else:
     mean_width= np.mean(children_contours['width'])
     return int(mean_width)

# Image goes through second round of cropping to remove watermark and header
# by taking a slice (10% of width) from left-hand side of the page 
# PARAMETERS: cv2 image, dil_iter = dilation iterations
# RETURNS: top_diff = change in minimum y-value, bottom_diff = change in maximum y-value
## values returned will adjust the y1 and y2 variables in main function

def crop_round2(img, dil_iter=24):
 strip_width = int(img.shape[1]*0.1)
 strip = img[:,0:strip_width]
 
 gray = cv2.cvtColor(strip,cv2.COLOR_BGR2GRAY) # grayscale
 _,thresh = cv2.threshold(gray,140, 255,cv2.THRESH_BINARY_INV) # threshold
 kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
 dilated = cv2.dilate(thresh,kernel,iterations = dil_iter) # dilate
 contours, hierarchy = cv2.findContours(dilated,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
 c_df = contour_df(strip, contours, hierarchy, round==2)
 
 if len(c_df) == 1:
     min_y = c_df['y'][0]
     max_y = c_df['y'][0] + c_df['height'][0]
 
 else:
     # CHANGED THIS FROM ABOVE::
     c_df["bottom"] = c_df.y+c_df.height
     y_vals = np.array(c_df['y'])
     highest_contour = c_df[c_df['y'] == min(y_vals)].head(1)
     lowest_contour = c_df[c_df['bottom'] == c_df.bottom.max()]
     min_y = int(highest_contour['y'].values)
     max_y = int(lowest_contour['y'].values + lowest_contour['height'].values)

 top_diff = min_y
 bottom_diff = img.shape[0] - max_y
 return top_diff, bottom_diff 
 
#...............................................................
# Morphological operations are a set of operations that process images based on shapes. They apply a structuring element to an input image and generate an output image. 
# The most basic morphological operations are two: Erosion and Dilation 
# Basics of Erosion: 

# Erodes away the boundaries of the foreground object
# Used to diminish the features of an image.
# Working of erosion: 
    # A kernel(a matrix of odd size(3,5,7) is convolved with the image.
    # A pixel in the original image (either 1 or 0) will be considered 1 only if all the pixels under the kernel are 1, otherwise, it is eroded (made to zero).
    # Thus all the pixels near the boundary will be discarded depending upon the size of the kernel.
# So the thickness or size of the foreground object decreases or simply the white region decreases in the image.
# Basics of dilation: Increases the object area and Used to accentuate features
# Working of dilation: 
    # A kernel(a matrix of odd size(3,5,7) is convolved with the image
    # A pixel element in the original image is ‘1’ if at least one pixel under the kernel is ‘1’.
    # It increases the white region in the image or the size of the foreground object increases 

#....................................................
# In[5]:


## Main Function is crop2csv ##
# Currently configured to show original + cropped image in sample 
# saves a csv in current folder of the image paths and the main bounding boxes
# not written to append to existing CSVs 
# PARAMETERS: pathlist = list of full image paths, dil_iter = dilation iterations, 
#                        x_buffer = buffer for x-axis, y_buffer = buffer for y-axis
def crop2csv(path_list, dil_iter=30, x_buffer=20, y_buffer=5):
    imgs_dict = {}
    imgs_df = pd.DataFrame(columns=["path", "bbox_x1", "bbox_y1", "bbox_y1", "bbox_y2"])
    
    for i, path in enumerate(path_list):
        img = cv2.imread(path)
        contours, hierarchy = get_contours(img, dil_iter)
        
        c_df = contour_df(img, contours, hierarchy)
        try:
            x1, x2, y1, y2 = main_bbox(img, c_df, x_buffer, y_buffer)
        except:
            print(f"There was an issue finding the main bounding box with {path}")
            print(f"{path} looks like this:")
            plt.imshow(img)
            plt.show()
        
        cropped = img[y1:y2, x1:x2]

        check = check_for_marginalia(cropped)
        
        if check == True:
            try:    
                diff = remove_child_marginalia(cropped, dil_iter)
                x1 = x1 + diff 
            except:
                print(f"There was an issue removing child marginalia with {path}")
                print(f"{path} looks like this:")
                plt.imshow(img)
                plt.show()
        
        cropped = img[y1:y2, x1:x2]
        try:
            top_diff, bottom_diff = crop_round2(cropped, dil_iter)
            y1 = y1+top_diff
            y2 = y2 - bottom_diff
        except:
            print(f"There was an issue in the second round of cropping with {path}")
            print(f"{path} looks like this:")
            plt.imshow(img)
            plt.show()
            imgs_df = pd.DataFrame.from_dict(imgs_dict, orient="index")
            imgs_df.to_csv("./sample_csv.csv", mode='a', index_label=False, index=False)
            return path

        imgs_dict[i] = {
            'path': path,
            'bbox_x1': x1,
            'bbox_y1': y1, 
            'bbox_x2': x2,
            'bbox_y2': y2,
                }
        print(path)
        f, ax = plt.subplots(1,2)
        ax[0].imshow(img)
        ax[1].imshow(img[y1:y2, x1:x2])
        plt.show()
    
    imgs_df = pd.DataFrame.from_dict(imgs_dict, orient="index")
    imgs_df.to_csv("./sample_csv.csv", mode='a', index_label=False, index=False)
    return ''

