from __future__ import print_function

import PyKDL as kdl
import rospy
import sys
import tf_conversions.posemath as pm

from geometry_msgs.msg import Pose
from costar_robot_msgs.srv import SmartMoveRequest
from costar_robot_msgs.srv import ServoToJointStateRequest
from costar_robot_msgs.srv import ServoToPoseRequest
from costar_robot_msgs.msg import Constraint
from std_srvs.srv import EmptyRequest
from std_srvs.srv import Empty as EmptySrv
from costar_task_plan.abstract.task import *
from ctp_integration.util import GetSmartGraspService
from ctp_integration.util import GetSmartReleaseService
from ctp_integration.util import GetPlanToJointStateService
from ctp_integration.util import GetPlanToHomeService
from ctp_integration.util import MakeServoToJointStateRequest
from ctp_integration.util import MakeForwardKinematicsRequest
from ctp_integration.util import GetOpenGripperService
from ctp_integration.util import GetServoModeService
from ctp_integration.util import GetPlanToPoseService
from ctp_integration.util import GetForwardKinematicsService
from ctp_integration.constants import GetColors
from ctp_integration.constants import GetHomeJointSpace
from ctp_integration.constants import GetHomePose
from ctp_integration.ros_geometry import pose_to_vec_quat_pair
from ctp_integration.ros_geometry import pose_to_vec_quat_list

from .stack_manager import StackManager

def GetHomePoseKDL():
    """ Home pose relative to the base linmk
    """
    home_vec_quat = GetHomePose()
    pose_home = kdl.Frame(
            kdl.Rotation.Quaternion(home_vec_quat[3], home_vec_quat[4], home_vec_quat[5], home_vec_quat[6]),
            kdl.Vector(home_vec_quat[0], home_vec_quat[1], home_vec_quat[2]))
    return pose_home

def GetHomeRequest():
    """ Returns a request object set to home as defined in joint space

    This is just a rosmessage object which stores data 
    representing the home location, it doesn't do anything on its own
    and must be passed to another service to take effect.
    """
    # Create joint move request:
    req = MakeServoToJointStateRequest(GetHomeJointSpace())
    return req

def GetHome():
    """ Returns a function that will move the robot to the home position when called.
    """
    go_to_js = GetPlanToJointStateService()
    req = GetHomeRequest()
    print('req home: ' + str(req))
    open_gripper = GetOpenGripperService()
    move = GetPlanToPoseService()
    servo_mode = GetServoModeService()
    def home():
        rospy.loginfo("HOME: set servo mode")
        servo_mode("servo")
        rospy.loginfo("HOME: open gripper to drop anything")
        open_gripper()
        rospy.loginfo("HOME: move to config home")
        res1 = go_to_js(req)
        if res1 is None or "failure" in res1.ack.lower():
            rospy.logerr(res1.ack)
            raise RuntimeError("HOME(): error moving to home1")
        # rospy.loginfo("HOME: move to pose over objects")
        # res2 = move(req)
        # if res2 is None or "failure" in res2.ack.lower():
        #     rospy.logerr("move failed:" + str(res2.ack))
        #     raise RuntimeError("HOME(): error moving to pose over workspace")
        rospy.loginfo("HOME: done")
    return home


