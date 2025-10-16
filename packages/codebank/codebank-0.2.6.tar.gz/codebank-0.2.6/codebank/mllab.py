def one():
    print('''
import numpy as np
import pandas as pd
df = pd.read_csv('Iris1.csv')
df.head()
from sklearn import tree
from sklearn.model_selection import train_test_split
X = df[['SepalLengthCm', 'SepalWidthCm', 'PetalLengthCm', 'PetalWidthCm']]
Y = df['Species']
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
model = tree.DecisionTreeClassifier()
model.fit(X_train, Y_train)
print("score", model.score(X_test, Y_test))
tree.plot_tree(model)
''')

def two():
    print('''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn import svm
data = pd.read_csv("D:\\dataset\\spam.csv", encoding='ISO-8859-1')
data.info()
X = data["v2"].values
Y = data["v1"].values
from sklearn.model_selection import train_test_split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=0)
cv = CountVectorizer()
X_train = cv.fit_transform(X_train)
X_test = cv.transform(X_test)
print(X_train)
print(X_test)
print(Y_train)
from sklearn.svm import SVC
classifier = SVC(kernel="rbf", random_state=0)
classifier.fit(X_train, Y_train)
print(classifier.score(X_test, Y_test))
''')

def three():
    print('''
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
imagePath = "argentina.png"
faceCascadePath = "haarcascade_frontalface_default.xml"
eyeCascadePath = "haarcascade_eye_tree_eyeglasses.xml"
img = np.array(Image.open(imagePath))
plt.imshow(img)
plt.axis('off')
plt.show()
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
faceCascade = cv2.CascadeClassifier(faceCascadePath)
eyeCascade = cv2.CascadeClassifier(eyeCascadePath)
faces = faceCascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=2,
    minSize=(30, 30),
    flags=cv2.CASCADE_SCALE_IMAGE
)
print("Found {0} faces!".format(len(faces)))
for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.axis('off')
plt.show()
''')

def four():
    print('''
import tensorflow as tf
from tensorflow.keras import layers, losses
from random import shuffle
import os
import cv2
import numpy as np
from PIL import Image

class_name1 = "person1"
class_name2 = "person2"
n_samples = 40
os.system(f'mkdir {class_name1}')
os.system(f'mkdir {class_name2}')

def generate_dataset(class_name):
    face_classifier = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    
    def face_cropped(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        if faces == ():
            return None
        for (x, y, w, h) in faces:
            cropped_face = img[y:y+h, x:x+w]
            return cropped_face

    cap = cv2.VideoCapture(0)
    img_id = 0
    while img_id <= n_samples:
        ret, frame = cap.read()
        if face_cropped(frame) is not None:
            img_id += 1
            face = cv2.resize(face_cropped(frame), (200, 200))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"{class_name}/img{img_id}.jpg", face)
            cv2.putText(face, str(img_id), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Cropped_Face", face)
        if cv2.waitKey(1) == 13 or int(img_id) == 20:
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Collecting samples is completed !!!")

generate_dataset(class_name1)
generate_dataset(class_name2)

def load_data(path):
    data = []
    for imgs in os.listdir(path):
        img = np.array(Image.open(f'{path}/{imgs}'))
        data.append(img)
    return data

def process_data(c1, c2):
    data = []
    x = []
    y = []
    
    for i in range(len(c1)):
        data.append([c1[i], [1, 0]])
    
    for i in range(len(c2)):
        data.append([c2[i], [0, 1]])
    
    for i in range(len(data)):
        x.append(data[i][0])
    
    for i in range(len(data)):
        y.append(data[i][1])
    
    return np.array(x), np.array(y)

def get_model(n_class):
    model = tf.keras.Sequential([
        tf.keras.Input((200, 200)),
        layers.Flatten(),
        layers.Dense(1024, activation='relu'),
        layers.Dense(512, activation='relu'),
        layers.Dense(256, activation='relu'),
        layers.Dense(128, activation='relu'),
        layers.Dense(n_class, activation='softmax'),
    ])
    model.compile(loss='categorical_crossentropy',
                  optimizer='Adam',
                  metrics=['accuracy'])
    return model

class1, class2 = load_data(class_name1), load_data(class_name2)
x, y = process_data(class1, class2)
model = get_model(n_class=2)
model.fit(x, y, epochs=20)
print(model.predict(np.array(Image.open()).reshape(1, 200, 200))[0])
''')

