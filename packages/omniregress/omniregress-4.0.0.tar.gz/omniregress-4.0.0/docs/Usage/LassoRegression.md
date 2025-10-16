# LassoRegression Usage Guide

## 🌟 Overview

Lasso (Least Absolute Shrinkage and Selection Operator) Regression is a linear modeling technique that performs both **regularization** and **feature selection** using L1 penalty. It's particularly useful for:

- **Feature selection**: Automatically drives irrelevant feature coefficients to exactly zero
- **High-dimensional data**: Works well when number of features > number of samples
- **Multicollinearity**: Handles correlated features by selecting one
- **Interpretable models**: Creates sparse, interpretable models

## 📦 Importing

```python
from omniregress import LassoRegression
import numpy as np
```

## 🛠️ Initialization

### Basic initialization
```python
# Default parameters
model = LassoRegression()

# Custom parameters
model = LassoRegression(
    alpha=1.0,      # Regularization strength
    max_iter=1000,  # Maximum iterations
    tol=1e-4        # Convergence tolerance
)
```

### Parameter Details

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 1.0 | Regularization strength. **Higher = more sparsity** |
| `max_iter` | 1000 | Maximum coordinate descent iterations |
| `tol` | 1e-4 | Convergence tolerance for coefficients |

## ⚙️ Methods

### 🎯 Fitting the Model

```python
# Basic fit
model.fit(X, y)

# With method chaining
model = LassoRegression(alpha=0.5).fit(X, y)
```

### 🔮 Making Predictions

```python
# Predict on training data
y_pred = model.predict(X_train)

# Predict on new data
y_test_pred = model.predict(X_test)
```

### 📊 Evaluating Performance

```python
# R² score
r_squared = model.score(X, y)

# Custom evaluation
from sklearn.metrics import mean_squared_error, mean_absolute_error

mse = mean_squared_error(y_true, y_pred)
mae = mean_absolute_error(y_true, y_pred)
```

### 🔍 Feature Selection Analysis

```python
# Get non-zero coefficients
indices, values = model.get_nonzero_coefficients()
print(f"Selected features: {indices}")
print(f"Coefficient values: {values}")

# Sparsity analysis
sparsity = model.sparsity_ratio()
print(f"{sparsity:.1%} of features were eliminated")
```

## 🏷️ Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `coefficients` | ndarray | Feature coefficients (some may be zero) |
| `intercept` | float | Model intercept term |
| `alpha` | float | Current regularization strength |
| `max_iter` | int | Maximum iterations setting |
| `tol` | float | Convergence tolerance setting |

## 👨‍💻 Complete Examples

### Example 1: Basic Usage with Feature Selection

```python
import numpy as np
from omniregress import LassoRegression

# Generate synthetic data with irrelevant features
np.random.seed(42)
X = np.random.randn(100, 10)  # 10 features
true_coef = np.array([1.5, -2.0, 0, 0, 3.0, 0, 0, 0, -1.0, 0])  # Only 4 relevant features
y = X @ true_coef + np.random.normal(0, 0.5, 100)

# Fit Lasso model
model = LassoRegression(alpha=0.5)
model.fit(X, y)

# Analyze results
print("True non-zero coefficients:", np.where(true_coef != 0)[0])
print("Estimated non-zero coefficients:", model.get_nonzero_coefficients()[0])
print(f"R² Score: {model.score(X, y):.3f}")
print(f"Sparsity: {model.sparsity_ratio():.1%}")
```

### Example 2: Alpha Tuning for Optimal Sparsity

```python
import matplotlib.pyplot as plt
import numpy as np
from omniregress import LassoRegression

# Generate sample data
np.random.seed(42)
X = np.random.randn(100, 10)  # 100 samples, 10 features
# Only 4 features are actually relevant
true_coef = np.array([1.5, -2.0, 0, 0, 3.0, 0, 0, 0, -1.0, 0])
y = X @ true_coef + np.random.normal(0, 0.5, 100)

print(f"Data shape: X {X.shape}, y {y.shape}")
print(f"True non-zero coefficients at indices: {np.where(true_coef != 0)[0]}")

# Test different alpha values
alphas = [0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0]
non_zero_counts = []
scores = []

for alpha in alphas:
    model = LassoRegression(alpha=alpha)
    model.fit(X, y)
    
    non_zero = len(model.get_nonzero_coefficients()[0])
    score = model.score(X, y)
    
    non_zero_counts.append(non_zero)
    scores.append(score)
    
    print(f"Alpha: {alpha:6.3f} | Features: {non_zero:2d} | R²: {score:.3f}")

# Plot results
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.semilogx(alphas, non_zero_counts, 'bo-', linewidth=2, markersize=8)
plt.xlabel('Alpha (Regularization Strength)')
plt.ylabel('Number of Non-zero Features')
plt.title('Feature Selection vs Regularization')
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.semilogx(alphas, scores, 'ro-', linewidth=2, markersize=8)
plt.xlabel('Alpha (Regularization Strength)')
plt.ylabel('R² Score')
plt.title('Performance vs Regularization')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Show final model details for alpha=0.1 (usually a good default)
print("\n" + "="*50)
print("Detailed analysis for alpha=0.1:")
model = LassoRegression(alpha=0.1)
model.fit(X, y)

indices, values = model.get_nonzero_coefficients()
print(f"Selected features: {indices}")
print(f"Coefficient values: {np.round(values, 3)}")
print(f"True coefficients: {true_coef[indices]}")
print(f"Sparsity ratio: {model.sparsity_ratio():.1%}")
print(f"R² score: {model.score(X, y):.3f}")
```

