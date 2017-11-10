'''
  ___   _   _    ___  __  __ ___    _  _____    _ _____ ___  ___  
 / __| /_\ | |  / _ \|  \/  | __|__| |/ / _ \  /_\_   _/ _ \/ __| 
 \__ \/ _ \| |_| (_) | |\/| | _|___| ' <|   / / _ \| || (_) \__ \ 
 |___/_/ \_\____\___/|_|  |_|___|  |_|\_\_|_\/_/ \_\_| \___/|___/ 
  / __|___ _ ___ _____ _ _| |_ ___ _ _                            
 | (__/ _ \ ' \ V / -_) '_|  _/ -_) '_|                           
  \___\___/_||_\_/\___|_|  \__\___|_|                             
                                                                  

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
    converter_gui_utilities.py  ### Auxilliary Functions for GUI functions

    kratos_utilities.py  ### Kratos Related Utilities, also used in other Projects
    global_utilities.py  ### Global Utilities, also used in other Projects
'''

# Python imports
import tkinter
import logging

# Project imports
import converter_gui as gui
import converter_gui_utilities as utils
import kratos_utilities as kratos_utils


def main():
    logging.info("Starting Converter")
    utils.PrintLogo()
    model_part = kratos_utils.MainModelPart()
    root = tkinter.Tk()
    gui.GUIObject(root, model_part)
    root.mainloop()  


if __name__ == '__main__':
    main()  
