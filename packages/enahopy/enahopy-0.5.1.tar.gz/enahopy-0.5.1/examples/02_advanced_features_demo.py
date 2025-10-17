"""
ENAHOPY BUILD Phase 3 - Advanced Features Demo
==============================================

This example demonstrates the advanced features implemented in BUILD Phase 3:
1. ML-based Imputation
2. Statistical Analysis (Poverty indicators, Gini coefficient)
3. Data Quality Assessment
4. Automated Report Generation
"""

import pandas as pd
import numpy as np
import enahopy

def create_sample_enaho_data(n_samples=2000):
    """Create realistic ENAHO-like sample data for demonstration"""
    np.random.seed(42)
    
    # Generate realistic income data (log-normal distribution)
    income = np.random.lognormal(mean=8.5, sigma=1.2, size=n_samples)
    
    # Age distribution
    age = np.concatenate([
        np.random.randint(0, 18, int(n_samples * 0.3)),      # Children
        np.random.randint(18, 65, int(n_samples * 0.6)),     # Working age
        np.random.randint(65, 90, int(n_samples * 0.1))      # Elderly
    ])
    np.random.shuffle(age)
    
    # Education (years of study)
    education = np.random.choice([0, 6, 11, 16, 18], size=n_samples, 
                               p=[0.1, 0.3, 0.4, 0.15, 0.05])
    
    # Geographic and demographic variables
    area = np.random.choice(['Urbano', 'Rural'], size=n_samples, p=[0.7, 0.3])
    gender = np.random.choice(['M', 'F'], size=n_samples, p=[0.5, 0.5])
    region = np.random.choice(['Costa', 'Sierra', 'Selva'], size=n_samples, p=[0.5, 0.3, 0.2])
    
    # Household size
    household_size = np.random.poisson(4, n_samples) + 1
    household_size = np.clip(household_size, 1, 12)
    
    # Create DataFrame
    data = pd.DataFrame({
        'ingreso_hogar': income,
        'edad': age,
        'años_educacion': education,
        'area_geografica': area,
        'sexo': gender,
        'region': region,
        'tamaño_hogar': household_size,
        'gasto_alimentario': income * np.random.uniform(0.2, 0.4, n_samples),
        'acceso_servicios': np.random.choice([0, 1], size=n_samples, p=[0.2, 0.8])
    })
    
    # Introduce realistic missing data patterns
    
    # Income missing for rural areas (data collection challenges)
    rural_mask = data['area_geografica'] == 'Rural'
    missing_income = np.random.choice(rural_mask.sum(), int(rural_mask.sum() * 0.15), replace=False)
    data.loc[data[rural_mask].index[missing_income], 'ingreso_hogar'] = np.nan
    
    # Education missing for elderly (record keeping issues)
    elderly_mask = data['edad'] > 70
    missing_education = np.random.choice(elderly_mask.sum(), int(elderly_mask.sum() * 0.25), replace=False)
    data.loc[data[elderly_mask].index[missing_education], 'años_educacion'] = np.nan
    
    # Random missing in other variables
    for col in ['gasto_alimentario', 'acceso_servicios']:
        n_missing = int(n_samples * np.random.uniform(0.05, 0.1))
        missing_indices = np.random.choice(n_samples, n_missing, replace=False)
        data.loc[missing_indices, col] = np.nan
    
    return data

