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
import os
import fileinput
from io import StringIO
import argparse
import importlib.metadata as metadata
from pyaml import yaml
import itertools

import testomaton.generator as generator
import testomaton.model as model
import testomaton.validator as validator
import testomaton.errors as errors
from testomaton.errors import ExitCodes as ec
from testomaton.solver import TomatoSolver

import csv

class DuplicateCheckLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            # check if key already in mapping
            if key in mapping:
                raise ValueError(f"Duplicate key found: {key}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping
    
def version():
    """Get the version of tomato"""
    return metadata.version('testomaton')

def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--version", action='store_true', 
        default=False, 
        help="Print version and exit")
    parser.add_argument("--demo-level", type=int, default=0,
        help="Can be used to demostrate working of the algorithm. \
        1: Show progress, 2: Show progress and introduces delay at each step. \
        3: Show progress and introduce a larger delay at each step.",
        choices=[1, 2, 3])
    parser.add_argument("--show-progress", nargs='?', const='stderr',
        choices=['stderr', 'stdout'],
        help="Show progress information during test generation in format 'current/total'. " \
        "Options: 'stderr' (default), 'stdout'")
    parser.add_argument("-f", "--function", type=str, default=None, 
        help="Function name to generate tests for. If not provided\
            tests for the first function defined in the model will be generated")
    
    validation_group = parser.add_argument_group('Validation')

    validate_group = validation_group.add_mutually_exclusive_group()
    validate_group.add_argument("-v", "--validate-model", action='store_true', default=False, 
        help=f"Validate the model and exit. Returns {ec.SUCCESS} if the model is valid, \
{ec.MODEL_VALIDATION_ERROR} if the model is not syntatically correct. \
If this flag is used, the only effective arguments are -f/--function and the arguments from \
the  'Model content filtering'. Validated elements can still be filtered using whitelists \
and blacklists. Other arguments are silently ignored.")
    validate_group.add_argument("-V", "--validate-tests", nargs='?', type=str, const=None, 
        default=argparse.SUPPRESS, metavar='TEST_FILE',
        help=f"Validate the tests and exit. Prints on stdandard output the tests are valid, ie. \
they could be generated from this model using all the elements and constraints (blacklists, \
whitelists, negations and invertions still can be used). If a test or the headrow could  not \
be generated using given model, it is printed in the stderr with an error message, \
The opional argument is a path to the file with tests (with headrow or not, configured by \
-H/--no-headrow flag). If no test file is provided, the tests are read from the standard input. \
In this case, if the model is also read from the standard input, the model is read first and \
must be separated from the tests by a line starting from '---' \
(three dashes). ")
    
    validation_group.add_argument("--exit-on-error", action='store_true', default=False, 
        help="Exit on the first error. If this flag is not set, the program will continue \
to the next test or model element after an error.")
    validation_group.add_argument("-F", "--no-error-formatting", action='store_true', default=False,
        help="Do not format error messages. If this flag is not set, the error messages are formatted \
to be more readable and distinguishable from valid tests.")
    validation_group.add_argument("-M", "--no-error-messages", action='store_true', default=False,  
        help="Do not print error messages. If this flag is set, only the tests that fail validation \
are printed on stderr, without any additional messages.")
    validation_group.add_argument("--duplicate-headrow", action='store_true', default=False, 
        help="Print the headrow both on top of the valid tests and the tests that fail validation.")
    
    model_content_group = parser.add_argument_group('Model content filtering')
    model_content_group.add_argument("-w", "--whitelist", type=str, default=None,
        help="Comma separated list of names and labels of elements\
            that should be parsed. All function elements (parameters, choices, \
            constraints etc.) without name or label on that list will be ignored.")
    model_content_group.add_argument("-b", "--blacklist", type=str, default=None,
        help="Comma separated list of names and labels of elements\
            that should be ignored. All function elements (parameters, choices, \
            constraints etc.) with name or label on that list will be ignored.")    
    model_content_group.add_argument("--input-whitelist", type=str, default=None,
        help="Whitelist of input elements (parameters and choices) to parse.\
            Labels for input elements are inherited from parent element of the same type.")
    model_content_group.add_argument("--input-blacklist", type=str, default=None,
        help="Blacklist of input elements (parameters and choices) to ignore.\
        Labels for input elements are inherited from parent element of the same type.")
    model_content_group.add_argument("--parameters-whitelist", type=str, default=None,
        help="Whitelist of parameters to parse. Labels within structures are inherited\
        from parent parameter.")
    model_content_group.add_argument("--parameters-blacklist", type=str, default=None,
        help="Blacklist of parameters to ignore. Labels within structures are inherited")
    model_content_group.add_argument("--choices-whitelist", type=str, default=None,
        help="Whitelist of choices to parse. Labels of nested choices are inherited from the parent choice.")
    model_content_group.add_argument("--choices-blacklist", type=str, default=None,
        help="Blacklist of choices to ignore. Labels of nested choices are inherited from the parent choice.")
    model_content_group.add_argument("--logic-whitelist", type=str, default=None,
        help="Whitelist of logic elements (constraints and assignments) to parse.")
    model_content_group.add_argument("--logic-blacklist", type=str, default=None,
        help="Blacklist of logic elements (constraints and assignments) to ignore.")
    model_content_group.add_argument("--constraints-whitelist", type=str, default=None,
        help="Whitelist of constraints to parse.")
    model_content_group.add_argument("--constraints-blacklist", type=str, default=None,
        help="Blacklist of constraints to ignore.")
    model_content_group.add_argument("--assignments-whitelist", type=str, default=None,
        help="Whitelist of assignments to parse.")
    model_content_group.add_argument("--assignments-blacklist", type=str, default=None,
        help="Blacklist of assignments to ignore.")
            
    
    parser.add_argument("input_file", type=str, nargs='?', default=None,
                        help="Input file containing the model. If not provided, the model is read from the standard input.")

    formatting_group = parser.add_argument_group('Formatting')
    formatting_group.add_argument("-H", "--no-headrow", action='store_true', 
        default=False, 
        help="do not print the head row with the parameter names")
    formatting_group.add_argument("--use-choice-names", action='store_true', 
        default=False, 
        help="When printing the output, do not print choice values but their full names.")
    formatting_group.add_argument("-s", "--separator", type=str, default=',', 
        help="Separator to use in the output")    
    
    group = parser.add_argument_group('Generators', 'Define a generator to use')
    generator_group = group.add_mutually_exclusive_group()
    generator_group.add_argument("--cartesian", action='store_true', 
        help="generate cartesian product of input choices")
    generator_group.add_argument("--random", action='store_true', 
        help="generate random test cases")
    generator_group.add_argument("--nwise", action='store_true',
        help="nwise generator (default)")
    
    random_group = parser.add_argument_group('Random generator options:')
    random_group.add_argument("-l", "--length", type=int, default=None,
        help="length of the randomly generated suite. 0 for infinite")
    random_group.add_argument("-D", "--duplicates", action='store_true', default=None,
        help="""Allows test cases to repeat. If not set and the number of test cases is 0,
            tests will be generated indifinitely""")
    random_group.add_argument("--adaptive", action='store_true', default=None,
        help="""Use adaptive techniques to generate tests that are far from 
            the ones already generated""")

    nwise_group = parser.add_argument_group('Nwise generator options')
    nwise_group.add_argument("-n", type=int, default=None, help="n in nwise. Default value: 2")
    nwise_group.add_argument("-c", "--coverage", default=None, 
        help="""Required coverage. 100 means all test cases that are allowed
            by constraints. Available for nwise and cartesian generators. Default vaule: 100""")
    nwise_group.add_argument("-T", "--tuples-from", default=None, 
        help="""Defines set of parameters to generate tuples from. Only tuples that contain
        parameters that are in the list will be generated. The list is comma separated and may contain
        parameter names and labels. If a label is provided, all parameters with that label will be included.""")

    constraints_manipulation_group = parser.add_argument_group('Constraints manipulation:')
    constraints_manipulation_group.add_argument("--ignore-constraints", action='store_true', default=False, 
        help="Ignore constraints when generating tests")
    constraints_manipulation_group.add_argument("--ignore-assignments", action='store_true', default=False, 
        help="Ignore assignments when generating tests")
    constraints_manipulation_group.add_argument("--negate-constraints", action='store_true', default=False,
        help="Negate the aggregated constraint. This will mean that the generated tests will fail to satisfy at least one of the constraints.\
        Negating implication constraint in fact means negating its invariant equivalence. So a constraint 'A => B' will be negated to 'A AND NOT B'.")
    constraints_manipulation_group.add_argument("--invert-constraints", action='store_true', default=False,
        help="Negate all individual constraints. This will mean that the generated tests will fail to satisfy all the defined constraints.")
    
    args = parser.parse_args()

    # Check if version is requested, then print and exit
    if args.version:
        print(f"tomato {version()}")
        sys.exit(int(ec.SUCCESS))

    # Set default generator
    if not (args.random or args.nwise or args.cartesian):
        args.nwise = True

    # Check if random options are used correctly
    if not args.random and (args.length is not None or args.duplicates is not None or args.adaptive is not None):
        parser.error("--length, --duplicates and --no-adaptive can only be used with --random")
    
    # Check if nwise options are used correctly
    if not args.nwise and (args.n is not None or args.tuples_from or args.coverage is not None):
        parser.error("-n, --tuples-from and --coverage can only be used with --nwise")
    
    # Check if input file is provided
    if args.input_file is None:
        sys.stderr.write("Reading model from stdin\n")
        sys.stderr.flush()
    
    # Check if whitelist and blacklist are used together   
    if args.whitelist is not None and args.blacklist is not None:
        parser.error("--whitelist and --blacklist cannot be used together")
    
    if args.input_whitelist is not None and (
        args.input_blacklist is not None or args.parameters_blacklist is not None or args.choices_blacklist is not None):
        parser.error("--input-whitelist and --input-blacklist/--parameters-blacklist/--choices-blacklist cannot be used together")
    
    if args.input_blacklist is not None and (
        args.input_whitelist is not None or args.parameters_whitelist is not None or args.choices_whitelist is not None):
        parser.error("--input-whitelist and --input-blacklist/--parameters-blacklist/--choices-blacklist cannot be used together")
        
    if args.parameters_whitelist is not None and (
        args.parameters_blacklist is not None or args.input_blacklist is not None):
        parser.error("--parameters-whitelist and --parameters-blacklist/--input-blacklist cannot be used together")
    
    if args.parameters_blacklist is not None and (
        args.parameters_whitelist is not None or args.input_whitelist is not None):
        parser.error("--parameters-whitelist and --parameters-blacklist/--input-blacklist cannot be used together")
    
    if args.choices_whitelist is not None and (
        args.choices_blacklist is not None or args.input_blacklist is not None):
        parser.error("--choices-whitelist and --choices-blacklist/--input-blacklist cannot be used together")
        
    if args.choices_blacklist is not None and (
        args.choices_whitelist is not None or args.input_whitelist is not None):
        parser.error("--choices-whitelist and --choices-blacklist/--input-blacklist cannot be used together")
        
    if args.logic_whitelist is not None and (args.logic_blacklist is not None or args.constraints_blacklist is not None or args.assignments_blacklist is not None):
        parser.error("--logic-whitelist and --logic-blacklist/--constraints-blacklist/--assignments-blacklist cannot be used together")
        
    if args.logic_blacklist is not None and (args.logic_whitelist is not None or args.constraints_whitelist is not None or args.assignments_whitelist is not None):
        parser.error("--logic-whitelist and --logic-blacklist/--constraints-blacklist/--assignments-blacklist cannot be used together")
        
    if args.constraints_whitelist is not None and (args.constraints_blacklist is not None or args.logic_blacklist is not None):
        parser.error("--constraints-whitelist and --constraints-blacklist/--logic-blacklist cannot be used together")
        
    if args.constraints_blacklist is not None and (args.constraints_whitelist is not None or args.logic_whitelist is not None):
        parser.error("--constraints-whitelist and --constraints-blacklist/--logic-blacklist cannot be used together")
        
    if args.assignments_whitelist is not None and (args.assignments_blacklist is not None or args.logic_blacklist is not None):
        parser.error("--assignments-whitelist and --assignments-blacklist/--logic-blacklist cannot be used together")
        
    if args.assignments_blacklist is not None and (args.assignments_whitelist is not None or args.logic_whitelist is not None):
        parser.error("--assignments-whitelist and --assignments-blacklist/--logic-blacklist cannot be used together")
        
    if args.ignore_constraints and (args.constraints_whitelist is not None or args.constraints_blacklist is not None):
        parser.error("--ignore-constraints and --constraints-whitelist/--constraints-blacklist cannot be used together")
        
    if args.ignore_assignments and (args.assignments_whitelist is not None or args.assignments_blacklist is not None):
        parser.error("--ignore-assignments and --assignments-whitelist/--assignments-blacklist cannot be used together")

    # Check if whitelist/blacklist is used with other whitelists/blacklists
    if (args.whitelist is not None or args.blacklist is not None) and \
        (args.input_whitelist is not None or 
        args.parameters_whitelist is not None or 
        args.choices_whitelist is not None or 
        args.logic_whitelist is not None or 
        args.constraints_whitelist is not None or 
        args.assignments_whitelist is not None or
        args.ignore_constraints or
        args.ignore_assignments or
        args.input_blacklist is not None or
        args.parameters_blacklist is not None or
        args.choices_blacklist is not None or
        args.logic_blacklist is not None or
        args.constraints_blacklist is not None or
        args.assignments_blacklist is not None):
            
        parser.error("--whitelist/--blacklist cannot be used with other whitelists or blacklists")

    if (args.exit_on_error or args.no_error_formatting or args.no_error_messages or args.duplicate_headrow) and ('validate_tests' not in args):
        parser.error("--exit-on-error, --no-error-formatting, --no-error-messages, --duplicate-headrow can only be used with --validate-tests")
    if args.no_headrow and args.duplicate_headrow:
        parser.error("--no-headrow and --duplicate-headrow cannot be used together")

    return args

