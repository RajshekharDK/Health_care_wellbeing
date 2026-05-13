import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os

# ==========================================================
# PATHS
# ==========================================================

DATA_DIR = "data/skin_dataset"   # structure: class folders
IMG_SIZE = 224
BATCH_SIZE = 32

# ==========================================================
# DATA AUGMENTATION (🔥 IMPORTANT)
# ==========================================================

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    zoom_range=0.2,
    horizontal_flip=True,
    validation_split=0.2
)

train_data = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="training"
)

val_data = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="validation"
)

# ==========================================================
# MODEL (🔥 TRANSFER LEARNING)
# ==========================================================

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False  # freeze base

x = base_model.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.BatchNormalization()(x)
x = layers.Dense(128, activation="relu")(x)
x = layers.Dropout(0.3)(x)
output = layers.Dense(train_data.num_classes, activation="softmax")(x)

model = models.Model(inputs=base_model.input, outputs=output)

# ==========================================================
# COMPILE
# ==========================================================

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.0003),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# ==========================================================
# TRAIN
# ==========================================================

history = model.fit(
    train_data,
    validation_data=val_data,
    epochs=15
)

# ==========================================================
# SAVE MODEL
# ==========================================================

model.save("skin_model")

print("✅ Skin model trained and saved")