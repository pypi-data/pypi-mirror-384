from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging


class PlotStyle(Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HISTOGRAM = "histogram"


class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"
    MINIMAL = "minimal"


@dataclass
class PlotConfig:
    style: PlotStyle = PlotStyle.LINE
    color: Optional[str] = None
    linewidth: float = 2.0
    alpha: float = 0.8
    marker: Optional[str] = None
    markersize: float = 6.0
    grid: bool = True
    legend: bool = True


@dataclass
class LayoutConfig:
    figsize: Tuple[int, int] = (12, 8)
    dpi: int = 100
    tight_layout: bool = True
    subplot_adjust: Optional[Dict[str, float]] = None


@dataclass
class UpdateConfig:
    frequency: int = 1
    max_points: int = 1000
    buffer_size: int = 100
    async_plotting: bool = True


@dataclass
class TFVizConfig:
    theme: Theme = Theme.LIGHT
    plot_config: PlotConfig = field(default_factory=PlotConfig)
    layout_config: LayoutConfig = field(default_factory=LayoutConfig)
    update_config: UpdateConfig = field(default_factory=UpdateConfig)
    
    log_level: int = logging.INFO
    save_plots: bool = False
    save_directory: str = "./tfviz_plots"
    
    metric_categories: Dict[str, List[str]] = field(default_factory=lambda: {
        "loss": ["loss"],
        "val_loss": ["val_loss"],
        "accuracy": ["accuracy", "acc"],
        "val_accuracy": ["val_accuracy", "val_acc"],
        "precision": ["precision"],
        "val_precision": ["val_precision"],
        "recall": ["recall"],
        "val_recall": ["val_recall"],
        "f1": ["f1", "f1_score"],
        "val_f1": ["val_f1", "val_f1_score"],
        "custom": []
    })
    
    plot_colors: Dict[str, str] = field(default_factory=lambda: {
        "loss": "#ff0000",
        "val_loss": "#0000ff",
        "accuracy": "#00ff00",
        "val_accuracy": "#ff8000",
        "precision": "#800080",
        "val_precision": "#ff00ff",
        "recall": "#00ffff",
        "val_recall": "#ffff00",
        "f1": "#008000",
        "val_f1": "#ffc0cb",
        "custom": "#2d3436"
    })
    
    def __post_init__(self):
        if self.update_config.frequency < 1:
            raise ValueError("Update frequency must be at least 1")
        if self.update_config.max_points < 10:
            raise ValueError("Max points must be at least 10")
        if self.update_config.buffer_size < 1:
            raise ValueError("Buffer size must be at least 1")
    
    def get_metric_category(self, metric_name: str) -> str:
        metric_lower = metric_name.lower()
        
        if metric_lower in self.plot_colors:
            return metric_lower
            
        if metric_lower.startswith('val_'):
            val_metric = metric_lower[4:]
            if val_metric in self.plot_colors:
                return metric_lower
                
        for category, patterns in self.metric_categories.items():
            for pattern in patterns:
                if metric_lower == pattern:
                    return category
        return "custom"
    
    def get_metric_color(self, metric_name: str) -> str:
        category = self.get_metric_category(metric_name)
        return self.plot_colors.get(category, self.plot_colors["custom"])
    
    def update_settings(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")
    
    def __repr__(self) -> str:
        return (f"TFVizConfig(theme={self.theme.value}, "
                f"frequency={self.update_config.frequency}, "
                f"max_points={self.update_config.max_points})")
