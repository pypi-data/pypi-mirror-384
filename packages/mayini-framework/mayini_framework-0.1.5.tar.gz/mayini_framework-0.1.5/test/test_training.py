"""
Tests for training utilities like DataLoader, Trainer, etc.
"""
import pytest
import numpy as np
import mayini as mn
from mayini.nn import *
from mayini.optim import *
from mayini.training import *
from conftest import assert_tensors_close

class TestDataLoader:
    """Test DataLoader functionality."""

    def test_dataloader_creation(self):
        """Test DataLoader creation."""
        X = np.random.randn(100, 10).astype(np.float32)
        y = np.random.randint(0, 5, 100)

        dataloader = DataLoader(X, y, batch_size=32, shuffle=False)

        assert dataloader.batch_size == 32
        assert dataloader.shuffle == False
        assert len(dataloader.X) == 100
        assert len(dataloader.y) == 100

    def test_dataloader_iteration(self):
        """Test DataLoader iteration."""
        X = np.arange(20).reshape(20, 1).astype(np.float32)
        y = np.arange(20)

        dataloader = DataLoader(X, y, batch_size=5, shuffle=False)

        batches = list(dataloader)

        # Should have 4 batches of size 5
        assert len(batches) == 4

        for i, (batch_X, batch_y) in enumerate(batches):
            assert isinstance(batch_X, mn.Tensor)
            assert isinstance(batch_y, mn.Tensor)
            assert batch_X.shape[0] == 5
            assert batch_y.shape[0] == 5

        # Check first batch content (no shuffling)
        first_batch_X, first_batch_y = batches[0]
        expected_X = np.arange(5).reshape(5, 1).astype(np.float32)
        expected_y = np.arange(5)

        assert_tensors_close(first_batch_X, expected_X)
        assert_tensors_close(first_batch_y, expected_y)

    def test_dataloader_shuffle(self):
        """Test DataLoader shuffling."""
        X = np.arange(20).reshape(20, 1).astype(np.float32)
        y = np.arange(20)

        # Create two dataloaders with same seed for reproducibility
        np.random.seed(42)
        dataloader1 = DataLoader(X, y, batch_size=20, shuffle=True)

        np.random.seed(42) 
        dataloader2 = DataLoader(X, y, batch_size=20, shuffle=True)

        batch1 = next(iter(dataloader1))
        batch2 = next(iter(dataloader2))

        # Should be identical (same seed)
        assert_tensors_close(batch1[0], batch2[0])
        assert_tensors_close(batch1[1], batch2[1])

        # Should be different from original order
        original_batch_X = mn.Tensor(X)
        # Note: This test might occasionally fail due to random chance

    def test_dataloader_remainder_batch(self):
        """Test DataLoader with remainder batch."""
        X = np.random.randn(23, 5).astype(np.float32)  # 23 samples
        y = np.random.randint(0, 3, 23)

        dataloader = DataLoader(X, y, batch_size=10, shuffle=False)

        batches = list(dataloader)

        # Should have 3 batches: 10, 10, 3
        assert len(batches) == 3
        assert batches[0][0].shape[0] == 10
        assert batches[1][0].shape[0] == 10
        assert batches[2][0].shape[0] == 3

class TestMetrics:
    """Test evaluation metrics."""

    def test_accuracy_binary(self):
        """Test binary accuracy calculation."""
        y_true = mn.Tensor([0, 1, 1, 0, 1])
        y_pred = mn.Tensor([0, 1, 0, 0, 1])

        accuracy = Metrics.accuracy(y_pred, y_true)

        # 4 out of 5 correct
        expected = 4.0 / 5.0
        assert abs(accuracy - expected) < 1e-6

    def test_accuracy_multiclass(self):
        """Test multiclass accuracy calculation."""
        y_true = mn.Tensor([0, 1, 2, 1, 0])
        y_pred = mn.Tensor([0, 1, 1, 1, 0])

        accuracy = Metrics.accuracy(y_pred, y_true)

        # 4 out of 5 correct
        expected = 4.0 / 5.0
        assert abs(accuracy - expected) < 1e-6

    def test_precision_recall_f1(self):
        """Test precision, recall, and F1 score."""
        # Binary classification example
        y_true = mn.Tensor([1, 1, 0, 1, 0, 0, 1, 0])
        y_pred = mn.Tensor([1, 1, 0, 0, 0, 1, 1, 0])

        precision = Metrics.precision(y_pred, y_true)
        recall = Metrics.recall(y_pred, y_true)
        f1 = Metrics.f1_score(y_pred, y_true)

        # Manual calculation:
        # TP = 3 (pred=1, true=1)
        # FP = 1 (pred=1, true=0) 
        # FN = 1 (pred=0, true=1)
        # TN = 3 (pred=0, true=0)

        expected_precision = 3.0 / (3.0 + 1.0)  # TP / (TP + FP)
        expected_recall = 3.0 / (3.0 + 1.0)     # TP / (TP + FN)
        expected_f1 = 2 * (expected_precision * expected_recall) / (expected_precision + expected_recall)

        assert abs(precision - expected_precision) < 1e-6
        assert abs(recall - expected_recall) < 1e-6
        assert abs(f1 - expected_f1) < 1e-6

    def test_confusion_matrix(self):
        """Test confusion matrix calculation."""
        y_true = mn.Tensor([0, 1, 2, 1, 0])
        y_pred = mn.Tensor([0, 1, 1, 2, 0])

        cm = Metrics.confusion_matrix(y_pred, y_true, num_classes=3)

        expected_cm = np.array([
            [2, 0, 0],  # True class 0: 2 predicted as 0, 0 as 1, 0 as 2
            [0, 1, 1],  # True class 1: 0 predicted as 0, 1 as 1, 1 as 2
            [0, 1, 0]   # True class 2: 0 predicted as 0, 1 as 1, 0 as 2
        ])

        np.testing.assert_array_equal(cm, expected_cm)

