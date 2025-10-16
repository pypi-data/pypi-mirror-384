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
#  For the commercial license, please contact Testify AS.
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
import csv
import regex as re

global_imports = {}
appended_columns = prepended_columns = replaced_columns = swapped_columns = []
columns_whitelist = []
columns_blacklist = []

def read_csv(file, separator=','):
    """
    reads a csv file and yields rows

    Args:
        file: file to read. If None, reads from stdin
        separator: separator used in the csv file
    
    Yields:
        a row from the csv file
    
    Raises:
        OSError: if the file can't be opened
    """
    csv_reader = None
    try:
        # if file is one, read from standard input
        if file is None:
            csv_reader = csv.reader(sys.stdin, delimiter=separator)
            for row in csv_reader:
                yield row
        else:
            with open(file) as f:
                csv_reader = csv.reader(f, delimiter=separator)
                for row in csv_reader:
                    yield row
    # if there is a file, but it can't be opened, raise an exception
    except OSError:
        print(f"Could not open file {file}")
        sys.exit(1)

def parse_column_refactoring_args(args):
    """
    Parses the arguments for column refactoring

    Args:
        args: the arguments to parse
    
    Returns:
        a list of tuples with the column refactoring information
    
    Raises:
        Exception: if the arguments are not in the correct format
    """
    result = []
    # loops through the args and returns a list of tuples with the column refactoring information
    for col in args if args is not None else []:
        ref = name = expr = None
        if len(col) == 2:
            ref, name, expr = None, col[0], col[1]
        elif len(col) == 3:
            ref, name, expr = col[0], col[1], col[2]
        else:
            raise Exception(f"Invalid format: {col}. Should be '[<column_name|index>] <new_name> <expression>''")
        if name and expr:
            result.append((ref, name, expr))
    return result

def parse_columns_swap_args(args):
    """
    Parses the arguments for column swapping
    
    Args:
        args: the arguments to parse
    
    Returns:
        a list of tuples with the columns to swap
    
    Raises:
        Exception: if the arguments are not in the correct format
    """
    result = []
    for col in args if args is not None else []:
        name1 = name2 = None
        if len(col) == 2:
            name1, name2 = col
        else:
            raise Exception(f"Invalid format: {col}. Should be '<name1|index1|-1> <name2|index2|-1>'")
        if name1 and name2:
            result.append((name1, name2))
    return result

