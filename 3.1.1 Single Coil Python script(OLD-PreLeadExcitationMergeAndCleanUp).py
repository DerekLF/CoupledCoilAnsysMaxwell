## 3D coil generator Ansys Maxwell V1.0, main coil
## The goal of this code is to reliably and dynamically generate a perfectly rounded or segmented spiral coil. Ideally with multiple layers and windings.

## 1. Setup Ansys Maxwell communication and import libraries
from ansys.aedt.core import Maxwell3d
import datetime
import math
# Attach to the ACTIVE project & session
m3d = Maxwell3d()

# Generate unique design name
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
design_name = f"CoupledCoilDesign_{timestamp}"

# Insert new Maxwell 3D design into current project
m3d.insert_design(design_name)

print(f"############################################################################")
print(f"Active project: {m3d.project_name}")
print(f"New design created: {m3d.design_name}")
m3d.autosave_disable()

## 2. Intiallize all used variables, but create new ones dont use existing ones, and generate new design inside existing project.

## Design wide variables
design_var = {
## Boundary/region related variables
"X_Boundary": "30mm",
"Y_Boundary": "30mm",
"Z_Boundary": "10mm",   

##mesh optimizations 
"CircleSegments": "8",
"CoilSegments": "1200",

## Coil Wire variables
"WireDiameter": "0.1mm",
"WirePitch": "WireDiameter*2.01",
"CoilTerm_Current": "1A"
}
for k, v in design_var.items():
    m3d[k] = v
print(f"Design variables initialized")
## Main Coil Variables
MC_var = {
"Main_InnerDiameter": "14mm",
"Main_Turns": "15",
"Main_Stack": "2"
}
for k, v in MC_var.items():
    m3d[k] = v
print(f"Main coil variables initialized")
## Secondary Coil Variables
Sec_var = {
"Sec_InnerDiameter": "7mm",
"Sec_Turns": "10",
"Sec_Stack": "2",
"Sec_Zoffset": "2mm"
}
for k, v in Sec_var.items():
    m3d[k] = v
print(f"Secondary coils variables initialized")
print(f"")
print(f"Adjust design properties/variables and press enter to continue")

#input(f"Edit base variables, then press ENTER...")

### PLacement and CS variables
Placement_var = {
##Main coil at origin, no phi change
"Main_X": "0mm",
"Main_Y": "0mm",
"Main_Z": "0mm",
"Main_Phi": "0deg",

#Secondary coils
"Sec1_X": "Main_InnerDiameter/2", "Sec1_Y": "0mm", "Sec1_Z": "Sec_Zoffset",
"Sec1_Phi" : "0deg",
"Sec2_X": "Main_InnerDiameter/2*cos(120deg)", "Sec2_Y": "Main_InnerDiameter/2*sin(120deg)", "Sec2_Z": "Sec_Zoffset",
"Sec2_Phi" : "90deg",
"Sec3_X": "Main_InnerDiameter/2*cos(240deg)", "Sec3_Y": "Main_InnerDiameter/2*sin(240deg)",  "Sec3_Z": "Sec_Zoffset",
"Sec3_Phi" : "270deg"
}
for k, v in Placement_var.items():
    m3d[k] = v
print(f"Relative CS variables initialized and calculated")

## 4. Create the 4 Coordinate systems for each Coil.

def create_cs(name, x, y, z, phi):
    print(f"Created ",name, " Relative Coordinate System")
    return m3d.modeler.create_coordinate_system(
        origin=[x, y, z],
        name=name,
        phi=phi,
        mode="zyz",
        view="XY"
    )

# Main coil CS
create_cs("CS_Main", "Main_X", "Main_Y", "Main_Z", "Main_Phi")

# Secondary coils CS
create_cs("CS_Sec1", "Sec1_X", "Sec1_Y", "Sec1_Z", "Sec1_Phi")
create_cs("CS_Sec2", "Sec2_X", "Sec2_Y", "Sec2_Z", "Sec2_Phi")
create_cs("CS_Sec3", "Sec3_X", "Sec3_Y", "Sec3_Z", "Sec3_Phi")

