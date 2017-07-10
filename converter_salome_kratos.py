'''
  ___   _   _    ___  __  __ ___    _  __         _             ___                     _           
 / __| /_\ | |  / _ \|  \/  | __|__| |/ /_ _ __ _| |_ ___ ___  / __|___ _ ___ _____ _ _| |_ ___ _ _ 
 \__ \/ _ \| |_| (_) | |\/| | _|___| ' <| '_/ _` |  _/ _ (_-< | (__/ _ \ ' \ V / -_) '_|  _/ -_) '_|
 |___/_/ \_\____\___/|_|  |_|___|  |_|\_\_| \__,_|\__\___/__/  \___\___/_||_\_/\___|_|  \__\___|_|  


Salome to Kratos Converter
Converts *.dat files that contain mesh information to *.mdpa file to be used as input for Kratos Multiphysics.
Author: Philipp Bucher
Chair of Structural Analysis
June 2017
Intended for non-commercial use in research

Prerequisites: tkinter
Works only with Python 3

Usage: Execute this file with Python 3

File Structure:
converter_salome_kratos.py  ### Main File
    converter_gui.py        ### GUI related Functionalities
    converter_utilities.py  ### Auxilliary Functions
'''

# Python imports
import tkinter
import logging

# Project imports
import converter_utilities as utils
import converter_gui as gui


def main():
    logging.info("Starting Converter")
    utils.PrintLogo()
    model_part = utils.MainModelPart()
    root = tkinter.Tk()
    gui.GUIObject(root, model_part)
    root.mainloop()  


if __name__ == '__main__':
    main()  
