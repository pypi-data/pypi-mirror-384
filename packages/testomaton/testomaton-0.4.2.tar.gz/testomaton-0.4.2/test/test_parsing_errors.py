import pytest

import yaml
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from testomaton.model import *
from testomaton.tomato import DuplicateCheckLoader
from testomaton.errors import * 

# Choice element error test cases

# Choice name tests:
@pytest.fixture(autouse=True)
def clear_state():
    parsing_errors.clear()
    yield
    parsing_errors.clear()

def verify_parsing_errors(expected_error_counter):
    print_errors = True
    error_count = sum(expected_error_counter.values())
    if print_errors:
        print(f'Expected errors:')
        [print(f'{e}') for e in expected_error_counter]
        print(f'Actual errors:')
        [print(f'{error}') for error in parsing_errors]
    assert len(parsing_errors) == error_count

    if len(parsing_errors) > 0:
        parsing_errors_tuples = [(error.path, error.tag) for error in parsing_errors]
        parsing_errors_counter = Counter(parsing_errors_tuples)
        assert parsing_errors_counter == expected_error_counter

@pytest.mark.parametrize("choice_name, expected_error_tags", [
    ("Long_valid_name_for_test", []),
    ("valid_name", []),
    ("na::me", [("overChoice::'na::me'", ParsingErrorTag.NAME)]),
    ("':name:'", [("overChoice::':name:'", ParsingErrorTag.NAME)]),
    ("':name'", [("overChoice::':name'", ParsingErrorTag.NAME)]),
    ("'name:'", [("overChoice::'name:'", ParsingErrorTag.NAME)]),
    ("''", [("overChoice::''", ParsingErrorTag.NAME)]),
    ("'  '", [("overChoice::'  '", ParsingErrorTag.NAME)]),
    ("'  na::me  '", [("overChoice::'  na::me  '", ParsingErrorTag.NAME), ("overChoice::'  na::me  '", ParsingErrorTag.NAME)]),
    ])
def test_choice_name(clear_state, choice_name, expected_error_tags):
    over_choice_name = 'overChoice'
    expected_error_counter = Counter([(tag) for tag in expected_error_tags])
    choice_list_model = f"""\
        choice: {over_choice_name}
        choices:
        - choice: {choice_name}
        - choice: name1
        """
    choice_flow_model = f"""\
        choice: {over_choice_name}
        choices: [{choice_name}, name1]
        """

    choice_list_description = yaml.safe_load(choice_list_model)
    Choice(parent_path='', description=choice_list_description, inherited_labels=[])
    verify_parsing_errors(expected_error_counter)
    parsing_errors.clear()

    choice_flow_description = yaml.safe_load(choice_flow_model)
    Choice(parent_path='', description=choice_flow_description, inherited_labels=[])
    verify_parsing_errors(expected_error_counter)

# duplicate choice name test:
@pytest.mark.parametrize("mode, choice_name, expected_error_tag", [
("list", "name1", [ParsingErrorTag.CHILDREN]),
("flow", "name1", [ParsingErrorTag.VALUE])
])
def test_choice_duplicate_name(clear_state, mode, choice_name, expected_error_tag):
    over_choice_name = 'overChoice'
    expected_error_counter = Counter([(over_choice_name, tag) for tag in expected_error_tag])

    if mode == 'list':
        choice_model = f"""\
            choice: overChoice
            choices:
            - choice: {choice_name}
            - choice: name1
            """

    if mode == 'flow':
        choice_model = f"""\
            choice: overChoice
            choices: [{choice_name}, name1]
            """
    print(choice_model)

    choice_description = yaml.safe_load(choice_model)
    Choice(parent_path='', description=choice_description, inherited_labels=[])
    verify_parsing_errors(expected_error_counter)
    parsing_errors.clear

# choices and value tests
def test_choice_conflicting_value_and_choices(clear_state):
    choice_value_and_choices_model = f"""\
        choice: choice name
        value: some_name
        choices:
        - choice: name2
        - choice: name1
        """
    choice_description = yaml.safe_load(choice_value_and_choices_model)
    Choice(parent_path='', description=choice_description, inherited_labels=[])

    expected_error = Counter([('choice name', ParsingErrorTag.CHILDREN)])
    verify_parsing_errors(expected_error)

def test_choice_with_values(clear_state):
    choice_with_values_model = f"""\
        choice: overChoice
        choices:
        - choice: name1
          value: 1
        - choice: name2
          value: 2
        """
    choice_description = yaml.safe_load(choice_with_values_model)
    Choice(parent_path='', description=choice_description, inherited_labels=[])

    expected_error = Counter([])
    verify_parsing_errors(expected_error)

