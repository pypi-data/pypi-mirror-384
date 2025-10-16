import sys
import os
import ctypes

def DoMavsConfig():
    #---- Load the MAVS shared library and specify the location of the MAVS data ---------#
    install_dir = os.path.dirname(sys.modules["mavspy"].__file__)
    mavs_data_dir = ""
    if os.name == 'nt':
        mavs_libfile = install_dir + "\\lib\\mavs.dll"
        mavs_data_dir = install_dir + "\\data"
    else:
        mavs_libfile = install_dir + "/lib/libmavs.so"
        mavs_data_dir = install_dir + "/data"        
    config_file = open("mavs_config.txt", "w")
    config_file.write(mavs_data_dir+"\n")
    config_file.close()
    return mavs_libfile, mavs_data_dir

#-------------------------------------------------------------------------------------#

def GetMavsDataPath():
    mavs_libfile, mavs_data_dir = DoMavsConfig()
    return mavs_data_dir

def LoadMavsLib():
    mavs_libfile, mavs_data_dir = DoMavsConfig()
    mavs_lib = ctypes.cdll.LoadLibrary(mavs_libfile)
    return mavs_lib
