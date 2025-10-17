
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
import tensorflow as tf
import os

# ==========================================
# a. Load the dataset
# ==========================================
train_path = 'coco/train'  # should contain subfolders per class
test_path = 'coco/test'

# ==========================================
# b. Show number of training and testing images
# ==========================================
def count_images(path):
    total = 0
    for folder in os.listdir(path):
        full_path = os.path.join(path, folder)
        if os.path.isdir(full_path):
            total += len(os.listdir(full_path))
    return total

print(f"Training images: {count_images(train_path)}")
print(f"Testing images: {count_images(test_path)}")

# ==========================================
# c. Plot some images
# ==========================================
sample_gen = ImageDataGenerator(rescale=1./255)
sample_data = sample_gen.flow_from_directory(train_path, target_size=(128,128), batch_size=9, shuffle=True)
x_batch, y_batch = next(sample_data)

plt.figure(figsize=(8,8))
for i in range(9):
    plt.subplot(3,3,i+1)
    plt.imshow(x_batch[i])
    plt.axis('off')
plt.suptitle('Sample Training Images')
plt.show()

# ==========================================
# d. Do the image augmentation – contrast, flipping and rotation
# ==========================================
train_gen_aug = ImageDataGenerator(rescale=1./255,
                                   rotation_range=25,
                                   horizontal_flip=True,
                                   brightness_range=[0.8,1.2])

test_gen = ImageDataGenerator(rescale=1./255)

train_data_aug = train_gen_aug.flow_from_directory(train_path, target_size=(128,128), batch_size=32, class_mode='sparse')
test_data = test_gen.flow_from_directory(test_path, target_size=(128,128), batch_size=32, class_mode='sparse')

# ==========================================
# e. After augmentation, show the number of training and testing images
# ==========================================
print(f"Training images (after augmentation): {train_data_aug.samples}")
print(f"Testing images: {test_data.samples}")

# ==========================================
# f. Normalizing the training data
# ==========================================
# (Already normalized using rescale=1./255)

# ==========================================
# g. Build a Convolutional Neural Network (CNN)
# ==========================================
def build_cnn():
    model = models.Sequential([
        layers.Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
        layers.MaxPooling2D(2,2),
        layers.Conv2D(64, (3,3), activation='relu'),
        layers.MaxPooling2D(2,2),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(10, activation='softmax')  # 10 example classes
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

# ==========================================
# h. Train CNN and show training/testing accuracy
# ==========================================
print("\\nTraining CNN Model...")
cnn_model = build_cnn()
cnn_history = cnn_model.fit(train_data_aug, validation_data=test_data, epochs=3, verbose=1)

cnn_train_acc = cnn_history.history['accuracy'][-1]
cnn_test_acc = cnn_history.history['val_accuracy'][-1]

print(f"CNN Train Accuracy: {cnn_train_acc:.4f}")
print(f"CNN Test Accuracy: {cnn_test_acc:.4f}")

# ==========================================
# i. Normalizing the training data
# (done above with ImageDataGenerator)
# ==========================================

# ==========================================
# j. Build a Faster R-CNN (using pretrained model from TensorFlow)
# ==========================================
# We'll use a pretrained Faster R-CNN model from TensorFlow Hub (for object detection)

import tensorflow_hub as hub

print("\\nLoading Faster R-CNN pretrained model...")
faster_rcnn_model = hub.load("https://tfhub.dev/tensorflow/faster_rcnn/resnet50_v1_640x640/1")

# Function to run inference on a few test images
def detect_objects(model, dataset):
    x_batch, _ = next(dataset)
    img_tensor = tf.convert_to_tensor(x_batch[:2])  # use 2 images for demo
    results = model(img_tensor)
    return results

# Perform inference on test images (demo)
results = detect_objects(faster_rcnn_model, test_data)

print("Faster R-CNN inference complete.")
print("Detection result keys:", list(results.keys()))

# ==========================================
# k. Show the training and testing accuracy (for classification comparison)
# ==========================================
# Note: Faster R-CNN is pretrained and used for object detection, 
# not direct classification accuracy like CNN, 
# but we show CNN accuracy as comparison metric.

print("\\n=========== MODEL PERFORMANCE COMPARISON ===========")
print(f"CNN Model Accuracy - Train: {cnn_train_acc:.4f}, Test: {cnn_test_acc:.4f}")
print("Faster R-CNN - Pretrained model used for object detection (no classification accuracy metric).")

