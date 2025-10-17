Convenience Functions
=====================

High-level convenience functions for common workflows. These functions provide simplified interfaces to complex operations.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

ENAHOPY provides convenience functions that:

- Simplify common tasks with sensible defaults
- Combine multiple steps into single function calls
- Provide quick access to core functionality
- Reduce boilerplate code

Quick Start Functions
---------------------

download_enaho_data
^^^^^^^^^^^^^^^^^^^

Simplified data download interface.

.. autofunction:: enahopy.download_enaho_data

Example:

   .. code-block:: python

      from enahopy import download_enaho_data

      # Simple download
      data_dict = download_enaho_data(
          modules=['34', '37'],
          years=[2021, 2022],
          cache_dir='.cache'
      )

      # Access downloaded data
      sumaria_2021 = data_dict['34_2021']

read_enaho_file
^^^^^^^^^^^^^^^

Quick file reading with automatic format detection.

.. autofunction:: enahopy.read_enaho_file

Example:

   .. code-block:: python

      from enahopy import read_enaho_file

      # Read any supported format
      df = read_enaho_file('enaho01-2021-34.dta')

      # Read with options
      df = read_enaho_file(
          'large_file.dta',
          columns=['ubigeo', 'mieperho', 'inghog1d'],
          chunksize=10000
      )

Module Operations
-----------------

merge_enaho_modules
^^^^^^^^^^^^^^^^^^^

Simplified module merging.

.. autofunction:: enahopy.merge_enaho_modules

Example:

   .. code-block:: python

      from enahopy import merge_enaho_modules
      import pandas as pd

      modules = {
          '34': pd.read_stata('sumaria.dta'),
          '37': pd.read_stata('education.dta'),
          '85': pd.read_stata('health.dta')
      }

      # Merge at household level
      merged_df = merge_enaho_modules(
          modules_dict=modules,
          base_module='34',
          level='hogar',
          strategy='coalesce',
          verbose=True
      )

create_panel_data
^^^^^^^^^^^^^^^^^

Quick panel dataset creation.

.. autofunction:: enahopy.create_panel_data

Example:

   .. code-block:: python

      from enahopy import create_panel_data
      import pandas as pd

      # Load data for multiple years
      data = {
          2020: pd.read_stata('enaho-2020-34.dta'),
          2021: pd.read_stata('enaho-2021-34.dta'),
          2022: pd.read_stata('enaho-2022-34.dta')
      }

      # Create balanced panel
      panel_df = create_panel_data(
          data_dict=data,
          id_columns=['conglome', 'vivienda', 'hogar'],
          time_column='anio',
          balanced=True
      )

Geographic Operations
---------------------

merge_with_geography
^^^^^^^^^^^^^^^^^^^^

Simplified geographic data integration.

.. autofunction:: enahopy.merger.merge_with_geography

Example:

   .. code-block:: python

      from enahopy.merger import merge_with_geography
      import pandas as pd

      enaho_df = pd.read_stata('sumaria.dta')
      ubigeo_df = pd.read_excel('ubigeo_data.xlsx')

      # Merge with geography
      result_df, validation = merge_with_geography(
          df_principal=enaho_df,
          df_geografia=ubigeo_df,
          columna_union='ubigeo',
          verbose=True
      )

      # Check validation results
      print(f"Match rate: {validation.match_rate*100:.1f}%")

Null Analysis Operations
-------------------------

analyze_null_patterns
^^^^^^^^^^^^^^^^^^^^^

Quick null pattern analysis.

.. autofunction:: enahopy.analyze_null_patterns

Example:

   .. code-block:: python

      from enahopy import analyze_null_patterns
      import pandas as pd

      df = pd.read_stata('sumaria.dta')

      # Analyze patterns
      results = analyze_null_patterns(df)

      print(f"Missing: {results['summary']['null_percentage']:.2f}%")
      print(f"Columns affected: {results['summary']['columns_with_nulls']}")

generate_null_report
^^^^^^^^^^^^^^^^^^^^

Generate comprehensive null analysis report.

.. autofunction:: enahopy.generate_null_report

Example:

   .. code-block:: python

      from enahopy import generate_null_report

      # Generate HTML report
      report = generate_null_report(
          df=my_dataframe,
          output_path='null_analysis.html',
          format='html',
          include_visualizations=True
      )

