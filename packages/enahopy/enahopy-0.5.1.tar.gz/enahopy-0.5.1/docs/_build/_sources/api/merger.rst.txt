Merger Module
=============

The ``enahopy.merger`` module provides advanced functionality for merging ENAHO modules, integrating geographic data, and creating panel datasets.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

The merger module handles complex data integration tasks:

- **Module merging**: Combine multiple ENAHO modules at different levels (household, person, dwelling)
- **Geographic integration**: Merge geographic data with UBIGEO validation
- **Panel data creation**: Build longitudinal datasets across multiple years
- **Conflict resolution**: Intelligent strategies for handling duplicate columns
- **Data quality validation**: Comprehensive checks for merge integrity

Main Classes
------------

ENAHOGeoMerger
^^^^^^^^^^^^^^

Primary class for geographic and module merging operations.

.. autoclass:: enahopy.merger.ENAHOGeoMerger
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Example:

   .. code-block:: python

      from enahopy.merger import ENAHOGeoMerger, GeoMergeConfiguration

      # Basic usage
      merger = ENAHOGeoMerger(verbose=True)

      # Merge modules
      result_df, report = merger.merge_multiple_modules(
          modules_dict={'34': df_sumaria, '37': df_education},
          base_module='34'
      )

      # Merge with geography
      merged_df, validation = merger.merge_geographic_data(
          df_principal=df_enaho,
          df_geografia=df_ubigeo,
          columna_union='ubigeo'
      )

ENAHOModuleMerger
^^^^^^^^^^^^^^^^^

Specialized class for module-to-module merging.

.. autoclass:: enahopy.merger.ENAHOModuleMerger
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

PanelCreator
^^^^^^^^^^^^

Create longitudinal panel datasets.

.. autoclass:: enahopy.merger.PanelCreator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Example:

   .. code-block:: python

      from enahopy.merger import create_panel_data

      # Create panel from multiple years
      panel_df = create_panel_data(
          data_dict={
              2020: df_2020,
              2021: df_2021,
              2022: df_2022
          },
          id_columns=['conglome', 'vivienda', 'hogar'],
          time_column='anio'
      )

Configuration Classes
---------------------

GeoMergeConfiguration
^^^^^^^^^^^^^^^^^^^^^

Configuration for geographic merging operations.

.. autoclass:: enahopy.merger.GeoMergeConfiguration
   :members:
   :undoc-members:
   :show-inheritance:

Options:

- **columna_union**: UBIGEO column name (default: 'ubigeo')
- **manejo_duplicados**: Strategy for duplicates ('first', 'last', 'aggregate', 'best_quality')
- **manejo_errores**: Error handling ('strict', 'coerce', 'ignore')
- **tipo_validacion_ubigeo**: Validation level ('none', 'structural', 'complete')
- **chunk_size**: Chunk size for large datasets
- **optimizar_memoria**: Enable memory optimization
- **usar_cache**: Enable result caching

Example:

   .. code-block:: python

      from enahopy.merger import GeoMergeConfiguration, TipoManejoDuplicados

      config = GeoMergeConfiguration(
          columna_union='ubigeo',
          manejo_duplicados=TipoManejoDuplicados.AGGREGATE,
          funciones_agregacion={'mieperho': 'sum', 'inghog1d': 'mean'},
          tipo_validacion_ubigeo=TipoValidacionUbigeo.COMPLETE,
          chunk_size=50000,
          optimizar_memoria=True
      )

ModuleMergeConfig
^^^^^^^^^^^^^^^^^

Configuration for module merging.

.. autoclass:: enahopy.merger.ModuleMergeConfig
   :members:
   :undoc-members:
   :show-inheritance:

Example:

   .. code-block:: python

      from enahopy.merger import ModuleMergeConfig, ModuleMergeLevel, ModuleMergeStrategy

      config = ModuleMergeConfig(
          merge_level=ModuleMergeLevel.HOGAR,
          merge_strategy=ModuleMergeStrategy.COALESCE,
          min_match_rate=0.9,
          max_conflicts_allowed=100,
          chunk_processing=True
      )

Enumerations
------------

Geographic Enums
^^^^^^^^^^^^^^^^

.. autoclass:: enahopy.merger.TipoManejoDuplicados
   :members:
   :undoc-members:

.. autoclass:: enahopy.merger.TipoManejoErrores
   :members:
   :undoc-members:

.. autoclass:: enahopy.merger.NivelTerritorial
   :members:
   :undoc-members:

.. autoclass:: enahopy.merger.TipoValidacionUbigeo
   :members:
   :undoc-members:

Module Merge Enums
^^^^^^^^^^^^^^^^^^

.. autoclass:: enahopy.merger.ModuleMergeLevel
   :members:
   :undoc-members:

.. autoclass:: enahopy.merger.ModuleMergeStrategy
   :members:
   :undoc-members:

.. autoclass:: enahopy.merger.ModuleType
   :members:
   :undoc-members:

Result Classes
--------------

GeoValidationResult
^^^^^^^^^^^^^^^^^^^

Results from geographic data validation.

.. autoclass:: enahopy.merger.GeoValidationResult
   :members:
   :undoc-members:
   :show-inheritance:

ModuleMergeResult
^^^^^^^^^^^^^^^^^

Results from module merge operations.

.. autoclass:: enahopy.merger.ModuleMergeResult
   :members:
   :undoc-members:
   :show-inheritance:

