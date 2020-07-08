import os
import pybullet as p
import numpy as np
from .agent import Agent

class Tool(Agent):
    def __init__(self):
        super(Tool, self).__init__()

    def init(self, robot, task, directory, id, np_random, right=True, mesh_scale=[1]*3, maximal=False, alpha=1.0, mass=1):
        if robot is not None:
            pos_offset = robot.tool_pos_offset[task]
            orient_offset = p.getQuaternionFromEuler(robot.tool_orient_offset[task], physicsClientId=id)
            gripper_pos, gripper_orient = robot.get_pos_orient(robot.right_tool_joint if right else robot.left_tool_joint, center_of_mass=True)
            transform_pos, transform_orient = p.multiplyTransforms(positionA=gripper_pos, orientationA=gripper_orient, positionB=pos_offset, orientationB=orient_offset, physicsClientId=id)
        else:
            transform_pos = [0, 0, 0]
            transform_orient = [0, 0, 0, 1]

        # Instantiate the tool mesh
        if task == 'scratch_itch':
            tool = p.loadURDF(os.path.join(directory, 'scratcher', 'tool_scratch.urdf'), basePosition=transform_pos, baseOrientation=transform_orient, physicsClientId=id)
        elif task == 'bed_bathing':
            tool = p.loadURDF(os.path.join(directory, 'bed_bathing', 'wiper.urdf'), basePosition=transform_pos, baseOrientation=transform_orient, physicsClientId=id)
        elif task in ['drinking', 'feeding', 'arm_manipulation']:
            if task == 'drinking':
                visual_filename = os.path.join(directory, 'dinnerware', 'plastic_coffee_cup.obj')
                collision_filename = os.path.join(directory, 'dinnerware', 'plastic_coffee_cup_vhacd.obj')
            elif task == 'feeding':
                visual_filename = os.path.join(directory, 'dinnerware', 'spoon.obj')
                collision_filename = os.path.join(directory, 'dinnerware', 'spoon_vhacd.obj')
            elif task == 'arm_manipulation':
                visual_filename = os.path.join(directory, 'arm_manipulation', 'arm_manipulation_scooper.obj')
                collision_filename = os.path.join(directory, 'arm_manipulation', 'arm_manipulation_scooper_vhacd.obj')
            tool_visual = p.createVisualShape(shapeType=p.GEOM_MESH, fileName=visual_filename, meshScale=mesh_scale, rgbaColor=[1, 1, 1, alpha], physicsClientId=id)
            tool_collision = p.createCollisionShape(shapeType=p.GEOM_MESH, fileName=collision_filename, meshScale=mesh_scale, physicsClientId=id)
            tool = p.createMultiBody(baseMass=mass, baseCollisionShapeIndex=tool_collision, baseVisualShapeIndex=tool_visual, basePosition=transform_pos, baseOrientation=transform_orient, useMaximalCoordinates=maximal, physicsClientId=id)
        else:
            tool = None

        super(Tool, self).init(tool, id, np_random, indices=-1)

        if robot is not None:
            # Disable collisions between the tool and robot
            for j in (robot.right_gripper_collision_indices if right else robot.left_gripper_collision_indices):
                for tj in self.all_joint_indices + [self.base]:
                    p.setCollisionFilterPair(robot.body, self.body, j, tj, False, physicsClientId=id)
            # Create constraint that keeps the tool in the gripper
            constraint = p.createConstraint(robot.body, robot.right_tool_joint if right else robot.left_tool_joint, self.body, -1, p.JOINT_FIXED, [0, 0, 0], parentFramePosition=pos_offset, childFramePosition=[0, 0, 0], parentFrameOrientation=orient_offset, childFrameOrientation=[0, 0, 0, 1], physicsClientId=id)
            p.changeConstraint(constraint, maxForce=500, physicsClientId=id)

