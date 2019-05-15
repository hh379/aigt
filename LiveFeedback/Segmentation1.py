import os
import keras
import sys
import time
import numpy as np
#
# from keras.models import Sequential
# from keras.layers import Activation, GlobalAveragePooling2D
# from keras.layers.core import Dense, Dropout, Flatten
# from keras.optimizers import Adam, SGD
# from keras.metrics import categorical_crossentropy
# from keras.preprocessing.image import ImageDataGenerator
# from keras.layers.normalization import BatchNormalization
# from keras.layers.convolutional import *
# from keras.utils import Sequence

import cv2
from pyIGTLink import pyIGTLink

from LiveModels import small_unet
from LiveModels import unet_input_image_size

# Parameters

image_size = 128

# Check command line arguments

if len(sys.argv) < 2:
	print("Usage: {} WEIGHTS_FILE".format(sys.argv[0]))
	sys.exit()

weights_file_name = sys.argv[1]

print("Loading weights from: {}".format(weights_file_name))

# Building the model. Should be the same as the weights to be loaded.

model = small_unet(weights_file_name)

print("Server starting...")
client = pyIGTLink.PyIGTLinkClient(host="127.0.0.1")
client.start()
print("Server running...")

try:
    image_squeezed = np.zeros([image_size, image_size]).astype(np.uint8)
    image_padded = np.zeros([1, image_size, image_size, 1]).astype(np.uint8)
    image_input = np.zeros([1, image_size, image_size, 1]).astype(np.uint8)
    
    while True:
      messages = client.get_latest_messages()
      if len(messages) > 0:
        for message in messages:
          if message._type == "IMAGE":
            image = message._image
            image = np.flip(image, 1)
            image_squeezed = np.squeeze(image)
            image_padded[0,:,:,0] = cv2.resize(image_squeezed, (unet_input_image_size, unet_input_image_size)).astype(np.uint8)
            image_input = image_padded / 255.0
            prediction = np.flip(model.predict(image_input) * 255, 1)
            prediction_resized = np.zeros(image.shape)
            prediction_resized[0, :, :, 0] = cv2.resize(prediction[0, :, :, 0], (image.shape[1], image.shape[2])).astype(np.uint8)
            image_message = pyIGTLink.ImageMessage(prediction_resized, device_name=message._device_name + "Predicted")
            image_message._matrix[0][3] = image.shape[1] / 2
            image_message._matrix[1][3] = image.shape[2] / 2
            client.send_message(image_message)
      time.sleep(0.05)
except KeyboardInterrupt:
    pass

client.stop()


