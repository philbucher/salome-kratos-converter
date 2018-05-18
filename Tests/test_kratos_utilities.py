import unittest
import sys
import os
import filecmp
sys.path.insert(0, '../')
import kratos_io_utilities as kratos_utils
import global_utilities as global_utils



class TestKratosEntity(unittest.TestCase):

    def _test_GetID(self, obj2test):
        with self.assertRaisesRegex(RuntimeError,"No new ID has been assiged"):
            obj2test.GetID()

    def _test_SetID(self,obj2test):
        obj2test.SetID(5)
        self.assertEqual(5,obj2test.GetID())

    def _test___eq__(self,obj2test,class2test):
        other_entity = global_utils.GeometricEntity(125, 203, [1,2], {"NodalData" : 123})
        other_obj = class2test(
            origin_entity=other_entity, name="SomeName", property_ID=5)

        self.assertTrue(obj2test.__eq__(other_obj))

    def _test_SetIsAdded(self,obj2test):
        obj2test.SetIsAdded()
        self.assertTrue(obj2test.IsAddedAlready())

    def _test_IsAddedAlready(self,obj2test):
        obj2test.ResetWritingInfo()
        self.assertFalse(obj2test.IsAddedAlready())

    def _test_ResetWritingInfo(self,obj2test):
        obj2test.ResetWritingInfo()
        self.assertFalse(obj2test.IsAddedAlready())
        #self.assertEqual(-1,obj2test.GetID())

    def _test___str__(self,obj2test,class2test):
        recieved=obj2test.__str__()

        if class2test == kratos_utils.KratosEntity:
            expected="Name: SomeName; PropID: 5; NewId: -1; OriginEntity: GeometricEntity | origin_ID: 125; geometry_identifier: 203; node_list: [1, 2]; entity_data: {'NodalData': 123}"
        elif class2test == kratos_utils.Element:
            expected="Element | Name: SomeName; PropID: 5; NewId: -1; OriginEntity: GeometricEntity | origin_ID: 125; geometry_identifier: 203; node_list: [1, 2]; entity_data: {'NodalData': 123}"
        elif class2test == kratos_utils.Condition:
            expected="Condition | Name: SomeName; PropID: 5; NewId: -1; OriginEntity: GeometricEntity | origin_ID: 125; geometry_identifier: 203; node_list: [1, 2]; entity_data: {'NodalData': 123}"

        self.assertEqual(recieved,expected)

    # def _test_GetWriteLineNode(self, class2test):
    #     """
    #     Here the KratosEntity is a "Node", sine it is not constructed with a Geometrical Entity
    #     """
    #     obj2test = class2test(
    #         origin_entity=1, name="SomeOtherName", property_ID=2)
    #     write_line = obj2test.GetWriteLine(
    #         NewID=85, format_str='{} {}', space=" ")

    #     expected = "85 2 1"

    #     self.assertEqual(expected, write_line)

    # def _test_GetWriteLineGeomEntity(self, class2test):
    #     """
    #     Here the KratosEntity is an "Element" or "Condition", sine it is constructed with a Geometrical Entity
    #     """
    #     geom_entity = global_utils.GeometricEntity(35, 102, [1,5,9])
    #     obj2test = class2test(
    #         origin_entity=geom_entity, name="SomeOtherName", property_ID=2)
    #     write_line = obj2test.GetWriteLine(
    #         NewID=85, format_str='{} {}', space=" ")

    #     if global_utils.GetDebug():
    #         expected = "85 2 1 5 9 // 35"
    #     else:
    #         expected = "85 2 1 5 9"

    #     self.assertEqual(expected, write_line)

    def _test_HasEntityData(self, obj2test):
        self.assertTrue(obj2test.HasEntityData())

    def _test_GetEntityData(self,obj2test):
        self.assertEqual(obj2test.GetEntityData(),{"NodalData":123})

    def _test_GetNodeList(self,obj2test):
        self.assertEqual(obj2test.GetNodeList(), [1,2])

    def _execute_entity_tests(self, class2test):

        orig_entity = global_utils.GeometricEntity(125, 203, [1,2], {"NodalData" : 123})
        obj2test = class2test(
            origin_entity=orig_entity, name="SomeName", property_ID=5)

        self._test_GetID(obj2test)
        self._test_SetID(obj2test)
        self._test___eq__(obj2test,class2test)
        self._test_SetIsAdded(obj2test)
        self._test_IsAddedAlready(obj2test)
        self._test_ResetWritingInfo(obj2test)
        self._test___str__(obj2test,class2test)
        # self._test_GetWriteLineNode(class2test)
        # self._test_GetWriteLineGeomEntity(class2test)
        self._test_HasEntityData(obj2test)
        self._test_GetEntityData(obj2test)
        self._test_GetNodeList(obj2test)

    def test_KratosEntity(self):
        class2test = kratos_utils.KratosEntity # "Class-Pointer"

        self._execute_entity_tests(class2test)

    def test_Element(self):
        class2test = kratos_utils.Element # "Class-Pointer"

        self._execute_entity_tests(class2test)

    def test_Condition(self):
        class2test = kratos_utils.Condition  # "Class-Pointer"

        self._execute_entity_tests(class2test)


