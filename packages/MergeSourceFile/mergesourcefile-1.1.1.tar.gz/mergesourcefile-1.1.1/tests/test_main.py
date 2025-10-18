"""
Tests para las funciones principales de MergeSourceFile
"""
import pytest
from pathlib import Path
from MergeSourceFile.main import parse_sqlplus_file, process_file_sequentially


class TestParseSQL:
    """Tests para la función parse_sqlplus_file"""
    
    def test_parse_simple_file(self, sample_sql_file):
        """Test para procesar un archivo SQL simple"""
        result = parse_sqlplus_file(str(sample_sql_file), verbose=False)
        
        assert "-- Archivo de prueba" in result
        assert "DEFINE var1='valor1'" in result
        assert "SELECT '&var1' as col1" in result
    
    def test_parse_file_with_includes(self, sql_with_includes):
        """Test para procesar archivos con inclusiones"""
        main_file = sql_with_includes['main']
        base_path = main_file.parent
        
        result = parse_sqlplus_file(str(main_file), str(base_path), verbose=False)
        
        # Verificar que incluye el contenido de los archivos incluidos
        assert "-- Include 1" in result
        assert "CREATE TABLE tabla1" in result
        assert "-- Include 2" in result
        assert "CREATE TABLE tabla2" in result
        assert "SELECT * FROM tabla_principal" in result
    
    def test_parse_nonexistent_file(self):
        """Test para manejar archivos que no existen"""
        with pytest.raises(FileNotFoundError):
            parse_sqlplus_file("archivo_inexistente.sql")


class TestVariableSubstitution:
    """Tests para la función process_file_sequentially"""
    
    def test_simple_substitution(self):
        """Test para sustitución simple de variables"""
        content = """DEFINE var1='valor1'
SELECT '&var1' FROM dual;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        assert "DEFINE var1=valor1" not in result  # Las líneas DEFINE no deben aparecer
        assert "SELECT 'valor1' FROM dual;" in result
    
    def test_multiple_variables(self):
        """Test para múltiples variables"""
        content = """DEFINE var1='valor1'
DEFINE var2='valor2'
SELECT '&var1', '&var2' FROM dual;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        assert "SELECT 'valor1', 'valor2' FROM dual;" in result
    
    def test_variable_redefinition(self):
        """Test para redefinición de variables"""
        content = """DEFINE var1='inicial'
SELECT '&var1' FROM tabla1;
DEFINE var1='nuevo'
SELECT '&var1' FROM tabla2;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        lines = result.strip().split('\n')
        assert "SELECT 'inicial' FROM tabla1;" in lines
        assert "SELECT 'nuevo' FROM tabla2;" in lines
    
    def test_undefine_variable(self):
        """Test para UNDEFINE de variables"""
        content = """DEFINE var1='valor1'
SELECT '&var1' FROM tabla1;
UNDEFINE var1;
SELECT '&var1' FROM tabla2;"""
        
        # Esto debería fallar porque usa una variable indefinida después de UNDEFINE
        with pytest.raises(ValueError, match="se usa antes de ser definida"):
            process_file_sequentially(content, verbose=False)
    
    def test_undefined_variable_error(self):
        """Test para error cuando se usa variable no definida"""
        content = "SELECT '&variable_no_definida' FROM dual;"
        
        with pytest.raises(ValueError, match="se usa antes de ser definida"):
            process_file_sequentially(content, verbose=False)
    
    def test_comments_are_preserved(self):
        """Test para verificar que los comentarios se preservan"""
        content = """-- Este es un comentario
DEFINE var1='valor1'
SELECT '&var1' FROM dual; -- Comentario al final"""
        
        result = process_file_sequentially(content, verbose=False)
        
        assert "-- Este es un comentario" in result
        assert "-- Comentario al final" in result
    
    def test_variable_with_dots(self):
        """Test para variables con puntos concatenados"""
        content = """DEFINE var1='tabla'
SELECT * FROM &var1..datos;"""
        
        result = process_file_sequentially(content, verbose=False)
        
        assert "SELECT * FROM tabla.datos;" in result


class TestEdgeCases:
    """Tests para casos especiales"""
    
    def test_empty_file(self, temp_dir):
        """Test para archivo vacío"""
        empty_file = temp_dir / "empty.sql"
        empty_file.write_text("", encoding='utf-8')
        
        result = parse_sqlplus_file(str(empty_file), verbose=False)
        assert result == ""
    
    def test_file_with_only_comments(self, temp_dir):
        """Test para archivo solo con comentarios"""
        comment_file = temp_dir / "comments.sql"
        comment_file.write_text("-- Solo comentarios\n-- Mas comentarios", encoding='utf-8')
        
        result = parse_sqlplus_file(str(comment_file), verbose=False)
        assert "-- Solo comentarios" in result
        assert "-- Mas comentarios" in result
    
    def test_define_without_quotes(self):
        """Test para DEFINE sin comillas - ahora debería funcionar después del bug fix"""
        content = "DEFINE var1=valor_sin_comillas\nSELECT '&var1' FROM dual;"
        
        # Después del bug fix, esto debería funcionar correctamente
        result = process_file_sequentially(content, verbose=False)
        assert "SELECT 'valor_sin_comillas' FROM dual;" in result