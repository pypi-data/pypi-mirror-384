Null Analysis Module
====================

The ``enahopy.null_analysis`` module provides comprehensive tools for analyzing and handling missing data in ENAHO datasets.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Missing data is common in survey data. This module offers:

- **Pattern detection**: Identify systematic patterns in missing data
- **Impact assessment**: Evaluate how missingness affects analysis
- **Imputation strategies**: Multiple methods from simple to ML-based
- **Quality assessment**: Validate imputation results
- **Visual reporting**: Interactive charts and reports

Main Classes
------------

ENAHONullAnalyzer
^^^^^^^^^^^^^^^^^

Primary class for null value analysis.

.. autoclass:: enahopy.null_analysis.ENAHONullAnalyzer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Example:

   .. code-block:: python

      from enahopy.null_analysis import ENAHONullAnalyzer

      # Create analyzer
      analyzer = ENAHONullAnalyzer(verbose=True)

      # Analyze dataset
      results = analyzer.analyze(
          df=my_dataframe,
          generate_report=True,
          include_visualizations=True
      )

      # View summary
      print(f"Missing: {results['summary']['null_percentage']:.2f}%")
      print(f"Columns with nulls: {results['summary']['columns_with_nulls']}")

      # Get recommendations
      recommendations = analyzer.get_imputation_recommendations(results)
      print(f"Suggested strategy: {recommendations['strategy']}")

Configuration
-------------

NullAnalysisConfig
^^^^^^^^^^^^^^^^^^

Configuration for analysis behavior.

.. autoclass:: enahopy.null_analysis.NullAnalysisConfig
   :members:
   :undoc-members:
   :show-inheritance:

Example:

   .. code-block:: python

      from enahopy.null_analysis import NullAnalysisConfig, AnalysisComplexity

      config = NullAnalysisConfig(
          complexity=AnalysisComplexity.ADVANCED,
          threshold_critical=0.5,
          threshold_moderate=0.2,
          threshold_low=0.05,
          enable_pattern_detection=True,
          enable_visualization=True
      )

      analyzer = ENAHONullAnalyzer(config=config)

AnalysisComplexity
^^^^^^^^^^^^^^^^^^

.. autoclass:: enahopy.null_analysis.AnalysisComplexity
   :members:
   :undoc-members:

- ``BASIC``: Quick summary statistics
- ``INTERMEDIATE``: Include pattern detection
- ``ADVANCED``: Full analysis with correlations
- ``EXPERT``: ML-based analysis and predictions

Pattern Detection
-----------------

PatternDetector
^^^^^^^^^^^^^^^

Detect systematic patterns in missing data.

.. autoclass:: enahopy.null_analysis.PatternDetector
   :members:
   :undoc-members:
   :show-inheritance:

NullPatternAnalyzer
^^^^^^^^^^^^^^^^^^^

Advanced pattern analysis with statistical tests.

.. autoclass:: enahopy.null_analysis.NullPatternAnalyzer
   :members:
   :undoc-members:
   :show-inheritance:

Pattern Types
^^^^^^^^^^^^^

.. autoclass:: enahopy.null_analysis.PatternType
   :members:
   :undoc-members:

- ``MCAR``: Missing Completely At Random
- ``MAR``: Missing At Random
- ``MNAR``: Missing Not At Random
- ``MONOTONE``: Monotone missing pattern
- ``NON_MONOTONE``: Non-monotone pattern

PatternSeverity
^^^^^^^^^^^^^^^

.. autoclass:: enahopy.null_analysis.PatternSeverity
   :members:
   :undoc-members:

Example:

   .. code-block:: python

      from enahopy.null_analysis import PatternDetector

      detector = PatternDetector()
      patterns = detector.detect_patterns(df)

      for pattern in patterns:
          print(f"Pattern: {pattern.pattern_type}")
          print(f"Severity: {pattern.severity}")
          print(f"Affected columns: {pattern.affected_columns}")
          print(f"Recommendation: {pattern.recommendation}")

