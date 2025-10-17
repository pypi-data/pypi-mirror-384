"""
Advanced ML-Based Missing Data Imputation - ENAHO Demo
=======================================================

Comprehensive demonstration of advanced machine learning imputation methods
for ENAHO survey data including MICE, missForest, Autoencoders, pattern-aware
imputation, and quality assessment.
"""

import sys
import os
import numpy as np
import pandas as pd
import logging

# Add the parent directory to path to import enahopy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_enaho_data_with_missing():
    """Create sample ENAHO data with realistic missing patterns"""
    np.random.seed(42)
    n_samples = 1000
    
    # Create base data
    data = {
        # Demographics
        'vivienda': np.repeat(range(1, 201), 5)[:n_samples],  # Household ID
        'persona': np.tile(range(1, 6), 200)[:n_samples],     # Person ID within household
        'edad': np.random.randint(0, 85, n_samples),
        'sexo': np.random.choice([1, 2], n_samples),          # 1=Male, 2=Female
        'parentesco': np.random.choice([1, 2, 3, 4, 5], n_samples),
        
        # Geographic
        'region': np.random.choice(range(1, 26), n_samples),
        'provincia': np.random.choice(range(1, 196), n_samples),
        'ubigeo': np.random.choice(range(10000, 99999), n_samples),
        
        # Education
        'nivel_educ': np.random.choice([1, 2, 3, 4, 5, 6], n_samples),
        'anios_educ': np.random.randint(0, 20, n_samples),
        
        # Employment
        'ocupacion': np.random.choice(range(1, 1000), n_samples),
        'rama': np.random.choice(range(1, 22), n_samples),
        
        # Income (with realistic skewness)
        'ing_lab': np.random.lognormal(6, 1, n_samples),
        'ing_indep': np.random.lognormal(5, 1.5, n_samples),
        'ing_total': lambda x: x['ing_lab'] + x['ing_indep'],
        
        # Survey weights
        'factor07': np.random.uniform(0.5, 3.0, n_samples)
    }
    
    df = pd.DataFrame(data)
    df['ing_total'] = df['ing_lab'] + df['ing_indep']
    
    # Add realistic missing patterns
    
    # 1. Income reporting patterns (some people refuse to report all income)
    income_refusal = np.random.random(n_samples) < 0.15
    df.loc[income_refusal, ['ing_lab', 'ing_indep', 'ing_total']] = np.nan
    
    # 2. Partial income reporting
    partial_income = np.random.random(n_samples) < 0.08
    df.loc[partial_income & ~income_refusal, 'ing_indep'] = np.nan
    
    # 3. Employment sequence missing (unemployed people)
    unemployed = np.random.random(n_samples) < 0.12
    df.loc[unemployed, ['ocupacion', 'rama']] = np.nan
    
    # 4. Education cascade missing (some people don't report years)
    edu_years_missing = np.random.random(n_samples) < 0.06
    df.loc[edu_years_missing, 'anios_educ'] = np.nan
    
    # 5. Random missingness in other variables
    for col in ['edad', 'provincia']:
        missing_mask = np.random.random(n_samples) < 0.03
        df.loc[missing_mask, col] = np.nan
    
    logger.info(f"Created sample data with shape {df.shape}")
    logger.info(f"Missing value counts:\n{df.isnull().sum()}")
    
    return df


