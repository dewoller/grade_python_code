"""
Code template provider for generating realistic student code.

This module provides different types of code templates:
- Perfect implementations for each task
- Partial/incomplete implementations  
- Code with syntax errors
- Code with special characters/unicode

All templates are realistic and match expected student submissions.
"""

from typing import Dict
from .error_templates import ErrorCodeTemplates, SpecialCharTemplates


class CodeTemplateProvider:
    """Provides code templates for different scenarios."""
    
    def __init__(self):
        self.error_templates = ErrorCodeTemplates()
        self.special_templates = SpecialCharTemplates()
    
    def get_perfect_code(self, task_num: int) -> str:
        """Get perfect code implementation for a task."""
        templates = {
            2: '''# Task 2: Basic data manipulation
import pandas as pd
import numpy as np

def load_and_clean_data(file_path):
    """Load CSV file and clean the data."""
    df = pd.read_csv(file_path)
    df = df.dropna()
    df = df.drop_duplicates()
    return df

def analyze_data(df):
    """Perform basic statistical analysis."""
    return {
        'mean': df.select_dtypes(include=[np.number]).mean(),
        'std': df.select_dtypes(include=[np.number]).std(),
        'count': len(df)
    }

# Test the functions
df = load_and_clean_data('sample_data.csv')
results = analyze_data(df)
print(results)''',
            
            3: '''# Task 3: Data visualization
import matplotlib.pyplot as plt
import seaborn as sns

def create_histogram(data, column, bins=20):
    """Create histogram for specified column."""
    plt.figure(figsize=(10, 6))
    plt.hist(data[column], bins=bins, alpha=0.7, edgecolor='black')
    plt.title(f'Distribution of {column}')
    plt.xlabel(column)
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    plt.show()

def create_scatter_plot(data, x_col, y_col):
    """Create scatter plot between two columns."""
    plt.figure(figsize=(10, 6))
    plt.scatter(data[x_col], data[y_col], alpha=0.6)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f'{x_col} vs {y_col}')
    plt.grid(True, alpha=0.3)
    plt.show()

# Generate sample plots
create_histogram(df, 'value')
create_scatter_plot(df, 'x', 'y')''',
            
            4: '''# Task 4: Advanced data processing
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def preprocess_data(df):
    """Preprocess data for machine learning."""
    # Handle missing values
    df_clean = df.fillna(df.mean())
    
    # Scale numerical features
    scaler = StandardScaler()
    numerical_cols = df_clean.select_dtypes(include=[np.number]).columns
    df_clean[numerical_cols] = scaler.fit_transform(df_clean[numerical_cols])
    
    return df_clean, scaler

def perform_clustering(df, n_clusters=3):
    """Perform K-means clustering."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(df)
    return clusters, kmeans

# Apply preprocessing and clustering
df_processed, scaler = preprocess_data(df)
clusters, model = perform_clustering(df_processed)
df['cluster'] = clusters
print(f"Clustering completed with {len(set(clusters))} clusters")''',
            
            5: '''# Task 5: Statistical analysis
from scipy import stats
import statsmodels.api as sm

def correlation_analysis(df):
    """Perform correlation analysis."""
    numerical_df = df.select_dtypes(include=[np.number])
    correlation_matrix = numerical_df.corr()
    
    # Find strongest correlations
    strong_corr = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            corr_val = correlation_matrix.iloc[i, j]
            if abs(corr_val) > 0.7:
                strong_corr.append({
                    'var1': correlation_matrix.columns[i],
                    'var2': correlation_matrix.columns[j],
                    'correlation': corr_val
                })
    
    return correlation_matrix, strong_corr

def hypothesis_testing(group1, group2):
    """Perform t-test between two groups."""
    t_stat, p_value = stats.ttest_ind(group1, group2)
    return {
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }

# Perform statistical analysis
corr_matrix, strong_correlations = correlation_analysis(df)
test_result = hypothesis_testing(df[df['cluster'] == 0]['value'], 
                               df[df['cluster'] == 1]['value'])
print(f"Found {len(strong_correlations)} strong correlations")
print(f"T-test p-value: {test_result['p_value']:.4f}")''',
            
            6: '''# Task 6: Model evaluation and validation
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

def train_model(X, y):
    """Train and evaluate a machine learning model."""
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5)
    
    return {
        'model': model,
        'mse': mse,
        'r2': r2,
        'cv_scores': cv_scores,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std()
    }

# Prepare features and target
X = df_processed.drop(['cluster'], axis=1)
y = df['value']

# Train and evaluate model
results = train_model(X, y)
print(f"Model R² Score: {results['r2']:.4f}")
print(f"Cross-validation Score: {results['cv_mean']:.4f} ± {results['cv_std']:.4f}")''',
            
            7: '''# Task 7: Comprehensive reporting and conclusions
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

def generate_comprehensive_report(df, model_results, output_file='analysis_report.pdf'):
    """Generate comprehensive analysis report."""
    
    with PdfPages(output_file) as pdf:
        # Page 1: Data Overview
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Data Analysis Overview', fontsize=16)
        
        # Distribution plot
        axes[0,0].hist(df['value'], bins=20, alpha=0.7)
        axes[0,0].set_title('Value Distribution')
        
        # Correlation heatmap
        numerical_df = df.select_dtypes(include=[np.number])
        sns.heatmap(numerical_df.corr(), ax=axes[0,1], annot=True, cmap='coolwarm')
        axes[0,1].set_title('Correlation Matrix')
        
        # Cluster visualization
        axes[1,0].scatter(df['x'], df['y'], c=df['cluster'], cmap='viridis')
        axes[1,0].set_title('Clustering Results')
        
        # Model performance
        cv_scores = model_results['cv_scores']
        axes[1,1].bar(range(len(cv_scores)), cv_scores)
        axes[1,1].set_title('Cross-validation Scores')
        axes[1,1].axhline(y=cv_scores.mean(), color='r', linestyle='--')
        
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()
    
    # Summary statistics
    summary = {
        'total_samples': len(df),
        'clusters_found': len(df['cluster'].unique()),
        'model_performance': model_results['r2'],
        'significant_correlations': len([c for c in strong_correlations if abs(c['correlation']) > 0.8])
    }
    
    return summary

# Generate final report
summary = generate_comprehensive_report(df, results)
print("Analysis Complete!")
print(f"Summary: {summary}")

# Final conclusions
print("\\n=== CONCLUSIONS ===")
print(f"1. Dataset contains {summary['total_samples']} samples")
print(f"2. Identified {summary['clusters_found']} distinct clusters")
print(f"3. Model achieved R² score of {summary['model_performance']:.3f}")
print(f"4. Found {summary['significant_correlations']} strong correlations")
print("Analysis demonstrates successful data exploration and modeling.")'''
        }
        
        return templates.get(task_num, f"# Task {task_num}: Basic implementation\\nprint('Task {task_num} completed')")
    
    def get_partial_code(self, task_num: int) -> str:
        """Get partial/incomplete code implementation."""
        templates = {
            2: '''# Task 2: Basic data manipulation
import pandas as pd
# TODO: Add numpy import

def load_and_clean_data(file_path):
    """Load CSV file and clean the data."""
    df = pd.read_csv(file_path)
    # TODO: Add data cleaning steps
    return df

# Missing analyze_data function
# df = load_and_clean_data('sample_data.csv')
# print("Data loaded but not analyzed")''',
            
            3: '''# Task 3: Data visualization  
import matplotlib.pyplot as plt
# Missing seaborn import

def create_histogram(data, column):
    """Create basic histogram."""
    plt.hist(data[column])
    plt.title(f'{column} Distribution')
    # Missing labels and formatting
    plt.show()

# Missing scatter plot function
# create_histogram(df, 'value')''',
            
            4: '''# Task 4: Advanced data processing
from sklearn.preprocessing import StandardScaler
# Missing KMeans import

def preprocess_data(df):
    """Basic preprocessing."""
    # Only handles missing values, no scaling
    df_clean = df.fillna(df.mean())
    return df_clean

# Missing clustering implementation
df_processed = preprocess_data(df)
print("Preprocessing complete, but no clustering performed")''',
            
            5: '''# Task 5: Statistical analysis
from scipy import stats
# Missing imports

def correlation_analysis(df):
    """Basic correlation."""
    return df.corr()

# Missing hypothesis testing
corr = correlation_analysis(df)
print("Basic correlation computed")''',
            
            6: '''# Task 6: Model evaluation
from sklearn.model_selection import train_test_split
# Missing other imports

def basic_split(X, y):
    """Just split the data."""
    return train_test_split(X, y, test_size=0.2)

# Missing model training and evaluation
print("Data split but no model trained")''',
            
            7: '''# Task 7: Basic reporting
import matplotlib.pyplot as plt

def basic_plot(df):
    """Create one simple plot."""
    plt.hist(df['value'])
    plt.title('Basic Plot')
    plt.show()

# Missing comprehensive reporting
basic_plot(df)
print("Basic visualization created")'''
        }
        
        return templates.get(task_num, f"# Task {task_num}: Incomplete\\n# TODO: Implement this task")
    
    def get_syntax_error_code(self, task_num: int) -> str:
        """Get code with syntax errors for testing."""
        return self.error_templates.get_syntax_error_code(task_num)
    
    def get_special_chars_code(self, task_num: int) -> str:
        """Get code with special characters for testing."""
        return self.special_templates.get_special_chars_code(task_num)
