Frequently Asked Questions (FAQ)
==================================

General Usage
-------------

What is ENAHOPY?
^^^^^^^^^^^^^^^^

ENAHOPY is a Python library for analyzing ENAHO (Encuesta Nacional de Hogares) microdata from Peru's INEI. It simplifies downloading, merging, and analyzing household survey data.

**Key features:**

- Automated data downloading from INEI servers
- Intelligent module merging with validation
- Advanced missing data analysis
- Performance-optimized operations

Who should use ENAHOPY?
^^^^^^^^^^^^^^^^^^^^^^^^

ENAHOPY is designed for:

- **Economists** analyzing poverty and inequality
- **Social scientists** studying household behavior
- **Policy researchers** evaluating social programs
- **Data scientists** working with survey microdata
- **Students** learning survey data analysis

**Prerequisites:** Basic Python knowledge and familiarity with pandas.

How is ENAHOPY different from manual analysis?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Manual approach:**

1. Download ZIP files from INEI website
2. Extract files manually
3. Load .dta files with pandas/stata
4. Manually merge modules with complex keys
5. Handle missing data ad-hoc

**With ENAHOPY:**

.. code-block:: python

   # One command does it all
   downloader.download(modules=['34'], years=['2023'], load_dta=True)
   merger.merge(df1, df2, on=['conglome', 'vivienda', 'hogar'])
   analyzer.analyze(df)

**Benefits:**

- 10x faster development
- Cached downloads (5-10x faster re-runs)
- Built-in validation
- Consistent methodology

Is ENAHOPY free?
^^^^^^^^^^^^^^^^

Yes! ENAHOPY is open-source under the MIT license. Free for academic, commercial, and personal use.

Installation & Setup
--------------------

What Python version do I need?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Minimum:** Python 3.8+

**Recommended:** Python 3.10 or 3.11

Check your version:

.. code-block:: bash

   python --version

Do I need to install ENAHO data separately?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No! ENAHOPY downloads data automatically from INEI servers.

You can also load local .dta files:

.. code-block:: python

   import pandas as pd
   df = pd.read_stata('local_file.dta')

What are the optional dependencies?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Core installation** (required):

.. code-block:: bash

   pip install enahopy

**Full installation** (recommended for advanced features):

.. code-block:: bash

   pip install enahopy[full]

**Includes:**

- ``scikit-learn`` - ML imputation (MICE, MissForest)
- ``seaborn`` - Enhanced visualizations
- ``matplotlib`` - Plotting
- ``scipy`` - Statistical functions

Can I use ENAHOPY with Anaconda?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes!

.. code-block:: bash

   # Create conda environment
   conda create -n enahopy python=3.10
   conda activate enahopy

   # Install ENAHOPY
   pip install enahopy[full]

Data Downloading
----------------

Which ENAHO modules are available?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Household-level modules:**

- **01** - Dwelling and household characteristics
- **34** - Sumaria (income, expenditure, poverty)
- **37** - Governance and social programs

**Individual-level modules:**

- **02** - Household members roster
- **03** - Education
- **04** - Health
- **05** - Employment

**Full list:** See INEI microdata portal.

Which years can I download?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ENAHO started in **2004**. Most modules available from 2004-present.

**Note:**

- Module availability varies by year
- Older years may have different variable names
- Always check INEI technical fiches for changes

How do I download multiple years?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   result = downloader.download(
       modules=['34'],
       years=['2021', '2022', '2023'],  # List of years
       decompress=True,
       load_dta=True
   )

How long do downloads take?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**First download:** 30 seconds - 5 minutes per module/year (depends on internet speed)

**Cached downloads:** < 1 second

**Tips for faster downloads:**

- Use cache (enabled by default)
- Download during off-peak hours
- Download multiple years in one call

What if INEI servers are down?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ENAHOPY has built-in retry logic (3 attempts). If servers are unavailable:

1. **Check cache** - May have data from previous download
2. **Try later** - INEI servers are sometimes temporarily offline
3. **Use local files** - Load .dta files directly with pandas

Can I use my own .dta files?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! ENAHOPY works with any ENAHO .dta file:

.. code-block:: python

   import pandas as pd

   # Load local file
   df = pd.read_stata('/path/to/sumaria.dta')

   # Use with ENAHOPY tools
   merger = ENAHOMerger()
   analyzer = ENAHONullAnalyzer()

Module Merging
--------------

What are the merge keys?
^^^^^^^^^^^^^^^^^^^^^^^^^

**Household-level:** ``['conglome', 'vivienda', 'hogar']``

**Individual-level:** ``['conglome', 'vivienda', 'hogar', 'codperso']``

**Explanation:**

- ``conglome`` - Cluster/conglomerate ID
- ``vivienda`` - Dwelling ID within cluster
- ``hogar`` - Household ID within dwelling
- ``codperso`` - Person ID within household

Can I merge different survey levels?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not directly. **First aggregate individual → household:**

.. code-block:: python

   # Aggregate employment data to household level
   empleo_hh = df_empleo.groupby(['conglome', 'vivienda', 'hogar']).agg({
       'employed': 'sum',
       'income': 'mean'
   }).reset_index()

   # Now merge with household-level data
   df_merged = merger.merge(df_sumaria, empleo_hh, on=['conglome', 'vivienda', 'hogar'])

What if merge keys don't match?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Common causes:**

1. **Data type mismatch** - One is string, other is int
2. **Leading zeros missing** - '123' vs '000123'
3. **Different variable names** - 'conglome' vs 'Conglome'

**Solutions:**

.. code-block:: python

   # Standardize types
   df['conglome'] = df['conglome'].astype(str).str.zfill(6)

   # Rename columns
   df = df.rename(columns={'Conglome': 'conglome'})

How do I merge multiple modules at once?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Merge sequentially:

.. code-block:: python

   # Merge 1: Sumaria + Hogar
   df_merged = merger.merge(df_sumaria, df_hogar, on=keys)

   # Merge 2: Result + Governance
   df_final = merger.merge(df_merged, df_governance, on=keys)

Or use pandas' multi-way merge:

.. code-block:: python

   from functools import reduce

   dfs = [df_sumaria, df_hogar, df_governance]
   df_final = reduce(lambda left, right: merger.merge(left, right, on=keys), dfs)

Missing Data Analysis
---------------------

What missing data strategies does ENAHOPY support?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Basic strategies:**

- Mean/median imputation
- Mode imputation (categorical)
- Forward/backward fill
- Deletion (listwise/pairwise)

**Advanced strategies (with ML dependencies):**

- **MICE** - Multiple Imputation by Chained Equations
- **MissForest** - Random Forest imputation
- **Autoencoders** - Deep learning imputation
- **ENAHO-specific patterns** - Domain-aware imputation

When should I use advanced imputation?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use advanced imputation when:

- Missing data > 5-10%
- Data is **missing at random (MAR)**
- You need to preserve correlations
- Analysis requires complete cases

**Don't use when:**

- Data is **missing not at random (MNAR)**
- Missing data has structural meaning
- Small sample size (< 500 observations)

How do I choose between MICE and MissForest?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Use MICE when:**

- Mixed data types (numeric + categorical)
- Need uncertainty quantification (multiple imputations)
- Computational resources limited

**Use MissForest when:**

- Complex non-linear relationships
- Many categorical variables
- Don't need multiple imputations

**Benchmark both:**

.. code-block:: python

   from enahopy.null_analysis import compare_imputation_methods

   results = compare_imputation_methods(
       df,
       methods=['mice', 'missforest'],
       test_fraction=0.1
   )

Can ENAHOPY detect missing data patterns?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! ENAHONullAnalyzer automatically detects:

- **MCAR** - Missing Completely at Random
- **MAR** - Missing at Random
- **MNAR** - Missing Not at Random
- **Structural missingness** - E.g., employment questions for children
- **Skip patterns** - Survey logic-based missingness

.. code-block:: python

   analyzer = ENAHONullAnalyzer()
   results = analyzer.analyze(df)
   print(results['patterns'])

Performance
-----------

How can I speed up my analysis?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**1. Enable caching:**

.. code-block:: python

   config = ENAHOConfig(cache_dir='./.enaho_cache')

