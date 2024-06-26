# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2018 kbwbe                                              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import os
import FreeCAD, FreeCADGui
from PySide import QtGui
#from a2p_translateUtils import *
import a2plib
from a2plib import (
    path_a2p,
    Msg,
    DebugMsg,
    A2P_DEBUG_LEVEL,
    A2P_DEBUG_1,
    PARTIAL_SOLVE_STAGE1,
    )
from a2p_dependencies import Dependency
from a2p_rigid import Rigid

SOLVER_MAXSTEPS = 50000
translate = FreeCAD.Qt.translate

# SOLVER_CONTROLDATA has been replaced by SolverSystem.getSolverControlData()
#SOLVER_CONTROLDATA = {
#    #Index:(posAccuracy,spinAccuracy,completeSolvingRequired)
#    1:(0.1,0.1,True),
#    2:(0.01,0.01,True),
#    3:(0.001,0.001,True),
#    4:(0.0001,0.0001,False),
#    5:(0.00001,0.00001,False)
#    }

SOLVER_POS_ACCURACY = 1.0e-1  # gets to smaller values during solving
SOLVER_SPIN_ACCURACY = 1.0e-1 # gets to smaller values during solving

SOLVER_STEPS_CONVERGENCY_CHECK = 2000 #200
SOLVER_CONVERGENCY_FACTOR = 0.99
SOLVER_CONVERGENCY_ERROR_INIT_VALUE = 1.0e+20

#------------------------------------------------------------------------------

