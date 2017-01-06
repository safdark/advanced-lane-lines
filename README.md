## Advanced Lane Finding

### Overview

This was project # 4 of the Self Driving Car curriculum at Udacity. It was aimed at advanced lane detection for a front-facing camera on the car. No additional sensor inputs were utilized for this project.

The goals / steps of this project were the following:

* Compute the camera calibration matrix and distortion coefficients given a set of chessboard images.
* Apply the distortion correction to the raw image.
* Use color transforms, gradients, etc., to create a thresholded binary image.
* Apply a perspective transform to rectify binary image ("birds-eye view"). 
* Detect lane pixels and fit to find lane boundary.
* Determine curvature of the lane and vehicle position with respect to center.
* Warp the detected lane boundaries back onto the original image.
* Output visual display of the lane boundaries and numerical estimation of lane curvature and vehicle position.

### Installation

This is a python utility requiring the following libraries to be installed prior to use:
* python (>= 3)
* numpy
* scikit-learn
* OpenCV3
* matplotlib

### Execution

#### Lane Mapper Utility

This is reflected in the file lanemapper.py. It is a command line utility, invoked as follows:

```
/Users/safdar/advanced-lane-detection/src> python3.5 lanemapper.py [-h] -i INPUT [-o OUTPUT] -c [CONFIGS [CONFIGS ...]]
                     [-s SELECTOR] [-x SPEED] [-d]
```

Here's the help menu:
```
###############################################
#                 LANE FINDER                 #
###############################################
usage: lanemapper.py [-h] -i INPUT [-o OUTPUT] -c [CONFIGS [CONFIGS ...]]
                     [-s SELECTOR] [-x SPEED] [-d]

Lane Finder

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT              Path to image file, image folder, or video file.
  -o OUTPUT             Location of output (Will be treated as the same as
                        input type)
  -c [CONFIGS [CONFIGS ...]]
                        Configuration files.
  -s SELECTOR           Short circuit the pipeline to perform only specified #
                        of operations.
  -x SPEED              Speed (1 ,2, 3 etc) interpreted as 1x, 2x, 3x etc)
  -d                    Dry run. Will not save anything to disk (default:
                        false).
```


#### Image Calibration

This is reflected in the file calibrator.py. It is a command line utility, invoked as follows:

```
/Users/safdar/advanced-lane-detection/src> python3.5 calibrator.py [-h] -i INPUT -o OUTPUT [-s SIZE] [-t TEST] [-p] [-d]
```

Here's the help menu:
```
###############################################
#                 CALIBRATOR                  #
###############################################
usage: calibrator.py [-h] -i INPUT -o OUTPUT [-s SIZE] [-t TEST] [-p] [-d]

Camera Calibrator

optional arguments:
  -h, --help  show this help message and exit
  -i INPUT    Path to folder containing calibration images.
  -o OUTPUT   Location of output (Will be treated as the same as input type)
  -s SIZE     Size of the checkboard : (horizontal, vertical)
  -t TEST     Test file to undistort for visual verification.
  -p          Plot the chessboard with dots drawn (default: false).
  -d          Dry run. Will not save anything to disk (default: false).
  ```

Note the '-o' flag because the parameter used here will need to be provided in the configuration settings for the 'Lane Mapper' utility above. Please see the 'Implementation' section below for details.


### Implementation

The following sections discuss the implemented components/algorithms of this project. Each component's configuration is illustrated for further clarity. The goal of the configuration sections below was to separate the user-configurable parts from the actual code, though basic familiarity with JSON files would still be expected of any user. A look at the configuration should serve as a convenient segue into the implementation details.

#### Pipeline
This lays out the processor pipeline that each frame is put through prior to being returned to the user for lane visualization. Each processor supports a 'ToPlot' setting that dictates whether the illustrations produced by the processor are to be displayed to the user, or whether they are to be kept silent. In essence, it serves as a sort of 'silencing' flag ('0' indicating silence).

```
{

"Pipeline": [
    	"StatsWriter",
    	"Undistorter",
    	"Thresholder",
    	"PerspectiveTransformer",
    	"LaneFinder",
    	"LaneFiller"
    ],
```

There's not much to discuss here. A top level pipeline object is created, that sets up the processor pipeline after reading this configuration. Each processor listed above is expected to have a corresponding configuration 'section' further down in the JSON, as illustrated in each processor subsection below.

In essence, for the configuration above, the following pipeline is generated:
```
StatsWriter --> Undistorter --> Thresholder --> PerspectiveTransformer --> LaneFinder --> LaneFiller
                                                                                              V
                                                                                              V
StatsWriter <-- Undistorter <-- Thresholder <-- PerspectiveTransformer <-- LaneFinder <-- LaneFiller 
```
The first line is the 'upstream' pipeline, and the lower line is the 'downstream' pipeline, which is always a reversal of the upstream, based on the Chain Of Responsibility design pattern.