def parse_args():
    """
    Parses the command line arguments using argparse
    
    Returns:
        the parsed arguments
    
    Raises:
        Exception: if there is an error parsing the arguments
    """

    global global_imports
    global appended_columns, prepended_columns, replaced_columns, swapped_columns
    global columns_whitelist, columns_blacklist
    
    # create the parser
    parser = argparse.ArgumentParser(description='Evaluate expressions in a csv file. Expressions are evaluated in the order they appear in the input list. Use @python <expression> to evaluate python expressions. In the expressions, use {column_name} to refer to a column value. Use {row id} to refer to the row number.')
    parser.add_argument('input_file', type=str,  nargs='?', default=None, help='Input file. If not provided, stdin is used')
    parser.add_argument('-v', '--version', action='store_true', help='Print version')
    
    # general arguments
    parser.add_argument('-n', '--add-linenumber', nargs='?', type=str, default='', help='Add a column with the line number. Optional argument is the name of the column. Default name is empty. The column may be referenced in the expressions by its name.')
    parser.add_argument('-H', '--remove-headrow', action='store_true', default=False, help='Do not output the first line that was read')
    parser.add_argument("-s", "--input-separator", type=str, default=',', help="Separator used in the input")    
    parser.add_argument("-S", "--output-separator", type=str, default=None, help="Separator used in the output. If not provided, the input separator is used")    

    # column manipulation arguments
    column_manipulation_group = parser.add_argument_group('Column manipulation. All arguments except white/blacklists are applied in the following order ADD -> REPLACE -> SWAP -> WHITELIST/BLACKLIST.')
    column_manipulation_group.add_argument("-B", "--columns-blacklist", type=str, default=None, help="Comma separated list of columns to remove. A column may be indicated with its index number, range of indices X..Y, or a regex pattern for the column name")
    column_manipulation_group.add_argument("-W", "--columns-whitelist", type=str, default=None, help="Comma separated list of columns to show. A column may be indicated with its index number, range of indices X..Y, or a regex pattern for the column name")
    column_manipulation_group.add_argument("-A", "--add-after", metavar='<column_name|index> <new_name> <expression>', nargs='+', action='append', type=str, default=None, help="Add column[s] after the specified column. If column name is empty, the column is added at the end. Columns are indexed starting at 1.")
    column_manipulation_group.add_argument("-F", "--add-before", metavar='<column_name|index>::<new_name>::<expression>', nargs='+', action='append', type=str, default=None, help="Add column[s] before the specified column. If column name is empty, the column is added at the beginning. Columns are indexed starting at 1.")
    column_manipulation_group.add_argument("-R", "--replace-columns", metavar='<column_name|index>::<new_name>::<expression>', nargs='+', action='append', type=str, default=None, help="Replace column[s] with new header and value. '-1' for the colummn index means the last column. Columns are indexed starting at 1.")
    column_manipulation_group.add_argument("-X", "--swap-columns", metavar='<name1|index1|-1>::<name2|index2|-1>', nargs='+', action='append', type=str, default=None, help="Swaps two columns. '-1' for the colummn index means the last column. Columns are indexed starting at 1.")
    
    args = parser.parse_args()

    # checks if whitelist and blacklist are used
    columns_whitelist = args.columns_whitelist.split(',') if args.columns_whitelist is not None else []
    columns_blacklist = args.columns_blacklist.split(',') if args.columns_blacklist is not None else []
    if len(columns_whitelist) != 0 and len(columns_blacklist) != 0:
        print("You can't use both columns whitelist and blacklist")
        sys.exit(1)
    
    if args.output_separator is None:
        args.output_separator = args.input_separator
    
    # prints the version of tomato
    if args.version:
        print(f"tomato {version()}")
        sys.exit(0)
    
    # use the refactoring methods on the specified inputs
    try:    
        appended_columns = parse_column_refactoring_args(args.add_after)
    except Exception as e:
        print(f"Error parsing -A|add_after: {e}")
        sys.exit(1)
    try:    
        prepended_columns = parse_column_refactoring_args(args.add_before)
    except Exception as e:
        print(f"Error parsing -B|add_before: {e}")
        sys.exit(1)
    try:    
        replaced_columns = parse_column_refactoring_args(args.replace_columns)
    except Exception as e:
        print(f"Error parsing -R|--replace: {e}")
        sys.exit(1)   
    
    try:
        swapped_columns = parse_columns_swap_args(args.swap_columns)
    except Exception as e:
        print(f"Error parsing -X|--swap_columns: {e}")
        sys.exit(1)
    
    return args        


def version():
    return metadata.version('testomaton')

