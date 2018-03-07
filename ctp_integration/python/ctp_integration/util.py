
'''
This function contains some helpful functions for different purposes.
'''

from std_srvs.srv import Empty as EmptySrv
from costar_robot_msgs.srv import SmartMove
from costar_robot_msgs.srv import ServoToJointState

import rospy

def GetDetectObjectsService(srv='/costar_perception/segmenter'):
    '''
    Get a service that will update object positions

    Parameters:
    ----------
    srv: service, defaults to the correct name for costar
    '''
    rospy.wait_for_service(srv)
    return rospy.ServiceProxy(srv, EmptySrv)

def GetCloseGripperService(srv="/costar/gripper/close"):
    rospy.wait_for_service(srv)
    return rospy.ServiceProxy(srv, EmptySrv)

def GetCloseGripperService(srv="/costar/gripper/open"):
    rospy.wait_for_service(srv)
    return rospy.ServiceProxy(srv, EmptySrv)

def GetSmartGraspService(srv="/costar/SmartGrasp"):
    rospy.wait_for_service(srv)
    return rospy.ServiceProxy(srv, SmartMove)

def GetSmartPlaceService(srv="/costar/SmartPlace"):
    rospy.wait_for_service(srv)
    return rospy.ServiceProxy(srv, SmartMove)

def GetSmartGraspService(srv="/costar/ServoToJointState"):
    rospy.wait_for_service(srv)
    return rospy.ServiceProxy(srv, ServoToJointState)
