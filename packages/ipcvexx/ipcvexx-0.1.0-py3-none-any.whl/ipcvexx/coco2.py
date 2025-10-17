import tensorflow as tf
import tensorflow_datasets as tfds
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

# a) Load dataset
data, info = tfds.load('coco_captions', with_info=True, as_supervised=False)

train_ds = data['train']
val_ds = data['validation']

# b) Show number of images
print("Training images:", info.splits['train'].num_examples)
print("Validation images:", info.splits['validation'].num_examples)

# c) Plot sample images
plt.figure(figsize=(8, 8))
for i, sample in enumerate(train_ds.take(6)):
    image = sample['image']
    plt.subplot(2, 3, i+1)
    plt.imshow(image)
    plt.axis("off")
plt.show()

# f) Normalize images
def preprocess(image):
    image = tf.image.resize(image, (128, 128))
    image = tf.cast(image, tf.float32) / 255.0
    return image

train_images = train_ds.map(lambda x: preprocess(x['image'])).batch(32)
val_images = val_ds.map(lambda x: preprocess(x['image'])).batch(32)

# g) Build CNN model
model = models.Sequential([
    layers.Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
    layers.MaxPooling2D(2,2),
    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax')  # Dummy 10-class output
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# h) Train and evaluate
history = model.fit(train_images, validation_data=val_images, epochs=2)

# d) Augmentation
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomContrast(0.3)
])

aug_train_ds = train_ds.map(lambda x: (data_augmentation(x['image']),))
aug_train_images = aug_train_ds.map(lambda x: preprocess(x[0])).batch(32)

print("After augmentation:")
print("Training images (approx):", info.splits['train'].num_examples)
print("Validation images:", info.splits['validation'].num_examples)

# i + j) Rebuild CNN (same architecture for fair comparison)
aug_model = models.clone_model(model)
aug_model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

aug_history = aug_model.fit(aug_train_images, validation_data=val_images, epochs=2)

# k) Compare before and after augmentation
plt.plot(history.history['accuracy'], label='Before Aug')
plt.plot(aug_history.history['accuracy'], label='After Aug')
plt.title('Training Accuracy Comparison')
plt.legend()
plt.show()