def demonstrate_ml_imputation(df):
    """Demonstrate ML-based imputation capabilities"""
    print("=" * 60)
    print("🤖 ML-BASED IMPUTATION DEMONSTRATION")
    print("=" * 60)
    
    # Show original missing data
    print("Original missing data summary:")
    print(df.isnull().sum())
    print(f"Total missing values: {df.isnull().sum().sum():,}")
    
    # Create ML imputation manager
    imputation_manager = enahopy.create_ml_imputation_manager()
    
    # Compare different strategies (this might take a moment)
    print("\n🔄 Comparing imputation strategies...")
    try:
        comparison_results = imputation_manager.compare_strategies(df, test_size=0.2)
        
        print("\nStrategy Comparison Results:")
        for strategy, results in comparison_results.items():
            if 'error' not in results:
                avg_performance = np.mean([v for v in results.values() if isinstance(v, (int, float))])
                print(f"  • {strategy}: Average performance = {avg_performance:.3f}")
            else:
                print(f"  • {strategy}: Error - {results['error']}")
        
        # Get best strategy
        best_strategy = imputation_manager.get_best_strategy(comparison_results)
        print(f"\n🏆 Best strategy: {best_strategy}")
        
        # Apply best imputation
        if best_strategy:
            print(f"\n🔧 Applying {best_strategy} imputation...")
            imputed_df = enahopy.quick_ml_imputation(df, strategy=best_strategy)
            
            print("\nAfter imputation:")
            print(imputed_df.isnull().sum())
            print(f"Remaining missing values: {imputed_df.isnull().sum().sum()}")
            
            return imputed_df
    
    except Exception as e:
        print(f"Error in ML imputation: {e}")
        print("Using simple forward-fill as fallback...")
        return df.fillna(method='ffill')
    
    return df

