Troubleshooting Guide
=====================

This guide covers common issues and their solutions when using ENAHOPY.

Installation Issues
-------------------

ModuleNotFoundError: No module named 'enahopy'
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** Cannot import enahopy after installation.

**Diagnosis:**

.. code-block:: bash

   # Check if enahopy is installed
   pip list | grep enahopy

**Solutions:**

1. **Verify installation:**

   .. code-block:: bash

      pip install enahopy
      pip show enahopy

2. **Check Python environment:**

   .. code-block:: python

      import sys
      print(sys.executable)  # Verify you're using the right Python

3. **Try reinstalling:**

   .. code-block:: bash

      pip uninstall enahopy
      pip install enahopy --no-cache-dir

4. **Use absolute path import:**

   .. code-block:: python

      import sys
      sys.path.append('/path/to/enahopy')
      import enahopy

Dependency Conflicts
^^^^^^^^^^^^^^^^^^^^

**Problem:** Conflicting package versions.

**Diagnosis:**

.. code-block:: bash

   pip check

**Solution:** Use a virtual environment:

.. code-block:: bash

   # Create virtual environment
   python -m venv enahopy-env

   # Activate (Linux/macOS)
   source enahopy-env/bin/activate

   # Activate (Windows)
   enahopy-env\Scripts\activate

   # Install in isolated environment
   pip install enahopy[full]

Download Failures
-----------------

Timeout Errors
^^^^^^^^^^^^^^

**Problem:** ``TimeoutError`` or ``ReadTimeout`` during download.

**Symptoms:**

.. code-block:: text

   TimeoutError: Download exceeded 120 seconds

**Solutions:**

1. **Increase timeout:**

   .. code-block:: python

      config = ENAHOConfig(timeout=300)  # 5 minutes

2. **Check internet connection:**

   .. code-block:: bash

      ping iinei.inei.gob.pe

3. **Try during off-peak hours** - INEI servers may be overloaded

4. **Enable retry logic** (built-in):

   The downloader automatically retries failed downloads up to 3 times.

Connection Errors
^^^^^^^^^^^^^^^^^

**Problem:** ``ConnectionError`` or ``URLError``.

**Diagnosis:**

- Check if you're behind a proxy/firewall
- Verify INEI servers are accessible

**Solutions:**

1. **Configure proxy:**

   .. code-block:: python

      import os
      os.environ['HTTP_PROXY'] = 'http://proxy.example.com:8080'
      os.environ['HTTPS_PROXY'] = 'http://proxy.example.com:8080'

2. **Use cached data if available:**

   .. code-block:: python

      # Check cache first
      cache = CacheManager(cache_dir='./.enaho_cache')
      analytics = cache.get_analytics()
      print(f"Cached entries: {analytics['total_entries']}")

Invalid Module/Year
^^^^^^^^^^^^^^^^^^^

**Problem:** ``ValueError: Invalid module`` or ``Invalid year``.

**Solution:** Verify valid modules and years:

**Valid modules:** 01-05, 34, 37, and others (see INEI documentation)

**Valid years:** 2004-present (availability varies by module)

.. code-block:: python

   # Always use string format for years
   downloader.download(modules=['34'], years=['2023'])  # Correct
   # downloader.download(modules=['34'], years=[2023])  # Wrong!

Memory Errors
-------------

MemoryError During Load
^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** ``MemoryError`` when loading large datasets.

**Symptoms:**

.. code-block:: text

   MemoryError: Unable to allocate X.XX GiB for an array

**Solutions:**

1. **Enable chunked reading:**

   .. code-block:: python

      config = ENAHOConfig(
          chunk_size=10000,       # Process 10k rows at a time
          optimize_memory=True    # Enable memory optimization
      )

2. **Load only needed columns:**

   .. code-block:: python

      # Instead of loading full file
      df = pd.read_stata('sumaria.dta', columns=['conglome', 'gashog2d', 'inghog2d'])

3. **Use categorical dtypes:**

   .. code-block:: python

      # Convert string columns to categorical
      for col in df.select_dtypes(include='object').columns:
          df[col] = df[col].astype('category')

4. **Process in batches:**

   .. code-block:: python

      # Process data year by year instead of all at once
      for year in ['2021', '2022', '2023']:
          result = downloader.download(modules=['34'], years=[year])
          # Process result
          del result  # Free memory

High Memory Usage
^^^^^^^^^^^^^^^^^

**Problem:** Python process using excessive RAM.

**Diagnosis:**

.. code-block:: python

   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024**2:.2f} MB")

**Solutions:**

1. **Enable compression in cache:**

   .. code-block:: python

      config = ENAHOConfig(enable_compression=True)  # Saves ~40% space

2. **Clear unused variables:**

   .. code-block:: python

      del large_dataframe
      import gc
      gc.collect()

3. **Use memory-mapped files for very large datasets:**

   .. code-block:: python

      df = pd.read_stata('file.dta', iterator=True, chunksize=50000)

Merge Issues
------------

Key Mismatch Errors
^^^^^^^^^^^^^^^^^^^

