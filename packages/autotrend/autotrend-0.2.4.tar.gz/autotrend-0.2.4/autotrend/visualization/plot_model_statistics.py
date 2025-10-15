import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def plot_model_statistics(result, figsize=(14, 8)):
    """
    Plot summary statistics and model characteristics.
    
    4-panel layout:
    - Panel 1: Segment lengths bar chart
    - Panel 2: Model slopes bar chart
    - Panel 3: Points covered per iteration
    - Panel 4: Model parameters table
    
    Args:
        result: LLTResult object from decompose_llt
        figsize: Figure size tuple
        
    Returns:
        matplotlib Figure object
    """
    sns.set(style="whitegrid", context="talk", palette="muted")
    
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle('Model Statistics Summary', fontsize=18, y=0.995)
    
    num_iterations = result.get_num_iterations()
    colors = sns.color_palette("husl", num_iterations)
    
    # Panel 1: Segment Lengths
    ax1 = axes[0, 0]
    segments = result.get_trend_segments()
    segment_lengths = [end - start for start, end, _ in segments]
    iterations = [iteration for _, _, iteration in segments]
    
    bars = ax1.bar(range(len(segment_lengths)), segment_lengths, 
                   color=[colors[it-1] for it in iterations], alpha=0.7)
    ax1.set_title('Trend Segment Lengths', fontsize=14, pad=10)
    ax1.set_xlabel('Segment Index', fontsize=12)
    ax1.set_ylabel('Length', fontsize=12)
    ax1.grid(True, alpha=0.3, axis='y')
    
    for i, (bar, length) in enumerate(zip(bars, segment_lengths)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                f'{length}', ha='center', va='bottom', fontsize=9)
    
    # Panel 2: Model Slopes
    ax2 = axes[0, 1]
    slopes = [model.coef_[0] for model in result.models]
    
    bars = ax2.bar(range(1, num_iterations + 1), slopes, 
                   color=colors, alpha=0.7)
    ax2.set_title('Model Slopes by Iteration', fontsize=14, pad=10)
    ax2.set_xlabel('Iteration', fontsize=12)
    ax2.set_ylabel('Slope', fontsize=12)
    ax2.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax2.grid(True, alpha=0.3, axis='y')
    
    for bar, slope in zip(bars, slopes):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                f'{slope:.4f}', ha='center', 
                va='bottom' if slope >= 0 else 'top', fontsize=9)
    
    # Panel 3: Coverage per Iteration
    ax3 = axes[1, 0]
    coverage = []
    for iteration in range(1, num_iterations + 1):
        count = np.sum(result.trend_marks == iteration)
        coverage.append(count)
    
    bars = ax3.bar(range(1, num_iterations + 1), coverage, 
                   color=colors, alpha=0.7)
    ax3.set_title('Points Covered by Each Iteration', fontsize=14, pad=10)
    ax3.set_xlabel('Iteration', fontsize=12)
    ax3.set_ylabel('Number of Points', fontsize=12)
    ax3.grid(True, alpha=0.3, axis='y')
    
    for bar, count in zip(bars, coverage):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                f'{count}', ha='center', va='bottom', fontsize=9)
    
    # Panel 4: Model Parameters Table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = [['Iteration', 'Slope', 'Intercept', 'Points']]
    for iteration in range(1, num_iterations + 1):
        model = result.models[iteration-1]
        slope = model.coef_[0]
        intercept = model.intercept_
        count = coverage[iteration-1]
        table_data.append([f'{iteration}', f'{slope:.4f}', 
                          f'{intercept:.2f}', f'{count}'])
    
    table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.2, 0.3, 0.3, 0.2])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(4):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    for i in range(1, len(table_data)):
        for j in range(4):
            table[(i, j)].set_facecolor(colors[i-1])
            table[(i, j)].set_alpha(0.3)
    
    ax4.set_title('Model Parameters', fontsize=14, pad=20)
    
    plt.tight_layout()
    sns.despine()
    
    # Don't call plt.show() - let the caller decide
    return fig