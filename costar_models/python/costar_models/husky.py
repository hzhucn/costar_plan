from __future__ import print_function

'''
===============================================================================
Contains tools to make the sub-models for the Husky application
===============================================================================
'''

import keras.backend as K
import keras.losses as losses
import keras.optimizers as optimizers
import numpy as np
import tensorflow as tf

from keras.constraints import maxnorm
from keras.layers.advanced_activations import LeakyReLU
from keras.layers import Input, RepeatVector, Reshape
from keras.layers import UpSampling2D, Conv2DTranspose
from keras.layers import BatchNormalization, Dropout
from keras.layers import Dense, Conv2D, Activation, Flatten
from keras.layers import Lambda
from keras.layers.merge import Add, Multiply
from keras.layers.merge import Concatenate
from keras.losses import binary_crossentropy
from keras.models import Model, Sequential
from keras.optimizers import Adam
from keras.constraints import max_norm

from .planner import *
from .data_utils import *

def HuskyNumOptions():
    return 5

def HuskyNullOption():
    return 4

def GetHuskyActorModel(x, num_options, pose_size,
        dropout_rate=0.5, batchnorm=True):
    '''
    Make an "actor" network that takes in an encoded image and an "option"
    label and produces the next command to execute.
    '''
    xin = Input([int(d) for d in x.shape[1:]], name="actor_h_in")
    x0in = Input([int(d) for d in x.shape[1:]], name="actor_h0_in")

    pose_in = Input((pose_size,), name="actor_pose_in")
    option_in = Input((num_options,), name="actor_o_in")
    x = xin
    x0 = x0in
    dr, bn = dropout_rate, False
    use_lrelu = False

    x = Concatenate(axis=-1)([x, x0])
    x = AddConv2D(x, 32, [3,3], 1, dr, "same", lrelu=use_lrelu, bn=bn)

    # Add arm, gripper
    y = pose_in
    y = AddDense(y, 32, "relu", 0., output=True, constraint=3)
    x = TileOnto(x, y, 32, (8,8), add=False)
    x = AddConv2D(x, 64, [3,3], 1, dr, "valid", lrelu=use_lrelu, bn=bn)

    # Add arm, gripper
    y2 = AddDense(option_in, 64, "relu", 0., output=True, constraint=3)
    x = TileOnto(x, y2, 64, (6,6), add=False)
    x = AddConv2D(x, 128, [3,3], 1, dr, "valid", lrelu=use_lrelu, bn=bn)
    x = AddConv2D(x, 64, [3,3], 1, dr, "valid", lrelu=use_lrelu, bn=bn)

    x = Flatten()(x)
    x = AddDense(x, 512, "relu", dr, output=True, bn=bn)
    x = AddDense(x, 512, "relu", dr, output=True, bn=bn)    # Same setup as the state decoders


    pose = AddDense(x, pose_size, "linear", 0., output=True)
    actor = Model([x0in, xin, option_in, pose_in], [pose], name="actor")
    return actor

def GetHuskyPoseModel(x, num_options, pose_size,
        dropout_rate=0.5, batchnorm=True):
    '''
    Make an "actor" network that takes in an encoded image and an "option"
    label and produces the next command to execute.
    '''
    xin = Input([int(d) for d in x.shape[1:]], name="pose_h_in")
    x0in = Input([int(d) for d in x.shape[1:]], name="pose_h0_in")

    pose_in = Input((pose_size,), name="pose_pose_in")
    option_in = Input((num_options,), name="pose_o_in")
    x = xin
    x0 = x0in
    dr, bn = dropout_rate, False
    use_lrelu = False

    x = Concatenate(axis=-1)([x, x0])
    x = AddConv2D(x, 32, [3,3], 1, dr, "same", lrelu=use_lrelu, bn=bn)

    # Add arm, gripper
    y = pose_in
    y = AddDense(y, 32, "relu", 0., output=True, constraint=3)
    x = TileOnto(x, y, 32, (8,8), add=False)
    x = AddConv2D(x, 64, [3,3], 1, dr, "valid", lrelu=use_lrelu, bn=bn)

    # Add arm, gripper
    y2 = AddDense(option_in, 64, "relu", 0., output=True, constraint=3)
    x = TileOnto(x, y2, 64, (6,6), add=False)
    x = AddConv2D(x, 128, [3,3], 1, dr, "valid", lrelu=use_lrelu, bn=bn)
    x = AddConv2D(x, 64, [3,3], 1, dr, "valid", lrelu=use_lrelu, bn=bn)

    x = Flatten()(x)
    x = AddDense(x, 512, "relu", dr, output=True, bn=bn)
    x = AddDense(x, 512, "relu", dr, output=True, bn=bn)    # Same setup as the state decoders


    pose = AddDense(x, pose_size, "linear", 0., output=True)
    pose = Model([x0in, xin, option_in, pose_in], [pose], name="pose")
    return pose

