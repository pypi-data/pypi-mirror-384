"""
Tests para la funcionalidad de plantillas Jinja2 en MergeSourceFile
"""
import pytest
from pathlib import Path
from MergeSourceFile.main import (
    process_jinja2_template,
    process_file_with_jinja2_replacements,
    process_content_with_both_engines
)


class TestJinja2Processing:
    """Tests para el procesamiento de plantillas Jinja2"""
    
    def test_simple_variable_substitution(self):
        """Test para sustitución simple de variables con Jinja2"""
        template = "SELECT * FROM {{ table_name }} WHERE id = {{ user_id }};"
        variables = {
            'table_name': 'usuarios',
            'user_id': 123
        }
        
        result = process_jinja2_template(template, variables)
        
        assert result == "SELECT * FROM usuarios WHERE id = 123;"
    
    def test_conditional_rendering(self):
        """Test para renderizado condicional"""
        template = """SELECT * FROM usuarios
{% if include_email %}
, email
{% endif %}
WHERE active = 1;"""
        
        # Test con condición verdadera
        variables = {'include_email': True}
        result = process_jinja2_template(template, variables)
        assert ", email" in result
        assert "WHERE active = 1;" in result
        
        # Test con condición falsa
        variables = {'include_email': False}
        result = process_jinja2_template(template, variables)
        assert ", email" not in result
        assert "WHERE active = 1;" in result
    
    def test_loop_rendering(self):
        """Test para bucles en plantillas"""
        template = """SELECT * FROM usuarios WHERE id IN (
{% for user_id in user_ids -%}
{{ user_id }}{% if not loop.last %}, {% endif %}
{% endfor -%}
);"""
        
        variables = {
            'user_ids': [1, 2, 3, 4, 5]
        }
        
        result = process_jinja2_template(template, variables)
        # Verificar que todos los números estén presentes
        for i in range(1, 6):
            assert str(i) in result
        # Verificar que haya exactamente 4 comas para 5 elementos
        assert result.count(",") == 4
    
    def test_filters(self):
        """Test para filtros de Jinja2"""
        template = """-- Usuario: {{ username | upper }}
SELECT * FROM {{ table_name | lower }} 
WHERE created_date > '{{ date_value | strftime('%Y-%m-%d') }}';"""
        
        from datetime import datetime
        variables = {
            'username': 'alejandro',
            'table_name': 'USUARIOS',
            'date_value': datetime(2023, 12, 15)
        }
        
        result = process_jinja2_template(template, variables)
        assert "-- Usuario: ALEJANDRO" in result
        assert "FROM usuarios" in result
        assert "2023-12-15" in result
    
    def test_nested_structures(self):
        """Test para estructuras anidadas"""
        template = """-- Configuración de tablas
{% for schema in schemas %}
-- Schema: {{ schema.name }}
{% for table in schema.tables %}
CREATE TABLE {{ schema.name }}.{{ table.name }} (
{% for column in table.columns -%}
    {{ column.name }} {{ column.type }}{% if not loop.last %},{% endif %}
{% endfor %}
);
{% endfor %}
{% endfor %}"""
        
        variables = {
            'schemas': [
                {
                    'name': 'public',
                    'tables': [
                        {
                            'name': 'usuarios',
                            'columns': [
                                {'name': 'id', 'type': 'INTEGER'},
                                {'name': 'nombre', 'type': 'VARCHAR(100)'},
                                {'name': 'email', 'type': 'VARCHAR(255)'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = process_jinja2_template(template, variables)
        assert "-- Schema: public" in result
        assert "CREATE TABLE public.usuarios" in result
        assert "id INTEGER," in result
        assert "email VARCHAR(255)" in result
    
    def test_missing_variable_error(self):
        """Test para error cuando falta una variable"""
        template = "SELECT * FROM {{ missing_table }};"
        variables = {}
        
        with pytest.raises(Exception):  # Jinja2 debería lanzar un error
            process_jinja2_template(template, variables)
    
    def test_invalid_template_syntax(self):
        """Test para sintaxis inválida de plantilla"""
        template = "SELECT * FROM {{ invalid syntax };"
        variables = {}
        
        with pytest.raises(Exception):  # Error de sintaxis de Jinja2
            process_jinja2_template(template, variables)
    
    def test_empty_template(self):
        """Test para plantilla vacía"""
        template = ""
        variables = {}
        
        result = process_jinja2_template(template, variables)
        assert result == ""
    
    def test_template_without_variables(self):
        """Test para plantilla sin variables de Jinja2"""
        template = "SELECT * FROM usuarios WHERE active = 1;"
        variables = {}
        
        result = process_jinja2_template(template, variables)
        assert result == template
    
    def test_custom_filters(self):
        """Test para filtros personalizados"""
        template = "SELECT * FROM {{ table_name | sql_escape }};"
        variables = {
            'table_name': "test'table"
        }
        
        result = process_jinja2_template(template, variables)
        assert "test''table" in result  # SQL escape doble quote


class TestJinja2Integration:
    """Tests para integración de Jinja2 con el procesamiento existente"""
    
    def test_jinja2_with_file_includes(self, temp_dir):
        """Test para combinar Jinja2 con inclusiones de archivos"""
        # Crear archivo principal con plantilla Jinja2
        main_file = temp_dir / "main.sql"
        main_file.write_text("""-- Archivo principal
@@included.sql
SELECT * FROM {{ main_table }} WHERE id = {{ user_id }};""", encoding='utf-8')
        
        # Crear archivo incluido
        included_file = temp_dir / "included.sql"
        included_file.write_text("""-- Archivo incluido
CREATE TABLE {{ main_table }} (
    id INTEGER,
    name VARCHAR({{ name_length }})
);""", encoding='utf-8')
        
        variables = {
            'main_table': 'usuarios',
            'user_id': 123,
            'name_length': 100
        }
        
        result = process_file_with_jinja2_replacements(str(main_file), variables)
        
        assert "CREATE TABLE usuarios" in result
        assert "VARCHAR(100)" in result
        assert "WHERE id = 123" in result
    
    def test_jinja2_with_sql_variables(self):
        """Test para combinar Jinja2 con variables SQL existentes"""
        content = """DEFINE schema_name='public'
-- Plantilla Jinja2 con variable SQL
SELECT * FROM &schema_name..{{ table_name }} 
WHERE {{ where_condition }};"""
        
        variables = {
            'table_name': 'usuarios',
            'where_condition': 'active = 1'
        }
        
        result = process_content_with_both_engines(content, variables)
        
        # Resultado esperado: primero Jinja2, luego variables SQL
        assert "SELECT * FROM public.usuarios" in result
        assert "WHERE active = 1" in result


class TestJinja2Configuration:
    """Tests para configuración y opciones de Jinja2"""
    
    def test_strict_undefined_mode(self):
        """Test para modo estricto de variables indefinidas"""
        template = "SELECT * FROM {{ undefined_var }};"
        variables = {}
        
        # En modo estricto debería fallar
        with pytest.raises(Exception):
            process_jinja2_template(template, variables, strict_undefined=True)
    
    def test_custom_delimiters(self):
        """Test para delimitadores personalizados"""
        template = "SELECT * FROM <% table_name %> WHERE id = <% user_id %>;"
        variables = {
            'table_name': 'usuarios',
            'user_id': 123
        }
        
        # Con delimitadores personalizados
        result = process_jinja2_template(
            template, 
            variables, 
            variable_start_string='<%', 
            variable_end_string='%>'
        )
        assert result == "SELECT * FROM usuarios WHERE id = 123;"