Utility Functions
-----------------

get_file_info
^^^^^^^^^^^^^

Get metadata about ENAHO files.

.. autofunction:: enahopy.loader.get_file_info

Example:

   .. code-block:: python

      from enahopy.loader import get_file_info

      info = get_file_info('enaho01-2021-34.dta')

      print(f"Format: {info['format']}")
      print(f"Size: {info['size_mb']:.2f} MB")
      print(f"Rows: {info['n_rows']:,}")
      print(f"Columns: {info['n_cols']}")

find_enaho_files
^^^^^^^^^^^^^^^^

Search for ENAHO files in directories.

.. autofunction:: enahopy.loader.find_enaho_files

Example:

   .. code-block:: python

      from enahopy.loader import find_enaho_files

      # Find all .dta files
      files = find_enaho_files(
          directory='./data',
          pattern='*.dta',
          recursive=True
      )

      print(f"Found {len(files)} files")
      for f in files:
          print(f"  - {f.name}")

get_available_data
^^^^^^^^^^^^^^^^^^

Query available modules and years.

.. autofunction:: enahopy.loader.get_available_data

Example:

   .. code-block:: python

      from enahopy.loader import get_available_data

      available = get_available_data()

      print("Available modules:")
      for code, name in available['modules'].items():
          print(f"  {code}: {name}")

      print(f"\nAvailable years: {available['years']}")

Status and Information
----------------------

show_status
^^^^^^^^^^^

Display library component status.

.. code-block:: python

   from enahopy import show_status

   # Show status
   show_status(verbose=True)

Output:

.. code-block:: text

   enahopy v0.1.2 - Estado de componentes:
   --------------------------------------------------
   [OK] Loader: Disponible
   [OK] Merger: Disponible
   [OK] Null_analysis: Disponible
   [~] Statistical_analysis: Lazy (no cargado aún)
   [~] ML_imputation: Lazy (no cargado aún)

   BUILD Phase Features:
      - Advanced Statistical Analysis: [OK]
      - ML-based Imputation: [OK]
      - Data Quality Assessment: [OK]

   MEASURE Phase Features:
      - Async Downloading: [OK]
      - Memory Optimization: [OK]
      - Streaming Processing: [OK]

get_available_components
^^^^^^^^^^^^^^^^^^^^^^^^

Get programmatic component availability.

.. code-block:: python

   from enahopy import get_available_components

   components = get_available_components()

   if components['loader']:
       print("Loader is available")

   if components['ml_imputation']:
       print("ML imputation is available")

Workflow Helpers
----------------

validate_download_request
^^^^^^^^^^^^^^^^^^^^^^^^^^

Validate download parameters before execution.

.. autofunction:: enahopy.loader.validate_download_request

Example:

   .. code-block:: python

      from enahopy.loader import validate_download_request

      # Validate before downloading
      validation = validate_download_request(
          modules=['01', '34', '37'],
          years=['2020', '2021', '2022'],
          is_panel=False
      )

      if validation['status'] == 'valid':
          print(f"Will download {validation['estimated_downloads']} files")
      else:
          print(f"Error: {validation['error']}")

detect_geographic_columns
^^^^^^^^^^^^^^^^^^^^^^^^^^

Automatically detect geographic columns.

.. autofunction:: enahopy.merger.detect_geographic_columns

Example:

   .. code-block:: python

      from enahopy.merger import detect_geographic_columns

      geo_cols = detect_geographic_columns(
          df=my_dataframe,
          confianza_minima=0.8,
          verbose=True
      )

      print("Detected geographic columns:")
      for col, confidence in geo_cols.items():
          print(f"  {col}: {confidence*100:.0f}% confidence")

validate_module_compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check if modules can be merged.

.. autofunction:: enahopy.merger.validate_module_compatibility

Example:

   .. code-block:: python

      from enahopy.merger import validate_module_compatibility

      modules = {
          '34': sumaria_df,
          '37': education_df,
          '85': health_df
      }

      compat = validate_module_compatibility(
          modules_dict=modules,
          level='hogar',
          verbose=True
      )

      if compat['overall_compatible']:
          print("Modules are compatible!")
      else:
          print("Issues found:")
          for issue in compat['potential_issues']:
              print(f"  - {issue}")

