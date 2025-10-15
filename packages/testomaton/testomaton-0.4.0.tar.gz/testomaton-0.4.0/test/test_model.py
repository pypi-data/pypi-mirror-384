import pytest

from pyaml import yaml
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from testomaton.model import *

# Tests for get_choice_names

test_get_choice_names_1 = """\
    parameter: p1
    choices:
    - choice: c1
    """
test_get_choice_names_result_1 = ['c1']

test_get_choice_names_2 = """\
    parameter: p1
    choices:
    - choice: c1
      choices: [c11, c12]
    """
test_get_choice_names_result_2 = ['c1::c11', 'c1::c12']

test_get_choice_names_3 = """\
    parameter: p1
    choices:
    - choice: c1
      choices: [c11, c12]
    - choice: c2
    """
test_get_choice_names_result_3 = ['c1::c11', 'c1::c12', 'c2']

@pytest.mark.parametrize("tested_class, model, expected_result", [
    ('ChoiceParent', test_get_choice_names_1, test_get_choice_names_result_1),
    ('ChoiceParent', test_get_choice_names_2, test_get_choice_names_result_2),
    ('ChoiceParent', test_get_choice_names_3, test_get_choice_names_result_3),
    ('Choice', test_get_choice_names_1, test_get_choice_names_result_1),
    ('Choice', test_get_choice_names_2, test_get_choice_names_result_2),
    ('Choice', test_get_choice_names_3, test_get_choice_names_result_3),
    ('Parameter', test_get_choice_names_1, test_get_choice_names_result_1),
    ('Parameter', test_get_choice_names_2, test_get_choice_names_result_2),
    ('Parameter', test_get_choice_names_3, test_get_choice_names_result_3),
])
def test__get_choice_names(tested_class, model, expected_result):
    if tested_class == 'Choice':
        parent = Choice(yaml.safe_load(model), None)
        print(f'Choice names: {parent.get_choice_names()}')
    elif tested_class == 'Parameter':
        parent = Parameter(yaml.safe_load(model), None)
        print(f'Choice names: {parent.get_choice_names()}')
    elif tested_class == 'ChoiceParent':
        parent = ChoiceParent(yaml.safe_load(model))
        print(f'Choice names: {parent.get_choice_names()}')
    print(f'Choice names : {parent.get_choice_names()}')
    assert parent.get_choice_names() == expected_result


# tests for get_parameter
test_get_parameter_1 = """\
    function: dinner
    parameters:
    - parameter: p1
    """    
test_get_parameter_result_1 = ['p1']

test_get_parameter_2 = """\
    function: dinner
    parameters:
    - parameter: p1
      parameters:
      - parameter: p2
        choice: c2
    """
test_get_parameter_result_2 = ['p2']

test_get_parameter_3 = """\
    function: dinner
    parameters:
    - parameter: p1
      parameters:
      - parameter: p2
        parameters:
        - parameter: p3
          choice: c3
    """
test_get_parameter_result_3 = ['p3']

@pytest.mark.parametrize("tested_class, model, param_name, expected_result", [
    ('ParameterParent', test_get_parameter_1, 'p1', test_get_parameter_result_1),
    ('ParameterParent', test_get_parameter_2, 'p1::p2', test_get_parameter_result_2),
    ('ParameterParent', test_get_parameter_3, 'p1::p2::p3', test_get_parameter_result_3),
    ('Function', test_get_parameter_1, 'p1', test_get_parameter_result_1),
    ('Function', test_get_parameter_2, 'p1::p2', test_get_parameter_result_2),
    ('Function', test_get_parameter_3, 'p1::p2::p3', test_get_parameter_result_3),
    ('Parameter', test_get_parameter_1, 'p1', test_get_parameter_result_1),
    ('Parameter', test_get_parameter_2, 'p1::p2', test_get_parameter_result_2),
    ('Parameter', test_get_parameter_3, 'p1::p2::p3', test_get_parameter_result_3),
])
def test__get_parameters(tested_class, model, param_name, expected_result):
    if tested_class == 'Function':
        parent = Function(None, yaml.safe_load(model))
        result = parent.get_parameter(param_name)
    elif tested_class == 'Parameter':
        parent = Parameter(yaml.safe_load(model), None)
        result = parent.get_parameter(param_name)
    elif tested_class == 'ParameterParent':
        parent = ParameterParent(yaml.safe_load(model), None)
        result = parent.get_parameter(param_name)
        
    print(f'Parameters : {parent.get_parameter(param_name)}')
    assert result.name == expected_result[0]


# tests for get_parameter_names
test_get_parameter_names_1 = """\
    parameters:
    - parameter: p1
    """    
