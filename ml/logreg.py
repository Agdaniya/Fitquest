import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier,plot_tree
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


data = pd.read_csv('ml/assets/fitness_level.csv')

X = data[['Age', 'BMI', 'FAF_value', 'Gender_v']]
y = data['Fitness_Level']


encoder = LabelEncoder()
y = encoder.fit_transform(y)


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)


models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Naive Bayes": GaussianNB(),
    "Decision Tree": DecisionTreeClassifier(random_state=42)
}


for name, model in models.items():
    print(f"\n{name} Results:")
    
   
    model.fit(X_train, y_train)
    
    
    y_pred = model.predict(X_test)
    
    
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")
    
   
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

best_model = max(models, key=lambda m: accuracy_score(y_test, models[m].predict(X_test)))
joblib.dump(models[best_model], 'ml/models/best_fitness_model.pkl')
joblib.dump(scaler, 'ml/models/scaler.pkl')

print(f"\nBest Model Saved: {best_model}")
tree_model = models["Decision Tree"]




logreg_model = models["Logistic Regression"]
intercept = logreg_model.intercept_[0]
coefficients = logreg_model.coef_[0]
feature_names = ['Age', 'BMI', 'FAF_value', 'Gender_v']


equation = f"P(Y=1 | X) = 1 / (1 + exp(-({intercept:.4f} + " + " + ".join(f"{coef:.4f}*{feat}" for coef, feat in zip(coefficients, feature_names)) + ")))"

print("\nLogistic Regression Equation:")
print(equation)

nb_model = models["Naive Bayes"]
class_labels = encoder.classes_  
priors = nb_model.class_prior_   
means = nb_model.theta_          
variances = nb_model.var_      

print("\nNaïve Bayes Equations:")

for i, class_label in enumerate(class_labels):
    print(f"\nFor Class {class_label}: P(Y={class_label}) = {priors[i]:.4f}")
    for j, feature in enumerate(feature_names):
        mu = means[i, j]
        sigma = np.sqrt(variances[i, j])
        print(f"P({feature} | Y={class_label}) = (1 / sqrt(2π * {sigma:.4f}²)) * exp(-((X - {mu:.4f})²) / (2 * {sigma:.4f}²))")

plt.figure(figsize=(8, 4))
plot_tree(tree_model, feature_names=['Age', 'BMI', 'FAF_value', 'Gender_v'], 
          class_names=['Beginner', 'Intermediate', 'Advanced'], filled=True, fontsize=10)
plt.title("Decision Tree Visualization")
plt.show()