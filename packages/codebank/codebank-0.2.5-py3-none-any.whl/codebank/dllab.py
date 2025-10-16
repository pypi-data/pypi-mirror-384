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

