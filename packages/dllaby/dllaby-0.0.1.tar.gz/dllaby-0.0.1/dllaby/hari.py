def dl1():
    print ("""import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras import regularizers
# XOR dataset
X = np.array([[0,0], [0,1], [1,0], [1,1]])
Y = np.array([[0], [1], [1], [0]])
# Build the model
model = Sequential()
model.add(Dense(4, input_dim=2, activation='sigmoid',
                kernel_regularizer=regularizers.l2(0.01)))
model.add(Dense(1, activation='sigmoid'))
# Compile the model
model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])
# Train the model
model.fit(X, Y, epochs=500, verbose=0)
# Test XOR predictions
print("Testing XOR predictions:")
inputs = [[0,0], [0,1], [1,0], [1,1]]
for inp in inputs:
    result = model.predict([inp])[0][0]
    print(f"{inp} XOR = {round(result)} (raw={result:.4f})")
""")

def dl2():
    print("""import tensorflow as tf
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
import matplotlib.pyplot as plt

# Load dataset
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Normalize (0–1 scale)
x_train = x_train / 255.0
x_test = x_test / 255.0

# Build model
model = Sequential([
    Flatten(input_shape=(28, 28)),
    Dense(128, activation='relu'),
    Dense(10, activation='softmax')
])

# Compile model
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# Train model
model.fit(x_train, y_train, epochs=5)

# Evaluate model
loss, acc = model.evaluate(x_test, y_test)
print(f"\nTest Accuracy: {acc * 100:.2f}%")

# Make predictions
predictions = model.predict(x_test)

# Show first 5 test images with predictions
for i in range(5):
    plt.imshow(x_test[i], cmap='gray')
    plt.title(f"Predicted: {tf.argmax(predictions[i]).numpy()} | Actual: {y_test[i]}")
    plt.axis('off')
    plt.show()
""")
    
def dl3():
    print("""import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
# Load Fashion-MNIST dataset
(x_train, _), (x_test, _) = tf.keras.datasets.fashion_mnist.load_data()
# Normalize (0–1 range)
x_train = x_train.astype("float32") / 255.0
x_test = x_test.astype("float32") / 255.0
# Reshape to (28,28,1) for Conv2D
x_train = np.reshape(x_train, (len(x_train), 28, 28, 1))
x_test = np.reshape(x_test, (len(x_test), 28, 28, 1))

# Build Autoencoder
autoencoder = tf.keras.Sequential([
    # Encoder
    tf.keras.layers.Conv2D(32, (3,3), activation='relu', padding='same', input_shape=(28,28,1)),
    tf.keras.layers.MaxPooling2D((2,2), padding='same'),
    tf.keras.layers.Conv2D(16, (3,3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D((2,2), padding='same'),

    # Decoder
    tf.keras.layers.Conv2D(16, (3,3), activation='relu', padding='same'),
    tf.keras.layers.UpSampling2D((2,2)),
    tf.keras.layers.Conv2D(32, (3,3), activation='relu', padding='same'),
    tf.keras.layers.UpSampling2D((2,2)),
    tf.keras.layers.Conv2D(1, (3,3), activation='sigmoid', padding='same')])
# Compile
autoencoder.compile(optimizer='adam', loss='binary_crossentropy')
autoencoder.fit(x_train, x_train,
                epochs=5,
                batch_size=128,
                shuffle=True,
                validation_data=(x_test, x_test))
# Reconstruct images
decoded_imgs = autoencoder.predict(x_test)
# Plot original vs reconstructed
n = 5
plt.figure(figsize=(10, 4))
for i in range(n):
    # Original
    ax = plt.subplot(2, n, i+1)
    plt.imshow(x_test[i].reshape(28, 28), cmap='gray')
    plt.title("Original")
    plt.axis('off')
    ax = plt.subplot(2, n, i + 1 + n)
    plt.imshow(decoded_imgs[i].reshape(28, 28), cmap='gray')
    plt.title("Reconstructed")
    plt.axis('off')
plt.tight_layout()
plt.show()
""")
    
def dl4():
    print("""import speech_recognition as sr
import spacy

# Function to transcribe audio
def transcribe_audio(audio_path):
    print(f"--- Transcribing audio from {audio_path} ---")
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Request error: {e}"

# Function to analyze text with spaCy
def analyze_text(text):
    print("\n--- Named Entities ---")
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)

    if doc.ents:
        for ent in doc.ents:
            print(f"{ent.text:25} → {ent.label_}")
    else:
        print("No named entities found.")

# Example usage
audio_file = "harvard.wav"   # put your .wav file here

print("\n--- Transcribed Text ---")
transcribed_text = transcribe_audio(audio_file)
print(transcribed_text)

# Run NER analysis
analyze_text(transcribed_text)
 
""")
    
