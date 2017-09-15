from __future__ import print_function

'''
Chris Paxton
(c) 2017 Johns Hopkins University
See license for details
'''
import numpy as np
import os

import keras.backend as K
import keras.optimizers as optimizers

class AbstractAgentBasedModel(object):
    '''
    In CTP, models are trained based on output from a particular agent --
    possibly the null agent (which would just load a dataset). The Agent class
    will also provide the model with a way to collect data or whatever.
    '''

    def __init__(self, taskdef=None, lr=1e-4, epochs=1000, iter=1000, batch_size=32,
            clipnorm=100., show_iter=0, pretrain_iter=5,
            optimizer="sgd", model_descriptor="model", zdim=16, features=None,
            steps_per_epoch=300, validation_steps=100, choose_initial=5,
            num_generator_files=3,
            task=None, robot=None, model="", model_directory="./", *args,
            **kwargs):

        if lr == 0 or lr < 1e-30:
            raise RuntimeError('You probably did not mean to set ' + \
                               'learning rate to %f'%lr)
        elif lr > 1.:
            raise RuntimeError('Extremely high learning rate: %f' % lr)

        self.lr = lr
        self.iter = iter
        self.choose_initial = choose_initial
        self.show_iter = show_iter
        self.steps_per_epoch = steps_per_epoch
        self.pretrain_iter = pretrain_iter
        self.noise_dim = zdim
        self.epochs = epochs
        self.batch_size = batch_size
        self.optimizer = optimizer
        self.validation_steps = validation_steps
        self.model_descriptor = model_descriptor
        self.task = task
        self.features = features
        self.robot = robot
        self.name_prefix = "%s_%s"%(model, self.model_descriptor)
        self.clipnorm = float(clipnorm)
        self.taskdef = taskdef
        self.model_directory = os.path.expanduser(model_directory)
        self.name = os.path.join(self.model_directory, self.name_prefix)
        self.num_generator_files = num_generator_files
        if self.task is not None:
            self.name += "_%s"%self.task
        if self.features is not None:
            self.name += "_%s"%self.features   

        # Define previous option for when executing -- this should default to
        # None, set to 2 for testing only
        self.prev_option = 2

        # default: store the whole model here.
        # NOTE: this may not actually be where you want to save it.
        self.model = None

        print("===========================================================")
        print("==========   TRAINING CONFIGURATION REPORT   ==============")
        print("===========================================================")
        print("Name =", self.name_prefix)
        print("Features = ", self.features)
        print("Robot = ", self.robot)
        print("Task = ", self.task)
        print("Model type = ", model)
        print("Model description = ", self.model_descriptor)
        print("Model directory = ", self.model_directory)
        print("Models saved with prefix = ", self.name)
        print("-----------------------------------------------------------")
        print("Iterations =", self.iter)
        print("Epochs =", self.epochs)
        print("Steps per epoch =", self.steps_per_epoch)
        print("Batch size =", self.batch_size)
        print("Noise dim =", self.noise_dim)
        print("Show images every %d iter"%self.show_iter)
        print("Pretrain for %d iter"%self.pretrain_iter)
        print("p(Generator sample first frame) = 1/%d"%(self.choose_initial))
        print("-----------------------------------------------------------")
        print("Optimizer =", self.optimizer)
        print("Learning Rate = ", self.lr)
        print("Clip Norm = ", self.clipnorm)
        print("===========================================================")

        try:
            if not os.path.exists(self.model_directory):
                os.makedirs(self.model_directory)
        except OSError as e:
            print("Could not create dir", self.model_directory)
            raise e

    def trainGenerator(self, dataset):
        raise NotImplementedError('trainGenerator(dataset) unsupported.')

    def testGenerator(self, dataset):
        raise NotImplementedError('testGenerator(dataset) unsupported.')

    def _numLabels(self):
        '''
        Use the taskdef to get total number of labels
        '''
        if self.taskdef is None:
            raise RuntimeError('must provide a task definition including' + \
                               'all actions and descriptions.')
        return self.taskdef.numActions()

    def train(self, agent, *args, **kwargs):
        raise NotImplementedError('train() takes an agent.')

    def trainFromGenerators(self, train_generator, test_generator, data=None):
        raise NotImplementedError('trainFromGenerators() not implemented.')

    def _getData(self, *args, **kwargs):
        '''
        This function should process all the data you need for a generator.
        ''' 
        raise NotImplementedError('_getData() requires a dataset.')
        
    def trainGenerator(self, dataset):
        while True:
            data = {}
            for _ in range(self.num_generator_files):
                fdata = dataset.sampleTest()
                for key, value in fdata.items():
                    if key not in data:
                        data[key] = value
                    if value.shape[0] == 0:
                        continue
                    data[key] = np.concatenate([data[key],value],axis=0)
            yield self._yield(data)

    def testGenerator(self, dataset):
        if self.validation_steps is None:
            # update the validation steps if we did not already set it --
            # something proportional to the amount of validation data we have
            self.validation_steps = len(dataset.test) + 1
        while True:
            data = {}
            for _ in range(self.num_generator_files):
                fdata = dataset.sampleTest()
                for key, value in fdata.items():
                    if key not in data:
                        data[key] = value
                    if value.shape[0] == 0:
                        continue
                    data[key] = np.concatenate([data[key],value],axis=0)
            yield self._yield(data)

    def _yield(self, data):
            features, targets = self._getData(**data)
            n_samples = features[0].shape[0]
            idx = np.random.randint(n_samples,size=(self.batch_size,))
            r = np.random.randint(self.choose_initial)
            if r > 0:
                idx[0] = 0
            return ([f[idx] for f in features],
                    [t[idx] for t in targets])

    def save(self):
        '''
        Save to a filename determined by the "self.name" field.
        '''
        if self.model is not None:
            print("saving to " + self.name)
            self.model.save_weights(self.name + ".h5f")
        else:
            raise RuntimeError('save() failed: model not found.')

    def load(self, world, *args, **kwargs):
        '''
        Load will use the current model descriptor and name to load the file
        that you are interested in, at least for now.
        '''
        if world is not None:
            control = world.zeroAction()
            reward = world.initial_reward
            features = world.computeFeatures()
            action_label = np.zeros((self._numLabels(),))
            example = 0
            done = False
            data = world.vectorize(control, features, reward, done, example,
                 action_label)
            kwargs = {}
            for k, v in data:
                kwargs[k] = np.array([v])
            self._makeModel(**kwargs)
        else:
            self._makeModel(**kwargs)
        self._loadWeights()

    def _makeModel(self, *args, **kwargs):
        '''
        Create the model based on some data set shape information.
        '''
        raise NotImplementedError('_makeModel() not supported yet.')

    def _loadWeights(self, *args, **kwargs):
        '''
        Load model weights. This is the default load weights function; you may
        need to overload this for specific models.
        '''
        if self.model is not None:
            print("using " + self.name + ".h5f")
            self.model.load_weights(self.name + ".h5f")
        else:
            raise RuntimeError('_loadWeights() failed: model not found.')

    def getOptimizer(self):
        '''
        Set up a keras optimizer based on whatever settings you provided.
        '''
        optimizer = optimizers.get(self.optimizer)
        try:
            optimizer.lr = K.variable(self.lr, name='lr')
            optimizer.clipnorm = self.clipnorm
        except Exception:
            print('WARNING: could not set all optimizer flags')
        return optimizer

    def predict(self, world):
        '''
        Implement this to predict... something... from a world state
        observation.

        Parameters:
        -----------
        world: a single world observation.
        '''
        raise NotImplementedError('predict() not supported yet.')

    def toOneHot2D(self, f, dim):
        '''
        Convert all to one-hot vectors. If we have a "-1" label, example was
        considered unlabeled and should just get a zero...
        '''
        if len(f.shape) == 1:
            f = np.expand_dims(f, -1)
        assert len(f.shape) == 2
        shape = f.shape + (dim,)
        oh = np.zeros(shape)
        #oh[np.arange(f.shape[0]), np.arange(f.shape[1]), f]
        for i in range(f.shape[0]):
            for j in range(f.shape[1]):
                idx = f[i,j]
                if idx >= 0:
                    oh[i,j,idx] = 1.
        return oh


