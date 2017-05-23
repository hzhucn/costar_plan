from costar_task_plan.abstract import AbstractReward
from costar_task_plan.models import GMM

class DemoReward(AbstractReward):
    '''
    In this case, we want to learn a controller that sticks as close as
    possible to the demonstrated trajectory.

    We load in a demonstration or a set of demonstrations, and then we use the
    distance to the mean path as a cost function during our learning process.
    In general, this cost function is:
      R(x, u, t) = - log p (x, u | mu, Sigma, t)
    '''

    def __init__(self, models={}, *args, **kwargs):
        '''
        Take a set of models decribing expected features over time
        Compute the best ones
        '''
        self.models = models

    def __call__(self, world):
        '''
        Look at the features for this possible world and determine how likely
        they seem to be under our given feature model.
        '''
        # get world features for this state
        f = world.initial_features
        model = self.models[world.actors[0].state.reference.skill_name]
        return gmm.score(f)
