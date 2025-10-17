Tutorials
=========

Welcome to the ENAHOPY tutorials! These step-by-step guides will teach you how to use ENAHOPY for analyzing ENAHO microdata.

Tutorial Series
----------------

The tutorials are designed to be completed in order, with each building on concepts from previous ones.

.. toctree::
   :maxdepth: 1
   :caption: Tutorial Sequence

   tutorial_01_data_downloading
   tutorial_02_module_merging
   tutorial_03_geographic_integration
   tutorial_04_missing_data_analysis
   tutorial_05_complete_pipeline

Tutorial Overview
-----------------

Tutorial 1: Data Downloading
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Runtime:** < 5 minutes

**You will learn:**

- How to download ENAHO modules from INEI servers
- How to configure and use the cache system
- How to explore downloaded data
- How to download multiple years and modules

**Prerequisites:** None (start here!)

**Key Topics:**

- ENAHODataDownloader basics
- Cache configuration
- Module structure
- Data validation

Tutorial 2: Module Merging
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Runtime:** < 5 minutes

**You will learn:**

- How to merge household-level modules
- How to merge individual-level modules
- How to aggregate individual data to household level
- How to validate merge results

**Prerequisites:** Tutorial 1

**Key Topics:**

- ENAHOMerger usage
- Primary keys (conglome, vivienda, hogar)
- Merge validation
- Performance optimization

Tutorial 3: Geographic Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Runtime:** < 5 minutes

**You will learn:**

- How to add geographic information using UBIGEO codes
- How to perform spatial analysis
- How to calculate regional statistics
- How to visualize geographic patterns

**Prerequisites:** Tutorials 1-2

**Key Topics:**

- UBIGEO hierarchy (department, province, district)
- Geographic merging
- Regional indicators
- Spatial visualization

Tutorial 4: Missing Data Analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Runtime:** < 8 minutes

**You will learn:**

- How to detect missing data patterns
- How to use basic imputation strategies
- How to apply advanced ML imputation (MICE, MissForest)
- How to assess imputation quality

**Prerequisites:** Tutorials 1-2

**Key Topics:**

- ENAHONullAnalyzer
- Missing data patterns
- Imputation strategies
- Quality assessment

Tutorial 5: Complete Pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Runtime:** < 10 minutes

**You will learn:**

- How to build end-to-end analysis workflows
- How to combine all ENAHOPY modules
- How to create production-ready pipelines
- How to optimize for performance

**Prerequisites:** Tutorials 1-4

**Key Topics:**

- Workflow integration
- Performance optimization
- Best practices
- Production deployment

Learning Path
-------------

Beginner Path
^^^^^^^^^^^^^

1. Start with **Getting Started Guide** for installation and basic concepts
2. Complete **Tutorial 1** to learn data downloading
3. Complete **Tutorial 2** to learn module merging
4. Practice with your own analysis

Intermediate Path
^^^^^^^^^^^^^^^^^

1. Complete Beginner Path
2. Work through **Tutorial 3** for geographic analysis
3. Work through **Tutorial 4** for missing data handling
4. Explore the **API Reference** for advanced features

Advanced Path
^^^^^^^^^^^^^

1. Complete Intermediate Path
2. Work through **Tutorial 5** for complete pipelines
3. Study the **DS-3 Demo Scripts** in `examples/`
4. Review **Troubleshooting Guide** for edge cases
5. Contribute to the project!

Support
-------

If you get stuck:

1. Check the **Troubleshooting Guide**
2. Review the **FAQ**
3. Search **GitHub Issues**
4. Ask a question (open a new issue)

Additional Resources
--------------------

Example Scripts
^^^^^^^^^^^^^^^

See `examples/` directory for production-ready demo scripts:

- ``01_complete_poverty_analysis.py`` - Full poverty analysis workflow
- ``02_geographic_inequality_analysis.py`` - Regional analysis
- ``03_multimodule_analysis.py`` - Cross-sectional analysis
- ``04_advanced_ml_imputation_demo.py`` - Advanced imputation

API Documentation
^^^^^^^^^^^^^^^^^

For detailed API reference:

- :doc:`../api/loader` - Data downloading
- :doc:`../api/merger` - Module merging
- :doc:`../api/null_analysis` - Missing data analysis
- :doc:`../api/convenience` - Helper functions

INEI Resources
^^^^^^^^^^^^^^

Official INEI documentation:

- `INEI Microdatos <http://iinei.inei.gob.pe/microdatos/>`_
- `ENAHO Methodology <http://iinei.inei.gob.pe/iinei/srienaho/>`_
- `Technical Fiches <http://iinei.inei.gob.pe/iinei/srienaho/Descarga/FichaTecnica/>`_

Feedback
--------

We welcome feedback on these tutorials! If you find:

- Errors or typos
- Unclear explanations
- Missing topics
- Better examples

Please open an issue on GitHub with the label ``documentation``.

Happy learning!
