Loader Module
=============

The ``enahopy.loader`` module provides comprehensive functionality for downloading, reading, and caching ENAHO microdata files from INEI servers.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

The loader module is the primary entry point for acquiring ENAHO data. It handles:

- **Automated downloading** from INEI servers with retry logic
- **Intelligent caching** with compression and LRU eviction
- **Multiple file format support** (SPSS, Stata, CSV, Parquet)
- **Parallel downloads** for improved performance
- **Data validation** to ensure integrity

Main Classes
------------

ENAHODataDownloader
^^^^^^^^^^^^^^^^^^^

The main class for downloading and managing ENAHO data.

.. autoclass:: enahopy.loader.ENAHODataDownloader
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Example:

   .. code-block:: python

      from enahopy.loader import ENAHODataDownloader

      # Basic usage
      downloader = ENAHODataDownloader(verbose=True)

      # Download with options
      downloader.download(
          modules=['01', '34'],
          years=['2021', '2022'],
          output_dir='./data',
          decompress=True,
          parallel=True,
          max_workers=4
      )

ENAHOLocalReader
^^^^^^^^^^^^^^^^

Read and process local ENAHO files.

.. autoclass:: enahopy.loader.ENAHOLocalReader
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Example:

   .. code-block:: python

      from enahopy.loader import ENAHOLocalReader

      # Read local file
      reader = ENAHOLocalReader('enaho01-2021-34.dta')
      df, validation = reader.read_data()

      # Read with streaming for large files
      for chunk in reader.read_in_chunks(chunksize=10000):
          process_chunk(chunk)

Cache Management
----------------

CacheManager
^^^^^^^^^^^^

Intelligent cache with compression, LRU eviction, and analytics.

.. autoclass:: enahopy.loader.core.CacheManager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Features:

- **Automatic compression**: Reduces disk usage by ~40%
- **LRU eviction**: Configurable size limits with least-recently-used removal
- **Hit/miss tracking**: Performance analytics for cache optimization
- **TTL management**: Automatic expiration of stale entries

Example:

   .. code-block:: python

      from enahopy.loader.core import CacheManager

      # Basic cache
      cache = CacheManager(cache_dir='.cache', ttl_hours=48)

      # Advanced cache with LRU and compression
      cache = CacheManager(
          cache_dir='.cache',
          ttl_hours=48,
          max_size_mb=100,
          enable_compression=True
      )

      # Store data
      cache.set_metadata('my_key', {'data': 'value'})

      # Retrieve data
      data = cache.get_metadata('my_key')

      # Get analytics
      stats = cache.get_analytics()
      print(f"Hit rate: {stats['hit_rate']*100:.1f}%")

File Readers
------------

ReaderFactory
^^^^^^^^^^^^^

Factory for creating appropriate file readers.

.. autoclass:: enahopy.loader.io.ReaderFactory
   :members:
   :undoc-members:
   :show-inheritance:

Supported Formats
^^^^^^^^^^^^^^^^^

SPSSReader
""""""""""

.. autoclass:: enahopy.loader.io.SPSSReader
   :members:
   :undoc-members:
   :show-inheritance:

StataReader
"""""""""""

.. autoclass:: enahopy.loader.io.StataReader
   :members:
   :undoc-members:
   :show-inheritance:

CSVReader
"""""""""

.. autoclass:: enahopy.loader.io.CSVReader
   :members:
   :undoc-members:
   :show-inheritance:

ParquetReader
"""""""""""""

.. autoclass:: enahopy.loader.io.ParquetReader
   :members:
   :undoc-members:
   :show-inheritance:

All readers support:

- **Streaming mode**: Read large files in chunks
- **Column selection**: Load only needed columns
- **Memory optimization**: Automatic dtype optimization
- **Validation**: Data integrity checks

Configuration
-------------

ENAHOConfig
^^^^^^^^^^^

Configuration class for loader behavior.

.. autoclass:: enahopy.loader.core.ENAHOConfig
   :members:
   :undoc-members:
   :show-inheritance:

Example:

   .. code-block:: python

      from enahopy.loader.core import ENAHOConfig

      # Custom configuration
      config = ENAHOConfig(
          base_url='http://custom-server.com',
          cache_dir='/data/cache',
          cache_ttl_hours=72,
          default_max_workers=8
      )

      downloader = ENAHODataDownloader(config=config)

Validation
----------

ENAHOValidator
^^^^^^^^^^^^^^

Validates download requests and data integrity.

.. autoclass:: enahopy.loader.io.ENAHOValidator
   :members:
   :undoc-members:
   :show-inheritance:

ColumnValidator
^^^^^^^^^^^^^^^

Validates column data types and constraints.

.. autoclass:: enahopy.loader.io.ColumnValidator
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. autoexception:: enahopy.loader.core.ENAHOError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.loader.core.ENAHODownloadError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.loader.core.ENAHOValidationError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.loader.core.ENAHOIntegrityError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.loader.core.ENAHOTimeoutError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.loader.core.FileReaderError
   :members:
   :show-inheritance:

Utility Functions
-----------------

Convenience functions for common tasks:

.. autofunction:: enahopy.loader.download_enaho_data

.. autofunction:: enahopy.loader.read_enaho_file

.. autofunction:: enahopy.loader.get_file_info

.. autofunction:: enahopy.loader.find_enaho_files

.. autofunction:: enahopy.loader.get_available_data

Performance Tips
----------------

**For Large Downloads**:

1. Enable parallel downloads:

   .. code-block:: python

      downloader.download(
          modules=['01', '34'],
          years=['2020', '2021', '2022'],
          parallel=True,
          max_workers=4
      )

2. Use compression to save disk space:

   .. code-block:: python

      cache = CacheManager(
          cache_dir='.cache',
          enable_compression=True,
          max_size_mb=500
      )

**For Large Files**:

1. Use streaming mode:

   .. code-block:: python

      reader = ENAHOLocalReader('large_file.dta')
      for chunk in reader.read_in_chunks(chunksize=50000):
          process_chunk(chunk)

2. Select only needed columns:

   .. code-block:: python

      df, _ = reader.read_data(columns=['ubigeo', 'mieperho', 'inghog1d'])

See Also
--------

- :doc:`merger`: Merge multiple ENAHO modules
- :doc:`null_analysis`: Analyze missing data
- :doc:`../tutorials/01-basic-download`: Step-by-step tutorial