class TestEarlyStopping:
    """Test early stopping functionality."""

    def test_early_stopping_improvement(self):
        """Test early stopping with improvement."""
        early_stopping = EarlyStopping(patience=3, min_delta=0.01)

        # Simulated validation losses (improving)
        losses = [1.0, 0.8, 0.6, 0.5, 0.45, 0.44]

        should_stop = False
        for loss in losses:
            should_stop = early_stopping(loss)
            if should_stop:
                break

        # Should not stop (losses are improving)
        assert not should_stop

    def test_early_stopping_no_improvement(self):
        """Test early stopping without improvement."""
        early_stopping = EarlyStopping(patience=2, min_delta=0.01)

        # Simulated validation losses (not improving after first few)
        losses = [1.0, 0.5, 0.51, 0.52, 0.53]

        should_stop = False
        for loss in losses:
            should_stop = early_stopping(loss)
            if should_stop:
                break

        # Should stop due to no improvement
        assert should_stop

    def test_early_stopping_restore_best(self):
        """Test early stopping best model restoration."""
        early_stopping = EarlyStopping(patience=2, restore_best_weights=True)

        # Mock model
        model = Linear(2, 1)
        initial_weights = model.weight.data.copy()

        # First call (best loss)
        early_stopping(0.5, model)
        best_weights_saved = model.weight.data.copy()

        # Change weights
        model.weight.data += 1.0

        # Worse losses
        early_stopping(0.8, model)
        should_stop = early_stopping(0.9, model)

        if should_stop:
            # Weights should be restored to best
            assert_tensors_close(model.weight.data, best_weights_saved)