**Problem:** ``MergeError: No common columns to perform merge on``.

**Diagnosis:**

.. code-block:: python

   # Check if keys exist
   print(df1.columns.tolist())
   print(df2.columns.tolist())

   # Check data types
   print(df1[['conglome', 'vivienda', 'hogar']].dtypes)
   print(df2[['conglome', 'vivienda', 'hogar']].dtypes)

**Solutions:**

1. **Standardize key names:**

   .. code-block:: python

      # Rename if needed
      df2 = df2.rename(columns={'Conglome': 'conglome'})

2. **Convert data types:**

   .. code-block:: python

      # Ensure consistent types
      for df in [df1, df2]:
          df['conglome'] = df['conglome'].astype(str)
          df['vivienda'] = df['vivienda'].astype(str)
          df['hogar'] = df['hogar'].astype(int)

Duplicate Keys
^^^^^^^^^^^^^^

**Problem:** ``MergeError: Merge keys are not unique``.

**Diagnosis:**

.. code-block:: python

   # Find duplicates
   merge_keys = ['conglome', 'vivienda', 'hogar']
   duplicates = df[df.duplicated(subset=merge_keys, keep=False)]
   print(f"Duplicates: {len(duplicates)}")
   print(duplicates[merge_keys].head())

**Solutions:**

1. **Remove duplicates:**

   .. code-block:: python

      # Keep first occurrence
      df_clean = df.drop_duplicates(subset=merge_keys, keep='first')

2. **Aggregate duplicates:**

   .. code-block:: python

      # Sum numeric columns, keep first for others
      df_agg = df.groupby(merge_keys).agg({
          'gashog2d': 'mean',
          'mieperho': 'first'
      }).reset_index()

3. **Investigate cause:**

   .. code-block:: python

      # Check if it's a data issue
      # Some households may legitimately have multiple records

Unexpected NaN Values After Merge
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** Many NaN values appear after merging.

**Diagnosis:**

.. code-block:: python

   # Compare record counts
   print(f"Left: {len(df_left)}")
   print(f"Right: {len(df_right)}")
   print(f"Merged: {len(df_merged)}")

   # Check match rate
   matched = df_merged.notna().all(axis=1).sum()
   match_rate = (matched / len(df_merged)) * 100
   print(f"Match rate: {match_rate:.1f}%")

**Solutions:**

1. **Verify merge type:**

   .. code-block:: python

      # Use 'inner' to see only matched records
      df_inner = merger.merge(df1, df2, on=keys, how='inner')

      # Use 'left' to keep all records from df1
      df_left = merger.merge(df1, df2, on=keys, how='left')

2. **Check key formats:**

   .. code-block:: python

      # Leading zeros may be missing
      df['conglome'] = df['conglome'].str.zfill(6)

3. **Validate data quality:**

   Not all modules cover the same households. Some NaNs are expected.

Cache Issues
------------

Cache Consuming Too Much Space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** ``.enaho_cache`` directory is very large.

**Diagnosis:**

.. code-block:: python

   from enahopy.loader.core.cache import CacheManager

   cache = CacheManager(cache_dir='./.enaho_cache')
   analytics = cache.get_analytics()
   print(f"Cache size: {analytics['total_size_mb']:.2f} MB")

**Solutions:**

1. **Clear expired entries:**

   .. code-block:: python

      cache.clear_expired()

2. **Clear specific entries:**

   .. code-block:: python

      # Clear by year
      cache.clear()  # Clears all

3. **Set size limit:**

   .. code-block:: python

      config = ENAHOConfig(
          cache_dir='./.enaho_cache',
          max_cache_size_mb=1000  # 1 GB limit
      )

4. **Enable compression:**

   .. code-block:: python

      config = ENAHOConfig(enable_compression=True)

Cache Corruption
^^^^^^^^^^^^^^^^

**Problem:** ``PickleError`` or ``EOFError`` when loading cached data.

**Solution:**

.. code-block:: python

   # Clear corrupted cache
   cache = CacheManager(cache_dir='./.enaho_cache')
   cache.clear_all()

   # Re-download data
   downloader.download(modules=['34'], years=['2023'])

Missing Data Analysis Issues
-----------------------------

ENAHONullAnalyzer Not Found
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** ``ImportError: cannot import name 'ENAHONullAnalyzer'``.

**Solution:**

.. code-block:: python

   # Correct import
   from enahopy.null_analysis import ENAHONullAnalyzer

   # Or use convenience function
   from enahopy import ENAHONullAnalyzer

Advanced Imputation Not Available
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** ``ML_IMPUTATION_AVAILABLE = False``.

**Cause:** Optional dependencies not installed.

**Solution:**

.. code-block:: bash

   # Install with all optional dependencies
   pip install enahopy[full]

   # Or install specific packages
   pip install scikit-learn scipy

Report Generation Fails
^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** HTML report not generated.

**Diagnosis:** Check write permissions and disk space.

**Solutions:**