Imputation Strategies
---------------------

Simple Imputation
^^^^^^^^^^^^^^^^^

Basic imputation methods:

.. autofunction:: enahopy.null_analysis.impute_with_strategy

Strategies:

- ``mean``: Replace with column mean
- ``median``: Replace with column median
- ``mode``: Replace with most frequent value
- ``forward_fill``: Use previous valid value
- ``backward_fill``: Use next valid value
- ``interpolate``: Linear interpolation

Example:

   .. code-block:: python

      from enahopy.null_analysis import impute_with_strategy

      # Simple mean imputation
      df_imputed = impute_with_strategy(
          df=my_df,
          strategy='mean',
          columns=['income', 'expenditure']
      )

ML-Based Imputation
^^^^^^^^^^^^^^^^^^^

MLImputationManager
"""""""""""""""""""

.. autoclass:: enahopy.null_analysis.MLImputationManager
   :members:
   :undoc-members:
   :show-inheritance:

MICEImputer
"""""""""""

Multiple Imputation by Chained Equations.

.. autoclass:: enahopy.null_analysis.MICEImputer
   :members:
   :undoc-members:
   :show-inheritance:

MissForestImputer
"""""""""""""""""

Random forest-based imputation.

.. autoclass:: enahopy.null_analysis.MissForestImputer
   :members:
   :undoc-members:
   :show-inheritance:

AutoencoderImputer
""""""""""""""""""

Neural network-based imputation.

.. autoclass:: enahopy.null_analysis.AutoencoderImputer
   :members:
   :undoc-members:
   :show-inheritance:

Example:

   .. code-block:: python

      from enahopy.null_analysis import create_ml_imputation_manager, ImputationConfig

      # Configure imputation
      config = ImputationConfig(
          method='mice',
          max_iter=10,
          n_nearest_features=5,
          random_state=42
      )

      # Create manager
      manager = create_ml_imputation_manager(config)

      # Impute
      result = manager.impute(df)

      print(f"Imputation quality score: {result.quality_score:.2f}")
      print(f"Convergence: {result.converged}")

ENAHO-Specific Imputation
^^^^^^^^^^^^^^^^^^^^^^^^^^

ENAHOPatternImputer
"""""""""""""""""""

Imputation aware of ENAHO survey structure.

.. autoclass:: enahopy.null_analysis.ENAHOPatternImputer
   :members:
   :undoc-members:
   :show-inheritance:

Features:

- Respects household structure
- Uses geographic stratification
- Handles income variables correctly
- Accounts for survey weights

Example:

   .. code-block:: python

      from enahopy.null_analysis import create_enaho_pattern_imputer, ENAHOImputationConfig

      config = ENAHOImputationConfig(
          use_household_structure=True,
          use_geographic_stratification=True,
          household_id_col='hogar_id',
          ubigeo_col='ubigeo',
          weight_col='factor07'
      )

      imputer = create_enaho_pattern_imputer(config)
      df_imputed = imputer.impute(df)

Quality Assessment
------------------

ImputationQualityAssessor
^^^^^^^^^^^^^^^^^^^^^^^^^^

Evaluate imputation quality.

.. autoclass:: enahopy.null_analysis.ImputationQualityAssessor
   :members:
   :undoc-members:
   :show-inheritance:

QualityMetricType
^^^^^^^^^^^^^^^^^

.. autoclass:: enahopy.null_analysis.QualityMetricType
   :members:
   :undoc-members:

Metrics:

- ``RMSE``: Root Mean Squared Error
- ``MAE``: Mean Absolute Error
- ``R2``: R-squared score
- ``DISTRIBUTION_SIMILARITY``: KS test statistic
- ``CORRELATION_PRESERVATION``: Correlation matrix similarity