def validate_tests(function, solver, args):
    test_file = args.validate_tests

    def validate(in_stream):
        return validator.validate_test_stream(in_stream, function, solver, 
            separator=args.separator, 
            no_headrow=args.no_headrow, 
            use_choice_names=args.use_choice_names, 
            exit_on_error=args.exit_on_error,
            no_error_formatting=args.no_error_formatting,
            no_error_messages=args.no_error_messages,
            duplicate_headrow=args.duplicate_headrow)

    if test_file == None:
        result = validate(sys.stdin)
    else:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                result = validate(f)
        except OSError as e:
            print(f'Error: unable to open file {test_file}: {e}', file=sys.stderr)
            sys.exit(int(ec.TEST_FILE_NOT_FOUND))
    return result
                
def tomato():
    args = parse_args()
    
    function_name = args.function

    validate_model = args.validate_model

    whitelist = []    
    blacklist = []
    parameters_blacklist = []
    parameters_whitelist = []
    choices_blacklist = []
    choices_whitelist = []
    constraints_blacklist = []
    constraints_whitelist = []
    assignments_blacklist = []
    assignments_whitelist = []
    
    # Parse filter lists
    def parse_filter_list(list_str):
        return [l.strip() for l in list_str.split(',')]
    
    if args.whitelist is not None:        
        whitelist = parse_filter_list(args.whitelist)
    if args.blacklist is not None:
        blacklist = parse_filter_list(args.blacklist)
    if args.input_whitelist is not None:
        parameters_whitelist.extend(parse_filter_list(args.input_whitelist))
        choices_whitelist.extend(parse_filter_list(args.input_whitelist))
    if args.input_blacklist is not None:
        parameters_blacklist.extend(parse_filter_list(args.input_blacklist))
        choices_blacklist.extend(parse_filter_list(args.input_blacklist))
    if args.parameters_whitelist is not None:
        parameters_whitelist.extend(parse_filter_list(args.parameters_whitelist))
    if args.parameters_blacklist is not None:
        parameters_blacklist.extend(parse_filter_list(args.parameters_blacklist))
    if args.choices_whitelist is not None:
        choices_whitelist.extend(parse_filter_list(args.choices_whitelist))
    if args.choices_blacklist is not None:
        choices_blacklist.extend(parse_filter_list(args.choices_blacklist))
    if args.logic_whitelist is not None:
        constraints_whitelist.extend(parse_filter_list(args.logic_whitelist))
        assignments_whitelist.extend(parse_filter_list(args.logic_whitelist))
    if args.logic_blacklist is not None:
        constraints_blacklist.extend(parse_filter_list(args.logic_blacklist))
        assignments_blacklist.extend(parse_filter_list(args.logic_blacklist))
    if args.constraints_whitelist is not None:
        constraints_whitelist.extend(parse_filter_list(args.constraints_whitelist))
    if args.constraints_blacklist is not None:
        constraints_blacklist.extend(parse_filter_list(args.constraints_blacklist))
    if args.assignments_whitelist is not None:
        assignments_whitelist.extend(parse_filter_list(args.assignments_whitelist))
    if args.assignments_blacklist is not None:
        assignments_blacklist.extend(parse_filter_list(args.assignments_blacklist))

    input_file = args.input_file

    parsed_yaml_model = None
    if input_file is not None:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
                parsed_yaml_model = yaml.load(file_content, Loader=DuplicateCheckLoader)
                if parsed_yaml_model is None:
                    filename = os.path.basename(input_file)
                    print(f"Error: The input YAML file {filename} is empty.", file=sys.stderr)
                    sys.exit(int(ec.MODEL_PARSING_ERROR))
        except OSError as e:
            print(f'Error: unable to open file {input_file}: {e}', file=sys.stderr)
            sys.exit(int(ec.MODEL_FILE_NOT_FOUND))
        except ValueError as e:
            print(f"Value error: {e}", file=sys.stderr) 
            sys.exit(int(ec.YAML_PARSING_ERROR))
        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}", file=sys.stderr) 
            sys.exit(int(ec.YAML_PARSING_ERROR))
    else:
        try:
            yaml_lines = []
            #read from stdin until the end of input, or a line that starts with '----'
            for line in sys.stdin:
                if line.startswith('----'):
                    break
                yaml_lines.append(line)
            yaml_content = ''.join(yaml_lines)           
            parsed_yaml_model = yaml.load(StringIO(yaml_content), Loader=DuplicateCheckLoader)
        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}", file=sys.stderr) 
            sys.exit(int(ec.YAML_PARSING_ERROR))
        except ValueError as e:
            print(f"Value error: {e}", file=sys.stderr) 
            sys.exit(int(ec.YAML_PARSING_ERROR))

    parsing_errors = []

    if 'global parameters' in parsed_yaml_model:
        allowed_keys = {'parameter'}
        model.validate_list('___GLOBAL_PARAMETERS___', parsed_yaml_model['global parameters'], allowed_keys)

    if 'functions' not in parsed_yaml_model:
        print(f"Error: model must containt 'functions' top element", file=sys.stderr)
        sys.exit(int(ec.MODEL_PARSING_ERROR))

    functions = parsed_yaml_model['functions']
    allowed_keys = { 'function' }
    model.validate_list('functions', functions, allowed_keys)
    parsing_errors.extend(errors.parsing_errors)

    if function_name is not None:
        functions_to_parse = [function_name]
    else:
        all_functions = model.get_function_names(parsed_yaml_model, whitelist, blacklist)
        if len(all_functions) == 0:
            print(f'No function to parse', file=sys.stderr)
            sys.exit(int(ec.MODEL_PARSING_ERROR))
        if validate_model:
            functions_to_parse = all_functions
        else:
            functions_to_parse = [all_functions[0]]

    for function_name in functions_to_parse:
        errors.parsing_errors = []
        function = None
        solver = None
        # Parse the function. If the function name is None, the first function in the model is parsed
        try:
            function = model.parse_function(parsed_yaml_model, function_name,
                ignore_constraints=args.ignore_constraints, 
                ignore_assignments=args.ignore_assignments,
                whitelist=whitelist,
                blacklist=blacklist,
                parameters_whitelist=parameters_whitelist,
                parameters_blacklist=parameters_blacklist,
                choices_whitelist=choices_whitelist,
                choices_blacklist=choices_blacklist,
                constraints_whitelist=constraints_whitelist,
                constraints_blacklist=constraints_blacklist,
                assignments_whitelist=assignments_whitelist,
                assignments_blacklist=assignments_blacklist)
        except Exception as e:
            print(f"Error parsing function '{function_name}': {e}", file=sys.stderr)
            continue
        if function is not None:
            try:
                solver = TomatoSolver(function,
                    negate_constraints=args.negate_constraints,
                    invert_constraints=args.invert_constraints)
            except Exception as e:
                print(f"Error creating solver for function '{function_name}': {e}", file=sys.stderr)
                continue

        if errors.parsing_errors is not None:
            parsing_errors.extend(errors.parsing_errors)
            continue
        if len(errors.parsing_errors) > 0 :
            parsing_errors.extend(errors.parsing_errors)
            continue

    if len(parsing_errors):
        for error in parsing_errors:
            print(f"{error}", file=sys.stderr)
        sys.exit(int(ec.MODEL_PARSING_ERROR))
    elif validate_model:
        print(f"Model is valid", file=sys.stderr)
        sys.exit(int(ec.SUCCESS))
    
    if not function:
        print(f"No functions to parse", file=sys.stderr)
        sys.exit(int(ec.MODEL_PARSING_ERROR))

    if 'validate_tests' in args:        
        result = validate_tests(function, solver, args)
        if not result:
            sys.exit(int(ec.TEST_PARSING_ERROR))
        else:
            sys.exit(int(ec.SUCCESS))

    # select the nwise generator
    if args.nwise:
        n = args.n
        if n is None:
            n = 2
        if args.coverage is None:
            args.coverage = 100
        coverage = int(args.coverage)
        tuples_from = None
        if args.tuples_from is not None:
            tuples_from = parse_filter_list(args.tuples_from)
            
        gen = generator.nwise(function, solver, n, tuples_from=tuples_from, coverage=coverage)


    # select the cartesian generator
    if args.cartesian:
        gen = generator.cartesian(function, solver)
    
    # select the random generator  
    if args.random:
        length = args.length
        duplicates = args.duplicates
        adaptive = args.adaptive
        if length is None:
            length = 0
        if duplicates is None:
            duplicates = False
        if adaptive is None:
            adaptive = False

        gen = generator.random(function,
                                solver,
                                length=length, 
                                duplicates=duplicates,
                                adaptive=adaptive)

    sep = args.separator
    
    # Set demo level
    if args.demo_level > 0:
        generator.demo_mode = True
    
    if args.show_progress: # Experimental feature
        generator.show_progress = True
        generator.progress_format = "detailed"
        generator.progress_output_mode = args.show_progress
        #generator.step_delay = 0.5
        
    # Set demo level
    if args.demo_level == 2:
        generator.step_delay = 0.05
    if args.demo_level == 3:
        generator.step_delay = 0.2

    # Check for conflicting options
    if args.demo_level and args.show_progress:
        sys.exit(Warning("--demo-level and --show-progress are mutually exclusive arguments."))
    
    writer = csv.writer(sys.stdout, delimiter=sep)
    
    if not args.no_headrow:
        writer.writerow(function.get_all_parameter_names())

    try:
        #generate test cases with the selected generator
        for test in gen:
            if isinstance(test, str) and test.startswith("PROGRESS:"):
                #print(test)
                writer.writerow([test])
                continue
            if not args.use_choice_names:
                parameter_names = function.get_all_parameter_names()
                for i, name in enumerate(parameter_names):
                    if name in [p.name for p in function.output_parameters]:
                        continue
                    parameter = function.get_parameter(name)
                    choice_name = test[i]
                    choice = parameter.get_choice(choice_name)
                    try:
                        test[i] = choice.value
                    except AttributeError:
                        raise ValueError(f"Choice '{choice_name}' not found in parameter {name}")
            writer.writerow(test)
    except Exception as e:
        print(f"Error during generation: {e}", file=sys.stderr)
        sys.exit(int(ec.GENERATION_ERROR))
    
if __name__ == '__main__':
    tomato()
    