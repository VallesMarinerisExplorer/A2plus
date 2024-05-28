import time
import pybullet as p
import getpass

# Initialize PyBullet
p.connect(p.GUI)  # Open a graphical user interface (GUI)

# Specify file location and load URDF file

urdf_file = "C:\\Users\\" + str(getpass.getuser()) + "\\" + str(FreeCAD.ActiveDocument.Label) + "\\" + urdf_file # Specify the path to your URDF file
robot_id = p.loadURDF(urdf_file, globalScaling=0.007)

# Add a camera so we can see with the GUI
p.resetDebugVisualizerCamera(cameraDistance=8.0, cameraYaw=0, cameraPitch=-89, cameraTargetPosition=[0, -0.5, 0])

# Run simulation
# p.setGravity(0, 0, -9.8)  # Set gravity

p.setTimeStep(1.0 / 240.0)  # Set time step
p.setRealTimeSimulation(0)  # Manually call each time step in the while loop as opposed to real-time simulation

while p.isConnected():
    # You can use setJointMotorControlArray too to set forces on a list of motors at the same time with one line of code
    # See PyBullet Quickstart Guide
    p.setJointMotorControl2(robot_id, 0, p.TORQUE_CONTROL, force=250)
    p.setJointMotorControl2(robot_id, 1, p.TORQUE_CONTROL, force=250)
    p.setJointMotorControl2(robot_id, 2, p.TORQUE_CONTROL, force=250)

    p.stepSimulation()
    # Probably redundant? V ^
    time.sleep(1/240)
