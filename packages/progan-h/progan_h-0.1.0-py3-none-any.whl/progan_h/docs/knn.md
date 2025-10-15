# K-Nearest Neighbors (KNN) Regression

## Overview

K-Nearest Neighbors is a simple, yet powerful machine learning algorithm used for both classification and regression tasks. In this example, we'll explore KNN Regression for predicting city scores based on population and area.

---

## Installation

First, install the required dependencies:

```bash
pip install scikit-learn numpy pandas
```

---

## Complete Example

### 1. Import Required Libraries

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error
```

### 2. Generate Sample Dataset

```python
# Generating the dataset
np.random.seed(0)  # For reproducibility
num_samples = 1000

# Generate features and target
city_population = np.random.uniform(10000, 1000000, num_samples)
city_area = np.random.uniform(10, 500, num_samples)
city_score = 0.5 + 0.0001 * city_population + 0.001 * city_area + np.random.normal(0, 0.1, num_samples)

# Create DataFrame
df = pd.DataFrame({
    'City_Population': city_population,
    'City_Area': city_area,
    'City_Score': city_score
})
```

### 3. Prepare Data for Modeling

```python
# Prepare Data for Modeling
X = df[['City_Population', 'City_Area']]
y = df['City_Score']

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```

### 4. Scale the Data

```python
# Scaling the data (important for KNN!)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

### 5. Find Optimal K Value

```python
# DEFINE THE MODEL for KNN
def knn_regression():
    best_k = None
    best_mse = float("inf")

    for k in range(5, 20):  # Test K values from 5 to 19
        model = KNeighborsRegressor(n_neighbors=k)
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)

        mse = mean_squared_error(y_test, y_pred)

        if mse < best_mse:
            best_mse = mse
            best_k = k

    return best_k, best_mse


# Run the function
best_k_value, best_mse_value = knn_regression()

print("Best K value:", best_k_value)
print("Best MSE value:", best_mse_value)
```

### 6. Error Handling (Optional)

```python
# Get best K value with error handling
try:
    best_k_value, _ = knn_regression()
    print(f"Best K value: {best_k_value}")
except Exception as e:
    print(f"Error: {type(e).__name__} - {e}")
    best_k_value = None

# Get best MSE value with error handling
try:
    _, best_mse_value = knn_regression()
    print(f"Best MSE value: {best_mse_value}")
except Exception as e:
    print(f"Error: {type(e).__name__} - {e}")
    best_mse_value = None
```

---

## Key Concepts

### What is KNN?

- **K-Nearest Neighbors** finds the K closest data points to make predictions
- For regression, it averages the values of the K nearest neighbors
- The choice of K significantly impacts model performance

### Why Scale Data?

KNN uses distance metrics, so features with larger ranges can dominate the calculation. StandardScaler ensures all features contribute equally.

### Choosing K

- **Small K**: More sensitive to noise, can overfit
- **Large K**: Smoother predictions, may underfit
- **Optimal K**: Balance between bias and variance (found through testing)

---

## Tips & Best Practices

1. **Always scale your data** when using KNN
2. **Test multiple K values** to find the optimal one
3. **Use cross-validation** for more robust K selection
4. **Consider the curse of dimensionality** - KNN struggles with high-dimensional data
5. **Monitor performance metrics** like MSE, RMSE, or R²

---

## Common Parameters

- `n_neighbors`: Number of neighbors to use (K value)
- `weights`: 'uniform' or 'distance' (distance-weighted predictions)
- `metric`: Distance metric to use (default: 'minkowski')
- `p`: Power parameter for Minkowski metric (p=2 is Euclidean distance)

---

**Happy Learning! 🚀**
