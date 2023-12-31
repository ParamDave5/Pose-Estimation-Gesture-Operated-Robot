import argparse
import logging
import time

import cv2
import numpy as np

from tf_pose.estimator import TfPoseEstimator
from tf_pose.networks import get_graph_path, model_wh
from tf_pose.gesture_detection import *
from tf_pose.depth import *
import serial

s = serial.Serial('/dev/ttyACM0', 9600, timeout = 1)


fps_time = 0

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='tf-pose-estimation realtime webcam')
    parser.add_argument('--camera', type=int, default=0)

    parser.add_argument('--resize', type=str, default='0x0',
                        help='if provided, resize images before they are processed. default=0x0, Recommends : 432x368 or 656x368 or 1312x736 ')
    parser.add_argument('--resize-out-ratio', type=float, default=4.0,
                        help='if provided, resize heatmaps before they are post-processed. default=1.0')

    parser.add_argument('--model', type=str, default='mobilenet_thin', help='cmu / mobilenet_thin / mobilenet_v2_large / mobilenet_v2_small')
    parser.add_argument('--show-process', type=bool, default=False,
                        help='for debug purpose, if enabled, speed for inference is dropped.')
    
    parser.add_argument('--tensorrt', type=str, default="False",
                        help='for tensorrt process.')
    args = parser.parse_args()

    # logger.debug('initialization %s : %s' % (args.model, get_graph_path(args.model)))
    w, h = model_wh(args.resize)
    if w > 0 and h > 0:
        e = TfPoseEstimator(get_graph_path(args.model), target_size=(w, h), trt_bool=str2bool(args.tensorrt))
    else:
        e = TfPoseEstimator(get_graph_path(args.model), target_size=(432, 368), trt_bool=str2bool(args.tensorrt))
    # logger.debug('cam read+')
    cam = cv2.VideoCapture(args.camera)
    ret_val, image = cam.read()
    # logger.info('cam image=%dx%d' % (image.shape[1], image.shape[0]))
    cs = 0
    cf = 0
    cb = 0


    while True:
        ret_val, image = cam.read()
        if ret_val:

            # logger.debug('image process+')
            humans = e.inference(image, resize_to_default=(w > 0 and h > 0), upsample_size=args.resize_out_ratio)

            # logger.debug('postprocess+')
            image, output_keypoints = TfPoseEstimator.draw_humans(image, humans, imgcopy=False) # Receives OP points
            
            # print(output_keypoints)
            input_robot = robot_input(output_keypoints)
            dist, op_image = calc_depth(image)
            # print(input_robot)
            if input_robot == 'f':
                cf +=1
                if cf == 10:
                    s.write(b'1')
                    print("F")
                    cf = 0
                    cs = 0
                    cb = 0
            elif input_robot == 'b':
                cb +=1
                if cb == 10:
                    print("B")
                    s.write(b'2')
                    cf = 0
                    cs = 0
                    cb = 0
            else:
                cs +=1
                if cs == 10:
                    print("S")
                    s.write(b'3')
                    cf = 0
                    cs = 0
                    cb = 0

            # logger.debug('show+')
            cv2.putText(image,
                        "FPS: %f" % (1.0 / (time.time() - fps_time)),
                        (10, 10),  cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)

            
            cv2.imshow('tf-pose-estimation result', op_image)
            fps_time = time.time()
            if cv2.waitKey(1) == 27:
                break
            # logger.debug('finished+')

    cv2.destroyAllWindows()
