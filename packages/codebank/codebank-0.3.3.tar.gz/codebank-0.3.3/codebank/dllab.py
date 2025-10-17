def xor():
    print("""
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

X = np.array([[0,0], [0,1], [1,0], [1,1]])
y = np.array([[0], [1], [1], [0]])

model = Sequential()
model.add(Dense(4, input_dim=2, activation='relu'))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X, y, epochs=200, verbose=0)
loss, accuracy = model.evaluate(X, y, verbose=0)

print(f"Model Accuracy: {accuracy*100:.2f}%")
predictions = model.predict(X)
print("Predictions:")
for i in range(len(X)):
    print(f"Input: {X[i]} => Predicted: {predictions[i][0]:.4f}")
""")
    
def digit():
    print("""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.utils import to_categorical
(X_train, y_train), (X_test, y_test) = mnist.load_data()
X_train = X_train / 255.0
X_test = X_test / 255.0
y_train = to_categorical(y_train, 10)
y_test = to_categorical(y_test, 10)
model = Sequential()
model.add(Flatten(input_shape=(28,28)))
model.add(Dense(128, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(10, activation='softmax'))
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=5, batch_size=128, verbose=1)
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Accuracy: {accuracy*100:.2f}%")
predictions = model.predict(X_test)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = np.argmax(y_test, axis=1)
fig, axes = plt.subplots(3, 3, figsize=(9,9))
for i, ax in enumerate(axes.flat):
    ax.imshow(X_test[i], cmap='gray')
    ax.set_title(f"Pred: {predicted_classes[i]}")
    ax.axis('off')
plt.tight_layout()
plt.show()
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(true_classes, predicted_classes)
plt.figure(figsize=(10,8))
sns.heatmap(cm, annot=False, cmap='Blues')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()
""")

def xray():
    print("""
!pip install tensorflow numpy matplotlib

import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Flatten, Reshape

(X_train, _), (X_test, _) = cifar10.load_data()

X_train = np.mean(X_train, axis=-1)
X_test = np.mean(X_test, axis=-1)

X_train = X_train.astype("float32") / 255.0
X_test = X_test.astype("float32") / 255.0

X_train_flat = X_train.reshape((len(X_train), -1))
X_test_flat = X_test.reshape((len(X_test), -1))
input_dim = X_train_flat.shape[1]

input_layer = Input(shape=(input_dim,))
encoded = Dense(128, activation='relu')(input_layer)
encoded = Dense(64, activation='relu')(encoded)
decoded = Dense(128, activation='relu')(encoded)
decoded = Dense(input_dim, activation='sigmoid')(decoded)

autoencoder = Model(input_layer, decoded)
autoencoder.compile(optimizer='adam', loss='mse')

history = autoencoder.fit(X_train_flat, X_train_flat,
                          epochs=10,
                          batch_size=256,
                          shuffle=True,
                          validation_data=(X_test_flat, X_test_flat),
                          verbose=1)

decoded_imgs = autoencoder.predict(X_test_flat[:7])

plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.title("Autoencoder Training Loss")
plt.show()

n = 7
plt.figure(figsize=(14, 4))
for i in range(n):
    ax = plt.subplot(2, n, i+1)
    plt.imshow(X_test[i], cmap='gray')
    plt.title("Original")
    plt.axis("off")

    ax = plt.subplot(2, n, i+1+n)
    plt.imshow(decoded_imgs[i].reshape(32, 32), cmap='gray')
    plt.title("Reconstructed")
    plt.axis("off")

plt.tight_layout()
plt.show()
""")
    
