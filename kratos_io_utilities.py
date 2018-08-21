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

# Python imports
import time

# Project imports
import global_utilities as global_utils

READABLE_MDPA = False


def CreateNode(node_id, coords, nodal_data={}):
    '''Wrapper function for once the Node-Class will be used'''
    if node_id <= 0:
        raise Exception("The NodeID has to be larger than 0!")
    if type(coords) != list:
        raise Exception("The NodeCoords have to be provided as a list!")
    if len(coords) != 3:
        raise Exception("The NodeCoords have to consist of three doubles!")
    return [coords, nodal_data]

class Node(object):
    def __init__(self, Id, coordinates, nodal_data=None):
        self.Id = Id
        self.coordinates = coordinates
        self.nodal_data = nodal_data
        if self.nodal_data == None: # this is done bcs default args are shared!
            self.nodal_data = {}

        if not type(coordinates) == list:
            raise TypeError('type of "coordinates" should be "list", received: ' + str(type(coordinates)))
        if not len(coordinates) == 3:
            raise Exception('Coordinates have to be three doubles!')
        if not type(nodal_data) == dict:
            raise TypeError('type of "nodal_data" should be "dict", received: ' + str(type(nodal_data)))

    def GetId(self):
        return self.Id

    def GetCoordinates(self):
        return self.coordinates

    def HasNodalData(self):
        return len(self.nodal_data) > 0

    def GetNodalData(self):
        return self.nodal_data

    def SetNodalData(self, data_name, data_value):
        self.entity_data[data_name] = data_value

    def Serialize(self):
        """This function returns the serialized node
        """
        serialized_node = [self.Id,
                           self.coordinates,
                           self.nodal_data]

        return serialized_node

    @staticmethod
    def Deserialize(serialized_node):
        """This function takes a serialized node and creates a new
        node out of it
        """
        Id          = serialized_node[0]
        coordinates = serialized_node[1]
        nodal_data  = serialized_node[2]

        node = Node(Id, coordinates, nodal_data)

        return node


class KratosEntity(object):
    def __init__(self, origin_entity, name, property_ID):
        self.is_node = False
        if isinstance(origin_entity, int):
            self.is_node = True

        self.origin_entity = origin_entity # int for Node, GeometricEntitySalome for Element/Condition

        self.name = name
        self.property_ID = property_ID
        self.new_ID = -1
        self.is_added_already = False

    def __str__(self):
        stringbuf = "Name: " + self.name
        stringbuf += "; PropID: " + str(self.property_ID)
        stringbuf += "; NewId: " + str(self.new_ID)
        '''
        if self.is_node:
            stringbuf += "; OriginEntity: " + str(self.origin_entity)
        else:
            stringbuf += "; OriginEntity: " + str(self.origin_entity)
        '''
        stringbuf += "; OriginEntity: " + str(self.origin_entity)

        return stringbuf

    __repr__ = __str__

    def __eq__(self, Other):
        if self.origin_entity != Other.origin_entity:
            return False
        if self.name != Other.name:
            return False
        if self.property_ID != Other.property_ID:
            return False
        return True

    def GetWriteLine(self, format_str, space):
        # "0" is the Property Placeholder
        line = format_str.format(str(self.new_ID), str(self.property_ID))

        if self.is_node:
            line += space + str(self.origin_entity)
        else:
            for node in self.origin_entity.GetNodeList():
                line += space + str(node)

            if global_utils.DEBUG:
                line += " // " + str(self.origin_entity.GetID()) # add the origin ID

        return line

    def SetIsAdded(self):
        self.is_added_already = True

    def IsAddedAlready(self):
        return self.is_added_already

    def ResetWritingInfo(self):
        self.new_ID = -1
        self.is_added_already = False

    def SetID(self, new_id):
        self.new_ID = new_id

    def GetID(self):
        if self.new_ID == -1:
            raise RuntimeError("No new ID has been assiged")
        return self.new_ID

    def GetNodeList(self):
        return self.origin_entity.GetNodeList()

    def HasEntityData(self):
        return self.origin_entity.HasEntityData()

    def GetEntityData(self):
        return self.origin_entity.GetEntityData()

    def SetEntityData(self, data_name, data_value):
        self.origin_entity.SetEntityData(data_name, data_value)