def GetRandomHome():
    """ Returns a function that will move the robot a random home position when called.

    The final joint will move to a random angle for this home position.
    This makes it possible for the gripper to occasionally choose vertically
    oriented grasps in addition to horizontally oriented grasps.
    
    """
    go_to_js = GetPlanToJointStateService()
    req = GetHomeRequest()
    print('req home: ' + str(req))
    open_gripper = GetOpenGripperService()
    move = GetPlanToPoseService()
    servo_mode = GetServoModeService()
    forward_kinematics = GetForwardKinematicsService()

    def pose_response_to_vec_quat_pair(c_pose):
        c_xyz = np.array([c_pose.pose.position.x,
                    c_pose.pose.position.y,
                    c_pose.pose.position.z,])
        c_quat = np.array([c_pose.pose.orientation.x,
                    c_pose.pose.orientation.y,
                    c_pose.pose.orientation.z,
                    c_pose.pose.orientation.w,])
        return c_xyz, c_quat

    def pose_response_to_vec_quat_list(c_pose):
        """ Turn a forward kinematics pose into a vec quat in xyz qx qy qz qw
        """
        c_xyz, c_quat = pose_response_to_vec_quat_pair(c_pose)
        return np.concatenate([c_xyz, c_quat])

    def random_home():

        Q_RANDOM_HOME = [-0.202, -0.980, -1.800, -0.278, 1.460, 1.613]
        # Amount to change the angle of the final gripper joint for home
        delta_theta = 3 * np.pi / 2
        Q_RANDOM_HOME[-1] += np.random.uniform(-delta_theta, delta_theta)
        req = MakeServoToJointStateRequest(Q_RANDOM_HOME)
        fk_req = MakeForwardKinematicsRequest(Q_RANDOM_HOME)
        rospy.loginfo("GetRandomHome::random_home(): get forward kinematics")

        # this will be a ForwardKinematicsResponse
        fk_response = None
        while fk_response is None:
            fk_response = forward_kinematics(fk_req)
        pose = pose_response_to_vec_quat_list(fk_response)
        rospy.loginfo("GetRandomHome::random_home(): set servo mode")
        servo_mode("servo")
        rospy.loginfo("GetRandomHome::random_home(): open gripper to drop anything")
        open_gripper()
        rospy.loginfo("GetRandomHome::random_home(): move to config home")
        max_tries = 10
        tries = 0
        res1 = None
        while tries < max_tries and (res1 is None or "failure" in res1.ack.lower()):
            res1 = go_to_js(req)
            tries += 1
        if res1 is None or "failure" in res1.ack.lower():
            rospy.logerr(res1.ack)
            raise RuntimeError("GetRandomHome::random_home(): error moving to home: " + str(res1.ack))
        rospy.loginfo("HOME: move to pose over objects")
        
        if res1 is None or "failure" in res1.ack.lower():
            rospy.logerr(res1.ack)
            raise RuntimeError("GetRandomHome::home()(): error moving to home1")
        # rospy.loginfo("HOME: move to pose over objects")
        # res2 = move(req)
        # if res2 is None or "failure" in res2.ack.lower():
        #     rospy.logerr("move failed:" + str(res2.ack))
        #     raise RuntimeError("HOME(): error moving to pose over workspace")
        rospy.loginfo("GetRandomHome::home(): done")
        return Q_RANDOM_HOME, pose
    return random_home

def GetHomeFunctorViaPose():
    """ Deprecated. 
    Returns a function that will move the robot to the home position when called.
    """
    js_home = GetPlanToHomeService()
    req = ServoToPoseRequest()
    pose_home = GetHomePoseKDL()
    req.target = pm.toMsg(pose_home)
    open_gripper = GetOpenGripperService()
    move = GetPlanToPoseService()
    servo_mode = GetServoModeService()
    def home():
        rospy.loginfo("HOME: set servo mode")
        servo_mode("servo")
        rospy.loginfo("HOME: open gripper to drop anything")
        open_gripper()
        rospy.loginfo("HOME: move to config home")
        max_tries = 10
        tries = 0
        res1 = None
        while tries < max_tries and (res1 is None or "failure" in res1.ack.lower()):
            res1 = js_home(ServoToPoseRequest())
            tries += 1
        if res1 is None or "failure" in res1.ack.lower():
            rospy.logerr(res1.ack)
            raise RuntimeError("HOME(): error moving to home1: " + str(res1.ack))
        rospy.loginfo("HOME: move to pose over objects")

        res2 = None
        tries = 0
        while tries < max_tries and (res2 is None or "failure" in res2.ack.lower()):
            res2 = move(req)
            tries += 1
        if res2 is None or "failure" in res2.ack.lower():
            rospy.logerr("move failed:" + str(res2.ack))
            raise RuntimeError("HOME(): error moving to pose over workspace" + str(res2.ack))
        rospy.loginfo("HOME: done")
    return home

# def GetPoses():
#     '''
#     All poses have been recorded relative to /base_link. If the robot moves
#     they may no longer work.