def speech():
    print("""
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np

SpeechCommands = [
    "turn on the lights", "turn off the lights", "play music", "stop music",
    "increase volume", "decrease volume", "open door", "close door",
    "call john", "send message", "set alarm", "cancel alarm",
    "weather today", "time now", "battery status", "wifi connect"
]

AudioFeatures = np.random.rand(len(SpeechCommands) * 50, 13)
CommandLabels = np.repeat(range(len(SpeechCommands)), 50)

CommandTokenizer = Tokenizer()
CommandTokenizer.fit_on_texts(SpeechCommands)
VocabSize = len(CommandTokenizer.word_index) + 1

TokenizedCommands = CommandTokenizer.texts_to_sequences(SpeechCommands)
MaxLength = max(len(seq) for seq in TokenizedCommands)
PaddedCommands = pad_sequences(TokenizedCommands, maxlen=MaxLength)

SpeechModel = Sequential([
    Dense(128, activation='relu', input_shape=(13,)),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(len(SpeechCommands), activation='softmax')
])

SpeechModel.compile(optimizer='adam',
                    loss='sparse_categorical_crossentropy',
                    metrics=['accuracy'])

TrainingHistory = SpeechModel.fit(
    AudioFeatures, CommandLabels,
    validation_split=0.2,
    epochs=30,
    verbose=0
)

TestFeatures = np.random.rand(10, 13)
Predictions = SpeechModel.predict(TestFeatures, verbose=0)
PredictedCommands = np.argmax(Predictions, axis=1)
Confidences = np.max(Predictions, axis=1)

print("\nSpeech Recognition Results:")
print("Sample | Predicted Command        | Confidence")
print("-" * 50)
for i in range(10):
    CommandText = SpeechCommands[PredictedCommands[i]]
    print(f"   {i+1}   | {CommandText:<20} | {Confidences[i]*100:.1f}%")

TrainAccuracy = TrainingHistory.history['accuracy'][-1]
ValAccuracy = TrainingHistory.history['val_accuracy'][-1]

print(f"\nModel Performance:")
print(f"Training Accuracy   : {TrainAccuracy:.4f}")
print(f"Validation Accuracy : {ValAccuracy:.4f}")
print(f"Vocabulary Size     : {VocabSize}")
print(f"Command Classes     : {len(SpeechCommands)}")
""")
    
def traffic():
    print("""
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Dropout, Flatten
from tensorflow.keras.utils import to_categorical
(X_train, y_train), (X_test, y_test) = cifar10.load_data()
X_train = X_train.astype('float32') / 255.0
X_test = X_test.astype('float32') / 255.0
y_train = to_categorical(y_train, 10)
y_test = to_categorical(y_test, 10)
model = Sequential()
model.add(Conv2D(32, (3,3), activation='relu', input_shape=(32,32,3)))
model.add(MaxPooling2D((2,2)))
model.add(Dropout(0.25))
model.add(Conv2D(64, (3,3), activation='relu'))
model.add(MaxPooling2D((2,2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(10, activation='softmax'))
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=5, batch_size=64, verbose=1, validation_data=(X_test, y_test))
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Accuracy: {accuracy*100:.2f}%")

predictions = model.predict(X_test)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = np.argmax(y_test, axis=1)
labels = ['airplane','automobile','bird','cat','deer','dog','frog','horse','ship','truck']
n = 9
plt.figure(figsize=(10,10))
for i in range(n):
    plt.subplot(3,3,i+1)
    plt.imshow(X_test[i])
    plt.title(f"Pred: {labels[predicted_classes[i]]}")
    plt.axis('off')
plt.tight_layout()
plt.show()
""")
    
def fraud():
    print("""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier
X = np.array([
    [100, 2000],
    [102, 1800],
    [98, 2500],
    [150, 8000],
    [160, 9000],
    [95, 1500],
    [170, 10000],
    [120, 3000]
])
y = np.array([0,0,0,1,1,0,1,0])
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = SGDClassifier(loss='log_loss', max_iter=1000, tol=1e-3)
model.fit(X_scaled, y)
new_data = np.array([[155, 8500]])
new_scaled = scaler.transform(new_data)
prob = model.predict_proba(new_scaled)[0][1]
print(f"Fraud Probability: {prob:.2f}")
if prob > 0.6:
    print("Alert: Potential fraud detected in share market transaction!")
else:
    print("No fraud detected.")
probs = model.predict_proba(X_scaled)[:,1]
plt.scatter(range(len(probs)), probs, c=y, cmap='coolwarm', edgecolor='k')
plt.axhline(0.6, color='r', linestyle='--', label='Alert Threshold')
plt.xlabel("Sample Index")
plt.ylabel("Fraud Probability")
plt.legend()
plt.title("Fraud Probability Visualization")
plt.show()

""")
    