test_get_parameter_names_result_1 = ['p1']

test_get_parameter_names_2 = """\
    parameters:
    - parameter: p1
      parameters:
      - parameter: p2
      - parameter: p3
        choice: c3
    """
test_get_parameter_names_result_2 = ['p1::p2', 'p1::p3']

test_get_parameter_names_3 = """\
    parameters:
    - parameter: p1
      parameters:
      - parameter: p2
      - parameter: p3
        choice: c3
    - parameter: p4
    """
test_get_parameter_names_result_3 = ['p1::p2', 'p1::p3', 'p4']

@pytest.mark.parametrize("tested_class, model, expected_result", [
    ('ParameterParent', test_get_parameter_names_1, test_get_parameter_names_result_1),
    ('ParameterParent', test_get_parameter_names_2, test_get_parameter_names_result_2),
    ('ParameterParent', test_get_parameter_names_3, test_get_parameter_names_result_3),
    ('Parameter', test_get_parameter_names_1, test_get_parameter_names_result_1),
    ('Parameter', test_get_parameter_names_2, test_get_parameter_names_result_2),
    ('Parameter', test_get_parameter_names_3, test_get_parameter_names_result_3),
])
def test__get_parameter_names(tested_class, model, expected_result):
    if tested_class == 'Parameter':
        parent = Parameter(yaml.safe_load(model), None)
    elif tested_class == 'ParameterParent':
        parent = ParameterParent(yaml.safe_load(model), None)
        
    print(f'Parameter names: {parent.get_parameter_names()}')
    assert parent.get_parameter_names() == expected_result


# tests for get_leaf_choice_names 

test_get_leaf_choice_names_simple = """\
    - parameter: main course
      choices: [🍲, 🍖]
    - parameter: dessert
      choices: [🍧, 🍰]
    """
test_get_leaf_choice_names_simple_expected = [['🍲', '🍖'], ['🍧', '🍰']]

test_get_leaf_choice_names_nested_parameters = """\
    - parameter: main course
      choices: [🍲, 🍖]
    - parameter: side_dishes
      parameters:
      - parameter: dessert
        choices: [🍧, 🍰]
      - parameter: drink
        choices: [🍷, 🍸]
    """
test_get_leaf_choice_names_nested_parameters_expected = [['🍲', '🍖'], ['🍧', '🍰'], ['🍷', '🍸']]

test_get_leaf_choice_names_nested_choices = """\
    - parameter: main course
      choices: [🍲, 🍖]
    - parameter: dessert
      choices: [🍧, 🍰]
    - parameter: drink
      choices: 
      - choice: alkoholic
        choices: [🍷, 🍸]
      - choice: non alkoholic
        choices: [🥛, 🍵]
    """
test_get_leaf_choice_names_nested_choices_expected = [['🍲', '🍖'], ['🍧', '🍰'], ['alkoholic::🍷', 'alkoholic::🍸', 'non alkoholic::🥛', 'non alkoholic::🍵']]

test_get_leaf_choice_names_nested_parameter_and_choices = """\
    - parameter: main course
      choices: [🍲, 🍖]
    - parameter: side_dishes
      parameters:
      - parameter: dessert
        choices: [🍧, 🍰]
      - parameter: drink
        choices: 
        - choice: alkoholic
          choices: [🍷, 🍸]
        - choice: non alkoholic
          choices: [🥛, 🍵]
    - output parameter: milk
      default value: 10
    """

test_get_leaf_choice_names_nested_parameter_and_choices_expected = [['🍲', '🍖'], ['🍧', '🍰'], ['alkoholic::🍷', 'alkoholic::🍸', 'non alkoholic::🥛', 'non alkoholic::🍵'], ['10']]

