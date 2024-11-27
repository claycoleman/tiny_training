# ask the user which dataset to use, in the /datasets folder
# read in all the images and their classes, organized /datasets/<ds name>/<class name or number>/<img name>
# split into training and test and maybe validation?
# send uart for training mode
# start training loop, looping over training data 
# display the image to train in a large window with black background. image should be centered in that black background.
# in first iteration only, wait until the camera is pointing at the image and solicit user input (like spacebar)
# send a signal to the microcontroller for the relevant class number
# wait until you read the "TRAINING DONE" uart message from the microcontroller
# go to next loop in training
# repeat for N epochs
# get test / validation performance
# send uart for inference mode, maybe a different signal to enable the validation flag (like "v"), starts logging
# display validation image
# wait for 3 consecutive "INFERENCE COMPLETE: <class number>" uart message with same class number
# record prediction, move to next image

# additional goals, work on after we have above complete:
# based on dataset, update the OUTPUT_CH in a specified .h file
# recompile binary
# deploy on the microcontroller