## 3. Generate spiral(s) based on coil layer count. Even is right handed, odd is left handed.
def create_multilayer_spiral(
    base_name,
    cs_name,
    inner_dia,
    turns,
    stack
):

    spirals = []

    for layer in range(int(m3d[stack])):
        
        #reverse orientation of the coil layers every other one
        reverse = (layer % 2 == 1)

        #Calculate Z offset for each coil.
        z_expr = f"{layer}*WirePitch"

        t_end = f"2*pi*{turns}"

        if not reverse:
            x_expr = f"({inner_dia}/2 + (WirePitch/(2*pi))*_t)*cos(_t)"
            y_expr = f"({inner_dia}/2 + (WirePitch/(2*pi))*_t)*sin(_t)"
        else:
            x_expr = f"({inner_dia}/2 + (WirePitch/(2*pi))*_t)*cos(-_t)"
            y_expr = f"({inner_dia}/2 + (WirePitch/(2*pi))*_t)*sin(-_t)"
        #flip coil orientation by turning _t negative.
        
        m3d.modeler.set_working_coordinate_system(cs_name)

        name = f"{base_name}_L{layer}"
        #Create coil with name name.
        spiral = m3d.modeler.create_equationbased_curve(
            x_t=x_expr,
            y_t=y_expr,
            z_t=z_expr,
            t_start="0",
            t_end=t_end,
            num_points="CoilSegments",
            name=name,
            xsection_type="circle",
            xsection_width="2*WireDiameter",
            xsection_sum_seg="CircleSegments"
        )
        print(f"generated spiral: ", name) 
        spirals.append(spiral)
    return spirals

main_spirals = create_multilayer_spiral(
    base_name="Main",
    cs_name="CS_Main",
    inner_dia="Main_InnerDiameter",
    turns="Main_Turns",
    stack="Main_Stack"
)

sec_spirals = []

for i in range(1, 4):
    spirals = create_multilayer_spiral(
        base_name=f"Sec{i}",
        cs_name=f"CS_Sec{i}",
        inner_dia="Sec_InnerDiameter",
        turns="Sec_Turns",
        stack="Sec_Stack"
    )
    sec_spirals.extend(spirals)
    
## 4. Calculate intersection spots and place cylinder
print(f"Calculating spiral intersection points")
# This is yet to be upgraded to more then 2 layers.
def create_IC (
name,
cs_name,
inner_dia,
stack
): 
    ICs=[]
    m3d.modeler.set_working_coordinate_system(cs_name)
    
    x=f"{inner_dia}/2"
    y=0
    z="-WireDiameter"
    IC=m3d.modeler.create_cylinder(
    orientation="z",
    origin=[x,y,z],
    radius="WireDiameter",
    height = "WirePitch*2",
    num_sides = "CircleSegments",
    name=f"{name}_IC"
    )
    ICs.append(IC)
    return ICs

create_IC("Main", "CS_Main", "Main_InnerDiameter", "Main_Stack")
create_IC("Sec1", "CS_Sec1", "Sec_InnerDiameter", "Sec_Stack")
create_IC("Sec2", "CS_Sec2", "Sec_InnerDiameter", "Sec_Stack")
create_IC("Sec3", "CS_Sec3", "Sec_InnerDiameter", "Sec_Stack")
## 5. Calculate lead positions and generate leads, only when number of coil layers is even. throw error in odd mode
#Box is 15x15x10. 
#############################################################################################################################
#############################################################################################################################
#############################################################################################################################
#############################################################################################################################
#Maybe join Create_lead and assign excitaion together, as it does something similar at the same spot.
#############################################################################################################################
#############################################################################################################################
#############################################################################################################################
#############################################################################################################################
def create_lead (
name,
cs_name,
X_offset,
inner_dia,
stack,
turns
):
    m3d.modeler.set_working_coordinate_system(cs_name)
    #bot is -Y=IN top is +Y=OUT
    x0=f"{inner_dia}/2+WirePitch*{turns}"
    x1=f"X_Boundary/2-{inner_dia}/2-WirePitch*{turns}-{X_offset}"
    # why can I can't change "{inner_dia}/2+WirePitch*{turns}" for x0 is a really good question
    
    lead_in = m3d.modeler.create_box(
    origin=[x0,"-WireDiameter","-WireDiameter/2"],
    sizes=[x1,"WireDiameter","WireDiameter"],
    name=f"{name}_Lead_In"
    )
    lead_out = m3d.modeler.create_box(
    origin=[x0,"WireDiameter","-WireDiameter/2+WirePitch"],
    sizes=[x1,"WireDiameter","WireDiameter"],
    name=f"{name}_Lead_Out"
    )
    print(f"Created Input/Output leads for {name}")
    return lead_in, lead_out

