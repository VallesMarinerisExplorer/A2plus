# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2019 kbwbe                                              *
# *                                                                         *
# *   Portions of code based on hamish's assembly 2                         *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import os
import sys
import math
import copy

from PySide import QtGui, QtCore

import FreeCAD
# from FreeCAD import Base
import FreeCADGui
import Part

from a2plib import *
import a2p_constraints
import a2p_ConstraintDialog
from a2p_viewProviderProxies import *
from a2p_solversystem import solveConstraints

translate = FreeCAD.Qt.translate


class a2p_PointIdentityConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.PointIdentityConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.PointIdentityConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_PointIdentity.svg',
            'MenuText': translate("A2plus_Constraints", "Add PointIdentity constraint"),
            'ToolTip': a2p_constraints.PointIdentityConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_PointIdentityConstraintCommand', a2p_PointIdentityConstraintCommand())


class a2p_PointOnLineConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.PointOnLineConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.PointOnLineConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_PointOnLineConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add PointOnLine constraint"),
            'ToolTip': a2p_constraints.PointOnLineConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_PointOnLineConstraintCommand', a2p_PointOnLineConstraintCommand())


class a2p_PointOnPlaneConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.PointOnPlaneConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.PointOnPlaneConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_PointOnPlaneConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add PointOnPlane constraint"),
            'ToolTip': a2p_constraints.PointOnPlaneConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_PointOnPlaneConstraintCommand', a2p_PointOnPlaneConstraintCommand())


class a2p_SphericalSurfaceConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.SphericalConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.SphericalConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_SphericalSurfaceConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add SphereCenterIdent constraint"),
            'ToolTip': a2p_constraints.SphericalConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_SphericalSurfaceConstraintCommand', a2p_SphericalSurfaceConstraintCommand())


class a2p_CircularEdgeConnectionCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.CircularEdgeConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.CircularEdgeConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_CircularEdgeConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add CircularEdge constraint"),
            'ToolTip': a2p_constraints.CircularEdgeConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_CircularEdgeConnection', a2p_CircularEdgeConnectionCommand())


class a2p_AxialConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.AxialConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.AxialConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/Rotary.png',
            'MenuText': translate("A2plus_Constraints", "Create Revolute/Continuous Joint"),
            'ToolTip': a2p_constraints.AxialConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_AxialConstraintCommand', a2p_AxialConstraintCommand())

class a2p_LinearConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.LinearConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.LinearConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/Linear.png',
            'MenuText': translate("A2plus_Constraints", "Create Linear/Prismatic Joint"),
            'ToolTip': a2p_constraints.AxialConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_LinearConstraintCommand', a2p_LinearConstraintCommand())




class a2p_AxisParallelConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.AxisParallelConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.AxisParallelConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': ':/icons/a2p_AxisParallelConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add AxisParallel constraint"),
            'ToolTip': a2p_constraints.AxisParallelConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_AxisParallelConstraintCommand', a2p_AxisParallelConstraintCommand())


class a2p_AxisPlaneParallelCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.AxisPlaneParallelConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.AxisPlaneParallelConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': ':/icons/a2p_AxisPlaneParallelConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add AxisPlaneParallel constraint"),
            'ToolTip': a2p_constraints.AxisPlaneParallelConstraint.getToolTip()
             }


FreeCADGui.addCommand('a2p_AxisPlaneParallelCommand', a2p_AxisPlaneParallelCommand())


class a2p_AxisPlaneAngleCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.AxisPlaneAngleConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.AxisPlaneAngleConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': ':/icons/a2p_AxisPlaneAngleConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add AxisPlaneAngle constraint"),
            'ToolTip': a2p_constraints.AxisPlaneAngleConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_AxisPlaneAngleCommand', a2p_AxisPlaneAngleCommand())


class a2p_AxisPlaneNormalCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.AxisPlaneNormalConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.AxisPlaneNormalConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': ':/icons/a2p_AxisPlaneNormalConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add AxisPlaneNormal constraint"),
            'ToolTip': a2p_constraints.AxisPlaneNormalConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_AxisPlaneNormalCommand', a2p_AxisPlaneNormalCommand())


class a2p_PlanesParallelConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.PlanesParallelConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.PlanesParallelConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_PlanesParallelConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add PlanesParallel constraint"),
            'ToolTip': a2p_constraints.PlanesParallelConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_PlanesParallelConstraintCommand', a2p_PlanesParallelConstraintCommand())


class a2p_PlaneCoincidentConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.PlaneConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.PlaneConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_PlaneCoincidentConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add PlaneCoincident constraint"),
            'ToolTip': a2p_constraints.PlaneConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_PlaneCoincidentConstraintCommand', a2p_PlaneCoincidentConstraintCommand())


class a2p_AngledPlanesConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.AngledPlanesConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.AngledPlanesConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_AngleConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add AngledPlanes constraint"),
            'ToolTip': a2p_constraints.AngledPlanesConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_AngledPlanesConstraintCommand', a2p_AngledPlanesConstraintCommand())


class a2p_CenterOfMassConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        c = a2p_constraints.CenterOfMassConstraint(selection)
        cvp = a2p_ConstraintDialog.a2p_ConstraintValuePanel(
            c.constraintObject,
            'createConstraint'
            )
        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return a2p_constraints.CenterOfMassConstraint.isValidSelection(
            FreeCADGui.Selection.getSelectionEx()
            )

    def GetResources(self):
        return {
            'Pixmap': path_a2p + '/icons/a2p_CenterOfMassConstraint.svg',
            'MenuText': translate("A2plus_Constraints", "Add CenterOfMass constraint"),
            'ToolTip': a2p_constraints.CenterOfMassConstraint.getToolTip()
            }


FreeCADGui.addCommand('a2p_CenterOfMassConstraintCommand', a2p_CenterOfMassConstraintCommand())
