"""
Tests para verificar que el usuario está adecuadamente informado cuando 
los DEFINE no se inicializan por sintaxis incorrecta.
"""
import pytest
from MergeSourceFile.main import process_file_sequentially
import io
import sys
from contextlib import redirect_stdout


class TestDefineErrorReporting:
    """Tests que verifican la información al usuario sobre DEFINE problemáticos."""
    
    def test_invalid_define_syntax_ignored_with_verbose(self):
        """Test que verifica que DEFINE con sintaxis inválida se reporta en modo verbose."""
        content = """DEFINE variable_mala = ;
DEFINE otra_mala =;
DEFINE = valor_sin_nombre;
DEFINE variable_buena = valor;
SELECT '&variable_buena' FROM dual;"""
        
        # Capturar output verbose
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = process_file_sequentially(content, verbose=True)
        
        verbose_output = captured_output.getvalue()
        
        # Verificar que se reportan los DEFINE ignorados
        assert "Ignorando DEFINE con sintaxis invalida" in verbose_output
        assert "variable_mala" in verbose_output
        assert "otra_mala" in verbose_output
        assert "valor_sin_nombre" in verbose_output
        
        # Verificar que el DEFINE válido funciona
        assert "SELECT 'valor' FROM dual;" in result
        
    def test_empty_string_define_works(self):
        """Test que verifica que DEFINE con string vacío funciona correctamente."""
        content = """DEFINE variable_vacia = '';
SELECT '&variable_vacia' FROM dual;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        # Un string vacío debe ser reemplazado correctamente
        assert "SELECT '' FROM dual;" in result
        
    def test_invalid_define_with_special_characters(self):
        """Test que verifica que DEFINE con caracteres especiales se reporta."""
        content = """DEFINE variable@ = valor;
DEFINE variable# = valor;
DEFINE variable_buena = valor;
SELECT '&variable_buena' FROM dual;"""
        
        # Capturar output verbose
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = process_file_sequentially(content, verbose=True)
        
        verbose_output = captured_output.getvalue()
        
        # Verificar que se reportan los DEFINE con caracteres especiales
        assert "Ignorando DEFINE con sintaxis invalida" in verbose_output
        assert "variable@" in verbose_output
        assert "variable#" in verbose_output
        
        # El DEFINE válido debe funcionar
        assert "SELECT 'valor' FROM dual;" in result
        
    def test_undefined_variable_error_clear(self):
        """Test que verifica que el error de variable indefinida es claro."""
        content = """DEFINE variable_mala = ;
SELECT '&variable_mala' FROM dual;"""
        
        # Debe fallar con un error claro
        with pytest.raises(ValueError, match="La variable 'variable_mala' se usa antes de ser definida"):
            process_file_sequentially(content, verbose=False)
            
    def test_numeric_variable_names_accepted(self):
        """Test que verifica que nombres de variables que empiezan con números se aceptan."""
        # Nota: Aunque no es estándar SQL*Plus, nuestro regex actual lo permite
        content = """DEFINE 123variable = valor;
SELECT '&123variable' FROM dual;"""
        
        # Capturar output para verificar que no se ignora
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = process_file_sequentially(content, verbose=True)
        
        verbose_output = captured_output.getvalue()
        
        # No debe aparecer como "ignorado"
        assert "Ignorando DEFINE" not in verbose_output
        # Debe definirse correctamente
        assert "Definiendo variable: 123variable = valor" in verbose_output
        # Y debe reemplazarse
        assert "SELECT 'valor' FROM dual;" in result