class SolverSystem():
    """
    class Solversystem():
    A new iterative solver, inspired by physics.
    Using "attraction" of parts by constraints
    """

    def __init__(self):
        self.doc = None
        self.stepCount = 0
        self.rigids = []        # list of rigid bodies
        self.linkinfo = []
        self.alllinkinfo = []
        self.constraints = []
        self.objectNames = []
        self.mySOLVER_SPIN_ACCURACY = SOLVER_SPIN_ACCURACY
        self.mySOLVER_POS_ACCURACY = SOLVER_POS_ACCURACY
        self.lastPositionError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
        self.lastAxisError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
        self.convergencyCounter = 0
        self.status = "created"
        self.partialSolverCurrentStage = 0
        self.currentstage = 0
        self.solvedCounter = 0
        self.maxPosError = 0.0
        self.maxAxisError = 0.0
        self.maxSingleAxisError = 0.0
        self.unmovedParts = []
        self.baselink = False
        # Initialize cache dictionary to store positions of rigids and their solutions
        self.rigid_positions_cache = {}

    def clear(self):
        for r in self.rigids:
            r.clear()
        self.stepCount = 0
        self.rigids = []
        self.constraints = []
        self.objectNames = []
        self.partialSolverCurrentStage = PARTIAL_SOLVE_STAGE1

    def getSolverControlData(self):
        if a2plib.SIMULATION_STATE:
            # do less accurate solving for simulations...
            solverControlData = {
                #Index:(posAccuracy,spinAccuracy,completeSolvingRequired)
                1:(0.1,0.1,True)
                }
        else:
            solverControlData = {
                #Index:(posAccuracy,spinAccuracy,completeSolvingRequired)
                1:(0.1,0.1,True),
                2:(0.01,0.01,True),
                3:(0.001,0.001,False),
                4:(0.0001,0.0001,False),
                5:(0.00001,0.00001,False)
                }
        return solverControlData


    def getRigid(self,objectName):
        """Get a Rigid by objectName."""
        rigs = [r for r in self.rigids if r.objectName == objectName]
        if len(rigs) > 0: return rigs[0]
        return None

    def removeFaultyConstraints(self, doc):
        """
        Remove constraints where referenced objects do not exist anymore.
        """
        constraints = [ obj for obj in doc.Objects if 'ConstraintInfo' in obj.Content]

        faultyConstraintList = []
        for c in constraints:
            constraintOK = True
            for attr in ['Object1','Object2']:
                objectName = getattr(c, attr, None)
                o = doc.getObject(objectName)
                if o is None:
                    constraintOK = False
            if not constraintOK:
                faultyConstraintList.append(c)

        if len(faultyConstraintList) > 0:
            for fc in faultyConstraintList:
                FreeCAD.Console.PrintMessage(translate("A2plus", "Remove faulty constraint '{}'").format(fc.Label) + "\n")
                doc.removeObject(fc.Name)

    def export_obj_w_autoscale(self):
        for shape in ShapeList1:
            filesize = 100000000
            scale = 0.1
            while filesize > 400000:

                Draft.clone(FreeCAD.ActiveDocument.getObject(shape))
                if shape != "Body":
                    shapemod = shape[2:]
                    modstop = shapemod.find("_")
                    shapemod = shapemod[:modstop]
                else:
                    shapemod = FreeCAD.ActiveDocument.Label

                FreeCAD.ActiveDocument.getObject("Clone").Scale = (scale, scale, scale)

                scale = scale / 10

                MeshExportName = str(FreeCAD.ActiveDocument.Label) + "/" + shapemod + ".obj"
                filesize = os.path.getsize(str(FreeCAD.ActiveDocument.Label) + "/" + shapemod + ".obj")

                FreeCAD.ActiveDocument.recompute()
                __objs__ = []
                __objs__.append(FreeCAD.ActiveDocument.getObject("Clone"))
                Mesh.export(__objs__, MeshExportName)
                del __objs__
                FreeCAD.ActiveDocument.removeObject('Clone')

    def export_obj_no_autoscale(self, shape):
        import Mesh
        import Draft
        MeshExportName = "C:/Users/" + str(os.getlogin()) + "/" + str(FreeCAD.ActiveDocument.Label) + "/" + shape + ".obj"
        __objs__ = []
        __objs__.append(FreeCAD.ActiveDocument.getObject(shape))
        Mesh.export(__objs__, MeshExportName)
        del __objs__

    def prettify_urdf(self, urdf_file):
        """
        Prettify the URDF file by adding newlines after each tag.

        Parameters:
            urdf_file (str): The path to the URDF file.

        Returns:
            None
        """
        import xml.dom.minidom as mini

        totalPath = "C:\\Users\\" + str(os.getlogin()) + "\\" + str(FreeCAD.ActiveDocument.Label) + "\\" + urdf_file
        # Parse the URDF file
        doc = mini.parse(totalPath)

        # Add indentation
        pretty_urdf_content = doc.toprettyxml(indent="    ")

        # Write the prettified URDF back to the file
        with open(totalPath, "w") as f:
            f.write(pretty_urdf_content)

    def create_urdf(self, base_link_name, urdf_file):
        # """
        # Create a URDF file with a single base link and no joints, and export the mesh as an OBJ file.
        #
        # Parameters:
        #     base_link_name (str): The name of the base link.
        #     urdf_file (str): The path to the URDF file to be created.
        #     obj_file (str): The path to the OBJ file to be created.
        #
        # Returns:
        #     None
        # """
        print("CREATING NEW URDF")
        import os
        import xml.etree.ElementTree as ET
        import Mesh
        from math import radians
        obj_file = str(FreeCAD.ActiveDocument.Objects[0].Name) + ".obj"
        # Create directory if it doesn't exist
        directory = "C:\\Users\\" + str(os.getlogin()) + "\\" + str(FreeCAD.ActiveDocument.Label)
        os.makedirs(directory, exist_ok=True)

        # Create URDF root element
        root = ET.Element("robot", name="robot")
        base_link = ET.SubElement(root, "link", name=str(FreeCAD.ActiveDocument.Objects[0].Name))
        # Visual Geometry (Mesh)
        visual = ET.SubElement(base_link, "visual")
        geometry = ET.SubElement(visual, "geometry")
        visualmesh = ET.SubElement(geometry, "mesh")
        visualmesh.attrib["filename"] = str(FreeCAD.ActiveDocument.Objects[0].Name) + ".obj"
        origin1 = ET.SubElement(visual, "origin")
        origin1.set("xyz","0 0 0")
        origin1.set("rpy", "0 0 0")

        # Material
        material = ET.SubElement(visual, "material", name="visual_material")  # Add name attribute to material
        color = ET.SubElement(material, "color")
        color.attrib["rgba"] = "1 0 0 1"  # Red color, with alpha value 1 (fully opaque)

        # Inertial Properties
        inertial = ET.SubElement(base_link, "inertial")
        mass = ET.SubElement(inertial, "mass", value="1")
        origin_inertial = ET.SubElement(inertial, "origin", xyz="0 0 0", rpy="0 0 0")
        inertia = ET.SubElement(inertial, "inertia", ixx="1", ixy="0", ixz="0", iyy="1", iyz="0", izz="1")

        # Collision Geometry (Mesh)
        collision = ET.SubElement(base_link, "collision")
        geometry2 = ET.SubElement(collision, "geometry")
        collision_mesh = ET.SubElement(geometry2, "mesh")
        collision_mesh.attrib["filename"] = str(FreeCAD.ActiveDocument.Objects[0].Name) + ".obj"
        origin_collision = ET.SubElement(collision, "origin", xyz="0 0 0", rpy="0 0 0")

        MeshExportName = "C:/Users/" + str(os.getlogin()) + "/" + str(FreeCAD.ActiveDocument.Label) + "/" + obj_file
        __objs__ = []
        __objs__.append(FreeCAD.ActiveDocument.Objects[0])
        Mesh.export(__objs__, MeshExportName)

        # Write URDF file
        urdf_path = directory + "\\" + urdf_file
        tree = ET.ElementTree(root)
        with open(urdf_path, "wb") as f:
            tree.write(f)
        print("URDF Saved to: " + urdf_path)
        self.baselink = True

    def append_joint_to_urdf(self, urdf_file, linkinfo):

        """
        Append joint data to a URDF file.

        Parameters:
            urdf_file (str): The path to the URDF file.
            linkinfo (dict): Dictionary containing joint information.

        Returns:
            None
        """
        def LastLinkXYZ(root, last_link_name):
            for link in root.findall('link'):
                if link.get('name') == last_link_name:
                    visual = link.find('visual')
                    if visual is not None:
                        origin = visual.find('origin')
                        if origin is not None:
                            xyz = origin.get('xyz')
                            if xyz:
                                xyz_values = list(map(float, xyz.split()))
                                print(f"Position of the last link ({last_link_name}): {xyz_values}")
                                return xyz_values
                            else:
                                print(f"Origin tag found, but no xyz attribute in link {last_link_name}.")
                        else:
                            print(f"No origin tag found in the visual element of link {last_link_name}.")
                    else:
                        print(f"No visual element found in link {last_link_name}.")
                    break

        import xml.etree.ElementTree as ET
        from math import radians

        totalpath = "C:\\Users\\" + str(os.getlogin()) + "\\" + str(FreeCAD.ActiveDocument.Label) + "\\" + urdf_file

        tree = ET.parse(totalpath)
        root = tree.getroot()
        # Find all links in the URDF
        links = []
        for link in root.findall('link'):
            links.append(link.get('name'))
        self.links = links

        # def GetLinks():
        #     import xml.etree.ElementTree as ET
        #     from math import radians
        #
        #     totalpath = "C:\\Users\\" + str(os.getlogin()) + "\\" + str(FreeCAD.ActiveDocument.Label) + "\\" + urdf_file
        #
        #     tree = ET.parse(totalpath)
        #     root = tree.getroot()
        #     links = []
        #     for link in root.findall('link'):
        #         links.append(link.get('name'))
        #     joints = []
        #     for joint in root.findall('joint'):
        #         joints.append(joint.get('name'))
        #     self.links = links
        #     return links, joints

        # # Helper function to remove joint and corresponding link and save the URDF
        # def remove_joint_and_link(root, joint_name):
        #     joint_found = False
        #     link_found = False
        #
        #
        #     # NEED TO REDO THIS LOGIC AND FIND A FOR SURE WAY TO KNOW  WHAT CHILD OBJECT IS
        #     # BECAUSE if joint.get('name') == joint_name:   ONLY WORKS IF YOU ARE ADDING THE EXACT SAME KIND OF JOINT BACK
        #     # WHAT IF I WANT TO DELETE AND RE-ADD A LINEAR JOINT? DOESN'T CATCH NOW I HAVE BOTH ROTARY AND LINEAR JOINTS IN THE
        #     # URDF FOR SAME PARENT CHILD VERY BAD
        #     # Remove joint
        #
        #
        #     # 1 Is there a joint that has the same parent and child as current joint to be added?
        #     # 2 If yes, delete this joint
        #     # 3 Delete the child
        #     # 4 Re-add new joint and new child
        #
        #     for joint in root.findall('joint'):
        #
        #         if joint.get('name') == joint_name:
        #             child = joint.find('child')
        #             if child is not None:
        #                 childtodelete = child.get('link')
        #             print(childtodelete)
        #             print("FOUND!")
        #             root.remove(joint)
        #             joint_found = True
        #             break
        #
        #     # # Remove link
        #     for link in root.findall('link'):
        #         if link.get('name') == childtodelete:
        #             root.remove(link)
        #             link_found = True
        #             break
        #
        #     # If either joint or link was found and removed, save the modified URDF
        #     if joint_found or link_found:
        #         tree.write(totalpath)
        #         print(f"Joint '{joint_name}' and/or link '{link.get('name')}' removed and URDF saved.")
        #     else:
        #         print(f"Joint '{joint_name}' or link '{link.get('name')}' not found in URDF.")

        # Function to remove redundant constraints
        from typing import List, Dict, Tuple

        # def remove_redundant_constraints(constraints: List[Dict[str, Dict]]) -> List[Dict[str, Dict]]:
        #     unique_constraints = []
        #     seen = set()
        #
        #     for constraint in constraints:
        #         key = list(constraint.keys())[0]
        #         value = constraint[key]
        #
        #         # Convert vector attributes to tuples if they are not already tuples
        #         def vector_to_tuple(v):
        #             return tuple(v) if isinstance(v, (tuple, list)) else (v.x, v.y, v.z)
        #
        #         unique_tuple = (
        #             value['parent_object'],
        #             vector_to_tuple(value['childPlacement']),
        #             vector_to_tuple(value['parentPlacement']),
        #             vector_to_tuple(value['destination_axis']),
        #             vector_to_tuple(value['foreign_axis']),
        #             value['dependency_type'],
        #             value['joint_name']
        #         )
        #
        #         # If this unique combination has not been seen before, add it to the result
        #         if unique_tuple not in seen:
        #             seen.add(unique_tuple)
        #             unique_constraints.append(constraint)
        #
        #     return unique_constraints

        # LAST GEOMETRY UPDATE ON THE RECENTLY UPDATED LINK
        with open("C:\\Users\\" + str(os.getlogin()) + "\\" + str(FreeCAD.ActiveDocument.Label) + "\\temp.txt", "r") as f:
            lines = f.readlines()
        lines[0] = lines[0].replace("\n","")

        for specificlinkinfo in self.alllinkinfo:
            if list(specificlinkinfo.items())[-1][0] == lines[0] and specificlinkinfo[next(iter(specificlinkinfo))]['parent_object'] == lines[1] or \
                list(specificlinkinfo.items())[-1][0] == lines[1] and specificlinkinfo[next(iter(specificlinkinfo))]['parent_object'] == lines[0]:

                break
            else:
                print("ERROR: Link Not Found")

        link1, _ = list(specificlinkinfo.items())[-1]
        link2 = specificlinkinfo[next(iter(specificlinkinfo))]['parent_object']
        jointtype = specificlinkinfo[next(iter(specificlinkinfo))]['dependency_type']
        joint_name = specificlinkinfo[next(iter(specificlinkinfo))].get('joint_name', None)  # Assuming joint_name is part of the info

        if link2 not in links:
            self.parent_link_name = link1
            self.child_link_name = link2
            newlinkinfo = specificlinkinfo
        elif link1 not in links:
            self.parent_link_name = link2
            self.child_link_name = link1
            newlinkinfo = specificlinkinfo
        else:
            # NEED TO REDO THIS LOGIC AND FIND A FOR SURE WAY TO KNOW  WHAT CHILD OBJECT IS
            # BECAUSE if joint.get('name') == joint_name:   ONLY WORKS IF YOU ARE ADDING THE EXACT SAME KIND OF JOINT BACK
            # WHAT IF I WANT TO DELETE AND RE-ADD A LINEAR JOINT? DOESN'T CATCH NOW I HAVE BOTH ROTARY AND LINEAR JOINTS IN THE
            # URDF FOR SAME PARENT CHILD VERY BAD
            # Remove joint

            # 1 Is there a joint that has the same parent and child as current joint to be added?
            # 2 If yes, delete this joint
            # 3 Delete the child
            # 4 Re-add new joint and new child

            for joint in root.findall('joint'):
                child = joint.find('child')
                parent = joint.find('parent')

                if (child.get('link') == link1 and parent.get('link') == link2) or (child.get('link') == link2 and parent.get('link') == link1):
                    print("Let's delete this joint")
                    print(joint.get('name'))

                    root.remove(joint)
                    childtodelete = child.get('link')
                    self.parent_link_name = parent.get('link')
                    self.child_link_name = childtodelete
                    break

            for link in root.findall('link'):
                if link.get('name') == childtodelete:

                    root.remove(link)
                    break
                childtodelete = ""
            tree.write(totalpath)
            newlinkinfo = specificlinkinfo


            # remove_joint_and_link(root,joint_name)
        # else: # Elif link1 and link2 in links AND
        #     # print(specificlinkinfo)
        #     # print(link1)
        #     # print(link2)
        #     # print(links)
        #     # Overwrite or delete existing joint and link
        #     print("Overwriting or deleting existing joint and link...")
        #     # print(joint_name)
        #     if joint_name:
        #         remove_joint_and_link(root, joint_name, link1)
        #     else:
        #         remove_joint_and_link(root, link1 + '_joint', link1)  # Assuming joint naming convention
        #     links = GetLinks()
        #     # print(links)
        #     if link2 not in links:
        #         self.parent_link_name = link1
        #         self.child_link_name = link2
        #         newlinkinfo = specificlinkinfo
        #         break
        #     elif link1 not in links:
        #         self.parent_link_name = link2
        #         self.child_link_name = link1
        #         newlinkinfo = specificlinkinfo
        #         break
        #     else:
        #         print("I'm tired of this grandpa")

        # Foreign Axis has some errors sometimes
        # print("HERE IS NEW LINK INFO")
        # print(newlinkinfo)
        # print("END NEW LINK INFO")
        foreign_axis = newlinkinfo[next(iter(newlinkinfo))]['foreign_axis']
        destination_axis = newlinkinfo[next(iter(newlinkinfo))]['destination_axis']
        ChildObjPlacement = FreeCAD.ActiveDocument.getObject(self.child_link_name).Placement.Base

        ParentObjPlacement = FreeCAD.ActiveDocument.getObject(self.parent_link_name).Placement.Base

        if jointtype == 'axial':
            joint = ET.Element("joint", name=joint_name, type="continuous")
        elif jointtype == 'linear':
            joint = ET.Element("joint", name=joint_name, type="prismatic")

        parent = ET.SubElement(joint, "parent", link=self.parent_link_name)
        child = ET.SubElement(joint, "child", link=self.child_link_name)

        """ORIGIN IS NEGATIVE OF FOREIGN AXIS"""
        """JOINT XYZ IS FOREIGN AXIS"""

        if len(links) == 1:
            origin = ET.SubElement(joint, "origin", rpy="0 0 0",
                                   xyz=str(foreign_axis[0]) + " " + str(foreign_axis[1]) + " " + str(
                                       foreign_axis[2]))

        else:
            xyzlast = LastLinkXYZ(root,self.parent_link_name)
            origin = ET.SubElement(joint, "origin", rpy="0 0 0",
                                   xyz=str(xyzlast[0]+foreign_axis[0]) + " " + str(xyzlast[1]+foreign_axis[1]) + " " + str(xyzlast[2]+
                                           foreign_axis[2]))

        axis = ET.SubElement(joint, "axis",
                             xyz=f"{destination_axis.x} {destination_axis.y} {destination_axis.z}")
        limit = ET.SubElement(joint, "limit", velocity="10000000")

        root.append(joint)

        # ADD LINK
        volume = FreeCAD.ActiveDocument.getObject(self.child_link_name).Shape.Volume / 1000000000  # Convert volume from mm^3 to m^3
        m = FreeCAD.ActiveDocument.getObject(self.child_link_name).Shape.MatrixOfInertia
        ixx = "{:.6f}".format(m.A[0])
        ixy = "{:.6f}".format(m.A[1])
        ixz = "{:.6f}".format(m.A[2])
        iyy = "{:.6f}".format(m.A[5])
        iyz = "{:.6f}".format(m.A[6])
        izz = "{:.6f}".format(m.A[10])

        child_link = ET.Element("link", name=self.child_link_name)
        visual = ET.SubElement(child_link, "visual")
        origin1 = ET.SubElement(visual, "origin")
        # SIGN ON SECOND ENTRY IS FLIPPED FOR SOME REASON
        # THE DESTINATION AXIS IS THE UNIT VECTOR THAT THE CHILD OBJECT HAS BEEN ROTATED TO WITH RESPECT
        # TO HOW IT WAS LAID OUT ORIGINALLY IN THE ORIGINAL FREECAD DOCUMENT
        origin1.set("xyz", str(-foreign_axis[0]) + " " + str(-foreign_axis[1]) + " " + str(-foreign_axis[2]))
        origin1.set("rpy", "0 0 0")
        geometry = ET.SubElement(visual, "geometry")

        mesh = ET.SubElement(geometry, "mesh")
        mesh.attrib["filename"] = str(self.child_link_name) + ".obj"

        inertial = ET.SubElement(child_link, "inertial")
        mass = ET.SubElement(inertial, "mass", value="1")
        origin = ET.SubElement(inertial, "origin", xyz="0 0 0")
        inertia = ET.SubElement(inertial, "inertia", ixx=ixx, ixy=ixy, ixz=ixz, iyy=iyy, iyz=iyz, izz=izz)

        # Add collision geometry
        collision = ET.SubElement(child_link, "collision")
        geometry2 = ET.SubElement(collision, "geometry")
        collision_mesh = ET.SubElement(geometry2, "mesh")
        collision_mesh.attrib["filename"] = self.child_link_name + ".obj"
        ET.SubElement(collision, "origin", xyz=str(-foreign_axis[0]) + " " + str(-foreign_axis[1]) + " " + str(-foreign_axis[2]), rpy="0 0 0")
        root.append(child_link)
        tree.write(totalpath)
        print("URDF Saved to: " + totalpath)



    def loadSystem(self,doc, matelist=None):
        self.clear()
        self.doc = doc
        self.status = "loading"

        self.removeFaultyConstraints(doc)

        self.convergencyCounter = 0
        self.lastPositionError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
        self.lastAxisError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
        #
        self.constraints = []
        constraints =[]             # temporary list
        if matelist is not None:        # Transfer matelist to the temp list
            for obj in matelist:
                if 'ConstraintInfo' in obj.Content:
                    constraints.append(obj)
        else:
            # if there is not a list of my mates get the list from the doc
            constraints = [ obj for obj in doc.Objects if 'ConstraintInfo' in obj.Content]
        # check for Suppressed mates here and transfer mates to self.constraints
        for obj in constraints:
            if hasattr(obj,'Suppressed'):
                #if the mate is suppressed do not add it
                if obj.Suppressed == False:
                    self.constraints.append(obj)
        #
        # Extract all the objectnames which are affected by constraints..
        self.objectNames = []
        for c in self.constraints:
            for attr in ['Object1','Object2']:
                objectName = getattr(c, attr, None)
                if objectName is not None and not objectName in self.objectNames:
                    self.objectNames.append( objectName )
        #
        # create a Rigid() dataStructure for each of these objectnames...
        for o in self.objectNames:
            ob1 = doc.getObject(o)
            if hasattr(ob1, "fixedPosition"):
                fx = ob1.fixedPosition
            else:
                fx = False
            if hasattr(ob1, "debugmode"):
                debugMode = ob1.debugmode
            else:
                debugMode = False
            rig = Rigid(
                o,
                ob1.Label,
                fx,
                ob1.Placement,
                debugMode
                )
            rig.spinCenter = ob1.Shape.BoundBox.Center
            self.rigids.append(rig)
        #
        # link constraints to rigids using dependencies
        deleteList = [] # a list to collect broken constraints
        for c in self.constraints:
            rigid1 = self.getRigid(c.Object1)
            rigid2 = self.getRigid(c.Object2)

            # create and update list of constrained rigids
            if rigid2 is not None and not rigid2 in rigid1.linkedRigids: rigid1.linkedRigids.append(rigid2);
            if rigid1 is not None and not rigid1 in rigid2.linkedRigids: rigid2.linkedRigids.append(rigid1);

            try:
                Dependency.Create(doc, c, self, rigid1, rigid2)
            except:
                self.status = "loadingDependencyError"
                deleteList.append(c)


        for rig in self.rigids:
            rig.hierarchyLinkedRigids.extend(rig.linkedRigids)

        if len(deleteList) > 0:
            msg = translate("A2plus", "The following constraints are broken:") + "\n"
            for c in deleteList:
                msg += "{}\n".format(c.Label)
            msg += translate("A2plus", "Do you want to delete them?")

            flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.No
            response = QtGui.QMessageBox.critical(
                QtGui.QApplication.activeWindow(),
                translate("A2plus", "Delete broken constraints?"),
                msg,
                flags
                )
            if response == QtGui.QMessageBox.Yes:
                for c in deleteList:
                    a2plib.removeConstraint(c)

        if self.status == "loadingDependencyError":
            return

        for rig in self.rigids:

            rig.calcSpinCenter()
            rig.calcRefPointsBoundBoxSize()

        self.retrieveDOFInfo() # function only once used here at this place in whole program
        self.status = "loaded"

    def DOF_info_to_console(self):
        doc = FreeCAD.activeDocument()

        dofGroup = doc.getObject("dofLabels")
        if dofGroup is None:
            dofGroup=doc.addObject("App::DocumentObjectGroup", "dofLabels")
        else:
            for lbl in dofGroup.Group:
                doc.removeObject(lbl.Name)
            doc.removeObject("dofLabels")
            dofGroup=doc.addObject("App::DocumentObjectGroup", "dofLabels")

        self.loadSystem( doc )

        # look for unconstrained objects and label them
        solverObjectNames = []
        for rig in self.rigids:
            solverObjectNames.append(rig.objectName)
        shapeObs = a2plib.filterShapeObs(doc.Objects)
        for so in shapeObs:
            if so.Name not in solverObjectNames:
                ob = doc.getObject(so.Name)
                if ob.ViewObject.Visibility == True:
                    bbCenter = ob.Shape.BoundBox.Center
                    dofLabel = doc.addObject("App::AnnotationLabel","dofLabel")
                    dofLabel.LabelText = translate("A2plus", "FREE")
                    dofLabel.BasePosition.x = bbCenter.x
                    dofLabel.BasePosition.y = bbCenter.y
                    dofLabel.BasePosition.z = bbCenter.z
                    #
                    dofLabel.ViewObject.BackgroundColor = a2plib.BLUE
                    dofLabel.ViewObject.TextColor = a2plib.WHITE
                    dofGroup.addObject(dofLabel)


        numdep = 0
        self.retrieveDOFInfo() #function only once used here at this place in whole program
        for rig in self.rigids:
            dofCount = rig.currentDOF()
            ob = doc.getObject(rig.objectName)
            if ob.ViewObject.Visibility == True:
                bbCenter = ob.Shape.BoundBox.Center
                dofLabel = doc.addObject("App::AnnotationLabel","dofLabel")
                if rig.fixed:
                    dofLabel.LabelText = translate("A2plus", "Fixed")
                else:
                    dofLabel.LabelText = translate("A2plus", "DOFs: {}").format(dofCount)
                dofLabel.BasePosition.x = bbCenter.x
                dofLabel.BasePosition.y = bbCenter.y
                dofLabel.BasePosition.z = bbCenter.z

                if rig.fixed:
                    dofLabel.ViewObject.BackgroundColor = a2plib.RED
                    dofLabel.ViewObject.TextColor = a2plib.BLACK
                elif dofCount == 0:
                    dofLabel.ViewObject.BackgroundColor = a2plib.RED
                    dofLabel.ViewObject.TextColor = a2plib.BLACK
                elif dofCount < 6:
                    dofLabel.ViewObject.BackgroundColor = a2plib.YELLOW
                    dofLabel.ViewObject.TextColor = a2plib.BLACK
                dofGroup.addObject(dofLabel)


            rig.beautyDOFPrint()
            numdep+=rig.countDependencies()
        Msg(translate("A2plus", "There are {:.0f} dependencies").format(numdep/2) + "\n")

    def retrieveDOFInfo(self):
        """
        Method used to retrieve all info related to DOF handling.
        the method scans each rigid, and on each not tempfixed rigid scans the list of linkedobjects
        then for each linked object compile a dict where each linked object has its dependencies
        then for each linked object compile a dict where each linked object has its dof position
        then for each linked object compile a dict where each linked object has its dof rotation
        """
        for rig in self.rigids:

            #if not rig.tempfixed:  #skip already fixed objs

            for linkedRig in rig.linkedRigids:
                tmplinkedDeps = []
                tmpLinkedPointDeps = []
                for dep in rig.dependencies:
                    if linkedRig==dep.dependedRigid:
                        #be sure pointconstraints are at the end of the list
                        if dep.isPointConstraint :
                            tmpLinkedPointDeps.append(dep)
                        else:
                            tmplinkedDeps.append(dep)
                #add at the end the point constraints
                tmplinkedDeps.extend(tmpLinkedPointDeps)
                rig.depsPerLinkedRigids[linkedRig] = tmplinkedDeps

            #dofPOSPerLinkedRigid is a dict where for each
            for linkedRig in rig.depsPerLinkedRigids.keys():
                linkedRig.pointConstraints = []
                _dofPos = linkedRig.posDOF
                _dofRot = linkedRig.rotDOF
                for dep in rig.depsPerLinkedRigids[linkedRig]:
                    _dofPos, _dofRot = dep.calcDOF(_dofPos,_dofRot, linkedRig.pointConstraints)
                rig.dofPOSPerLinkedRigids[linkedRig] = _dofPos
                rig.dofROTPerLinkedRigids[linkedRig] = _dofRot

            #ok each rigid has a dict for each linked objects,
            #so we now know the list of linked objects and which
            #dof rot and pos both limits.



    # TODO: maybe instead of traversing from the root every time, save a list of objects on current distance
    # and use them to propagate next distance to their children
    def assignParentship(self, doc):
        # Start from fixed parts
        for rig in self.rigids:
            if rig.fixed:
                rig.disatanceFromFixed = 0
                haveMore = True
                distance = 0
                while haveMore:
                    haveMore = rig.assignParentship(distance)
                    distance += 1

        if A2P_DEBUG_LEVEL > 0:
            Msg(20*"=" + "\n")
            Msg(translate("A2plus", "Hierarchy:") + "\n")
            Msg(20*"=" + "\n")
            for rig in self.rigids:
                if rig.fixed: rig.printHierarchy(0)
            Msg(20*"=" + "\n")

        #self.visualizeHierarchy()

    def visualizeHierarchy(self):
        '''
        Generate an html file with constraints structure.

        The html file is in the same folder
        with the same filename of the assembly
        '''
        out_file = os.path.splitext(self.doc.FileName)[0] + '_asm_hierarchy.html'
        Msg(translate("A2plus", "Writing visual hierarchy to: '{}'").format(out_file) + "\n")
        f = open(out_file, "w")

        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n")
        f.write("<head>\n")
        f.write('    <meta charset="utf-8">\n')
        f.write('    <meta http-equiv="X-UA-Compatible" content="IE=edge">\n')
        f.write('    <title>' + translate("A2plus", "A2P assembly hierarchy visualization") + '</title>\n')
        f.write("</head>\n")
        f.write("<body>\n")
        f.write('<div class="mermaid">\n')

        f.write("graph TD\n")
        for rig in self.rigids:
            rigLabel = a2plib.to_str(rig.label).replace(u' ',u'_')
            # No children, add current rogod as a leaf entry
            if len(rig.childRigids) == 0:
                message = u"{}\n".format(rigLabel)
                f.write(message)
            else:
                # Rigid have children, add them based on the dependency list
                for d in rig.dependencies:
                    if d.dependedRigid in rig.childRigids:
                        dependedRigLabel = a2plib.to_str(d.dependedRigid.label).replace(u' ',u'_')
                        if rig.fixed:
                            message = "{}({}<br>*" + translate("A2plus", "FIXED") + "*) -- {} --> {}\n".format(rigLabel, rigLabel, d.Type, dependedRigLabel)
                            f.write(message)
                        else:
                            message = u"{} -- {} --> {}\n".format(rigLabel, d.Type, dependedRigLabel)
                            f.write(message)

        f.write("</div>\n")
        f.write('    <script src="https://unpkg.com/mermaid@7.1.2/dist/mermaid.js"></script>\n')
        f.write("    <script>\n")
        f.write('        mermaid.initialize({startOnLoad: true});\n')
        f.write("    </script>\n")
        f.write("</body>")
        f.write("</html>")
        f.close()

    def calcMoveData(self,doc):
        for rig in self.rigids:
            rig.calcMoveData(doc, self)

    def prepareRestart(self):
        for rig in self.rigids:
            rig.prepareRestart()
        self.partialSolverCurrentStage = PARTIAL_SOLVE_STAGE1

    def detectUnmovedParts(self):
        doc = FreeCAD.activeDocument()
        self.unmovedParts = []
        for rig in self.rigids:
            if rig.fixed: continue
            if not rig.moved:
                self.unmovedParts.append(
                    doc.getObject(rig.objectName)
                    )

    def solveAccuracySteps(self,doc, matelist=None):
        self.level_of_accuracy=1
        self.mySOLVER_POS_ACCURACY = self.getSolverControlData()[self.level_of_accuracy][0]
        self.mySOLVER_SPIN_ACCURACY = self.getSolverControlData()[self.level_of_accuracy][1]

        self.loadSystem(doc, matelist)
        if self.status == "loadingDependencyError":
            return
        self.assignParentship(doc)
        while True:
            systemSolved, linkinfoinst = self.calculateChain(doc)

            if self.level_of_accuracy == 1:
                self.detectUnmovedParts()   # do only once here. It can fail at higher accuracy levels
                                            # where not a final solution is required.
            if linkinfoinst == 99999:
                # If the constraint is created between two child objects
                print("PROBLEM")
                break
            if linkinfoinst not in self.linkinfo:
                self.linkinfo.append(linkinfoinst)
            if a2plib.SOLVER_ONESTEP > 0:
                systemSolved = True
                break
            if systemSolved:
                self.level_of_accuracy+=1
                if self.level_of_accuracy > len(self.getSolverControlData()):
                    self.solutionToParts(doc)

                    urdf_file = str(FreeCAD.ActiveDocument.Label) + ".urdf"
                    directory = "C:\\Users\\" + str(os.getlogin()) + "\\" + str(FreeCAD.ActiveDocument.Label)
                    urdf_path = directory + "\\" + urdf_file
                    if os.path.exists(urdf_path) == False:
                        self.create_urdf(FreeCAD.ActiveDocument.Objects[0].Label,urdf_file)

                    self.append_joint_to_urdf(urdf_file, self.linkinfo)
                    self.prettify_urdf(urdf_file)
                    self.export_obj_no_autoscale(self.child_link_name)

                    break
                self.mySOLVER_POS_ACCURACY = self.getSolverControlData()[self.level_of_accuracy][0]
                self.mySOLVER_SPIN_ACCURACY = self.getSolverControlData()[self.level_of_accuracy][1]
                self.loadSystem(doc, matelist)
            else:
                completeSolvingRequired = self.getSolverControlData()[self.level_of_accuracy][2]
                if not completeSolvingRequired: systemSolved = True
                break
        self.maxAxisError = 0.0
        self.maxSingleAxisError = 0.0
        self.maxPosError = 0.0
        for rig in self.rigids:
            if rig.maxPosError > self.maxPosError:
                self.maxPosError = rig.maxPosError
            if rig.maxAxisError > self.maxAxisError:
                self.maxAxisError = rig.maxAxisError
            if rig.maxSingleAxisError > self.maxSingleAxisError:
                self.maxSingleAxisError = rig.maxSingleAxisError
        if not a2plib.SIMULATION_STATE:
            Msg(translate("A2plus", "TARGET   POS-ACCURACY :{}").format(self.mySOLVER_POS_ACCURACY) + "\n")
            Msg(translate("A2plus", "REACHED  POS-ACCURACY :{}").format(self.maxPosError) + "\n")
            Msg(translate("A2plus", "TARGET  SPIN-ACCURACY :{}").format(self.mySOLVER_SPIN_ACCURACY) + "\n")
            Msg(translate("A2plus", "REACHED SPIN-ACCURACY :{}").format(self.maxAxisError) + "\n")
            Msg(translate("A2plus", "SA      SPIN-ACCURACY :{}").format(self.maxSingleAxisError) + "\n")

        return systemSolved

    def solveSystem(self,doc,matelist=None, showFailMessage=True):
        if not a2plib.SIMULATION_STATE:
            Msg("===== " + translate("A2plus", "Start Solving System") + " =====\n")

        systemSolved = self.solveAccuracySteps(doc,matelist)

        if self.status == "loadingDependencyError":
            return systemSolved
        if systemSolved:
            self.status = "solved"
            if not a2plib.SIMULATION_STATE:
                Msg("===== " + translate("A2plus", "System solved using partial + recursive unfixing") + " =====\n")
                self.checkForUnmovedParts()
        else:
            if a2plib.SIMULATION_STATE == True:
                self.status = "unsolved"
                return systemSolved

            else: # a2plib.SIMULATION_STATE == False
                self.status = "unsolved"
                if showFailMessage == True:
                    Msg("===== " + translate("A2plus", "Could not solve system") + " =====\n")
                    msg = \
