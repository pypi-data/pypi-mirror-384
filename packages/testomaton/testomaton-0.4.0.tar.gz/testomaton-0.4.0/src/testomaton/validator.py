from testomaton.model import Function, OutputParameter
from testomaton.solver import TomatoSolver

from itertools import combinations, product
import sys
import copy
import csv
import itertools

def validate_headrow(headrow: list, function: Function):
    messages = []
    parameter_names = function.get_all_parameter_names()
    valid = (headrow == parameter_names)
    if not valid:
        messages.append(f'Expected:\n{parameter_names}')
    return messages, valid

def validate_test_by_choice_names(test: list, function: Function, solver: TomatoSolver):
    messages = []
    result = True

    geninput = function.get_generator_input()
    parameter_names = geninput[0]
    parameters = [function.get_parameter(name) for name in parameter_names]
    leaf_choices = geninput[1]

    #first check if the test has the same number of values as the function has parameters
    if len(test) != len(parameter_names):
        result = False
        messages.append(f'Number of values in the test ({len(test)}) does not match the number of parameters in the function ({len(parameter_names)})')
        # print_exit_messages(messages, result)
        return messages, result

    #check if the values in the test are in the list of allowed values for the corresponding parameter
    for i in range(len(test)):
        parameter = parameters[i]
        if isinstance(parameter, OutputParameter):
            continue
        if parameter.get_choice(test[i]) is None:
            result = False
            messages.append(f"Choice '{test[i]}' is not defined for parameter '{parameter_names[i]}'")
    
    if not result:
        # print_exit_messages(messages, result)
        return messages, result

    #test if the test case satisfies the constraints
    test_copy = [test[i] if not isinstance(parameters[i], OutputParameter) else parameters[i].default_value for i in range(len(test))]
    if not solver.test(test_copy):
        result = False
        messages.append(f'Test case does not satisfy the constraints')
        # print_exit_messages(messages, result)
        return messages, result

    #test if the test case satisfies the assignments
    test_copy = solver.adapt(test_copy)
    for i in range(len(test)):
        if test_copy[i] != test[i]:
            result = False
            messages.append(f"Value of parameter {parameter_names[i]} should be {test_copy[i]}")

    # print_exit_messages(messages, result)
    return messages, result

def validate_test_by_values(test: list, function: Function, solver: TomatoSolver):
    messages = []
    result = True

    geninput = function.get_generator_input()
    parameter_names = geninput[0]
    parameters = [function.get_parameter(name) for name in parameter_names]
    leaf_choices = geninput[1]

    #first check if the test has the same number of values as the function has parameters
    if len(test) != len(parameter_names):
        result = False
        messages.append(f'Number of values in the test ({len(test)}) does not match the number of parameters in the function ({len(parameter_names)})')
        # print_exit_messages(messages, result)
        return messages, result

    #check if the values in the test are in the list of allowed values for the corresponding parameter
    for i in range(len(test)):
        parameter = parameters[i]
        full_name = parameter_names[i]
        if isinstance(parameter, OutputParameter):
            continue
        leaf_choices[i] = choices = [choice for choice in leaf_choices[i] if parameter.get_choice(choice).value == test[i]]
        if len(choices) == 0:
            result = False
            messages.append(f"Value '{test[i]}' not allowed for parameter '{full_name}'")
    if not result:
        # print_exit_messages(messages, result)
        return messages, result

    #in theory it is possible that many choices have the same value,
    #so we need to check each potential combination of choices
    test_cases = [list(test_case) for test_case in product(*leaf_choices)]
    #remove test cases that do not satisfy the constraints
    constrained_test_cases = [test_case for test_case in test_cases if solver.test(test_case)]
    if len(constrained_test_cases) == 0:
        result = False
        messages.append(f'Test case does not satisfy the constraints')
        # print_exit_messages(messages, result)
        return messages, result

    #remove test cases that do not satisfy the assignments
    def check_output_values(test_case):
        output_values = [test_case[i] if not isinstance(parameters[i], OutputParameter) else parameters[i].default_value for i in range(len(test_case))]
        output_values = solver.adapt(output_values)
        test_case_copy = [test_case[i] if not isinstance(parameters[i], OutputParameter) else test[i] for i in range(len(test_case))]
        the_same = True
        return (test_case_copy == output_values)

    assigned_test_cases = [test_case for test_case in constrained_test_cases if check_output_values(test_case)]
    if len(assigned_test_cases) == 0:
        messages.append(f'Output values not correct ')
        #in most cases, the values of choices are unique so the length of
        #constraints_test_cases should be 1. In this case, we can compare the 
        #result of assignment and indicate the exact differences
        if len(constrained_test_cases) == 1:
            test_case = copy.deepcopy(constrained_test_cases[0])
            test_case = solver.adapt(test_case)
            for i in range(len(test_case)):
                if test_case[i] != constrained_test_cases[0][i]:
                    messages.append(f"Value of parameter {parameter_names[i]} should be {test_case[i]}")
        # print_exit_messages(messages, False)
        return messages, False

    # print_exit_messages(messages, result)

    return messages, result