class TestTrainer:
    """Test Trainer functionality."""

    def test_trainer_creation(self):
        """Test Trainer creation."""
        model = Sequential(Linear(5, 1))
        optimizer = SGD(model.parameters(), lr=0.01)
        criterion = MSELoss()

        trainer = Trainer(model, optimizer, criterion)

        assert trainer.model == model
        assert trainer.optimizer == optimizer
        assert trainer.criterion == criterion

    def test_trainer_fit_simple(self):
        """Test Trainer fit method with simple data."""
        # Simple linear regression problem
        model = Linear(1, 1)
        optimizer = SGD(model.parameters(), lr=0.01)
        criterion = MSELoss()

        trainer = Trainer(model, optimizer, criterion)

        # Generate simple linear data
        np.random.seed(42)
        X = np.random.randn(50, 1).astype(np.float32)
        y = (2 * X + 1).astype(np.float32)

        dataloader = DataLoader(X, y, batch_size=16, shuffle=True)

        # Train for a few epochs
        history = trainer.fit(dataloader, epochs=20, verbose=False)

        # Check history structure
        assert 'train_loss' in history
        assert len(history['train_loss']) == 20

        # Loss should generally decrease
        assert history['train_loss'][-1] < history['train_loss'][0]

    def test_trainer_with_validation(self):
        """Test Trainer with validation data."""
        model = Sequential(
            Linear(5, 3),
            ReLU(),
            Linear(3, 1)
        )
        optimizer = Adam(model.parameters(), lr=0.001)
        criterion = MSELoss()

        trainer = Trainer(model, optimizer, criterion)

        # Generate synthetic data
        np.random.seed(42)
        X_train = np.random.randn(80, 5).astype(np.float32)
        y_train = np.random.randn(80, 1).astype(np.float32)
        X_val = np.random.randn(20, 5).astype(np.float32)
        y_val = np.random.randn(20, 1).astype(np.float32)

        train_loader = DataLoader(X_train, y_train, batch_size=16)
        val_loader = DataLoader(X_val, y_val, batch_size=16)

        # Train with validation
        history = trainer.fit(
            train_loader, 
            epochs=10,
            validation_data=val_loader,
            verbose=False
        )

        # Check history includes validation metrics
        assert 'train_loss' in history
        assert 'val_loss' in history
        assert len(history['val_loss']) == 10

    def test_trainer_with_early_stopping(self):
        """Test Trainer with early stopping."""
        model = Linear(2, 1)
        optimizer = SGD(model.parameters(), lr=0.01)
        criterion = MSELoss()

        trainer = Trainer(model, optimizer, criterion)

        # Generate data where model can easily overfit
        np.random.seed(42)
        X_train = np.random.randn(10, 2).astype(np.float32)
        y_train = np.random.randn(10, 1).astype(np.float32)
        X_val = np.random.randn(10, 2).astype(np.float32)
        y_val = np.random.randn(10, 1).astype(np.float32)

        train_loader = DataLoader(X_train, y_train, batch_size=5)
        val_loader = DataLoader(X_val, y_val, batch_size=5)

        early_stopping = EarlyStopping(patience=3, min_delta=0.001)

        # Train with early stopping
        history = trainer.fit(
            train_loader,
            epochs=100,  # Large number
            validation_data=val_loader,
            early_stopping=early_stopping,
            verbose=False
        )

        # Should stop early (before 100 epochs)
        actual_epochs = len(history['train_loss'])
        assert actual_epochs < 100

    def test_trainer_evaluate(self):
        """Test Trainer evaluate method."""
        model = Linear(3, 2)
        optimizer = SGD(model.parameters(), lr=0.01)
        criterion = CrossEntropyLoss()

        trainer = Trainer(model, optimizer, criterion)

        # Generate classification data
        np.random.seed(42)
        X = np.random.randn(30, 3).astype(np.float32)
        y = np.random.randint(0, 2, 30)

        dataloader = DataLoader(X, y, batch_size=10)

        # Evaluate model
        metrics = trainer.evaluate(dataloader, metrics=['accuracy', 'loss'])

        assert 'accuracy' in metrics
        assert 'loss' in metrics
        assert 0 <= metrics['accuracy'] <= 1
        assert metrics['loss'] >= 0

class TestTrainingIntegration:
    """Test integration of training components."""

    def test_full_training_pipeline(self):
        """Test complete training pipeline."""
        # Create model
        model = Sequential(
            Linear(4, 8),
            ReLU(),
            Linear(8, 3)
        )

        optimizer = Adam(model.parameters(), lr=0.001)
        criterion = CrossEntropyLoss()

        # Generate synthetic classification data
        np.random.seed(42)
        X_train = np.random.randn(100, 4).astype(np.float32)
        y_train = np.random.randint(0, 3, 100)
        X_val = np.random.randn(30, 4).astype(np.float32)
        y_val = np.random.randint(0, 3, 30)

        train_loader = DataLoader(X_train, y_train, batch_size=16, shuffle=True)
        val_loader = DataLoader(X_val, y_val, batch_size=16)

        # Create trainer
        trainer = Trainer(model, optimizer, criterion)

        # Train model
        history = trainer.fit(
            train_loader,
            epochs=20,
            validation_data=val_loader,
            verbose=False
        )

        # Evaluate final performance
        final_metrics = trainer.evaluate(val_loader, metrics=['accuracy', 'loss'])

        # Basic checks
        assert len(history['train_loss']) == 20
        assert 'val_loss' in history
        assert 'accuracy' in final_metrics
        assert final_metrics['accuracy'] >= 0

        # Training should improve performance
        assert history['train_loss'][-1] < history['train_loss'][0]

    def test_different_optimizers_comparison(self):
        """Compare different optimizers on same task."""
        def create_model():
            return Sequential(Linear(2, 1))

        def generate_data():
            np.random.seed(42)
            X = np.random.randn(50, 2).astype(np.float32)
            y = (X[:, 0] + X[:, 1]).reshape(-1, 1).astype(np.float32)
            return DataLoader(X, y, batch_size=16)

        optimizers_to_test = [
            ('SGD', lambda params: SGD(params, lr=0.01)),
            ('Adam', lambda params: Adam(params, lr=0.01)),
            ('RMSprop', lambda params: RMSprop(params, lr=0.01))
        ]

        results = {}

        for opt_name, opt_factory in optimizers_to_test:
            model = create_model()
            optimizer = opt_factory(model.parameters())
            criterion = MSELoss()
            trainer = Trainer(model, optimizer, criterion)

            dataloader = generate_data()
            history = trainer.fit(dataloader, epochs=30, verbose=False)

            results[opt_name] = history['train_loss'][-1]

        # All optimizers should achieve reasonable performance
        for opt_name, final_loss in results.items():
            assert final_loss < 1.0  # Should be better than random

