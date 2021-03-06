
from .multi_regression_model import RobotMultiFFRegression
from .multi_tcn_regression_model import RobotMultiTCNRegression
from .multi_lstm_regression import RobotMultiLSTMRegression
from .multi_conv_lstm_regression import RobotMultiConvLSTMRegression
from .multi_autoencoder_model import RobotMultiAutoencoder
from .multi_hierarchical import RobotMultiHierarchical
from .multi_policy import RobotPolicy

# Model for sampling predictiosn
from .multi_sampler import RobotMultiPredictionSampler
from .multi_sequence import RobotMultiSequencePredictor
from .image_sampler import RobotMultiImageSampler
from .pretrain_image import PretrainImageAutoencoder
from .pretrain_sampler import PretrainSampler
from .pretrain_image_gan import PretrainImageGan

# Multi stuff -- primary models
from .conditional_sampler import ConditionalSampler
from .conditional_image import ConditionalImage
from .conditional_image_gan import ConditionalImageGan
from .discriminator import Discriminator
from .secondary import Secondary

# CoSTAR
from .pretrain_image_costar import PretrainImageCostar
from .conditional_image_costar import ConditionalImageCostar
from .discriminator import CostarDiscriminator

# Jigsaws stuff
from .dvrk import *
from .pretrain_image_jigsaws import PretrainImageJigsaws
from .pretrain_image_jigsaws_gan import PretrainImageJigsawsGan
from .conditional_image_jigsaws import ConditionalImageJigsaws
from .conditional_image_gan_jigsaws import ConditionalImageGanJigsaws
from .discriminator import JigsawsDiscriminator

# Husky stuff
from .husky import *
from .husky_sampler import HuskyRobotMultiPredictionSampler
from .pretrain_image_husky import PretrainImageAutoencoderHusky
from .pretrain_image_husky_gan import PretrainImageHuskyGan
from .conditional_image_husky import ConditionalImageHusky
from .conditional_image_husky_gan import ConditionalImageHuskyGan
from .discriminator import HuskyDiscriminator
from .multi_policy import HuskyPolicy
from .secondary import HuskySecondary

