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

It does/can **NOT** replace GiD!

# Usage
## In SALOME
1. Create a case in SALOME, including the mesh
2. Create a SubMesh for each SubModelPart (e.g. Inlet, Dirichlet-BC, ...)
3. Export the Mesh and each SubMesh to a *.dat-file
## In the Converter
1. Launch the Converter with `python3 converter_salome_kratos.py`
2. Read each *.dat-file with the **Read Mesh** Button
    * You are offered a selection of entities that is present in the *.dat-file
    * _double-click_ the entity you want to use.
    * Now you can select 
        * Entity Type
        * Name of Entity (Names available in Kratos can be selected from a list)
        * Property ID (legacy, atm only needed for Fluid cases)
3. After reading every mesh file, create the *.mdpa-file with the **Write MDPA** Button

## Mesh Refinement
If you have a set of files on which you want to apply the same operations (e.g. Mesh Refinement), then you can export a "Converter Scheme" from an existing case.

If you import this scheme, you will be asked to provide a set of files


## Additional Information:
* Every Entry can be edited by _double-clicking_ on it
* Every Entry can be deleted with _delete_
* Cases can be saved and loaded
* Commonly used shortcuts such are supported:
    * _Ctrl - n_ : New Project
    * _Ctrl - o_ : Open Project
    * _Ctrl - s_ : Save Project
    * _Ctrl - Shift - s_ : Save Project as
    * _Ecs_ : Close Window (except main window)
    * _Ctrl - r_ : Read Mesh
    * _Ctrl - i_ : Import Converter Scheme
    * _Ctrl - e_ : Export Converter Scheme