import json
import os
import numpy as np

class MetricsTracker:
    def __init__(self, num_classes: int, run_name: str, 
                 mode: str = "val", 
                 model: str = "base",
                 track_predictions: bool = False,
                 examples_per_class: int = 100,
                 random_seed: int = 42,
                 ):
        """ Initialize metrics tracker

            Args:
                num_classes: Number of classes in the dataset
                run_name: Path to save metrics to
                mode: Mode of the metrics (train, val, test)
                model: Model name
                track_predictions: Whether to track predictions
                examples_per_class: Number of examples per class to track
        """
        metrics_path = os.path.join("metrics", run_name)
        self.metrics_path = metrics_path
        if not os.path.exists(metrics_path):
            os.makedirs(metrics_path)

        self.run_name = run_name
        self.num_classes = num_classes
        self.examples_per_class = examples_per_class
        self.metrics = {
            "true_positives": 0,
            "total": 0,
            "false_positives": 0,
            **{class_id: {"true_positives": 0, "false_positives": 0, "total": 0} for class_id in range(num_classes)},
            "run_time": 0,
        }
        self.mode = mode
        self.model = model
        self.epoch = 0
        self.step = 0
        self.random_seed = random_seed
        self.track_predictions = track_predictions

        if track_predictions:
            self.predicted_classes = []
            self.true_classes = []
        else:
            self.predicted_classes = None
            self.true_classes = None

    def val_mode(self):
        self.mode = "val"
        self.step = 0
        self.reset_metrics()

    def train_mode(self):
        self.mode = "train"
        self.step = 0
        self.epoch += 1
        self.reset_metrics()

    def update(self, predicted_class: int, true_class: int):
        self.metrics["total"] += 1
        self.metrics[true_class]["total"] += 1
        if predicted_class == true_class:
            self.metrics[true_class]["true_positives"] += 1
            self.metrics["true_positives"] += 1
        else:
            self.metrics[predicted_class]["false_positives"] += 1

        if self.track_predictions:
            self.true_classes.append(true_class)
            self.predicted_classes.append(predicted_class)
        
        self.step += 1

    def reset_metrics(self):
        self.metrics = {
            "true_positives": 0,
            "total": 0,
            "false_positives": 0,
            "run_time": 0,
            **{class_id: {"true_positives": 0, "false_positives": 0, "total": 0} for class_id in range(self.num_classes)},
        }
        self.predicted_classes = []
        self.true_classes = []

    def save_metrics(self):
        model = self.model
        mode = self.mode
        epoch = self.epoch
        step = self.step

        metrics = self.metrics.copy()
        metrics["epoch"] = epoch
        metrics["step"] = step
        metrics["model"] = model
        metrics["mode"] = mode
        metrics["run_name"] = self.run_name
        metrics["random_seed"] = self.random_seed
        metrics["examples_per_class"] = self.examples_per_class
        if self.track_predictions:
            metrics["predicted_classes"] = self.predicted_classes
            metrics["true_classes"] = self.true_classes
        
        save_path = os.path.join(self.metrics_path, f"{mode}_{model}_{epoch}_{step}.json")
        print(f"[{mode}] [{epoch}/{step}] Saving metrics to {save_path}")
        with open(save_path, "w") as f:
            json.dump(metrics, f)

    def get_accuracy(self, class_id=None):
        """Get accuracy overall or for specific class"""
        if class_id is not None:
            metrics = self.metrics[class_id]
            return metrics["true_positives"] / max(metrics["total"], 1)
        
        total_correct = sum(self.metrics[i]["true_positives"] 
                        for i in range(self.num_classes))
        return total_correct / max(self.metrics["total"], 1)

    
    def print_summary(self):
        """Print current metrics summary"""
        print(f"\n[{self.mode}] Epoch {self.epoch}, Step {self.step}")
        print(f"Overall accuracy: {self.get_accuracy():.3f}")
        
        print("\nPer-class metrics:")
        all_class_metrics = [self.metrics[class_id] for class_id in range(self.num_classes)]
        for class_id, class_metrics in enumerate(all_class_metrics):
            acc = self.get_accuracy(class_id)
            print(f"Class {class_id}: {acc:.3f} "
              f"({class_metrics['true_positives']}/{class_metrics['total']} correct)")
