import os
import json
import glob
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

def load_experiment_data(experiment_name):
    """Load and process metrics for a single experiment."""
    metrics_path = f'metrics/{experiment_name}/'
    
    # Load metrics files
    training_metrics = [json.load(open(os.path.join(metrics_path, f))) 
                       for f in sorted(os.listdir(metrics_path)) 
                       if f.startswith("train_") and f.endswith(".json")]
    validation_metrics = [json.load(open(os.path.join(metrics_path, f))) 
                         for f in sorted(os.listdir(metrics_path))
                         if f.startswith("val_") and f.endswith(".json")]
    
    num_classes = training_metrics[0]['num_classes']
    
    # Process into DataFrames (using your existing processing code)
    training_df = pd.DataFrame([
        {
            'step': m['step'],
            'epoch': m['epoch'],
            'epoch_steps': m['total'],
            'accuracy': m['true_positives'] / m['total'] if m['total'] > 0 else 0,
            'experiment': experiment_name,
            **{f'class_{k}_acc': m[str(k)]['true_positives']/m[str(k)]['total'] 
               if m[str(k)]['total'] > 0 else 0 
               for k in range(num_classes)}
        }
        for m in training_metrics
    ])
    
    validation_df = pd.DataFrame([
        {
            'step': m['step'],
            'epoch': m['epoch'],
            'epoch_steps': m['total'],
            'accuracy': m['true_positives'] / m['total'] if m['total'] > 0 else 0,
            'experiment': experiment_name,
            **{f'class_{k}_acc': m[str(k)]['true_positives']/m[str(k)]['total'] 
               if m[str(k)]['total'] > 0 else 0 
               for k in range(num_classes)}
        }
        for m in validation_metrics
    ])
    
    return training_df, validation_df, num_classes

def plot_comparison_dashboard(experiment_names, friendly_names=None):
    """Create a comprehensive comparison dashboard."""
    if friendly_names is None:
        friendly_names = experiment_names
    
    name_mapping = dict(zip(experiment_names, friendly_names))
    
    # Load all experiment data
    all_training = []
    all_validation = []
    num_classes_per_exp = {}
    
    for exp_name in experiment_names:
        train_df, val_df, num_classes = load_experiment_data(exp_name)
        all_training.append(train_df)
        all_validation.append(val_df)
        num_classes_per_exp[exp_name] = num_classes
    
    # Combine all data
    combined_training = pd.concat(all_training, ignore_index=True)
    combined_validation = pd.concat(all_validation, ignore_index=True)
    
    # Set style for cleaner plots
    plt.style.use('seaborn-whitegrid')
    
    # Create the dashboard
    fig = plt.figure(figsize=(12, 10))
    gs = GridSpec(2, 2, figure=fig)
    
    # 1. Overall Training Progress (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    for exp_name in experiment_names:
        exp_data = combined_training[combined_training['experiment'] == exp_name]
        sns.lineplot(data=exp_data, x='epoch', y='accuracy', 
                    label=name_mapping[exp_name], marker='o')
    
    ax1.set_title('Training Accuracy', fontsize=14, pad=10)
    ax1.set_xlabel('Epoch', fontsize=12)
    ax1.set_ylabel('Accuracy', fontsize=12)
    ax1.grid(True, alpha=0.2)
    ax1.set_ylim(0, 1.0)
    ax1.legend(frameon=True, facecolor='white', framealpha=1)
    
    # 2. Final Performance Comparison (top right)
    ax2 = fig.add_subplot(gs[0, 1])
    final_metrics = []
    
    for exp_name in experiment_names:
        exp_val_data = combined_validation[combined_validation['experiment'] == exp_name]
        final_metrics.append({
            'experiment': name_mapping[exp_name],
            'Final Train': combined_training[combined_training['experiment'] == exp_name]['accuracy'].iloc[-1],
            'Final Val': exp_val_data['accuracy'].iloc[-1],
            'Best Val': exp_val_data['accuracy'].max()
        })
    
    final_df = pd.DataFrame(final_metrics)
    final_df_melted = pd.melt(final_df, 
                             id_vars=['experiment'], 
                             var_name='Metric',
                             value_name='Accuracy')
    
    sns.barplot(data=final_df_melted, x='experiment', y='Accuracy', hue='Metric', ax=ax2)
    ax2.set_title('Final Performance', fontsize=14, pad=10)
    # ax2.set_xticklabels(ax2.get_xticklabels(), rotation=30, ha='right')
    ax2.set_ylim(0, 1.0)
    ax2.grid(True, alpha=0.2)
    ax2.legend(frameon=True, facecolor='white', framealpha=1)
    
    # 3. Per-Class Performance Heatmap (bottom left)
    ax3 = fig.add_subplot(gs[1, 0])
    
    class_columns = [col for col in combined_validation.columns if col.startswith('class_')]
    final_class_accuracies = []
    
    for exp_name in experiment_names:
        exp_data = combined_validation[combined_validation['experiment'] == exp_name]
        final_row = exp_data.iloc[-1]
        class_accs = [final_row[col] for col in class_columns]
        final_class_accuracies.append(class_accs)
    
    class_acc_matrix = np.array(final_class_accuracies)
    
    sns.heatmap(class_acc_matrix, 
                annot=True, 
                fmt='.2f',
                cmap='RdYlGn',
                xticklabels=[f'Class {i}' for i in range(len(class_columns))],
                yticklabels=friendly_names,
                ax=ax3,
                vmin=0,
                vmax=1,
                cbar_kws={'label': 'Accuracy'})
    
    ax3.set_title('Per-Class Validation Accuracy', fontsize=14, pad=10)
    ax3.set_ylabel('Dataset')
    
    # 4. Learning Dynamics (bottom right)
    ax4 = fig.add_subplot(gs[1, 1])
    
    for exp_name in experiment_names:
        train_data = combined_training[combined_training['experiment'] == exp_name]
        val_data = combined_validation[combined_validation['experiment'] == exp_name]
        
        sns.lineplot(data=train_data, x='epoch', y='accuracy', 
                    label=f'{name_mapping[exp_name]} (train)',
                    alpha=0.3, linestyle='--')
        
        sns.lineplot(data=val_data, x='epoch', y='accuracy',
                    label=f'{name_mapping[exp_name]} (val)',
                    marker='o')
    
    ax4.set_title('Training vs Validation', fontsize=14, pad=10)
    ax4.set_xlabel('Epoch')
    ax4.set_ylabel('Accuracy')
    ax4.grid(True, alpha=0.2)
    ax4.set_ylim(0, 1.0)
    ax4.legend(frameon=True, facecolor='white', framealpha=1)
    
    plt.suptitle('Model Training Analysis', fontsize=16, y=1.02)
    plt.tight_layout()
    
    return fig

# Example usage:
experiment_ids = ['celebA_small_lr', 'tiny_imagenet', 'binary_class']

# Create mapping for friendly names
name_map = {
    'celebA_small_lr': 'CelebA',
    'tiny_imagenet': 'Tiny ImageNet',
    'binary_class': 'Person Detection'
}

friendly_names = [name_map[exp_id] for exp_id in experiment_ids]

fig = plot_comparison_dashboard(experiment_ids, friendly_names)
plt.show()