import pytest
import tempfile
import os
from pathlib import Path
from MergeSourceFile.main import process_file_with_replacements


def test_define_without_quotes_bug_fix():
    """
    Test para el bug donde las variables DEFINE sin comillas no se procesaban correctamente.
    
    Este test reproduce el escenario donde un archivo de configuración define variables
    sin comillas y archivos posteriores las usan, lo que causaba errores de 
    "variable se usa antes de ser definida".
    """
    
    # Crear archivos temporales
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_dir = os.getcwd()
        
        try:
            # Cambiar al directorio temporal para que las rutas relativas funcionen
            os.chdir(temp_path)
            
            # Archivo principal
            main_file = temp_path / "main.sql"
            main_file.write_text("""-- Script principal
@config.sql
@table.sql
""")
            
            # Archivo de configuración (sin comillas en DEFINE)
            config_file = temp_path / "config.sql"
            config_file.write_text("""-- Configuración
DEFINE TABLE_NAME = users
DEFINE SCHEMA_NAME = prod_schema
""")
            
            # Archivo que usa las variables
            table_file = temp_path / "table.sql"
            table_file.write_text("""-- Creación de tabla
CREATE TABLE &SCHEMA_NAME..&TABLE_NAME (
    id NUMBER PRIMARY KEY,
    name VARCHAR2(100)
);
""")
            
            # Ejecutar el procesamiento
            result = process_file_with_replacements(str(main_file), skip_var=False, verbose=False)
            
            # Verificar que las sustituciones se hicieron correctamente
            assert "CREATE TABLE prod_schema.users (" in result
            assert "&TABLE_NAME" not in result
            assert "&SCHEMA_NAME" not in result
            assert "DEFINE TABLE_NAME" not in result
            assert "DEFINE SCHEMA_NAME" not in result
            
        finally:
            # Restaurar el directorio original
            os.chdir(original_dir)


def test_define_with_quotes_still_works():
    """
    Test para asegurar que variables DEFINE con comillas siguen funcionando.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_dir = os.getcwd()
        
        try:
            os.chdir(temp_path)
            
            # Archivo principal
            main_file = temp_path / "main.sql"
            main_file.write_text("""-- Script principal
@config.sql
@table.sql
""")
            
            # Archivo de configuración (con comillas en DEFINE)
            config_file = temp_path / "config.sql"
            config_file.write_text("""-- Configuración
DEFINE TABLE_NAME = 'users_with_quotes'
DEFINE SCHEMA_NAME = 'test_schema'
""")
            
            # Archivo que usa las variables
            table_file = temp_path / "table.sql"
            table_file.write_text("""-- Creación de tabla
CREATE TABLE &SCHEMA_NAME..&TABLE_NAME (
    id NUMBER PRIMARY KEY,
    name VARCHAR2(100)
);
""")
            
            # Ejecutar el procesamiento
            result = process_file_with_replacements(str(main_file), skip_var=False, verbose=False)
            
            # Verificar que las sustituciones se hicieron correctamente
            assert "CREATE TABLE test_schema.users_with_quotes (" in result
            assert "&TABLE_NAME" not in result
            assert "&SCHEMA_NAME" not in result
            
        finally:
            os.chdir(original_dir)


def test_mixed_define_formats():
    """
    Test para verificar que se pueden mezclar variables con y sin comillas.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_dir = os.getcwd()
        
        try:
            os.chdir(temp_path)
            
            # Archivo principal
            main_file = temp_path / "main.sql"
            main_file.write_text("""-- Script principal
@config.sql
@script.sql
""")
            
            # Archivo de configuración (mezcla de formatos)
            config_file = temp_path / "config.sql"
            config_file.write_text("""-- Configuración mixta
DEFINE VAR_WITH_QUOTES = 'value_with_quotes'
DEFINE VAR_WITHOUT_QUOTES = value_without_quotes
DEFINE VAR_NUMBER = 123
""")
            
            # Archivo que usa las variables
            script_file = temp_path / "script.sql"
            script_file.write_text("""-- Uso de variables
SELECT '&VAR_WITH_QUOTES' as quoted_var,
       '&VAR_WITHOUT_QUOTES' as unquoted_var,
       &VAR_NUMBER as number_var
FROM dual;
""")
            
            # Ejecutar el procesamiento
            result = process_file_with_replacements(str(main_file), skip_var=False, verbose=False)
            
            # Verificar que las sustituciones se hicieron correctamente
            assert "SELECT 'value_with_quotes' as quoted_var," in result
            assert "'value_without_quotes' as unquoted_var," in result
            assert "123 as number_var" in result
            
        finally:
            os.chdir(original_dir)


if __name__ == "__main__":
    # Ejecutar tests individuales para debugging
    test_define_without_quotes_bug_fix()
    test_define_with_quotes_still_works()
    test_mixed_define_formats()
    print("✅ Todos los tests del bug fix pasaron correctamente!")