Example:

   .. code-block:: python

      from enahopy.null_analysis import assess_imputation_quality, QualityAssessmentConfig

      # Assess quality
      quality = assess_imputation_quality(
          original_df=df_original,
          imputed_df=df_imputed,
          config=QualityAssessmentConfig(
              metrics=['rmse', 'distribution_similarity'],
              confidence_level=0.95
          )
      )

      print(f"Overall quality: {quality.overall_score:.2f}")
      print(f"Metrics: {quality.metric_scores}")

Reporting and Visualization
----------------------------

ReportGenerator
^^^^^^^^^^^^^^^

Generate comprehensive analysis reports.

.. autoclass:: enahopy.null_analysis.ReportGenerator
   :members:
   :undoc-members:
   :show-inheritance:

NullVisualizer
^^^^^^^^^^^^^^

Create visualizations for null patterns.

.. autoclass:: enahopy.null_analysis.NullVisualizer
   :members:
   :undoc-members:
   :show-inheritance:

VisualizationType
^^^^^^^^^^^^^^^^^

.. autoclass:: enahopy.null_analysis.VisualizationType
   :members:
   :undoc-members:

Types:

- ``MATRIX``: Missing data matrix
- ``BAR``: Bar chart of missing percentages
- ``HEATMAP``: Correlation heatmap of missingness
- ``DENDROGRAM``: Hierarchical clustering of patterns
- ``UPSET``: UpSet plot for pattern combinations

Example:

   .. code-block:: python

      from enahopy.null_analysis import NullVisualizer

      visualizer = NullVisualizer()

      # Create visualizations
      fig_matrix = visualizer.visualize_null_matrix(df)
      fig_bars = visualizer.visualize_null_bars(df)
      fig_heatmap = visualizer.visualize_null_heatmap(df)

      # Save
      fig_matrix.savefig('null_matrix.png')

Convenience Functions
---------------------

Quick Analysis
^^^^^^^^^^^^^^

.. autofunction:: enahopy.null_analysis.analyze_null_patterns

.. autofunction:: enahopy.null_analysis.quick_null_analysis

Report Generation
^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.null_analysis.generate_null_report

.. autofunction:: enahopy.null_analysis.generate_comprehensive_null_report

Utilities
^^^^^^^^^

.. autofunction:: enahopy.null_analysis.calculate_null_percentage

.. autofunction:: enahopy.null_analysis.find_columns_with_nulls

.. autofunction:: enahopy.null_analysis.get_null_summary

.. autofunction:: enahopy.null_analysis.get_null_correlation_matrix

.. autofunction:: enahopy.null_analysis.detect_monotone_pattern

.. autofunction:: enahopy.null_analysis.suggest_imputation_methods

.. autofunction:: enahopy.null_analysis.validate_data_completeness

.. autofunction:: enahopy.null_analysis.compare_null_patterns

Exceptions
----------

.. autoexception:: enahopy.null_analysis.NullAnalysisError
   :members:
   :show-inheritance:

Workflow Examples
-----------------

Basic Analysis Workflow
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy.null_analysis import ENAHONullAnalyzer

   # 1. Create analyzer
   analyzer = ENAHONullAnalyzer(verbose=True)

   # 2. Analyze data
   results = analyzer.analyze(df, generate_report=True)

   # 3. Review summary
   summary = results['summary']
   print(f"Missing data: {summary['null_percentage']:.2f}%")

   # 4. Check patterns
   if 'patterns' in results:
       for pattern_type, pattern_data in results['patterns'].items():
           print(f"Pattern {pattern_type}: {pattern_data}")

   # 5. Get recommendations
   recommendations = analyzer.get_imputation_recommendations(results)
   print(f"Recommended: {recommendations['methods']}")