def rbm():
    print("""
# rbm image segmentation
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_digits
from sklearn.neural_network import BernoulliRBM
from sklearn.preprocessing import MinMaxScaler

digits = load_digits()
images = digits.images
X = digits.data

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

rbm = BernoulliRBM(n_components=64, learning_rate=0.05, n_iter=50, random_state=42)
rbm.fit(X_scaled)

hidden = rbm.transform(X_scaled)
X_reconstructed = np.dot(hidden, rbm.components_)
X_reconstructed = np.clip(X_reconstructed, 0, 1)

n = 7
plt.figure(figsize=(14, 4))
for i in range(n):
    plt.subplot(2, n, i + 1)
    plt.imshow(images[i], cmap='gray')
    plt.title("Original")
    plt.axis('off')

    plt.subplot(2, n, i + 1 + n)
    plt.imshow(X_reconstructed[i].reshape(8, 8), cmap='gray')
    plt.title("Segmented")
    plt.axis('off')

plt.tight_layout()
plt.show()
""")

def lstm():
    print("""
import numpy as np
from tensorflow.keras.datasets import imdb
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dropout, Dense
from tensorflow.keras.preprocessing.sequence import pad_sequences
max_features = 10000
maxlen = 200
(X_train, y_train), (X_test, y_test) = imdb.load_data(num_words=max_features)
X_train = pad_sequences(X_train, maxlen=maxlen)
X_test = pad_sequences(X_test, maxlen=maxlen)
model = Sequential()
model.add(Embedding(max_features, 128, input_length=maxlen))
model.add(LSTM(128))
model.add(Dropout(0.5))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.summary()
model.fit(X_train, y_train, epochs=3, batch_size=64, validation_split=0.2, verbose=1)
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Accuracy: {accuracy*100:.2f}%")
predictions = model.predict(X_test)
pred_labels = (predictions > 0.5).astype(int)
word_index = imdb.get_word_index()
index_word = {v+3:k for k,v in word_index.items()}
index_word[0] = '<PAD>'
index_word[1] = '<START>'
index_word[2] = '<UNK>'
index_word[3] = '<UNUSED>'
n = 5
for i in range(n):
    review = ' '.join([index_word.get(idx, '?') for idx in X_test[i] if idx > 3])
    print(f"\nReview {i+1}: {review}")
    print(f"Predicted Sentiment: {'Positive' if pred_labels[i][0]==1 else 'Negative'} (Probability: {predictions[i][0]:.2f})")
""")
    
def speech1():
    print("""
# Step 1: Install Whisper and ffmpeg
!pip install openai-whisper
!sudo apt update && sudo apt install ffmpeg -y

# Step 2: Import libraries
import whisper
from google.colab import files

# Step 3: Upload your audio file
print("Upload your audio file (wav/mp3):")
uploaded = files.upload()

# Get the uploaded file name
file_path = list(uploaded.keys())[0]
print(f"File uploaded: {file_path}")

# Step 4: Load Whisper model
print("Loading Whisper model...")
model = whisper.load_model("small")  # you can also try "tiny", "base", "medium", "large"

# Step 5: Transcribe the audio
print("Transcribing...")
result = model.transcribe(file_path)

# Step 6: Show the transcribed text
print("\nTranscribed Text:")
print(result["text"]""")


def rbm_fe():
    print("""
from sklearn.datasets import fetch_openml
from sklearn.neural_network import BernoulliRBM
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

print("Loading MNIST dataset...")
mnist = fetch_openml('mnist_784', version=1)
X, y = mnist.data, mnist.target.astype(int)

X = MinMaxScaler().fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rbm = BernoulliRBM(n_components=100, learning_rate=0.06, batch_size=10, n_iter=10, random_state=0)

print("Training RBM for feature extraction...")
rbm.fit(X_train)

X_train_features = rbm.transform(X_train)
X_test_features = rbm.transform(X_test)

print("Original feature shape:", X_train.shape)
print("Extracted RBM feature shape:", X_train_features.shape)

classifier = LogisticRegression(max_iter=1000)
classifier.fit(X_train_features, y_train)

accuracy = classifier.score(X_test_features, y_test)
print("Accuracy using RBM features:", accuracy)
""")
    