Methods:

- ``get_summary_report()``: Generate formatted summary
- ``get_quality_metrics()``: Extract quality indicators
- ``get_warnings()``: List of merge warnings

Validators
----------

UbigeoValidator
^^^^^^^^^^^^^^^

Validates UBIGEO codes and geographic consistency.

.. autoclass:: enahopy.merger.UbigeoValidator
   :members:
   :undoc-members:
   :show-inheritance:

TerritorialValidator
^^^^^^^^^^^^^^^^^^^^

Validates territorial hierarchy consistency.

.. autoclass:: enahopy.merger.TerritorialValidator
   :members:
   :undoc-members:
   :show-inheritance:

GeoDataQualityValidator
^^^^^^^^^^^^^^^^^^^^^^^

Comprehensive data quality validation.

.. autoclass:: enahopy.merger.GeoDataQualityValidator
   :members:
   :undoc-members:
   :show-inheritance:

ModuleValidator
^^^^^^^^^^^^^^^

Validates module compatibility and merge keys.

.. autoclass:: enahopy.merger.ModuleValidator
   :members:
   :undoc-members:
   :show-inheritance:

Pattern Detection
-----------------

GeoPatternDetector
^^^^^^^^^^^^^^^^^^

Automatic detection of geographic columns.

.. autoclass:: enahopy.merger.GeoPatternDetector
   :members:
   :undoc-members:
   :show-inheritance:

Example:

   .. code-block:: python

      from enahopy.merger import GeoPatternDetector

      detector = GeoPatternDetector()
      geo_columns = detector.detectar_columnas_geograficas(
          df=my_dataframe,
          confianza_minima=0.8
      )

      print(geo_columns)
      # {'ubigeo': 0.98, 'departamento': 0.95, 'provincia': 0.92}

Convenience Functions
---------------------

High-level functions for common merge operations:

merge_with_geography
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.merge_with_geography

Example:

   .. code-block:: python

      from enahopy.merger import merge_with_geography

      result_df, validation = merge_with_geography(
          df_principal=enaho_df,
          df_geografia=ubigeo_df,
          columna_union='ubigeo',
          verbose=True
      )

merge_enaho_modules
^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.merge_enaho_modules

Example:

   .. code-block:: python

      from enahopy.merger import merge_enaho_modules

      merged_df = merge_enaho_modules(
          modules_dict={'34': sumaria, '37': education, '85': health},
          base_module='34',
          level='hogar',
          strategy='coalesce',
          verbose=True
      )

merge_modules_with_geography
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.merge_modules_with_geography

validate_ubigeo_data
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.validate_ubigeo_data

detect_geographic_columns
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.detect_geographic_columns

extract_ubigeo_components
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.extract_ubigeo_components

validate_module_compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.validate_module_compatibility

create_merge_report
^^^^^^^^^^^^^^^^^^^

.. autofunction:: enahopy.merger.create_merge_report

Exceptions
----------

.. autoexception:: enahopy.merger.GeoMergeError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.merger.ModuleMergeError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.merger.UbigeoValidationError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.merger.IncompatibleModulesError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.merger.TerritorialInconsistencyError
   :members:
   :show-inheritance:

.. autoexception:: enahopy.merger.DataQualityError
   :members:
   :show-inheritance:

Best Practices
--------------

**Module Merging**:

1. Always validate compatibility first:

   .. code-block:: python

      from enahopy.merger import validate_module_compatibility

      compat = validate_module_compatibility(
          modules_dict={'34': df1, '37': df2},
          level='hogar',
          verbose=True
      )

2. Use appropriate merge strategy:

   - ``COALESCE``: For complementary data (no conflicts expected)
   - ``LEFT_PRIORITY``: Trust base module for conflicts
   - ``LATEST``: Prefer most recent data
   - ``AGGREGATE``: Combine numeric values

**Geographic Merging**:

1. Validate UBIGEO codes before merging:

   .. code-block:: python

      from enahopy.merger import validate_ubigeo_data

      validation = validate_ubigeo_data(
          df=my_df,
          columna_ubigeo='ubigeo',
          tipo_validacion=TipoValidacionUbigeo.COMPLETE
      )

2. Handle duplicates explicitly:

   .. code-block:: python

      config = GeoMergeConfiguration(
          manejo_duplicados=TipoManejoDuplicados.AGGREGATE,
          funciones_agregacion={'mieperho': 'sum'}
      )

**Panel Data**:

1. Ensure consistent identifiers across years
2. Handle attrition and new entries
3. Validate temporal consistency

Performance Optimization
------------------------

**For Large Datasets**:

1. Enable chunked processing:

   .. code-block:: python

      config = GeoMergeConfiguration(
          chunk_size=50000,
          optimizar_memoria=True
      )

2. Use caching for repeated operations:

   .. code-block:: python

      config = GeoMergeConfiguration(
          usar_cache=True
      )

**Memory Management**:

1. Optimize before merging:

   .. code-block:: python

      config = ModuleMergeConfig(
          chunk_processing=True,
          chunk_size=25000
      )

See Also
--------

- :doc:`loader`: Download and read ENAHO data
- :doc:`null_analysis`: Handle missing data
- :doc:`../tutorials/02-module-merging`: Detailed merge tutorial
- :doc:`../tutorials/03-geographic-integration`: Geographic merge tutorial