class Element(KratosEntity):
    def __init__(self, origin_entity, name, property_ID):
        super(Element, self).__init__(origin_entity, name, property_ID)

    def __str__(self):
        return "Element | " + super(Element, self).__str__()

    __repr__ = __str__



class Condition(KratosEntity):
    def __init__(self, origin_entity, name, property_ID):
        super(Condition, self).__init__(origin_entity, name, property_ID)

    def __str__(self):
        return "Condition | " + super(Condition, self).__str__()

    __repr__ = __str__



class MainModelPart:
    def __init__(self):
        self.__Initialize()


    def __Initialize(self):
        self.sub_model_parts = {}
        self.__InitializeMesh()
        self.mesh_read = False
        self.precision = 12 # Same as in Kratos ("/kratos/includes/gid_io.h")
        self.num_spaces = 3 # number of spaces in mdpa btw numbers


    def __InitializeMesh(self):
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
        self.__Initialize()


    def SubModelPartNameExists(self, smp_name):
        smp_exists = False

        if smp_name in self.sub_model_parts.keys():
            smp_exists = True

        return smp_exists


    def FileNameExists(self, file_name):
        for smp in self.sub_model_parts.values():
            smp_file_name = smp.GetFileName()
            if smp_file_name != "":
                if file_name == smp_file_name:
                    return True
        return False


    def FilePathExists(self, file_path):
        for smp in self.sub_model_parts.values():
            smp_file_path = smp.GetFilePath()
            if smp_file_path != "":
                if file_path == smp_file_path:
                    return True
        return False


    def AssembleMeshInfoDict(self):
        mp_dict = {}

        for smp_name in self.sub_model_parts.keys():
            mp_dict[smp_name] = self.sub_model_parts[smp_name].GetMeshInfoDict()

        return mp_dict


    def AddMesh(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        smp_name = smp_info_dict["smp_name"]
        if smp_name in self.sub_model_parts.keys():
            raise NameError("SubModelPart \"" + smp_name + "\" exists already!")

        self.sub_model_parts[smp_name] = MeshSubmodelPart()
        self.sub_model_parts[smp_name].FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)

        self.mesh_read = True


    def UpdateMesh(self, old_smp_name, smp_info_dict, mesh_dict):
        new_smp_name = smp_info_dict["smp_name"]
        if old_smp_name not in self.sub_model_parts.keys():
            raise NameError("SubModelPart \"" + old_smp_name + "\" does not exist!")
        self.sub_model_parts[new_smp_name] = self.sub_model_parts.pop(old_smp_name) # Update the key

        self.sub_model_parts[new_smp_name].Update(smp_info_dict, mesh_dict)


    def RemoveSubmodelPart(self, name_smp):
        self.sub_model_parts.pop(name_smp, None)


    def Serialize(self):
        # This function serializes the ModelPart such that it can be saved in a json file
        global_utils.LogDebug("Serializing ModelPart")
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

        global_utils.LogDebug("Deserialized ModelPart")


    def GetTreeItems(self):
        return sorted(self.sub_model_parts.keys()) # return sorted bcs it is also sorted in the json format!

    def WriteMesh(self, mdpa_file_path, info_text="", readable_mdpa=False): # TODO use this
        self.__Assemble(readable_mdpa) # TODO only do this if sth has changed

        start_time = time.time()
        global_utils.LogInfo("Writing Mesh")

        # Write Header
        if not mdpa_file_path.endswith('.mdpa'):
             mdpa_file_path += ".mdpa"
        with open(mdpa_file_path,"w") as mdpa_file:
            self.__WriteMeshInfo(mdpa_file, info_text)
            mdpa_file.write("\nBegin ModelPartData\n//  VARIABLE_NAME value\nEnd ModelPartData\n\n")
            mdpa_file.write("Begin Properties 0\nEnd Properties\n\n")

            # Write Nodes
            self.__WriteNodes(mdpa_file, readable_mdpa)

            # Write Elements
            self.__WriteElements(mdpa_file, readable_mdpa)

            # Write Conditions
            self.__WriteConditions(mdpa_file, readable_mdpa)

            # Write Nodal Data
            self.__WriteNodalData(mdpa_file, readable_mdpa)

            # Write Elemental Data
            self.__WriteGeometricalEntityData(mdpa_file, readable_mdpa, self.elements, "Element")

            # Write Conditional Data
            self.__WriteGeometricalEntityData(mdpa_file, readable_mdpa, self.conditions, "Condition")

            # Write SubModelParts
            for smp_name in sorted(self.sub_model_parts.keys()):
                smp = self.sub_model_parts[smp_name]
                smp.WriteMesh(mdpa_file, readable_mdpa)

            global_utils.LogTiming("Mesh writing time", start_time)

        return True


    def __WriteMeshInfo(self, open_file, info_text=""):
        '''
        Writing some information about the ModelPart to the mdpa file
        '''
        import time
        localtime = time.asctime( time.localtime(time.time()) )
        open_file.write("// File created on " + localtime + "\n")
        if info_text != "":
            open_file.write("// " + info_text + "\n")
        open_file.write("// Mesh Information:\n")
        open_file.write("// Number of Nodes: " + str(self.NumberOfNodes()) + "\n")
        open_file.write("// Number of Elements: " + str(self.NumberOfElements()) + "\n")
        open_file.write("// Number of Conditions: " + str(self.NumberOfConditions()) + "\n")
        num_smps_to_write = sum([smp.WriteSubModelPart() for smp in self.sub_model_parts.values()])
        open_file.write("// Number of SubModelParts: " + str(num_smps_to_write) + "\n")
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.WriteMeshInfo(open_file)

        open_file.write("\n")


    def __WriteNodes(self, open_file, readable_mdpa):
        open_file.write("Begin Nodes\n")

        if readable_mdpa:
            max_ID = max(self.nodes.keys())
            global_utils.LogDebug("Max Node ID: " + str(max_ID))

            spaces_coords_x = '{:>' + str(len(str(int(self.max_node_coord_x))) + self.precision + self.num_spaces) + '} '
            spaces_coords_y = '{:>' + str(len(str(int(self.max_node_coord_y))) + self.precision + self.num_spaces) + '} '
            spaces_coords_z = '{:>' + str(len(str(int(self.max_node_coord_z))) + self.precision + self.num_spaces) + '} '
            format_str = '{:>' + str(len(str(max_ID))) + '} ' + spaces_coords_x + spaces_coords_y + spaces_coords_z
        else:
            format_str = '{} {} {} {}'

        global_utils.LogDebug("Node Format String: " + str(format_str))

        for ID in sorted(list(self.nodes.keys())):
            coords = self.nodes[ID][0]

            coords = [round(coords[0], self.precision),
                      round(coords[1], self.precision),
                      round(coords[2], self.precision)]

            line = format_str.format(str(ID), coords[0], str(coords[1]), str(coords[2])) + "\n"

            open_file.write(line)

        open_file.write("End Nodes\n\n")


    def __WriteElements(self, open_file, readable_mdpa):
        if readable_mdpa:
            num_elements = self.NumberOfElements()
            format_str = '{:>' + str(len(str(num_elements))) + '} {:>' + str(self.num_spaces) + '}'
            space = "\t"
        else:
            format_str = '{} {}'
            space = " "

        global_utils.LogDebug("Element Format String: " + str(format_str))

        for element_name in sorted(list(self.elements.keys())):
            open_file.write("Begin Elements " + element_name + "\n")
            elements_by_name = self.elements[element_name]
            for elem in elements_by_name:
                open_file.write(elem.GetWriteLine(format_str, space) + "\n")

            open_file.write("End Elements // " + element_name + "\n\n")

    def __WriteNodalData(self, open_file, readable_mdpa):
        all_geom_entity_data = {}

        # Extracting the Data from the Nodes
        for node_id in sorted(list(self.nodes.keys())):
            node = self.nodes[node_id]
            nodal_data = node[1]
            if len(nodal_data) > 0:
                for var_name, var_data in nodal_data.items():
                    if not var_name in all_geom_entity_data:
                        all_geom_entity_data[var_name] = {}
                    all_geom_entity_data[var_name][node_id] = var_data

        self.__WriteEntityData(open_file, readable_mdpa, all_geom_entity_data, "Nod")

    def __WriteGeometricalEntityData(self, open_file, readable_mdpa, geom_entities, entity_name):
        all_geom_entity_data = {}

        # Extracting the Data from the geom_entities
        for geom_entity_name in sorted(list(geom_entities.keys())):
            geom_entities_by_name = geom_entities[geom_entity_name]
            for geom_entity in geom_entities_by_name:
                if geom_entity.HasEntityData():
                    geom_entity_data = geom_entity.GetEntityData()
                    geom_entity_id = geom_entity.GetID()
                    for var_name, var_data in geom_entity_data.items():
                        if not var_name in all_geom_entity_data:
                            all_geom_entity_data[var_name] = {}
                        all_geom_entity_data[var_name][geom_entity_id] = var_data

        self.__WriteEntityData(open_file, readable_mdpa, all_geom_entity_data, entity_name)

    def __WriteEntityData(self, open_file, readable_mdpa, all_geom_entity_data, entity_name):
        entity_name += "alData" # Convert e.g. "Element" to "ElementalData"
        if readable_mdpa:
            space = "    "
        else:
            space = ""

        for var_name in sorted(list(all_geom_entity_data.keys())):
            geom_entity_data_by_var = all_geom_entity_data[var_name]
            rand_var = next(iter(geom_entity_data_by_var.values())) # gettign a random value to check the type
            var_type = self.__GetVariableType(rand_var)

            open_file.write("Begin " + entity_name + " " + var_name + "\n")

            if var_type == "scalar":
                for geom_entity_data_id in sorted(list(geom_entity_data_by_var.keys())):
                    data = geom_entity_data_by_var[geom_entity_data_id]
                    open_file.write(space + str(geom_entity_data_id) + " " + str(data) + "\n")
            elif var_type == "vector":
                for geom_entity_data_id in sorted(list(geom_entity_data_by_var.keys())):
                    data = geom_entity_data_by_var[geom_entity_data_id]
                    open_file.write(space + str(geom_entity_data_id) + " [" + str(len(data)) + "] ( ")
                    open_file.write(str(data[0]))
                    for entry in data[1:]:
                        open_file.write(" , " + str(entry))
                    open_file.write(" )\n")
            elif var_type == "matrix":
                raise NotImplementedError("writting Matrices as Data is not yet implemented!")

            open_file.write("End " + entity_name + " // " + var_name + "\n\n")

    def __GetVariableType(self, variable):
        if type(variable) == list:
            if len(variable) == 0:
                raise Exception("Entity data vector cannot have size 0!")
            if type(variable[0]) == list:
                return "matrix"
            elif isinstance(variable[0], (float, int)):
                return "vector"
            else:
                raise Exception("Wrong data type!", type(variable[0]))
        elif isinstance(variable, (float, int)):
            return "scalar"
        else:
            raise Exception("Wrong data type!", type(variable))

    def __WriteConditions(self, open_file, readable_mdpa):
        if readable_mdpa:
            num_conditions = self.NumberOfConditions()
            format_str = '{:>' + str(len(str(num_conditions))) + '} {:>' + str(self.num_spaces) + '}'
            space = "\t"
        else:
            format_str = '{} {}'
            space = " "

        global_utils.LogDebug("Condition Format String: " + str(format_str))

        for condition_name in sorted(list(self.conditions.keys())):
            open_file.write("Begin Conditions " + condition_name + "\n")
            conditions_by_name = self.conditions[condition_name]
            for cond in conditions_by_name:
                open_file.write(cond.GetWriteLine(format_str, space) + "\n")

            open_file.write("End Conditions // " + condition_name + "\n\n")


    def __Assemble(self, readable_mdpa):
        # TODO Check if this was done before! (same for the submodelparts)
        start_time = time.time()
        global_utils.LogInfo("Assembling Mesh")
        self.__InitializeMesh()
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.Assemble()
            smp_nodes, smp_elements, smp_conditions = smp.GetMesh()
            self.__AddNodes(smp_nodes, readable_mdpa)
            self.__AddElements(smp_elements)
            self.__AddConditions(smp_conditions)

        global_utils.LogTiming("Mesh assembling time", start_time)


    def __AddNodes(self, smp_nodes, readable_mdpa):
        for node_ID in smp_nodes.keys():
            if node_ID in self.nodes.keys():
                existing_node_coords = self.nodes[node_ID][0]
                new_coords = smp_nodes[node_ID][0]
                if existing_node_coords != new_coords:
                    err_msg  = "Node with ID " + str(node_ID) + " already exists with different coordinates!\n"
                    err_msg += "\tExisting Coords: [" + str(existing_node_coords[0]) + " , "
                    err_msg += str(existing_node_coords[1]) + " , "
                    err_msg += str(existing_node_coords[2]) + "]\n"
                    err_msg += "\tNew Coords: [" + str(new_coords[0]) + " , "
                    err_msg += str(new_coords[1]) + " , "
                    err_msg += str(new_coords[2]) + "] "
                    raise Exception(err_msg)
            else:
                self.nodes[node_ID] = smp_nodes[node_ID]
                if readable_mdpa:
                    if smp_nodes[node_ID][0][0] > self.max_node_coord_x: self.max_node_coord_x = smp_nodes[node_ID][0][0]
                    if smp_nodes[node_ID][0][1] > self.max_node_coord_y: self.max_node_coord_y = smp_nodes[node_ID][0][1]
                    if smp_nodes[node_ID][0][2] > self.max_node_coord_z: self.max_node_coord_z = smp_nodes[node_ID][0][2]


    def __AddElements(self, smp_elements):
        self.__AddGeometricEntities(smp_elements, self.elements)


    def __AddConditions(self, smp_conditions):
        self.__AddGeometricEntities(smp_conditions, self.conditions)


    def __AddGeometricEntities(self, smp_entities, all_entities):
        id_index = sum([len(val) for val in all_entities.values()]) + 1
        for entity_name in sorted(smp_entities.keys()):
            entities = smp_entities[entity_name]

            if entity_name not in all_entities.keys():
                all_entities[entity_name] = []

            for entity in entities:
                if not entity.IsAddedAlready():
                    all_entities[entity_name].append(entity)
                    entity.SetID(id_index)
                    entity.SetIsAdded()
                    id_index += 1


    def NumberOfNodes(self):
        return len(self.nodes)


    def NumberOfElements(self):
        return sum([len(val) for val in self.elements.values()])


    def NumberOfConditions(self):
        return sum([len(val) for val in self.conditions.values()])