Common Workflows
----------------

Complete Download-Merge-Analyze Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy import (
       ENAHODataDownloader,
       merge_enaho_modules,
       ENAHONullAnalyzer
   )

   # 1. Download data
   downloader = ENAHODataDownloader(verbose=True)
   downloader.download(
       modules=['34', '37'],
       years=['2021'],
       output_dir='./data',
       decompress=True,
       load_dta=True
   )

   # 2. Merge modules
   merged_df = merge_enaho_modules(
       modules_dict={
           '34': sumaria,
           '37': education
       },
       base_module='34',
       level='hogar'
   )

   # 3. Analyze nulls
   analyzer = ENAHONullAnalyzer()
   results = analyzer.analyze(merged_df)

   print(f"Analysis complete! Missing: {results['summary']['null_percentage']:.2f}%")

Quick Poverty Analysis Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy import read_enaho_file, analyze_null_patterns
   from enahopy.merger import extract_ubigeo_components

   # 1. Read data
   df = read_enaho_file('sumaria-2021.dta')

   # 2. Extract geographic components
   df = extract_ubigeo_components(df, columna_ubigeo='ubigeo')

   # 3. Analyze data quality
   null_results = analyze_null_patterns(df)

   # 4. Filter complete cases for analysis
   threshold = 5.0  # 5% missing threshold
   if null_results['summary']['null_percentage'] < threshold:
       df_clean = df.dropna()
       print("Data ready for analysis!")
   else:
       print(f"High missingness: {null_results['summary']['null_percentage']:.2f}%")
       print("Consider imputation")

Geographic Analysis Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy import read_enaho_file
   from enahopy.merger import (
       merge_with_geography,
       validate_ubigeo_data,
       detect_geographic_columns
   )

   # 1. Load datasets
   enaho_df = read_enaho_file('sumaria.dta')
   ubigeo_df = read_enaho_file('ubigeo_2022.xlsx')

   # 2. Detect geographic columns
   geo_cols = detect_geographic_columns(ubigeo_df)
   print(f"Found geographic columns: {list(geo_cols.keys())}")

   # 3. Validate UBIGEO codes
   validation = validate_ubigeo_data(enaho_df, columna_ubigeo='ubigeo')
   print(f"Valid codes: {validation.valid_count}/{validation.total_count}")

   # 4. Merge
   if validation.is_valid:
       merged_df, result = merge_with_geography(
           df_principal=enaho_df,
           df_geografia=ubigeo_df,
           columna_union='ubigeo'
       )
       print(f"Merge complete! Rows: {len(merged_df):,}")

Best Practices
--------------

1. **Use convenience functions for prototyping**:

   .. code-block:: python

      # Quick prototype
      from enahopy import download_enaho_data, merge_enaho_modules

      data = download_enaho_data(['34', '37'], [2021])
      merged = merge_enaho_modules(data, base_module='34')

2. **Switch to classes for production code**:

   .. code-block:: python

      # Production code with full control
      from enahopy.loader import ENAHODataDownloader
      from enahopy.merger import ENAHOGeoMerger, ModuleMergeConfig

      downloader = ENAHODataDownloader(config=custom_config)
      merger = ENAHOGeoMerger(module_config=merge_config)

3. **Validate before processing**:

   .. code-block:: python

      from enahopy.loader import validate_download_request
      from enahopy.merger import validate_module_compatibility

      # Validate download
      val = validate_download_request(modules, years)
      if val['status'] != 'valid':
          raise ValueError(val['error'])

      # Validate merge
      compat = validate_module_compatibility(modules_dict, level)
      if not compat['overall_compatible']:
          raise ValueError("Modules incompatible")

4. **Check component availability**:

   .. code-block:: python

      from enahopy import get_available_components

      components = get_available_components()

      if not components['ml_imputation']:
          print("Install ML dependencies: pip install enahopy[full]")

See Also
--------

- :doc:`loader`: Full loader module documentation
- :doc:`merger`: Full merger module documentation
- :doc:`null_analysis`: Full null analysis documentation
- :doc:`../tutorials/index`: Step-by-step tutorials