#### Stats Writer
This is a downstream processor that writes various pipeline stats to the final processed image. It is placed first, but actually kicks in last on the unwind of pipeline stack. The pipeline stats in this case are generated by the 'LaneFinder' component that kicks in during upstream processing of the pipeline, which is available to this processor downstream.

```
"StatsWriter": {
		"ToPlot": 0
},
```

#### Undistorter
This is an upstream and downstream processor that respectively undistorts/redistorts the image based on calibration data generated through a different utility ('calibrator.py'), which is expected to have been previously saved to the 'CalibrationFile' below. The image is UNdistorted on the upstream path, and re-distorted on the downstream path before being written out to disk.

```
"Undistorter": {
		"ToPlot": 0,
        "CalibrationFile": "config/calibration.pickle"
},
```

#### Thresholder
This is an upstream processor that is one of the most configuration-heavy components in the pipeline. It is still a W-I-P but at present supports expressions combining Color- and Sobel- based transformations of the images in any number of desired ways (including multi-level nesting). The image that is output by this processor at present is necessarily a binary image.

```
"Thresholder": {
		"ToPlot": 0,
    	"HoughFilter": {
    		"Rho": 2, "Theta": 0.0174, "Threshold": 100, "MinLineLength": 75, "MaxLineGap": 30,
	    	"LeftRadianRange": [-0.95, -0.50], "RightRadianRange": [0.50, 0.95], "DepthRangeRatio": [0.95, 0.70]
    	},
		"Term":
		{
			"ToPlot": 1,
			"Operator": "OR",
			"Negate": 0,
			"Operands": [
				{
					"ToPlot": 1,
					"Operator": "AND",
					"Negate": 0,
					"Operands": [
				    	{"Color": { "Space": "HLS", "Channel": 0, "MinMax": [50,200], "Negate": 1, "ToPlot": 1}},
				    	{"Color": { "Space": "RGB", "Channel": 0, "MinMax": [50,200], "Negate": 1, "ToPlot": 1}}
				    ]
				},
				{
					"ToPlot": 1,
					"Operator": "AND",
					"Negate": 0,
					"Operands": [
				    	{"Color": { "Space": "HLS", "Channel": 2, "MinMax": [50,200], "Negate": 0, "ToPlot": 1}},
				    	{"Color": { "Space": "RGB", "Channel": 1, "MinMax": [50,200], "Negate": 1, "ToPlot": 1}}
				    ]
				}
			]
		}
},
```

#### Perspective Transformer
This component, as is obvious, performs a perspective transformation of the input image. The 'DefaultHeadingRatios' setting is of the form '[X-Origin-Ratio, Orientation]' and in conjunction with the 'DepthRangeRatio', specifies the source points for transformation. The 'TransformRatios' setting is of the form '[XRatio, YRatio]' is used to specify the transformed points desired. The order is [UpperLeft, UpperRight, LowerLeft, LowerRight]. All points are expressed as ratios of the length of the corresponding dimension. It transforms the persective from source to destination during upstream processing, and destination back to source during the downstream pipeline.

```
"PerspectiveTransformer": {
      "ToPlot": 0,
      "DefaultHeadingRatios": [
        	[0.20, -1.2],
        	[0.86, 1.60]
      ],
      "DepthRangeRatio": [0.99, 0.63],
      "TransformRatios": [
        	[0.25, 0.0],
        	[0.75, 0.0],
        	[0.25, 1.0],
        	[0.75, 1.0]
      ]
},
```

#### Lane Finder
This upstream processor locates the lane lines in the frame. It is where all the lane detection algorithms are used. Data discovered about the current frame, and a few of the previous frames (as history), is output by this component, for subsequent processors in the pipeline to utilize. Specifically, it generates data about the left and right lane polynomial fits, the associated X/Y points observed (as well as the fit-generated X/Y points) for each lane. It also detects the position of the car relative to the center of the lane. Confidence levels are also associated with each discoved lane line, for each frame.

```
"LaneFinder": {
	"ToPlot": 0,
	"SliceRatio": 0.10,
    	"PeakWindowRatio": 0.05,
    	"PeakRangeRatios": [0.10, 0.50],
    	"LookBackFrames": 4,
    	"CameraPositionRatio": 0.50
},
```

##### Algorithm Details



###### Horizontal slicing

###### Horizontal search

###### Search bounding

###### Peak detection

###### Lookback period


#### Lane Filler
This downstream processor takes the lane and car data generated by the 'LaneFinder' and 'fills' in the lane.

