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
# Global Variables
DEBUG = True          # Set this Variable to "True" for debugging
LOG_TIMING = True
READABLE_MDPA = True  # Use this to get a nicely formatted mdpa file. Works in most cases, but files are larger (~20%) and mdpa writing takes slightly more time

# Python imports
import sys
import time
import logging

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

NODE_IDENTIFIER = 101 # This was made by me, it does not come from SALOME! Cannot start with 0!
SALOME_IDENTIFIERS = {
        NODE_IDENTIFIER : "Node", 
        102 : "Line",
        203 : "Triangle",
        204 : "Quadrilateral",
        304 : "Tetrahedral",
        308 : "Hexahedral"        
}

ELEMENTS = {
    "0_Generic" : {
        102 : [ 
            "Element2D2N",
        ],
        203 : [ 
            "Element2D3N",
            "Element3D3N"
        ],
        204 : [ 
            "Element2D4N"
        ],
        304 : [ 
            "Element3D4N"
        ],
        308 : [ 
            "Element3D8N"
        ],
    },
    "1_Fluid" : {
        203 : [ 
            "Element2D3N"
        ],
        304 : [ 
            "Element3D4N"
        ]
    },
    "2_Structure" : {
        NODE_IDENTIFIER : [ 
            "NodalConcentratedElement2D1N",
            "NodalConcentratedDampedElement2D1N",

            "NodalConcentratedElement3D1N",
            "NodalConcentratedDampedElement3D1N"
        ],
        102 : [ 
            "TrussElement3D2N",
            "TrussLinearElement3D2N",

            "CrBeamElement3D2N",
            "CrLinearBeamElement3D2N",

            "SpringDamperElement3D2N"
        ],
        203 : [ 
            "SmallDisplacementElement2D3N",
            "TotalLagrangianElement2D3N",
            "UpdatedLagrangianElement2D3N",

            "PreStressMembraneElement3D3N",

            "ShellThinElementCorotational3D3N"
            "ShellThickElementCorotational3D3N"
        ],
        204 : [ 
            "SmallDisplacementElement2D4N",
            "TotalLagrangianElement2D4N",
            "UpdatedLagrangianElement2D4N",

            "PreStressMembraneElement3D4N",

            "ShellThinElementCorotational3D4N", 
            "ShellThickElementCorotational3D4N"
        ],
        304 : [
            "SmallDisplacementElement3D4N",
            "TotalLagrangianElement3D4N",
            "UpdatedLagrangianElement3D4N"

        ],
        308 : [
            "SmallDisplacementElement3D8N",
            "TotalLagrangianElement3D8N",
            "UpdatedLagrangianElement3D8N"

        ]
    }
}

CONDITIONS = {
    "0_Generic" : {
        NODE_IDENTIFIER : [ 
            "PointCondition2D1N",
            "PointCondition3D1N"
        ],
        102 : [  
            "LineCondition2D2N",
            "LineCondition3D2N"
        ],
        203 : [ 
            "SurfaceCondition3D3N"            
        ],
        204 : [ 
            "SurfaceCondition3D4N"
        ]
    },
    "1_Fluid" : {
        102 : [ 
            "WallCondition2D2N"
        ],
        203 : [ 
            "WallCondition3D3N"
        ]
    },
    "2_Structure" : {
        NODE_IDENTIFIER : [ 
            "PointLoadCondition2D1N",
            "PointLoadCondition2D1N",

            "PointMomentCondition3D1N",

            "PointTorqueCondition3D1N"
        ],
        102 : [ 
            "LineLoadCondition2D2N"
        ],
        203 : [ 
            "SurfaceLoadCondition3D3N"
        ],
        204 : [ 
            "SurfaceLoadCondition3D4N"
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


# Other Functions
def GetGeneralInfoDict(Version=None):
    general_info_dict = {}
    localtime = time.asctime( time.localtime(time.time()) )
    if Version:
        general_info_dict.update({"Version" : Version})
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


def GetEntityType(SalomeIdentifier):
    post_string = "Unknown"
    if SalomeIdentifier in SALOME_IDENTIFIERS:
        post_string = SALOME_IDENTIFIERS[SalomeIdentifier]

    return str(SalomeIdentifier) + "_" + post_string


def GetSalomeIdentifier(origin_entity):
    return int(origin_entity.split("_")[0])


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
            salome_identifier = GetSalomeIdentifier(item_values[2])
            
            AddEntryToDict(dictionary, salome_identifier, "Element", element_name, property_ID)

        if (tree.tag_has("Condition", child)):
            item_values = tree.item(child,"values")
            condition_name = item_values[0]
            property_ID = item_values[1]
            salome_identifier = GetSalomeIdentifier(item_values[2])
            
            AddEntryToDict(dictionary, salome_identifier, "Condition", condition_name, property_ID)
    
    return dictionary
    
    
def AddEntryToDict(json_dict, salome_identifier, entity_type, entity_name, property_ID):
    if salome_identifier not in json_dict["entity_creation"]:
        json_dict["entity_creation"][salome_identifier] = {}
        
    if entity_type not in json_dict["entity_creation"][salome_identifier]:
        json_dict["entity_creation"][salome_identifier][entity_type] = {}
            
    json_dict["entity_creation"][salome_identifier][entity_type].update({entity_name: property_ID})

def GetDebug():
    return DEBUG

def GetReadableMDPA():
    return READABLE_MDPA

def LogInfo(LogInfo):
    logging.info(LogInfo)

def LogDebug(LogInfo):
    logging.debug(LogInfo)

def LogTiming(log_info, start_time):
    if LOG_TIMING:
        logging.info(" [TIMING] \"" + log_info + "\" {:.2f}".format(time.time() - start_time) + " sec")



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


    def GetID(self):
        return self.salome_ID


    def Serialize(self):
        serialized_entity = [self.salome_ID, self.salome_identifier, self.node_list]
        return serialized_entity
        