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
'''

# This file contains the file parser, i.e. it converts the output of Salome to MDPA
import converter_utilities as utils

def ReadAndParseFile(file_path):
    with open(file_path,"r") as f:
        lines = f.readlines()
        # .dat header
        line = lines[0].split()
        num_nodes = int(line[0])
        # num_elems = int(line[1])
        # nodes = lines[1:num_nodes+1]
        
        nodes = {}
        for line in lines[1:num_nodes+1]:
            words = line.split()
            salome_ID = int(words[0])
            coords = [float(words[1]), float(words[2]), float(words[3])] # X, Y, Z
            nodes.update({salome_ID : coords})
        
        geom_entities = {}

        # Read Geometric Objects (Lines, Triangles, Quads, ...)
        for line in lines[num_nodes+1:]:
            words = line.split()
            salome_ID = int(words[0])
            salome_identifier = int(words[1]) # get the salome identifier
            node_list = []
            for i in range(2, len(words)):
                node_list.append(int(words[i]))
            
            geom_entity = utils.GeometricEntitySalome(salome_ID,
                                          salome_identifier,
                                          node_list)
            
            if salome_identifier not in geom_entities: # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                geom_entities[salome_identifier] = []

            geom_entities[salome_identifier].append(geom_entity)

        return nodes, geom_entities