def five():
    print('''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler

iris = pd.read_csv("Iris1.csv")
x = iris.iloc[:, [0, 1, 2, 3]].values
iris_outcome = pd.crosstab(index=iris["Species"], columns="count")
iris_outcome

iris_setosa = iris.loc[iris["Species"] == "Iris-setosa"]
iris_virginica = iris.loc[iris["Species"] == "Iris-virginica"]
iris_versicolor = iris.loc[iris["Species"] == "Iris-versicolor"]

sns.FacetGrid(iris, hue="Species", height=3).map(sns.distplot, "PetalLengthCm").add_legend()
sns.FacetGrid(iris, hue="Species", height=3).map(sns.distplot, "PetalWidthCm").add_legend()
sns.FacetGrid(iris, hue="Species", height=3).map(sns.distplot, "SepalLengthCm").add_legend()
plt.show()

sns.boxplot(x="Species", y="PetalLengthCm", data=iris)
plt.show()

sns.violinplot(x="Species", y="PetalLengthCm", data=iris)
plt.show()

sns.set_style("whitegrid")
sns.pairplot(iris, hue="Species", height=3)
plt.show()

wcss = []
for i in range(1, 11):
    kmeans = KMeans(n_clusters=i, init='k-means++', max_iter=300, n_init=10, random_state=0)
    kmeans.fit(x)
    wcss.append(kmeans.inertia_)

plt.plot(range(1, 11), wcss)
plt.title('The elbow method')
plt.xlabel('Number of clusters')
plt.ylabel('WCSS')  # within-cluster sum of squares
plt.show()

kmeans = KMeans(n_clusters=3, init='k-means++', max_iter=300, n_init=10, random_state=0)
y_kmeans = kmeans.fit_predict(x)

plt.scatter(x[y_kmeans == 0, 0], x[y_kmeans == 0, 1], s=100, c='purple', label='Iris-setosa')
plt.scatter(x[y_kmeans == 1, 0], x[y_kmeans == 1, 1], s=100, c='orange', label='Iris-versicolour')
plt.scatter(x[y_kmeans == 2, 0], x[y_kmeans == 2, 1], s=100, c='green', label='Iris-virginica')
plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=100, c='red', label='Centroids')
plt.legend()

fig = plt.figure(figsize=(15, 15))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x[y_kmeans == 0, 0], x[y_kmeans == 0, 1], s=100, c='purple', label='Iris-setosa')
ax.scatter(x[y_kmeans == 1, 0], x[y_kmeans == 1, 1], s=100, c='orange', label='Iris-versicolour')
ax.scatter(x[y_kmeans == 2, 0], x[y_kmeans == 2, 1], s=100, c='green', label='Iris-virginica')
ax.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=100, c='red', label='Centroids')
plt.show()
''')

def fivea():
    print('''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

columns = ['age', 'workclass', 'fnlwgt', 'education', 'education_num', 'marital_status',
           'occupation', 'relationship', 'race', 'sex', 'capital_gain', 'capital_loss',
           'hours_per_week', 'native_country', 'salary']

data = pd.read_csv('D:/Docz/Clg/ML Lab/Dataset/adult/adult.data', names=columns, na_values=' ?')
print(data.head())

data = data.dropna()

label_enc = LabelEncoder()
for col in ['workclass', 'education', 'marital_status', 'occupation', 'relationship',
            'race', 'sex', 'native_country', 'salary']:
    data[col] = label_enc.fit_transform(data[col])

scaler = StandardScaler()
data[['age', 'fnlwgt', 'education_num', 'capital_gain', 'capital_loss', 'hours_per_week']] = scaler.fit_transform(
    data[['age', 'fnlwgt', 'education_num', 'capital_gain', 'capital_loss', 'hours_per_week']])

X = data.drop('salary', axis=1)
y = data['salary']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f'Accuracy: {accuracy}')
print(classification_report(y_test, y_pred))
''')

def six():
    print('''
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

mnist = fetch_openml('mnist_784', version=1)
X, y = mnist["data"], mnist["target"]
X = X / 255.0

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

mlp = MLPClassifier(hidden_layer_sizes=(50,), max_iter=20, alpha=1e-4,
                    solver='sgd', verbose=10, random_state=1, learning_rate_init=0.1)
mlp.fit(X_train, y_train)

y_pred = mlp.predict(X_test)

fig, axes = plt.subplots(2, 5, figsize=(10, 5))
for i, ax in enumerate(axes.ravel()):
    ax.matshow(X_test[i].reshape(28, 28), cmap=plt.cm.gray)
    ax.set_title(f'Prediction: {y_pred[i]}')
    ax.axis('off')

plt.show()
''')

