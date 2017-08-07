from __future__ import division
__author__ = 'jsc-nle'

import pycity_calc.data.El_grid.RealisticData as data
from numpy import sqrt


class Transformer(object):
    """
    Implementation of the class Transformer which represents a transformer used in the simulated grid.
    """

    static_transformer_id = 0

    def __init__(self, name, transformertype, busf, bust):
        self._kind = "Transformer"
        self.__Name = name
        Transformer.static_transformer_id += 1
        self.__ID = Transformer.static_transformer_id
        self.MVA_Rating = data.transformerdata[transformertype]["Sn"]
        self.Tap_Ratio = data.transformerdata[transformertype]["Tap"]
        self.Shift = data.transformerdata[transformertype]["Phaseshift"]
        self.busf = busf
        self.bust = bust
        self.Ukr = data.transformerdata[transformertype]["Ukr"]
        self.URr = data.transformerdata[transformertype]["URr"]
        self.RatedVoltage = data.transformerdata[transformertype]["Ur"]
        self.Impedence = self.Ukr * (self.RatedVoltage * self.RatedVoltage) / self.MVA_Rating
        self.Resistance = self.URr * (self.RatedVoltage * self.RatedVoltage) / self.MVA_Rating
        self.Inductance = sqrt((self.Impedence*self.Impedence)-(self.Resistance*self.Resistance))

    #   function that returns the name of the transformer object
    def getName(self):
        return self.__Name

    #   function that returns the MVA rating of the transformer object
    def getMVA(self):
        return self.MVA_Rating

    #   function that returns the tap ratio of the transformer object
    def getTap(self):
        return self.Tap_Ratio

    #   function that returns the phaseshift of the transformer object
    def getShift(self):
        return self.Shift

    #   function that returns the bus of the transformer object's primary winding
    def getBusf(self):
        return self.busf

    #   function that returns the bus of the transformer object's secondary winding
    def getBust(self):
        return self.bust

    #   function that returns the rated voltage of the transformer
    def getRatedVoltage(self):
        return self.RatedVoltage

    #   function that returns the transformer object's winding resistance
    def getResistance(self):
        return self.Resistance

    #   function that returns the transformer object's leakage inductance
    def getInductance(self):
        return self.Inductance
