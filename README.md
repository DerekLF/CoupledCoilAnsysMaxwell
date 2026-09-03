# Ansys Maxwell 3D Coupled Coil Generator

An automated Python script using the PyAEDT library to dynamically generate, connect, and excite multi-layer spiral coils in Ansys Maxwell 3D. 

The primary goal of this tool is to build perfectly rounded, equation-based spiral coils with customizable layers, windings, and dynamic routing. It generates one main central coil and three offset secondary coils, assigns copper materials, and sets up boundary regions and coil terminals.

## Features
* **Dynamic Generation:** Uses equation-based curves to generate spirals based on user-defined turns, pitch, and wire diameter.
* **Multi-Layer Routing:** Automatically reverses coil orientation (chirality) for alternating layers to allow continuous routing.
* **Automated Interconnects:** Generates intersection cylinders to bridge alternating coil layers.
* **Relative Coordinate Systems:** Secondary coils are placed dynamically using parametric coordinate systems relative to the main coil's dimensions.
* **Excitation Setup:** Automatically calculates face coordinates for leads and assigns positive/negative coil terminals.

## Prerequisites
* **Ansys Electronics Desktop (AEDT):** Maxwell 3D installed and licensed.
* **Python Environment:** Compatible with the PyAEDT library.
* **Libraries:** `ansys.aedt.core`, `datetime`, `math`.

## Usage
1. Open Ansys Electronics Desktop and ensure a project is open.
2. Run the script via an external IDE or the AEDT script console connected to your active session.
3. The script initializes and pushes all parameters into Ansys Maxwell as **Design Variables**.
4. If you uncomment the interactive pause line (`#input(f"Edit base variables, then press ENTER...")`) in the script, execution will pause after variable initialization. 
5. While the script is paused, navigate to the **Design Properties** window in the Maxwell GUI to modify your parameters (such as `Main_Turns`, `WireDiameter`, or `Main_InnerDiameter`) dynamically before geometry generation begins.
6. Press **Enter** in your console to resume execution, and the script will build the model based on your updated variables.

## Known Limitations

While the script dynamically generates spirals, several functions contain hardcoded limitations that prevent fully parametric scaling:

* **Hardcoded Union Operations:** The `unite_coil` function explicitly looks for layers `L0` through `L3` and specific intersection cylinders (`0_IC` to `2_IC`). If you change the `stack` variable to anything other than 4, the script will crash during the boolean unite operation.
* **Restricted Layer Count:** The `create_IC` function is explicitly hardcoded to support only 2 or 4 layers. The logic for bridging layers does not scale dynamically to arbitrary odd or higher even numbers.
* **Hardcoded Lead Offsets:** In the `create_lead` function, variables like `ly0 = "-WireDiameter"` restrict the leads to a specific geometric plane, which may break if the spiral generation equations are modified.

## Missing Features

The following Maxwell operations are defined in the script's comments but are not yet implemented in the code:

* **Winding Assignments:** The script creates positive and negative terminals (`assign_coil`), but it never groups these terminals into a Winding or applies the defined `"CoilTerm_Current": "1A"`. 
* **Solution Setup:** Step 8 mentions creating an initial solution setup, but no `m3d.create_setup()` function is called. The solver type (e.g., Eddy Current or Magnetostatic) is also never explicitly defined.
* **Boundary Conditions:** A region is created, but no specific boundary conditions (like Radiation or Zero Tangential H-field) are assigned to the region's faces.
* **Mesh Operations:** Mesh optimization variables (`CircleSegments`, `CoilSegments`) are defined, but no advanced PyAEDT mesh refinement operations are applied to the coil bodies.
