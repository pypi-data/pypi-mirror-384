import tensorflow as tf
import tensorflow_datasets as tfds
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

# a) Load BCCD dataset
data, info = tfds.load('bccd', with_info=True, as_supervised=False)
train_ds = data['train']
val_ds = data['validation']
test_ds = data['test']

# b) Show number of images
print("Train:", info.splits['train'].num_examples)
print("Validation:", info.splits['validation'].num_examples)
print("Test:", info.splits['test'].num_examples)

plt.figure(figsize=(8,8))
for i, sample in enumerate(train_ds.take(6)):
    img = sample['image']
    label = sample['objects']['label'][0]  # first object’s label
    plt.subplot(2,3,i+1)
    plt.imshow(img)
    plt.title(f"Label: {info.features['objects'].feature['label'].int2str(label)}")
    plt.axis('off')
plt.show()


def preprocess(sample):
    img = sample['image']
    # If multiple objects, take the first label (just for classification demo)
    label = sample['objects']['label'][0]
    img = tf.image.resize(img, (128, 128))
    img = tf.cast(img, tf.float32) / 255.0
    return img, label

train_ds_proc = train_ds.map(preprocess).batch(32).prefetch(tf.data.AUTOTUNE)
val_ds_proc = val_ds.map(preprocess).batch(32).prefetch(tf.data.AUTOTUNE)
test_ds_proc = test_ds.map(preprocess).batch(32).prefetch(tf.data.AUTOTUNE)

model = models.Sequential([
    layers.Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
    layers.MaxPooling2D(2,2),
    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(info.features['objects'].feature['label'].num_classes, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

history = model.fit(train_ds_proc, validation_data=val_ds_proc, epochs=5)
# Evaluate on test
test_loss, test_acc = model.evaluate(test_ds_proc)
print("Test accuracy before augmentation:", test_acc)

data_aug = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomContrast(0.3)
])

# Directly apply augmentation
aug_train = train_ds_proc.map(lambda x, y: (data_aug(x), y))

# Clone model or reinitialize
aug_model = models.clone_model(model)
aug_model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

aug_history = aug_model.fit(aug_train, validation_data=val_ds_proc, epochs=5)
test_loss2, test_acc2 = aug_model.evaluate(test_ds_proc)
print("Test accuracy after augmentation:", test_acc2)

plt.plot(history.history['accuracy'], label='Train Before Aug')
plt.plot(aug_history.history['accuracy'], label='Train After Aug')
plt.plot(history.history['val_accuracy'], '--', label='Val Before Aug')
plt.plot(aug_history.history['val_accuracy'], '--', label='Val After Aug')
plt.title('Accuracy Comparison')
plt.legend()
plt.show()

print("Test accuracy before:", test_acc)
print("Test accuracy after:", test_acc2)