create_lead("Main", "CS_Main", "Main_X", "Main_InnerDiameter", "Main_Stack", "Main_Turns")
create_lead("Sec1", "CS_Sec1", "Sec1_X", "Sec_InnerDiameter", "Sec_Stack", "Sec_Turns")
## Change Sec2_Y to X if we ever intend to make it easier for all of us. and have the leads stretch across the X axis.
create_lead("Sec2", "CS_Sec2", "Sec2_Y", "Sec_InnerDiameter", "Sec_Stack", "Sec_Turns")
create_lead("Sec3", "CS_Sec3", "Sec3_Y*-1", "Sec_InnerDiameter", "Sec_Stack", "Sec_Turns")

## 6. Unite full model and assign material

def unite_coil(name):
    objects = [
    f"{name}_L0",
    f"{name}_L1",
    f"{name}_IC",
    f"{name}_Lead_In",
    f"{name}_Lead_Out"
    ]
    coil=m3d.modeler.unite(objects)
    m3d.modeler.objects[f"{name}_L0"].name = f"{name}_Coil"
    m3d.modeler.objects[f"{name}_Coil"].material_appearance = True 
    print(f"{name}_Coil Unified and ready for action")
    
    return coil

def assign_material (name):
    print(f"{name}_Coil Copper assigned")
    m3d.assign_material(
    assignment=name,
    material="copper" 
)

unite_coil("Main")
assign_material("Main_Coil")

for i in range(1,4):
    unite_coil(f"Sec{i}")
    assign_material(f"Sec{i}_Coil")


## 7. Generate region and assign excitations.
print(f"Performing behind the scene magic to create a region. . .")

def create_region(name, cs_name):
    m3d.modeler.set_working_coordinate_system(f"{cs_name}")
    region = m3d.modeler.create_region(
        pad_value=["X_Boundary/2",
        "-X_Boundary/2",
        "Y_Boundary/2",
        "-Y_Boundary/2",
        "Z_Boundary/3*2",
        "-Z_Boundary/3"],
        pad_type= "Absolute Position",
        name=f"{name}"
    )
return region

create_region("region", "CS_Main")


def assign_excitation (
name,
cs_name,
Boundary,
inner_dia,
stack,
turns
):
    print(f"Assigning {name}_Coils excitations")
    m3d.modeler.set_working_coordinate_system(cs_name)
    #bot is -Y=in top is +Y=out
    x0 = Boundary 
    z0 = "-WireDiameter/2"
    x1 = Boundary
    z1 = "-WireDiameter/2+WirePitch"
    


    in_face = m3d.modeler.get_faceid_from_position(x0,  "-WireDiameter",z0)
    out_face = m3d.modeler.get_faceid_from_position(x1,  "WireDiameter",z1)
    
    term_in = m3d.assign_coil_terminal(
    assignment=[in_face],
    name = f"{name}_Terminal_In"
    )
    term_out = m3d.assign_coil_terminal(
    assignment=[out_face],
    name = f"{name}_Terminal_Out"
    )

    return term_in, term_out

## 8. Have fun


CoilTerm_Current