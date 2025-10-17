Getting Started with ENAHOPY
==============================

Welcome to ENAHOPY! This guide will help you get started with analyzing ENAHO microdata in less than 15 minutes.

What is ENAHOPY?
----------------

ENAHOPY is a Python library designed to simplify working with ENAHO (Encuesta Nacional de Hogares) microdata from Peru's INEI. It provides tools for:

- **Downloading** ENAHO data directly from INEI servers
- **Merging** different ENAHO modules intelligently
- **Analyzing** missing data patterns
- **Processing** large datasets efficiently

Installation
------------

Basic Installation
^^^^^^^^^^^^^^^^^^

Install ENAHOPY using pip:

.. code-block:: bash

   pip install enahopy

This installs the core functionality needed for most tasks.

Full Installation (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For advanced features like machine learning imputation and comprehensive visualizations:

.. code-block:: bash

   pip install enahopy[full]

This includes optional dependencies:

- ``scikit-learn`` - For advanced ML imputation (MICE, MissForest)
- ``seaborn`` - For enhanced visualizations
- ``matplotlib`` - For plotting
- ``scipy`` - For statistical functions

Installation from Source
^^^^^^^^^^^^^^^^^^^^^^^^^

For the latest development version:

.. code-block:: bash

   git clone https://github.com/elpapx/enahopy.git
   cd enahopy
   pip install -e .

Platform-Specific Notes
^^^^^^^^^^^^^^^^^^^^^^^

**Windows**

.. code-block:: bash

   # Using Command Prompt or PowerShell
   pip install enahopy

**macOS/Linux**

.. code-block:: bash

   # May need sudo for system-wide installation
   pip install enahopy

   # Or use a virtual environment (recommended)
   python3 -m venv venv
   source venv/bin/activate
   pip install enahopy

Verify Installation
^^^^^^^^^^^^^^^^^^^

Check that ENAHOPY is installed correctly:

.. code-block:: python

   import enahopy
   print(enahopy.__version__)  # Should print version number (e.g., '0.5.0')

Quick Start: Your First Analysis
---------------------------------

Let's perform a complete analysis in just a few lines of code.

Step 1: Download ENAHO Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy.loader import ENAHODataDownloader, ENAHOConfig

   # Configure the downloader
   config = ENAHOConfig(
       cache_dir='./.enaho_cache',  # Where to cache downloaded files
       cache_ttl_hours=24,           # Cache validity (24 hours)
       timeout=120                    # Download timeout in seconds
   )

   # Initialize downloader
   downloader = ENAHODataDownloader(config=config)

   # Download Sumaria module for 2023
   result = downloader.download(
       modules=['34'],           # Module 34 = Sumaria (calculated variables)
       years=['2023'],
       output_dir='./data',
       decompress=True,
       load_dta=True            # Automatically load .dta files
   )

   # Extract the DataFrame
   df_sumaria = result[('2023', '34')][list(result[('2023', '34')].keys())[0]]
   print(f"Loaded {len(df_sumaria)} households with {len(df_sumaria.columns)} variables")

**Expected Output:**

.. code-block:: text

   Loaded 36,000 households with 580 variables

Step 2: Basic Data Exploration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # View basic statistics
   print(df_sumaria.head())

   # Check for missing values
   missing = df_sumaria.isnull().sum()
   print(f"Variables with missing values: {(missing > 0).sum()}")

   # Summary statistics for expenditure
   if 'gashog2d' in df_sumaria.columns:
       print(f"Average household expenditure: S/. {df_sumaria['gashog2d'].mean():.2f}")

Step 3: Merge Multiple Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy.merger import ENAHOMerger, MergerConfig

   # Download another module (Module 01 - Household characteristics)
   result_hogar = downloader.download(
       modules=['01'],
       years=['2023'],
       output_dir='./data',
       decompress=True,
       load_dta=True
   )

   df_hogar = result_hogar[('2023', '01')][list(result_hogar[('2023', '01')].keys())[0]]

   # Configure merger
   merger_config = MergerConfig(enable_validation=True)
   merger = ENAHOMerger(config=merger_config)

   # Merge datasets
   df_merged = merger.merge(
       left=df_sumaria,
       right=df_hogar,
       on=['conglome', 'vivienda', 'hogar'],  # Primary keys
       how='left',
       validate='one_to_one'
   )

   print(f"Merged dataset: {df_merged.shape}")

Step 4: Analyze Missing Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from enahopy.null_analysis import ENAHONullAnalyzer

   # Create analyzer
   analyzer = ENAHONullAnalyzer()

   # Analyze missing patterns
   results = analyzer.analyze(
       df_merged,
       generate_report=True,
       report_path='./missing_data_report.html'
   )

   # View summary
   print(f"Total missing values: {results['summary']['null_count']:,}")
   print(f"Missing percentage: {results['summary']['null_percentage']:.2f}%")

   # View patterns
   print(f"Detected {len(results['patterns'])} missing data patterns")

**Expected Output:**

.. code-block:: text

   Total missing values: 12,450
   Missing percentage: 2.34%
   Detected 3 missing data patterns

   Report saved to: ./missing_data_report.html

Basic Concepts
--------------

ENAHO Data Structure
^^^^^^^^^^^^^^^^^^^^^

ENAHO data is organized into **modules**, each covering different survey topics:

+--------+----------------------------------------+-------------+
| Module | Description                            | Level       |
+========+========================================+=============+
| 01     | Household & dwelling characteristics   | Household   |
+--------+----------------------------------------+-------------+
| 02     | Household members                      | Individual  |
+--------+----------------------------------------+-------------+
| 03     | Education                              | Individual  |
+--------+----------------------------------------+-------------+
| 04     | Health                                 | Individual  |
+--------+----------------------------------------+-------------+
| 05     | Employment                             | Individual  |
+--------+----------------------------------------+-------------+
| 34     | Sumaria (calculated variables)         | Household   |
+--------+----------------------------------------+-------------+
| 37     | Governance & social programs           | Household   |
+--------+----------------------------------------+-------------+

Primary Keys
^^^^^^^^^^^^

To merge ENAHO modules, you need to understand the hierarchical key structure:

- **conglome** - Cluster identifier
- **vivienda** - Dwelling identifier within cluster
- **hogar** - Household identifier within dwelling
- **codperso** - Person identifier within household (for individual-level data)

**Household-level merge:**

.. code-block:: python

   merger.merge(left, right, on=['conglome', 'vivienda', 'hogar'])

**Individual-level merge:**

.. code-block:: python

   merger.merge(left, right, on=['conglome', 'vivienda', 'hogar', 'codperso'])

Cache System
^^^^^^^^^^^^

ENAHOPY uses an intelligent cache system to avoid re-downloading files:

- Downloaded files are stored in ``cache_dir`` (default: ``./.enaho_cache``)
- Cache entries have a Time-To-Live (TTL) of 24 hours by default
- Cached files are compressed to save ~40% disk space
- Second runs are **significantly faster** (5-10x speedup)

.. code-block:: python

   # First run: downloads from INEI (slow)
   downloader.download(modules=['34'], years=['2023'])

   # Second run: uses cache (fast!)
   downloader.download(modules=['34'], years=['2023'])

Data Types
^^^^^^^^^^

ENAHO data comes in different formats:

- **.dta** - Stata format (most common, includes labels)
- **.sav** - SPSS format (less common)
- **.dbf** - DBase format (older surveys)

ENAHOPY handles all formats automatically when you set ``load_dta=True``.

Common Workflows
----------------

Workflow 1: Poverty Analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # 1. Download sumaria module
   downloader.download(modules=['34'], years=['2023'])

   # 2. Calculate poverty status
   poverty_line = 378  # INEI 2023 poverty line (soles/month per capita)
   df['is_poor'] = df['gashog2d'] < poverty_line

   # 3. Calculate poverty rate
   poverty_rate = df['is_poor'].mean() * 100
   print(f"Poverty rate: {poverty_rate:.1f}%")

Workflow 2: Geographic Analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # 1. Extract department from UBIGEO
   df['departamento'] = df['ubigeo'].str[:2]

   # 2. Calculate statistics by department
   dept_stats = df.groupby('departamento').agg({
       'gashog2d': 'mean',
       'conglome': 'count'
   })

   # 3. Identify poorest departments
   poorest = dept_stats.nsmallest(5, 'gashog2d')
   print(poorest)

Workflow 3: Multi-Year Panel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Download multiple years
   result = downloader.download(
       modules=['34'],
       years=['2021', '2022', '2023'],
       output_dir='./data'
   )

   # Concatenate years
   dfs = []
   for year in ['2021', '2022', '2023']:
       df_year = result[(year, '34')][...]
       df_year['year'] = year
       dfs.append(df_year)

   df_panel = pd.concat(dfs, ignore_index=True)
   print(f"Panel data: {df_panel.shape}")

Common Troubleshooting
----------------------

Import Errors
^^^^^^^^^^^^^

**Problem:** ``ModuleNotFoundError: No module named 'enahopy'``

**Solution:**

.. code-block:: bash

   # Verify installation
   pip list | grep enahopy

   # Reinstall if needed
   pip install --upgrade enahopy

Download Failures
^^^^^^^^^^^^^^^^^

**Problem:** Download times out or fails

**Solutions:**

1. **Increase timeout:**

   .. code-block:: python

      config = ENAHOConfig(timeout=300)  # 5 minutes

2. **Check internet connection**

3. **Try again later** - INEI servers may be temporarily unavailable

4. **Use cache** - If file was partially downloaded, cache may have it

Cache Issues
^^^^^^^^^^^^

**Problem:** Cache consuming too much disk space

**Solution:**

.. code-block:: python

   from enahopy.loader.core.cache import CacheManager

   cache = CacheManager(cache_dir='./.enaho_cache')

   # Clear old entries
   cache.clear_expired()

   # Clear all cache
   cache.clear_all()

Memory Errors
^^^^^^^^^^^^^

**Problem:** ``MemoryError`` when loading large datasets

**Solutions:**

1. **Use chunked reading:**

   .. code-block:: python

      config = ENAHOConfig(chunk_size=10000, optimize_memory=True)

2. **Load only needed columns:**

   .. code-block:: python

      df = pd.read_stata('file.dta', columns=['conglome', 'gashog2d'])

3. **Use categorical dtypes for text columns:**

   .. code-block:: python

      df['departamento'] = df['departamento'].astype('category')

Next Steps
----------

Now that you have the basics, explore these resources:

1. **Tutorials** - Step-by-step guides for common tasks

   - :doc:`tutorials/tutorial_01_data_downloading`
   - :doc:`tutorials/tutorial_02_module_merging`
   - :doc:`tutorials/tutorial_03_geographic_integration`
   - :doc:`tutorials/tutorial_04_missing_data_analysis`
   - :doc:`tutorials/tutorial_05_complete_pipeline`

2. **API Reference** - Detailed documentation for all functions

   - :doc:`api/loader`
   - :doc:`api/merger`
   - :doc:`api/null_analysis`

3. **Troubleshooting** - Solutions to common problems

   - :doc:`troubleshooting`

4. **FAQ** - Frequently asked questions

   - :doc:`faq`

Getting Help
------------

If you encounter issues:

1. **Check the documentation** - Most common questions are answered here
2. **Search existing issues** - `GitHub Issues <https://github.com/elpapx/enahopy/issues>`_
3. **Ask a question** - Open a new issue with the ``question`` label
4. **Community** - Join discussions on GitHub Discussions

Tips for Success
----------------

1. **Always use virtual environments** - Avoid dependency conflicts

   .. code-block:: bash

      python -m venv enahopy-env
      source enahopy-env/bin/activate  # Linux/macOS
      enahopy-env\Scripts\activate     # Windows

2. **Enable caching** - Speeds up development significantly

3. **Start small** - Test your code on a subset before processing all data

4. **Read INEI documentation** - Understand ENAHO methodology and variables

   - `INEI Microdatos <http://iinei.inei.gob.pe/microdatos/>`_
   - `ENAHO Methodology <http://iinei.inei.gob.pe/iinei/srienaho/Descarga/FichaTecnica/2023-632.pdf>`_

5. **Use Jupyter notebooks** - Great for exploratory analysis

6. **Validate your results** - Cross-check with official INEI statistics

Summary
-------

You've learned:

- ✓ How to install ENAHOPY
- ✓ How to download ENAHO data
- ✓ How to merge multiple modules
- ✓ How to analyze missing data
- ✓ Basic ENAHO data structure
- ✓ Common workflows
- ✓ Troubleshooting basics

**Ready for more?** Continue to the :doc:`tutorials/index` for in-depth guides!
