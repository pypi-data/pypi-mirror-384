import cv2

# Open video file
cap = cv2.VideoCapture(r'vid.mp4')  # replace with your video

count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    # Save each frame as image
    cv2.imwrite(f'frame/frame_{count}.jpg', frame)
    count += 1

cap.release()
print(f"Extracted {count} frames")



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