def MakeModel(features, model, taskdef, **kwargs):
    '''
    This function will create the appropriate neural net based on images and so
    on.

    Parameters:
    -----------
    features: string describing the set of features (inputs) we are using.
    model: string describing the particular method that should be applied.
    taskdef: a (simulation) task definition used to extract specific
             parameters.
    '''
    # set up some image parameters
    if features in ['rgb', 'multi']:
        nchannels = 3
    elif features in ['depth']:
        nchannels = 1

    model_instance = None
    model = model.lower()

    if features == 'multi':
        '''
        This set of features has three components that may be handled
        differently:
            - image input
            - current arm pose
            - current gripper state

        All of these models are expected to use the three fields:
            ["features", "arm", "gripper"]
        As a part of their state input.
        '''
        if model == 'predictor':
            model_instance = RobotMultiPredictionSampler(taskdef,
                    model=model,
                    **kwargs)
        elif model == 'ff_regression':
            model_instance = RobotMultiFFRegression(taskdef,
                    model=model,
                    **kwargs)
        elif model == 'tcn_regression':
            model_instance = RobotMultiTCNRegression(taskdef,
                    model=model,
                    **kwargs)
        elif model == 'lstm_regression':
            model_instance = RobotMultiLSTMRegression(taskdef,
                    model=model,
                    **kwargs)
        elif model == 'conv_lstm_regression':
            model_instance = RobotMultiConvLSTMRegression(taskdef,
                    model=model,
                    **kwargs)
        elif model == "hierarchical":
            model_instance = RobotMultiHierarchical(taskdef,
                    model=model,
                    **kwargs)
        elif model == "policy":
            model_instance = RobotPolicy(taskdef,
                    model=model,
                    **kwargs)
        elif model == "husky_predictor":
            model_instance = HuskyRobotMultiPredictionSampler(taskdef,
                    model=model,
                    **kwargs)
        elif model == "goal_sampler":
            model_instance = RobotMultiGoalSampler(taskdef, model=model,
                    **kwargs)
        elif model == "image_sampler":
            model_instance = RobotMultiImageSampler(taskdef, model=model,
                    **kwargs)
        elif model == "pretrain_image_encoder":
            model_instance = PretrainImageAutoencoder(taskdef, model=model,
                    **kwargs)
        elif model == "pretrain_state_encoder":
            model_instance = PretrainStateAutoencoder(taskdef, model=model,
                    **kwargs)
        elif model == "pretrain_sampler":
            model_instance = PretrainSampler(taskdef, model=model, **kwargs)
        elif model == "conditional_sampler":
            model_instance = ConditionalSampler(taskdef, model=model, **kwargs)
        elif model == "conditional_image":
            model_instance = ConditionalImage(taskdef, model=model, **kwargs)
        elif model == "conditional_image_gan":
            model_instance = ConditionalImageGan(taskdef, model=model, **kwargs)
        elif model == "pretrain_image_gan":
            model_instance = PretrainImageGan(taskdef, model=model, **kwargs)
        elif model == "discriminator":
            model_instance = Discriminator(False, taskdef, model=model, **kwargs)
        elif model == "goal_discriminator":
            model_instance = Discriminator(True, taskdef, model=model, **kwargs)
        elif model == "secondary":
            model_instance = Secondary(taskdef, model=model, **kwargs)
    elif features == "jigsaws":
        '''
        These models are all meant for use with the JHU-JIGSAWS dataset. This
        is a surgical activity data set containing suturing, needle passing,
        and a few other tasks.
        '''
        if model == "pretrain_image_encoder":
            model_instance = PretrainImageJigsaws(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "pretrain_image_gan":
            model_instance = PretrainImageJigsawsGan(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "conditional_image":
            model_instance = ConditionalImageJigsaws(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "conditional_image_gan":
            model_instance = ConditionalImageGanJigsaws(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "discriminator":
            model_instance = JigsawsDiscriminator(False, taskdef,
                    features=features,
                    model=model, **kwargs)
        elif model == "goal_discriminator":
            model_instance = JigsawsDiscriminator(True, taskdef,
                    features=features,
                    model=model, **kwargs)

        # Global setup for all JIGSAWS data:
        # - images are set up as jpegs
        # - number of options, etc.
        model_instance.load_jpeg = True
        model_instance.num_options = SuturingNumOptions()

    elif features == "costar":
        '''
        These are CoSTAR models -- meant to be used with data collected from the
        real robot.
        '''
        if model == "pretrain_image_encoder":
            model_instance = PretrainImageCostar(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "conditional_image":
            model_instance = ConditionalImageCostar(taskdef,
                    features=features,
                    model=model,
                    **kwargs)
        elif model == "discriminator":
            model_instance = CostarDiscriminator(False, taskdef,
                    features=features,
                    model=model, **kwargs)
        elif model == "goal_discriminator":
            model_instance = CostarDiscriminator(True, taskdef,
                    features=features,
                    model=model, **kwargs)

        # Global setup for CoSTAR
        # this one uses jpegs
        model_instance.load_jpeg = True
        # 2018-06-05 incremented null_option and num_options by 1 because of new move_to_home option
        model_instance.null_option = 41
        model_instance.num_options = 42
        model_instance.validation_split = 0.2

    elif features == "husky":
        '''
        Husky simulator. This is a robot moving around on a 2D plane, so our
        action and state spaces are slightly different.
        '''
        if model == "pretrain_image_encoder":
            model_instance = PretrainImageAutoencoderHusky(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "policy":
            model_instance = HuskyPolicy(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "pretrain_image_gan":
            model_instance = PretrainImageHuskyGan(taskdef,
                    model=model,
                    features=features,
                    **kwargs)
        elif model == "predictor":
            model_instance = HuskyRobotMultiPredictionSampler(taskdef,
                    features=features,
                    model=model,
                    **kwargs)
        elif model == "conditional_image":
            model_instance = ConditionalImageHusky(taskdef,
                    features=features,
                    model=model,
                    **kwargs)
        elif model == "conditional_image_gan":
            model_instance = ConditionalImageHuskyGan(taskdef,
                    features=features,
                    model=model,
                    **kwargs)
        elif model == "discriminator":
            model_instance = HuskyDiscriminator(False, taskdef,
                    features=features,
                    model=model, **kwargs)
        elif model == "goal_discriminator":
            model_instance = HuskyDiscriminator(True, taskdef,
                    features=features,
                    model=model, **kwargs)
        elif model == "secondary":
            model_instance = HuskySecondary(taskdef,
                    features=features,
                    model=model, **kwargs)

        # Set global options for the husky robot simulation
        # It uses four options -- barrier, cone, hydrant, and dumpster
        # Images are bitmaps stored as numpy arrays
        model_instance.load_jpeg = False
        model_instance.num_options = HuskyNumOptions()
        model_instance.null_option = HuskyNullOption()

    # If we did not create a model then die.
    if model_instance is None:
        if features is None:
            features = "n/a"
        raise NotImplementedError("Combination of model {} and features {}"
                                  " is not currently supported by CTP."
                                  .format(model, features))

    return model_instance

def GetModels():
    return [None,
            "ff_regression", # regression model; just a dense net
            "tcn_regression", # ff regression model with a TCN
            "lstm_regression", # lstm regression model
            "conv_lstm_regression", # lstm regression model
            "predictor", # sampler NN to generate image goals
            "hierarchical", # hierarchical policy for planning
            "policy", # single policy hierarchical
            "goal_sampler", # samples goals instead of everything else
            "image_sampler", #just learn to predict goal image
            "pretrain_image_encoder", # tool for pretraining images
            "pretrain_state_encoder", # tool for pretraining states
            "pretrain_sampler", # tool for pretraining the sampler
            "conditional_sampler", # just give the condition
            "conditional_image", # just give label and predict image
            "conditional_image_gan", # just give label and predict image
            "pretrain_image_gan",
            "discriminator",
            "goal_discriminator",
            "secondary", # train secondary models like value, actor, state, etc
            ]

