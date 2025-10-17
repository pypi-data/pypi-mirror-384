#!/usr/bin/env python
"""
Análisis Multi-Módulo - ENAHO 2023 (Corte Transversal)
=======================================================

Script de demostración para análisis integrado de múltiples módulos ENAHO.

Workflow:
1. Descargar 3 módulos: sumaria, enaho01, enaho34 (empleo)
2. Merge módulos usando claves comunes (conglome, vivienda, hogar)
3. Análisis integrado: características del hogar + individuos + empleo
4. Crear dataset analítico consolidado
5. Análisis de empleo por características del hogar

Valida:
- DE-3: Multi-module merge performance
- Merger: Module compatibility validation
- Integration across different data structures

Autor: ENAHOPY Data-Scientist Team
Fecha: 2025-10-10
Tiempo estimado: 5-7 minutos (primera vez), <2 minutos (cached)
"""

import sys
import logging
import time
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

try:
    from enahopy.loader import ENAHODataDownloader, ENAHOConfig
    from enahopy.merger import ENAHOMerger, MergerConfig
except ImportError:
    print("ERROR: enahopy no está instalado")
    sys.exit(1)

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_synthetic_data():
    """Crea datos sintéticos para demostración"""
    np.random.seed(42)
    n = 5000

    # Módulo sumaria
    sumaria = pd.DataFrame({
        'conglome': [f'HH{i:06d}' for i in range(n)],
        'vivienda': [f'V{i:04d}' for i in range(n)],
        'hogar': [1] * n,
        'gashog2d': np.random.gamma(3, 150, n),
        'inghog2d': np.random.gamma(3, 200, n),
        'mieperho': np.random.poisson(4, n)
    })

    # Módulo 01 (hogar)
    hogar = pd.DataFrame({
        'conglome': sumaria['conglome'].values,
        'vivienda': sumaria['vivienda'].values,
        'hogar': sumaria['hogar'].values,
        'area': np.random.choice(['Urbano', 'Rural'], n, p=[0.7, 0.3]),
        'p104': np.random.choice([1, 2, 3, 4, 5], n),
        'p110': np.random.choice([1, 2, 3, 4], n)
    })

    # Módulo 34 (empleo) - nivel individual
    n_individuos = n * 3  # Promedio 3 individuos por hogar
    empleo = pd.DataFrame({
        'conglome': np.repeat(sumaria['conglome'].values, 3)[:n_individuos],
        'vivienda': np.repeat(sumaria['vivienda'].values, 3)[:n_individuos],
        'hogar': [1] * n_individuos,
        'codperso': [f'P{i%10:02d}' for i in range(n_individuos)],
        'p301a': np.random.choice([1, 2], n_individuos, p=[0.6, 0.4]),  # Ocupado
        'p301b': np.random.choice([1, 2], n_individuos, p=[0.3, 0.7]),  # Desempleado
        'i524a1': np.random.gamma(2, 500, n_individuos)  # Ingreso principal
    })

    return sumaria, hogar, empleo


