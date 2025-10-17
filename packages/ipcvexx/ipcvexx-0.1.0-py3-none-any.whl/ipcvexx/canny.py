# Experiment 1 — Edge Detection (Canny)

import cv2
import numpy as np
from matplotlib import pyplot as plt

img = cv2.imread(r'img.jpg', cv2.IMREAD_GRAYSCALE)

blurred = cv2.GaussianBlur(img, (5, 5), 1.4)

grad_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
grad_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)

magnitude = np.sqrt(grad_x**2 + grad_y**2)
direction = np.arctan2(grad_y, grad_x) * 180 / np.pi

magnitude = cv2.convertScaleAbs(magnitude)

edges = cv2.Canny(blurred, 100, 200)

plt.figure(figsize=(12,6))

plt.subplot(1, 4, 1)
plt.imshow(img, cmap='gray')
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 4, 2)
plt.imshow(blurred, cmap='gray')
plt.title('After Smoothing')
plt.axis('off')

plt.subplot(1, 4, 3)
plt.imshow(magnitude, cmap='gray')
plt.title('Gradient Magnitude')
plt.axis('off')

plt.subplot(1, 4, 4)
plt.imshow(edges, cmap='gray')
plt.title('Final Edges (Canny)')
plt.axis('off')

plt.tight_layout()
plt.show()

# Experiment 2 — Region Growing Segmentation

import cv2
import numpy as np
from matplotlib import pyplot as plt

def region_growing(img, seed):
    h, w = img.shape
    segmented = np.zeros((h, w), np.uint8)
    stack = [seed]
    threshold = 15
    while stack:
        x, y = stack.pop()
        if segmented[x, y] == 0:
            segmented[x, y] = 255
            for i in range(-1,2):
                for j in range(-1,2):
                    nx, ny = x+i, y+j
                    if 0 <= nx < h and 0 <= ny < w:
                        if abs(int(img[nx, ny]) - int(img[x, y])) < threshold:
                            stack.append((nx, ny))
    return segmented

img = cv2.imread(r'img.jpg', 0)
seg = region_growing(img, (100, 100))

plt.subplot(121); plt.imshow(img, cmap='gray'); plt.title('Original')
plt.subplot(122); plt.imshow(seg, cmap='gray'); plt.title('Region Grown')
plt.show()