def demo_advanced_ml_imputation():
    """Demonstrate advanced ML-based imputation methods"""
    
    print("=" * 80)
    print("ADVANCED ML-BASED IMPUTATION FOR ENAHO DATA")
    print("=" * 80)
    
    # Create sample data
    print("\n1. Creating sample ENAHO data with missing values...")
    df = create_sample_enaho_data_with_missing()
    
    # Show initial missing data summary
    print(f"\nOriginal data shape: {df.shape}")
    print(f"Total missing values: {df.isnull().sum().sum()}")
    print(f"Missing percentage: {(df.isnull().sum().sum() / df.size) * 100:.2f}%")
    
    try:
        from enahopy.null_analysis import (
            # Check availability
            ML_IMPUTATION_AVAILABLE, ENAHO_PATTERN_AVAILABLE, QUALITY_ASSESSMENT_AVAILABLE,
            
            # Advanced imputation methods
            create_advanced_imputer, compare_imputation_methods,
            ImputationConfig, 
            
            # ENAHO pattern-aware imputation
            create_enaho_pattern_imputer, ENAHOImputationConfig,
            
            # Quality assessment
            assess_imputation_quality, QualityAssessmentConfig
        )
        
        print(f"\nAdvanced imputation availability:")
        print(f"  ML Imputation: {ML_IMPUTATION_AVAILABLE}")
        print(f"  ENAHO Pattern: {ENAHO_PATTERN_AVAILABLE}")
        print(f"  Quality Assessment: {QUALITY_ASSESSMENT_AVAILABLE}")
        
    except ImportError as e:
        print(f"\nError importing advanced imputation: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install scikit-learn scipy matplotlib seaborn")
        print("  pip install tensorflow  # For autoencoder imputation")
        return
    
    # Identify categorical columns for imputation
    categorical_cols = ['sexo', 'parentesco', 'region', 'nivel_educ', 'ocupacion', 'rama']
    
    print(f"\nCategorical columns: {categorical_cols}")
    
    # ================================
    # 2. MICE Imputation
    # ================================
    if ML_IMPUTATION_AVAILABLE:
        print("\n" + "="*60)
        print("2. MICE (Multiple Imputation by Chained Equations)")
        print("="*60)
        
        try:
            # Configure MICE
            mice_config = ImputationConfig(
                method='mice',
                max_iter=10,
                convergence_threshold=1e-3,
                random_state=42
            )
            
            # Create and apply MICE imputer
            mice_imputer = create_advanced_imputer('mice', mice_config, logger)
            mice_result = mice_imputer.fit_transform(
                df,
                categorical_cols=categorical_cols,
                survey_weights=df['factor07']
            )
            
            print(f"MICE completed in {mice_result.computational_time:.2f} seconds")
            print(f"Converged: {mice_result.convergence_info.get('converged', 'Unknown')}")
            print(f"Iterations performed: {mice_result.imputation_diagnostics.get('iterations_performed', 'Unknown')}")
            
            # Show quality metrics
            print("\nMICE Quality Metrics:")
            for metric, value in mice_result.quality_metrics.items():
                if isinstance(value, (int, float)):
                    print(f"  {metric}: {value:.4f}")
            
        except Exception as e:
            logger.error(f"Error with MICE imputation: {e}")
    
    # ================================
    # 3. MissForest Imputation  
    # ================================
    if ML_IMPUTATION_AVAILABLE:
        print("\n" + "="*60)
        print("3. MissForest (Random Forest Imputation)")
        print("="*60)
        
        try:
            # Configure MissForest
            missforest_config = ImputationConfig(
                method='missforest',
                n_estimators=50,
                max_iter=5,
                random_state=42
            )
            
            # Create and apply MissForest imputer
            missforest_imputer = create_advanced_imputer('missforest', missforest_config, logger)
            missforest_result = missforest_imputer.fit_transform(
                df,
                categorical_cols=categorical_cols
            )
            
            print(f"MissForest completed in {missforest_result.computational_time:.2f} seconds")
            print(f"Iterations performed: {missforest_result.imputation_diagnostics.get('iterations_performed', 'Unknown')}")
            
            # Show OOB errors
            oob_errors = missforest_result.imputation_diagnostics.get('oob_errors', {})
            print(f"\nOut-of-Bag Errors:")
            for col, error in list(oob_errors.items())[:5]:  # Show first 5
                if error is not None:
                    print(f"  {col}: {error:.4f}")
            
        except Exception as e:
            logger.error(f"Error with MissForest imputation: {e}")
    
    # ================================
    # 4. Autoencoder Imputation
    # ================================
    if ML_IMPUTATION_AVAILABLE:
        print("\n" + "="*60)
        print("4. Autoencoder (Deep Learning Imputation)")
        print("="*60)
        
        try:
            # Configure Autoencoder
            autoencoder_config = ImputationConfig(
                method='autoencoder',
                random_state=42
            )
            
            # Create and apply Autoencoder imputer  
            autoencoder_imputer = create_advanced_imputer('autoencoder', autoencoder_config, logger)
            autoencoder_result = autoencoder_imputer.fit_transform(
                df,
                categorical_cols=categorical_cols,
                hidden_dims=[64, 32, 16, 32, 64],
                epochs=50,
                batch_size=32
            )
            
            print(f"Autoencoder completed in {autoencoder_result.computational_time:.2f} seconds")
            
            # Show training info
            training_history = autoencoder_result.imputation_diagnostics.get('training_history', {})
            final_loss = autoencoder_result.imputation_diagnostics.get('final_loss')
            if final_loss:
                print(f"Final training loss: {final_loss:.4f}")
                
        except ImportError:
            print("TensorFlow not available. Skipping Autoencoder imputation.")
        except Exception as e:
            logger.error(f"Error with Autoencoder imputation: {e}")
    
    # ================================
    # 5. ENAHO Pattern-Aware Imputation
    # ================================
    if ENAHO_PATTERN_AVAILABLE:
        print("\n" + "="*60)
        print("5. ENAHO Pattern-Aware Imputation")
        print("="*60)
        
        try:
            # Configure ENAHO pattern imputation
            enaho_config = ENAHOImputationConfig(
                method='enaho_pattern_aware',
                household_id_col='vivienda',
                person_id_col='persona',
                weight_col='factor07',
                respect_household_structure=True,
                preserve_income_ratios=True,
                maintain_education_hierarchy=True,
                use_geographic_proximity=True
            )
            
            # Create and apply ENAHO pattern imputer
            enaho_imputer = create_enaho_pattern_imputer(enaho_config)
            enaho_result = enaho_imputer.fit_transform(df)
            
            print(f"ENAHO Pattern Imputation completed in {enaho_result.computational_time:.2f} seconds")
            
            # Show pattern detection results
            missing_patterns = enaho_result.missing_patterns
            print(f"\nDetected Missing Patterns:")
            for pattern_name, pattern_info in missing_patterns.items():
                if isinstance(pattern_info, dict):
                    print(f"  {pattern_name}: {len(pattern_info)} metrics detected")
            
            # Show applied strategies
            strategies_applied = enaho_result.imputation_diagnostics.get('pattern_strategies_applied', [])
            print(f"\nPattern Strategies Applied: {[s for s in strategies_applied if s is not None]}")
            
        except Exception as e:
            logger.error(f"Error with ENAHO pattern imputation: {e}")
    
    # ================================
    # 6. Method Comparison
    # ================================
    if ML_IMPUTATION_AVAILABLE:
        print("\n" + "="*60)
        print("6. Comparing Imputation Methods")
        print("="*60)
        
        try:
            # Create a smaller dataset for comparison (faster)
            comparison_df = df.head(300).copy()  
            
            # Compare multiple methods
            comparison_results = compare_imputation_methods(
                comparison_df,
                methods=['mice', 'missforest'],  # Skip autoencoder for speed
                categorical_cols=categorical_cols,
                test_fraction=0.1
            )
            
            print("\nMethod Comparison Results:")
            for method, results in comparison_results.items():
                if 'error' in results:
                    print(f"  {method}: ERROR - {results['error']}")
                else:
                    print(f"  {method}:")
                    print(f"    Computation time: {results.get('computation_time', 'N/A'):.2f}s")
                    
                    # Show sample metrics
                    metric_count = 0
                    for key, value in results.items():
                        if isinstance(value, (int, float)) and 'accuracy' in key or 'rmse' in key:
                            print(f"    {key}: {value:.4f}")
                            metric_count += 1
                            if metric_count >= 3:  # Limit output
                                break
            
        except Exception as e:
            logger.error(f"Error in method comparison: {e}")
    
    # ================================
    # 7. Quality Assessment
    # ================================
    if QUALITY_ASSESSMENT_AVAILABLE and 'mice_result' in locals():
        print("\n" + "="*60)
        print("7. Comprehensive Quality Assessment")  
        print("="*60)
        
        try:
            # Configure quality assessment
            quality_config = QualityAssessmentConfig(
                metrics_to_compute=[
                    "distribution_preservation", 
                    "correlation_preservation",
                    "outlier_detection"
                ],
                significance_level=0.05,
                cv_folds=3,
                bootstrap_samples=100  # Reduced for demo
            )
            
            # Perform quality assessment on MICE results
            quality_result = assess_imputation_quality(
                original_df=df,
                imputed_df=mice_result.imputed_data,
                categorical_cols=categorical_cols,
                config=quality_config
            )
            
            print(f"Overall Quality Score: {quality_result.overall_score:.3f}")
            print(f"\nMetric Scores:")
            for metric, score in quality_result.metric_scores.items():
                print(f"  {metric}: {score:.3f}")
            
            print(f"\nRecommendations:")
            for i, rec in enumerate(quality_result.recommendations[:3], 1):
                print(f"  {i}. {rec[:100]}...")
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
    
    print("\n" + "="*80)
    print("ADVANCED IMPUTATION DEMO COMPLETED")
    print("="*80)
    
    # Final summary
    total_missing_before = df.isnull().sum().sum()
    print(f"\nSummary:")
    print(f"  Original missing values: {total_missing_before}")
    
    if 'mice_result' in locals():
        mice_missing_after = mice_result.imputed_data.isnull().sum().sum()
        print(f"  MICE missing after: {mice_missing_after}")
    
    if 'missforest_result' in locals():  
        missforest_missing_after = missforest_result.imputed_data.isnull().sum().sum()
        print(f"  MissForest missing after: {missforest_missing_after}")
    
    if 'enaho_result' in locals():
        enaho_missing_after = enaho_result.imputed_data.isnull().sum().sum()
        print(f"  ENAHO Pattern missing after: {enaho_missing_after}")


