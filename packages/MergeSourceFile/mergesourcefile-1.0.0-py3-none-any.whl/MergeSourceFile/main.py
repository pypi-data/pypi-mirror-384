# MIT License
# 
# Copyright (c) 2023 Alejandro G.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import argparse
from pathlib import Path

# Sobrescribir la clase ArgumentParser para modificar los mensajes predeterminados
class CustomArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format_help(self):
        help_text = super().format_help()
        # Reemplazar el mensaje de ayuda predeterminado en inglés con español
        help_text = help_text.replace("show this help message and exit", "muestra este mensaje de ayuda y sale")
        return help_text


# 1. Función para leer y resolver inclusiones @ y @@, construyendo un árbol
def parse_sqlplus_file(input_file, base_path='.', tree_depth=0, verbose=False):
    
    def read_file(file_path, base_path, tree_depth):
        full_path = Path(base_path) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {full_path}")
        
        # Crear un prefijo basado en la profundidad del árbol
        prefix = "    " * tree_depth + "└── "
        
        # Mostrar el archivo que se está procesando con el nuevo estilo
        print(prefix + f"{full_path.name}")

        content = ""
        with full_path.open('r') as f:
            for line in f:
                line = line.rstrip()
                if verbose:
                    print(f"[VERBOSE] Procesando línea: {line}")
                if line.startswith('@@'):
                    nested_file_path = line[2:].strip()
                    if verbose:
                        print(f"[VERBOSE] Se encontró inclusión de archivo con @@: {nested_file_path}")
                    content += read_file(nested_file_path, full_path.parent, tree_depth + 1) + '\n'
                elif line.startswith('@'):
                    nested_file_path = line[1:].strip()
                    if verbose:
                        print(f"[VERBOSE] Se encontró inclusión de archivo con @: {nested_file_path}")
                    content += read_file(nested_file_path, base_path, tree_depth + 1) + '\n'
                else:
                    content += line + '\n'
        return content
        
    base_path = Path(base_path)
    return read_file(input_file, base_path, tree_depth)


# 2. Función para reemplazar variables en el archivo con evaluación de orden
def process_file_sequentially(file_content, verbose=False):
    defines = {}
    replaced_content = []
    # Modificado para que el ';' sea opcional
    define_pattern = re.compile(r'^define\s+(\w+)\s*=\s*\'(.*?)\'\s*;?\s*$', re.IGNORECASE)
    undefine_pattern = re.compile(r'^undefine\s+(\w+)\s*;\s*$', re.IGNORECASE)
    variable_pattern = re.compile(r"(&\w+)(\.\.)?")
    
    # Diccionario para contar las veces que se reemplazan las variables
    replacement_count = {}

    for line_number, line in enumerate(file_content.splitlines(), 1):
        clean = line.rstrip()

        # Si es un comentario, simplemente lo agregamos sin procesar
        if clean.lstrip().startswith('--'):
            replaced_content.append(line)
            continue

        # Si es una línea DEFINE, la registramos o redefinimos
        match_define = define_pattern.match(clean)
        if match_define:
            var_name = match_define.group(1)
            var_value = match_define.group(2)
            defines[var_name] = var_value  # Redefinición permitida
            if verbose:
                print(f"[VERBOSE] Definiendo variable: {var_name} = {var_value}")
            # Inicializar el contador de reemplazo para la variable definida
            if var_name not in replacement_count:
                replacement_count[var_name] = 0
            continue  # No agregar la línea DEFINE al resultado final

        # Si es una línea UNDEFINE, eliminamos la variable
        match_undefine = undefine_pattern.match(clean)
        if match_undefine:
            var_name = match_undefine.group(1)
            if var_name in defines:
                del defines[var_name]  # Eliminar la variable del diccionario
            if verbose:
                print(f"[VERBOSE] Variable indefinida: {var_name}")
            continue  # No agregar la línea UNDEFINE al resultado final

        # Si no es un DEFINE ni UNDEFINE, verificamos si hay variables que deben ser reemplazadas
        all_matches = variable_pattern.findall(clean)

        # Revisar cada variable usada en la línea
        replaced_line = clean
        for match in all_matches:
            var_name = match[0][1:]  # Nombre de la variable sin el símbolo '&'
            if var_name not in defines:
                raise ValueError(f"Error: La variable '{var_name}' se usa antes de ser definida (línea {line_number}).")
            value = defines[var_name]
            
            # Reemplazar y contar
            if match[1]:  # Si tiene puntos concatenados (..)
                replaced_line = replaced_line.replace(match[0] + "..", value + ".")
            else:
                replaced_line = replaced_line.replace(match[0], value)
            
            if verbose:
                print(f"[VERBOSE] Reemplazando variable {var_name} con valor {value} en la línea {line_number}")
            # Incrementar el contador de reemplazos para la variable
            replacement_count[var_name] += 1

        replaced_content.append(replaced_line)

    # Mostrar las variables y cuántas veces fueron reemplazadas, con formato justificado
    print("\nResumen de sustituciones:")
    if replacement_count:
        max_var_length = max(len(var) for var in replacement_count)  # Ancho máximo de las variables
        for var, count in replacement_count.items():
            print(f"{var.ljust(max_var_length)}\t{count}")
    else:
        print("No se realizaron sustituciones de variables.")

    return "\n".join(replaced_content)


# 3. Función que combina todo el proceso
def process_file_with_replacements(input_file, skip_var=False, verbose=False):
    # Siempre resolveremos las inclusiones @ y @@
    print("Árbol de inclusiones:")
    full_content = parse_sqlplus_file(input_file, verbose=verbose)

    if not skip_var:
        # Si NO se pasa el flag --skip-var, hacer el reemplazo de variables de sustitución secuencialmente
        final_content = process_file_sequentially(full_content, verbose=verbose)
        return final_content
    else:
        # Si se pasa el flag --skip-var, devolver solo el contenido combinado sin hacer sustituciones
        return full_content


# 4. Configuración de argparse y ejecución
def main():
    parser = CustomArgumentParser(description='Procesa un script de SQL*Plus, resolviendo inclusiones y sustituyendo variables.')
    
    # Opción para saltar el procesamiento de variables -sv / --skip-var
    parser.add_argument('--skip-var', '-sv', action='store_true',
                        help='Omite el proceso de sustitución de variables. Solo resuelve inclusiones @ y @@.')

    # Opción para activar el modo verbose -v / --verbose
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Muestra información detallada sobre el procesamiento interno (modo verbose).')
    
    # Argumentos de entrada y salida (renombrados a --input y --output)
    parser.add_argument('--input', '-i', required=True, help='El archivo de entrada a procesar')
    parser.add_argument('--output', '-o', required=True, help='El archivo donde se escribirá el resultado')

    args = parser.parse_args()

    try:
        # Ejecutar el proceso completo o parcial
        result = process_file_with_replacements(args.input, args.skip_var, args.verbose)

        # Escribir el resultado en el archivo de salida
        with open(args.output, 'w') as output_file:
            output_file.write(result)

        print(f"Procesamiento completado. Resultado escrito en: {args.output}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error de procesamiento: {e}")


if __name__ == '__main__':
    main()
