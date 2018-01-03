import tensorflow as tf
import os.path
from grasp_dataset import GraspDataset
from grasp_dataset import FLAGS
from grasp_dataset import mkdir_p

""" Counts the grasp successes, failures, and ratio of succsesses vs the total number of attempts.

    Writes to the following location by default:

    ~/.keras/datasets/grasping/grasp_dataset_<dataset number>_statistics.txt'

    To run:

    python2 success_fail_statistic.py --grasp_dataset 102

    Output:

    grasp_dataset_<dataset number>_statistics.txt

"""
if __name__ == '__main__':
    with tf.Session() as sess:
        gd = GraspDataset()
        default_save_path = FLAGS.data_dir
        mkdir_p(default_save_path)
        filename = 'grasp_dataset_' + gd.dataset + '_statistics.txt'
        complete_path = os.path.join(default_save_path, filename)
        success_num, fail_num, success_ratio = gd.count_success_failure_number(sess)
        file_object = open(complete_path, 'w')
        text_lines = ['Statistics for grasp_dataset_', gd.dataset+'\n',
                      'total attempts: ', str(success_num+fail_num)+'\n',
                      'number of success: ', str(success_num)+'\n',
                      'number of failure: ', str(fail_num)+'\n',
                      'success ratio to total: ', str(success_ratio)+'\n']
        file_object.writelines(text_lines)
        file_object.close()
        print('number of attempts', success_num+fail_num)
        print('number of success', success_num)
        print('number of failure', fail_num)
        print('success ratio to total', success_ratio)
