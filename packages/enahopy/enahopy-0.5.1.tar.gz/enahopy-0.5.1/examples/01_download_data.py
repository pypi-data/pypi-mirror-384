#!/usr/bin/env python
"""
Script de Demostración: Descarga de Datos ENAHO
================================================
Muestra cómo descargar datos ENAHO desde los servidores del INEI
usando la librería enahopy.

Autor: ENAHOPY Team
Fecha: 2024
"""

import logging
from pathlib import Path
from enahopy.loader import (
    ENAHODataDownloader,
    ENAHOConfig,
    download_enaho_data,
    get_available_data
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def demo_basic_download():
    """Demostración básica de descarga"""
    print("\n" + "=" * 60)
    print("DEMO 1: Descarga Básica de un Módulo")
    print("=" * 60)

    # Forma más simple: usando función de conveniencia
    df = download_enaho_data(
        year=['2023'],
        module='01',  # Módulo de características del hogar
        format='dta'
    )

    print(f"✓ Datos descargados: {df.shape[0]} filas, {df.shape[1]} columnas")
    print(f"✓ Columnas disponibles: {list(df.columns[:5])}...")

    return df


def demo_download_with_config():
    """Demostración con configuración personalizada"""
    print("\n" + "=" * 60)
    print("DEMO 2: Descarga con Configuración Personalizada")
    print("=" * 60)

    # Configurar parámetros personalizados
    config = ENAHOConfig(
        cache_dir='./mi_cache_enaho',
        max_workers=4,
        chunk_size=10000,
        timeout=60,
        enable_validation=True
    )

    # Crear instancia del downloader
    downloader = ENAHODataDownloader(config=config)

    # Descargar múltiples módulos
    modules_to_download = ['01', '02', '34']  # Hogar, Personas, Ingresos

    for module in modules_to_download:
        print(f"\nDescargando módulo {module}...")
        df = downloader.download_module(
            year=2023,
            module=module,
            format='dta'
        )
        print(f"  ✓ Módulo {module}: {df.shape[0]} registros")

    return downloader


def demo_check_available_data():
    """Verificar datos disponibles antes de descargar"""
    print("\n" + "=" * 60)
    print("DEMO 3: Verificar Datos Disponibles")
    print("=" * 60)

    # Verificar qué años y módulos están disponibles
    available = get_available_data()

    print("\nAños disponibles:")
    for year in available['years']:
        print(f"  • {year}")

    print("\nMódulos disponibles para 2023:")
    for module_code, module_name in available['modules_2023'].items():
        print(f"  • {module_code}: {module_name}")

    return available


def demo_batch_download():
    """Descarga en lote de múltiples años"""
    print("\n" + "=" * 60)
    print("DEMO 4: Descarga en Lote (Múltiples Años)")
    print("=" * 60)

    downloader = ENAHODataDownloader()

    years = [2021, 2022, 2023]
    module = '01'  # Características del hogar

    data_collection = {}

    for year in years:
        print(f"\nDescargando año {year}...")
        try:
            df = downloader.download_module(
                year=year,
                module=module,
                format='dta'
            )
            data_collection[year] = df
            print(f"  ✓ Año {year}: {df.shape[0]} hogares")
        except Exception as e:
            print(f"  ✗ Error en año {year}: {e}")

    return data_collection


def demo_download_with_validation():
    """Descarga con validación automática de columnas"""
    print("\n" + "=" * 60)
    print("DEMO 5: Descarga con Validación de Columnas")
    print("=" * 60)

    config = ENAHOConfig(
        enable_validation=True,
        strict_validation=False  # Permite mapeo de columnas similares
    )

    downloader = ENAHODataDownloader(config=config)

    # Descargar y validar
    df, validation_result = downloader.download_and_validate(
        year=2023,
        module='02',  # Características de los miembros del hogar
        expected_columns=['p203', 'p204', 'p207', 'p208']  # Columnas esperadas
    )

    print("\nResultados de validación:")
    print(f"  • Columnas encontradas: {validation_result['found']}")
    print(f"  • Columnas faltantes: {validation_result['missing']}")
    print(f"  • Columnas mapeadas: {validation_result['mapped']}")

    return df, validation_result


def main():
    """Ejecutar todas las demostraciones"""
    print("\n" + "=" * 70)
    print(" DEMOSTRACIONES DE DESCARGA DE DATOS ENAHO ".center(70))
    print("=" * 70)

    # Demo 1: Descarga básica
    df_basic = demo_basic_download()

    # Demo 2: Configuración personalizada
    downloader = demo_download_with_config()

    # Demo 3: Verificar disponibilidad
    available_data = demo_check_available_data()

    # Demo 4: Descarga en lote
    multi_year_data = demo_batch_download()

    # Demo 5: Descarga con validación
    df_validated, validation = demo_download_with_validation()

    print("\n" + "=" * 70)
    print(" RESUMEN DE DESCARGAS ".center(70))
    print("=" * 70)
    print(f"\n✓ Todas las demostraciones completadas exitosamente")
    print(f"✓ Datos almacenados en cache para uso futuro")
    print(f"✓ Total de registros procesados: {sum(df.shape[0] for df in multi_year_data.values())}")


if __name__ == "__main__":
    main()