@pytest.mark.parametrize("tested_class, model, expected_result", [
    ('ParameterParent', test_get_leaf_choice_names_simple, test_get_leaf_choice_names_simple_expected),
    ('ParameterParent', test_get_leaf_choice_names_nested_parameters, test_get_leaf_choice_names_nested_parameters_expected),
    ('ParameterParent', test_get_leaf_choice_names_nested_choices, test_get_leaf_choice_names_nested_choices_expected),
    ('ParameterParent', test_get_leaf_choice_names_nested_parameter_and_choices, test_get_leaf_choice_names_nested_parameter_and_choices_expected),
    ('Function', test_get_leaf_choice_names_simple, test_get_leaf_choice_names_simple_expected),
    ('Function', test_get_leaf_choice_names_nested_parameters, test_get_leaf_choice_names_nested_parameters_expected),
    ('Function', test_get_leaf_choice_names_nested_choices, test_get_leaf_choice_names_nested_choices_expected),
    ('Function', test_get_leaf_choice_names_nested_parameter_and_choices, test_get_leaf_choice_names_nested_parameter_and_choices_expected),
    ('Parameter', test_get_leaf_choice_names_simple, test_get_leaf_choice_names_simple_expected),
    ('Parameter', test_get_leaf_choice_names_nested_parameters, test_get_leaf_choice_names_nested_parameters_expected),
    ('Parameter', test_get_leaf_choice_names_nested_choices, test_get_leaf_choice_names_nested_choices_expected),
    ('Parameter', test_get_leaf_choice_names_nested_parameter_and_choices, test_get_leaf_choice_names_nested_parameter_and_choices_expected),
])
def test__get_leaf_choice_names(tested_class, model, expected_result):
    if tested_class == 'Function':
        model = 'function: f1\n' + 'parameters:\n' + model
        parent = Function(None, yaml.safe_load(model))
    elif tested_class == 'Parameter':
        model = 'parameters:\n' + model
        parent = Parameter(yaml.safe_load(model), None)
    elif tested_class == 'ParameterParent':
        model = 'function: f1\n' + 'parameters:\n' + model
        parent = ParameterParent(yaml.safe_load(model), None)
        
    print(f'Leaf Choices: {parent.get_leaf_choice_names()}')
    assert parent.get_leaf_choice_names() == expected_result


    

# tests for get_constraints
constraint_parent_element_name = 'P'  
test_get_constraints_simple = \
f"""
  parameters:
  - parameter: main course
    choices: [🍲,🍖]
  - parameter: dessert
    choices: [🍧,🍰]

  logic:
  - constraint: meat always to cake
    expression: "'dessert' IS '🍰' => 'main course' IS '🍖'"
"""
test_get_constraints_simple_expected = [
  (constraint_parent_element_name, 'meat always to cake', (None,"'dessert' IS '🍰' => 'main course' IS '🍖'"))
]

test_get_constraints_medium = """\
  parameters:
  - parameter: main course
    choices: [🍲,🍖]
  - parameter: dessert
    choices: [🍧,🍰]
  - parameter: drink
    choices: [🍷,🍸]

  logic:
  - constraint: Always meat to cake and wine
    expression: "'drink' IS '🍷' AND 'dessert' IS '🍰' => 'main course' IS '🍖'"
    """
test_get_constraints_medium_expected = [
  (constraint_parent_element_name, 'Always meat to cake and wine', (None,"'drink' IS '🍷' AND 'dessert' IS '🍰' => 'main course' IS '🍖'"))
]

test_get_constraints_hard = """\
  parameters:
    - parameter: salad
      choices: [🥗, 🍅, 🌶, 🍆, 🥦]
    - parameter: main course
      choices: [🍲, 🍖, 🥩, 🐟, 🍗]
    - parameter: dessert
      choices: [🍨, 🍦, 🍧, 🍰]
    - parameter: drink
      choices: [🍷, 🍸, 🍺, 🍹 ]

  logic:
  - constraint: martini always to cake with fish
    expression: "'dessert' IS '🍰' AND 'main course' IS '🐟' => 'drink' IS '🍸'"
  - constraint: no beer and chilli
    expression: "NOT ('salad' IS '🌶' AND 'drink' IS '🍺')"

    """
test_get_constraints_hard_expected = [
  (constraint_parent_element_name, 'martini always to cake with fish', (None,"'dessert' IS '🍰' AND 'main course' IS '🐟' => 'drink' IS '🍸'")), 
  (constraint_parent_element_name, 'no beer and chilli', (None,"NOT ('salad' IS '🌶' AND 'drink' IS '🍺')"))
]

@pytest.mark.parametrize("tested_class, model, expected_result", [
    ('Parameter', test_get_constraints_simple, test_get_constraints_simple_expected),
    ('Parameter', test_get_constraints_medium, test_get_constraints_medium_expected),
    ('Parameter', test_get_constraints_hard, test_get_constraints_hard_expected),
])
def test__get_constraints(tested_class, model, expected_result):
  if tested_class == 'Parameter':
    prefix = (
    "parameters:\n"
    "- parameter: " + constraint_parent_element_name + "\n"
    )
    model = prefix + model
    print(f"\nModel:\n{model}")
    parsed_model = yaml.safe_load(model)
    descr = parsed_model['parameters'][0]
    # Pass the parsed model to the function
    parent = Parameter(descr, None)

  # Capture the actual constraints for debugging
  actual_constraints = parent.get_constraints()
  print(f"Actual constraints: {actual_constraints}")
  print(type(actual_constraints))
  assert actual_constraints == expected_result

