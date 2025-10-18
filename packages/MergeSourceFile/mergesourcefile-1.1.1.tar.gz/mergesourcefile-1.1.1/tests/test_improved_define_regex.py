"""
Tests para la mejora del regex DEFINE que soporta valores con decimales,
guiones y otros caracteres especiales.
"""
import pytest
from MergeSourceFile.main import process_file_sequentially


class TestImprovedDefineRegex:
    """Tests para verificar que el regex mejorado maneja correctamente todos los tipos de valores."""
    
    def test_define_decimal_values(self):
        """Test que verifica que los valores decimales se procesan correctamente."""
        content = """DEFINE precio = 3.14;
DEFINE ratio = 0.75;
SELECT &precio FROM dual;
SELECT &ratio FROM dual;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        # Los valores decimales deben ser reemplazados
        assert "SELECT 3.14 FROM dual;" in result
        assert "SELECT 0.75 FROM dual;" in result
        
    def test_define_hyphenated_values(self):
        """Test que verifica que los valores con guiones se procesan correctamente."""
        content = """DEFINE codigo = ABC-123;
DEFINE version = v1-2-3;
INSERT INTO tabla VALUES ('&codigo', '&version');"""
        
        result = process_file_sequentially(content, verbose=False)
        
        # Los valores con guiones deben ser reemplazados
        assert "INSERT INTO tabla VALUES ('ABC-123', 'v1-2-3');" in result
        
    def test_define_alphanumeric_with_underscores(self):
        """Test que verifica valores alfanuméricos con guiones bajos."""
        content = """DEFINE tabla_audit = log_audit_2024;
DEFINE schema_name = DB_PROD;
CREATE TABLE &schema_name..&tabla_audit (id INT);"""
        
        result = process_file_sequentially(content, verbose=False)
        
        assert "CREATE TABLE DB_PROD.log_audit_2024 (id INT);" in result
        
    def test_define_mixed_formats_compatibility(self):
        """Test que verifica que todos los formatos funcionan juntos."""
        content = """DEFINE texto = 'valor con espacios';
DEFINE numero = 42;
DEFINE decimal = 3.14;
DEFINE codigo = ABC-123;
DEFINE variable = valor_simple;
SELECT '&texto', &numero, &decimal, '&codigo', '&variable' FROM dual;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        expected = "SELECT 'valor con espacios', 42, 3.14, 'ABC-123', 'valor_simple' FROM dual;"
        assert expected in result
        
    def test_backward_compatibility_with_original_bug_fix(self):
        """Test que verifica que el ejemplo original del bug sigue funcionando."""
        content = """DEFINE NOMBRE_TABLA_LOG = AUDIT_LOG;
DEFINE ESQUEMA_LOG = DBO;
CREATE TABLE &ESQUEMA_LOG..&NOMBRE_TABLA_LOG (id INT);"""
        
        result = process_file_sequentially(content, verbose=False)
        
        assert "CREATE TABLE DBO.AUDIT_LOG (id INT);" in result