def demonstrate_statistical_analysis(df):
    """Demonstrate poverty and inequality analysis"""
    print("\n" + "=" * 60)
    print("📊 STATISTICAL ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    # Create statistical analyzer
    analyzer = enahopy.create_statistical_analyzer()
    
    # Define poverty line (30th percentile of income distribution)
    poverty_line = df['ingreso_hogar'].quantile(0.3)
    print(f"Poverty line (30th percentile): {poverty_line:,.2f}")
    
    # Comprehensive poverty analysis
    poverty_analysis = enahopy.quick_poverty_analysis(
        df, 'ingreso_hogar', poverty_line, 'area_geografica'
    )
    
    print("\n📈 Poverty Indicators:")
    print(f"  • Headcount Ratio (P0): {poverty_analysis['poverty_headcount']:.1%}")
    print(f"  • Poverty Gap (P1): {poverty_analysis['poverty_gap']:.1%}")
    print(f"  • Poverty Severity (P2): {poverty_analysis['poverty_severity']:.1%}")
    
    print("\n📏 Inequality Measures:")
    print(f"  • Gini Coefficient: {poverty_analysis['gini_coefficient']:.3f}")
    print(f"  • Theil Index: {poverty_analysis['theil_index']:.3f}")
    print(f"  • Palma Ratio: {poverty_analysis['palma_ratio']:.2f}")
    
    print("\n💰 Income Statistics:")
    print(f"  • Mean Income: {poverty_analysis['mean_income']:,.2f}")
    print(f"  • Median Income: {poverty_analysis['median_income']:,.2f}")
    
    # Poverty by groups
    print("\n🌍 Regional Analysis:")
    poverty_calc = analyzer['poverty_indicators']
    
    regional_profile = poverty_calc.poverty_profile(
        df, 'ingreso_hogar', poverty_line, ['region'], 'tamaño_hogar'
    )
    
    for _, row in regional_profile.iterrows():
        print(f"  • {row['group']}: {row['headcount_ratio']:.1%} poverty rate, "
              f"mean income: {row['mean_income']:,.0f}")
    
    return poverty_analysis

def demonstrate_data_quality_assessment(df):
    """Demonstrate comprehensive data quality assessment"""
    print("\n" + "=" * 60)
    print("🔍 DATA QUALITY ASSESSMENT DEMONSTRATION")
    print("=" * 60)
    
    # Perform comprehensive quality assessment
    quality_report = enahopy.assess_data_quality(df)
    
    print(f"📋 Overall Quality Score: {quality_report.overall_score:.1f}/100 (Grade: {quality_report.grade})")
    
    print("\n📊 Quality Dimensions:")
    for name, dimension in quality_report.dimensions.items():
        print(f"  • {dimension.name}: {dimension.score:.1f}/100 (Weight: {dimension.weight:.0%})")
        
        if dimension.issues:
            print(f"    Issues detected: {len(dimension.issues)}")
            for issue in dimension.issues[:2]:  # Show first 2 issues
                print(f"      - {issue}")
    
    print(f"\n🔢 Dataset Information:")
    print(f"  • Records: {quality_report.sample_info['total_records']:,}")
    print(f"  • Columns: {quality_report.sample_info['total_columns']}")
    print(f"  • Memory Usage: {quality_report.sample_info['memory_usage_mb']:.1f} MB")
    
    if quality_report.critical_issues:
        print(f"\n⚠️ Critical Issues ({len(quality_report.critical_issues)}):")
        for issue in quality_report.critical_issues[:3]:  # Top 3 critical issues
            print(f"  • {issue}")
    
    if quality_report.recommendations:
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(quality_report.recommendations[:3], 1):
            print(f"  {i}. {rec}")
    
    return quality_report

def demonstrate_automated_reporting(df):
    """Demonstrate automated report generation"""
    print("\n" + "=" * 60)
    print("📄 AUTOMATED REPORTING DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Generate comprehensive report
        print("🔄 Generating comprehensive ENAHO report...")
        
        poverty_line = df['ingreso_hogar'].quantile(0.3)
        
        report_path = enahopy.generate_enaho_report(
            df,
            output_dir="./reports",
            income_col='ingreso_hogar',
            poverty_line=poverty_line,
            group_col='region',
            export_format='html'
        )
        
        print(f"✅ Report generated: {report_path}")
        
        # Create quick dashboard
        print("\n🚀 Creating interactive dashboard...")
        dashboard_path = enahopy.create_quick_dashboard(df, "reports/dashboard.html")
        print(f"✅ Dashboard created: {dashboard_path}")
        
        return report_path, dashboard_path
        
    except Exception as e:
        print(f"❌ Error in report generation: {e}")
        print("This might be due to missing visualization dependencies (matplotlib/plotly)")
        return None, None

def main():
    """Main demonstration function"""
    print("🚀 ENAHOPY BUILD PHASE 3 - ADVANCED FEATURES DEMONSTRATION")
    print("=" * 70)
    
    # Show component status
    print("\n📊 Component Status:")
    enahopy.show_status(verbose=True)
    
    # Create sample data
    print("\n📁 Creating sample ENAHO-like dataset...")
    df = create_sample_enaho_data(n_samples=1500)
    print(f"Created dataset with {len(df):,} records and {len(df.columns)} variables")
    
    print("\n📋 Dataset Preview:")
    print(df.head())
    print(f"\nDataset Info:")
    print(f"  • Shape: {df.shape}")
    print(f"  • Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    print(f"  • Missing values: {df.isnull().sum().sum():,}")
    
    # Demonstrate each advanced feature
    try:
        # 1. ML-based Imputation
        imputed_df = demonstrate_ml_imputation(df)
        
        # 2. Statistical Analysis
        poverty_results = demonstrate_statistical_analysis(imputed_df)
        
        # 3. Data Quality Assessment
        quality_report = demonstrate_data_quality_assessment(imputed_df)
        
        # 4. Automated Reporting
        report_files = demonstrate_automated_reporting(imputed_df)
        
        print("\n" + "=" * 70)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print("\n📋 Summary of Results:")
        print(f"  • Dataset processed: {len(imputed_df):,} records")
        print(f"  • Data quality score: {quality_report.overall_score:.1f}/100")
        print(f"  • Poverty headcount: {poverty_results['poverty_headcount']:.1%}")
        print(f"  • Income inequality (Gini): {poverty_results['gini_coefficient']:.3f}")
        
        if report_files[0]:
            print(f"  • Reports generated: {report_files[0]}")
        
        print("\n🔥 BUILD Phase 3 features are ready for production use!")
        print("\n💡 Next steps:")
        print("  • Use these features with real ENAHO data")
        print("  • Customize analysis parameters for specific research needs")
        print("  • Generate comprehensive reports for policy analysis")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("Some advanced features might require additional dependencies:")
        print("  • pip install scikit-learn scipy matplotlib plotly jinja2")

if __name__ == "__main__":
    main()