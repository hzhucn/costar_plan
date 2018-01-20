export CUDA_VISIBLE_DEVICES="" && python grasp_train.py --grasp_model grasp_model_levine_2016 --data_dir=~/.keras/datasets/grasping/ --grasp_success_label 'move_to_grasp/time_ordered/grasp_success' --grasp_sequence_motion_command_feature 'move_to_grasp/time_ordered/reached_pose/transforms/endeffector_current_T_endeffector_final/vec_sin_cos_5' --loss 'binary_crossentropy' --metric 'binary_accuracy' --batch_size 1 --distributed None --grasp_dataset 052 --grasp_datasets_train 052 --grasp_dataset_eval 057 --progress_tracker tensorboard
