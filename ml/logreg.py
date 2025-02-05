import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

data = pd.read_csv('ml/assets/fitness_level.csv')  

X = data[['Age', 'BMI', 'FAF_value', 'Gender_v']]  
y = data['Fitness_Level']  

encoder = LabelEncoder()
y = encoder.fit_transform(y)  


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)


model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)


y_pred = model.predict(X_test)


print("Accuracy: ", accuracy_score(y_test, y_pred))


joblib.dump(model, 'ml/models/fitness_level_model.pkl')
joblib.dump(scaler, 'ml/models/scaler.pkl')

from sklearn.metrics import confusion_matrix, classification_report


cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(cm)

cr = classification_report(y_test, y_pred)
print("Classification Report:")
print(cr)
import os

os.makedirs('ml/models', exist_ok=True)
