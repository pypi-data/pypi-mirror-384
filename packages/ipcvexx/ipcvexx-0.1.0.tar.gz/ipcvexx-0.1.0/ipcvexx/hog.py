# Exercise 1 — Pixel-wise Image Difference

import cv2
import numpy as np
from matplotlib import pyplot as plt

# Load two images
M1 = cv2.imread(r'img1', 0)
M2 = cv2.imread(r'img2', 0)

# Resize M2 to match the dimensions of M1
M2_resized = cv2.resize(M2, (M1.shape[1], M1.shape[0]))

# Compute absolute difference
Out = cv2.absdiff(M1, M2_resized)

# Display result
plt.imshow(Out, cmap='gray')
plt.title('Absolute Difference')
plt.axis('off')
plt.show()

# Exercise 2 — HOG Feature Extraction

import cv2
import matplotlib.pyplot as plt
from skimage.feature import hog
from skimage import color, io
import numpy as np

img = cv2.imread(r'img.jpg')

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

img_resized = cv2.resize(img_rgb, (64, 128))

gray = color.rgb2gray(img_resized)

grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

magnitude = np.sqrt(grad_x**2 + grad_y**2)
orientation = np.arctan2(grad_y, grad_x) * (180 / np.pi) % 180

features, hog_image = hog(
    gray,
    orientations=9,
    pixels_per_cell=(8, 8),
    cells_per_block=(2, 2),
    visualize=True,
    block_norm='L2-Hys'
)


print(f"Feature vector length: {len(features)}")

plt.figure(figsize=(12, 6))

plt.subplot(1, 3, 1)
plt.imshow(img_resized)
plt.title("Original Image")
plt.axis('off')

plt.subplot(1, 3, 2)
plt.imshow(magnitude, cmap='gray')
plt.title("Gradient Magnitude")
plt.axis('off')

plt.subplot(1, 3, 3)
plt.imshow(hog_image, cmap='gray')
plt.title("HOG Features")
plt.axis('off')

plt.tight_layout()
plt.show()