#     This creates the poses necessary to make certain colorful patterns on the
#     bottom of the white tray.
#     '''
#     pose1_left = kdl.Frame(
#             kdl.Rotation.Quaternion(),
#             kdl.Vector(0.493, -0.202, 0.216))
#     pose2_left = kdl.Frame(
#             kdl.Rotation.Quaternion(0.610, 0.318, -0.549, 0.474),
#             kdl.Vector(0.450, -0.304, 0.216))
#     pose3_left = kdl.Frame(
#             kdl.Rotation.Quaternion(0.603, 0.320, -0.528, 0.505),
#             kdl.Vector(0.557, -0.336, 0.198))
#     pose4_left = kdl.Frame(
#             kdl.Rotation.Quaternion(0.627, 0.320, -0.518, 0.486),
#             kdl.Vector(0.594, -0.228, 0.205))
#     pose1_right = kdl.Frame(
#             kdl.Rotation.Quaternion(0.650, 0.300, -0.451, 0.533),
#             kdl.Vector(0.492, 0.013, 0.214))
#     pose2_right = kdl.Frame(
#             kdl.Rotation.Quaternion(0.645, 0.304, -0.467, 0.523),
#             kdl.Vector(0.480, -0.089, 0.210))
#     pose3_right = kdl.Frame(
#             kdl.Rotation.Quaternion(0.657, 0.283, -0.472, 0.514),
#             kdl.Vector(0.569, -0.110, 0.198))
#     pose4_right = kdl.Frame(
#             kdl.Rotation.Quaternion(0.638, 0.330, -0.421, 0.553),
#             kdl.Vector(0.596, -0.014, 0.203))
#     pose_home = kdl.Frame(
#             kdl.Rotation.Quaternion(0.711, -0.143, -0.078, 0.684),
#             kdl.Vector(0.174, -0.157, 0.682))
#     poses = {"home": pose_home,
#              "pose1_left": pose1_left,
#              "pose2_left": pose2_left,
#              "pose3_left": pose3_left,
#              "pose4_left": pose4_left,
#              "pose1_right": pose1_right,
#              "pose2_right": pose2_right,
#              "pose3_right": pose3_right,
#              "pose4_right": pose4_right,}
#     return poses

def GetGraspPose():
    # Grasp from the top, centered (roughly)
    pose = kdl.Frame(
            kdl.Rotation.Quaternion(1.,0.,0.,0.),
            kdl.Vector(-0.22, -0.02, -0.01))
    return pose

def GetStackPose():
    # Grasp from the top, centered (roughly)
    pose = GetGraspPose()
    #pose = pose * kdl.Frame(kdl.Vector(-0.052,0.0,0.0))
    pose.p[0] += -0.052
    # 2018-04-30 changing p[1] to try and eliminate
    # the tower of pisa tilted stacks we often get.
    # previous setting:
    # pose.p[1] = -0.01
    pose.p[1] = -0.02
    # pose.p[1] = 0.
    pose.p[2] = 0.
    return pose

# def GetTowerPoses():
#     pose1 = kdl.Frame(
#             kdl.Rotation.Quaternion(0.580, 0.415, -0.532, 0.456),
#             kdl.Vector(0.533, -0.202, 0.234))
    
#     poses = {"tower1": pose1,}
#     return poses

def _makeSmartPlaceRequest(poses, name):
    '''
    Helper function for making the place call
    '''
    req = None
    while req is None:
        req = SmartMoveRequest()
    req.pose = pm.toMsg(poses[name])
    req.name = name
    req.obj_class = "place"
    req.backoff = 0.05
    req.vel = 1.0
    req.accel = 0.75
    return req

def GetMoveToPose():
    class MoveToPoseScope:
        # This is a permanently defined local scope
        move_srv = None
        servo_mode = None

    # initialize once
    if MoveToPoseScope.move_srv is None:
        while MoveToPoseScope.move_srv is None:
            MoveToPoseScope.move_srv = GetPlanToPoseService()
        while MoveToPoseScope.servo_mode is None:
            MoveToPoseScope.servo_mode = GetServoModeService()

    def move(pose):
        if pose is None:
            raise RuntimeError("GetMoveToPose::move() pose parameter was invalid: None")
        req = None
        while req is None:
            req = ServoToPoseRequest()
        req.vel = 1.0
        req.accel = 0.75
        req.target = pm.toMsg(pose)
        max_tries = 10
        tries = 0
        res = None
        while tries < max_tries and (res is None or "failure" in res.ack.lower()):
            res = MoveToPoseScope.move_srv(req)
            tries += 1
        if res is None or "failure" in res.ack.lower():
            rospy.logerr("GetMoveToPose::move() failed:" + str(res.ack))
            raise RuntimeError("GetMoveToPose::move(): error moving to pose " + str(res.ack))
        
    return move

