# Update 05.03.2020:
The new version can be found [here](https://github.com/philbucher/KratosSalomePlugin). Check [here](https://github.com/philbucher/KratosSalomePlugin/issues/32) for the current status.

# Update 21.02.2019:
I used this for a while now and it is working nicely for many applications.
I noticed however that it is not possible to have overlapping domains, elements and conditions will be created twice, even though they should not be! Now while this has not been a problem for all "standard"-cases, it is still is a bug that unfortunately cannot be fixed without major effort.
Due to this I have decided to take the opportunity to rewrite the entire converter to be able to provide this feature and also clean things up a lot.
The new version will be working as a full interface in Salome.

**Therefore this repository will no longer be maintained!**

# SALOME-Kratos Converter
```
  ___   _   _    ___  __  __ ___    _  _____    _ _____ ___  ___
 / __| /_\ | |  / _ \|  \/  | __|__| |/ / _ \  /_\_   _/ _ \/ __|
 \__ \/ _ \| |_| (_) | |\/| | _|___| ' <|   / / _ \| || (_) \__ \
 |___/_/ \_\____\___/|_|  |_|___|  |_|\_\_|_\/_/ \_\_| \___/|___/
  / __|___ _ ___ _____ _ _| |_ ___ _ _
 | (__/ _ \ ' \ V / -_) '_|  _/ -_) '_|
  \___\___/_||_\_/\___|_|  \__\___|_|
```
This is a small tool to create mdpa-files form SALOME dat-files.

It does/can **NOT** replace GiD! You still have to create a case in GiD and then exchange the *.mdpa-file.

## Usage

### In SALOME
1. Create a case in SALOME, including the mesh
2. Create a SubMesh for each SubModelPart (e.g. Inlet, Dirichlet-BC, ...)
3. Export the Mesh and each SubMesh to a *.dat-file

---

**NOTE:** The converter can be used either directly in python, OR using the GUI, as explained in the following

---
### Using the converter directly directly from Python
The converter can be directly used from python, see [this example](https://github.com/philbucher/salome-kratos-converter/tree/master/Examples/use_converter_from_python). This way the mesh generation can be done automatically, when used together with the "dump script" functionality of Salome.

---
### Using the GUI of the Converter
Note that this requires the `tkinter` module of Python, which should be available by default
1. Launch the Converter with `python3 converter_salome_kratos.py`
2. Read each *.dat-file with the **Read Mesh** Button
    * You are offered a selection of entities that is present in the *.dat-file
    * _double-click_ the entity you want to use.
    * Now you can select
        * Entity Type
        * Name of Entity (Names available in Kratos can be selected from a list)
        * Property ID (legacy, currently only needed for Fluid cases)
3. After reading every mesh file, create the *.mdpa-file with the **Write MDPA** Button

#### Mesh Refinement
If you have a set of files on which you want to apply the same operations (e.g. Mesh Refinement), then you can export a "Converter Scheme" from an existing case.

If you import this scheme, you will be asked to provide a set of files on which the same operations are applied.

An example can be found under `/Examples/Fluid/Test_1_2D.salome/dat-files/`

#### Examples
Check out the **Examples** Folder to see how the Converter can be used.

#### Additional Information:
* Every Entry can be edited by _double-clicking_ on it
* Every Entry can be deleted with _delete_
* Cases can be saved and loaded
* Commonly used shortcuts are supported:
    * _Ctrl - n_ : New Project
    * _Ctrl - o_ : Open Project
    * _Ctrl - s_ : Save Project
    * _Ctrl - Shift - s_ : Save Project as
    * _Esc_ : Close Window (except main window)
    * _Ctrl - r_ : Read Mesh
    * _Ctrl - i_ : Import Converter Scheme
    * _Ctrl - e_ : Export Converter Scheme
* If you want to create Nodal entites (e.g. _NodalConcentratedElement_ or _PointCondition_), create and export a group of Nodes in SALOME. Read this file in the same way and _double-click_ on _Nodes_ to select what you want to assign.

---

## Enhanced Functionalities:
At the beginning of the file `global_utilities.py`, the user can select more advanced options:
* DEBUG: This flag enables debugging, which includes:
    * DEBUG output in logging
    * In the mdpa-file, each geometrical entity (Elements and Conditions) is appended with the ID of the SALOME entity it was created with
    * When a project is saved, the json-file is formatted in a readable way
* LOG_TIMING: This flag enables timing output in logging
* READABLE_MDPA: Use this to get a nicely formatted mdpa file. Works in most cases, but files are larger (~20%) and mdpa writing takes slightly more time


## Troubleshooting:
- Problem: Negative Volume when using tetrahedral elements. Try changing the orientation of the geometry (in GEOM module: repair => change orinetation) or the meh itself (in MESH module: Modification => orientation)