class MeshSubmodelPart:
    def __init__(self):
        """Constructor of the MeshSubModelPart
        Sets some internal variables
        """
        self.is_properly_initialized = False
        self.is_assembled = False


    def __InitializeMesh(self):
        """This function initializes the member variables for the mesh
        """
        self.nodes = {}
        self.elements = {}
        self.conditions = {}


    def FillWithEntities(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        """This function fills the MeshSubModelPart with entities
        This function has to be called before other operations such
        as assembling can be performed
        """
        self.__ValidateSMPInfoDict(smp_info_dict)
        self.smp_info_dict = smp_info_dict

        self.__ValidateMeshDict(mesh_dict)
        self.mesh_dict = mesh_dict

        self.nodes_read = nodes_read
        self.geom_entities_read = geom_entities_read
        self.is_properly_initialized = True


    def Update(self, smp_info_dict, mesh_dict):
        """This function updates the MeshSubModelPart
        E.g. if different Elements/Conditions should
        be created from the Geometric Entities
        """
        self.__CheckIsProperlyInitialized()

        self.__ValidateSMPInfoDict(smp_info_dict)
        self.smp_info_dict = smp_info_dict

        self.__ValidateMeshDict(mesh_dict)
        self.mesh_dict = mesh_dict

        self.is_assembled = False


    def __ValidateSMPInfoDict(self, smp_info_dict):
        """This function adds missing information to the
        dictionary based on default values.
        It mimics the "ValidateAndAssignDefaults" function in Kratos
        """
        default_smp_info_dict = {
            "smp_name"      : "PLEASE_SPECIFY_SUBMODELPART_NAME",
            "smp_file_name" : "",
            "smp_file_path" : ""
        }

        for k,v in default_smp_info_dict.items():
            if k not in smp_info_dict:
                smp_info_dict[k] = v # Assigning the default value


    def __ValidateMeshDict(self, mesh_dict):
        """This function adds missing information to the
        dictionary based on default values.
        It mimics the "ValidateAndAssignDefaults" function in Kratos
        """
        default_mesh_dict = {
            "entity_creation" : {},
            "write_smp"       : True
        }

        for k,v in default_mesh_dict.items():
            if k not in mesh_dict:
                mesh_dict[k] = v # Assigning the default value


    def Assemble(self):
        """This function assembles the entities in the MeshSubModelPart
        After this operation the Object is ready to write it's
        entities to an mdpa file
        """
        self.__CheckIsProperlyInitialized()
        self.__InitializeMesh()

        # This function creates the Kratos entities from the read entities
        # that are defined in it's dictionary
        self.__AddNodes()
        self.__AddElements()
        self.__AddConditions()

        self.is_assembled = True


    def __AddNodes(self):
        self.nodes = self.nodes_read


    def __AddElements(self):
        self.__AddGeometricEntities("Element", Element, self.elements)


    def __AddConditions(self):
        self.__AddGeometricEntities("Condition", Condition, self.conditions)


    def __AddGeometricEntities(self, entity_name, entity_class, entity_container):
        entity_container.clear()

        for geometry_identifier in self.mesh_dict["entity_creation"].keys():
            if geometry_identifier == global_utils.NODE_IDENTIFIER:
                if geometry_identifier in self.geom_entities_read:
                    entities = self.geom_entities_read[geometry_identifier] # in case the 101-entities were created outside
                else:
                    entities = self.__CreateGeometricEntitiesFromNodes(self.nodes)
            else:
                entities = self.geom_entities_read[geometry_identifier]

            if entity_name in self.mesh_dict["entity_creation"][geometry_identifier]:
                entity_dict = self.mesh_dict["entity_creation"][geometry_identifier][entity_name]
                entity_name_list = entity_dict.keys()
                for ent_name in sorted(entity_name_list):
                    if ent_name not in entity_container:
                        entity_container[ent_name] = []
                    property_ID = entity_dict[ent_name]

                    for entity in entities:
                        new_entity = entity.GetChildObject(ent_name, entity_class, property_ID)
                        entity_container[ent_name].append(new_entity)


    def __CreateGeometricEntitiesFromNodes(self, nodes):
        """This function creates objects of type "GeometricEntity"
        from Nodes. This is needed for point-based entities in Kratos,
        e.g. PointLoadCondition, NodalConcentratedElement
        """
        geom_entities = []

        for node_id, node_data in nodes.items():
            nodal_data = node_data[1]
            if type(nodal_data) != dict:
                raise Exception("wrong datatype for nodal_data, type received: "+ str(type(nodal_data)))
            geom_entities.append(global_utils.GeometricEntity(-1,
                                                              global_utils.NODE_IDENTIFIER,
                                                              [node_id],
                                                              nodal_data))

        return geom_entities

    def GetMesh(self):
        self.__CheckIsAssembled()
        return self.nodes, self.elements, self.conditions

    def GetGeomEntites(self): # TODO still needed?
        return self.geom_entities_read

    def GetInfoDict(self):
        self.__CheckIsProperlyInitialized()
        return self.smp_info_dict

    def GetMeshInfoDict(self):
        self.__CheckIsProperlyInitialized()
        return self.mesh_dict

    def GetFileName(self):
        if self.is_properly_initialized:
            return self.smp_info_dict["smp_file_name"]
        else:
            return ""

    def GetFilePath(self):
        if self.is_properly_initialized:
            return self.smp_info_dict["smp_file_path"]
        else:
            return ""

    def NumberOfNodes(self):
        """Returns the number of Nodes in this SubModelPart
        """
        self.__CheckIsAssembled()
        return len(self.nodes)

    def NumberOfElements(self):
        """Returns the number of Elements in this SubModelPart
        """
        self.__CheckIsAssembled()
        return sum([len(val) for val in self.elements.values()])

    def NumberOfConditions(self):
        """Returns the number of Conditions in this SubModelPart
        """
        self.__CheckIsAssembled()
        return sum([len(val) for val in self.conditions.values()])

    def WriteMesh(self, open_file, readable_mdpa=False):
        """This function writes the SubModelPart to the
        mdpa-file (If wanted).
        """
        self.__CheckIsAssembled()

        # Write Header
        if self.mesh_dict["write_smp"]:
            smp_name = self.smp_info_dict["smp_name"]
            open_file.write("Begin SubModelPart " + smp_name + "\n")

            space = ""
            if readable_mdpa:
                space = "\t"

            self.__WriteNodes(open_file, space)
            self.__WriteElements(open_file, space)
            self.__WriteConditions(open_file, space)

            open_file.write("End SubModelPart // " + smp_name + "\n\n")


    def __WriteNodes(self, open_file, space):
        """This function write the SubModelPartNodes to the
        mdpa-file.
        Note that these are only the Ids of the Nodes
        """
        self.__CheckIsAssembled()

        open_file.write(space + "Begin SubModelPartNodes\n")

        for ID in sorted(self.nodes.keys()):
            open_file.write(space + space + str(ID) + "\n")

        open_file.write(space + "End SubModelPartNodes\n")


    def __WriteElements(self, open_file, space):
        """This function write the SubModelPartElements to the
        mdpa-file.
        """
        self.__WriteEntityIds(open_file, space, "Elements", self.elements)


    def __WriteConditions(self, open_file, space):
        """This functin write the SubModelPartConditions to the
        mdpa-file.
        """
        self.__WriteEntityIds(open_file, space, "Conditions", self.conditions)


    def __WriteEntityIds(self, open_file, space, entity_type_name, entities):
        """This function writes the Ids of the entities to the
        mdpa file.
        Note that these are only the Ids of the entities
        """
        self.__CheckIsAssembled()

        smp_entities_name = "SubModelPart" + entity_type_name

        open_file.write(space + "Begin " + smp_entities_name + "\n")

        for entity_name in sorted(entities.keys()):
            for entity in entities[entity_name]:
                open_file.write(space + space + str(entity.GetID()) + "\n")

        open_file.write(space + "End " + smp_entities_name + "\n")

    def WriteSubModelPart(self):
        return self.mesh_dict["write_smp"]

    def WriteMeshInfo(self, open_file):
        """This function is called by the parent class to write info about this
        SubModelPart to the header of the mdpa-file
        """
        self.__CheckIsAssembled()
        if self.mesh_dict["write_smp"]:
            open_file.write("// SubModelPart " + self.smp_info_dict["smp_name"] + "\n")
            open_file.write("//   Number of Nodes: " + str(self.NumberOfNodes()) + "\n")
            open_file.write("//   Number of Elements: " + str(self.NumberOfElements()) + "\n")
            open_file.write("//   Number of Conditions: " + str(self.NumberOfConditions()) + "\n")


    def __CheckIsAssembled(self):
        """This function checks if the MeshSubModelPart has been assembled
        It is used internally to ensure that the MeshSubModelPart is assembled
        """
        self.__CheckIsProperlyInitialized()
        if not self.is_assembled:
            raise RuntimeError("MeshSubmodelPart was not assembled!")


    def __CheckIsProperlyInitialized(self):
        """This function checks if the MeshSubModelPart has been properly initialized
        It is used internally to ensure that the MeshSubModelPart is properly initialized
        """
        if not self.is_properly_initialized:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")

    ##############################################
    ##### Functions related to Serialization #####
    ##############################################
    def Serialize(self):
        self.__CheckIsProperlyInitialized()

        global_utils.LogDebug("Serializing " + self.smp_info_dict["smp_name"])
        serialized_smp = {}

        serialized_smp["submodelpart_information"] = self.smp_info_dict
        serialized_smp["mesh_information"] = self.mesh_dict
        serialized_smp["nodes_read"] = self.__SerializeNodesRead()
        serialized_smp["geom_entities_read"] = self.__SerializeGeomEntitiesRead()

        return {self.smp_info_dict["smp_name"] : serialized_smp}


    def __SerializeNodesRead(self):
        self.__AddNodes() # Update the internal information
        return self.nodes


    def __SerializeGeomEntitiesRead(self):
        serialized_geom_entities = []

        for salome_ID in self.geom_entities_read:
            for entity in self.geom_entities_read[salome_ID]:
                serialized_geom_entities.append(entity.Serialize())

        return serialized_geom_entities


    def Deserialize(self, smp_name, serialized_smp):
        smp_info_dict, mesh_dict = self.__DeserializeDictionary(serialized_smp)

        nodes_read = {}
        geom_entities_read = {}
        if "nodes_read" in serialized_smp:
            nodes_read  = self.__DeserializeNodesRead(serialized_smp["nodes_read"])
            if "geom_entities_read" in serialized_smp: # Geometric Entities can only exist if there are nodes!
                geom_entities_read = self.__DeserializeGeomEntitiesRead(serialized_smp["geom_entities_read"])

        self.FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)

        global_utils.LogDebug("Deserialized " + smp_name)


    def __DeserializeDictionary(self, serialized_smp):
        # concert the keys to strings (has to be done bcs json converts ints to string)
        if not "submodelpart_information" in serialized_smp:
            raise RuntimeError("\"submodelpart_information\" is not in serialized SubModelPart!")

        if not "mesh_information" in serialized_smp:
            raise RuntimeError("\"mesh_information\" is not in serialized SubModelPart!")

        mesh_dict = global_utils.CorrectMeshDict(serialized_smp["mesh_information"])

        return serialized_smp["submodelpart_information"], mesh_dict


    def __DeserializeNodesRead(self, serialized_nodes_read):
        return global_utils.DictKeyToInt(serialized_nodes_read) # Nodes don't need deserialization


    def __DeserializeGeomEntitiesRead(self, serialized_geom_entities_read):
        deserialized_geom_entities_read = {}

        for serialized_entity in serialized_geom_entities_read:
            geom_entity = global_utils.GeometricEntity.Deserialize(serialized_entity)

            geometry_identifier = geom_entity.GetGeometryIdentifier()

            if geometry_identifier not in deserialized_geom_entities_read.keys(): # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                deserialized_geom_entities_read[geometry_identifier] = []

            deserialized_geom_entities_read[geometry_identifier].append(geom_entity)

        return deserialized_geom_entities_read