class TestMainModelPart(unittest.TestCase):
    maxDiff = None # this is needed to get the output of "self.assertDictEqual"

    def setUp(self):

        self.nodes = {1: [[0.0, 0.0, 0.0],{}], 2: [[5.0, 0.0, 0.0],{}], 3: [[5.0, 1.0, 0.0],{}],
                      4: [[0.0, 1.0, 0.0],{}], 5: [[0.2, 0.0, 0.0],{}], 6: [[0.4, 0.0, 0.0],{}],
                      7: [[1.0, 1.0, 0.0],{}], 8: [[0.2, 1.0, 0.0],{}], 9: [[0.4, 1.0, 0.0],{}]}

        entity_1 = global_utils.GeometricEntity(23, 102, [1,2])
        entity_2 = global_utils.GeometricEntity(24, 102, [2,3])
        entity_3 = global_utils.GeometricEntity(25, 102, [3,4])
        entity_4 = global_utils.GeometricEntity(27, 102, [4,1])

        entity_5 = global_utils.GeometricEntity(29, 204, [4,1,5,6])
        entity_6 = global_utils.GeometricEntity(28, 204, [4,1,2,3])

        self.geom_entities = {102 : [entity_1, entity_2, entity_3, entity_4], 204 : [entity_5, entity_6]}

        self.elements = {
            'ShellThinElement3D4N' : [kratos_utils.Element(entity_5, 'ShellThinElement3D4N', '2'),
                                      kratos_utils.Element(entity_6, 'ShellThinElement3D4N', '2')],
            'TrussElement' : [kratos_utils.Element(entity_1, 'TrussElement', '4'),
                              kratos_utils.Element(entity_2, 'TrussElement', '4'),
                              kratos_utils.Element(entity_3, 'TrussElement', '4'),
                              kratos_utils.Element(entity_4, 'TrussElement', '4')],
            'UpdatedLagrangianElement2D4N' : [kratos_utils.Element(entity_5, 'UpdatedLagrangianElement2D4N', '15'),
                                              kratos_utils.Element(entity_6, 'UpdatedLagrangianElement2D4N', '15')]
        }

        #why is this kratos_utils.Elements ????
        self.conditions = {
            'SurfaceCondition2D4N' : [kratos_utils.Element(entity_5, 'SurfaceCondition2D4N', '5'),
                                      kratos_utils.Element(entity_6, 'SurfaceCondition2D4N', '5')],
            'LineLoadCondition2D2N' : [kratos_utils.Element(entity_1, 'LineLoadCondition2D2N', '0'),
                                       kratos_utils.Element(entity_2, 'LineLoadCondition2D2N', '0'),
                                       kratos_utils.Element(entity_3, 'LineLoadCondition2D2N', '0'),
                                       kratos_utils.Element(entity_4, 'LineLoadCondition2D2N', '0')]
        }

        self.smp1_dict = {'smp_name': 'domain_custom', 'smp_file_name': 'domain',
                                'smp_file_path': '/Examples/Structure/Test_1_2D.salome/dat-files/domain.dat'}

        self.smp1_mesh_dict = {'write_smp': 1, 'entity_creation': {204: {'Element':
                                {'UpdatedLagrangianElement2D4N': '15', 'ShellThinElement3D4N' : '2'}, 'Condition' : {'SurfaceCondition2D4N' : '5'}},
                                102: {'Element' : {'TrussElement' : '4'}, 'Condition': {'LineLoadCondition2D2N': '0'}}}}

        self.serialized_smp1 = {'domain_custom': {'nodes_read': self.nodes,
                                'submodelpart_information': self.smp1_dict,
                                'geom_entities_read': [[29, 204, [4, 1, 5, 6]], [28, 204, [4, 1, 2, 3]],
                                [23, 102, [1, 2]], [24, 102, [2, 3]], [25, 102, [3, 4]], [27, 102, [4, 1]]],
                                'mesh_information': self.smp1_mesh_dict}}

        self.mp_dict={'domain_custom': self.smp1_mesh_dict}

        self.serialized_mp={'domain_custom': {'submodelpart_information': {'smp_name': 'domain_custom', 'smp_file_name': 'domain', 'smp_file_path': '/Examples/Structure/Test_1_2D.salome/dat-files/domain.dat'},
                            'mesh_information': {'write_smp': 1, 'entity_creation': {204: {'Element': {'UpdatedLagrangianElement2D4N': '15', 'ShellThinElement3D4N': '2'}, 'Condition': {'SurfaceCondition2D4N': '5'}}, 102: {'Element': {'TrussElement': '4'}, 'Condition': {'LineLoadCondition2D2N': '0'}}}},
                            'nodes_read': {1: [[0.0, 0.0, 0.0], {}], 2: [[5.0, 0.0, 0.0], {}], 3: [[5.0, 1.0, 0.0], {}], 4: [[0.0, 1.0, 0.0], {}], 5: [[0.2, 0.0, 0.0], {}], 6: [[0.4, 0.0, 0.0], {}], 7: [[1.0, 1.0, 0.0], {}], 8: [[0.2, 1.0, 0.0], {}], 9: [[0.4, 1.0, 0.0], {}]},
                            'geom_entities_read': [[23, 102, [1, 2], {}], [24, 102, [2, 3], {}], [25, 102, [3, 4], {}], [27, 102, [4, 1], {}], [29, 204, [4, 1, 5, 6], {}], [28, 204, [4, 1, 2, 3], {}]]}}

    # Incomplete
    def _test_mp_for_correctness(self,MpToTest):

        print("imcomplete")
        #for smp in self.sub_model_parts.items()


    def test_MainModelPart(self):
        obj2test = kratos_utils.MainModelPart()

        serialized_obj = obj2test.Serialize()
        self.assertEqual({}, serialized_obj)

    def testGetMeshRead(self):
        obj2test = kratos_utils.MainModelPart()

        self.assertEqual(obj2test.GetMeshRead(),False)

    #def testGetSubModelPart(self):
        #obj2test = kratos_utils.MainModelPart()

        #model_part = KratosMultiphysics.ModelPart()

        #obj2test.__AddSubModelPart(model_part)
    def testReset(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)
        self.assertEqual(obj2test.GetMeshRead(),True)
        obj2test.Reset()
        self.assertEqual(obj2test.GetMeshRead(),False)


    def testSubModelPartNameExists(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        self.assertEqual(obj2test.SubModelPartNameExists('domain_custom'),True)

    def testFileNameExists(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        self.assertEqual(obj2test.FileNameExists('domain'),True)

    def testFilePathExists(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        self.assertEqual(obj2test.FilePathExists('/Examples/Structure/Test_1_2D.salome/dat-files/domain.dat'),True)

    def testAssembleMeshInfoDict(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        self.assertDictEqual(obj2test.AssembleMeshInfoDict(),self.mp_dict)

    def testAddMesh(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        self.assertEqual(obj2test.GetMeshRead(),True)

    def testUpdateMesh(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        smp2_dict = {'smp_name': 'domain_custom2', 'smp_file_name': 'domain2',
                                'smp_file_path': 'randomfilename.dat'}

        smp2_mesh_dict = {'write_smp': 1, 'entity_creation': {204: {'Element':
                                {'UpdatedLagrangianElement2D4N': '15', 'ShellThinElement3D4N' : '2'}, 'Condition' : {'SurfaceCondition2D4N' : '5'}},
                                102: {'Element' : {'TrussElement' : '4'}, 'Condition': {'LineLoadCondition2D2N': '0'}}}}

        obj2test.UpdateMesh('domain_custom',smp2_dict,smp2_mesh_dict)

        # following statement checks for new smp name as a submodel part in main model part
        self.assertEqual(obj2test.SubModelPartNameExists('domain_custom2'),True)

    def testRemoveSubmodelPart(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        obj2test.RemoveSubmodelPart('domain_custom')
        self.assertFalse(obj2test.SubModelPartNameExists('domain_custom'))

    def testSerialize(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.AddMesh(self.smp1_dict,self.smp1_mesh_dict,self.nodes,self.geom_entities)

        self.assertDictEqual(obj2test.Serialize(),self.serialized_mp)

    # Incomplete
    def testDeserialize(self):
        obj2test = kratos_utils.MainModelPart()
        obj2test.Deserialize(self.serialized_mp)

        self.assertEqual(obj2test.GetMeshRead(),True)
        self._test_mp_for_correctness(obj2test)

    def test_SameEntitiesInDifferentSMPs(self):
        nodes = {1: [[0.0, 0.0, 0.0],{}], 2: [[5.0, 0.0, 0.0],{}], 3: [[5.0, 1.0, 0.0],{}]}

        entity_1 = global_utils.GeometricEntity(23, 102, [1,2])
        entity_2 = global_utils.GeometricEntity(24, 102, [2,3])

        geom_entities = {102 : [entity_1, entity_2]}

        smp_dict_1 = {'smp_name': 'domain_1'}
        smp_dict_2 = {'smp_name': 'domain_2'}

        smp_mesh ={'write_smp': 1, 'entity_creation': {102: {'Element': {'TrussElement': '15'}}}}

        main_mp = kratos_utils.MainModelPart()

        main_mp.AddMesh(smp_dict_1, smp_mesh, nodes, geom_entities)
        main_mp.AddMesh(smp_dict_2, smp_mesh, nodes, geom_entities)

        main_mp.WriteMesh("my_file")

        print(main_mp.NumberOfNodes())
        print(main_mp.NumberOfElements())
        print(main_mp.NumberOfConditions())




class MeshSubmodelPart(unittest.TestCase):

    def setUp(self):
        self.write_mesh_readable_ref_file = os.path.join(os.getcwd(), "MeshSubmodelPart_WriteMesh_readable.ref")
        self.write_mesh_ref_file = os.path.join(os.getcwd(), "MeshSubmodelPart_WriteMesh.ref")
        self.write_mesh_info_ref_file = os.path.join(os.getcwd(), "MeshSubmodelPart_WriteMeshInfo.ref")
        self.test_file = os.path.join(os.getcwd(), "test_file.tmp")

        self.nodes = {1: [[0.0, 0.0, 0.0], {}], 2: [[5.0, 0.0, 0.0], {}], 3: [[5.0, 1.0, 0.0], {}],
                      4: [[0.0, 1.0, 0.0], {}], 5: [[0.2, 0.0, 0.0], {}], 6: [[0.4, 0.0, 0.0], {}]}

        entity_1 = global_utils.GeometricEntity(23, 102, [1,2])
        entity_2 = global_utils.GeometricEntity(24, 102, [2,3])
        entity_3 = global_utils.GeometricEntity(25, 102, [3,4])
        entity_4 = global_utils.GeometricEntity(27, 102, [4,1])

        entity_5 = global_utils.GeometricEntity(29, 204, [4,1,5,6])
        entity_6 = global_utils.GeometricEntity(28, 204, [4,1,2,3])

        self.geom_entities = {102 : [entity_1, entity_2, entity_3, entity_4], 204 : [entity_5, entity_6]}

        self.elements = {
            'ShellThinElement3D4N' : [kratos_utils.Element(entity_5, 'ShellThinElement3D4N', '2'),
                                      kratos_utils.Element(entity_6, 'ShellThinElement3D4N', '2')],
            'TrussElement' : [kratos_utils.Element(entity_1, 'TrussElement', '4'),
                              kratos_utils.Element(entity_2, 'TrussElement', '4'),
                              kratos_utils.Element(entity_3, 'TrussElement', '4'),
                              kratos_utils.Element(entity_4, 'TrussElement', '4')],
            'UpdatedLagrangianElement2D4N' : [kratos_utils.Element(entity_5, 'UpdatedLagrangianElement2D4N', '15'),
                                              kratos_utils.Element(entity_6, 'UpdatedLagrangianElement2D4N', '15')]
        }

        #why is this kratos_utils.Elements ????
        self.conditions = {
            'SurfaceCondition2D4N' : [kratos_utils.Element(entity_5, 'SurfaceCondition2D4N', '5'),
                                      kratos_utils.Element(entity_6, 'SurfaceCondition2D4N', '5')],
            'LineLoadCondition2D2N' : [kratos_utils.Element(entity_1, 'LineLoadCondition2D2N', '0'),
                                       kratos_utils.Element(entity_2, 'LineLoadCondition2D2N', '0'),
                                       kratos_utils.Element(entity_3, 'LineLoadCondition2D2N', '0'),
                                       kratos_utils.Element(entity_4, 'LineLoadCondition2D2N', '0')]
        }

        self.smp_dict = {'smp_name': 'domain_custom', 'smp_file_name': 'domain',
                                'smp_file_path': '/Examples/Structure/Test_1_2D.salome/dat-files/domain.dat'}

        self.smp_mesh_dict = {'write_smp': 1, 'entity_creation': {204: {'Element':
                                {'UpdatedLagrangianElement2D4N': '15', 'ShellThinElement3D4N' : '2'}, 'Condition' : {'SurfaceCondition2D4N' : '5'}},
                                102: {'Element' : {'TrussElement' : '4'}, 'Condition': {'LineLoadCondition2D2N': '0'}}}}

        self.serialized_smp = {'domain_custom': {'nodes_read': self.nodes,
                                'submodelpart_information': self.smp_dict,
                                'geom_entities_read': [[29, 204, [4, 1, 5, 6]], [28, 204, [4, 1, 2, 3]],
                                [23, 102, [1, 2]], [24, 102, [2, 3]], [25, 102, [3, 4]], [27, 102, [4, 1]]],
                                'mesh_information': self.smp_mesh_dict}}

    def tearDown(self):
        if os.path.isfile(self.test_file):
            os.remove(self.test_file)

    def _fill_smp(self, SmpToFill):

        smp_dict = {'smp_file_name': 'domain', 'smp_name': 'domain_custom', 'smp_file_path':
                    '/Examples/Structure/Test_1_2D.salome/dat-files/domain.dat'}
        mesh_dict = {'entity_creation': {204: {'Element': {'UpdatedLagrangianElement2D4N': '15', 'ShellThinElement3D4N' : '2'},
                                        'Condition' : {'SurfaceCondition2D4N' : '5'}},
                                         102: {'Element' : {'TrussElement' : '4'}, 'Condition': {'LineLoadCondition2D2N': '0'}}},
                                         'write_smp': 1}

        SmpToFill.FillWithEntities(smp_dict, mesh_dict, self.nodes, self.geom_entities)

    def _test_smp_for_correctness(self, SmpToTest):
        self.assertDictEqual(self.geom_entities, SmpToTest.GetGeomEntites())

        self.assertDictEqual(self.smp_dict, SmpToTest.GetInfoDict())
        self.assertDictEqual(self.smp_mesh_dict, SmpToTest.GetMeshInfoDict())
        self.assertEqual(self.smp_dict['smp_file_name'], SmpToTest.GetFileName())
        self.assertEqual(self.smp_dict['smp_file_path'], SmpToTest.GetFilePath())

        SmpToTest.Assemble()

        self.assertEqual(6, SmpToTest.NumberOfNodes())
        self.assertEqual(8, SmpToTest.NumberOfElements())
        self.assertEqual(6, SmpToTest.NumberOfConditions())

        nodes, elements, conditions = SmpToTest.GetMesh()

        # compare Nodes
        self.assertDictEqual(self.nodes, nodes)

        # compare Elements
        self.assertEqual(len(self.elements), len(elements))

        for elem_name in self.elements.keys():
            self_elems = self.elements[elem_name]
            new_elems = elements[elem_name]
            self.assertEqual(len(self_elems), len(new_elems))
            for i in range(len(self_elems)):
                self.assertEqual(self_elems[i], new_elems[i])

        # compare Conditions
        self.assertEqual(len(self.conditions), len(conditions))

        for cond_name in self.conditions.keys():
            self_conds = self.conditions[cond_name]
            new_conds = conditions[cond_name]
            self.assertEqual(len(self_conds), len(new_conds))
            for i in range(len(self_conds)):
                self.assertEqual(self_conds[i], new_conds[i])

    def test_Assemble(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaisesRegex(RuntimeError,"MeshSubmodelPart is not properly initialized!"): # Throws bcs the obj2test is not properly initialized!
            obj2test.Assemble()

    def test_FillWithEntities(self):
        obj2test = kratos_utils.MeshSubmodelPart()
        self._fill_smp(obj2test) # Must not throw!

        self._test_smp_for_correctness(obj2test)

    def test_Update(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        smp_dict_new = {'smp_file_name': 'dirichlet', 'smp_name': 'dirichlet_name', 'smp_file_path': '/Examples/Structure/Test_1_2D.salome/dat-files/dirichlet.dat'}
        mesh_dict_new = {'entity_creation': {204: {'Element': {'TotalLagrangianElement2D4N': '15'}}, 102: {'Condition': {'Condition2D2N': '0'}}}, 'write_smp': 1}

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.Update(smp_dict_new, mesh_dict_new)

        self._fill_smp(obj2test) # Must not throw!

        obj2test.Update(smp_dict_new, mesh_dict_new)

        self.assertDictEqual(smp_dict_new, obj2test.GetInfoDict())
        self.assertDictEqual(mesh_dict_new, obj2test.GetMeshInfoDict())

    def _test_Serialize(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.Serialize()

        self._fill_smp(obj2test) # Must not throw!

        serialized_smp = obj2test.Serialize()

        self.assertDictEqual(self.serialized_smp, serialized_smp)

    # def test_Deserialize(self):
    #     obj2test = kratos_utils.MeshSubmodelPart()

    #     obj2test.Deserialize("domain_custom", self.serialized_smp["domain_custom"])

    #     self._test_smp_for_correctness(obj2test)


    def test_DoubleSerializing(self):
        smp_generic = kratos_utils.MeshSubmodelPart()

        self._fill_smp(smp_generic) # Must not throw!

        serialized_smp = smp_generic.Serialize()

        obj2test = kratos_utils.MeshSubmodelPart()

        obj2test.Deserialize("domain_custom", serialized_smp["domain_custom"])

        self._test_smp_for_correctness(obj2test)

    def test_CreateGeometricEntitiesFromNodes(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        geom_entities_from_nodes = obj2test.__CreateGeometricEntitiesFromNodes(self.nodes)

        reference_geom_entities = [
            global_utils.GeometricEntity(-1, 101, [1]),
            global_utils.GeometricEntity(-1, 101, [2]),
            global_utils.GeometricEntity(-1, 101, [3]),
            global_utils.GeometricEntity(-1, 101, [4]),
            global_utils.GeometricEntity(-1, 101, [5]),
            global_utils.GeometricEntity(-1, 101, [6])
        ]

        self.assertEqual(len(geom_entities_from_nodes), len(reference_geom_entities))

        for created_entitiy, ref_entity in zip(geom_entities_from_nodes, reference_geom_entities):
            self.assertEqual(created_entitiy, ref_entity)



    def test_GetGeomEntites(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(AttributeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.GetGeomEntites()

    def test_GetMesh(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.GetMesh()

    def test_GetInfoDict(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.GetInfoDict()

    def test_GetMeshInfoDict(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.GetMeshInfoDict()

    def test_NumberOfNodes(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.NumberOfNodes()

    def test_NumberOfElements(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.NumberOfElements()

    def test_NumberOfConditions(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.NumberOfConditions()

    def test_GetFileName(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        self.assertEqual(obj2test.GetFileName(), "")

    def test_GetFilePath(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        self.assertEqual(obj2test.GetFilePath(), "")

    def test_WriteMesh(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with open(self.test_file, "w") as test_file:
            with self.assertRaisesRegex(RuntimeError,"MeshSubmodelPart is not properly initialized!"):
                obj2test.WriteMesh(test_file)

        self._fill_smp(obj2test)
        obj2test.Assemble()

        nodes, elements, conditions = obj2test.GetMesh()

        # Hackish way to assign new IDs, bcs Elements and Conditions throw if the didn't get assigned a new ID!
        index = 1
        for elem_name in sorted(elements.keys()):
            new_elems = elements[elem_name]
            for i in range(len(new_elems)):
                new_elems[i].new_ID = index
                index +=1

        index = 1
        for elem_name in sorted(conditions.keys()):
            new_conds = conditions[elem_name]
            for i in range(len(new_conds)):
                new_conds[i].new_ID = index
                index +=1

        with open(self.test_file, "w") as test_file:
            obj2test.WriteMesh(test_file, readable_mdpa=True)

        self.assertTrue(filecmp.cmp(self.write_mesh_readable_ref_file, self.test_file))

        with open(self.test_file, "w") as test_file:
            obj2test.WriteMesh(test_file)

        self.assertTrue(filecmp.cmp(self.write_mesh_ref_file, self.test_file))

        # TODO test the unreadable version

    def _test_WriteMeshInfo(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with open(self.test_file, "w") as test_file:
            with self.assertRaisesRegex(RuntimeError,"MeshSubmodelPart is not properly initialized!"):
                obj2test.WriteMeshInfo(test_file)

        self._fill_smp(obj2test)
        obj2test.Assemble()

        with open(self.test_file, "w") as test_file:
            obj2test.WriteMeshInfo(test_file)

        self.assertTrue(filecmp.cmp(self.write_mesh_info_ref_file, self.test_file))

    def test_CheckIsAssembled(self):
        obj2test = kratos_utils.MeshSubmodelPart()
        obj2test.is_properly_initialized = True
        with self.assertRaisesRegex(RuntimeError,"MeshSubmodelPart was not assembled!"):
            obj2test.__CheckIsAssembled()

    def test_CheckIsProperlyInitialized(self):
        obj2test = kratos_utils.MeshSubmodelPart()
        with self.assertRaisesRegex(RuntimeError,"MeshSubmodelPart is not properly initialized!"):
            obj2test.__CheckIsProperlyInitialized()

    def test_ValidateSMPInfoDict(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        # these are the default values
        default_smp_info_dict = {
            "smp_name"      : "PLEASE_SPECIFY_SUBMODELPART_NAME",
            "smp_file_name" : "",
            "smp_file_path" : ""
        }

        dict2validate = {}
        obj2test.__ValidateSMPInfoDict(dict2validate)

        self.assertDictEqual(default_smp_info_dict, dict2validate)

    def test_ValidateMeshDict(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        # these are the default values
        default_mesh_dict = {
            "entity_creation" : {},
            "write_smp"       : True
        }

        dict2validate = {}
        obj2test.__ValidateMeshDict(dict2validate)

        self.assertDictEqual(default_mesh_dict, dict2validate)


if __name__ == '__main__':
    unittest.main()
