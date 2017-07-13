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
'''

### TODO list ###
# add geometrical information to the Kratos entities
# Nodal Elements => ask Vicente
# sort selection window by entities (nodes, elements, conditions)
# initial directories

DEBUG = False          # Set this Variable to "True" for debugging
READABLE_MDPA = True  # Use this to get a nicely formatted mdpa file. Works in most cases, but files are larger (~20%) and mdpa writing takes slightly more time
VERSION = 1.0

# Python imports
import sys
import tkinter as tk
from tkinter import filedialog
from os.path import splitext, basename, isfile
import time
import logging

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

conv_scheme_file_ending = ".conv.scheme.json"
conv_project_file_ending = ".conv.proj.json"

SALOME_IDENTIFIERS = {
        102 : "Line",
        203 : "Triangle",
        204 : "Quadrilateral",
        304 : "Tetrahedral",
        308 : "Hexahedral"        
}


ELEMENTS = {
  "0_Generic" : {
      2 : [ "Element2D2N",

          ],
      3 : [ "Element2D3N",
            "Element3D3N"
          ],
      4 : [ "Element3D4N"
          ]
  },
  "1_Fluid" : {
      2 : [
          ],
      3 : [ "Element2D3N"
          ],
      4 : [ "Element3D4N"
          ]
  },
  "2_Structure" : {
      1 : [ "NodalConcentratedElement2D1N",
            "NodalConcentratedDampedElement2D1N",
            "NodalConcentratedElement3D1N",
            "NodalConcentratedDampedElement3D1N"
          ],
      2 : [ "TrussElement3D2N",
            "TrussLinearElement3D2N",
            "CrBeamElement3D2N",
            "CrLinearBeamElement3D2N"
          ],
      3 : [ "PreStressMembraneElement3D3N",
            "ShellThinElementCorotational3D3N",
            "ShellThickElementCorotational3D3N"
          ],
      4 : [ "PreStressMembraneElement3D4N",
            "ShellThinElementCorotational3D4N",
            "ShellThickElementCorotational3D4N"
          ],
      8 : ["SmallDisplacementElement3D8N"

          ]
  }
}
  

CONDITIONS = {
  "0_Generic" : {
      1 : [ "PointCondition2D1N",
            "PointCondition3D1N"
          ],
      2 : [ "LineCondition2D2N",
            "LineCondition3D2N",
          ],
      3 : [ "SurfaceCondition3D3N"            
          ],
      4 : [ "SurfaceCondition3D4N"
          ]
  },
  "1_Fluid" : {
      2 : [ "WallCondition2D2N"
          ],
      3 : [ "WallCondition3D3N"
          ],
      4 : [
          ]
  },
  "2_Structure" : {
      2 : [
          ],
      3 : [
          ],
      4 : [ "SurfaceLoadCondition3D4N",
          ]
  }
}


def ReadAndParseFile(file_path):
    valid_file = True
    nodes = {}
    geom_entities = {}

    try:
        with open(file_path,"r") as f:
            lines = f.readlines()
            # .dat header
            line = lines[0].split()
            num_nodes = int(line[0])
            # num_elems = int(line[1])
            # nodes = lines[1:num_nodes+1]

            if num_nodes == 0:
                logging.error('No nodes in file \"{}\"'.format(file_path))
                valid_file = False
            
            if valid_file:
                
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
                    
                    geom_entity = GeometricEntitySalome(salome_ID,
                                                salome_identifier,
                                                node_list)
                    
                    if salome_identifier not in geom_entities: # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                        geom_entities[salome_identifier] = []

                    geom_entities[salome_identifier].append(geom_entity)
    except:
        logging.error('Reading File \"{}\" failed!'.format(file_path))
        valid_file = False

    return valid_file, nodes, geom_entities

# Functions related to Window
def BringWindowToFront(window):
    window.lift()
    window.attributes('-topmost', 1)
    window.focus_force() # Forcing the focus on the window, seems to be not the nicest solution but it works
    window.after_idle(window.attributes,'-topmost',False) # TODO check under Windows


def MaximizeWindow(window):
    # TODO check which one works for MacOS
    if (GetOS() == "linux"):
        window.attributes('-zoomed', True)
    else:   
        window.state('zoomed')


def CloseWindow(window, master):
    window.destroy()
    if master is not None:
        master.SetChildWindowIsClosed()


# Functions related to Files
def GetFilePathOpen(FileType):
    file_path = ""
    valid_file = False
    if (FileType == "dat"):
        file_path = tk.filedialog.askopenfilename(title="Open file",filetypes=[("salome mesh","*.dat")])
    elif (FileType == conv_project_file_ending):
        file_path = tk.filedialog.askopenfilename(title="Open file",filetypes=[("converter files","*" + conv_project_file_ending)])
    elif (FileType == conv_scheme_file_ending):
        file_path = tk.filedialog.askopenfilename(title="Open file",filetypes=[("converter files","*" + conv_scheme_file_ending)])
        # file_path = tk.filedialog.askopenfilename(initialdir='/home/philippb', title="Open file",filetypes=[("converter files","*" + conv_file_ending)])
    else:
        print("Unsupported FileType") # TODO make messagebox
    
    if file_path != "":
        valid_file = FileExists(file_path)
        logging.debug("File Path: " + file_path)
    
    return file_path, valid_file


def FileExists(file_path):
    return isfile(file_path)


def GetFilePathSave(FileType):
    file_path = ""
    if (FileType == "mdpa"):
        file_path = tk.filedialog.asksaveasfilename(title="Select file",
                                                    filetypes=[("mdpa files","*.mdpa")])
        if file_path: # check if a file path was read (i.e. if the file-selection was NOT aborted)
            if not file_path.endswith(".mdpa"):
                file_path += ".mdpa"
    else:
        print("Unsupported FileType") # TODO make messagebox

    return file_path


def GetFileName(FilePath):
    return splitext(basename(FilePath))[0]


# Other Functions
def GetGeneralInfoDict():
    general_info_dict = {}
    localtime = time.asctime( time.localtime(time.time()) )
    
    general_info_dict.update({"Version" : VERSION})
    general_info_dict.update({"Date" : localtime})
    general_info_dict.update({"OperatingSystem" : GetOS()})
    
    return general_info_dict


def GetOS():
    os_name = "unknown"

    os_platform = sys.platform

    if (os_platform.startswith("linux")):
        os_name = "linux"
    elif (os_platform == ("win32" or "cygwin")):
        os_name = "windows"
    elif (os_platform == "darwin"):
        os_name = "macos"

    return os_name


def PrintLogo():
    print('''  ___   _   _    ___  __  __ ___    _  _____    _ _____ ___  ___  
 / __| /_\ | |  / _ \|  \/  | __|__| |/ / _ \  /_\_   _/ _ \/ __| 
 \__ \/ _ \| |_| (_) | |\/| | _|___| ' <|   / / _ \| || (_) \__ \ 
 |___/_/ \_\____\___/|_|  |_|___|  |_|\_\_|_\/_/ \_\_| \___/|___/ 
  / __|___ _ ___ _____ _ _| |_ ___ _ _                            
 | (__/ _ \ ' \ V / -_) '_|  _/ -_) '_|                           
  \___\___/_||_\_/\___|_|  \__\___|_|  ''')
    print("   VERSION", VERSION)


def GetEntityType(SalomeIdentifier):
    post_string = "Unknown"
    if SalomeIdentifier in SALOME_IDENTIFIERS:
        post_string = SALOME_IDENTIFIERS[SalomeIdentifier]

    return str(SalomeIdentifier) + "_" + post_string


def GetNumberOfNodes(String):
    return int(String[1:3])


def GetTreeItem(tree, event):
    return tree.identify('item', event.x, event.y)


def DictKeyToInt(dictionary):
    if not isinstance(dictionary, dict):
        raise Exception("Input is not a dict!")

    dictionary_int = {}

    for key, val in dictionary.items():
        dictionary_int.update({ int(key) : val })

    return dictionary_int


def CorrectMeshDict(mesh_dict):
    # This function converts some keys from str back to int (caused by loading json files)
    corrected_mesh_dict = {}
    for key, val in mesh_dict.items():
        if key == "entity_creation":
            corrected_mesh_dict.update({"entity_creation" : DictKeyToInt(mesh_dict["entity_creation"])})
        else:
            corrected_mesh_dict.update({key : val})
    
    return corrected_mesh_dict
  

def CorrectNodeListOrder(salome_node_list, salome_identifier):
    # This function corrects the order in the node list because for
    # some elements the nodal order is different btw SALOME and Kratos
    if salome_identifier == 308: # Hexahedral
        salome_node_list[1], salome_node_list[3] = salome_node_list[3], salome_node_list[1]
        salome_node_list[5], salome_node_list[7] = salome_node_list[7], salome_node_list[5]

    return salome_node_list


def GetDictFromTree(tree):
    dictionary = {"entity_creation" : {}}

    for child in tree.get_children():
        if (tree.tag_has("Element", child)):
            item_values = tree.item(child,"values")
            element_name = item_values[0]
            property_ID = item_values[1]
            salome_identifier = int(item_values[2].split("_")[0])
            
            AddEntryToDict(dictionary, salome_identifier, "Element", element_name, property_ID)

        if (tree.tag_has("Condition", child)):
            item_values = tree.item(child,"values")
            condition_name = item_values[0]
            property_ID = item_values[1]
            salome_identifier = int(item_values[2].split("_")[0])
            
            AddEntryToDict(dictionary, salome_identifier, "Condition", condition_name, property_ID)
    
    return dictionary
    
    
def AddEntryToDict(json_dict, salome_identifier, entity_type, entity_name, property_ID):
    if salome_identifier not in json_dict["entity_creation"]:
        json_dict["entity_creation"][salome_identifier] = {}
        
    if entity_type not in json_dict["entity_creation"][salome_identifier]:
        json_dict["entity_creation"][salome_identifier][entity_type] = {}
            
    json_dict["entity_creation"][salome_identifier][entity_type].update({entity_name: property_ID})




class GeometricEntitySalome:
    def __init__(self, salome_ID, salome_identifier, node_list):
        self.salome_ID = salome_ID
        self.salome_identifier = salome_identifier
        self._SetNodeList(node_list)

    def _SetNodeList(self, salome_node_list):
        CorrectNodeListOrder(salome_node_list, self.salome_identifier)
        self.node_list = salome_node_list
        
    def GetNodeList(self):
        return self.node_list

    def Serialize(self):
        serialized_entity = [self.salome_ID, self.salome_identifier, self.node_list]
        return serialized_entity
        
        
    
class GeometricalObject:
    def __init__(self, salome_entity, name, property_ID):
        self.origin_entity = salome_entity
        self.name = name        
        self.new_ID = -1
        self.property_ID = property_ID
    
    def GetID(self):
        if self.new_ID == -1:
            raise Exception("No new ID has been assiged")
        return self.new_ID
    
    def GetWriteLine(self, ID, format_str, space):
        self.new_ID = ID
        # "0" is the Property Placeholder
        line = format_str.format(str(self.new_ID), str(self.property_ID))

        for node in self.origin_entity.GetNodeList():
            line += space + str(node)
        
        return line
        
        
    
class Element(GeometricalObject):
    def __init__(self, salome_entity, name, property_ID):
        super().__init__(salome_entity, name, property_ID)
        
        
        
class Condition(GeometricalObject):
    def __init__(self, salome_entity, name, property_ID):
        super().__init__(salome_entity, name, property_ID)
        
        
        
class MainModelPart:
    def __init__(self):
        self._Initialize()
        
    def _Initialize(self):
        self.sub_model_parts = {}
        self._InitializeMesh()
        self.mesh_read = False
        self.precision = 12 # Same as in Kratos ("/kratos/includes/gid_io.h")
        self.num_spaces = 3 # number of spaces in mdpa btw numbers
        
        
    def _InitializeMesh(self):
        self.nodes = {} # ID : [Coord_X, Coord_Y, Coord_Z]
        self.elements = {} # Name : [List]
        self.conditions = {} # Name : [List]
        self.node_counter = 1
        self.element_counter = 1
        self.condition_counter = 1
        # Variables for optimizing the size of the mdpa file
        self.max_node_coord_x = 0
        self.max_node_coord_y = 0
        self.max_node_coord_z = 0
    
    
    def GetMeshRead(self):
        return self.mesh_read
    
    
    def GetSubModelPart(self, smp_name):
        if smp_name in self.sub_model_parts:
            return self.sub_model_parts[smp_name]
    

    def Reset(self):
        self._Initialize()
    
    
    def FileExists(self, file_name):
        # TODO check against path, name, or both? Or even allow it with a warning?
        # TODO modify such that it checks against the file_name and not the smp_name
        file_exists = False
        
        if file_name in self.sub_model_parts.keys():
            file_exists = True
            
        return file_exists
    
    
    def AssembleMeshInfoDict(self):
        mp_dict = {}
        
        for smp_name in self.sub_model_parts.keys():
            mp_dict[smp_name] = self.sub_model_parts[smp_name].GetMeshInfoDict()
        
        return mp_dict
        
        
    def AddMesh(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        smp_name = smp_info_dict["smp_name"]
        self.sub_model_parts[smp_name] = MeshSubmodelPart()
        self.sub_model_parts[smp_name].FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)
        
        self.mesh_read = True

    def UpdateMesh(self, old_smp_name, smp_info_dict, mesh_dict):
        new_smp_name = smp_info_dict["smp_name"]
        self.sub_model_parts[new_smp_name] = self.sub_model_parts.pop(old_smp_name) # Update the key
        
        self.sub_model_parts[new_smp_name].Update(smp_info_dict, mesh_dict)

    
    def RemoveSubmodelPart(self, name_smp):
        self.sub_model_parts.pop(name_smp, None)

        self._Assemble() # Update the ModelPart


    def Serialize(self):
        # This function serializes the ModelPart such that it can be saved in a json file
        logging.debug("Serializing ModelPart")
        serialized_dict = {}
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            serialized_dict.update(smp.Serialize())

        return serialized_dict

        
    def Deserialize(self, serialized_dict):
        # This function constructs a modelpart from a serialized dictionary
        self.Reset()

        for smp_name in sorted(serialized_dict.keys()):
            if smp_name != "general":
                self.sub_model_parts[smp_name] = MeshSubmodelPart()
                self.sub_model_parts[smp_name].Deserialize(smp_name, serialized_dict[smp_name])
        
        self.mesh_read = True

        logging.debug("Deserialized ModelPart")


    def _Assemble(self):
        # TODO Check if this was done before! (same for the submodelparts)
        self._InitializeMesh()
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.Assemble()
            smp_nodes, smp_elements, smp_conditions = smp.GetMesh()
            self._AddNodes(smp_nodes)
            self._AddElements(smp_name, smp_elements)
            self._AddConditions(smp_name, smp_conditions)
        

    def _AddNodes(self, smp_nodes):
        for node_ID in smp_nodes.keys():
            if node_ID in self.nodes.keys():
                existing_node_coords = self.nodes[node_ID]
                if existing_node_coords != smp_nodes[node_ID]:
                    raise Exception("Node with ID", node_ID, "already exists with different coordinates!")
            else:
                self.nodes[node_ID] = smp_nodes[node_ID]
                if READABLE_MDPA:
                    if smp_nodes[node_ID][0] > self.max_node_coord_x: self.max_node_coord_x = smp_nodes[node_ID][0]
                    if smp_nodes[node_ID][1] > self.max_node_coord_y: self.max_node_coord_y = smp_nodes[node_ID][1]
                    if smp_nodes[node_ID][2] > self.max_node_coord_z: self.max_node_coord_z = smp_nodes[node_ID][2]
        
        
    def _AddElements(self, smp_name, smp_elements):
        self.elements[smp_name] = smp_elements
            
            
    def _AddConditions(self, smp_name, smp_conditions):
        self.conditions[smp_name] = smp_conditions
        
        
    def GetTreeItems(self):
        return sorted(self.sub_model_parts.keys()) # return sorted bcs it is also sorted in the json format!
            
    
    def _NumberOfNodes(self):
        return len(self.nodes)


    def _NumberOfElements(self):
        num_elements = 0
        for smp in self.sub_model_parts.values():
            num_elements += smp.NumberOfElements()
        return num_elements


    def _NumberOfConditions(self):
        num_conditions = 0
        for smp in self.sub_model_parts.values():
            num_conditions += smp.NumberOfConditions()
        return num_conditions
    

    def WriteMesh(self, file):
        start_time = time.time()
        logging.info("Writing Mesh")
        self._Assemble() # TODO only do this if sth has changed
        # Write Header
        self._WriteMeshInfo(file)
        file.write("\nBegin ModelPartData\n//  VARIABLE_NAME value\nEnd ModelPartData\n\n")
        file.write("Begin Properties 0\nEnd Properties\n\n")
        
        # Write Nodes
        self._WriteNodes(file)
        
        # Write Elements
        self._WriteElements(file)
        
        # Write Conditions
        self._WriteConditions(file)
        
        # Write SubModelParts
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.WriteMesh(file)
        
        logging.info("Mesh writing time: " + "{:.2f}".format(time.time() - start_time) + " sec")
                
        return True
            
            
    def _WriteNodes(self, file):
        file.write("Begin Nodes\n")

        if READABLE_MDPA:
            max_ID = max(self.nodes.keys())
            logging.debug("Max Node ID: " + str(max_ID))

            spaces_coords_x = '{:>' + str(len(str(int(self.max_node_coord_x))) + self.precision + self.num_spaces) + '} '
            spaces_coords_y = '{:>' + str(len(str(int(self.max_node_coord_y))) + self.precision + self.num_spaces) + '} '
            spaces_coords_z = '{:>' + str(len(str(int(self.max_node_coord_z))) + self.precision + self.num_spaces) + '} '
            format_str = '{:>' + str(len(str(max_ID))) + '} ' + spaces_coords_x + spaces_coords_y + spaces_coords_z
        else:
            format_str = '{} {} {} {}'
            
        logging.debug("Node Format String: " + str(format_str))

        for ID in sorted(list(self.nodes.keys())):
            coords = self.nodes[ID]

            coords = [round(coords[0], self.precision), 
                      round(coords[1], self.precision), 
                      round(coords[2], self.precision)]
            
            line = format_str.format(str(ID), coords[0], str(coords[1]), str(coords[2])) + "\n"

            file.write(line)
        
        file.write("End Nodes\n\n")
        
        
    def _WriteElements(self, file):
        if READABLE_MDPA:
            num_elements = self._NumberOfElements()
            format_str = '{:>' + str(len(str(num_elements))) + '} {:>' + str(self.num_spaces) + '}'
            space = "\t"
        else:
            format_str = '{} {}'
            space = " "

        logging.debug("Element Format String: " + str(format_str))

        for smp_name in sorted(list(self.elements.keys())):
            for element_name in sorted(list(self.elements[smp_name])):

                file.write("Begin Elements " + element_name + " // " + smp_name + "\n")
                elements_by_name = self.elements[smp_name][element_name]
                for elem in elements_by_name:
                    file.write(elem.GetWriteLine(self.element_counter, format_str, space) + "\n")
                    self.element_counter += 1
                
                file.write("End Elements // " + element_name + "\n\n")        
        
        
    def _WriteConditions(self, file):
        if READABLE_MDPA:
            num_conditions = self._NumberOfConditions()
            format_str = '{:>' + str(len(str(num_conditions))) + '} {:>' + str(self.num_spaces) + '}'
            space = "\t"
        else:
            format_str = '{} {}'
            space = " "

        logging.debug("Condition Format String: " + str(format_str))

        for smp_name in sorted(list(self.conditions.keys())):
            for condition_name in sorted(list(self.conditions[smp_name])):

                file.write("Begin Conditions " + condition_name + " // " + smp_name + "\n")
                conditions_by_name = self.conditions[smp_name][condition_name]
                for cond in conditions_by_name:
                    file.write(cond.GetWriteLine(self.condition_counter, format_str, space) + "\n")
                    self.condition_counter += 1
                
                file.write("End Conditions // " + condition_name + "\n\n")
    

    def _WriteMeshInfo(self, file):
        localtime = time.asctime( time.localtime(time.time()) )
        file.write("// File created on " + localtime + " with SALOME-Kratos Converter\n")
        file.write("// Mesh Information:\n")
        file.write("// Number of Nodes: " + str(self._NumberOfNodes()) + "\n")
        file.write("// Number of Elements: " + str(self._NumberOfElements()) + "\n")
        file.write("// Number of Conditions: " + str(self._NumberOfConditions()) + "\n")

        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.WriteMeshInfo(file)



class MeshSubmodelPart:
    def __init__(self): # TODO is this needed?
        pass
        
        
    def Initialize(self):
        self.nodes = {}
        self.elements = {}
        self.conditions = {}


    def FillWithEntities(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        self.smp_info_dict = smp_info_dict
        self.mesh_dict = mesh_dict
        self.nodes_read = nodes_read
        self.geom_entities_read = geom_entities_read
        self.smp_info_dict_used_for_assembly = None
        self.mesh_dict_used_for_assembly = None
        self.Initialize()
        

    def Update(self, smp_info_dict, mesh_dict):
        self.smp_info_dict = smp_info_dict
        self.mesh_dict = mesh_dict


    def Serialize(self):
        logging.debug("Serializing " + self.smp_info_dict["smp_name"])
        serialized_smp = {}

        serialized_smp["submodelpart_information"] = self.smp_info_dict
        serialized_smp["mesh_information"] = self.mesh_dict
        serialized_smp["nodes_read"] = self._SerializeNodesRead()
        serialized_smp["geom_entities_read"] = self._SerializeGeomEntitiesRead()

        return {self.smp_info_dict["smp_name"] : serialized_smp}


    def _SerializeNodesRead(self):
        self._AddNodes() # Update the internal information
        
        return self.nodes


    def _SerializeGeomEntitiesRead(self):
        serialized_geom_entities = []
        
        for salome_ID in self.geom_entities_read:
            for entity in self.geom_entities_read[salome_ID]:
                serialized_geom_entities.append(entity.Serialize())
            
        return serialized_geom_entities


    def Deserialize(self, smp_name, serialized_smp):
        smp_info_dict, mesh_dict = self._DeserializeDictionary(serialized_smp)

        nodes_read = {}
        geom_entities_read = {}
        if "nodes_read" in serialized_smp:
            nodes_read  = self._DeserializeNodesRead(serialized_smp["nodes_read"])
            if "geom_entities_read" in serialized_smp: # Geometric Entities can only exist if there are nodes!
                geom_entities_read = self._DeserializeGeomEntitiesRead(serialized_smp["geom_entities_read"])

        self.FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)

        logging.debug("Deserialized " + smp_name)


    def _DeserializeDictionary(self, serialized_smp):
        # concert the keys to strings (has to be done bcs json converts ints to string)
        if not "submodelpart_information" in serialized_smp:
            raise Exception("\"submodelpart_information\" is not in serialized SubModelPart!")

        if not "mesh_information" in serialized_smp:
            raise Exception("\"mesh_information\" is not in serialized SubModelPart!")
        
        mesh_dict = CorrectMeshDict(serialized_smp["mesh_information"])

        return serialized_smp["submodelpart_information"], mesh_dict

    
    def _DeserializeNodesRead(self, serialized_nodes_read):
        return DictKeyToInt(serialized_nodes_read) # Nodes don't need deserialization


    def _DeserializeGeomEntitiesRead(self, serialized_geom_entities_read):
        deserialized_geom_entities_read = {}
        
        for serialized_entity in serialized_geom_entities_read:
            # serialized_entity = [self.salome_ID, self.salome_identifier, self.node_list]
            salome_ID         = serialized_entity[0]
            salome_identifier = serialized_entity[1]
            node_list         = serialized_entity[2]
    
            geom_entity = GeometricEntitySalome(salome_ID, salome_identifier, node_list)
            
            if salome_identifier not in deserialized_geom_entities_read: # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                deserialized_geom_entities_read[salome_identifier] = []

            deserialized_geom_entities_read[salome_identifier].append(geom_entity)
        
        return deserialized_geom_entities_read        
        
    
    def GetGeomEntites(self):
        return self.geom_entities_read
    
    
    def Assemble(self):
        # This function creates the Kratos entities from the read entities  
        # that are defined in it's dictionary
        if (self.mesh_dict_used_for_assembly != self.mesh_dict and
            self.smp_info_dict_used_for_assembly != self.smp_info_dict):
        
            self.smp_info_dict_used_for_assembly = self.smp_info_dict
            self.mesh_dict_used_for_assembly = self.mesh_dict
            
            self._AddNodes()
            self._AddElements()
            self._AddConditions()
        
    
    def _AddNodes(self):
        self.nodes = self.nodes_read        
        
        
    def _AddElements(self):
        self.elements.clear()

        for salome_identifier in self.mesh_dict["entity_creation"].keys():
            geom_entities = self.geom_entities_read[salome_identifier]
            
            if "Element" in self.mesh_dict["entity_creation"][salome_identifier]:
                element_dict = self.mesh_dict["entity_creation"][salome_identifier]["Element"]
                element_list = element_dict.keys()
                for element_name in sorted(element_list):
                    if element_name not in self.elements:
                        self.elements[element_name] = []
                    
                    property_ID = element_dict[element_name]
            
                    for entity in geom_entities:
                        self.elements[element_name].append(Element(entity, element_name, property_ID))
        
        
    def _AddConditions(self):
        self.conditions.clear()

        for salome_identifier in self.mesh_dict["entity_creation"].keys():
            geom_entities = self.geom_entities_read[salome_identifier]
            
            if "Condition" in self.mesh_dict["entity_creation"][salome_identifier]:
                condition_dict = self.mesh_dict["entity_creation"][salome_identifier]["Condition"]
                condition_list = condition_dict.keys()
                for condition_name in sorted(condition_list):
                    if condition_name not in self.conditions:
                        self.conditions[condition_name] = []
                    
                    property_ID = condition_dict[condition_name]
                        
                    for entity in geom_entities:
                        self.conditions[condition_name].append(Condition(entity, condition_name, property_ID))        
    
    def GetMesh(self):
        return self.nodes, self.elements, self.conditions
    
    def GetInfoDict(self):
        return self.smp_info_dict
    
    def GetMeshInfoDict(self):
        return self.mesh_dict

    def NumberOfNodes(self):
        return len(self.nodes)

    def NumberOfElements(self):
        return sum([len(val) for val in self.elements.values()])

    def NumberOfConditions(self):
        return sum([len(val) for val in self.conditions.values()])
    
    
    def WriteMesh(self, file):
        # Write Header
        if self.mesh_dict["write_smp"]:
            smp_name = self.smp_info_dict["smp_name"]
            file.write("Begin SubModelPart " + smp_name + "\n")
            
            space = ""
            if READABLE_MDPA:
                space = "\t"

            # Write Nodes
            self._WriteNodes(file, space)
            
            # Write Elements
            self._WriteElements(file, space)
            
            # Write Conditions
            self._WriteConditions(file, space)
            
            file.write("End SubModelPart // " + smp_name + "\n\n")
        
            
    def _WriteNodes(self, file, space):
        file.write(space + "Begin SubModelPartNodes\n")

        for ID in sorted(self.nodes.keys()):
            file.write(space + space + str(ID) + "\n")
        
        file.write(space + "End SubModelPartNodes\n")
        
        
    def _WriteElements(self, file, space):
        file.write(space + "Begin SubModelPartElements \n")
        
        for element_name in sorted(self.elements.keys()):
            for elem in self.elements[element_name]:
                file.write(space + space + str(elem.GetID()) + "\n")
            
        file.write(space + "End SubModelPartElements \n")
        
        
    def _WriteConditions(self, file, space):
        file.write(space + "Begin SubModelPartConditions \n")
        
        for condition_name in sorted(self.conditions.keys()):
            for cond in self.conditions[condition_name]:
                file.write(space + space + str(cond.GetID()) + "\n")
            
        file.write(space + "End SubModelPartConditions \n")


    def WriteMeshInfo(self, file):
        if self.mesh_dict["write_smp"]: 
            file.write("// SubModelPart " + self.smp_info_dict["smp_name"] + "\n")
            file.write("//   Number of Nodes: " + str(self.NumberOfNodes()) + "\n")
            file.write("//   Number of Elements: " + str(self.NumberOfElements()) + "\n")
            file.write("//   Number of Conditions: " + str(self.NumberOfConditions()) + "\n")