def define_output_columns(input_columns):
    """
    Defines the output columns based on the input columns and the column refactoring arguments
    
    Args:
        input_columns: the input columns
    
    Returns:
        a tuple with the output columns and the output columns mapping
    
    Raises:
        Exception: if the column index is 0
    """
    output_columns = input_columns.copy()
    output_columns_mapping = {}
    
    # loop through the appended columns, adding to the end
    for after, name, expr in appended_columns:
        if after == '-1' or after == None:
            output_columns.append(name)
        elif after.isdigit():
            if(int(before) == 0):
                raise Exception("Column index should start at 1")
            index = int(after) - 1
            output_columns.insert(index + 1, name)
        else:
            for i, col in enumerate(output_columns):
                if re.match(after, col):
                    output_columns.insert(i + 1, name)
                    break
        output_columns_mapping[name] = expr
    # loop through the prepended columns, adding to the beginning
    for before, name, expr in prepended_columns:
        if before == None:
            output_columns.insert(0, name)
        elif before == '-1':
            output_columns.insert(len(output_columns) - 1, name)
        elif before.isdigit():
            if(int(before) == 0):
                raise Exception("Column index should start at 1")
            output_columns.insert(int(before) - 1, name)
        else:
            for i, col in enumerate(output_columns):
                if re.match(before, col):
                    output_columns.insert(i, name)
                    break
        output_columns_mapping[name] = expr
    # loop through the replaced columns
    for index, name, expr in replaced_columns:
        if index == None or index == '-1':
            last_index = len(output_columns) - 1
            output_columns[last_index] = name
        elif index.isdigit():
            output_columns[int(index) - 1] = name
        else:
            for i, col in enumerate(output_columns):
                if re.match(index, col):
                    output_columns[i] = name
                    break
        output_columns_mapping[name] = expr
    # loop through the swapped columns
    for name1, name2 in swapped_columns:
        if name1 == '-1':
            name1 = output_columns[-1]
        if name2 == '-1':
            name2 = output_columns[-2]
        index1 = output_columns.index(name1)
        index2 = output_columns.index(name2)
        output_columns[index1], output_columns[index2] = output_columns[index2], output_columns[index1]
    
    # return the output columns and the output columns mapping
    return output_columns, output_columns_mapping

def is_column_on_list(list, index, column_name):
    """
    Checks if the column is on the list
    
    Args:
        list: the list of columns
        index: the index of the column
        column_name: the name of the column
    
    Returns:
        True if the column is on the list, False otherwise
    """
    for token in list:
        range_tokens = token.split('..')
        # if the token is a range, check if the index is within the range
        if len(range_tokens) == 2:
            if index >= int(range_tokens[0]) - 1 and index <= int(range_tokens[1]) - 1:
                return True 
        # if the token is a digit, check if it matches the index + 1
        elif token.isdigit():
            if int(token) == index + 1:
                return True
        # if the column name matches the token, return True
        elif re.match(token, column_name):
            return True
        
def jigsaw():
    """
    The main method, which calls on the other methods to read and print the processed 
    rows
    """
    args = parse_args()
       
    input_columns = next(read_csv(args.input_file, separator=args.input_separator))
    output_columns, output_mapping = define_output_columns(input_columns)

    # checks if there is a whitelist or blacklist and if there is, filters the columns
    if len(columns_whitelist) == 0 and len(columns_blacklist) == 0:
        printed_columns = output_columns
    elif len(columns_whitelist) != 0:
        printed_columns = [str(output_columns[i]) for i in range(len(output_columns)) if is_column_on_list(columns_whitelist, i, output_columns[i])]
    elif len(columns_blacklist) != 0:
        printed_columns = [str(output_columns[i]) for i in range(len(output_columns)) if not is_column_on_list(columns_blacklist, i, output_columns[i])]
    
        
    if len(printed_columns) == 0:
        print("No columns to print")
        sys.exit(0)

    # print the first row if the remove headrow argument is not provided    
    if not args.remove_headrow:
        first_row = printed_columns.copy()
        if args.add_linenumber:
            first_row.insert(0, args.add_linenumber)
        print(args.output_separator.join(first_row))
        
    csv_writer = csv.writer(sys.stdout, delimiter=args.output_separator)
    row_id = 0
    # loop through the rows and write them to the output
    for row in read_csv(args.input_file, separator=args.input_separator):
        row_id += 1
        values = {}
        for index, token in enumerate(row):
            values[input_columns[index]] = token
        for name, expr in output_mapping.items():
            values[name] = expr
        output = [str(values[presented_column]) for presented_column in printed_columns]
        if args.add_linenumber:
            output.insert(0, str(row_id))
        
        csv_writer.writerow(output)
        
if __name__ == '__main__':
    jigsaw()
