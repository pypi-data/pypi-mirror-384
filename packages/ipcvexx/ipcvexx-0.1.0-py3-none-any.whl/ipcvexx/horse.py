import cv2
import numpy as np
import matplotlib.pyplot as plt

# 1) Load grayscale image
img = cv2.imread(r'img.jpg', cv2.IMREAD_GRAYSCALE)

# 2) Contrast stretching
min_val, max_val = np.min(img), np.max(img)
contrast_stretched = ((img - min_val) / (max_val - min_val) * 255)

# 3) Linear filtering with visible smoothing (Gaussian blur)
filtered = cv2.GaussianBlur(contrast_stretched, (5,5), 0)

# 4) Plot original, contrast-stretched, filtered images
plt.figure(figsize=(12,4))

plt.subplot(1,3,1)
plt.imshow(img, cmap='gray')
plt.title('Original')
plt.axis('off')

plt.subplot(1,3,2)
plt.imshow(contrast_stretched, cmap='gray')
plt.title('Contrast Stretched')
plt.axis('off')

plt.subplot(1,3,3)
plt.imshow(filtered, cmap='gray')
plt.title('Filtered (Gaussian Blur)')
plt.axis('off')

plt.show()

# Histogram of filtered image
plt.figure()
plt.hist(filtered.ravel(), bins=256)
plt.title("Histogram of Filtered Image")
plt.show()



# Install required packages
# pip install tensorflow tensorflow-datasets matplotlib

import tensorflow as tf
import tensorflow_datasets as tfds
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
import matplotlib.pyplot as plt

# a) Load Horse vs Human dataset from TensorFlow Datasets
data, info = tfds.load('horses_or_humans', with_info=True, as_supervised=True)
train_ds = data['train'].take(800)
val_ds = data['train'].skip(800)

# b) View number of images
print("Training images:", tf.data.experimental.cardinality(train_ds).numpy())
print("Validation images:", tf.data.experimental.cardinality(val_ds).numpy())

# Normalize pixel values (rescale=1./255)
def normalize_img(image, label):
    image = tf.image.resize(image, (150, 150))
    image = tf.cast(image, tf.float32) / 255.0
    return image, label

train_ds = train_ds.map(normalize_img).batch(32).prefetch(tf.data.AUTOTUNE)
val_ds = val_ds.map(normalize_img).batch(32).prefetch(tf.data.AUTOTUNE)

# c) Plot some sample images
plt.figure(figsize=(8, 8))
for images, labels in train_ds.take(1):
    for i in range(9):
        plt.subplot(3, 3, i + 1)
        plt.imshow(images[i])
        plt.title("Horse" if labels[i] == 0 else "Human")
        plt.axis('off')
plt.show()

# e) Build CNN using Pretrained ResNet50
base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(150, 150, 3))
base_model.trainable = False  # Freeze pretrained layers

model = Sequential([
    base_model,
    GlobalAveragePooling2D(),
    Dense(128, activation='relu'),
    Dense(1, activation='sigmoid')  # Binary output: Horse/Human
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

# f) Train the model
history = model.fit(train_ds, validation_data=val_ds, epochs=5)

# Plot training and validation accuracy
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Training vs Validation Accuracy')
plt.legend()
plt.show()