class HierarchicalAgentBasedModel(AbstractAgentBasedModel):

    '''
    This version of the model will save a set of associated policies, all
    trained via direct supervision. These are:

    - transition model (x, u) --> (x'): returns next expected state
    - supervisor policy (x, o) --> (o'): returns next high-level action to take
    - control policies (x, o) --> (u): return the next action to take

    The supervisor takes in the previous labeled action, not the one currently
    being executed; it takes in 0 if no action has been performed yet.
    '''

    def __init__(self, taskdef, *args, **kwargs):
        super(HierarchicalAgentBasedModel, self).__init__(taskdef, *args, **kwargs)
        self.num_actions = 0

        # =====================================================================
        # Experimental hierarchical policy models:
        # Predictor model learns the transition function T(x, u) --> (x')
        self.predictor = None
        # Supervisor learns the high-level policy pi(x, o_-1) --> o
        self.supervisor = None
        # Baseline is just a standard behavioral cloning policy pi(x) --> u
        self.baseline = None
        # All low-level policies pi(x,o) --> u
        self.policies = []

        # Helper models -- may be created or not (experimental code)
        self.predict_goal = None
        self.predict_next = None
        
    def _makeOption1h(self, option):
        opt_1h = np.zeros((1,self._numLabels()))
        opt_1h[0,option] = 1.
        return opt_1h

    def _makeSupervisor(self, feature):
        '''
        This needs to create a supervisor. This one maps from input to the
        space of possible action labels.
        '''
        raise NotImplementedError('does not create supervisor yet')

    def _makePolicy(self, features, action, hidden=None):
        '''
        Create the control policy mapping from features (or hidden) to actions.
        '''
        raise NotImplementedError('does not create policy yet')

    def _makeHierarchicalModel(self, features, action, label, *args, **kwargs):
        '''
        This is the helper that actually sets everything up.
        '''
        num_labels = self._numLabels()
        hidden, self.supervisor, self.predictor, \
                self.predict_goal, self.predict_next = \
                self._makeSupervisor(features)

        # These are the outputs to other layers -- this is the hidden world
        # state.
        hidden.trainable = False
        return

        # Learn a baseline for comparisons and whatnot
        self.baseline = self._makePolicy(features, action, hidden)

        # We assume label is one-hot. This is the same as the "baseline"
        # policy, but we learn a separate one for each high-level action
        # available to the actor.
        self.policies = []
        for i in xrange(num_labels):
            self.policies.append(self._makePolicy(features, action, hidden))

    def _fitSupervisor(self, features, label):
        '''
        Fit a high-level policy that tells us which low-level action we could
        be taking at any particular time.
        '''
        self._fixWeights()
        self.supervisor.compile(
                loss="binary_crossentropy",
                optimizer=self.getOptimizer())
        self.supervisor.summary()
        self.supervisor.fit(features, [label], epochs=self.epochs)

    def _fitPolicies(self, features, label, action):
        '''
        Fit different policies for each model.
        '''
        # Divide up based on label
        idx = np.argmax(np.squeeze(label[:,-1,:]),axis=-1)

        self._fixWeights()

        for i, model in enumerate(self.policies):

            optimizer = self.getOptimizer()
            model.compile(loss="mse", optimizer=optimizer)

            # select data for this model
            if isinstance(features, list):
                x = [f[idx==i] for f in features]
            else:
                x = features[idx==i]
            if isinstance(action, list):
                a = [ac[idx==i] for ac in action]
                if len(a) == 0 or a[0].shape[0] == 0:
                    print('WARNING: no examples for %d'%i)
                    continue
            else:
                a = action[idx==i]
                if a.shape[0] == 0:
                    print('WARNING: no examples for %d'%i)
                    continue
            model.fit(x, a, epochs=self.epochs)

    def _fixWeights(self):
        self.predictor.trainable = False
        for layer in self.predictor.layers:
            layer.trainable = False

    def _unfixWeights(self):
        self.predictor.trainable = True
        for layer in self.predictor.layers:
            layer.trainable = True

    def _fitPredictor(self, features, targets):
        '''
        Can be different for every set of features so...
        '''
        self._unfixWeights()
        self.predictor.compile(
                loss="mse",
                optimizer=self.getOptimizer())
        self.predictor.fit(features, targets)
        self._fixWeights()

    def _fitBaseline(self, features, action):
        self._fixWeights()
        self.baseline.compile(loss="mse", optimizer=self.getOptimizer())
        self.baseline.fit(features, action, epochs=self.epochs)

    def save(self):
        '''
        Save to a filename determined by the "self.name" field.
        '''
        if self.predictor is not None:
            print("saving to " + self.name)
            self.predictor.save_weights(self.name + "_predictor.h5f")
            if self.supervisor is not None:
                self.supervisor.save_weights(self.name + "_supervisor.h5f")
            if self.baseline is not None:
                self.baseline.save_weights(self.name + "_baseline.h5f")
            for i, policy in enumerate(self.policies):
                policy.save_weights(self.name + "_policy%02d.h5f"%i)
        else:
            raise RuntimeError('save() failed: model not found.')

    def _loadWeights(self, *args, **kwargs):
        '''
        Load model weights. This is the default load weights function; you may
        need to overload this for specific models.
        '''
        if self.predictor is not None:
            print("----------------------------")
            print("using " + self.name + " to load")
            try:
                self.baseline.load_weights(self.name + "_baseline.h5f")
            except Exception as e:
                print(e)
            for i, policy in enumerate(self.policies):
                try:
                    policy.load_weights(self.name + "_policy%02d.h5f"%i)
                except Exception as e:
                    print(e)
            try:
                self.supervisor.load_weights(self.name + "_supervisor.h5f")
            except Exception as e:
                print(e)
            self.predictor.load_weights(self.name + "_predictor.h5f")
        else:
            raise RuntimeError('_loadWeights() failed: model not found.')

    def reset(self):
        self.prev_option = None

    def predict(self, world):
        '''
        This is the basic, "dumb" option. Compute the next option/policy to
        execute by evaluating the supervisor, then just call that model.
        '''
        features = world.initial_features #getHistoryMatrix()
        if isinstance(features, list):
            assert len(features) == len(self.supervisor.inputs) - 1
        else:
            features = [features]
        if self.supervisor is None:
            raise RuntimeError('high level model is missing')
        features = [f.reshape((1,)+f.shape) for f in features]
        res = self.supervisor.predict(features +
                [self._makeOption1h(self.prev_option)])
        next_policy = np.argmax(res)

        print("Next policy = ", next_policy,)
        if self.taskdef is not None:
            print("taskdef =", self.taskdef.name(next_policy))
        one_hot = np.zeros((1,self._numLabels()))
        one_hot[0,next_policy] = 1.
        features2 = features + [one_hot]

        # ===============================================
        # INTERMEDIATE CODE PLEASE REMOVE
        res = self.predictor.predict(features2)
        import matplotlib.pyplot as plt
        plt.subplot(2,1,1)
        plt.imshow(features[0][0])
        plt.subplot(2,1,2)
        plt.imshow(res[0][0])
        plt.ion()
        plt.show(block=False)
        plt.pause(0.01)
        # ===============================================

        # Retrieve the next policy we want to execute
        policy = self.policies[next_policy]

        # Update previous option -- which one did we end up choosing, and which
        # policy did we execute?
        self.prev_option = next_policy

        # Evaluate this policy to get the next action out
        return policy.predict(features)