def demo_usage_patterns():
    """Demonstrate common usage patterns for the imputation system"""
    
    print("\n" + "="*60)
    print("COMMON USAGE PATTERNS")
    print("="*60)
    
    # Create small sample
    df = create_sample_enaho_data_with_missing().head(200)
    
    try:
        from enahopy.null_analysis import (
            ENAHONullAnalyzer, 
            create_advanced_imputer, ImputationConfig,
            ML_IMPUTATION_AVAILABLE
        )
        
        # Pattern 1: Quick analysis with built-in imputation
        print("\n1. Quick Analysis with Built-in Methods:")
        analyzer = ENAHONullAnalyzer()
        basic_results = analyzer.analyze(df, generate_report=False)
        print(f"   Basic analysis completed. Found {len(basic_results['patterns'])} pattern types.")
        
        # Pattern 2: Advanced imputation for specific use case
        if ML_IMPUTATION_AVAILABLE:
            print("\n2. Targeted Advanced Imputation:")
            
            # For income data - use MICE with careful configuration
            income_cols = [col for col in df.columns if 'ing' in col]
            if income_cols:
                print(f"   Imputing income variables: {income_cols}")
                
                # Configure for income imputation
                income_config = ImputationConfig(
                    method='mice',
                    max_iter=5,
                    convergence_threshold=1e-2
                )
                
                # Focus on income columns
                income_df = df[income_cols + ['edad', 'sexo', 'nivel_educ']].copy()
                
                mice_imputer = create_advanced_imputer('mice', income_config)
                income_result = mice_imputer.fit_transform(
                    income_df, 
                    categorical_cols=['sexo', 'nivel_educ']
                )
                
                print(f"   Income imputation completed in {income_result.computational_time:.2f}s")
        
        # Pattern 3: Validation workflow
        print("\n3. Validation-First Workflow:")
        print("   - Always validate constraints after imputation")
        print("   - Check for logical inconsistencies")
        print("   - Assess impact on downstream analyses")
        
    except ImportError as e:
        print(f"Could not demonstrate usage patterns: {e}")


if __name__ == "__main__":
    # Run the comprehensive demo
    demo_advanced_ml_imputation()
    
    # Show usage patterns
    demo_usage_patterns()
    
    print(f"\n{'='*80}")
    print("For more information:")
    print("- Check the documentation in each imputation method")
    print("- Experiment with different configurations")
    print("- Always validate results with domain knowledge")
    print("- Consider multiple imputation for uncertainty quantification")
    print(f"{'='*80}")