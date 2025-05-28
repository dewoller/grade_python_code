"""
Code templates for syntax errors and special characters.

This module extends the code template provider with:
- Syntax error examples for each task
- Special character/unicode examples
- International formatting examples

These templates create realistic test scenarios for error handling.
"""

from typing import Dict


class ErrorCodeTemplates:
    """Provides code templates with syntax errors."""
    
    def get_syntax_error_code(self, task_num: int) -> str:
        """Get code with syntax errors for testing."""
        templates = {
            2: '''# Task 2: Data manipulation with syntax errors
import pandas as pd
import numpy as np

def load_and_clean_data(file_path):
    """Load CSV file with syntax error."""
    df = pd.read_csv(file_path
    df = df.dropna()  # Missing closing parenthesis above
    return df

def analyze_data(df)  # Missing colon
    return df.describe()

# Indentation error
df = load_and_clean_data('data.csv')
    results = analyze_data(df)  # Wrong indentation
print(results)''',
            
            3: '''# Task 3: Visualization with errors
import matplotlib.pyplot as plt

def create_plot(data):
    plt.figure(figsize=(10, 6)  # Missing closing parenthesis
    plt.hist(data['value'], bins=20)
    plt.title('Distribution')
    plt.show()

# Undefined variable
create_plot(undefined_df)  # This variable doesn't exist''',
            
            4: '''# Task 4: Processing with errors
from sklearn.preprocessing import StandardScaler

def preprocess_data(df):
    scaler = StandardScaler()
    # Syntax error in list comprehension
    cols = [col for col in df.columns if col.isdigit(]  # Missing closing parenthesis
    scaled_data = scaler.fit_transform(df[cols])
    return scaled_data

df_processed = preprocess_data(df)''',
            
            5: '''# Task 5: Analysis with errors
from scipy import stats

def correlation_test(x, y):
    # Missing import and syntax error
    result = stats.pearsonr(x, y
    return result  # Missing closing parenthesis

# Wrong function call
test_result = correlation_test(df['x'], df['y'])
print(test_result''',  # Missing closing parenthesis
            
            6: '''# Task 6: Model with errors
from sklearn.ensemble import RandomForestRegressor

def train_model(X, y):
    model = RandomForestRegressor(n_estimators=100)
    model.fit(X, y)
    # String concatenation error
    print("Model trained with" + 100 + "estimators")  # Can't concatenate str and int
    return model

model = train_model(X, y)''',
            
            7: '''# Task 7: Reporting with errors
import matplotlib.pyplot as plt

def generate_report():
    # Undefined variables and syntax errors
    plt.figure(figsize=(10, 8)
    plt.subplot(2, 2, 1)
    plt.hist(undefined_data['value'])  # Undefined variable
    
    # Dictionary syntax error
    summary = {
        'count': len(df),
        'mean': df.mean()
        'std': df.std()  # Missing comma
    }
    return summary'''
        }
        
        return templates.get(task_num, f"# Task {task_num}: Syntax error\\nprint('Error example' + 123)  # Type error")


