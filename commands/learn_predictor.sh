#!/usr/bin/env bash
rosrun costar_models ctp_model_tool \
	--features multi -i 50000 -e 100 \
	--model predictor --data_file ~/datasets/ctp_test.npz \
	--si 0 --lr 0.001 --optimizer nadam \
        --batch_size 64 

