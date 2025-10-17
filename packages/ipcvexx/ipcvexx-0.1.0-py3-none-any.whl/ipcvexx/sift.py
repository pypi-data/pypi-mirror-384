import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load image
img = cv2.imread(r'img.jpg')
rows, cols = img.shape[:2]

# 1) Scaling
scaled = cv2.resize(img, None, fx=1.5, fy=1.5)  # 150% size

# 2) Rotation
M_rot = cv2.getRotationMatrix2D((cols//2, rows//2), 45, 1)  # 45° rotation
rotated = cv2.warpAffine(img, M_rot, (cols, rows))

# 3) Shearing
M_shear = np.float32([[1, 0.5, 0], [0.5, 1, 0]])  # simple shear
sheared = cv2.warpAffine(img, M_shear, (int(cols*1.5), int(rows*1.5)))

# Show all transformations
plt.figure(figsize=(12,4))
plt.subplot(1,4,1)
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.title('Original'); plt.axis('off')

plt.subplot(1,4,2)
plt.imshow(cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB))
plt.title('Scaled'); plt.axis('off')

plt.subplot(1,4,3)
plt.imshow(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB))
plt.title('Rotated'); plt.axis('off')

plt.subplot(1,4,4)
plt.imshow(cv2.cvtColor(sheared, cv2.COLOR_BGR2RGB))
plt.title('Sheared'); plt.axis('off')

plt.show()


import cv2
import matplotlib.pyplot as plt

# Load grayscale image
img = cv2.imread(r'img.jpg', cv2.IMREAD_GRAYSCALE)

# Step 1,2,3,4: SIFT
sift = cv2.SIFT_create()
keypoints, descriptors = sift.detectAndCompute(img, None)

# Draw keypoints with orientation
img_sift = cv2.drawKeypoints(
    img, keypoints, None,
    flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
)

# Show image with keypoints
plt.figure(figsize=(8,6))
plt.imshow(img_sift, cmap='gray')
plt.title(f"SIFT Keypoints")
plt.axis('off')
plt.show()

# Print first 5 keypoints and their angles
print("First 5 keypoints (x, y, angle):")
for kp in keypoints[:5]:
    print(f"({kp.pt[0]:.1f}, {kp.pt[1]:.1f}), angle={kp.angle:.1f}°")

print("Number of keypoints detected:", len(keypoints))
print("Descriptor shape:", descriptors.shape)