def dl5():
    print("""import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt
import numpy as np

# Load CIFAR-10 dataset
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()

class_names = ['airplane', 'automobile', 'bird', 'cat', 'deer',
               'dog', 'frog', 'horse', 'ship', 'truck']

# Normalize (0–1)
x_train = x_train / 255.0
x_test = x_test / 255.0

# Build CNN model
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax')])
# Compile
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

history = model.fit(x_train, y_train, epochs=3,
                    validation_data=(x_test, y_test),
                    batch_size=64)

# Evaluate
test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
print(f"\nTest accuracy after 3 epochs: {test_acc * 100:.2f}%")
# Show predictions for a few test images
num_images = 4
plt.figure(figsize=(10, 5))
for i in range(num_images):
    img = x_test[i]
    label = y_test[i][0]
    prediction = model.predict(np.expand_dims(img, axis=0))
    prediction_class = np.argmax(prediction)
    plt.subplot(1, num_images, i+1)
    plt.imshow(img)
    plt.title(f"Pred: {class_names[prediction_class]}\nActual: {class_names[label]}")
    plt.axis('off')
plt.tight_layout()
plt.show()
 
""")
    
def dl6():
    print("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

n_samples = 500

# Generate synthetic data
price_change = np.random.normal(0, 1, n_samples)
volume_change = np.random.normal(0, 1, n_samples)

# Inject anomalies
price_change[::60] += np.random.normal(18, 3, len(price_change[::60]))
volume_change[::30] += np.random.normal(10, 4, len(volume_change[::30]))
price_change[::80] += np.random.normal(12, 2, len(price_change[::80]))

# Put into DataFrame
data = pd.DataFrame({
    "price_change": price_change,
    "volume_change": volume_change
})

# Parameters
window_size = 30
z_threshold = 3
anomaly_indices_price = []
anomaly_indices_volume = []
print("Starting online fraud detection with rolling Z-score...")

# Detect anomalies
for i in range(window_size, len(data)):
    window = data.iloc[i - window_size:i]

    mean_price = window["price_change"].mean()
    std_price = window["price_change"].std()

    mean_volume = window["volume_change"].mean()
    std_volume = window["volume_change"].std()

    current_price = data.iloc[i]["price_change"]
    current_volume = data.iloc[i]["volume_change"]

    z_score_price = (current_price - mean_price) / (std_price + 1e-6)
    z_score_volume = (current_volume - mean_volume) / (std_volume + 1e-6)

    if abs(z_score_price) > z_threshold:
        anomaly_indices_price.append(i)
        print(f"Anomaly detected at index {i} on price_change: {current_price:.2f}")
    if abs(z_score_volume) > z_threshold:
        anomaly_indices_volume.append(i)
        print(f"Anomaly detected at index {i} on volume_change: {current_volume:.2f}")

# Plot anomalies
plt.figure(figsize=(14, 7))
# Price anomalies
plt.subplot(2, 1, 1)
plt.plot(data.index, data["price_change"], label="Price Change")
plt.scatter(anomaly_indices_price, data.iloc[anomaly_indices_price]["price_change"],
            color="red", label="Anomalies")
plt.title("Price Change with Detected Anomalies")
plt.xlabel("Index")
plt.ylabel("Price Change")
plt.legend()
# Volume anomalies
plt.subplot(2, 1, 2)
plt.plot(data.index, data["volume_change"], label="Volume Change")
plt.scatter(anomaly_indices_volume, data.iloc[anomaly_indices_volume]["volume_change"],
            color="red", label="Anomalies")
plt.title("Volume Change with Detected Anomalies")
plt.xlabel("Index")
plt.ylabel("Volume Change")
plt.legend()
plt.tight_layout()
plt.show()
""")
    
def dl7():
    print("""import torch
from torchvision import transforms
from PIL import Image
# Define transformation pipeline
transform = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3),
    transforms.RandomResizedCrop(size=(224, 224), scale=(0.8, 1.0)),
    transforms.RandomAffine(degrees=15, shear=10),
    transforms.ToTensor()])

# Load an image
img = Image.open("sample.jpg")

# Apply augmentation
aug_img = transform(img)

# Convert back to PIL for saving & visualization
to_pil = transforms.ToPILImage()
aug_img_pil = to_pil(aug_img)
# Show and save
aug_img_pil.show()
aug_img_pil.save("augmented-sample.jpg")
 
""")
    
def dl8():
    print("""import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Load dataset
data = pd.read_csv("Sentiment.csv")   # Ensure file has 'text' and 'label' columns
X_text = data['text'].values
y = data['label'].values

# Tokenization
max_words = 15000
max_len = 200

tokenizer = Tokenizer(num_words=max_words)
tokenizer.fit_on_texts(X_text)
X = tokenizer.texts_to_sequences(X_text)
X = pad_sequences(X, maxlen=max_len)

# Build LSTM model
model = Sequential([
    Embedding(input_dim=max_words, output_dim=128, input_length=max_len),
    LSTM(128, dropout=0.2, recurrent_dropout=0.2),
    Dense(1, activation='sigmoid')
])

# Compile
model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# Train
model.fit(X, y, epochs=3, batch_size=64, validation_split=0.2)
""")