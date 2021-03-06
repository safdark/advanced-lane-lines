'''
Created on Jan 14, 2017

@author: safdar
'''
from skimage.feature._hog import hog
import cv2
import numpy as np

# blockSize=(8, 8), blockStride=(8,8),
#                             cellSize=(8,8), winSize=(64, 64), nbins=9,
#                             derivAperture=1, winSigma=4., histogramNormType=0,
#                             L2HysThreshold=2.0000000000000001e-01,
#                             gammaCorrection=0, nlevels=64, winStride=(8,8),
#                             padding=(8,8), locations=((10,20),)
                            
class HogExtractor(object):
    def __init__(self, orientations=9, space='GRAY', channel=0, size=(64,64), pixels_per_cell=8, cells_per_block=2):
        self.__orientations__ = orientations
        self.__pixels_per_cell__ = pixels_per_cell
        self.__cells_per_block__ = cells_per_block
        self.__channel__ = channel
        self.__size__ = size
        self.__color_space__ = space
        
    def extract(self, image, visualize=False):
        image = cv2.resize(image, tuple(self.__size__))
        cspace = self.__color_space__
        if cspace == 'RGB':
            image = np.copy(image)
        elif cspace == 'BGR':
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        elif cspace == 'HSV':
            image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        elif cspace == 'HLS':
            image = cv2.cvtColor(image, cv2.COLOR_RGB2HLS)
        elif cspace == 'YUV':
            image = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
        elif cspace == 'GRAY':
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        
        if cspace == 'GRAY':
            image = image
        else:
            image = image[:,:,self.__hog_channel__]

        if not visualize:
            features = hog(image,
                               orientations=self.__orientations__,
                               pixels_per_cell=(self.__pixels_per_cell__, self.__pixels_per_cell__),
                               cells_per_block=(self.__cells_per_block__, self.__cells_per_block__),
                               visualise=False, feature_vector=True)
#             features /= np.max(np.abs(features),axis=0)
            return features
        else:
            features, viz = hog(image,
                               orientations=self.__orientations__,
                               pixels_per_cell=(self.__pixels_per_cell__, self.__pixels_per_cell__),
                               cells_per_block=(self.__cells_per_block__, self.__cells_per_block__),
                               visualise=True, feature_vector=True)
#             features /= np.max(np.abs(features),axis=0)
            return features, viz
