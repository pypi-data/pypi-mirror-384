"""
Tests para diferentes órdenes de procesamiento en MergeSourceFile
"""
import pytest
from pathlib import Path
from MergeSourceFile.main import process_file_with_jinja2_replacements


class TestProcessingOrders:
    """Tests para diferentes órdenes de procesamiento"""
    
    def test_default_order_includes_first(self, temp_dir):
        """Test para orden por defecto: Inclusiones → Jinja2 → Variables SQL"""
        # Crear archivo principal
        main_file = temp_dir / "main.sql"
        main_file.write_text("""DEFINE schema='public'
@@config.sql
SELECT * FROM &schema..{{ table_name }};""", encoding='utf-8')
        
        # Crear archivo incluido con plantilla Jinja2
        config_file = temp_dir / "config.sql"
        config_file.write_text("""-- Configuración para {{ environment }}
CREATE SCHEMA IF NOT EXISTS {{ schema_name }};""", encoding='utf-8')
        
        variables = {
            'environment': 'production',
            'schema_name': 'prod_schema',
            'table_name': 'usuarios'
        }
        
        result = process_file_with_jinja2_replacements(
            str(main_file), variables, processing_order='default'
        )
        
        # Verificar que las inclusiones se resolvieron primero, luego Jinja2, luego SQL
        assert "production" in result  # Evitar problemas de encoding
        assert "CREATE SCHEMA IF NOT EXISTS prod_schema" in result
        assert "SELECT * FROM public.usuarios" in result
    
    def test_jinja2_first_order(self, temp_dir):
        """Test para orden Jinja2 → Inclusiones → Variables SQL"""
        # Archivo principal con plantilla que determina qué incluir
        main_file = temp_dir / "main.sql"
        main_file.write_text("""DEFINE env='{{ environment }}'
@@{{ config_file }}
SELECT * FROM &env..usuarios;""", encoding='utf-8')
        
        # Crear archivos de configuración
        prod_config = temp_dir / "prod_config.sql"
        prod_config.write_text("""-- Configuración de producción
CREATE TABLE usuarios (id INT, name VARCHAR(100));""", encoding='utf-8')
        
        dev_config = temp_dir / "dev_config.sql" 
        dev_config.write_text("""-- Configuración de desarrollo
CREATE TABLE usuarios (id INT, name VARCHAR(50));""", encoding='utf-8')
        
        variables = {
            'environment': 'production',
            'config_file': 'prod_config.sql'
        }
        
        result = process_file_with_jinja2_replacements(
            str(main_file), variables, processing_order='jinja2_first'
        )
        
        # Verificar que se incluyó el archivo correcto determinado por Jinja2
        assert "producción" in result or "production" in result  # Evitar problemas de encoding
        assert "VARCHAR(100)" in result  # prod tiene VARCHAR(100)
        assert "VARCHAR(50)" not in result  # dev tiene VARCHAR(50)
        assert "SELECT * FROM production.usuarios" in result
    
    def test_includes_last_order(self, temp_dir):
        """Test para orden Variables SQL → Jinja2 → Inclusiones"""
        # Caso más simple para includes_last - sin variables SQL complejas
        main_file = temp_dir / "main.sql"
        main_file.write_text("""-- Tabla: {{ table_prefix }}
@@create_{{ table_type }}.sql""", encoding='utf-8')
        
        # Crear archivos de creación
        create_simple = temp_dir / "create_simple.sql"
        create_simple.write_text("""CREATE TABLE usuarios_simple (id INT);""", encoding='utf-8')
        
        create_complex = temp_dir / "create_complex.sql"
        create_complex.write_text("""CREATE TABLE usuarios_complex (id INT, name VARCHAR(100), email VARCHAR(255));""", encoding='utf-8')
        
        variables = {
            'table_prefix': 'app',
            'table_type': 'complex'
        }
        
        result = process_file_with_jinja2_replacements(
            str(main_file), variables, processing_order='includes_last'
        )
        
        # Verificar que Jinja2 determinó qué incluir
        assert "-- Tabla: app" in result
        assert "CREATE TABLE usuarios_complex" in result  # incluyó complex
        assert "usuarios_simple" not in result  # no incluyó simple
    
    def test_complex_scenario_all_orders(self, temp_dir):
        """Test que compara los tres órdenes en un escenario complejo"""
        # Archivo principal complejo
        main_file = temp_dir / "main.sql"
        main_file.write_text("""DEFINE db_env='{{ environment }}'
-- Database: &db_env
@@{{ config_file }}
CREATE TABLE {{ table_name }} (id INT);
SELECT * FROM &db_env..{{ table_name }};""", encoding='utf-8')
        
        # Archivo de configuración
        config_file = temp_dir / "app_config.sql"
        config_file.write_text("""-- Config for {{ environment }}
DEFINE table_name='app_table'""", encoding='utf-8')
        
        variables = {
            'environment': 'staging',
            'config_file': 'app_config.sql',
            'table_name': 'usuarios'
        }
        
        # Test orden por defecto - esperamos que falle con inclusiones dinámicas
        try:
            result_default = process_file_with_jinja2_replacements(
                str(main_file), variables, processing_order='default'
            )
        except FileNotFoundError:
            result_default = "ERROR: No puede resolver inclusiones dinámicas"
        
        # Test Jinja2 primero
        result_jinja2_first = process_file_with_jinja2_replacements(
            str(main_file), variables, processing_order='jinja2_first'
        )
        
        # Test inclusiones al final
        result_includes_last = process_file_with_jinja2_replacements(
            str(main_file), variables, processing_order='includes_last'
        )
        
        # Verificar diferencias esperadas
        print("Default:", result_default)
        print("Jinja2 First:", result_jinja2_first)
        print("Includes Last:", result_includes_last)
        
        # Verificar que jinja2_first e includes_last funcionan
        for result in [result_jinja2_first, result_includes_last]:
            assert "staging" in result
            assert "usuarios" in result
        
        # Verificar que default falla como se esperaba
        assert "ERROR" in result_default
    
    def test_error_handling_invalid_order(self, temp_dir):
        """Test para manejo de errores con orden inválido"""
        main_file = temp_dir / "main.sql"
        main_file.write_text("SELECT 1;", encoding='utf-8')
        
        # El parámetro invalid_order no existe, debería usar default
        result = process_file_with_jinja2_replacements(
            str(main_file), {}, processing_order='invalid_order'
        )
        
        # Debería procesarse con orden por defecto
        assert "SELECT 1;" in result


class TestProcessingOrderIntegration:
    """Tests de integración para órdenes de procesamiento"""
    
    def test_recursive_includes_with_jinja2(self, temp_dir):
        """Test para casos recursivos básicos"""
        # Caso más simple: solo verificar que jinja2_first incluye el archivo correcto
        main_file = temp_dir / "main.sql"
        main_file.write_text("""-- Main file
@@level1_{{ config_type }}.sql
SELECT * FROM final_table;""", encoding='utf-8')
        
        # Nivel 1 - sin plantillas complejas anidadas
        level1_file = temp_dir / "level1_advanced.sql"
        level1_file.write_text("""-- Level 1 config
CREATE TABLE intermediate (id INT);""", encoding='utf-8')
        
        variables = {
            'config_type': 'advanced'
        }
        
        result = process_file_with_jinja2_replacements(
            str(main_file), variables, processing_order='jinja2_first'
        )
        
        # Verificar que se incluyó el archivo correcto
        assert "-- Level 1 config" in result
        assert "CREATE TABLE intermediate" in result
        assert "SELECT * FROM final_table" in result