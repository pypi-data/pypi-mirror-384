# MergeSourceFile 

A Python tool to process SQL*Plus scripts with Jinja2 template support, resolving file inclusions and variable substitutions.

## Description

This is a Python project that includes a script capable of processing SQL*Plus scripts with Jinja2 template support. The program resolves file inclusions referenced through `@` and `@@`, performs variable substitutions defined with `DEFINE`, supports variable removal with `UNDEFINE`, allows variable redefinition throughout the script, and **now includes Jinja2 template processing** with custom filters and multiple processing strategies.

## Features

- **File Inclusion Resolution**: Processes `@` and `@@` directives to include external SQL files
- **Variable Substitution**: Handles `DEFINE` and `UNDEFINE` commands for variable management
- **Variable Redefinition**: Supports redefining variables throughout the script
- **🆕 Jinja2 Template Processing**: Full Jinja2 template support with variables, conditionals, loops, and filters
- **🆕 Custom Jinja2 Filters**: `sql_escape` for SQL injection protection and `strftime` for date formatting
- **🆕 Multiple Processing Orders**: Choose between `default`, `jinja2_first`, or `includes_last` processing strategies
- **🆕 Dynamic File Inclusion**: Use Jinja2 variables to determine which files to include
- **Tree Display**: Shows the inclusion hierarchy in a tree structure
- **Verbose Mode**: Detailed logging for debugging and understanding the processing flow

## Installation

```bash
pip install MergeSourceFile
```

## What's New in v1.1.1

- 🐛 **DEFINE Bug Fixes**: Critical fix for DEFINE statements without quotes (e.g., `DEFINE VAR = value`)
- 🔧 **Enhanced DEFINE Support**: Improved regex to handle decimal values, hyphens, and complex alphanumeric values
- 📊 **Better Error Reporting**: Verbose mode now shows ignored DEFINE statements with line numbers
- 🪟 **Windows Compatibility**: Fixed Unicode encoding issues for full Windows support
- ✅ **Robust Testing**: 17 new tests added, 56/56 tests passing including full CLI integration

## What's New in v1.1.0

- ✨ **Jinja2 Template Support**: Full integration with Jinja2 templating engine
- 🔧 **Custom Filters**: Added `sql_escape` and `strftime` filters for enhanced functionality
- 🔀 **Processing Orders**: Three different processing strategies for complex scenarios
- 🎯 **Dynamic Inclusion**: Use Jinja2 variables to conditionally include files
- 📋 **Enhanced CLI**: New command-line options for Jinja2 functionality
- 🧪 **Comprehensive Testing**: 20+ new tests ensuring reliability

## Usage

### Command Line

```bash
mergesourcefile --input input.sql --output output.sql
```

### Options

- `--input, -i`: Input SQL*Plus file to process (required)
- `--output, -o`: Output file where the result will be written (required)
- `--skip-var, -sv`: Skip variable substitution, only resolve file inclusions
- `--verbose, -v`: Enable verbose mode for detailed processing information
- `--jinja2`: Enable Jinja2 template processing
- `--jinja2-vars`: JSON string with variables for Jinja2 template processing
- `--processing-order`: Choose processing order: `default`, `jinja2_first`, or `includes_last`

### Examples

1. **Process a SQL file with full processing**:
   ```bash
   mergesourcefile -i main.sql -o merged.sql
   ```

2. **Process only file inclusions, skip variable substitution**:
   ```bash
   mergesourcefile -i main.sql -o merged.sql --skip-var
   ```

3. **Process with verbose output**:
   ```bash
   mergesourcefile -i main.sql -o merged.sql --verbose
   ```

4. **🆕 Process with Jinja2 template support**:
   ```bash
   mergesourcefile -i template.sql -o merged.sql --jinja2
   ```

5. **🆕 Process with Jinja2 variables**:
   ```bash
   mergesourcefile -i template.sql -o merged.sql --jinja2 --jinja2-vars '{"environment": "production", "table_suffix": "_prod"}'
   ```

