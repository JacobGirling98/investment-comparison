import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Tuple
from src.ports.chart_generator import ChartGenerator

class MatplotlibChartGenerator(ChartGenerator):
    def generate_performance_chart(self, data: Dict[str, Tuple[float, float]], output_path: str):
        """
        data: Dict where key=Name, value=(XIRR, SimpleReturn)
        """
        names = list(data.keys())
        xirr_vals = [v[0] * 100 for v in data.values()]
        simple_vals = [v[1] * 100 for v in data.values()]
        
        x = np.arange(len(names))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        rects1 = ax.bar(x - width/2, xirr_vals, width, label='Annualized (XIRR)', color='#3498db')
        rects2 = ax.bar(x + width/2, simple_vals, width, label='Total Return (Simple)', color='#2ecc71')
        
        ax.set_ylabel('Percentage Return (%)')
        ax.set_title('ISA Performance Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.legend()
        
        ax.axhline(0, color='black', linewidth=0.8)

        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontweight='bold')

        autolabel(rects1)
        autolabel(rects2)

        fig.tight_layout()
        plt.savefig(output_path)
        plt.close()