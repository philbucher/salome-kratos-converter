from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

from KratosMultiphysics import *
from KratosMultiphysics.FluidDynamicsApplication import *
from KratosMultiphysics.ExternalSolversApplication import *
from KratosMultiphysics.MeshingApplication import *

######################################################################################
######################################################################################
######################################################################################

## Parse the ProjectParameters
parameter_file = open("ProjectParameters.json",'r')
ProjectParameters = Parameters( parameter_file.read())

## Get echo level and parallel type
verbosity = ProjectParameters["problem_data"]["echo_level"].GetInt()
parallel_type = ProjectParameters["problem_data"]["parallel_type"].GetString()

## Import KratosMPI if needed
if (parallel_type == "MPI"):
    import KratosMultiphysics.mpi as KratosMPI

## Fluid model part definition
main_model_part = ModelPart(ProjectParameters["problem_data"]["model_part_name"].GetString())
main_model_part.ProcessInfo.SetValue(DOMAIN_SIZE, ProjectParameters["problem_data"]["domain_size"].GetInt())

## Solver construction
import python_solvers_wrapper_fluid
solver = python_solvers_wrapper_fluid.CreateSolver(main_model_part, ProjectParameters)

solver.AddVariables()

## Read the model - note that SetBufferSize is done here
solver.ImportModelPart()

## Add AddDofs
solver.AddDofs()

## Initialize GiD  I/O
if (parallel_type == "OpenMP"):
    from gid_output_process import GiDOutputProcess
    gid_output = GiDOutputProcess(solver.GetComputingModelPart(),
                                  ProjectParameters["problem_data"]["problem_name"].GetString() ,
                                  ProjectParameters["output_configuration"])
elif (parallel_type == "MPI"):
    from gid_output_process_mpi import GiDOutputProcessMPI
    gid_output = GiDOutputProcessMPI(solver.GetComputingModelPart(),
                                     ProjectParameters["problem_data"]["problem_name"].GetString() ,
                                     ProjectParameters["output_configuration"])

gid_output.ExecuteInitialize()

## Creation of Kratos model
FluidModel = Model()
FluidModel.AddModelPart(main_model_part)

## Get the list of the skin submodel parts in the object Model
for i in range(ProjectParameters["solver_settings"]["skin_parts"].size()):
    skin_part_name = ProjectParameters["solver_settings"]["skin_parts"][i].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(skin_part_name))

## Get the list of the no-skin submodel parts in the object Model (results processes and no-skin conditions)
for i in range(ProjectParameters["solver_settings"]["no_skin_parts"].size()):
    no_skin_part_name = ProjectParameters["solver_settings"]["no_skin_parts"][i].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(no_skin_part_name))

## Get the list of the initial conditions submodel parts in the object Model
for i in range(ProjectParameters["initial_conditions_process_list"].size()):
    initial_cond_part_name = ProjectParameters["initial_conditions_process_list"][i]["Parameters"]["model_part_name"].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(initial_cond_part_name))

## Get the gravity submodel part in the object Model
for i in range(ProjectParameters["gravity"].size()):
    gravity_part_name = ProjectParameters["gravity"][i]["Parameters"]["model_part_name"].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(gravity_part_name))

## Print model_part and properties
if(verbosity > 1):
    print("")
    print(main_model_part)
    for properties in main_model_part.Properties:
        print(properties)

## Processes construction
import process_factory
# "list_of_processes" contains all the processes already constructed (boundary conditions, initial conditions and gravity)
# Note 1: gravity is firstly constructed. Outlet process might need its information.
# Note 2: conditions are constructed before BCs. Otherwise, they may overwrite the BCs information.
list_of_processes =  process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["gravity"] )
list_of_processes += process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["initial_conditions_process_list"] )
list_of_processes += process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["boundary_conditions_process_list"] )
list_of_processes += process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["auxiliar_process_list"] )

if(verbosity > 1):
    for process in list_of_processes:
        print(process)

## Processes initialization
for process in list_of_processes:
    process.ExecuteInitialize()

## Solver initialization
solver.Initialize()

#TODO: think if there is a better way to do this
fluid_model_part = solver.GetComputingModelPart()

## Stepping and time settings
# Dt = ProjectParameters["problem_data"]["time_step"].GetDouble()
start_time = ProjectParameters["problem_data"]["start_time"].GetDouble()
end_time = ProjectParameters["problem_data"]["end_time"].GetDouble()

time = start_time
step = 0
out = 0.0

gid_output.ExecuteBeforeSolutionLoop()

for process in list_of_processes:
    process.ExecuteBeforeSolutionLoop()

## Writing the full ProjectParameters file before solving
if ((parallel_type == "OpenMP") or (KratosMPI.mpi.rank == 0)) and (verbosity > 0):
    f = open("ProjectParametersOutput.json", 'w')
    f.write(ProjectParameters.PrettyPrintJsonString())
    f.close()

while(time <= end_time):

    Dt = solver.ComputeDeltaTime()
    step += 1
    time = time + Dt
    main_model_part.CloneTimeStep(time)

    if (parallel_type == "OpenMP") or (KratosMPI.mpi.rank == 0):
        print("")
        print("STEP = ", step)
        print("TIME = ", time)

    for process in list_of_processes:
        process.ExecuteInitializeSolutionStep()

    gid_output.ExecuteInitializeSolutionStep()

    if(step >= 3):
        solver.Solve()

    for process in list_of_processes:
        process.ExecuteFinalizeSolutionStep()

    gid_output.ExecuteFinalizeSolutionStep()

    #TODO: decide if it shall be done only when output is processed or not
    for process in list_of_processes:
        process.ExecuteBeforeOutputStep()

    if gid_output.IsOutputStep():
        gid_output.PrintOutput()

    for process in list_of_processes:
        process.ExecuteAfterOutputStep()

    out = out + Dt

for process in list_of_processes:
    process.ExecuteFinalize()

gid_output.ExecuteFinalize()