6. **🆕 Process with Jinja2-first processing order**:
   ```bash
   mergesourcefile -i template.sql -o merged.sql --jinja2 --processing-order jinja2_first
   ```

## How It Works

### File Inclusion

- `@filename`: Includes a file relative to the original base path
- `@@filename`: Includes a file relative to the current file's directory

### Variable Substitution

#### DEFINE Syntax (Enhanced in v1.1.1)
- `DEFINE varname = 'quoted value';`: Defines with quoted value (supports spaces)
- `DEFINE varname = unquoted_value;`: Defines with unquoted value (no spaces)
- `DEFINE varname = 3.14;`: Supports decimal values
- `DEFINE varname = ABC-123;`: Supports hyphenated values
- `DEFINE varname = '';`: Supports empty string values

#### Variable Usage
- `&varname`: References a variable for substitution
- `&varname..`: Variable concatenation with period
- `UNDEFINE varname;`: Removes a variable definition

#### Error Handling (v1.1.1)
- Invalid DEFINE syntax is ignored and reported in verbose mode
- Example: `DEFINE var = ;` will be skipped with a warning
- Variables must be defined before use or an error is thrown

### 🆕 Jinja2 Template Processing

#### Basic Template Syntax
- `{{ variable }}`: Variable substitution
- `{% if condition %}...{% endif %}`: Conditional blocks
- `{% for item in list %}...{% endfor %}`: Loop blocks
- `{# comment #}`: Template comments

#### Custom Filters
- `sql_escape`: Escapes single quotes for SQL safety
  ```sql
  SELECT * FROM users WHERE name = '{{ user_name | sql_escape }}';
  ```
- `strftime`: Formats datetime objects
  ```sql
  -- Generated on {{ now() | strftime('%Y-%m-%d %H:%M:%S') }}
  ```

#### Processing Orders
1. **default**: File Inclusions → Jinja2 Templates → SQL Variables
2. **jinja2_first**: Jinja2 Templates → File Inclusions → SQL Variables
3. **includes_last**: SQL Variables → Jinja2 Templates → File Inclusions

#### Dynamic File Inclusion Example
```sql
-- Using jinja2_first order to dynamically determine which files to include
{% if environment == 'production' %}
@prod_config.sql
{% else %}
@dev_config.sql
{% endif %}
```

## Complete Example

### Input Template (`template.sql`)
```sql
{# This is a Jinja2 comment #}
-- Database setup for {{ environment | upper }} environment
-- Generated on {{ now() | strftime('%Y-%m-%d %H:%M:%S') }}

{% if environment == 'production' %}
@production_settings.sql
{% else %}
@development_settings.sql
{% endif %}

DEFINE db_name = '{{ database_name }}';
DEFINE table_prefix = '{{ table_prefix }}';

CREATE TABLE &table_prefix._users (
    id NUMBER PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    email VARCHAR2(255) UNIQUE,
    created_date DATE DEFAULT SYSDATE
);

{% for table in additional_tables %}
CREATE TABLE &table_prefix._{{ table.name }} (
    id NUMBER PRIMARY KEY,
    {% for column in table.columns -%}
    {{ column.name }} {{ column.type }}{% if not loop.last %},{% endif %}
    {% endfor %}
);
{% endfor %}

-- Insert sample data with escaped values
INSERT INTO &table_prefix._users (name, email) 
VALUES ('{{ sample_user | sql_escape }}', '{{ sample_email | sql_escape }}');
```

### Command
```bash
mergesourcefile -i template.sql -o output.sql --jinja2 --processing-order jinja2_first --jinja2-vars '{
  "environment": "production",
  "database_name": "MYAPP_DB",
  "table_prefix": "APP",
  "sample_user": "John O'\''Brien",
  "sample_email": "john@example.com",
  "additional_tables": [
    {
      "name": "products",
      "columns": [
        {"name": "title", "type": "VARCHAR2(200)"},
        {"name": "price", "type": "NUMBER(10,2)"}
      ]
    }
  ]
}'
```