# Test choice labels
@pytest.mark.parametrize("labels, expected_error_tags", [
    ("[]", []),
    ("[l1]", []),
    ("[l1, l2]", []),
    ("", [ParsingErrorTag.LABEL]),
    ("l1", [ParsingErrorTag.LABEL]),
    ("l1, l2", [ParsingErrorTag.LABEL]),
    ("[{a: b, c: d}]", [ParsingErrorTag.LABEL]),
    ("[1, 2]", [ParsingErrorTag.LABEL]),
    ("[1, label]", [ParsingErrorTag.LABEL]),
])
def test_choice_labels(clear_state, labels, expected_error_tags):
    choice_with_values_model = f"""\
        choice: overChoice
        choices:
        - choice: name
          value: 1
          labels: {labels}
        """
    expected_error_counter = Counter([('overChoice::name', tag) for tag in expected_error_tags])
    choice_description = yaml.safe_load(choice_with_values_model)
    Choice(parent_path='', description=choice_description, inherited_labels=[])

    verify_parsing_errors(expected_error_counter)

@pytest.mark.parametrize("value, expected_error_tags", [
('Valid_value', []),
("''", []), # empty string
("'    '", []), # white string
(1, []),
(True, []),
(2.5, []),
("'[1, 2]'", []),
([1,2],[ParsingErrorTag.VALUE]),
([] ,[ParsingErrorTag.VALUE]),
({},[ParsingErrorTag.VALUE]),
])
def test_choice_value(value, expected_error_tags):
    choice_two_same_children_model = f"""\
    choice: overChoice
    choices:
    - choice: name
      value: {value}
    """
    expected_error_counter = Counter([('overChoice::name', tag) for tag in expected_error_tags])
    choice_description = yaml.safe_load(choice_two_same_children_model)
    Choice(parent_path='', description=choice_description, inherited_labels=[])

    verify_parsing_errors(expected_error_counter)

# Choice children tests
@pytest.mark.parametrize("child, expected_error", [
    ('choices',[("overChoice", ParsingErrorTag.CHILDREN)]),
    ('value',[("overChoice", ParsingErrorTag.CHILDREN)]),
])
def test_choice_two_same_children(child, expected_error):
    if child == 'choices':
        choice_two_same_children_model = f"""\
            choice: overChoice
            {child}: [one, two]
            choices: [three, four]
            """
    elif child == 'value':
        choice_two_same_children_model = f"""\
            choice: overChoice
            {child}: one
            value: two
            """
    
    with pytest.raises(ValueError, match='Duplicate key found'):
        choice_description = yaml.load(choice_two_same_children_model, Loader=DuplicateCheckLoader)
        Choice(parent_path='', description=choice_description, inherited_labels=[])

@pytest.mark.parametrize("child, expected_errors", [
('choices', []),
('value', []),
('parameter',[("overChoice", ParsingErrorTag.CHILDREN)]),
('unknown_child',[("overChoice", ParsingErrorTag.CHILDREN)]),
])
def test_choice_children(child, expected_errors):
    if child == 'choices':
        choice_two_same_children_model = f"""\
            choice: overChoice
            {child}: [one]
            """
    else:
        choice_two_same_children_model = f"""\
            choice: overChoice
            {child}: one
            """
    expected_error_counter = Counter([(tag) for tag in expected_errors])
    choice_description = yaml.safe_load(choice_two_same_children_model)
    Choice(parent_path='', description=choice_description, inherited_labels=[])

    verify_parsing_errors(expected_error_counter)


# path test
model_for_path_1 = """\
parameters:
- parameter: Parameter1
  choices:
  - choice: Choice1
    choices:
    - choice: invalid_::_choice
"""

model_for_path_2 = """\
parameters:
- parameter: Parameter1
  choices:
  - choice: Choice1
    choices:
    - choice: valid_choice
    - choice: Choice1_2
      choices:
      - choice: ':invalid_choice'
"""

model_for_path_3 = """\
parameters:
- parameter: Parameter1
  choices:
  - choice: Choice1
    choices:
    - choice: valid_choice
    - choice: Choice1_2
      choices:
      - choice: valid_choice2
      - choice: Choice1_2_3
        choices:
        - choice: invalid_value_choice
          value: []
"""

@pytest.mark.parametrize("model, expected_path", [
    (model_for_path_1, "Parameter1::Choice1::'invalid_::_choice'"),
    (model_for_path_2, "Parameter1::Choice1::Choice1_2::':invalid_choice'"),
    (model_for_path_3, "Parameter1::Choice1::Choice1_2::Choice1_2_3::invalid_value_choice"),
])

def test_choice_path(model, expected_path):
    parameters_description = yaml.safe_load(model)
    for parameter in parameters_description['parameters']:
        Parameter(parent_path='', description=parameter, inherited_labels=[])

    print(parsing_errors)

    for error in parsing_errors:
        assert error.path == expected_path

# more complex model tests
model_one = """\
parameters:
- parameter: Parameter1
  choices:
  - choice: Choice1
    choices:
    - choice: invalid_::_choice
    - choice: valid_choice
  - choice: Choice2
    value: {}
  - choice: Choice3
    value: valid_value
  - choice: Choice4
    choices:
    - choice: more_choices
      choices:
      - choice: ''
      - choice: ' '
      - choice: another_valid_choice
"""

