import tensorflow as tf
from tensorflow.keras.callbacks import Callback
from typing import Dict, List, Optional, Any
import logging
import threading
from collections import defaultdict

from .config import TFVizConfig
from .metrics import MetricsTracker
from .visualizer import VisualizationEngine


class TFVizCallback(Callback):
    def __init__(self, config: Optional[TFVizConfig] = None, 
                 metrics_tracker: Optional[MetricsTracker] = None,
                 visualizer: Optional[VisualizationEngine] = None,
                 plot_frequency: int = 1,
                 plot_metrics: Optional[List[str]] = None,
                 figure_name: str = "training_metrics"):
        super().__init__()
        
        self.config = config or TFVizConfig()
        self.metrics_tracker = metrics_tracker or MetricsTracker(self.config)
        self.visualizer = visualizer or VisualizationEngine(self.config, self.metrics_tracker)
        
        self.plot_frequency = plot_frequency
        self.plot_metrics = plot_metrics
        self.figure_name = figure_name
        
        self.logger = logging.getLogger(__name__)
        self.lock = threading.RLock()
        
        self.epoch_metrics: Dict[str, float] = {}
        self.batch_metrics: Dict[str, List[float]] = defaultdict(list)
        self.validation_metrics: Dict[str, float] = {}
        
        self._setup_logging()
        self._create_initial_plots()
    
    def _setup_logging(self) -> None:
        logging.basicConfig(level=self.config.log_level)
    
    def _create_initial_plots(self) -> None:
        try:
            self.visualizer.create_figure(self.figure_name)
            self.logger.info(f"Created initial figure: {self.figure_name}")
        except Exception as e:
            self.logger.error(f"Failed to create initial plots: {e}")
    
    def on_train_begin(self, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            self.logger.info("Training started - TFViz callback initialized")
            if logs:
                self.logger.debug(f"Initial logs: {logs}")
    
    def on_train_end(self, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            self.logger.info("Training ended")
            try:
                self.visualizer.save_all_figures()
                self.logger.info("Saved all figures")
            except Exception as e:
                self.logger.error(f"Failed to save figures: {e}")
    
    def on_epoch_begin(self, epoch: int, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            self.metrics_tracker.update_epoch(epoch)
            self.epoch_metrics.clear()
            self.batch_metrics.clear()
            self.validation_metrics.clear()
    
    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            if logs:
                self._process_epoch_logs(epoch, logs)
                self._update_plots_if_needed(epoch)
    
    def on_batch_begin(self, batch: int, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            self.metrics_tracker.update_step(batch)
    
    def on_batch_end(self, batch: int, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            if logs:
                self._process_batch_logs(logs)
    
    def on_test_begin(self, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            self.logger.debug("Validation/testing started")
    
    def on_test_end(self, logs: Optional[Dict[str, float]] = None) -> None:
        with self.lock:
            if logs:
                self._process_validation_logs(logs)
    
    def _process_epoch_logs(self, epoch: int, logs: Dict[str, float]) -> None:
        for metric_name, value in logs.items():
            if isinstance(value, (int, float)):
                self.metrics_tracker.add_metric(metric_name, float(value), epoch=epoch)
                self.epoch_metrics[metric_name] = value
                
                if metric_name.startswith('val_'):
                    self.validation_metrics[metric_name] = value
    
    def _process_batch_logs(self, logs: Dict[str, float]) -> None:
        for metric_name, value in logs.items():
            if isinstance(value, (int, float)):
                self.batch_metrics[metric_name].append(float(value))
    
    def _process_validation_logs(self, logs: Dict[str, float]) -> None:
        for metric_name, value in logs.items():
            if isinstance(value, (int, float)):
                self.validation_metrics[metric_name] = value
    
    def _update_plots_if_needed(self, epoch: int) -> None:
        if epoch % self.plot_frequency == 0:
            try:
                self._update_plots()
            except Exception as e:
                self.logger.error(f"Failed to update plots: {e}")
    
    def _update_plots(self) -> None:
        if self.plot_metrics:
            self._plot_specific_metrics()
        else:
            self._plot_all_metrics()
    
    def _plot_specific_metrics(self) -> None:
        for metric_name in self.plot_metrics:
            if self.metrics_tracker.get_metric_values(metric_name):
                self.visualizer.plot_metric(self.figure_name, metric_name)
    
    def _plot_all_metrics(self) -> None:
        metric_names = self.metrics_tracker.get_metric_names()
        if metric_names:
            self.visualizer.plot_metrics_by_category(self.figure_name)
    
    def add_custom_metric(self, name: str, value: float, epoch: Optional[int] = None) -> None:
        with self.lock:
            self.metrics_tracker.add_metric(name, value, epoch=epoch)
            self.logger.debug(f"Added custom metric: {name} = {value}")
    
    def plot_metric(self, metric_name: str, style: Optional[str] = None) -> None:
        with self.lock:
            try:
                from .config import PlotStyle
                plot_style = PlotStyle(style) if style else None
                self.visualizer.plot_metric(self.figure_name, metric_name, style=plot_style)
            except Exception as e:
                self.logger.error(f"Failed to plot metric {metric_name}: {e}")
    
    def create_custom_figure(self, name: str, subplot_layout: tuple = (1, 1)) -> None:
        with self.lock:
            try:
                self.visualizer.create_figure(name, subplot_layout)
                self.logger.info(f"Created custom figure: {name}")
            except Exception as e:
                self.logger.error(f"Failed to create custom figure {name}: {e}")
    
    def plot_to_custom_figure(self, figure_name: str, metric_name: str, 
                            ax_key: str = "main", style: Optional[str] = None) -> None:
        with self.lock:
            try:
                from .config import PlotStyle
                plot_style = PlotStyle(style) if style else None
                self.visualizer.plot_metric(figure_name, metric_name, ax_key, plot_style)
            except Exception as e:
                self.logger.error(f"Failed to plot {metric_name} to {figure_name}: {e}")
    
    def save_current_plots(self) -> None:
        with self.lock:
            try:
                self.visualizer.save_all_figures()
                self.logger.info("Saved current plots")
            except Exception as e:
                self.logger.error(f"Failed to save plots: {e}")
    
    def get_metric_summary(self) -> Dict[str, Any]:
        with self.lock:
            summary = {}
            for metric_name in self.metrics_tracker.get_metric_names():
                stats = self.metrics_tracker.get_metric_statistics(metric_name)
                if stats:
                    summary[metric_name] = stats
            return summary
    
    def export_training_data(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "metrics": self.metrics_tracker.export_metrics(),
                "config": {
                    "plot_frequency": self.plot_frequency,
                    "figure_name": self.figure_name,
                    "plot_metrics": self.plot_metrics
                },
                "summary": self.get_metric_summary()
            }
    
    def import_training_data(self, data: Dict[str, Any]) -> None:
        with self.lock:
            try:
                if "metrics" in data:
                    self.metrics_tracker.import_metrics(data["metrics"])
                
                if "config" in data:
                    config_data = data["config"]
                    self.plot_frequency = config_data.get("plot_frequency", self.plot_frequency)
                    self.figure_name = config_data.get("figure_name", self.figure_name)
                    self.plot_metrics = config_data.get("plot_metrics", self.plot_metrics)
                
                self.logger.info("Imported training data successfully")
            except Exception as e:
                self.logger.error(f"Failed to import training data: {e}")
    
    def __repr__(self) -> str:
        with self.lock:
            metric_count = len(self.metrics_tracker.get_metric_names())
            return (f"TFVizCallback(figure={self.figure_name}, "
                    f"metrics={metric_count}, "
                    f"frequency={self.plot_frequency})")