def validate_test_stream(in_stream, function, solver, **kwargs):
    """
    Validates a stream of test cases. The tests that are valid are written to stdout, the invalid ones are written to stderr with error message.
    The function returns True if all tests are parsed without problems. If there is a parsing error, the function returns False.
    """

    def print_error_messages(row, messages):
        print(f'{RED}', file=sys.stderr, end='')
        error_writer.writerow(row)
        if not no_error_messages:
            [print(f'{msg}', file=sys.stderr) for msg in messages]
        print(f'{END}', file=sys.stderr, end='', flush=True)


    no_error_formatting = False
    if 'no_error_formatting' in kwargs:
        no_error_formatting = kwargs['no_error_formatting']

    GREEN = '\033[92m' if not no_error_formatting else ''
    RED = '\033[91m' if not no_error_formatting else ''
    END = '\033[0m' if not no_error_formatting else ''
    VALID = f'{GREEN}✓{END}' if not no_error_formatting else ''
    INVALID = f'{RED}✗{END}' if not no_error_formatting else ''

    separator = ','
    if 'separator' in kwargs:
        separator = kwargs['separator']
    no_headrow = False
    if 'no_headrow' in kwargs:
        no_headrow = kwargs['no_headrow']

    use_choice_names = False
    if 'use_choice_names' in kwargs:
        use_choice_names = kwargs['use_choice_names']

    exit_on_error = False
    if 'exit_on_error' in kwargs:
        exit_on_error = kwargs['exit_on_error']

    no_error_messages = False
    if 'no_error_messages' in kwargs:
        no_error_messages = kwargs['no_error_messages']

    duplicate_headrow = False
    if 'duplicate_headrow' in kwargs:
        duplicate_headrow = kwargs['duplicate_headrow']

    #skip empty lines
    in_stream = filter(lambda x: x.strip(), in_stream)
    #check if there is any data to read
    try:
        first_line = next(in_stream)
    except StopIteration:
        print(f"Empty test stream", file=sys.stderr)
        return False

    #peek the first line to read it again
    reader = csv.reader(itertools.chain([first_line], in_stream), delimiter=separator)
    writer = csv.writer(sys.stdout, delimiter=separator)
    error_writer = csv.writer(sys.stderr, delimiter=separator)
    parsing_ok = True
    if not no_headrow:
        try: 
            headrow = next(reader)
            # print(f'Validating headrow', file=sys.stderr)
            messages, result = validate_headrow(headrow, function)
        except csv.Error as e:
            messages, result = [f"CSV parsing error: {e}"], False
            parsing_ok = False

        if result:
            writer.writerow(headrow)
            if duplicate_headrow:
                error_writer.writerow(headrow)
        else:
            print_error_messages(headrow, messages)
            if duplicate_headrow:
                writer.writerow(headrow)
            if exit_on_error:
                return parsing_ok

    while True:
        try:
            row = next(reader)
            if not use_choice_names:
                messages, result = validate_test_by_values(row, function, solver)
            else:
                messages, result = validate_test_by_choice_names(row, function, solver)
            if result:
                writer.writerow(row)
            else:
                print_error_messages(row, messages)
                if exit_on_error:
                    return parsing_ok

        except StopIteration:
            break
        except csv.Error as e:
            print(f"CSV parsing error while fetching next test: {e}", file=sys.stderr)
            parsing_ok = False
            continue
    return parsing_ok
