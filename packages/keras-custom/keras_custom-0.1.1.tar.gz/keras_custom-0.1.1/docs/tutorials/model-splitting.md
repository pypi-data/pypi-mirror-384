You are correct. My apologies for the misunderstanding.

Here is the raw text for the markdown file. You can copy everything below this line and paste it directly into a text editor and save it as a .md file.

🧠 Model Splitting: Creating Nested Models While Maintaining Functionality
In this tutorial, we will demonstrate how to split an existing Keras model into a sequence of nested models. The goal is to preserve the same underlying function of the original model but restructure it into smaller, modular components for easier inspection or experimentation.

## ⚙️ Step 1: Setting Up the Environment
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
## 📚 Step 2: Import Required Libraries
Next, we import the necessary libraries for our model and image processing.

Python

import os

import keras
import keras.backend as K
import numpy as np
from IPython.display import HTML, Image, display
from keras.applications.resnet50 import ResNet50, decode_predictions, preprocess_input
from keras.layers import Activation
from keras.models import Model, Sequential
## 🖼️ Step 3: Download and Preprocess the Image
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
## 🤖 Step 4: Load the Pre-trained Model
We will use the ResNet50 model pre-trained on ImageNet to make predictions.

Python

# Load the ResNet50 model without the final classification layer
model = ResNet50(weights="imagenet", classifier_activation=None)

# Make a prediction
preds = model.predict(x)

# Decode the predictions to show the top 3 predictions
print("Predicted:", decode_predictions(preds, top=3)[0])
## 🔪 Step 5: Split the Model into Nested Models
The goal is to break down the ResNet50 model into smaller, modular nested models. Each nested model will correspond to a part of the original model up to a specific layer. The split will be based on the activations of certain layers.

Identify Layers to Split

We will first identify the layers with activation functions (ReLU layers) and choose some layers to use as split points. For simplicity, let's pick layers at indices [0, 4, 8, 12, -1].

Python

import keras_custom
from keras_custom.model import get_nested_model

# Identify activation layers (ReLU) in the model
relu_name = [
    e.name for e in model.layers if isinstance(e, Activation) and e.name.split("_")[-1] == "out"
]

# Select layers to split at
indices = [0, 4, 8, 12, -1]
split = [relu_name[i] for i in indices] + [model.layers[-1].name]
Create Nested Models

Now, we will create a list of nested models by using the selected layers for the splits. Each nested model is built starting from the previous layer.

Python

# Initialize variables
layer_in = None
input_shape_wo_batch = list(model.input.shape[1:])
nested_models = []

# Loop through the selected split layers and create nested models
for name in split:
    layer_out = model.get_layer(name)
    nested_model = get_nested_model(model, layer_out, layer_in, input_shape_wo_batch)
    layer_in = layer_out
    nested_models.append(nested_model)

# Combine all nested models into a Sequential model
model_seq = Sequential(layers=nested_models)
## ✅ Step 6: Verify Predictions
We can now check whether the nested model produces the same predictions as the original ResNet50 model.

Python

# Make predictions using the nested model sequence
preds_ = model_seq.predict(x)

# Ensure the predictions are almost identical
np.testing.assert_almost_equal(preds, preds_)

# Print the prediction results
print("Predicted:", decode_predictions(preds, top=3)[0])
## 📊 Step 7: Visualize the Nested Model Architecture
Finally, we can visualize the architecture of the newly created model using Keras' built-in plot_model function.

Python

# Save model architecture visualization to a file
dot_img_file_backward = "./ResNet50_nested.png"
keras.utils.plot_model(
    model_seq, to_file=dot_img_file_backward, show_shapes=True, show_layer_names=True
)

# Display the model architecture image
display(
    HTML(
        '<div style="text-align: center;"><img src="{}" width="800"/></div>'.format(
            dot_img_file_backward
        )
    )
)
## 🎉 Conclusion
In this tutorial, we successfully split the ResNet50 model into a sequence of nested models. Each nested model corresponds to a portion of the original model, and we verified that the nested models produce the same predictions as the original model. This approach can be useful for visualizing and debugging complex models by breaking them down into smaller components.
