'''
Created on Jan 14, 2017

@author: safdar
'''

from operations.baseoperation import Operation
from sklearn.externals import joblib
from statistics import mean
import numpy as np
import cv2
from extractors.helper import buildextractor
import os
from utils.plotter import Image
import PIL
import time
from operations.vehicledetection.entities import Candidate, Box

class VehicleFinder(Operation):
    ClassifierFile = 'ClassifierFile'
    FeatureExtractors = 'FeatureExtractors'
    SlidingWindow = 'SlidingWindow'
    class Logging(object):
        LogHits = 'LogHits'
        LogMisses = 'LogMisses'
        FrameRange = 'FrameRange'
        Frames = 'Frames'
        LogFolder = 'LogFolder'
        HitsXRange = 'HitsXRange'
        MissesXRange = 'MissesXRange'
    class SlidingWindow(object):
        DepthRangeRatio = 'DepthRangeRatio'
        CenterShiftRatio = 'CenterShiftRatio'
        SizeVariations = 'SizeVariations'
        WindowRangeRatio = 'WindowRangeRatio'
        StepRatio = 'StepRatio'
        ConfidenceThreshold = 'ConfidenceThreshold'

    # Constants:
    AllWindowColor = [152, 0, 0]
    WeakWindowColor = [200, 0, 0]
    StrongWindowColor = [255, 0, 0]

    # Outputs
    FrameCandidates = "FrameCandidates"

    def __init__(self, params):
        Operation.__init__(self, params)
        self.__classifier__ = joblib.load(params[self.ClassifierFile])
        self.__windows__ = None
        loggingcfg = params[self.Logging.__name__]
        self.__is_logging_hits__ = loggingcfg[self.Logging.LogHits]
        self.__is_logging_misses__ = loggingcfg[self.Logging.LogMisses]
        self.__log_folder__ = os.path.join(loggingcfg[self.Logging.LogFolder], time.strftime('%m-%d-%H-%M-%S'))
        self.__hits_folder__ = os.path.join(self.__log_folder__, 'Hits')
        self.__misses_folder__ = os.path.join(self.__log_folder__, 'Misses')
        self.__frames_to_log__ = loggingcfg[self.Logging.Frames]
        self.__frame_range_to_log__ = loggingcfg[self.Logging.FrameRange]
        self.__hits_x_range_to_log__ = loggingcfg[self.Logging.HitsXRange]
        assert self.__hits_x_range_to_log__ is None or len(self.__hits_x_range_to_log__) == 2
        self.__misses_x_range_to_log__ = loggingcfg[self.Logging.MissesXRange]
        assert self.__misses_x_range_to_log__ is None or len(self.__misses_x_range_to_log__) == 2
        
        if self.__is_logging_hits__:
            if not os.path.isdir(self.__hits_folder__):
                os.makedirs(self.__hits_folder__, exist_ok=True)
        if self.__is_logging_misses__:
            if not os.path.isdir(self.__misses_folder__):
                os.makedirs(self.__misses_folder__, exist_ok=True)
        
        # Feature Extractors
        extractorsequence = params[self.FeatureExtractors]
        self.__feature_extractor__ = buildextractor(extractorsequence)
        
        self.__frame_candidates__ = None

    def islogginghits(self):
        return self.__is_logging_hits__==1

    def isloggingmisses(self):
        return self.__is_logging_misses__==1

    def isframewithrange(self, frame):
        return (self.__frame_range_to_log__ is None or frame.framenumber() in range(*self.__frame_range_to_log__)) and \
               (self.__frames_to_log__ is None or frame.framenumber() in self.__frames_to_log__)

    def log(self, folder, window, i, j, frame):
        if self.isframewithrange(frame):
            windowdumpfile = os.path.join(folder, "{:04d}_{:02d}_{:02d}.png".format(frame.framenumber(), i, j))
            towrite = PIL.Image.fromarray(window)
            towrite.save(windowdumpfile)

    def isWindowMissInRange(self, boundary):
        (x1, x2, _, _) = boundary
        if self.__misses_x_range_to_log__ is not None:
            return x1 in range(*self.__misses_x_range_to_log__) and x2 in range(*self.__misses_x_range_to_log__)
        return True

    def isWindowHitInRange(self, boundary):
        (x1, x2, _, _) = boundary
        if self.__hits_x_range_to_log__ is not None:
            return x1 in range(*self.__hits_x_range_to_log__) and x2 in range(*self.__hits_x_range_to_log__)
        return True
    
    def __processupstream__(self, original, latest, data, frame):
        x_dim, y_dim, xy_avg = latest.shape[1], latest.shape[0], int(mean(latest.shape[0:2]))
        slidingwindowconfig = self.getparam(self.SlidingWindow.__name__)
        if self.__windows__ is None:
            self.__continuity_threshold__ = slidingwindowconfig[self.SlidingWindow.ConfidenceThreshold]
            self.__windows__ = self.generatewindows(slidingwindowconfig, x_dim, y_dim, xy_avg)
            self.__window_range_ratio__ = slidingwindowconfig[self.SlidingWindow.WindowRangeRatio]
            self.__window_range__ = [int(xy_avg * r) for r in self.__window_range_ratio__]

        # Perform search:
        image = np.copy(latest)
        weak_candidates = []
        strong_candidates = []
        for i, scan in enumerate(self.__windows__):
            for j, box in enumerate(scan):
                (x1, x2, y1, y2) = box.boundary()
                snapshot = image[y1:y2,x1:x2,:]
                if np.min(snapshot) == 0 and np.max(snapshot)==0:
                    continue
                window = snapshot.astype(np.float32)
                if np.max(window) == 0:
                    print ("Error")
                features = self.__feature_extractor__.extract(window)
                try:
                    label = self.__classifier__.predict([features])
                except ValueError:
                    print ("Error")
                    
                score = self.__classifier__.decision_function([features])[0] if "decision_function" in dir(self.__classifier__) else None
                if label == 1 or label == [1]:
                    if score is None or score > self.__continuity_threshold__:
                        strong_candidates.append(Candidate(box.center(), box.diagonal(), score))
                        if self.islogginghits() and self.isWindowHitInRange(box.boundary()):
                            self.log(self.__hits_folder__, snapshot, i, j, frame)
                    else:
                        weak_candidates.append(Candidate(box.center(), box.diagonal(), score))
                else:
                    if self.isloggingmisses() and self.isWindowMissInRange(box.boundary()):
                        self.log(self.__misses_folder__, snapshot, i, j, frame)
        self.__frame_candidates__ = strong_candidates
        self.setdata(data, self.FrameCandidates, self.__frame_candidates__)
        
        if (self.islogginghits() or self.isloggingmisses()) and self.isframewithrange(frame):
            imagedumpfile = os.path.join(self.__log_folder__, "{:04d}.png".format(frame.framenumber()))
            towrite = PIL.Image.fromarray(latest)
            towrite.save(imagedumpfile)

        if self.isplotting():
            all_windows = [x for sublist in self.__windows__ for x in sublist]
            # First show all windows being searched:
            image_all = np.zeros_like(latest)
            for scan in self.__windows__:
                for box in scan:
                    (x1,x2,y1,y2) = box.boundary()
                    cv2.rectangle(image_all, (x1,y1), (x2,y2), self.AllWindowColor, 2)
                    if box.fitted():
                        cv2.putText(image_all,"~x~x~", (x1,y1), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, self.WeakWindowColor, 1)
                    
            # Then show all windows that were weak candidates:            
            image_weak = np.zeros_like(latest)
            for candidate in weak_candidates:
                (x1,x2,y1,y2) = candidate.boundary()
                cv2.rectangle(image_weak, (x1,y1), (x2,y2), self.WeakWindowColor, 2)
                if candidate.score() is not None:
                    cv2.putText(image_weak,"{:.2f}".format(candidate.score()), (x1,y1), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, self.WeakWindowColor, 1)

            # Then show all windows that were strong candidates:
            image_strong = np.copy(latest)
            for candidate in strong_candidates:
                (x1,x2,y1,y2) = candidate.boundary()
                cv2.rectangle(image_strong, (x1,y1), (x2,y2), self.StrongWindowColor, 4)
                if candidate.score() is not None:
                    cv2.putText(image_strong,"{:.2f}".format(candidate.score()), (x1,y1), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, self.StrongWindowColor, 1)

            # Now superimpose all 3 frames onto the latest color frame:
            todraw = cv2.addWeighted(image_strong, 1, image_all, 0.2, 0)
            todraw = cv2.addWeighted(todraw, 1, image_weak, 0.5, 0)
