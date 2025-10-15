from sklearn.linear_model import LinearRegression
import numpy as np

def calculate_correlation(x, y):
    x_mean = x.mean()
    y_mean = y.mean()
    covariance = ((x - x_mean) * (y - y_mean)).mean()
    x_var = ((x - x_mean) ** 2).mean()
    y_var = ((y - y_mean) ** 2).mean()
    x_std = x_var**0.5
    y_std = y_var**0.5
    correlation = covariance / (x_std * y_std)
    return correlation



def calculate_RMSE(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    RMSE = np.sqrt(np.mean((x-y)**2))
    
    return RMSE
