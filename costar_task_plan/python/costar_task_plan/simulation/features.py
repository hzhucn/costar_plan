from costar_task_plan.abstract.features import AbstractFeatures

import numpy as np

def GetAvailableFeatures():
    return ['null', 'depth']

def GetFeatures(features):
    '''
    Returns a particular task definition in the simulation.
    '''
    try:
        return {
            'null': EmptyFeatures(),
            'depth': DepthImageFeatures(),
        }[features]
    except KeyError, e:
        raise NotImplementedError('Feature function %s not implemented!' % task)

class EmptyFeatures(AbstractFeatures):
  def compute(self, world, state):
      return np.array([0])

  def updateBounds(self, world):
      pass

  def getBounds(self):
      return np.array([0]), np.array([0])

class DepthImageFeatures(AbstractFeatures):

  def compute(self, world, state):
      return world.cameras[0].capture().depth

  def updateBounds(self, world):
    raise Exception('feature.updateBounds not yet implemented!')

  def getBounds(self):
    raise Exception('feature.getBounds not yet implemented!')
