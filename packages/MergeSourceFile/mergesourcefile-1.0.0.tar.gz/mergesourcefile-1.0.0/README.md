# MergeSourceFile 

A Python tool to process SQL*Plus scripts, resolving file inclusions and variable substitutions.

## Descripción

Este es un proyecto Python que incluye un script capaz de procesar scripts de SQL*Plus. El programa resuelve las inclusiones de archivos referenciados mediante `@` y `@@`, realiza sustituciones de variables definidas con `DEFINE`, soporta la eliminación de variables con `UNDEFINE`, y permite la redefinición de variables a lo largo del script.

## Features

- **File Inclusion Resolution**: Processes `@` and `@@` directives to include external SQL files
- **Variable Substitution**: Handles `DEFINE` and `UNDEFINE` commands for variable management
- **Variable Redefinition**: Supports redefining variables throughout the script
- **Tree Display**: Shows the inclusion hierarchy in a tree structure
- **Verbose Mode**: Detailed logging for debugging and understanding the processing flow

## Installation

```bash
pip install MergeSourceFile
```

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

## How It Works

### File Inclusion

- `@filename`: Includes a file relative to the original base path
- `@@filename`: Includes a file relative to the current file's directory

### Variable Substitution

- `DEFINE varname = 'value';`: Defines or redefines a variable
- `&varname`: References a variable for substitution
- `&varname..`: Variable concatenation with period
- `UNDEFINE varname;`: Removes a variable definition

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Alejandro G.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
