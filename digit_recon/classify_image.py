import sys
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import json
from tensorflow.keras.models import Sequential, load_model
import matplotlib.pyplot as plt

# Check if a file path is provided as a command-line argument
# if len(sys.argv) != 2:
#     print("Usage: python classify_image.py <image_path>")
    
json_file_path = sys.argv[1]
try:
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)
except FileNotFoundError:
    print(f"Error: File not found - {json_file_path}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Invalid JSON format in file - {json_file_path}")
    sys.exit(1)

image_data = data["data"]["drawing"]

# Decode Base64-encoded image data
binary_data = base64.b64decode(image_data)

# Create an in-memory file-like object
image_stream = BytesIO(binary_data)

# Open the image using PIL (Python Imaging Library)
image = Image.open(image_stream)

# Resize the image to 28x28
resized_image = image.resize((28, 28))

# Convert the image to a NumPy array
pixel_values = np.array(resized_image)

gray_image = pixel_values[:, :, 3]


# Normalize pixel values to the range [0, 1]
normalized_image = (gray_image / 255.0).reshape(28,28,1)


loaded_model = load_model("digit_model.keras")
predictions = loaded_model.predict(normalized_image.reshape((1, 28, 28, 1)), verbose=False)

print(np.argmax(predictions))
sys.stdout.flush()



# Save or display the resulting image