#             todraw = cv2.addWeighted(todraw, 1, image_strong, 1, 0)
            self.__plot__(frame, Image("Vehicle Search & Hits (All/Weak/Strong = {}/{}/{})".format(
                                        len(all_windows),
                                        len(weak_candidates), 
                                        len(strong_candidates)),
                                       todraw, None))

            # Try group rectangles:
#             cons = np.copy(latest)
#             if len(self.__frame_candidates__)>0:
#                 grouped, weights = cv2.groupRectangles(list(zip(*self.__frame_candidates__))[0], 1, .2)
#                 for ((x1,x2,y1,y2), weight) in zip(grouped, weights):
#                     cv2.rectangle(cons, (x1,y1), (x2,y2), self.StrongWindowColor, 3)
#                     cv2.putText(cons,"{}".format(weight), (x1,y1), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, self.StrongWindowColor, 1)
#             self.__plot__(frame, Image("Grouped", cons, None))
            
        return latest

    def generatewindows(self, cfg, x_dim, y_dim, xy_avg):
        shift = cfg[self.SlidingWindow.CenterShiftRatio] * x_dim
        depth_range_ratio = sorted(cfg[self.SlidingWindow.DepthRangeRatio], reverse=True)
        horizon = min([int(y_dim * r) for r in depth_range_ratio])
        print ("Horizon is at depth: {}".format(horizon))
        window_range_ratio = cfg[self.SlidingWindow.WindowRangeRatio]
        window_range = [int(xy_avg * r) for r in window_range_ratio]
        print ("Window range: {}".format(window_range))
        size_variations = cfg[self.SlidingWindow.SizeVariations]
        grow_rate = int(np.absolute(window_range[1]-window_range[0])/(size_variations))
        print ("Window grow rate (each side): {}".format(grow_rate))
        slide_ratio = cfg[self.SlidingWindow.StepRatio]
        center = (int((x_dim / 2) + shift), horizon)
        print ("Center of vision: {}".format(center))
        
        windows = []
        for i in range(size_variations):
            print ("Scan # {}".format(i))
            windows.append([])
            scanwidth = int(x_dim/2)
            print ("\tScan width: {}".format(scanwidth))
            boxwidth = window_range[0] + (i * grow_rate)
            print ("\tBox width: {}".format(boxwidth))
            center_box = Box(center, boxwidth)
            if center_box is None:
                print ("\tCenter box (OUTSIDE BOUNDS): {}".format(center_box))
                continue
            print ("\tCenter box: {}".format(center_box))
            windows[i].append(center_box)
            shifts_per_box = int(1 / slide_ratio)
            boxshift = int(boxwidth * slide_ratio)
            print ("\t\tBox shift: {}".format(boxshift))
            numboxes = int(scanwidth / boxwidth) # Boxes each side of the center box
            print ("\t\tNum boxes: {}".format(numboxes))
            # Each box on left + right sides of center:
            print ("\t\t\tShifts Per Box: {}".format(shifts_per_box))
            for j in range(1, numboxes + 1):
                print ("\t\t\tShifted Boxes # ({})".format('~'*j))
                for k in range(0, shifts_per_box):
                    leftcenter = (center[0] - (j * boxwidth) - (k * boxshift), center[1])
                    if not leftcenter[0] in range(0,x_dim) or not leftcenter[1] in range(0,y_dim):
                        continue
                    left_box = Box(leftcenter, boxwidth, bounds=((0,x_dim),(0,y_dim)))
                    rightcenter = (center[0] + (j * boxwidth) + (k * boxshift), center[1])
                    if not rightcenter[0] in range(0,x_dim) or not rightcenter[1] in range(0,y_dim):
                        continue
                    right_box = Box(rightcenter, boxwidth)
                    windows[i].append(left_box)
                    windows[i].append(right_box)
                    print ("\t\t\t\tShift # {}: <--{} {} {}-->".format(k, left_box, '~'*(k+1), right_box))
            print ("\tTotal boxes in scan: {}".format(len(windows[i])))
        return windows

