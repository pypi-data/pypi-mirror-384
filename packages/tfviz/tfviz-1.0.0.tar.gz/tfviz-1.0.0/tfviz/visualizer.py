import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime

from .config import TFVizConfig, Theme, PlotStyle
from .metrics import MetricsTracker, MetricValue


class VisualizationEngine:
    def __init__(self, config: TFVizConfig, metrics_tracker: MetricsTracker):
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.figures: Dict[str, Figure] = {}
        self.axes: Dict[str, Dict[str, Axes]] = {}
        self.plot_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        self._setup_matplotlib()
        self._create_plot_directories()
    
    def _setup_matplotlib(self) -> None:
        plt.ion()
        
        if self.config.theme == Theme.DARK:
            plt.style.use('dark_background')
        elif self.config.theme == Theme.MINIMAL:
            plt.style.use('default')
            mplstyle.use(['seaborn-whitegrid', 'seaborn-pastel'])
        else:
            plt.style.use('default')
    
    def _create_plot_directories(self) -> None:
        if self.config.save_plots:
            os.makedirs(self.config.save_directory, exist_ok=True)
    
    def create_figure(self, name: str, subplot_layout: Tuple[int, int] = (1, 1)) -> None:
        with self.lock:
            if name in self.figures:
                plt.close(self.figures[name])
            
            fig, axes = plt.subplots(
                subplot_layout[0], 
                subplot_layout[1],
                figsize=self.config.layout_config.figsize,
                dpi=self.config.layout_config.dpi
            )
            
            self.figures[name] = fig
            self.axes[name] = {}
            
            if subplot_layout == (1, 1):
                self.axes[name]["main"] = axes
            else:
                for i in range(subplot_layout[0]):
                    for j in range(subplot_layout[1]):
                        key = f"subplot_{i}_{j}"
                        if subplot_layout[0] == 1:
                            self.axes[name][key] = axes[j]
                        elif subplot_layout[1] == 1:
                            self.axes[name][key] = axes[i]
                        else:
                            self.axes[name][key] = axes[i, j]
            
            fig.suptitle(f"TFViz - {name.replace('_', ' ').title()}")
            
            if self.config.layout_config.tight_layout:
                fig.tight_layout()
            
            self.logger.info(f"Created figure: {name}")
    
    def plot_metric(self, figure_name: str, metric_name: str, ax_key: str = "main", 
                   style: Optional[PlotStyle] = None) -> None:
        with self.lock:
            if figure_name not in self.figures:
                self.create_figure(figure_name)
            
            if ax_key not in self.axes[figure_name]:
                raise ValueError(f"Axis key '{ax_key}' not found in figure '{figure_name}'")
            
            ax = self.axes[figure_name][ax_key]
            metric_values = self.metrics_tracker.get_metric_values(metric_name)
            
            if not metric_values:
                self.logger.warning(f"No data for metric: {metric_name}")
                return
            
            epochs = [mv.epoch for mv in metric_values]
            values = [mv.value for mv in metric_values]
            
            plot_style = style or self.config.plot_config.style
            color = self.config.get_metric_color(metric_name)
            
            if plot_style == PlotStyle.LINE:
                ax.plot(epochs, values, 
                       color=color,
                       linewidth=self.config.plot_config.linewidth,
                       alpha=self.config.plot_config.alpha,
                       marker=self.config.plot_config.marker,
                       markersize=self.config.plot_config.markersize,
                       label=metric_name)
            elif plot_style == PlotStyle.SCATTER:
                ax.scatter(epochs, values,
                          color=color,
                          alpha=self.config.plot_config.alpha,
                          s=self.config.plot_config.markersize * 10,
                          label=metric_name)
            elif plot_style == PlotStyle.BAR:
                ax.bar(epochs, values,
                      color=color,
                      alpha=self.config.plot_config.alpha,
                      label=metric_name)
            
            ax.set_xlabel("Epoch")
            ax.set_ylabel("Value")
            ax.set_title(f"{metric_name.replace('_', ' ').title()}")
            
            if self.config.plot_config.grid:
                ax.grid(True, alpha=0.3)
            
            if self.config.plot_config.legend:
                ax.legend()
            
            self._update_figure_layout(figure_name)
    
    def plot_metrics_by_category(self, figure_name: str) -> None:
        with self.lock:
            categorized_metrics = self.metrics_tracker.get_metrics_by_category()
            
            if not categorized_metrics:
                self.logger.warning("No metrics to plot")
                return
            
            num_categories = len(categorized_metrics)
            subplot_layout = self._calculate_subplot_layout(num_categories)
            
            self.create_figure(figure_name, subplot_layout)
            
            for idx, (category, metrics) in enumerate(categorized_metrics.items()):
                ax_key = f"subplot_{idx // subplot_layout[1]}_{idx % subplot_layout[1]}"
                
                if ax_key in self.axes[figure_name]:
                    ax = self.axes[figure_name][ax_key]
                    self._plot_category_on_axis(ax, category, metrics)
            
            self._update_figure_layout(figure_name)
    
    def _plot_category_on_axis(self, ax: Axes, category: str, metrics: List[str]) -> None:
        for metric_name in metrics:
            metric_values = self.metrics_tracker.get_metric_values(metric_name)
            if not metric_values:
                continue
            
            epochs = [mv.epoch for mv in metric_values]
            values = [mv.value for mv in metric_values]
            color = self.config.get_metric_color(metric_name)
            
            ax.plot(epochs, values,
                   color=color,
                   linewidth=self.config.plot_config.linewidth,
                   alpha=self.config.plot_config.alpha,
                   label=metric_name)
        
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Value")
        ax.set_title(f"{category.replace('_', ' ').title()}")
        
        if self.config.plot_config.grid:
            ax.grid(True, alpha=0.3)
        
        if self.config.plot_config.legend:
            ax.legend()
    
    def _calculate_subplot_layout(self, num_plots: int) -> Tuple[int, int]:
        if num_plots <= 1:
            return (1, 1)
        elif num_plots <= 2:
            return (1, 2)
        elif num_plots <= 4:
            return (2, 2)
        elif num_plots <= 6:
            return (2, 3)
        elif num_plots <= 9:
            return (3, 3)
        else:
            rows = int(np.ceil(np.sqrt(num_plots)))
            cols = int(np.ceil(num_plots / rows))
            return (rows, cols)
    
    def _update_figure_layout(self, figure_name: str) -> None:
        fig = self.figures[figure_name]
        
        if self.config.layout_config.tight_layout:
            fig.tight_layout()
        
        if self.config.layout_config.subplot_adjust:
            fig.subplots_adjust(**self.config.layout_config.subplot_adjust)
        
        fig.canvas.draw()
        fig.canvas.flush_events()
    
    def update_plots(self) -> None:
        if self.config.update_config.async_plotting:
            self.executor.submit(self._async_update_plots)
        else:
            self._sync_update_plots()
    
    def _async_update_plots(self) -> None:
        try:
            self._sync_update_plots()
        except Exception as e:
            self.logger.error(f"Error in async plot update: {e}")
    
    def _sync_update_plots(self) -> None:
        with self.lock:
            for figure_name in self.figures:
                self._update_figure_layout(figure_name)
    
    def save_figure(self, figure_name: str, filename: Optional[str] = None) -> None:
        if not self.config.save_plots:
            return
        
        with self.lock:
            if figure_name not in self.figures:
                self.logger.warning(f"Figure '{figure_name}' not found")
                return
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{figure_name}_{timestamp}.png"
            
            filepath = os.path.join(self.config.save_directory, filename)
            self.figures[figure_name].savefig(filepath, dpi=self.config.layout_config.dpi, bbox_inches='tight')
            self.logger.info(f"Saved figure: {filepath}")
    
    def save_all_figures(self) -> None:
        for figure_name in self.figures:
            self.save_figure(figure_name)
    
    def close_figure(self, figure_name: str) -> None:
        with self.lock:
            if figure_name in self.figures:
                plt.close(self.figures[figure_name])
                del self.figures[figure_name]
                del self.axes[figure_name]
                self.logger.info(f"Closed figure: {figure_name}")
    
    def close_all_figures(self) -> None:
        with self.lock:
            for figure_name in list(self.figures.keys()):
                self.close_figure(figure_name)
            plt.close('all')
    
    def get_figure_info(self) -> Dict[str, Any]:
        with self.lock:
            info = {}
            for name, fig in self.figures.items():
                info[name] = {
                    "size": fig.get_size_inches(),
                    "axes_count": len(self.axes[name]),
                    "axes_keys": list(self.axes[name].keys())
                }
            return info
    
    def __del__(self):
        self.close_all_figures()
        self.executor.shutdown(wait=False)
    
    def __repr__(self) -> str:
        with self.lock:
            return f"VisualizationEngine(figures={len(self.figures)}, theme={self.config.theme.value})"