def main():
    print("\n" + "="*70)
    print(" ANÁLISIS MULTI-MÓDULO - ENAHO 2023 ".center(70))
    print("="*70 + "\n")

    start_time = time.time()

    # Configuración
    config = ENAHOConfig(cache_dir='./.enaho_cache', enable_compression=True)
    merger_config = MergerConfig(enable_categorical_encoding=True)

    downloader = ENAHODataDownloader(config=config)
    merger = ENAHOMerger(config=merger_config)

    try:
        # 1. DESCARGAR MÓDULOS
        print("\n[1/5] Descargando módulos ENAHO 2023...")
        try:
            df_sumaria = downloader.download_module(2023, 'sumaria', 'dta')
            df_hogar = downloader.download_module(2023, '01', 'dta')
            df_empleo = downloader.download_module(2023, '34', 'dta')
            logger.info("Módulos descargados desde INEI")
        except Exception as e:
            logger.warning(f"Error descargando: {e}. Usando datos sintéticos")
            df_sumaria, df_hogar, df_empleo = create_synthetic_data()

        print(f"  Sumaria: {df_sumaria.shape}")
        print(f"  Hogar: {df_hogar.shape}")
        print(f"  Empleo: {df_empleo.shape}")

        # 2. MERGE SECUENCIAL
        print("\n[2/5] Realizando merge de módulos...")

        merge_keys = ['conglome', 'vivienda', 'hogar']

        # Merge 1: Sumaria + Hogar
        logger.info("Merge 1: Sumaria + Hogar")
        merge1_start = time.time()
        df_merged1 = merger.merge(df_sumaria, df_hogar, on=merge_keys, how='left')
        merge1_time = time.time() - merge1_start
        print(f"  Merge 1 completado: {df_merged1.shape} en {merge1_time:.2f}s")

        # Merge 2: (Sumaria+Hogar) + Empleo
        logger.info("Merge 2: Añadiendo información de empleo")
        merge2_start = time.time()

        # Agregamos datos de empleo a nivel hogar
        if 'codperso' in df_empleo.columns:
            # Agregar métricas de empleo por hogar
            empleo_agg = df_empleo.groupby(merge_keys).agg({
                'p301a': lambda x: (x == 1).sum(),  # Número de ocupados
                'i524a1': 'sum'  # Ingreso total del hogar por trabajo
            }).reset_index()
            empleo_agg.columns = merge_keys + ['num_ocupados', 'ingreso_trabajo_total']

            df_final = merger.merge(df_merged1, empleo_agg, on=merge_keys, how='left')
        else:
            df_final = df_merged1

        merge2_time = time.time() - merge2_start
        print(f"  Merge 2 completado: {df_final.shape} en {merge2_time:.2f}s")
        print(f"  Tiempo total de merge: {merge1_time + merge2_time:.2f}s")

        # 3. ANÁLISIS INTEGRADO
        print("\n[3/5] Realizando análisis integrado...")

        # Calcular métricas integradas
        if 'num_ocupados' in df_final.columns and 'mieperho' in df_final.columns:
            df_final['tasa_ocupacion'] = (df_final['num_ocupados'] / df_final['mieperho']) * 100
            df_final['tasa_ocupacion'] = df_final['tasa_ocupacion'].clip(0, 100)

        if 'ingreso_trabajo_total' in df_final.columns and 'mieperho' in df_final.columns:
            df_final['ingreso_trabajo_percapita'] = df_final['ingreso_trabajo_total'] / df_final['mieperho']

        # Estadísticas por área
        if 'area' in df_final.columns:
            stats_area = df_final.groupby('area').agg({
                'mieperho': 'mean',
                'num_ocupados': 'mean' if 'num_ocupados' in df_final.columns else 'size',
                'tasa_ocupacion': 'mean' if 'tasa_ocupacion' in df_final.columns else 'size'
            }).round(2)

            print("\n  Estadísticas por Área:")
            print(stats_area)

        # 4. VISUALIZACIONES
        print("\n[4/5] Generando visualizaciones...")

        output_dir = Path('./output')
        output_dir.mkdir(exist_ok=True)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Gráfico 1: Distribución de miembros por hogar
        if 'mieperho' in df_final.columns:
            axes[0, 0].hist(df_final['mieperho'].dropna(), bins=20, edgecolor='black', alpha=0.7)
            axes[0, 0].set_xlabel('Miembros del Hogar')
            axes[0, 0].set_ylabel('Frecuencia')
            axes[0, 0].set_title('Distribución de Tamaño del Hogar')

        # Gráfico 2: Tasa de ocupación
        if 'tasa_ocupacion' in df_final.columns:
            axes[0, 1].hist(df_final['tasa_ocupacion'].dropna(), bins=20, edgecolor='black', alpha=0.7, color='green')
            axes[0, 1].set_xlabel('Tasa de Ocupación (%)')
            axes[0, 1].set_ylabel('Frecuencia')
            axes[0, 1].set_title('Distribución de Tasa de Ocupación')

        # Gráfico 3: Ingreso vs Gasto
        if 'inghog2d' in df_final.columns and 'gashog2d' in df_final.columns:
            sample = df_final.sample(min(1000, len(df_final)))
            axes[1, 0].scatter(sample['inghog2d'], sample['gashog2d'], alpha=0.3, s=20)
            axes[1, 0].plot([0, sample['inghog2d'].max()], [0, sample['inghog2d'].max()], 'r--', alpha=0.5)
            axes[1, 0].set_xlabel('Ingreso Per Cápita')
            axes[1, 0].set_ylabel('Gasto Per Cápita')
            axes[1, 0].set_title('Ingreso vs Gasto Per Cápita')

        # Gráfico 4: Comparación Urbano-Rural
        if 'area' in df_final.columns and 'ingreso_trabajo_percapita' in df_final.columns:
            df_plot = df_final[df_final['ingreso_trabajo_percapita'].notna()]
            if len(df_plot) > 0:
                axes[1, 1].boxplot([df_plot[df_plot['area'] == area]['ingreso_trabajo_percapita'].values
                                   for area in df_plot['area'].unique()],
                                  labels=df_plot['area'].unique())
                axes[1, 1].set_ylabel('Ingreso Trabajo Per Cápita')
                axes[1, 1].set_title('Ingreso por Trabajo: Urbano vs Rural')

        plt.tight_layout()
        plt.savefig(output_dir / 'multimodule_analysis.png', dpi=300, bbox_inches='tight')
        logger.info(f"Guardado: {output_dir}/multimodule_analysis.png")
        plt.close()

        # 5. EXPORTAR DATASET
        print("\n[5/5] Exportando dataset consolidado...")

        output_file = output_dir / 'enaho_2023_consolidated.csv'
        df_final.to_csv(output_file, index=False)
        print(f"  Dataset guardado: {output_file}")
        print(f"  Tamaño: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

        # REPORTE FINAL
        execution_time = time.time() - start_time

        print("\n" + "="*70)
        print(" RESULTADOS DEL ANÁLISIS ".center(70))
        print("="*70)
        print(f"\n📊 Registros en dataset final: {len(df_final):,}")
        print(f"📈 Variables disponibles: {len(df_final.columns)}")
        print(f"\n⏱️ Tiempo de ejecución: {execution_time:.2f} segundos")
        print(f"⚡ Performance del merger: {len(df_final) / (merge1_time + merge2_time):.0f} rec/s")

        print("\n" + "="*70)
        print(" ✅ ANÁLISIS COMPLETADO ".center(70))
        print("="*70)
        print(f"\nArchivos generados:")
        print(f"  • {output_dir}/multimodule_analysis.png")
        print(f"  • {output_dir}/enaho_2023_consolidated.csv")

        return 0

    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