Advanced Imputation Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy.null_analysis import (
       ENAHONullAnalyzer,
       create_ml_imputation_manager,
       assess_imputation_quality,
       ImputationConfig,
       QualityAssessmentConfig
   )

   # 1. Analyze missingness
   analyzer = ENAHONullAnalyzer()
   analysis = analyzer.analyze(df)

   # 2. Choose imputation strategy
   if analysis['summary']['null_percentage'] < 10:
       strategy = 'knn'
   else:
       strategy = 'mice'

   # 3. Configure and impute
   config = ImputationConfig(method=strategy, max_iter=10)
   manager = create_ml_imputation_manager(config)
   result = manager.impute(df)

   # 4. Assess quality
   quality = assess_imputation_quality(
       original_df=df,
       imputed_df=result.imputed_df,
       config=QualityAssessmentConfig()
   )

   # 5. Decide whether to use
   if quality.overall_score > 0.8:
       df_final = result.imputed_df
       print("Imputation successful!")
   else:
       print("Imputation quality insufficient, consider alternatives")

ENAHO-Specific Workflow
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy.null_analysis import (
       ENAHONullAnalyzer,
       create_enaho_pattern_imputer,
       ENAHOImputationConfig
   )

   # 1. Analyze with geographic grouping
   analyzer = ENAHONullAnalyzer()
   analysis = analyzer.analyze_null_patterns(
       df=enaho_df,
       group_by='ubigeo'
   )

   # 2. Check if patterns vary by region
   if 'group_analysis' in analysis:
       print(analysis['group_analysis'])

   # 3. Use ENAHO-aware imputation
   config = ENAHOImputationConfig(
       use_household_structure=True,
       use_geographic_stratification=True,
       household_id_col='conglome',
       ubigeo_col='ubigeo',
       weight_col='factor07'
   )

   imputer = create_enaho_pattern_imputer(config)
   df_imputed = imputer.impute(enaho_df)

   # 4. Generate comprehensive report
   report = analyzer.generate_comprehensive_report(
       df=df_imputed,
       output_path='null_analysis_report.html',
       group_by='ubigeo'
   )

Best Practices
--------------

1. **Always analyze before imputing**:

   .. code-block:: python

      # BAD: Impute immediately
      df_imputed = df.fillna(0)

      # GOOD: Analyze first
      analyzer = ENAHONullAnalyzer()
      results = analyzer.analyze(df)
      # Choose appropriate strategy based on results

2. **Validate imputation quality**:

   .. code-block:: python

      quality = assess_imputation_quality(df_original, df_imputed)
      if quality.overall_score < 0.7:
          warnings.warn("Low imputation quality!")

3. **Document imputation decisions**:

   .. code-block:: python

      report = analyzer.generate_comprehensive_report(
          df=df_imputed,
          output_path='imputation_report.html'
      )

4. **Use domain knowledge**:

   - For income variables: Use ENAHO-specific imputation
   - For geographic variables: Stratify by region
   - For household data: Preserve household structure

5. **Compare multiple methods**:

   .. code-block:: python

      from enahopy.null_analysis import compare_imputation_methods

      comparison = compare_imputation_methods(
          df=df,
          methods=['mean', 'knn', 'mice'],
          test_fraction=0.2
      )

      best_method = comparison['best_method']

Performance Considerations
--------------------------

**For Large Datasets**:

1. Use simpler methods for quick iteration:

   .. code-block:: python

      # Fast
      df_imputed = impute_with_strategy(df, 'median')

      # Slower but better quality
      manager = create_ml_imputation_manager(config)
      result = manager.impute(df)

2. Analyze representative samples:

   .. code-block:: python

      sample_df = df.sample(n=10000, random_state=42)
      results = analyzer.analyze(sample_df)

3. Use chunked processing for ML methods:

   .. code-block:: python

      config = ImputationConfig(
          method='mice',
          chunk_size=10000
      )

See Also
--------

- :doc:`loader`: Load ENAHO data
- :doc:`merger`: Merge modules before analysis
- :doc:`../tutorials/04-missing-data`: Comprehensive tutorial
- :doc:`../troubleshooting`: Common issues and solutions