1. **Specify valid output path:**

   .. code-block:: python

      analyzer.analyze(df, generate_report=True, report_path='./reports/missing.html')

2. **Check permissions:**

   .. code-block:: bash

      # Ensure directory is writable
      ls -la ./reports/

3. **Disable report temporarily:**

   .. code-block:: python

      results = analyzer.analyze(df, generate_report=False)

Performance Issues
------------------

Slow Download Speed
^^^^^^^^^^^^^^^^^^^

**Problem:** Downloads are very slow.

**Solutions:**

1. **Use cache effectively:**

   Second runs should be 5-10x faster with cache enabled.

2. **Download during off-peak hours:**

   INEI servers are faster at night/weekends.

3. **Check your internet speed:**

   .. code-block:: bash

      speedtest-cli

Slow Merge Operations
^^^^^^^^^^^^^^^^^^^^^

**Problem:** Merges take too long.

**Solutions:**

1. **Use ENAHOMerger instead of pandas:**

   .. code-block:: python

      # ENAHOMerger is 3-5x faster
      merger = ENAHOMerger(MergerConfig(enable_categorical_encoding=True))
      df = merger.merge(df1, df2, on=keys)

2. **Sort data by keys first:**

   .. code-block:: python

      df1 = df1.sort_values(merge_keys)
      df2 = df2.sort_values(merge_keys)

3. **Remove unnecessary columns:**

   .. code-block:: python

      # Keep only needed columns before merge
      df1_subset = df1[merge_keys + ['gashog2d', 'inghog2d']]

Data Quality Issues
-------------------

Unexpected Data Values
^^^^^^^^^^^^^^^^^^^^^^

**Problem:** Variables have unexpected values or ranges.

**Solutions:**

1. **Check INEI codebook:**

   Variable definitions and valid ranges are in the technical fiches.

2. **Handle missing data codes:**

   ENAHO uses specific codes for missing data (99, 999, etc.):

   .. code-block:: python

      # Replace missing codes
      df['income'] = df['income'].replace({99: np.nan, 999: np.nan})

3. **Validate against INEI statistics:**

   Cross-check your results with official INEI publications.

Inconsistent Time Series
^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** Variables change definition across years.

**Solution:** Check INEI methodology changes:

- Variable names may change
- Questionnaire structure may evolve
- Sample design may be updated

.. code-block:: python

   # Always check variable availability by year
   if 'gashog2d' in df.columns:
       # Process
   else:
       # Use alternative variable

Platform-Specific Issues
------------------------

Windows: Path Issues
^^^^^^^^^^^^^^^^^^^^

**Problem:** ``FileNotFoundError`` with forward slashes.

**Solution:**

.. code-block:: python

   from pathlib import Path

   # Use Path for cross-platform compatibility
   cache_dir = Path('.') / '.enaho_cache'
   config = ENAHOConfig(cache_dir=str(cache_dir))

macOS: SSL Certificate Errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem:** ``SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]``.

**Solution:**

.. code-block:: bash

   # Install certificates
   /Applications/Python\ 3.x/Install\ Certificates.command

Getting Help
------------

If your issue isn't covered here:

1. **Search GitHub Issues:** https://github.com/elpapx/enahopy/issues
2. **Check FAQ:** :doc:`faq`
3. **Open a new issue** with:

   - ENAHOPY version (``enahopy.__version__``)
   - Python version (``python --version``)
   - Operating system
   - Full error traceback
   - Minimal reproducible example

Debug Mode
^^^^^^^^^^

Enable verbose logging for troubleshooting:

.. code-block:: python

   import logging

   logging.basicConfig(level=logging.DEBUG)

   # Now all ENAHOPY operations will log detailed information

Common Error Messages
---------------------

Quick reference for error messages:

+------------------------------------------+---------------------------+
| Error Message                            | See Section               |
+==========================================+===========================+
| ``ModuleNotFoundError``                  | Installation Issues       |
+------------------------------------------+---------------------------+
| ``TimeoutError``                         | Download Failures         |
+------------------------------------------+---------------------------+
| ``MemoryError``                          | Memory Errors             |
+------------------------------------------+---------------------------+
| ``MergeError``                           | Merge Issues              |
+------------------------------------------+---------------------------+
| ``PickleError``                          | Cache Issues              |
+------------------------------------------+---------------------------+
| ``ImportError`` (imputation)             | Missing Data Analysis     |
+------------------------------------------+---------------------------+

Preventive Best Practices
--------------------------

Avoid common issues by following these practices:

1. **Always use virtual environments**
2. **Enable caching** for repeated analyses
3. **Validate data after downloads and merges**
4. **Check INEI documentation** for variable definitions
5. **Start with small samples** before processing full datasets
6. **Keep ENAHOPY updated:** ``pip install --upgrade enahopy``
7. **Monitor memory usage** for large datasets
8. **Use version control** for analysis scripts

Still Stuck?
------------

Open a GitHub issue with the ``help wanted`` label and provide:

- What you're trying to do
- What you expected to happen
- What actually happened
- Code to reproduce the issue

The community will help!