expected_errors = [
    ("Parameter1::Choice1::'invalid_::_choice'", ParsingErrorTag.NAME),
    ("Parameter1::Choice2", ParsingErrorTag.VALUE),
    ("Parameter1::Choice4::more_choices::' '", ParsingErrorTag.NAME),
    ("Parameter1::Choice4::more_choices::''", ParsingErrorTag.NAME),
    ]

@pytest.mark.parametrize("model, expected_errors", [
    (model_one, expected_errors)
])

def test_choice_complex_model(model, expected_errors):
    expected_error_counter = Counter([(tag) for tag in expected_errors])
    parameters_description = yaml.safe_load(model)
    for parameter in parameters_description['parameters']:
        Parameter(parent_path='', description=parameter, inherited_labels=[])

    verify_parsing_errors(expected_error_counter)
    
# Parameter element error test cases

#parameter names test
@pytest.mark.parametrize("parameter_name, expected_errors", [
    ("Long_valid_name_for_test", []),
    ("valid_name", []),
    ("na::me", [("parameter1::'na::me'", ParsingErrorTag.NAME)]),
    ("':name:'", [("parameter1::':name:'", ParsingErrorTag.NAME)]),
    ("':name'", [("parameter1::':name'", ParsingErrorTag.NAME)]),
    ("'name:'", [("parameter1::'name:'", ParsingErrorTag.NAME)]),
    ("''", [("parameter1::''", ParsingErrorTag.NAME)]),
    ("'     '", [("parameter1::'     '", ParsingErrorTag.NAME)]),
    ("' \n '", [("parameter1::' '", ParsingErrorTag.NAME)]),

    # duplicate test case
    # ("name123", [("parameter1::name1", ParsingErrorTag.NAME)])
])
def test_parameter_name(parameter_name, expected_errors):
    parameter_name_model = f"""\
    parameter: parameter1
    parameters: 
    - parameter: {parameter_name}
    - parameter: name123
    - parameter: parameter2
    """

    expected_error_counter = Counter([(tag) for tag in expected_errors])
    parameters_description = yaml.safe_load(parameter_name_model)
    Parameter(parent_path='', description=parameters_description, inherited_labels=[])

    verify_parsing_errors(expected_error_counter)

# duplicate parameter name test:
@pytest.mark.parametrize("parameter_name, expected_error", [
("name1", [ParsingErrorTag.CHILDREN]),
])
def test_parameter_duplicate_name(clear_state, parameter_name, expected_error):
    parameter_name = "name1"
    parameter_name_model = f"""\
    parameter: parameter1
    parameters: 
    - parameter: {parameter_name}
      choices: [4, 5, 6]
    - parameter: name1
      choices: [1, 2, 3]
    """
    parameters_description = yaml.safe_load(parameter_name_model)
    Parameter(parent_path='', description=parameters_description, inherited_labels=[])


    assert len(parsing_errors) == len(expected_error)
    expected_errors_counter = Counter(expected_error)
    parsing_errors_tuples = [(error.path, error.tag) for error in parsing_errors]
    parsing_errors_counter = Counter(parsing_errors_tuples)
    assert parsing_errors_counter == expected_errors_counter

#parameter children test
@pytest.mark.parametrize("child, expected_errors", [
('choices', []),
('value',[("parameter1", ParsingErrorTag.CHILDREN)]),
('unknown_child',[("parameter1", ParsingErrorTag.CHILDREN)]),
])
def test_parameter_children(child, expected_errors):
    if child != 'parameters':
        parameter_children_model = f"""\
        parameter: parameter1
        {child}: [one]
        """
    else:
        parameter_children_model = f"""\
        parameter: parameter1
        {child}: 
        - parameter: one
          choices: [1, 2, 3]
        """
    print(parameter_children_model)
    expected_error_counter = Counter([(tag) for tag in expected_errors])
    parameter_description = yaml.safe_load(parameter_children_model)
    Parameter(parent_path='', description=parameter_description, inherited_labels=[])

    verify_parsing_errors(expected_error_counter)


# Tests for logic
# model_one = """\

# function: function1
# parameters:
# - parameter: parameter1
#   choices: [1, 2, 3, 4]
# - parameter: parameter2
#   choices: [1, 2, 3, 4, 5]
# - parameter: parameter3
#   choices: [1, 2, 3, 4, 5, 6]

# logic:
#   - constraint: invalid constraint
#     expression: "'parameter11' IS '2' AND 'parameter23' IS '2' => 'parameter3' IS '2'"
# """

# expected_errors = [
#     ("parameter11", ParsingErrorTag.CONSTRAINT),
#     ("parameter23", ParsingErrorTag.CONSTRAINT),
#     ]

# @pytest.mark.parametrize("model, expected_errors", [
#     (model_one, expected_errors)
# ])

# def test_constraint_parameter_names(model, expected_errors):
#     expected_error_counter = Counter([(tag) for tag in expected_errors])
#     function_description = yaml.safe_load(model)
#     Function(function_description)

#     verify_parsing_errors(expected_error_counter)


