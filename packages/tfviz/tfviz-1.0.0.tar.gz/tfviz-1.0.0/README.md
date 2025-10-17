# TFViz

Real-time visualization for TensorFlow training metrics with automatic color coding and professional plotting capabilities.

## Features

- **Real-time plotting** with configurable update frequency
- **Automatic metric categorization** (loss, accuracy, precision, recall, etc.)
- **Thread-safe operations** for async plotting
- **Multiple visualization themes** (dark, light, minimal)
- **TensorFlow Callback integration** for seamless training monitoring
- **Configurable plot styles** (line, scatter, bar, histogram)
- **Export/import capabilities** for metric data
- **Professional API** with type hints and error handling
- **Distinct color coding** for training vs validation metrics

## Quick Start

```python
from tfviz import TFVizCallback

callback = TFVizCallback()
model.fit(X_train, y_train, callbacks=[callback])
```

## Installation

```bash
pip install tfviz
```

## Basic Usage

### Simple Training Visualization

```python
import tensorflow as tf
from tfviz import TFVizCallback

# Load your data
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()

# Create your model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Add TFViz callback
callback = TFVizCallback()

# Train with visualization
model.fit(x_train, y_train, epochs=10, validation_data=(x_test, y_test), callbacks=[callback])
```

### Advanced Configuration

```python
from tfviz import TFVizCallback, TFVizConfig
from tfviz.config import Theme, PlotStyle

# Custom configuration
config = TFVizConfig(
    theme=Theme.DARK,
    plot_config=PlotConfig(style=PlotStyle.LINE),
    update_config=UpdateConfig(frequency=5)
)

callback = TFVizCallback(config=config)
model.fit(X_train, y_train, callbacks=[callback])
```

## Library Structure

```
tfviz/
├── __init__.py          # Main package exports
├── config.py            # Configuration classes and settings
├── metrics.py           # Metrics tracking and management
├── visualizer.py        # Visualization engine and plotting
└── callback.py          # TensorFlow callback integration
```

## Components

### TFVizConfig
Configuration management with themes, plot styles, and update settings.

### MetricsTracker
Thread-safe metrics collection with automatic categorization and statistics.

### VisualizationEngine
Matplotlib-based plotting engine with async capabilities and multiple themes.

### TFVizCallback
TensorFlow callback for automatic metric collection and visualization during training.

## Color Coding

The library automatically assigns distinct colors to different metrics:
- **Training Loss**: Red
- **Validation Loss**: Blue
- **Training Accuracy**: Green
- **Validation Accuracy**: Orange

## Requirements

- Python 3.7+
- TensorFlow 2.x
- Matplotlib
- NumPy

## License

MIT License