def seven():
    print('''
import numpy as np
import pandas as pd
import re
import nltk
import matplotlib.pyplot as plt
%matplotlib inline

data_source_url = "Tweets.csv"
airline_tweets = pd.read_csv(data_source_url)
airline_tweets.head()

plot_size = plt.rcParams["figure.figsize"]
print(plot_size[0])
print(plot_size[1])

plt.rcParams["figure.figsize"] = plot_size
airline_tweets.airline.value_counts().plot(kind='pie', autopct='%1.0f%%')

airline_tweets.airline_sentiment.value_counts().plot(kind='pie', autopct='%1.0f%%', colors=["red", "yellow", "green"])

airline_sentiment = airline_tweets.groupby(['airline', 'airline_sentiment']).airline_sentiment.count().unstack()
airline_sentiment.plot(kind='bar')

import seaborn as sns
sns.barplot(x='airline_sentiment', y='airline_sentiment_confidence', data=airline_tweets)

features = airline_tweets.iloc[:, 10].values
labels = airline_tweets.iloc[:, 1].values

processed_features = []
for sentence in range(0, len(features)):
    processed_feature = re.sub(r'\W', ' ', str(features[sentence]))
    processed_feature = re.sub(r'\s+[a-zA-Z]\s+', ' ', processed_feature)
    processed_feature = re.sub(r'\^[a-zA-Z]\s+', ' ', processed_feature)
    processed_feature = re.sub(r'\s+', ' ', processed_feature, flags=re.I)
    processed_feature = re.sub(r'^b\s+', ' ', processed_feature)
    processed_feature = processed_feature.lower()
    processed_features.append(processed_feature)

!pip install nltk
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
nltk.download('stopwords')

vectorizer = TfidfVectorizer(max_features=2500, min_df=7, max_df=0.8, stop_words=stopwords.words('english'))
processed_features = vectorizer.fit_transform(processed_features).toarray()

from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(processed_features, labels, test_size=0.2, random_state=0)

from sklearn.ensemble import RandomForestClassifier
text_classifier = RandomForestClassifier(n_estimators=200, random_state=0)
text_classifier.fit(x_train, y_train)

predictions = text_classifier.predict(x_test)

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
print(confusion_matrix(y_test, predictions))
print(classification_report(y_test, predictions))
print(accuracy_score(y_test, predictions))
''')

def eight():
    print('''
import numpy as np
import pandas as pd
!pip install pgmpy

from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.estimators import MaximumLikelihoodEstimator
from pgmpy.inference import VariableElimination

heartDisease = pd.read_csv('heart.csv')
heartDisease = heartDisease.replace('?', np.nan)

print('Few examples from the dataset are given below')
print(heartDisease.head())
print('\nAttributes and datatypes')
print(heartDisease.dtypes)

model = BayesianModel([('age', 'heartdisease'), ('sex', 'heartdisease'), ('exang', 'heartdisease'), 
                       ('cp', 'heartdisease'), ('heartdisease', 'restecg'), ('heartdisease', 'chol')])

print('\nLearning CPD using Maximum likelihood estimators')
print(heartDisease.columns)

if 'heartdisease' not in heartDisease.columns:
    heartDisease = heartDisease.rename(columns={'target': 'heartdisease'})

unique_states = heartDisease['heartdisease'].unique().tolist()
print(unique_states)

model.fit(heartDisease, estimator=MaximumLikelihoodEstimator, state_names={'heartdisease': unique_states})

HeartDisease_infer = VariableElimination(model)

print('\n1. Probability of Heart Disease given evidence=restecg')
q1 = HeartDisease_infer.query(variables=['heartdisease'], evidence={'restecg': 1})
print(q1)

print('\n2. Probability of Heart Disease given evidence=cp')
q2 = HeartDisease_infer.query(variables=['heartdisease'], evidence={'cp': 2})
print(q2)
''')

def nine():
    print('''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sn
import keras
np.random.seed(2)
%matplotlib inline

data = pd.read_csv('creditcard.csv')
data.head()
data.info()

data.corrwith(data.Class).plot.bar(
    figsize=(20, 10), title="Correlation with class", fontsize=15, rot=45, grid=True)

sn.set(style="white")
corr = data.corr()
mask = np.zeros_like(corr)
mask[np.triu_indices_from(mask)] = True

f, ax = plt.subplots(figsize=(18, 15))
cmap = sn.diverging_palette(220, 10, as_cmap=True)
sn.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, center=0, square=True, linewidths=.5, cbar_kws={"shrink": .5})

data.isna().any()

from sklearn.preprocessing import StandardScaler
data['normalizedAmount'] = StandardScaler().fit_transform(data['Amount'].values.reshape(-1, 1))

data = data.drop(['Amount'], axis=1)
data = data.drop(['Time'], axis=1)
data.head()

X = data.iloc[:, data.columns != 'Class']
y = data.iloc[:, data.columns == 'Class']
X.info()
y.head()

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)

import keras
from keras.models import Sequential
from keras.layers import Dense

classifier = Sequential()
classifier.add(Dense(units=15, kernel_initializer='uniform', activation='relu', input_dim=29))
classifier.add(Dense(units=15, kernel_initializer='uniform', activation='relu'))
classifier.add(Dense(units=1, kernel_initializer='uniform', activation='sigmoid'))

classifier.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
classifier.fit(X_train, y_train, batch_size=32, epochs=10)

y_pred = classifier.predict(X_test)
y_pred = (y_pred > 0.5)
score = classifier.evaluate(X_test, y_test)
print(score)

from sklearn.metrics import confusion_matrix, accuracy_score
cm = confusion_matrix(y_test, y_pred)
from sklearn.metrics import classification_report
print(classification_report(y_test, y_pred))

df_cm = pd.DataFrame(cm, index=(0, 1), columns=(0, 1))
plt.figure(figsize=(10, 7))
sn.set(font_scale=1.4)
sn.heatmap(df_cm, annot=True, fmt='g')
print("Test Data Accuracy: %0.4f" % accuracy_score(y_test, y_pred))
''')