def GetUpdate(observe, collector, return_to_original_position=True):
    ''' Figure out where all the objects are.
    
    Save the current ur5 position,
    UR5 goes to the home position, 
    use vision to find the objects, 
    return back to prev position

    Parameters:
    -----------
    observe: callable functor that will call object detection
    collector: wrapper class aggregating robot info including joint state
    '''
    go_to_js = GetPlanToJointStateService()

    # Create cartesian move request:
    # we disabled this because sometimes it 
    # will go to an elbow down position,
    # which caused tons of problems.
    # pose_home = kdl.Frame(
    #         kdl.Rotation.Quaternion(0.711, -0.143, -0.078, 0.684),
    #         kdl.Vector(0.174, -0.157, 0.682))
    #req = ServoToPoseRequest()
    #req.target = pm.toMsg(pose_home)
    #move = GetPlanToPoseService()
    req = GetHomeRequest()

    servo_mode = GetServoModeService()
    def update():
        q0 = collector.q   # Save original position
        servo_mode("servo")

        # -------
        # Uncomment if you want to move to a 6DOF cartesian pose instead of a
        # joint pose
        #res = move(req)
    
        # -------
        # Move to home joint position    
        max_tries = 10
        tries = 0
        res = None
        while tries < max_tries and (res is None or "failure" in res.ack.lower()):
            res = go_to_js(req)

        if res is None or "failure" in res.ack.lower():
            rospy.logerr(res.ack)
            raise RuntimeError("UPDATE(): error moving out of the way")
            # return False
        observe()
        if return_to_original_position:
            if q0 is not None:

                max_tries = 10
                tries = 0
                res2 = None
                while tries < max_tries and (res2 is None or "failure" in res2.ack.lower()):
                    res2 = go_to_js(MakeServoToJointStateRequest(q0))
            else:
                raise RuntimeError("GetUpdate::update(): collector had joint position stored at None")
        else:
            # add a dummy motion to take a little more
            # time so logging can get an update after the
            # results of the observe call.
            res2 = go_to_js(req)
        if res2 is None or "failure" in res2.ack.lower():
            rospy.logerr(res2.ack)
            raise RuntimeError("GetUpdate::UPDATE(): error returning to original joint pose")
            # return False
        return True
    return update

def GetStackManager():
    '''
    Use addRequest() to create the graph of high-level actions to be performed.
    '''
    # smart grasp and release for stacking
    sm = StackManager()
    grasp = GetSmartGraspService()
    release = GetSmartReleaseService()
    # home and req5 are for the move to home step
    # which occurs at the very end
    home = GetPlanToJointStateService()
    req5 = GetHomeRequest()
    colors = GetColors()

    for color in colors:
        # stack is: bottom -> color2 -> color -> color3 -> top
        name = "1:grab_%s"%color
        req = _makeSmartGraspRequest(color)
        sm.addRequest(None, name, grasp, req)

        for color2 in colors:
            if color2 == color:
                continue
            else:
                # here we create one release for each possible grasped color
                name2 = "2%s:place_%s_on_%s"%(color2,color,color2)
                req2 = _makeSmartReleaseRequest(color2)
                sm.addRequest(name, name2, release, req2)

                for color3 in colors:
                    if color3 in [color, color2]:
                        continue
                    else:
                        # grasp and release block 2
                        name3 = "3%s%s:grab_%s"%(color,color2,color3)
                        req3 = _makeSmartGraspRequest(color3)
                        sm.addRequest(name2, name3, grasp, req3)
                        name4 = "4%s%s:place_%s_on_%s%s"%(color,color2,color3,color2,color)
                        req4 = _makeSmartReleaseRequest(color)
                        sm.addRequest(name3, name4, release, req4)
                        # add final move to home step for each case
                        name5 = "5%s%s%s:move_to_home"%(color,color2,color3)
                        sm.addRequest(name4, name5, home, req5)

    return sm

def GetKittingManager():
    sm = StackManager()
    grasp = GetSmartGraspService()
    release = GetSmartReleaseService()
    colors = GetColors()

    for color in colors:
        name = "1:grab_%s"%color
        req = _makeSmartGraspRequest(color)
        sm.addRequest(None, name, grasp, req)
        
        # TODO(ahundt): place block of "color" in the appropriate place
        # TODO(ahundt): grasp next block, etc.

    return sm

