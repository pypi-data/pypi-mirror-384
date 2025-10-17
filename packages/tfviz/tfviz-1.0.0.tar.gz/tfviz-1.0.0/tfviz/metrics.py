from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict, deque
import threading
import logging
from .config import TFVizConfig


@dataclass
class MetricValue:
    epoch: int
    step: int
    value: float
    timestamp: float
    
    def __repr__(self) -> str:
        return f"MetricValue(epoch={self.epoch}, step={self.step}, value={self.value:.4f})"


class MetricsTracker:
    def __init__(self, config: TFVizConfig):
        self.config = config
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=config.update_config.max_points))
        self.current_epoch = 0
        self.current_step = 0
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
    def add_metric(self, name: str, value: float, epoch: Optional[int] = None, step: Optional[int] = None) -> None:
        with self.lock:
            if epoch is None:
                epoch = self.current_epoch
            if step is None:
                step = self.current_step
                
            import time
            timestamp = time.time()
            
            metric_value = MetricValue(epoch=epoch, step=step, value=value, timestamp=timestamp)
            self.metrics[name].append(metric_value)
            
            self.logger.debug(f"Added metric {name}: {metric_value}")
    
    def update_epoch(self, epoch: int) -> None:
        with self.lock:
            self.current_epoch = epoch
            self.current_step = 0
    
    def update_step(self, step: int) -> None:
        with self.lock:
            self.current_step = step
    
    def get_metric_values(self, name: str) -> List[MetricValue]:
        with self.lock:
            return list(self.metrics.get(name, []))
    
    def get_metric_names(self) -> List[str]:
        with self.lock:
            return list(self.metrics.keys())
    
    def get_metrics_by_category(self) -> Dict[str, List[str]]:
        with self.lock:
            categorized = defaultdict(list)
            for metric_name in self.metrics.keys():
                category = self.config.get_metric_category(metric_name)
                categorized[category].append(metric_name)
            return dict(categorized)
    
    def get_latest_values(self) -> Dict[str, float]:
        with self.lock:
            latest = {}
            for name, values in self.metrics.items():
                if values:
                    latest[name] = values[-1].value
            return latest
    
    def get_metric_range(self, name: str) -> Optional[tuple]:
        with self.lock:
            values = self.metrics.get(name, [])
            if not values:
                return None
            
            metric_values = [mv.value for mv in values]
            return (min(metric_values), max(metric_values))
    
    def clear_metric(self, name: str) -> None:
        with self.lock:
            if name in self.metrics:
                self.metrics[name].clear()
                self.logger.info(f"Cleared metric: {name}")
    
    def clear_all_metrics(self) -> None:
        with self.lock:
            self.metrics.clear()
            self.logger.info("Cleared all metrics")
    
    def get_metric_statistics(self, name: str) -> Optional[Dict[str, float]]:
        with self.lock:
            values = self.metrics.get(name, [])
            if not values:
                return None
            
            metric_values = [mv.value for mv in values]
            return {
                "count": len(metric_values),
                "mean": sum(metric_values) / len(metric_values),
                "min": min(metric_values),
                "max": max(metric_values),
                "latest": metric_values[-1]
            }
    
    def export_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        with self.lock:
            exported = {}
            for name, values in self.metrics.items():
                exported[name] = [
                    {
                        "epoch": mv.epoch,
                        "step": mv.step,
                        "value": mv.value,
                        "timestamp": mv.timestamp
                    }
                    for mv in values
                ]
            return exported
    
    def import_metrics(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        with self.lock:
            for name, values in data.items():
                self.metrics[name].clear()
                for item in values:
                    metric_value = MetricValue(
                        epoch=item["epoch"],
                        step=item["step"],
                        value=item["value"],
                        timestamp=item["timestamp"]
                    )
                    self.metrics[name].append(metric_value)
            self.logger.info(f"Imported metrics for {len(data)} metric types")
    
    def __repr__(self) -> str:
        with self.lock:
            metric_count = len(self.metrics)
            total_values = sum(len(values) for values in self.metrics.values())
            return f"MetricsTracker(metrics={metric_count}, total_values={total_values})"