## Migration from v1.0.x

If you're upgrading from a previous version, your existing scripts will continue to work without any changes. The new Jinja2 functionality is **completely optional** and requires explicit activation with the `--jinja2` flag.

### Backward Compatibility
- All existing command-line options work exactly as before
- File inclusion (`@`, `@@`) behavior is unchanged
- Variable substitution (`DEFINE`, `UNDEFINE`) works as expected
- No breaking changes to existing functionality

### Gradual Adoption
You can gradually adopt Jinja2 features:
1. Start with simple variable substitution: `{{ variable }}`
2. Add conditional logic: `{% if condition %}`
3. Use loops for repetitive structures: `{% for item in list %}`
4. Apply custom filters: `{{ value | sql_escape }}`
5. Experiment with processing orders for complex scenarios

## Best Practices

### When to Use Each Processing Order

- **default**: Best for most use cases where Jinja2 templates don't need to generate file inclusion directives
- **jinja2_first**: Use when Jinja2 templates need to conditionally determine which files to include
- **includes_last**: Use when you need SQL variables to be processed before Jinja2 templates and file inclusions

### Security Considerations

Always use the `sql_escape` filter when inserting user-provided data:
```sql
-- ❌ Vulnerable to SQL injection
SELECT * FROM users WHERE name = '{{ user_input }}';

-- ✅ Safe with sql_escape filter
SELECT * FROM users WHERE name = '{{ user_input | sql_escape }}';
```

### Performance Tips

- Use `--skip-var` if you don't need SQL variable processing
- For large projects, consider splitting templates into smaller, focused files
- Use Jinja2 comments `{# comment #}` instead of SQL comments for template-specific notes

## Platform Compatibility

### Operating Systems
- ✅ **Linux**: Full support with all features
- ✅ **macOS**: Full support with all features  
- ✅ **Windows**: Full support with enhanced compatibility (v1.1.1)
  - Fixed Unicode encoding issues for CLI operations
  - All 56 tests pass successfully on Windows systems
  - Proper error codes and file path handling

### Python Versions
- Python 3.8+
- Tested with Python 3.9, 3.10, 3.11, 3.12, 3.14

### Character Encoding
- Primary support: UTF-8 (recommended)
- Windows compatibility: ASCII-safe output for CLI operations
- All text files should use UTF-8 encoding for best results

## Troubleshooting

### Common Issues

1. **DEFINE syntax errors** (Fixed in v1.1.1):
   - ✅ `DEFINE VAR = value` now works correctly (was broken in v1.1.0)
   - ✅ Both quoted and unquoted DEFINE values supported
   - Use verbose mode (`--verbose`) to see ignored invalid DEFINE statements

2. **Jinja2 syntax errors**: Ensure proper template syntax with matching braces and tags
3. **Variable not found**: Check that all variables are provided via `--jinja2-vars`
4. **File inclusion issues**: Verify file paths and choose appropriate processing order
5. **Encoding problems** (Fixed in v1.1.1): 
   - ✅ Windows encoding issues resolved
   - Ensure all files use consistent encoding (UTF-8 recommended)
   - CLI now works properly on all Windows systems

### Windows-Specific Issues (Resolved in v1.1.1)
- ✅ **Unicode character display**: Fixed issues with special characters in CLI output
- ✅ **File path resolution**: Enhanced path handling for nested file inclusions
- ✅ **Exit codes**: CLI now returns proper error codes (1 for errors, 0 for success)

### Debug Mode

Use `--verbose` flag to see detailed processing information:
```bash
mergesourcefile -i template.sql -o output.sql --jinja2 --verbose
```

## License

This project is licensed under the MIT License.  
You are free to use, copy, modify, and distribute this software, provided that the copyright notice and this permission are included.  
The software is provided "as is", without warranty of any kind.

## Author

Alejandro G.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
