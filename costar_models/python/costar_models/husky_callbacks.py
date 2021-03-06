from __future__ import print_function

import os
import keras
import matplotlib.pyplot as plt
import numpy as np

DEFAULT_MODEL_DIRECTORY = os.path.expanduser('~/.costar/models')


class HuskyPredictorShowImage(keras.callbacks.Callback):
    '''
    Save an image showing what some number of frames and associated predictions
    will look like at the end of an epoch.
    '''

    def __init__(self, predictor, features, targets,
            model_directory=DEFAULT_MODEL_DIRECTORY,
            num_hypotheses=4,
            verbose=False,
            min_idx=0, max_idx=66, step=11, **kwargs):
        '''
        Set up a data set we can use to output validation images.

        Parameters:
        -----------
        predictor: model used to generate predictions
        targets: training target info, in compressed form
        num_hypotheses: how many outputs to expect
        verbose: print out extra information
        '''
        self.verbose = verbose
        self.predictor = predictor
        self.idxs = range(min_idx, max_idx, step)
        self.num = len(self.idxs)
        self.features = [f[self.idxs] for f in features]
        self.targets = [np.squeeze(t[self.idxs]) for t in targets]
        self.num_hypotheses = num_hypotheses
        self.directory = os.path.join(model_directory,'debug')
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)


        self.logfile = open(os.path.join(self.directory,"pose_log.csv"),'w')

    def on_epoch_end(self, epoch, logs={}):
        # take the model and print it out
        if epoch == 0:
            msg = "epoch, idx, hypothesis, pose_x, pose_y, pose_z, pose_r, pose_p, pose_y, label\n"
            self.logfile.write(msg)

        imglen = 64*64*3
        #img = self.targets[0][:,:imglen]
        if len(self.targets[0].shape) == 2:
          img = self.targets[0][:,:imglen]
        elif len(self.targets[0].shape) == 3:
            assert self.targets[0].shape[1] == 1
            img = self.targets[0][:,0,:imglen]
        else:
            raise RuntimeError('did not recognize big train target shape; '
                               'are you sure you meant to use this callback'
                               'and not a normal image callback?')


        img = np.reshape(img, (self.num,64,64,3))




        data, poses, label, next_option, value = self.predictor.predict(self.features)

        if self.verbose:
            print("============================")


        for j in range(self.num):
            name = os.path.join(self.directory,
                    "predictor_epoch%d_result%d.png"%(self.epoch+1,j))
            if self.verbose:
                print("----------------")
                print(name)
            fig = plt.figure(figsize=(3+int(1.5*self.num_hypotheses),2))
            plt.subplot(1,2+self.num_hypotheses,1)
            plt.title('Input Image')
            plt.imshow(self.features[0][j])
            plt.subplot(1,2+self.num_hypotheses,2+self.num_hypotheses)
            plt.title('Observed Goal')
            plt.imshow(img[j])
            for i in range(self.num_hypotheses):

                msg = str(self.epoch+1) + "," + str(j) + "," + str(i) + "," + str(poses[j][i][0]) + "," + str(poses[j][i][1]) + "," + str(poses[j][i][2]) + "," + str(poses[j][i][3]) + "," + str(poses[j][i][4]) + "," + str(poses[j][i][5]) + "," + str(np.argmax(label[j][i])) + "\n"
                self.logfile.write(msg)
                if self.verbose:
                    print("Pose = ", poses[j][i])
                    print("Label = ", np.argmax(label[j][i]))
                plt.subplot(1,2+self.num_hypotheses,i+2)
                plt.imshow(np.squeeze(data[j][i]))
                plt.title('Hypothesis %d'%(i+1))
            fig.savefig(name, bbox_inches="tight")
            if self.verbose:
                print("Arm/gripper target = ",
                        self.targets[0][j,imglen:imglen+6])
                print("Label target = ",
                        np.argmax(self.targets[0][j,(imglen+6):]))
            plt.close(fig)

