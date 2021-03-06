'''
Created on Dec 22, 2016

@author: safdar
'''
from utils.plotter import Image
from utils.plotter import Graph

class Operation(object):
    # Parameters
    IsPlotting = 'ToPlot'
    
    # Data keys:
    Upstream = 'UpstreamOutputs'
    Downstream = 'DownstreamOutputs'
    
    # Data items:
    Original = 'Original'
    
    def __init__(self, options):
        self.__options__ = options
        self.__successor__ = None

    def name(self):
        return self.__class__.__name__
    
    def setdata(self, data, key, value):
        data[self.name()][key] = value

    def getdata(self, data, key, klass=None):
        if klass is None:
            return data[self.name()][key]
        else:
            return data.get(klass.__name__, {}).get(key, None)

    def hasdata(self, data, key, section=None):
        if not data is None:
            if section is None:
                return key in data[self.name()]
            else:
                return key in data[section]
        return False

    def process(self, original, latest, data, frame):
        # Prepare data space for this object:
        if not self.name() in data:
            data[self.name()] = {}
        
        # Upstream:
        upstream = self.__processupstream__(original, latest, data, frame)
        data[self.name()][self.Upstream] = upstream.copy() if not upstream is None else None 
        if not self.__successor__ == None:
            upstream = self.__successor__.process(original, upstream, data, frame)

        # Downstream:
        downstream = self.__processdownstream__(original, upstream, data, frame)
        data[self.name()][self.Downstream] = downstream.copy() if not downstream is None else None
        return downstream

    def setsuccessor(self, successor):
        self.__successor__ = successor

    def __processupstream__(self,original, latest, data, frame):
        return latest

    def __processdownstream__(self, original, latest, data, frame):
        return latest

    def getparam(self, paramname):
        return self.__options__[paramname]
    
    def getintparam(self, paramname):
        return int(self.getparam(paramname)) 
    
    def getboolparam(self, paramname):
        return bool(self.getparam(paramname)) 

    def getfloatparam(self, paramname):
        return float(self.getparam(paramname)) 

    def gettupleparam(self, paramname):
        raise "Not implemented" # Need to use a regular expression to parse '( .. , .. )'
        
    def getinttupleparam(self, paramname):
        raise "Not implemented" # Need to use a regular expression to parse '( .. , .. )'

    def getfloattupleparam(self, paramname):
        raise "Not implemented"

    def isplotting(self):
        return bool(self.__options__[self.IsPlotting])

    def __plot__(self, frame, plottable, toplot=True):
        if self.isplotting():
            if toplot:
                frame.add(plottable)

# class Canny(Operation):
#     def __init__(self, params):
#         raise "Not implemented"
# 
# class Hough(Operation):
#     def __init__(self, params):
#         raise "Not implemented"

# class Selector(object):
#     def __init__(self, params):
#         raise "Not implemented"


#self.__options__ = {setting[0]:setting[1] for setting in [option.split('=', 1) for option in optionstring.split(';')]}

