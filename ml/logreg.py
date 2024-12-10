import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

# Load the dataset
data = pd.read_csv('ml/assets/fitness_level.csv')  # Replace with your actual dataset

# Preprocess the data
# Assuming 'Age', 'BMI', 'FAF_value', 'Gender_v' are columns in your dataset
X = data[['Age', 'BMI', 'FAF_value', 'Gender_v']]  # Input features
y = data['Fitness_Level']  # Target variable (Fitness level: Beginner, Intermediate, Advanced)

# Encode the target variable using LabelEncoder (if categorical)
encoder = LabelEncoder()
y = encoder.fit_transform(y)  # Convert categorical labels into numeric values

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardize the features (optional but recommended)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train the logistic regression model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate the model
print("Accuracy: ", accuracy_score(y_test, y_pred))

# Save the model if needed for later use
joblib.dump(model, 'fitness_level_model.pkl')


from sklearn.metrics import confusion_matrix, classification_report

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(cm)

# Classification Report
cr = classification_report(y_test, y_pred)
print("Classification Report:")
print(cr)
