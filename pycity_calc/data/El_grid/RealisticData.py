__author__ = 'mdi-dmi'

import numpy as np
"""
Here a dictionary with the technical data of different cable/overhead connection types is defined.
"""

#   technical data for cable types, derived from "Klaus Farber AG" specifications and in accordance to the study of Dipl.-Ing. Peter Esslinger
cabledata = {
                "NFA2X 4X70": {"RperKm" : 0.433, "XperKm" : (0.433/2), "BperKm":0, "MVA_A" : (np.sqrt(3)*0.400*0.205) , "MVA_B" : (np.sqrt(3)*0.400*0.205), "MVA_C" : (np.sqrt(3)*0.400*0.205)},  #R/X ~ 2
                "NAYY 4X150": {"RperKm" : 0.206, "XperKm" : (0.000256*2*np.pi*50), "BperKm":0, "MVA_A" : (np.sqrt(3)*0.400*0.275), "MVA_B" : (np.sqrt(3)*0.400*0.275), "MVA_C" : (np.sqrt(3)*0.400*0.275)},
                "NAYY 4X50": {"RperKm" : 0.641, "XperKm" : (0.00027*2*np.pi*50), "BperKm":0, "MVA_A" : (np.sqrt(3)*0.400*0.144), "MVA_B" : (np.sqrt(3)*0.400*0.144), "MVA_C" : (np.sqrt(3)*0.400*0.144)},
                "NYY 4X35": {"RperKm" : 0.524, "XperKm" : (0.000271*2*np.pi*50), "BperKm":0, "MVA_A" : (np.sqrt(3)*0.400*0.159), "MVA_B" : (np.sqrt(3)*0.400*0.159), "MVA_C" : (np.sqrt(3)*0.400*0.159)},
                "NAYY 4X185": {"RperKm" : 0.164, "XperKm" : (0.000256*2*np.pi*50), "BperKm":0, "MVA_A" : (np.sqrt(3)*0.400*0.313), "MVA_B" : (np.sqrt(3)*0.400*0.313), "MVA_C" : (np.sqrt(3)*0.400*0.313)},
            }

#   technical data for typical transformers at the medium/low voltage grid connection derived from Neplan
transformerdata = {
                    "DIN42500(Oil) 100kVA 10kV": {"Sn" : 0.100, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0175, "Ur" : 12},
                    "DIN42500(Oil) 100kVA 20kV": {"Sn" : 0.100, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0175, "Ur" : 24},
                    "DIN42500(Oil) 160kVA 10kV": {"Sn" : 0.160, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0147, "Ur" : 12},
                    "DIN42500(Oil) 160kVA 20kV": {"Sn" : 0.160, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0147, "Ur" : 24},
                    "DIN42500(Oil) 400kVA 10kV": {"Sn" : 0.400, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0115, "Ur" : 12},
                    "DIN42500(Oil) 400kVA 20kV": {"Sn" : 0.400, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0115, "Ur" : 24},
                    "DIN42500(Oil) 630kVA 10kV": {"Sn" : 0.630, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0103, "Ur" : 12},
                    "DIN42500(Oil) 630kVA 20kV": {"Sn" : 0.630, "Phaseshift" : 0, "Tap" : 1, "Ukr" : 0.04, "URr" : 0.0103, "Ur" : 24}
                    }