def _makeSmartGraspRequest(color):
    '''
    Helper function to create a grasp request via smartmove.
    '''
    req = SmartMoveRequest()
    req.pose = pm.toMsg(GetGraspPose())
    colors = GetColors()

    if not color in colors:
        raise RuntimeError("color %s not recognized" % color)
    req.obj_class = "%s_cube" % color
    req.name = "grasp_%s" % req.obj_class
    req.backoff = 0.075
    req.vel = 1.0
    req.accel = 0.75
    return req

def _makeSmartReleaseRequest(color):
    '''
    Helper function for making the place call
    '''
    colors = GetColors()
    constraint = Constraint(
            pose_variable=Constraint.POSE_Z,
            threshold=0.015,
            greater=True)
    req = SmartMoveRequest()
    req.pose = pm.toMsg(GetStackPose())
    if not color in colors:
        raise RuntimeError("color %s not recognized" % color)
    req.obj_class = "%s_cube" % color
    req.name = "place_on_%s" % color
    req.backoff = 0.075
    req.constraints = [constraint]
    req.vel = 1.0
    req.accel = 0.75
    return req

# def MakeStackTask():
#     '''
#     Create a version of the robot task for stacking two blocks.
#     '''

#     # Make services
#     rospy.loginfo("Waiting for SmartMove services...")
#     rospy.wait_for_service("/costar/SmartPlace")
#     rospy.wait_for_service("/costar/SmartGrasp")
#     place = rospy.ServiceProxy("/costar/SmartPlace", SmartMove)
#     grasp = rospy.ServiceProxy("/costar/SmartGrasp", SmartMove)

#     # Create sub-tasks for left and right
#     rospy.loginfo("Creating subtasks...")
#     pickup_left = _makePickupLeft()
#     pickup_right = _makePickupRight()
#     place_left = _makePlaceLeft()
#     place_right = _makePlaceRight()

#     # Create the task: pick up any one block and put it down in a legal
#     # position somewhere on the other side of the bin.
#     rospy.loginfo("Creating task...")
#     task = Task()
#     task.add("pickup_left", None, pickup_left)
#     task.add("pickup_right", None, pickup_right)
#     task.add("place_left", "pickup_right", place_left)
#     task.add("place_right", "pickup_left", place_right)
#     task.add("DONE", ["place_right", "place_left"], {})

#     return task

# def _makePickupLeft():
#     pickup = TaskTemplate("pickup_left", None)
#     pickup.add("home", None, _homeArgs())
#     pickup.add("detect_objects", "home", _detectObjectsArgs())

#     return {"task": pickup, "args": ["object"]}

# def _makePickupRight():
#     pickup = TaskTemplate("pickup_right", None)
#     pickup.add("home", None, _homeArgs())
#     pickup.add("detect_objects", "home", _detectObjectsArgs())

#     return {"task": pickup, "args": ["object"]}

# def _makePlaceLeft():
#     place = TaskTemplate("place_left", ["pickup_right"])
#     place.add("home", None, _homeArgs())
#     place.add("detect_objects", "home", _detectObjectsArgs())
#     return {"task": place, "args": ["frame"]}

# def _makePlaceRight():
#     place = TaskTemplate("place_right", ["pickup_left"])
#     place.add("home", None, _homeArgs())
#     place.add("detect_objects", "home", _detectObjectsArgs())
#     return {"task": place, "args": ["frame"]}

# def _pickupLeftArgs():
#     # Create args for pickup from left task
#     return {
#         "task": pickup_left,
#         "args": ["block1"],
#     }

# def _pickupRightArgs():
#     # And create args for pickup from right task
#     return {
#         "task": pickup_right,
#         "args": ["block1"],
#     }

def _homeArgs():
    return {}

def _detectObjectsArgs():
    return {}

def _checkBlocks1And2(block1,block2,**kwargs):
    '''
    Simple function that is passed as a callable "check" when creating the task
    execution graph. This makes sure we don't build branches that just make no
    sense -- like trying to put a blue block on top of itself.

    Parameters:
    -----------
    block1: unique block name, e.g. "red_block"
    block2: second unique block name, e.g. "blue_block"
    '''
    return not block1 == block2