translate("A2plus",
'''
Constraints inconsistent. Cannot solve System.
Please run the conflict finder tool!
'''
)
                    QtGui.QMessageBox.information(
                        QtGui.QApplication.activeWindow(),
                        translate("A2plus", "Constraint mismatch"),
                        msg
                        )
                return systemSolved

    def checkForUnmovedParts(self):
        """
        If there are parts, which are constrained but have no
        constraint path to a fixed part, the solver will
        ignore them and they are not moved.
        This function detects this and signals it to the user.
        """
        if len(self.unmovedParts) != 0:
            FreeCADGui.Selection.clearSelection()
            for obj in self.unmovedParts:
                FreeCADGui.Selection.addSelection(obj)
                msg = translate("A2plus",
'''
The highlighted parts were not moved. They are
not constrained (also over constraint chains)
to a fixed part!
''')
            if a2plib.SHOW_WARNING_FLOATING_PARTS: #dialog is not needet during conflict finding
                QtGui.QMessageBox.information(
                    QtGui.QApplication.activeWindow(),
                    translate("A2plus", "Could not move some parts"),
                    msg
                    )
            else:
                print ('')
                print (msg) # during conflict finding do a print to console output
                print ('')

    def printList(self, name, l):
        Msg("{} = (".format(name))
        for e in l:
            Msg( "{} ".format(e.label) )
        Msg("):\n")

    def calculateChain(self, doc):
        # Initialize step count and work list
        self.stepCount = 0
        workList = []

        if a2plib.SIMULATION_STATE or not a2plib.PARTIAL_PROCESSING_ENABLED:
            # Solve complete system at once if simulation is running or partial processing is disabled
            workList = self.rigids
            return self.calculateWorkList(doc, workList)

        # Normal partial solving if no simulation is running and partial processing is enabled
        # Load initial worklist with all fixed parts
        workList.extend(rig for rig in self.rigids if rig.fixed)

        while True:
            addList = set()
            newRigFound = False
            
            # Check linked rigids for possible additions to the work list
            for rig in workList:
                for linkedRig in rig.linkedRigids:
                    if linkedRig not in workList and rig.isFullyConstrainedByRigid(linkedRig):
                        addList.add(linkedRig)
                        newRigFound = True
                        break

            if not newRigFound:
                # If no new rigids found, consider candidates for addition to the work list
                for rig in workList:
                    addList.update(rig.getCandidates())

            if addList:
                # Update cached state for rigids being added to the work list
                for rig in addList:
                    rig.updateCachedState(rig.placement)
                workList.extend(addList)

                solutionFound, linkinfo1 = self.calculateWorkList(doc, workList)
                first_key = next(iter(linkinfo1))

                if linkinfo1 not in self.alllinkinfo and linkinfo1[first_key]['foreign_axis'] is not None:
                    self.alllinkinfo.append(linkinfo1)

                if not solutionFound:
                    print("NO SOLUTION FOUND")
                    return False
            else:
                break

            if a2plib.SOLVER_ONESTEP > 2:
                break
        try:
            return True, linkinfo1
        except:
            print("You cannot constrain two child links together. Please select at least one parent link.")
            return True, 99999
    def calculateWorkList(self, doc, workList):
        reqPosAccuracy = self.mySOLVER_POS_ACCURACY
        reqSpinAccuracy = self.mySOLVER_SPIN_ACCURACY

        for rig in workList:
            rig.enableDependencies(workList)
        for rig in workList:
            rig.calcSpinBasicDataDepsEnabled()

        self.lastPositionError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
        self.lastAxisError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
        self.convergencyCounter = 0

        calcCount = 0
        goodAccuracy = False
        pos_error_check=True
        maxAxisError_check=True
        maxSingleAxisError_check=True
        pos_error_save=[]
        axis_error_save=[]
        single_axis_error_save=[]
        while not goodAccuracy:
            maxPosError = 0.0
            maxAxisError = 0.0
            maxSingleAxisError = 0.0

            calcCount += 1
            self.stepCount += 1
            self.convergencyCounter += 1
            # First calculate all the movement vectors
            for w in workList:
                w.moved = True
                linkinfo = w.calcMoveData(doc, self)
                if w.maxPosError > maxPosError:
                    maxPosError = w.maxPosError
                if w.maxAxisError > maxAxisError:
                    maxAxisError = w.maxAxisError
                if w.maxSingleAxisError > maxSingleAxisError:
                    maxSingleAxisError = w.maxSingleAxisError

            # Perform the move
            for w in workList:
                w.move(doc)

            # The accuracy is good, apply the solution to FreeCAD's objects
            if (maxPosError <= reqPosAccuracy and   # relevant check
                maxAxisError <= reqSpinAccuracy and # relevant check
                maxSingleAxisError <= reqSpinAccuracy * 10  # additional check for insolvable assemblies
                                                            # sometimes spin can be solved but singleAxis not..
                ) or (a2plib.SOLVER_ONESTEP > 0):
                # The accuracy is good, we're done here
                goodAccuracy = True

                # Mark the rigids as tempfixed and add its constrained rigids to pending list to be processed next
                for r in workList:
                    r.applySolution(doc, self)
                    r.tempfixed = True

            if self.convergencyCounter > SOLVER_STEPS_CONVERGENCY_CHECK:
                if (
                    maxPosError  >= SOLVER_CONVERGENCY_FACTOR * self.lastPositionError or
                    maxAxisError >= SOLVER_CONVERGENCY_FACTOR * self.lastAxisError
                    ):
                    foundRigidToUnfix = False
                    # search for unsolved dependencies...
                    for rig in workList:
                        if rig.fixed or rig.tempfixed: continue
                        #if rig.maxAxisError >= maxAxisError or rig.maxPosError >= maxPosError:
                        if rig.maxAxisError > reqSpinAccuracy or rig.maxPosError > reqPosAccuracy:
                            for r in rig.linkedRigids:
                                if r.tempfixed and not r.fixed:
                                    r.tempfixed = False
                                    #Msg("unfixed Rigid {}\n".format(r.label))
                                    foundRigidToUnfix = True

                    if foundRigidToUnfix:
                        self.lastPositionError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
                        self.lastAxisError = SOLVER_CONVERGENCY_ERROR_INIT_VALUE
                        self.convergencyCounter = 0
                        continue
                    else:
                        Msg('\n')
                        Msg('convergency-conter: {}\n'.format(self.convergencyCounter))
                        Msg(translate("A2plus", "No convergency anymore, retrying") + "\n")
                        pass

                self.lastPositionError = maxPosError
                self.lastAxisError = maxAxisError
                self.maxSingleAxisError = maxSingleAxisError
                self.convergencyCounter = 0

            if self.stepCount > SOLVER_MAXSTEPS:
                Msg(translate("A2plus", "Reached max calculations count: {}").format(SOLVER_MAXSTEPS) + "\n")
                return False, _
        return True, linkinfo

    def solutionToParts(self,doc):
        for rig in self.rigids:
            rig.applySolution(doc, self);