class SpecialCharTemplates:
    """Provides code templates with special characters and unicode."""
    
    def get_special_chars_code(self, task_num: int) -> str:
        """Get code with special characters for testing."""
        templates = {
            2: '''# Task 2: Data manipulation with special characters
import pandas as pd
import numpy as np

def load_data_with_encoding(file_path):
    """Load CSV with special characters: áéíóú, 中文, русский."""
    # Comments with unicode: ★ ♠ ♥ ♦ ♣
    df = pd.read_csv(file_path, encoding='utf-8')
    
    # Column names with special chars
    columns_map = {
        'température': 'temperature',
        'précipitation': 'precipitation', 
        'données_été': 'summer_data'
    }
    df = df.rename(columns=columns_map)
    return df

# String with emojis and special chars
message = "Data loaded successfully! 🎉 Température: 25°C ± 2°C"
print(message)''',
            
            3: '''# Task 3: Visualization with unicode
import matplotlib.pyplot as plt

def create_multilingual_plot(data):
    """Create plot with international labels."""
    plt.figure(figsize=(10, 6))
    plt.hist(data['temperature'], bins=20)
    
    # Unicode characters in labels
    plt.title('Distribution de température (°C) — Été 2024')
    plt.xlabel('Température (°C)')
    plt.ylabel('Fréquence')
    
    # Add text with special characters
    plt.text(0.7, 0.9, 'μ = 23.5°C\\nσ = 4.2°C', 
             transform=plt.gca().transAxes)
    plt.show()

# Test with special characters
print("Graphique créé avec succès! ✓")''',
            
            4: '''# Task 4: Processing with international data
from sklearn.preprocessing import StandardScaler

def process_international_data(df):
    """Process data with international formatting."""
    # Handle European number format (comma as decimal separator)
    for col in ['température', 'précipitation']:
        if col in df.columns:
            # Convert European format to US format
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    
    # Categories in multiple languages
    category_mapping = {
        'été': 'summer',
        'hiver': 'winter',
        'automne': 'autumn',
        'printemps': 'spring'
    }
    
    if 'saison' in df.columns:
        df['season'] = df['saison'].map(category_mapping)
    
    return df

# Status message with unicode
print("Données internationales traitées ✨")''',
            
            5: '''# Task 5: Statistical analysis with unicode
from scipy import stats
import numpy as np

def analyze_with_unicode_output(df):
    """Statistical analysis with unicode symbols."""
    results = {}
    
    for column in df.select_dtypes(include=[np.number]).columns:
        mean_val = df[column].mean()
        std_val = df[column].std()
        
        # Unicode statistical symbols
        results[column] = {
            'μ (mean)': mean_val,
            'σ (std)': std_val,
            'range': f"{df[column].min():.2f} ≤ x ≤ {df[column].max():.2f}"
        }
    
    return results

# Print with mathematical symbols
stats_results = analyze_with_unicode_output(df)
print("Résultats statistiques:")
for col, stats in stats_results.items():
    print(f"  {col}: μ = {stats['μ (mean)']:.2f}, σ = {stats['σ (std)']:.2f}")''',
            
            6: '''# Task 6: Model evaluation with international text
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestRegressor

def evaluate_model_international(X, y):
    """Model evaluation with multilingual output."""
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # Cross-validation with unicode output
    cv_scores = cross_val_score(model, X, y, cv=5)
    
    # Results in multiple languages/formats
    results = {
        'english': f"CV Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}",
        'français': f"Score CV: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}",
        'symbols': f"⚡ Performance: {cv_scores.mean():.3f} (±{cv_scores.std():.3f})"
    }
    
    return model, results

# Evaluation with special characters
model, eval_results = evaluate_model_international(X, y)
print("🎯 Évaluation du modèle terminée!")
for lang, result in eval_results.items():
    print(f"  {lang}: {result}")''',
            
            7: '''# Task 7: International reporting
import matplotlib.pyplot as plt
import numpy as np

def generate_international_report(df, model_results):
    """Generate report with international formatting."""
    
    # Create plots with unicode titles
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Rapport d\'Analyse Complète — Data Science 2024 🎓', fontsize=16)
    
    # Plot 1: Distribution with unicode
    axes[0,0].hist(df['temperature'], bins=20, alpha=0.7, color='skyblue')
    axes[0,0].set_title('Distribution de Température (°C)')
    axes[0,0].set_xlabel('Température (°C)')
    axes[0,0].set_ylabel('Fréquence')
    
    # Add statistical annotations with unicode
    mean_temp = df['temperature'].mean()
    axes[0,0].axvline(mean_temp, color='red', linestyle='--', 
                      label=f'μ = {mean_temp:.1f}°C')
    axes[0,0].legend()
    
    # Summary with international characters
    summary_text = f"""
    📊 Résumé de l'analyse:
    • Échantillons: {len(df):,} données
    • Température moyenne: {mean_temp:.1f}°C
    • Performance du modèle: {model_results.get('r2', 0):.3f}
    • Qualité: {'Excellente ⭐⭐⭐' if model_results.get('r2', 0) > 0.8 else 'Bonne ⭐⭐'}
    """
    
    plt.figtext(0.02, 0.02, summary_text, fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    
    plt.tight_layout()
    plt.show()
    
    return summary_text

# Generate report with special characters
print("🔄 Génération du rapport en cours...")
report = generate_international_report(df, results)
print("✅ Rapport généré avec succès!")'''
        }
        
        return templates.get(task_num, f"# Task {task_num}: Special chars\\nprint('Spéciał cháracters: áéíóú 中文 🎉')")
