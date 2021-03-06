'''
Created on Jan 19, 2017

@author: safdar
'''
import matplotlib
from utils.utilities import getallpathsunder
from random import shuffle
from extractors.featurecombiner import FeatureCombiner
matplotlib.use('TKAgg')
from matplotlib.pyplot import get_current_fig_manager
from utils.plotter import Illustrator, Image, Graph
import cv2
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
import argparse
import json
from sklearn.preprocessing import StandardScaler
from operations.vehicledetection.vehiclefinder import VehicleFinder
from extractors.helper import getextractors
from extractors.hogextractor import HogExtractor
from extractors.spatialbinner import SpatialBinner
from extractors.colorhistogram import ColorHistogram
import numpy as np

if __name__ == '__main__':
    print ("###############################################")
    print ("#              FEATURE EXPLORER               #")
    print ("###############################################")

    parser = argparse.ArgumentParser(description='Object Classifier')
    parser.add_argument('-v', dest='vehicledir',    required=True, type=str, help='Path to folder containing vehicle images.')
    parser.add_argument('-n', dest='nonvehicledir',    required=True, type=str, help='Path to folder containing non-vehicle images.')
    parser.add_argument('-c', dest='configfile',    required=True, type=str, help='Path to configuration file (.json).')
    args = parser.parse_args()
    
    # Collect the image file names:
    print ("Gathering data...")
    cars = getallpathsunder(args.vehicledir)
    shuffle(cars)
    print ("Number of car images found: \t{}".format(len(cars)))
    assert len(cars)>0, "There should be at least one vehicle image to process. Found 0."
    notcars = getallpathsunder(args.nonvehicledir)
    shuffle(notcars)
    print ("Number of non-car images found: \t{}".format(len(notcars)))
    assert len(notcars)>0, "There should be at least one non-vehicle image to process. Found 0."
    
    count = min(len(cars), len(notcars))
    zipped = zip(cars[:count], notcars[:count])
    
    print ("Loading extractors...")
    config = json.load(open(args.configfile))
    extractorsequence = config[VehicleFinder.__name__][VehicleFinder.FeatureExtractors]
    extractors = getextractors(extractorsequence)
    combiner = FeatureCombiner(extractors)
    
    print ("Performing extraction...")
    illustrator = Illustrator(True)
    for i, (carfile, notcarfile) in enumerate(zipped):
        car = mpimg.imread(carfile)
        notcar = mpimg.imread(notcarfile)
        frame = illustrator.nextframe(i)
        frame.newsection("Car")
        frame.newsection("Not-Car")
        frame.add(Image("Car", car, None), index=0)
        frame.add(Image("Not-Car", notcar, None), index=1)
        for (extractor,config) in zip(extractors, extractorsequence):
            if type(extractor) is HogExtractor:
                car_features, car_hogimage = extractor.extract(car, visualize=True)
                frame.add(Image("Hog Image", car_hogimage, None), index=0)
                frame.add(Graph("Hog Vector", None, car_features, None, None), index=0)
                notcar_features, notcar_hogimage = extractor.extract(notcar, visualize=True)
                frame.add(Image("Hog Image", notcar_hogimage, None), index=1)
                frame.add(Graph("Hog Vector", None, notcar_features, None, None), index=1)
            elif type(extractor) is SpatialBinner or type(extractor) is ColorHistogram:
                car_features = extractor.extract(car)
                frame.add(Graph("{}".format(extractor.__class__.__name__), None, car_features, None, None), index=0)
                notcar_features = extractor.extract(notcar)
                frame.add(Graph("{}".format(extractor.__class__.__name__), None, notcar_features, None, None), index=1)
            else:
                raise "Debugger is not aware of the extractor type: {}".format(extractor)
        # Finally, graph the entire feature vector:
        carvector = combiner.extract(car)
        frame.add(Graph("Total Vector", None, carvector, None, None), index=0)
        notcarvector = combiner.extract(notcar)
        frame.add(Graph("Total Vector", None, notcarvector, None, None), index=1)
        frame.render()

    wm = plt.get_current_fig_manager() 
    wm.window.attributes('-topmost', 1)
    wm.window.attributes('-topmost', 0)
    plt.pause(100)