def GetPolicyHuskyData(num_options, option, image, pose, action, label, *args,
        **kwargs):
    I = np.array(image) / 255.
    p = np.array(pose)
    a = np.array(action)
    idx = label == option
    if np.count_nonzero(idx) > 0:
        I = I[idx]
        p = p[idx]
        a = a[idx]
        I0 = I[0,:,:,:]
        length = I.shape[0]
        I0 = np.tile(np.expand_dims(I0,axis=0),[length,1,1,1]) 
        return [I0, I, p], [a]
    else:
        return [], []

def GetConditionalHuskyData(validate, no_disc, num_options, image, pose, action, label,
        prev_label, goal_image, goal_pose, value, *args, **kwargs):
    I = np.array(image) / 255.
    p = np.array(pose)
    a = np.array(action)
    I_target = np.array(goal_image) / 255.
    q_target = np.array(goal_pose)
    oin = np.array(prev_label)
    o1 = np.array(label)
    v = np.array(np.array(value) > 1.,dtype=float)

    I_target2, o2 = GetNextGoal(I_target, o1)
    I0 = I[0,:,:,:]
    length = I.shape[0]
    I0 = np.tile(np.expand_dims(I0,axis=0),[length,1,1,1]) 
    oin_1h = np.squeeze(ToOneHot2D(oin, num_options))
    o2_1h = np.squeeze(ToOneHot2D(o2, num_options))
    
    if validate:
        o1_1h = np.squeeze(ToOneHot2D(o1, num_options))
        return ([I0, I, o1, o2, oin],
             [I_target, I_target2, o1_1h, v, a, o2_1h])
    elif no_disc:
        return [I0, I, o1, o2, oin], [I_target, I_target2,]
    else:
        return [I0, I, o1, o2, oin], [I_target, I_target2, o2_1h]

def MakeHuskyPolicy(model, encoder, image, pose, action, option, verbose=True):
    '''
    Create a single policy corresponding to option 

    Parameters:
    -----------
    model: definition of model/training configuration
    encoder: converts to hidden representation
    image: example of image data
    pose: example of pose data
    action: example of action data
    option: index of the policy to create
    verbose: should we print model info?
    '''
    img_shape = image.shape[1:]
    pose_size = pose.shape[-1]
    action_size = action.shape[-1]
    if verbose:
        print("pose_size =", pose_size, "action_size =", action_size)

    img_in = Input(img_shape,name="policy_img_in")
    img0_in = Input(img_shape,name="policy_img0_in")
    pose_in = Input((pose_size,), name="pose_in")
    ins = [img0_in, img_in, pose_in]

    dr, bn = model.dropout_rate, False
    use_lrelu = False

    x = encoder(img_in)
    x0 = encoder(img0_in)
    y = pose_in

    x = Concatenate(axis=-1)([x, x0])
    x = AddConv2D(x, 32, [3,3], 1, dr, "same", lrelu=True, bn=bn)

    y = AddDense(y, 32, "relu", 0., output=True, constraint=3)
    x = TileOnto(x, y, 32, (8,8), add=False)

    x = AddConv2D(x, 32, [3,3], 1, dr, "valid", lrelu=True, bn=bn)

    x = Flatten()(x)

    x = AddDense(x, 512, "lrelu", dr, output=True, bn=bn)
    x = AddDense(x, 512, "lrelu", dr, output=True, bn=bn)

    action_out = Dense(action_size, name="action_out")(x)

    policy = Model(ins, [action_out])
    policy.compile(loss=model.loss, optimizer=model.getOptimizer())
    if verbose:
        policy.summary()
    return policy


