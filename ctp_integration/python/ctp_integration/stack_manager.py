from __future__ import print_function

import numpy as np

from .util import *
from .service_caller import ServiceCaller

class StackManager(object):
    '''
    This class creates and holds the different services we need to call to
    create the stacking task and execute it.
    '''
    objs = ["red_cube", "green_cube", "blue_cube", "yellow_cube"]

    def __init__(self, collector=None, *args, **kwargs):
        self.collector = collector
        self.service = ServiceCaller(*args, **kwargs)
        self.detect = GetDetectObjectsService()
        self.place = GetSmartPlaceService()
        self.reset()
        self.reqs = {}
        self.children = {}

    def reset(self):
        self.done = False
        self.current = None
        self.ok = True

    def addRequest(self, parents, name, srv, req):
        self.reqs[name] = (srv, req)
        if not isinstance(parents, list):
            parents = [parents]
        for parent in parents:
            if parent not in self.children:
                self.children[parent] = []
            self.children[parent].append(name)

    def tick(self):
        # Check to make sure everything is ok
        if not self.ok:
            self.done = True

        # Return status or continue
        if self.done:
            return self.ok
        elif self.service.update():
            self.done = False
            rospy.loginfo("still running: " + str(self.current))
            return
        elif self.current in self.children:
            # This one has a child to execute
            self.done = False
        else:
            self.done = True

        if self.service.ok:
            self.ok = True
        else:
            self.ok = False
            self.done = True

        if not self.done:
            children = self.children[self.current]
            idx = np.random.randint(len(children))
            next_action = children[idx]
            srv, req = self.reqs[next_action]
            if not self.service(srv, req):
                raise RuntimeError('could not start service: ' + next_action)
            self.current = next_action
        return self.done