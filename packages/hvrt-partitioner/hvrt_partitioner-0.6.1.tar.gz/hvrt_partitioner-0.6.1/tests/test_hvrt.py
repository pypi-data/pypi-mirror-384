import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split
from src.hvrt.partitioner import HVRTPartitioner
from src.metrics.metrics import full_report
from src.metrics.partition_profiler import PartitionProfiler

def test_partitioning():
    """
    Tests that the HVRTPartitioner creates the correct number of partitions.
    """
    # Create a sample dataset
    X = pd.DataFrame({
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100)
    })

    # Create a partitioner
    partitioner = HVRTPartitioner(max_leaf_nodes=10)

    # Fit the partitioner and get the partitions
    partitions = partitioner.fit_predict(X)

    # Check that the number of unique partitions is less than or equal to the max_leaf_nodes
    assert len(np.unique(partitions)) <= 10

def test_partitioner_multi_output():
    """
    Tests that the HVRTPartitioner works correctly with a multi-output target.
    """
    # Create a sample dataset with continuous and categorical features
    X = pd.DataFrame({
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    })

    # Create a partitioner
    partitioner = HVRTPartitioner(max_leaf_nodes=10)

    # Fit the partitioner and get the partitions
    partitions = partitioner.fit_predict(X)

    # Check that the number of unique partitions is less than or equal to the max_leaf_nodes
    assert len(np.unique(partitions)) <= 10

def test_metrics_report():
    """
    Tests that the full_report function generates a report without errors.
    """
    # Create a sample dataset
    X = pd.DataFrame({
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100)
    })

    # Create a partitioner
    partitioner = HVRTPartitioner(max_leaf_nodes=10, min_variance_reduction=0.0)

    # Fit the partitioner and get the partitions
    partitions = partitioner.fit_predict(X)

    # Generate the full report
    report = full_report(X, partitions)

    # Check that the report is a dictionary and is not empty
    assert isinstance(report, dict)
    assert len(report) > 0

def test_metrics_full_report():
    """
    Tests the full_report function in more detail.
    """
    # Create a sample dataset
    X = pd.DataFrame({
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100)
    })

    # Create a partitioner
    partitioner = HVRTPartitioner(max_leaf_nodes=10, min_variance_reduction=0.0)

    # Fit the partitioner and get the partitions
    partitions = partitioner.fit_predict(X)

    # Generate the full report
    report = full_report(X, partitions)

    # Check that the report has the correct structure
    assert isinstance(report, dict)
    for feature_name, feature_report in report.items():
        assert feature_name in X.columns
        assert hasattr(feature_report, 'variance_report')
        assert hasattr(feature_report, 'span_report')

def test_partition_profiler():
    """
    Tests the PartitionProfiler class.
    """
    # Create a sample dataset
    X = pd.DataFrame({
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100)
    })

    # Create a partitioner
    partitioner = HVRTPartitioner(max_leaf_nodes=10, min_variance_reduction=0.0)

    # Fit the partitioner and get the partitions
    partitions = partitioner.fit_predict(X)

    # Create a PartitionProfiler
    profiler = PartitionProfiler(X, pd.Series(partitions))

    # Run the profiling
    profiler.run_profiling()

    # Check that the summary table is generated
    summary_table = profiler.generate_summary_table()
    assert isinstance(summary_table, pd.DataFrame)
    assert not summary_table.empty

def test_min_variance_reduction_sensitivity():
    """
    Tests that the min_variance_reduction parameter is not too sensitive.
    """
    # Create a sample dataset
    X = pd.DataFrame({
        'feature1': np.random.rand(1000),
        'feature2': np.random.rand(1000)
    })

    # Create a partitioner with a small min_variance_reduction
    partitioner = HVRTPartitioner(min_variance_reduction=0.001)

    # Fit the partitioner and get the partitions
    partitions = partitioner.fit_predict(X)

    # Check that the number of unique partitions is greater than 2
    assert len(np.unique(partitions)) > 2

def test_incompatible_settings_fail():
    """
    Tests that HVRTPartitioner fails when initialized with incompatible settings
    (category_encoding='target' and target_categories=True).
    """
    with pytest.raises(ValueError, match="category_encoding='target' is incompatible with target_categories=True."):
        HVRTPartitioner(category_encoding='target', target_categories=True)

def test_ohe_with_categorical_target():
    """
    Tests that HVRTPartitioner works with OHE and a categorical target.
    """
    X = pd.DataFrame({
        'feature1': np.random.rand(100),
        'category1': np.random.choice(['A', 'B', 'C'], 100)
    })
    y = pd.Series(np.random.choice(['X', 'Y', 'Z'], 100), name='target_cat')

    partitioner = HVRTPartitioner(max_leaf_nodes=10, category_encoding='ohe', target_categories=True)
    partitions = partitioner.fit_predict(X, y)

    assert len(np.unique(partitions)) <= 10
    assert len(np.unique(partitions)) > 1  # Check that more than one partition is created

def test_ohe_with_continuous_target():
    """
    Tests that HVRTPartitioner works with OHE and a continuous target.
    """
    X = pd.DataFrame({
        'feature1': np.random.rand(100),
        'category1': np.random.choice(['A', 'B', 'C'], 100)
    })
    y = pd.Series(np.random.rand(100), name='target_cont')

    partitioner = HVRTPartitioner(max_leaf_nodes=10, category_encoding='ohe', target_categories=False)
    partitions = partitioner.fit_predict(X, y)

    assert len(np.unique(partitions)) <= 10
    assert len(np.unique(partitions)) > 1 # Check that more than one partition is created

def test_classification_workflow():
    """
    Tests a full classification workflow using the partitioner.
    1. Fits on a training set.
    2. Creates a partition-to-class mapping.
    3. Predicts on a test set.
    Ensures no dimension mismatches occur.
    """
    # 1. Create sample classification data
    X = pd.DataFrame({
        'feature1': np.random.rand(1000),
        'feature2': np.random.rand(1000),
        'category1': np.random.choice(['A', 'B', 'C', 'D'], 1000)
    })
    y = pd.Series(np.random.choice(['Class_X', 'Class_Y', 'Class_Z'], 1000), name='target')

    # 2. Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # 3. Fit partitioner on the training data
    partitioner = HVRTPartitioner(max_leaf_nodes=20, category_encoding='ohe', target_categories=True)
    partitioner.fit(X_train, y_train)

    # 4. Get partitions for both sets
    train_partitions = partitioner.get_partitions(X_train)
    test_partitions = partitioner.get_partitions(X_test)

    # 5. Create a "prediction model" from the training partitions
    # Map each partition ID to the majority class in that partition
    partition_to_class_map = y_train.groupby(train_partitions).agg(lambda x: x.mode()[0]).to_dict()

    # 6. "Predict" on the test set using the map
    # Use .get() to handle cases where a partition might not have a mapping (though unlikely here)
    # A default prediction can be the global majority class
    global_majority_class = y_train.mode()[0]
    y_pred = [partition_to_class_map.get(p_id, global_majority_class) for p_id in test_partitions]

    # 7. Verify dimensions
    assert len(y_pred) == len(y_test), "The number of predictions must match the number of test samples."
    assert len(y_pred) == X_test.shape[0], "The number of predictions must match the number of test samples."