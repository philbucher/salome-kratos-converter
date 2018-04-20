import unittest
import sys
import os
import filecmp
sys.path.insert(0, '../')
import kratos_io_utilities as kratos_utils
import global_utilities as global_utils


class TestKratosEntity(unittest.TestCase):

    def _test_GetID(self, class2test):
        obj2test = class2test(
            origin_entity=203, name="SomeName", property_ID=5)

        with self.assertRaises(Exception):
            obj2test.GetID()

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

    def _execute_entity_tests(self, class2test):
        self._test_GetID(class2test)
        # self._test_GetWriteLineNode(class2test)
        # self._test_GetWriteLineGeomEntity(class2test)

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

    def test_MainModelPart(self):
        obj2test = kratos_utils.MainModelPart()

        serialized_obj = obj2test.Serialize()
        self.assertEqual({}, serialized_obj)



class MeshSubmodelPart(unittest.TestCase):

    def setUp(self):
        self.write_mesh_ref_file = os.path.join(os.getcwd(), "MeshSubmodelPart_WriteMesh.ref")
        self.write_mesh_info_ref_file = os.path.join(os.getcwd(), "MeshSubmodelPart_WriteMeshInfo.ref")
        self.test_file = os.path.join(os.getcwd(), "test_file.tmp")

        self.nodes = {1: [0.0, 0.0, 0.0], 2: [5.0, 0.0, 0.0], 3: [5.0, 1.0, 0.0],
                      4: [0.0, 1.0, 0.0], 5: [0.2, 0.0, 0.0], 6: [0.4, 0.0, 0.0]}

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

        # self.assertEqual(6, SmpToTest.NumberOfNodes())
        # self.assertEqual(8, SmpToTest.NumberOfElements())
        # self.assertEqual(6, SmpToTest.NumberOfConditions())

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

    def test_Serialize(self):
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


    def test_GetGeomEntites(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(AttributeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.GetGeomEntites()

    def test_Assemble(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.Assemble()

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

    # def test_NumberOfNodes(self):
    #     obj2test = kratos_utils.MeshSubmodelPart()

    #     with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
    #         obj2test.NumberOfNodes()

    # def test_NumberOfElements(self):
    #     obj2test = kratos_utils.MeshSubmodelPart()

    #     with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
    #         obj2test.NumberOfElements()

    # def test_NumberOfConditions(self):
    #     obj2test = kratos_utils.MeshSubmodelPart()

    #     with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
    #         obj2test.NumberOfConditions()

    def test_GetFileName(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.GetFileName()

    def test_GetFilePath(self):
        obj2test = kratos_utils.MeshSubmodelPart()

        with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
            obj2test.GetFilePath()

    # def test_WriteMesh(self):
    #     obj2test = kratos_utils.MeshSubmodelPart()

    #     with open(self.test_file, "w") as test_file:
    #         with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
    #             obj2test.WriteMesh(test_file)

    #     self._fill_smp(obj2test)
    #     obj2test.Assemble()

    #     nodes, elements, conditions = obj2test.GetMesh()

    #     # Hackish way to assign new IDs, bcs Elements and Conditions throw if the didn't get assigned a new ID!
    #     index = 1
    #     for elem_name in sorted(elements.keys()):
    #         new_elems = elements[elem_name]
    #         for i in range(len(new_elems)):
    #             new_elems[i].new_ID = index
    #             index +=1

    #     index = 1
    #     for elem_name in sorted(conditions.keys()):
    #         new_conds = conditions[elem_name]
    #         for i in range(len(new_conds)):
    #             new_conds[i].new_ID = index
    #             index +=1

    #     with open(self.test_file, "w") as test_file:
    #         obj2test.WriteMesh(test_file)

    #     self.assertTrue(filecmp.cmp(self.write_mesh_ref_file, self.test_file))
    #     os.remove(self.test_file)

    # def test_WriteMeshInfo(self):
    #     obj2test = kratos_utils.MeshSubmodelPart()

    #     with open(self.test_file, "w") as test_file:
    #         with self.assertRaises(RuntimeError): # Throws bcs the obj2test is not properly initialized!
    #             obj2test.WriteMeshInfo(test_file)

    #     self._fill_smp(obj2test)
    #     obj2test.Assemble()

    #     with open(self.test_file, "w") as test_file:
    #         obj2test.WriteMeshInfo(test_file)

    #     self.assertTrue(filecmp.cmp(self.write_mesh_info_ref_file, self.test_file))
    #     os.remove(self.test_file)


if __name__ == '__main__':
    unittest.main()
