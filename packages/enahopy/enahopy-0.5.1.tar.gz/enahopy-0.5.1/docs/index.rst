ENAHOPY Documentation
=====================

**ENAHOPY** es una librería Python profesional para el análisis de microdatos de la Encuesta Nacional de Hogares (ENAHO) del Instituto Nacional de Estadística e Informática (INEI) del Perú.

Versión: v0.1.2 (Alpha → Beta)

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.8+

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://github.com/elpapx/enahopy/blob/main/LICENSE
   :alt: MIT License

Características Principales
----------------------------

📥 **Descarga Inteligente**
   - Descarga automática desde servidores INEI
   - Sistema de caché optimizado con compresión
   - Descarga paralela y gestión de errores robusta

🔗 **Fusión de Módulos**
   - Merge inteligente entre módulos ENAHO
   - Fusión geográfica con validación de UBIGEO
   - Creación de datos panel longitudinales

📊 **Análisis de Datos Faltantes**
   - Detección automática de patrones de valores nulos
   - Estrategias de imputación avanzadas (MICE, MissForest)
   - Reportes visuales interactivos

⚡ **Alto Rendimiento**
   - Procesamiento por chunks para datasets grandes
   - Streaming readers para archivos masivos
   - Optimización de memoria automática

Guía Rápida
-----------

Instalación
^^^^^^^^^^^

.. code-block:: bash

   pip install enahopy

Para funcionalidades completas:

.. code-block:: bash

   pip install enahopy[full]

Uso Básico
^^^^^^^^^^

Descargar datos ENAHO:

.. code-block:: python

   from enahopy import ENAHODataDownloader

   # Inicializar descargador
   downloader = ENAHODataDownloader(verbose=True)

   # Descargar módulos específicos
   downloader.download(
       modules=['01', '34'],  # Características de la vivienda y Sumaria
       years=['2021', '2022'],
       output_dir='./data',
       decompress=True
   )

Fusionar módulos:

.. code-block:: python

   from enahopy import merge_enaho_modules
   import pandas as pd

   # Cargar módulos
   modules = {
       '34': pd.read_stata('enaho01-2021-34.dta'),
       '37': pd.read_stata('enaho01-2021-37.dta')
   }

   # Fusionar a nivel de hogar
   merged_df = merge_enaho_modules(
       modules_dict=modules,
       base_module='34',
       level='hogar',
       strategy='coalesce'
   )

Analizar valores nulos:

.. code-block:: python

   from enahopy import ENAHONullAnalyzer

   # Crear analizador
   analyzer = ENAHONullAnalyzer(verbose=True)

   # Analizar patrones
   results = analyzer.analyze(merged_df, generate_report=True)

   # Ver resumen
   print(f"Valores nulos: {results['summary']['null_percentage']:.2f}%")

Contenido de la Documentación
------------------------------

.. toctree::
   :maxdepth: 2
   :caption: Guía del Usuario

   getting-started
   tutorials/index
   troubleshooting
   faq

.. toctree::
   :maxdepth: 2
   :caption: Referencia de API

   api/loader
   api/merger
   api/null_analysis
   api/convenience

.. toctree::
   :maxdepth: 1
   :caption: Especificaciones

   cli-specification
   architecture
   changelog

.. toctree::
   :maxdepth: 1
   :caption: Desarrollo

   contributing
   roadmap
   license

Índices y Tablas
----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Recursos Adicionales
--------------------

- **GitHub**: https://github.com/elpapx/enahopy
- **PyPI**: https://pypi.org/project/enahopy/
- **Issues**: https://github.com/elpapx/enahopy/issues
- **Datos INEI**: http://iinei.inei.gob.pe/microdatos/

Soporte
-------

Para reportar bugs o solicitar nuevas características, por favor abre un issue en GitHub:
https://github.com/elpapx/enahopy/issues

Licencia
--------

ENAHOPY está distribuido bajo la licencia MIT. Ver el archivo LICENSE para más detalles.

Cita
----

Si usas ENAHOPY en tu investigación, por favor cita:

.. code-block:: bibtex

   @software{enahopy2024,
     author = {Camacho, Paul},
     title = {ENAHOPY: Python Library for INEI ENAHO Microdata Analysis},
     year = {2024},
     url = {https://github.com/elpapx/enahopy},
     version = {0.1.2}
   }