#------------------------------------------------------------------------------
def solveConstraints( doc, cache=None, useTransaction = True, matelist=None, showFailMessage=True):

    if doc is None:
        QtGui.QMessageBox.information(
                    QtGui.QApplication.activeWindow(),
                    translate("A2plus", "No active document found!"),
                    translate("A2plus", "Before running solver, you have to open an assembly file.")
                    )
        return

    if useTransaction: doc.openTransaction("a2p_systemSolving")
    ss = SolverSystem()
    systemSolved = ss.solveSystem(doc, matelist, showFailMessage )
    if useTransaction: doc.commitTransaction()
    a2plib.unTouchA2pObjects()
    return systemSolved

def autoSolveConstraints( doc, callingFuncName, cache=None, useTransaction=True, matelist=None):
    if not a2plib.getAutoSolveState():
        return
    if callingFuncName is not None:
        """
        print (
            translate("A2plus", "AutoSolveConstraints called from '{}'").format(
                callingFuncName
                )
               )
        """
    solveConstraints(doc, useTransaction)

class a2p_SolverCommand:
    def Activated(self):
        solveConstraints( FreeCAD.ActiveDocument ) #the new iterative solver

    def GetResources(self):
        return {
            'Pixmap'  : path_a2p + '/icons/a2p_Solver.svg',
            'MenuText': translate("A2plus", "Solve constraints"),
            'ToolTip' : translate("A2plus", "Solves constraints")
            }

FreeCADGui.addCommand('a2p_SolverCommand', a2p_SolverCommand())
#------------------------------------------------------------------------------

if __name__ == "__main__":
    DebugMsg(A2P_DEBUG_1, translate("A2plus", "Starting solveConstraints latest script...") + "\n")
    doc = FreeCAD.activeDocument()
    solveConstraints(doc)
