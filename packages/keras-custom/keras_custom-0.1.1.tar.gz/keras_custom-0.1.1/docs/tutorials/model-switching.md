🔄 Tutorial: Switching the data_format in Keras Models
In this tutorial, we will demonstrate how to modify the input channel order (i.e., data_format) of a pre-trained Keras model. Specifically, we will swap between the channels_first and channels_last formats, allowing the model to process input images in a different format while maintaining the same underlying functionality.

We will also walk you through splitting an existing model into smaller, modular components for easier experimentation.

⚙️ Step 1: Setting Up the Environment
If you're running this tutorial on Google Colab, follow these steps to install the required libraries and dependencies:

Python

# On Colab: install the library
on_colab = "google.colab" in str(get_ipython())
if on_colab:
    import sys  # noqa: avoid having this import removed by pycln

    # install dev version for dev doc, or release version for release doc
    !{sys.executable} -m pip install -U pip
    !{sys.executable} -m pip install git+https://github.com/ducoffeM/keras_custom@main#egg=decomon
    # install desired backend (by default torch)
    !{sys.executable} -m pip install "torch"
    !{sys.executable} -m pip install "keras"

    # extra librabry used in this notebook
    !{sys.executable} -m pip install "numpy"
    # missing imports IPython
📚 Step 2: Import Required Libraries
First, we need to import the necessary libraries for model manipulation and image preprocessing.

Python

import os

import keras
import numpy as np
from IPython.display import HTML, Image, display
from keras.applications.resnet50 import ResNet50, decode_predictions, preprocess_input
from keras.layers import Activation
from keras.models import Model, Sequential
🖼️ Step 3: Download and Preprocess the Image
We will use an image of an elephant for our prediction. If the image file is not present, it will be downloaded from the web.

Python

# Check if the image is already available
if not os.path.isfile("elephant.jpg"):
    !wget https://upload.wikimedia.org/wikipedia/commons/f/f9/Zoorashia_elephant.jpg -O elephant.jpg

# Load and preprocess the image
img_path = "elephant.jpg"
img = keras.utils.load_img(img_path, target_size=(224, 224))
x = keras.utils.img_to_array(img)
x = np.expand_dims(x, axis=0)  # Add batch dimension
x = preprocess_input(x)  # Preprocess image for ResNet50
🤖 Step 4: Load the Pre-trained Model
Next, we load the pre-trained ResNet50 model without the final classification layer. This allows us to use the model for feature extraction or to make predictions without the final dense layer.

Python

# Load the ResNet50 model without the final classification layer
model = ResNet50(weights="imagenet", classifier_activation=None)

# Make a prediction
preds = model.predict(x)

# Decode the predictions to show the top 3 predictions
print("Predicted:", decode_predictions(preds, top=3)[0])
↔️ Step 5: Switch the Input Channel Format
In this step, we will modify the input channel format of the model. Specifically, we will switch between channels_first and channels_last. This is useful when you need to work with models built with different channel order conventions.

We will use a custom utility function switch_model_input_channel, which handles this transformation.

Python

def get_data_format(model):
    for layer in model.layers:
        if hasattr(layer, "data_format"):
            return layer.data_format
    return "channels_first"
Python

from keras_custom.model.channel import switch_model_input_channel

original_data_format = get_data_format(model)
# Switch the channel format of the model to 'channels_last'
model_last, _ = switch_model_input_channel(model, original_data_format)

# Permute the input image to match the 'channels_last' format
if original_data_format == "channels_first":
    y = np.transpose(
        x, (0, 2, 3, 1)
    )  # Change the dimensions to (batch_size, height, width, channel)
else:
    y = np.transpose(
        x, (0, 3, 1, 2)
    )  # Change the dimensions to (batch_size, channel, height, width)

# Make a prediction with the modified model
preds_ = model_last.predict(y)

np.testing.assert_almost_equal(preds, preds_, decimal=5)
Python

# Decode the predictions to show the top 3 predictions
print("Predicted (with switched channel format):", decode_predictions(preds_, top=3)[0])
Key Points:
The switch_model_input_channel function swaps the channel format of the model.

We use np.transpose to reorder the image dimensions, switching from (batch_size, height, width, channels) to (batch_size, channels, height, width) for channels_first.

After modifying the model, we make a prediction using the transformed model.

🎉 Conclusion
In this tutorial, we demonstrated how to:

Load and preprocess an image for use with a pre-trained Keras model.

Use ResNet50 to make predictions on the image.

Modify the input channel format (channels_first to channels_last and vice versa) for the model using a custom utility function.

Apply the necessary transformations to the input tensor to match the new channel format and make predictions.

This approach allows you to experiment with different input formats for your Keras models without modifying the underlying architecture, making it a useful technique for working with models in different environments or frameworks.