### Example 3: Comparison with Ridge Regression

```python
import numpy as np
from omniregress import LassoRegression, RidgeRegression

# Generate sample data with some irrelevant features
np.random.seed(42)
X = np.random.randn(100, 5)  # 100 samples, 5 features

# Only 3 features are actually relevant
true_coef = np.array([1.5, -2.0, 3.0, 0, 0])
y = X @ true_coef + np.random.normal(0, 0.3, 100)

print("Dataset Info:")
print(f"X shape: {X.shape}")
print(f"True relevant features: {np.where(true_coef != 0)[0]}")
print(f"True coefficients: {true_coef[true_coef != 0]}")
print()

# Compare Lasso vs Ridge
lasso_model = LassoRegression(alpha=0.5)
ridge_model = RidgeRegression(alpha=0.5)

lasso_model.fit(X, y)
ridge_model.fit(X, y)

print("Lasso Coefficients (sparse):")
print(np.round(lasso_model.coefficients, 3))
print(f"Non-zero features: {len(lasso_model.get_nonzero_coefficients()[0])}")

print("\nRidge Coefficients (dense):")
print(np.round(ridge_model.coefficients, 3))
print(f"Non-zero features: {len(ridge_model.coefficients)}")

print(f"\nLasso R²:  {lasso_model.score(X, y):.3f}")
print(f"Ridge R²: {ridge_model.score(X, y):.3f}")

# Additional comparison details
print("\n" + "="*50)
print("FEATURE SELECTION COMPARISON")
print("="*50)

lasso_indices, lasso_values = lasso_model.get_nonzero_coefficients()
print("Lasso selected features:", lasso_indices)
print("Lasso coefficient values:", np.round(lasso_values, 3))

print(f"\nLasso sparsity ratio: {lasso_model.sparsity_ratio():.1%}")
print(f"Features eliminated by Lasso: {X.shape[1] - len(lasso_indices)}/{X.shape[1]}")

# Show which features Lasso correctly identified
correct_selections = sum(1 for idx in lasso_indices if true_coef[idx] != 0)
print(f"Correctly identified relevant features: {correct_selections}/{sum(true_coef != 0)}")
```

## 💡 Key Notes

### 🎯 When to Use Lasso

- **Feature selection** is needed
- **High-dimensional** data (p > n)
- **Interpretable** models required
- Dealing with **multicollinearity**

### ⚠️ Important Considerations

1. **Alpha Selection**: 
   - Small alpha → Less regularization, fewer zeros
   - Large alpha → More regularization, more zeros
   - Use cross-validation to find optimal alpha

2. **Feature Scaling**:
   - Lasso is sensitive to feature scales
   - Standardize features for best results
   - Our implementation handles scaling internally

3. **Convergence**:
   - Monitor convergence with `max_iter` and `tol`
   - Increase `max_iter` if model doesn't converge
   - Decrease `tol` for more precise solutions

4. **Sparsity Interpretation**:
   - Zero coefficients = irrelevant features
   - Non-zero coefficients = selected features
   - Use `sparsity_ratio()` to quantify feature reduction

### 🔧 Advanced Usage

```python
# Progressive regularization
alphas = np.logspace(-3, 1, 20)
for alpha in alphas:
    model = LassoRegression(alpha=alpha)
    model.fit(X, y)
    sparsity = model.sparsity_ratio()
    score = model.score(X, y)
    print(f"Alpha: {alpha:.3f} | Sparsity: {sparsity:.1%} | R²: {score:.3f}")

# Feature stability analysis
feature_stability = {}
for feature_idx in range(X.shape[1]):
    feature_stability[feature_idx] = 0

n_runs = 10
for run in range(n_runs):
    model = LassoRegression(alpha=0.5)
    model.fit(X, y)
    selected_features = model.get_nonzero_coefficients()[0]
    for feature in selected_features:
        feature_stability[feature] += 1

print("Feature selection frequency:")
for feature, count in feature_stability.items():
    print(f"Feature {feature}: {count}/{n_runs} times")
```

Lasso regression is a powerful tool for creating parsimonious models that automatically select the most relevant features while maintaining good predictive performance!