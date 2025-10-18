"""
Tests para verificar el comportamiento con espacios en valores DEFINE.
Documenta que valores con espacios requieren comillas (estándar SQL*Plus).
"""
import pytest
from MergeSourceFile.main import process_file_sequentially


class TestDefineSpaceHandling:
    """Tests que documentan el manejo correcto de espacios en valores DEFINE."""
    
    def test_define_with_spaces_requires_quotes(self):
        """Test que verifica que valores con espacios requieren comillas."""
        # Contenido con espacios sin comillas (no debe funcionar)
        content_invalid = """DEFINE mensaje = Hola mundo;
SELECT '&mensaje' FROM dual;"""
        
        # Esto debe fallar con "variable not defined"
        with pytest.raises(ValueError, match="La variable 'mensaje' se usa antes de ser definida"):
            process_file_sequentially(content_invalid, verbose=False)
    
    def test_define_with_spaces_works_with_quotes(self):
        """Test que verifica que valores con espacios funcionan con comillas."""
        content_valid = """DEFINE mensaje = 'Hola mundo';
DEFINE ruta = 'C:\\Program Files\\App';
SELECT '&mensaje' FROM dual;
BACKUP TO '&ruta';"""
        
        result = process_file_sequentially(content_valid, verbose=False)
        
        # Los valores con espacios deben ser reemplazados correctamente
        assert "SELECT 'Hola mundo' FROM dual;" in result
        assert "BACKUP TO 'C:\\Program Files\\App';" in result
    
    def test_mixed_quoted_unquoted_values(self):
        """Test que verifica que se pueden mezclar valores con y sin comillas."""
        content = """DEFINE numero = 42;
DEFINE mensaje = 'Hola mundo';
DEFINE codigo = ABC123;
SELECT &numero, '&mensaje', '&codigo' FROM dual;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        expected = "SELECT 42, 'Hola mundo', 'ABC123' FROM dual;"
        assert expected in result
    
    def test_sqlplus_compliance_documentation(self):
        """Test que documenta el cumplimiento con SQL*Plus estándar."""
        # Este comportamiento es correcto según el estándar SQL*Plus:
        # - Valores simples sin espacios: no requieren comillas
        # - Valores con espacios: requieren comillas
        # - Espacios actúan como separadores de tokens
        
        valid_content = """DEFINE simple = valor;
DEFINE complejo = 'valor con espacios';
DEFINE numero = 123;
SELECT '&simple', '&complejo', &numero FROM dual;"""
        
        result = process_file_sequentially(valid_content, verbose=False)
        expected = "SELECT 'valor', 'valor con espacios', 123 FROM dual;"
        assert expected in result