def stock():
    print("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.optimizers import Adam

df = pd.read_csv("/mnt/data/Stock Market Anomaly Detection Dataset.csv")
print("Dataset shape:", df.shape)
print(df.head())

df = df.select_dtypes(include=[np.number])
df = df.dropna()

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(df)
print("Scaled data shape:", X_scaled.shape)

input_dim = X_scaled.shape[1]
encoding_dim = input_dim // 2
input_layer = Input(shape=(input_dim,))
encoded = Dense(encoding_dim, activation='relu')(input_layer)
encoded = Dense(encoding_dim // 2, activation='relu')(encoded)
decoded = Dense(encoding_dim, activation='relu')(encoded)
decoded = Dense(input_dim, activation='sigmoid')(decoded)

autoencoder = Model(inputs=input_layer, outputs=decoded)
autoencoder.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
autoencoder.summary()

history = autoencoder.fit(
    X_scaled, X_scaled,
    epochs=50,
    batch_size=32,
    validation_split=0.2,
    verbose=1
)

reconstructed = autoencoder.predict(X_scaled)
mse = np.mean(np.power(X_scaled - reconstructed, 2), axis=1)
df["Reconstruction_Error"] = mse

threshold = np.quantile(mse, 0.99)
df["Anomaly"] = df["Reconstruction_Error"] > threshold

print("Threshold:", threshold)
print("Number of anomalies:", df["Anomaly"].sum())

plt.figure(figsize=(12,6))
plt.plot(df.index, df["Reconstruction_Error"], label="Reconstruction Error")
plt.axhline(y=threshold, color='r', linestyle='--', label='Threshold')
plt.legend()
plt.title("Reconstruction Error - Anomaly Detection")
plt.xlabel("Index")
plt.ylabel("MSE Loss")
plt.show()

print("Top anomalies detected:")
print(df[df["Anomaly"]].head())
""")
    
def single():
    print("""
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

X = np.array([[0,0], [0,1], [1,0], [1,1]])
y = np.array([[0], [0], [0], [1]])

model = Sequential([
    Dense(1, input_dim=2, activation='sigmoid')
])

model.compile(optimizer='sgd', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(X, y, epochs=500, verbose=0)

loss, acc = model.evaluate(X, y, verbose=0)
print(f"Training Accuracy: {acc*100:.2f}%")

predictions = model.predict(X)
print("\nPredictions:")
for i, p in enumerate(predictions):
    print(f"Input: {X[i]} -> Predicted: {p[0]:.4f}")

model.summary()
""")
    
def email():
    print("""
import pandas as pd
import string
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')

data = pd.read_csv("emails.csv", encoding='latin-1')
data.columns = ['message', 'label_num']

def preprocess_text(text):
    text = text.lower()
    text = ''.join([char for char in text if char not in string.punctuation])
    stop_words = stopwords.words('english')
    text = ' '.join([word for word in text.split() if word not in stop_words])
    return text

data['clean_message'] = data['message'].apply(preprocess_text)

X_train, X_test, y_train, y_test = train_test_split(
    data['clean_message'], data['label_num'], test_size=0.2, random_state=42
)

tfidf = TfidfVectorizer()
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

model = MultinomialNB()
model.fit(X_train_tfidf, y_train)

y_pred = model.predict(X_test_tfidf)

print("✅ Accuracy:", accuracy_score(y_test, y_pred))
print("\n📊 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\n📈 Classification Report:\n", classification_report(y_test, y_pred))

sample_message = ["Subject: Win a free vacation now! Call us immediately!"]
sample_message_tfidf = tfidf.transform(sample_message)
prediction = model.predict(sample_message_tfidf)

print("\n💬 Message:", sample_message[0])
print("🔍 Prediction:", "Spam" if prediction[0] == 1 else "Not Spam")
          """)

def weather():
    print("""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout

df = pd.read_csv('weather_forecast_data.csv')
df['Rain'] = df['Rain'].map({'rain': 1, 'no rain': 0})

X = df.drop('Rain', axis=1)
y = df['Rain']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

model = Sequential([
    Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dropout(0.3),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

history = model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2, verbose=1)

loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Accuracy: {acc:.4f}")

def predict_weather(params):
    params_scaled = scaler.transform([params])
    prob = model.predict(params_scaled)[0][0]
    result = "Rain" if prob > 0.5 else "No Rain"
    print(f"Prediction: {result} (Rain Probability: {prob:.2%})")
    return result, prob

predict_weather([25, 80, 5, 60, 1015])

model.save('weather_forecast_model.h5')
""")

def ner():
    print("""
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Embedding, Dense, TimeDistributed, Bidirectional
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder

sentences = [
    ["John", "lives", "in", "New", "York"],
    ["Mary", "works", "at", "Google"],
    ["Paris", "is", "beautiful"]
]

tags = [
    ["B-PER", "O", "O", "B-LOC", "I-LOC"],
    ["B-PER", "O", "O", "B-ORG"],
    ["B-LOC", "O", "O"]
]


words = list(set(word for sent in sentences for word in sent))
tags_list = list(set(tag for tag_seq in tags for tag in tag_seq))

word2idx = {w: i + 2 for i, w in enumerate(words)}  # +2 for padding and unknown
word2idx["PAD"] = 0
word2idx["UNK"] = 1

tag2idx = {t: i for i, t in enumerate(tags_list)}

X = [[word2idx.get(w, 1) for w in s] for s in sentences]
y = [[tag2idx[t] for t in ts] for ts in tags]

max_len = max(len(s) for s in X)
X = pad_sequences(X, maxlen=max_len, padding="post")
y = pad_sequences(y, maxlen=max_len, padding="post")

y = [to_categorical(i, num_classes=len(tag2idx)) for i in y]

model = Sequential()
model.add(Embedding(input_dim=len(word2idx), output_dim=64, input_length=max_len))
model.add(Bidirectional(LSTM(units=64, return_sequences=True)))
model.add(TimeDistributed(Dense(len(tag2idx), activation="softmax")))

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

model.fit(np.array(X), np.array(y), batch_size=1, epochs=10, verbose=1)

test_sentence = ["John", "works", "in", "Paris"]
test_seq = [word2idx.get(w, 1) for w in test_sentence]
test_seq = pad_sequences([test_seq], maxlen=max_len, padding="post")

pred = model.predict(test_seq)
pred_tags = [list(tag2idx.keys())[np.argmax(p)] for p in pred[0]]

print("
🧾 Sentence:", test_sentence)
print("🏷️ Predicted Tags:", pred_tags)
""")

def facial():
    print("""

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
import numpy as np
from tensorflow.keras.preprocessing import image



train_dir = "dataset/train"
test_dir = "dataset/test"


img_height = 224
img_width = 224
batch_size = 32

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    zoom_range=0.2,
    shear_range=0.2,
    horizontal_flip=True
)

test_datagen = ImageDataGenerator(rescale=1./255)

train_data = train_datagen.flow_from_directory(
    train_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical'
)

test_data = test_datagen.flow_from_directory(
    test_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical'
)

num_classes = len(train_data.class_indices)
print("Classes:", train_data.class_indices)


model = models.Sequential([
    layers.Conv2D(32, (3,3), activation='relu', input_shape=(img_height, img_width, 3)),
    layers.MaxPooling2D(2,2),

    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Conv2D(128, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(num_classes, activation='softmax')
])

model.summary()

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])


history = model.fit(
    train_data,
    epochs=10,
    validation_data=test_data
)


model.save("face_recognition_cnn.h5")
print("✅ Model Saved!")


def predict_image(img_path):
    img = image.load_img(img_path, target_size=(img_height, img_width))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # add batch dimension

    predictions = model.predict(img_array)
    class_index = np.argmax(predictions[0])
    class_labels = list(train_data.class_indices.keys())
    return class_labels[class_index]

# Example usage
# print(predict_image("some_image.jpg"))

""")