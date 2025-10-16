#!/usr/bin/env python3

# 
#  Copyright Testify AS
# 
#  This file is part of testomaton suite
# 
#  testomaton is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  For commercial license, please contact Testify AS.
# 
#  testomaton is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with testomaton.  If not, see <http://www.gnu.org/licenses/>.
# 
#  See LICENSE file for the complete license text.
# 

import sys
import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import csv

global_imports = {}
appended_columns = prepended_columns = replaced_columns = swapped_columns = []
columns_whitelist = []
columns_blacklist = []

def read_csv(file, separator=','):
    csv_reader = None
    try:
        if file is None:
            csv_reader = csv.reader(sys.stdin, delimiter=separator)
            for row in csv_reader:
                yield row
        else:
            with open(file) as f:
                csv_reader = csv.reader(f, delimiter=separator)
                for row in csv_reader:
                    yield row
    except OSError:
        print(f"Could not open file {file}")
        sys.exit(1)

def parse_args():
    global global_imports
    global appended_columns, prepended_columns, replaced_columns, swapped_columns
    global columns_whitelist, columns_blacklist
    
    parser = argparse.ArgumentParser(description='Evaluate expressions in a csv file. Expressions are evaluated in the order they appear in the input list. Use @python <expression> to evaluate python expressions. In the expressions, use {column_name} to refer to a column value. Use {row id} to refer to the row number.')
    parser.add_argument('input_file', type=str,  nargs='?', default=None, help='Input file. If not provided, stdin is used')
    parser.add_argument('-v', '--version', action='store_true', help='Print version')
    
    parser.add_argument('-n', '--add-linenumber', nargs='?', type=str, default='', help='Add a column with the line number. Optional argument is the name of the column. Default name is empty. The column may be referenced in the expressions by its name.')
    parser.add_argument('-H', '--remove-headrow', action='store_true', default=False, help='Do not output the first line that was read')
    parser.add_argument("-s", "--input-separator", type=str, default=',', help="Separator used in the input")    
    parser.add_argument("-S", "--output-separator", type=str, default=None, help="Separator used in the output. If not provided, the input separator is used")    
    parser.add_argument("-i", "--imports", type=str, default=None, help="Comma separated list of packages to be imported and used in the expressions. Use 'as' to provide an alias.")
    parser.add_argument("-m", "--modules", type=str, default=None, help="Comma separated list of custom modules (files with python code) to be imported and used in the expressions. Use 'as' to provide an alias. The file should contain a single module.")
    parser.add_argument("-x", "--dont-evaluate", action='store_true', default=False, help="Do not evaluate expressions")

    args = parser.parse_args()

    if args.output_separator is None:
        args.output_separator = args.input_separator
    
    if args.version:
        print(f"tomato {version()}")
        sys.exit(0)
    
    if args.imports is not None:
        for imp in args.imports.split(','):
            tokens = imp.split(' as ')
            if len(tokens) == 1:
                module_name = alias = tokens[0].strip()
            else:
                module_name = tokens[0].strip()
                alias = tokens[1].strip()
                
            module = importlib.import_module(module_name)
            global_imports[alias] = module
    
    if args.modules is not None:
        for file_path in args.modules.split(','):
            tokens = file_path.split(' as ')
            file_name = tokens[0].strip().split('/')[-1]
            module_name = file_name.split('.')[0]
            if len(tokens) == 1:
                alias = module_name
            else:
                file_path = tokens[0].strip()
                alias = tokens[1].strip()
            # print(f"Importing module {module_name} from file {file_name} as {alias}")
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[alias] = module
            spec.loader.exec_module(module)
            global_imports[alias] = module
            for attr in dir(module):
                if not attr.startswith('__'):
                    global_imports[attr] = getattr(module, attr)

    return args        


def version():
    return metadata.version('testomaton')

def evaluate_token(row_id, token, values):
    stripped_token = token.strip()
    values_copy = values.copy()
    values_copy.update(global_imports)
    
    def is_numeric(value):
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    if token.startswith('@python '):
        expr = stripped_token[8:]
        expr = expr.replace('{row id}', str(row_id))
        for key, value in values.items():
            replaced_string = '{' + str(key) + '}'
            #if value is not surrounded by quotes already:
            if (str(value).strip()[0] != "'" and str(value).strip()[-1] != "'") and\
               (str(value).strip()[0] != '"' and str(value).strip()[-1] != '"'):
                
                #if value is not a number or bool literal then it should be enclosed in quotes
                if not is_numeric(value) and value.lower() not in ['true', 'false']:
                    value = f"'{value}'"
            expr = expr.replace(replaced_string, str(value))
        try:
            try:
                result = eval(expr, {}, values_copy)
            except Exception as e:
                print(f'evaluating {expr} failed: {e}')
            return result
        except Exception as e:
            exit(1)
    else:
        return token
        
def beaver():
    args = parse_args()
       
    input_columns = next(read_csv(args.input_file, separator=args.input_separator))

    if not args.remove_headrow:
        first_row = input_columns.copy()
        if args.add_linenumber:
            first_row.insert(0, args.add_linenumber)
        print(args.output_separator.join(first_row))
        
    csv_writer = csv.writer(sys.stdout, delimiter=args.output_separator)
    row_id = 0
    for row in read_csv(args.input_file, separator=args.input_separator):
        row_id += 1
        values = {}
        for index, token in enumerate(row):
            value = evaluate_token(row_id, token, values) if not args.dont_evaluate else token
            values[input_columns[index]] = value
        output = [str(v) for v in values.values()]
        if args.add_linenumber:
            output.insert(0, str(row_id))
        
        csv_writer.writerow(output)
        
if __name__ == '__main__':
    beaver()