```
"LaneFiller": {
	"ToPlot": 0,
	"LaneConfidenceThreshold": 0.40,
	"DriftToleranceRatio": 0.05,
	"SafeColor": [152, 251, 152],
    	"DangerColor": [255,0,0]
}
}
```
This component is also responsible for selecting which lanes to draw, based on the confidence level associated with each lane from the current frame. A threshold is utilized, called 'LaneConfidenceThreshold', that determines the minimum confidence level associated with the lane in order for it to be accepted and drawn by this component. The behavior obtained from this logic is that no lane will be drawn until *both* the left and right lanes satisfy this minimum threshold. Once that threshold is met, the component will continue using the corresponding polynomial fit of each side of the lane to paint the lane's body, until such time as the new data for either or both of the lanes satisfies the threshold, at which point it paints using the updated lane fit(s). This makes the algorithm able to adapt to situations when no new information of sufficient confidence is obtained from the LaneFinder, because in such cases, it continues to use the last high-confidence lane information. This applies to each side of the lane. So, it's possible that one side gets updated, while the other remains the same. Either way, once it starts painting the lane, there is never a period where the lane can vanish.

### Areas for Improvement & Potential Failure Scenarios:

Areas where this project could improve are discussed below, outlining scenarios where the algorithm would likel fail. I could not implement these options due to time considerations, but I might revisit them further "down the road' (pun intended).

#### Mid-Line for Left/Rigth Peak Categorization

Presently, the algorithm for searching for histogram peaks searches on each side of a vertical 'center' line that is calculated to be the midpoint of the X-dimension. There is a naive assumption here that the center of the lane is always more or less at the center of the camera. Clearly, this is a limiting assumption since the car is almost never right at the center of the screen. Furthermore, even if the car were at the center, the lanes could at times have such a short radius of curvature that the histogram peaks further down on each lane could spill over to the adjacent lane's search region causing the lane peaks to be inaccurately categorized by the search algorithm.

A simple, yet suboptimal solution, is to use the center of the lane from the previous frame instead of using the midpoint of the X-dimension, when partitioning the image into the left and right regions for searching for lane peaks. This is easiliy obtained by performing a mean of the positions of the two lanes at the bottom of the image.

A more robust solution, especially to avoid miscategorizing peaks further down on each lane, would be to calculate a polynomial fit of the midpoint of the 2 lanes (using a 2nd order polynomial in the same way as was used to fit each lane). The points for this mid-line polynomial would be obtained by averaging the peaks obtained from each slice of the frame. A confidence could be associated to this mid-line based on the lower of the confidence levels of the two lanes for that frame. Using this fitted center line would be the most accurate approach for this problem, in my view, particularly for meandering or curvy roads.

#### Dynamic identification of perspective points

Depending on the camera height relative to the road, and the contour of the road, the points used to transform the perspective for lane detection may vary. At present, a static set of points is being utilized, which assumes that both the above factors will remain static.

One option to avoid this limitation is to dynamically adjust the perspective used for the perspective transform, the goal being to (a) consistently obtain mostly parallel lane lines when scanning the transformation perspective, and (b) to advance the perspective only as far as not to include more than one curve in the transformation.


#### Using a 3rd order polynomial

Lanes that are particularly curvy or meandering may not always fit to a 2nd order polynomial. This is because the stretch of the lane over the same line of sight might include not just one curve, but two curves. In fact, in extreme circumstances, particularly when the camera is higher above the ground, multiple curves might be visible within the line of sight.

One option that was mentioned previously is to dynamically adjust the perspective used for the perspective transform, the goal being to advance the perspective only as far as not to include more than one curve in the transformation. The disadvange of this approach, as mentioned, would be that the car would have to slow down.

Another alternative, instead of shortening the perpspective, is to use a higher order polynomial to fit the discovered peaks. This would allow the car to potentially not have to slow down as much, and to also make higher confidence driving decisions.

#### Adaptive window for limiting peak searches

Presently, a static window is used to determine the bounds of the points used to detect a histogram peak, relative to the location of the peak in the slice right below the present slice, or the peak in the subsequent slice of the previous frame. Though these approaches allow a more efficient scan, it is possible to get stuck looking for a lane close to an erroneous lane or peak that was previously detected. To avoid this, it might be beneficial to increase the window size proportional to the confidence of the previously detected lane, or the confidence of the peaks obtained in the slices below. The lower the confidence, the larger the window becomes, upto a maximum size of the search region itself. The higher the confidence, the smaller the window gets, upto a minimum of the configured window size.

### Open Defects

I will get to these when time permits. Until then, am calling them out here. Please see the 'Issues' section of this github repository for further details.

* Performance of this utility is below par at the moment. Output from performance profiling suggests the culprit is the extensive use of matplotlib to illustrate the transformations/processing steps for each frame in the video. Switching off illustration speeds up performance significantly, but not sufficiently enough to ensure real-time detection during actual use on the road.

* Insufficient error checking. Since this is not a commercial use utility, emphasis was not given to ensuring producing descriptive error messages. If you choose to run this utility, but face issues, please feel free to create an 'Issue' for this project.
