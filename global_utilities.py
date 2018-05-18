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
DEBUG = False          # Set this Variable to "True" for debugging
LOG_TIMING = True

# Python imports
import sys
import os
import time
import logging

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

NODE_IDENTIFIER = 101 # This was made by me. Cannot start with 0!
GEOMETRY_IDENTIFIERS = {
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
            "CableElement3D2N",

            "TrussElement3D2N",
            "TrussLinearElement3D2N",

            "CrBeamElement2D2N",
            "CrLinearBeamElement2D2N",
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


def ReadAndParseSalomeDatFile(file_path):
    valid_file = True
    nodes = {}
    geom_entities = {}

    if not os.path.isfile(file_path):
        logging.error('File \"{}\" was not found!'.format(file_path))

        return False, None, None

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
                    nodes.update( {salome_ID : [coords, {}] } )

                geom_entities = {}

                # Read Geometric Objects (Lines, Triangles, Quads, ...)
                for line in lines[num_nodes+1:]:
                    words = line.split()
                    salome_ID = int(words[0])
                    geometry_identifier = int(words[1]) # get the salome identifier
                    node_list = []
                    for i in range(2, len(words)):
                        node_list.append(int(words[i]))

                    CorrectSalomeNodeListOrder(node_list, geometry_identifier)

                    geom_entity = GeometricEntity(salome_ID,
                                                  geometry_identifier,
                                                  node_list)

                    if geometry_identifier not in geom_entities: # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                        geom_entities[geometry_identifier] = []

                    geom_entities[geometry_identifier].append(geom_entity)
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


def GetEntityType(geometry_identifier):
    post_string = "Unknown"
    if geometry_identifier in GEOMETRY_IDENTIFIERS:
        post_string = GEOMETRY_IDENTIFIERS[geometry_identifier]

    return str(geometry_identifier) + "_" + post_string


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


def CorrectSalomeNodeListOrder(salome_node_list, geometry_identifier):
    # This function corrects the order in the node list because for
    # some elements the nodal order is different btw SALOME and Kratos
    if geometry_identifier == 308: # Hexahedral
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
            geometry_identifier = GetSalomeIdentifier(item_values[2])

            AddEntryToDict(dictionary, geometry_identifier, "Element", element_name, property_ID)

        if (tree.tag_has("Condition", child)):
            item_values = tree.item(child,"values")
            condition_name = item_values[0]
            property_ID = item_values[1]
            geometry_identifier = GetSalomeIdentifier(item_values[2])

            AddEntryToDict(dictionary, geometry_identifier, "Condition", condition_name, property_ID)

    return dictionary


def AddEntryToDict(json_dict, geometry_identifier, entity_type, entity_name, property_ID):
    if geometry_identifier not in json_dict["entity_creation"]:
        json_dict["entity_creation"][geometry_identifier] = {}

    if entity_type not in json_dict["entity_creation"][geometry_identifier]:
        json_dict["entity_creation"][geometry_identifier][entity_type] = {}

    json_dict["entity_creation"][geometry_identifier][entity_type].update({entity_name: property_ID})

def GetDebug():
    return DEBUG

def LogInfo(LogInfo):
    logging.info(LogInfo)

def LogDebug(LogInfo):
    logging.debug(LogInfo)

def LogError(LogInfo):
    logging.error(LogInfo)

def LogTiming(log_info, start_time):
    if LOG_TIMING:
        logging.info(" [TIMING] \"" + log_info + "\" {:.2f}".format(time.time() - start_time) + " sec")



class GeometricEntity:
    """
    This class is a generic geometric entity
    """
    def __init__(self, origin_ID, geometry_identifier, node_list, entity_data={}):
        self.origin_ID = origin_ID
        self.geometry_identifier = geometry_identifier
        self.node_list = node_list # The order or nodes has to be compatible with Kratos
        self.entity_data = entity_data # Nodal-, Elemental- or ConditionalData
        self.child_objects = {}


    def __str__(self):
        stringbuf = "GeometricEntity | "
        stringbuf += "origin_ID: " + str(self.origin_ID)
        stringbuf += "; geometry_identifier: " + str(self.geometry_identifier)
        stringbuf += "; node_list: " + str(self.node_list)
        stringbuf += "; entity_data: " + str(self.entity_data)
        return stringbuf

    __repr__ = __str__


    def __eq__(self, Other):
        if self.origin_ID != Other.origin_ID:
            return False
        if self.geometry_identifier != Other.geometry_identifier:
            return False
        if self.node_list != Other.node_list:
            return False
        if self.entity_data != Other.entity_data:
            return False
        return True


    def GetNodeList(self):
        return self.node_list


    def GetID(self):

        print("RRRR")
        return self.origin_ID


    def HasEntityData(self):
        return len(self.entity_data) > 0


    def GetEntityData(self):
        return self.entity_data

    def GetGeometryIdentifier(self):
        return self.geometry_identifier


    def GetChildObject(self, name_entity, class_object, propID):
        """
        This function checks if it already has a child of the
        requested name. If not, it creates one and returns it.
        This is needed if elements or conditions belong to separate
        SubModelParts in order to not create them multiple times
        """
        if name_entity not in self.child_objects.keys():
            self.child_objects[name_entity] = class_object(self, name_entity, propID)

        return self.child_objects[name_entity]


    def Serialize(self):
        """ This function serializes the object """
        serialized_entity = [self.origin_ID,
                             self.geometry_identifier,
                             self.node_list,
                             self.entity_data]

        return serialized_entity

    @staticmethod
    def Deserialize(serialized_entity):
        """
        This function takes a serialized entity and creates a new
        class object out of it
        """
        origin_ID           = serialized_entity[0]
        geometry_identifier = serialized_entity[1]
        node_list           = serialized_entity[2]
        entity_data         = serialized_entity[3]

        geom_entity = GeometricEntity(origin_ID,
                                      geometry_identifier,
                                      node_list,
                                      entity_data)

        return geom_entity
