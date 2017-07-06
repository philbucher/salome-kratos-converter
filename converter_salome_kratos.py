# Salome to Kratos Converter
# Converts *.dat files that contain mesh information to *.mdpa file to be used as input for Kratos Multiphysics.
# Author: Philipp Bucher
# Chair of Structural Analysis
# June 2017
# Intended for non-commercial use in research

# Prerequisites: tkinter
# Works only with Python 3


# Defining global variables
DEBUG = True

# Python imports
import tkinter

if DEBUG:
    print("Finished Python Imports")

# Importing converter files 
import converter_utilities as utils
import converter_gui as gui

if DEBUG:
    print("Finished Converter Imports")


def main():
    model_part = utils.MainModelPart()
    root = tkinter.Tk()
#    root.bind('<Control-slash>', quit)
    gui.GUIObject(root, model_part)
    root.mainloop()  


if __name__ == '__main__':
    main()  