**2. Use ENAHOMerger (not pandas):**

.. code-block:: python

   merger = ENAHOMerger(MergerConfig(enable_categorical_encoding=True))

**3. Load only needed columns:**

.. code-block:: python

   df = pd.read_stata('file.dta', columns=['conglome', 'gashog2d'])

**4. Process in chunks for large datasets:**

.. code-block:: python

   config = ENAHOConfig(chunk_size=10000, optimize_memory=True)

**5. Use categorical dtypes:**

.. code-block:: python

   df['departamento'] = df['departamento'].astype('category')

How much RAM do I need?
^^^^^^^^^^^^^^^^^^^^^^^^

**Typical requirements:**

- **Single year, single module:** 500 MB - 1 GB
- **Multiple years:** 2-4 GB
- **Full panel (10+ years):** 8-16 GB

**Memory-saving tips:**

- Use chunked processing
- Enable compression
- Remove unnecessary columns
- Use categorical dtypes

Why is the first run slow?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**First run downloads from INEI servers:**

- Download: 30 sec - 5 min
- Decompression: 10-30 sec
- Loading: 10-30 sec

**Second run uses cache:**

- Load from cache: < 1 sec
- **5-10x speedup!**

Geographic Analysis
-------------------

What is UBIGEO?
^^^^^^^^^^^^^^^

UBIGEO is Peru's geographic coding system:

**Format:** 6 digits ``DDPPDD``

- **DD** (1-2): Department code (01-25)
- **PP** (3-4): Province code within department
- **DD** (5-6): District code within province

**Example:** ``150131`` = Lima (15), Lima (01), San Isidro (31)

How do I extract department from UBIGEO?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Extract hierarchy
   df['ubigeo'] = df['ubigeo'].astype(str).str.zfill(6)
   df['dept'] = df['ubigeo'].str[:2]
   df['prov'] = df['ubigeo'].str[:4]
   df['dist'] = df['ubigeo'].str[:6]

Can I merge with external geographic data?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Use UBIGEO as the merge key:

.. code-block:: python

   # Load external shapefile or CSV with UBIGEO
   geo_data = pd.read_csv('ubigeo_names.csv')

   # Merge
   df_merged = pd.merge(df_enaho, geo_data, on='ubigeo')

Where can I find UBIGEO name mappings?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

INEI provides UBIGEO catalogs:

- `INEI UBIGEO <https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1261/Libro.pdf>`_
- Check ``notebooks/UBIGEO 2022_1891 distritos.xlsx`` in ENAHOPY repo

Data Quality & Validation
--------------------------

How do I validate my results?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**1. Cross-check with INEI official statistics:**

.. code-block:: python

   # Compare poverty rate
   my_poverty_rate = (df['gashog2d'] < 378).mean() * 100
   # INEI 2023: ~27.5%

**2. Check variable definitions in technical fiches**

**3. Validate merge results:**

.. code-block:: python

   # Check match rate
   matched_pct = (df_merged.notna().all(axis=1).sum() / len(df_merged)) * 100

**4. Use ENAHOPY validation:**

.. code-block:: python

   merger_config = MergerConfig(enable_validation=True)

What are common data quality issues?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Missing data codes** - 99, 999, etc. need to be converted to NaN
2. **Outliers** - Extreme values in income/expenditure
3. **Inconsistent coding** - Variable definitions change across years
4. **Survey weights** - Must use ``factor07`` for population estimates
5. **Skip patterns** - Structural missingness (e.g., children not asked employment questions)

How do I use survey weights?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Weighted mean
   weighted_mean = np.average(df['gashog2d'], weights=df['factor07'])

   # Weighted poverty rate
   poor = df['gashog2d'] < 378
   weighted_poverty = (poor * df['factor07']).sum() / df['factor07'].sum()

   # With pandas
   df['weighted_poor'] = df['pobreza'] * df['factor07']

Integration with Other Tools
-----------------------------

Can I use ENAHOPY with Stata?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Export to .dta format:

.. code-block:: python

   # After processing with ENAHOPY
   df.to_stata('processed_enaho.dta', write_index=False)

Can I use ENAHOPY with R?
^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Export to CSV or Feather:

.. code-block:: python

   # CSV (compatible with R)
   df.to_csv('enaho_data.csv', index=False)

   # Feather (faster, preserves types)
   df.to_feather('enaho_data.feather')

Then in R:

.. code-block:: r

   # R code
   library(arrow)
   df <- read_feather('enaho_data.feather')

Can I use ENAHOPY with Excel?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes, but not recommended for large datasets:

.. code-block:: python

   # Export subset to Excel
   df_sample = df.head(1000)  # Excel limit: ~1M rows
   df_sample.to_excel('enaho_sample.xlsx', index=False)

Can I use ENAHOPY in Jupyter notebooks?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Absolutely! ENAHOPY is designed for interactive use:

.. code-block:: python

   # In Jupyter
   from enahopy.loader import ENAHODataDownloader
   import pandas as pd

   downloader = ENAHODataDownloader()
   result = downloader.download(modules=['34'], years=['2023'])

   # Visualize
   df.hist(column='gashog2d', bins=50)

Troubleshooting
---------------

Where do I report bugs?
^^^^^^^^^^^^^^^^^^^^^^^

`GitHub Issues <https://github.com/elpapx/enahopy/issues>`_

Include:

- ENAHOPY version
- Python version
- Operating system
- Full error traceback
- Minimal reproducible example

How do I get help?
^^^^^^^^^^^^^^^^^^

1. **Documentation** - Check docs first
2. **Troubleshooting guide** - :doc:`troubleshooting`
3. **FAQ** - You're here!
4. **GitHub Issues** - Search existing issues
5. **GitHub Discussions** - Ask questions

Why is my question not here?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This FAQ is continuously updated. Help us improve it:

- Open an issue suggesting new FAQ entries
- Submit a PR adding your question
- Share common issues you've encountered

Advanced Topics
---------------

Can I extend ENAHOPY with custom imputation methods?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Implement the ``BaseImputer`` interface:

.. code-block:: python

   from enahopy.null_analysis.strategies.base import BaseImputer

   class CustomImputer(BaseImputer):
       def fit_transform(self, df, **kwargs):
           # Your custom logic
           return imputed_df

Can I contribute to ENAHOPY?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! We welcome contributions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See ``CONTRIBUTING.md`` for guidelines.

How do I cite ENAHOPY in research?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bibtex

   @software{enahopy2024,
     author = {Camacho, Paul},
     title = {ENAHOPY: Python Library for INEI ENAHO Microdata Analysis},
     year = {2024},
     url = {https://github.com/elpapx/enahopy},
     version = {0.5.0}
   }

Where can I find example notebooks?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check the ``examples/`` and ``notebooks/`` directories:

- ``examples/01_complete_poverty_analysis.py``
- ``examples/02_geographic_inequality_analysis.py``
- ``examples/03_multimodule_analysis.py``
- ``examples/04_advanced_ml_imputation_demo.py``
- ``notebooks/tutorial_enahopy_guia_rapida_fixed.ipynb``

Is there a community forum?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use **GitHub Discussions** for:

- Questions
- Show & tell (share your analyses)
- Feature requests
- General discussion

Link: https://github.com/elpapx/enahopy/discussions

License & Legal
---------------

What license does ENAHOPY use?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**MIT License** - Free for commercial, academic, and personal use.

Can I use ENAHOPY for commercial projects?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! The MIT license allows commercial use.

Is ENAHO data public?
^^^^^^^^^^^^^^^^^^^^^^

Yes! ENAHO microdata is publicly available from INEI under open data policies.

**Citation required:** When publishing results, cite INEI as the data source.

Roadmap & Future Features
--------------------------

What features are planned?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

See ``ROADMAP.md`` for the full roadmap. Highlights:

- Panel data construction tools
- Advanced econometric functions
- Geographic visualization with maps
- Integration with causal inference libraries
- CLI for command-line workflows

How can I request a feature?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open a GitHub issue with the ``enhancement`` label:

1. Describe the feature
2. Explain the use case
3. Provide example code (if possible)

Still have questions?
---------------------

**Ask on GitHub Discussions:** https://github.com/elpapx/enahopy/discussions

We're here to help!
