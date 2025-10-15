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

from copy import deepcopy
from enum import Enum

from testomaton.errors import ParsingErrorTag, report_parsing_error

global_params = {}

ignore_constraints = False
ignore_assignments = False
global_whitelist = []
global_blacklist = []
parameters_blacklist = []
parameters_whitelist = []
choices_blacklist = []
choices_whitelist = []
constraints_blacklist = []
constraints_whitelist = []
assignments_blacklist = []
assignments_whitelist = []

def should_parse_element(parent_path, description, specific_whitelist=[], specific_blacklist=[], extra_labels=[]):
    """
    Check if an element described by 'description' should be parsed based on global and local whitelists and blacklists, 
    as well as other conditions.

    Args:
        description (dict): The description of the element
        specific_whitelist (list): The list of labels that are allowed
        specific_blacklist (list): The list of labels that are not allowed
        extra_labels (list): The list of labels that are inherited from the parent. Those are added to the labels in the description.

    Returns: 
        bool: True if the element should be parsed, False otherwise.

    Examples: 
        >>> should_parse_element('choice')
        True
        >>> should_parse_element('constraint', ignore_constraints=True)
        False
    """
    #if description is a primitive type, return true and allow parsing. This is used for choices defined in a flow
    if not isinstance(description, dict):
        return True
    
    #get the keys of the dictionary and set the element type to the first key
    element_type = list(description.keys())[0]
    if element_type == 'constraint' and ignore_constraints:
        return False
    if element_type == 'assignment' and ignore_assignments:
        return False
    
    name = description[element_type]

    if isinstance(name, int) or isinstance(name, float):
        name = str(name)

    path = parent_path + '::' + name if parent_path else name
    #if labels are in the description, set the labels list to the labels in the description 
    labels = []
    if 'labels' in description:
        labels = deepcopy(description['labels'])
        if not isinstance(labels, list):
            report_parsing_error(path, ParsingErrorTag.LABEL, f"Invalid labels: {labels}. Labels must be a list")
            return False
        if not all(isinstance(label, str) for label in labels):
            not_strings = [label for label in labels if not isinstance(label, str)]
            report_parsing_error(path, ParsingErrorTag.LABEL, f"Invalid labels: {not_strings}. Labels must be strings")
            return False
    labels.extend(extra_labels)
    labels.append(name)
    
    #set the blacklist to the union of the global_blacklist and the specific_blacklist
    blacklist = list(set(global_blacklist) | set(specific_blacklist))    
    #set the whitelist to the union of the global_whitelist and the specific_whitelis
    whitelist = list(set(global_whitelist) | set(specific_whitelist))
    
    #if the whitelist is not empty, check if any of the labels in 'labels' are in the whitelist, if not return false
    if len(whitelist) > 0:
        if len([label for label in labels if label in whitelist]) == 0:
            return False
    #if the blacklist is not empty, check if any of the labels in 'labels' are in the blacklist, if so return false
    if len(blacklist) > 0:
        if len([label for label in labels if label in blacklist]) > 0:
            return False
    
    return True

def get_element_name(description, element_type):
    if element_type in description:
        if isinstance(description[element_type], dict):
            #if the element is a dictionary, it means that the name
            # of the element was not defined. Return '' so the error
            # can be reported in the validation step
            return ''
        return description[element_type]
    return None

def validate_dict(parent_path, description, allowed_keys, mutual_exclusions):
    """
    Check a dictionary if the key of a node is allowed in the context and check if there are any mutually exlusive keys. If the key is not 
    allowed in the context or there are mutualy exlusive keys together, report an error. mutual_exclusions is a dictionary: 
    {type: [mutually exclusive types]}, for example {'choices': ['parameters', 'logic']}
    """
    keys_set = description.keys()
    allowed_keys_copy = deepcopy(allowed_keys)
    allowed_keys_copy.add('metadata')
    if keys_set is None:
        return

    #check if any key is not in the allowed keys set
    forbidden_keys= [c for c in keys_set if c not in allowed_keys_copy]
    if len(forbidden_keys) > 0:
        report_parsing_error(parent_path, ParsingErrorTag.CHILDREN, f"['{', '.join(forbidden_keys)}'] not allowed in this context")

    for child_type in [t for t in keys_set if t in mutual_exclusions]:
        conflicting_types = [t for t in keys_set if t in mutual_exclusions[child_type]]    
        if len(conflicting_types) > 0:
            report_parsing_error(parent_path, ParsingErrorTag.CHILDREN, f"Tags ['{child_type}'] and ['{', '.join(conflicting_types)}'] are mutually exclusive")

def validate_list(path, list_to_validate, allowed_set):
    """
    checks list to contain only elements that are dictionaries. The dictionaries on the list 
    shall have the first element with a key from an allowed set. The value of the first element 
    should be a primitive type (string or number) and they shall be unique in the list.
    """
    try:
        element_types = [list(element.keys())[0] for element in list_to_validate]
    except:
        report_parsing_error(path, ParsingErrorTag.INCOMPLETE_MODEL, f"List with faulty or None elements detected: {list_to_validate}")

    if list_to_validate is None:
        return
    if len(list_to_validate) == 0:
        report_parsing_error(path, ParsingErrorTag.INCOMPLETE_MODEL, f"Empty list")
    forbidden_element = [c for c in element_types if c not in allowed_set]
    if len(forbidden_element) > 0:
        report_parsing_error(path, ParsingErrorTag.CHILDREN, f"['{', '.join(forbidden_element)}'] not allowed in this context")
    for element_type in allowed_set:
        names = [child[element_type] for child in list_to_validate if element_type in child]
        duplicate_names = {name for name in names if names.count(name) > 1}
        if len(duplicate_names) > 0:
            duplicate_names = list(set(duplicate_names))
            report_parsing_error(path, ParsingErrorTag.CHILDREN, f"Duplicate {element_type} names: ['{', '.join(duplicate_names)}']")

def validate_name(name, parent_path):
    path = parent_path + "::" + name + "" if parent_path else name

    if name.strip() != name:
        report_parsing_error(path, ParsingErrorTag.NAME, f"Invalid element name: ['{name}']. Name cannot have leading or trailing whitespace")
    if name == '':
        report_parsing_error(path, ParsingErrorTag.NAME, f"Invalid element name: ['{name}']. Name cannot be empty")
    if '::' in name or name.startswith(':') or name.endswith(':'):
        report_parsing_error(path, ParsingErrorTag.NAME, f"Invalid element name: ['{name}']. Name cannot contain '::' or start or end with ':'")
    if '\n' in name:
        report_parsing_error(path, ParsingErrorTag.NAME, f"Invalid element name: ['{name}']. Name cannot contain newline characters")

def validate_labels(path, labels):
    for label in labels:
        if label == '':
            report_parsing_error(path, ParsingErrorTag.LABEL, f"Invalid label: ['{label}']. Label cannot be empty")
        if '::' in label:
            report_parsing_error(path, ParsingErrorTag.LABEL, f"Invalid label: ['{label}']. Label cannot contain '::'")
        if ',' in label:
            report_parsing_error(path, ParsingErrorTag.LABEL, f"Invalid label: ['{label}']. Label cannot contain ','")

class AbstractNode:
    """
    Parent class for all nodes in the model. All nodes are required to have a name and possibly labels.
    A node's path is the concatenation of the parent path and the node's name, separated by '::'.
    """
    def __init__(self, name, parent_path, labels):
        self.name = str(name)
        self.parent_path = parent_path
        self.path = parent_path + "::" + self.name if parent_path else self.name
        self.labels = labels

        validate_name(name, parent_path)
        validate_labels(self.path, labels)

    def __str__(self):
        return self.path

    def __repr__(self):
        return str(self)

class LogicNode(AbstractNode):
    """
    Parent class for nodes that define logic in the model: aliases, constraints and assignments. 
    All logic nodes have an expression that is a string, which defines the logic. For each type
    of logic node, the expression may have different syntax.
    """
    def __init__(self, name, parent_path, description, logic_type):
        labels = description['labels'] if 'labels' in description else []
        super().__init__(name, parent_path, labels)
        self.expression = description['expression']
        path = parent_path + '::' + '___LOGIC___' + '::' + name

        allowed_keys = {logic_type, 'expression', 'labels'}
        conflicts = {}
        validate_dict(path, description, allowed_keys, conflicts)
    def __str__(self):
        return f'{self.name}: {self.expression}'

    def __repr__(self):
        return str(self)

class Alias(LogicNode):
    def __init__(self, parent_path, description):
        logic_type = 'alias'
        super().__init__(description['alias'], parent_path, description, logic_type)

class Constraint(LogicNode):
    def __init__(self, parent_path, description):
        logic_type = 'constraint'
        super().__init__(description['constraint'], parent_path, description, logic_type)


class Assignment(LogicNode):
    def __init__(self, parent_path, description):
        logic_type = 'assignment'
        super().__init__(description['assignment'], parent_path, description, logic_type)

class ParameterParent(AbstractNode):
    """ 
    Parent class for parameters, which includes all methods for handling parameters in the model. 
    Where are parameters, are constraints, so each ParameterParenty can potentially have logic element.
    """
    def __init__(self, name, parent_path,
        parameters_description, logic_description, 
        labels, **kwargs) -> None:
        """
        Initialize a ParameterParent object.
        
        Args:
            name (str): The name of the parameter.
            parent_path (str): The path of the parent node.
            parameters_description (list): The description of the sub-parameters. May be None.
            logic_description (list): The description of the logic elements. May be None.
            labels (list): Element's labels.

        Attributes:
            parameters (list): A list of sub-parameters, each being represented as a parameter object.
            output_parameters (list): A list of sub-output parameters.  A subset of parameters list.
            aliases (dict): A dictionary of aliases.
            constraints (dict): A dictionary of constraints.
        
        Returns:
            None
        """
        super().__init__(name=name, parent_path=parent_path, labels=labels, **kwargs)

        self.parameters = []
        self.output_parameters = []
        if parameters_description is not None:
            self.__parse_parameters(parameters_description, labels)
            validate_list(self.path, parameters_description, {'parameter', 'linked parameter', 'output parameter'})

        self.aliases = []
        self.constraints = []
        if logic_description is not None:
            self.__parse_logic(logic_description, labels)

    def get_leaf_choice_names(self):
        # Get all leaf parameters with full path
        parameter_names = self.get_all_parameter_names()
        result = []

        for name in parameter_names:
            if name is None:
                continue
            try:
                p = self.get_parameter(name)
                if not p.parameters:
                    # If the parameter has no sub-parameters, return its own choices
                    result.append(p.get_choice_names())  # Append the list of choices as a group
                else:
                    # If the parameter has sub-parameters, recursively get their choices
                    result.append(p.get_leaf_choice_names())
            except:
                continue

        return result
    
    def get_all_parameter_names(self, current_path=''):
        result = []
        for parameter in self.parameters:
            if isinstance(parameter, OutputParameter):
                result.append(parameter.name)
            elif parameter.parameters:
                if current_path == '':
                    result.extend(parameter.get_all_parameter_names(parameter.name))
                else:
                    result.extend(parameter.get_all_parameter_names(current_path + '::' + parameter.name))
            else:
                if(current_path == ''): 
                    result.append(parameter.name)
                else:
                    result.append(current_path + '::' + parameter.name)
        return result
    
    def get_parameters_by_labels(self, labels):
        result = []
        for name in self.get_all_parameter_names():
            parameter = self.get_parameter(name)
            if any(label in parameter.labels for label in labels):
                result.append(parameter)
            if isinstance(parameter, ParameterParent):
                result.extend(parameter.get_parameters_by_labels(labels))
        return result

    def get_parameter(self, name):
        if name is None:
            return None
        
        if '::' in name:
            tokens = name.split('::')
            child_name = tokens[0]
            remains = '::'.join(tokens[1:])
            #iterate through the parameters and recursively call get_parameter to get each parameter
            for parameter in self.parameters:
                if parameter.name == child_name:
                    return parameter.get_parameter(remains)
        else:
            #iterate through the parameters and return the parameter with the given name
            for parameter in self.parameters:
                if parameter.name == name:
                    return parameter
        return None
   

    def get_parameter_index(self, name):
        """ Get the index of a parameter by name."""
        for i, parameter in enumerate(self.get_all_parameter_names()):
            if parameter == name:
                return i
        return None

    def filter_constraints(self, whitelist, blacklist):

        def constraint_included(constraint, whitelist, blacklist):
            whitelist_set = {c.strip() for c in whitelist.split(',')} if whitelist is not None else None
            blacklist_set = {c.strip() for c in blacklist.split(',')} if blacklist is not None else None

            labels = constraint.labels + [constraint.name]
            if whitelist is not None:
                return len(set(labels) & whitelist_set) > 0
            if blacklist is not None:
                return len(set(labels) & blacklist_set) == 0
            return True

        if whitelist is not None and blacklist is not None:
            raise Exception(f'Both constraints whitelist and blacklist are defined for parameter {self.name}')
        
        self.constraints = [c for c in self.constraints if constraint_included(c, whitelist, blacklist)]
        [p.filter_constraints(whitelist, blacklist) for p in self.parameters]

    def get_aliases(self):
        result = [(a.name, a.expression) for a in self.aliases]
        for parameter in [p for p in self.parameters if isinstance(p, ParameterParent)]:
            for name, expression in parameter.get_aliases():
                result.append((parameter.name + '::' + name, expression))
        return result

    def get_constraints(self):
        result = [(c.name, c.expression) for c in self.constraints]    
        for parameter in [p for p in self.parameters if isinstance(p, ParameterParent)]:
            for name, expression in parameter.get_constraints():
                result.append((parameter.name + '::' + name, expression))
        return result
    
    def __parse_parameters(self, parameters_description, labels):
        parent_path = deepcopy(self.path) 
        if '___PARAMETERS___' not in parent_path.split('::'):
            parent_path += '::___PARAMETERS___'

        for parameter in parameters_description:
            if not should_parse_element(self.path, parameter, parameters_whitelist, parameters_blacklist, labels):
                continue
            
            #if description has 'output parameter'
            if 'output parameter' in parameter:
                param = OutputParameter(parent_path=parent_path, description=parameter)
                self.parameters.append(param)
                self.output_parameters.append(param)   

            #if description has 'linked parameter' key, copies and modifies parameter before appending to the parameters list
            elif 'linked parameter' in parameter:
                linked_to = parameter['linked to']
                linked_name = parameter['linked parameter']
                whitelist = parameter['constraints whitelist'] if 'constraints whitelist' in parameter else None
                blacklist = parameter['constraints blacklist'] if 'constraints blacklist' in parameter else None
                if whitelist is not None and blacklist is not None:
                    report_parsing_error(self.path, ParsingErrorTag.CHILDREN, f"Linked parameter ['{linked_name}'] cannot have both constraints whitelist and blacklist")
                    continue
                if linked_to not in global_params:
                    path = '___GLOBAL_PARAMETERS___' + '::' + parameter['linked parameter']
                    report_parsing_error(path, ParsingErrorTag.CHILDREN, f"Linked parameter ['{linked_to}'] not found in global parameters")
                    continue
                copy = deepcopy(global_params[linked_to]) 
                copy.name = linked_name
                copy.filter_constraints(whitelist, blacklist)
                self.parameters.append(copy)
            elif 'parameter' in parameter:
                self.parameters.append(Parameter(parent_path=parent_path, description=parameter, inherited_labels=labels))

    def __parse_logic(self, logic_description, labels):
        for element in logic_description:
            if 'alias' in element:
                self.aliases.append(Alias(parent_path=self.path, description=element))
            elif 'constraint' in element:
                if not should_parse_element(self.path, element, constraints_whitelist, constraints_blacklist):
                    continue
                self.constraints.append(Constraint(parent_path=self.path, description=element))

class ChoiceParent(AbstractNode):
    """ 
    Parent class for choices, which includes all methods for handling choices in the model
    """
    def __init__(self, name, parent_path, choices_description, labels, **kwargs) -> None:
        super().__init__(name=name, parent_path=parent_path, labels=labels, **kwargs)
        self.choices = []
        
        #description is a directory created from parsing the yaml file
        if choices_description is not None:
            # validate the content of choices description. It must be a list, bacause both yaml list and flows 
            # are converted to list in the parser.
            if isinstance(choices_description, list):
                if all(isinstance(c, dict) for c in choices_description):
                    # The list is a list of dictionaries, which means it is a list of choices
                    validate_list(self.path, choices_description, {'choice'})
                else:
                    #We parsed a flow. Manually check for duplicate choice names
                    duplicates = [n for n in choices_description if choices_description.count(n) > 1]
                    if len(duplicates) > 0:
                        duplicates = list(set(duplicates))
                        report_parsing_error(self.path, ParsingErrorTag.VALUE, f'Duplicate choice names {duplicates}')
            else:
                report_parsing_error(self.path, ParsingErrorTag.VALUE, f'Choices must be a list')
                
            parent_path = deepcopy(self.path)
            if '___CHOICES___' not in parent_path.split('::'):
                parent_path += '::___CHOICES___'
            for choice_element in choices_description:
                if not should_parse_element(self.path, choice_element, choices_whitelist, choices_blacklist, labels):
                    continue
                self.choices.append(Choice(parent_path, choice_element, labels))

    def get_choice_names(self, current_path=''):
        result = []
        for choice in self.choices:
            try:
                if choice.choices:
                    if current_path == '':
                        result.extend(choice.get_choice_names(choice.name))
                    else:
                        result.extend(choice.get_choice_names(current_path + '::' + choice.name))
                else:
                    if(current_path == ''): 
                        result.append(choice.name)
                    else:
                        result.append(current_path + '::' + choice.name)
            except:
                continue
        return result            
        
    def get_choice(self, name):
        """
        Get a choice by name.
    
        Args:
            name (str): The name of the choice to get.
            
        Returns:
            choice: The choice object with the given name.
            or None if the choice is not found.
        """
        #if the name contains '::', split the name into tokens
        if '::' in name:
            tokens = name.split('::')
            child_name = tokens[0]
            #set the remains to the concatenation of the tokens from index 1, separated by '::'
            remains = '::'.join(tokens[1:])
        
            #for each choice in the choices list, if the name of the choice is equal to the child_name, 
            #recursively call get_choice with the remains
            for choice in self.choices:
                if choice.name == child_name:
                    return choice.get_choice(remains)
        else:
            #for each choice in the choices list, if the name of the choice 
            #is equal to the name, return the choice
            for choice in self.choices:
                if choice.name == name:
                    return choice
        return None
    
    def get_choices_by_label(self, label):
        result = []
        
        for choice_name in self.get_choice_names():
            selected_choice = self.get_choice(choice_name) 
            if selected_choice is not None:
                choice_labels = selected_choice.labels
                if (label in choice_labels):
                    result.append(choice_name)
        return result

class Choice(ChoiceParent):
    def __init__(self, parent_path, description, inherited_labels):        
        self.value = None
        name = None
        subchoices = None
        labels = inherited_labels.copy()
        
        #description is a yaml node
        if isinstance(description, dict):
            if 'labels' in description:
                labels.extend(description['labels'])

            allowed_keys = {'choice', 'choices', 'value', 'labels'}
            conflicts = {'choices': ['value']}
            name = get_element_name(description, 'choice')
            if name is None:
            #     # This should never happen, as the content of choices list is validated in the parent element.
            #     # If it happens, it is a bug in the parser.
                report_parsing_error(parent_path, ParsingErrorTag.CHILDREN, f"Invalid choice element {list(description.keys())[0]}. Choice must have a 'choice' key")
                return
            
            if isinstance(name, int) or isinstance(name, float):
                name = str(name)

            path = parent_path + '::' + name
            validate_dict(path, description, allowed_keys, conflicts)

            if 'value' in description:
                value = description['value']
            else:
                value = name

            if 'choices' in description:
                subchoices = description['choices']
        # description is a string - choice was defined in a flow
        else:
            name = str(description)            
            value = name

        super().__init__(name=name, parent_path=parent_path, choices_description=subchoices, labels=labels)

        if not subchoices:
            if self.__check_value(value, self.path):
                self.value = str(value)

    def __str__(self):
        return f'{self.name}: {self.value}'
    
    def __repr__(self):
        return str(self)
    
    def __check_value(self, value, path):
        if not isinstance(value, (str, int, bool, float)) :
            report_parsing_error(path, ParsingErrorTag.VALUE, f'The value must be a string, int, bool or float, it is currently {type(value).__name__}')
            return False
        return True

class OutputParameter(ChoiceParent):
    """
    A class used to represent an output parameter in a model. 

    Output parameters do not have choices which are used in combinatoric test generation.
    However, their value can be defined based on a precondition defined in assignments
    
    Attributes:
        name (str): The name of the output parameter.
        default_value (str): The default value linked to the output parameter.
        parameters (list): The list of parameters that are children of the current output parameter.
    
    Methods:
        get_choice_names: returns a default_value which has been predefined.
    """
    def __init__(self, parent_path, description):
        """
        Initialize an OutputParameter object.
        
        Args:
            description (dict): The description of the output parameter.
            
        Attributes:
            name (str): The name of the output parameter.
            default_value (str): The default value linked to the output parameter.
            parameters (list): A list of sub-parameters, each being represented as a parameter object.
        
        Returns:
            None
        """
        name = ''
        if 'output parameter' in description:
            name = str(description['output parameter'])

        labels = []
        if 'labels' in description:
            labels = description['labels']

        super().__init__(name=name, parent_path=parent_path,
            choices_description=None,
            labels=labels)

        self.default_value = str(description['default value'])
        self.parameters = []

    def __str__(self):
        return f'{self.name}: {self.default_value}'
    
    def __repr__(self):
        return str(self)
    
    def is_structure(self):
        return len(self.parameters) > 0

    def get_choice_names(self):
        return [str(self.default_value)]
    
class Parameter(ParameterParent, ChoiceParent):
    def __init__(self, parent_path, description, inherited_labels) -> None:
        """
        Initialize a Parameter object.
        
        Args:
            description (dict): The description of the parameter.
            inherited_labels (list): The list of labels that are inherited from the parent. Defaults to an empty list.

        Raises:
            Exception: If the parameter has both 'parameters' and 'choices' keys. This is not allowed.
            
        Attributes:
            name (str): The name of the parameter.
            choices (list): A list of sub-choices, each being represented as a choice object.
            parameters (list): A list of sub-parameters, each being represented as a parameter object.
            aliases (dict): A dictionary of aliases.
            constraints (dict): A dictionary of constraints.
        
        Returns:
            None
        """
        name = None
        allowed_keys = {'parameter','parameters', 'choices', 'logic', 'labels'}
        conflicts = {'parameters': ['choices']}

        name = get_element_name(description, 'parameter')
        if name is None: 
            return 
        else:
            path = parent_path + '::' + name
            validate_dict(path, description, allowed_keys, conflicts)

        labels = inherited_labels
        if 'labels' in description:
            labels.extend(description['labels'])

        subparameters = None
        if 'parameters' in description:
            subparameters = description['parameters']
            allowed_children = {'parameter', 'linked parameter', 'output parameter'}

            validate_list(path, subparameters, allowed_children)

        logic = None
        if 'logic' in description:
            logic = description['logic']
            allowed_children = {'constraint', 'alias', 'assignment'}
            
            path = path + '::' + 'logic'
            validate_list(path, logic, allowed_children)

        choices = None
        if 'choices' in description:
            choices = description['choices']
    
        subparameters_count = len(subparameters) if subparameters is not None else 0
        choices_count = len(choices) if choices is not None else 0

        if subparameters_count == 0 and choices_count == 0:
            report_parsing_error(path, ParsingErrorTag.INCOMPLETE_MODEL, f"Parameter must have defined at least one parameter or one choice")
        
        super().__init__(name=name, parent_path=parent_path, 
            parameters_description=subparameters, logic_description=logic, 
            choices_description=choices, labels=labels)
                
    def __str__(self):
        result = f'{self.name}'
        if self.parameters:
            result += '('
            for parameter in self.parameters:
                result += f'{parameter}, '
            result = result[:-2] + ')'
        return result
    
    def __repr__(self):
        return str(self)

    def is_structure(self):
        return len(self.parameters) > 0

    def get_structures(self):
        return [p for p in self.parameters if p.is_structure()]

class Function(ParameterParent):
    def __init__(self, description):
        """
        Initialize a Function object.
        
        Args:
            description (dict): The description of the function.
        
        Attributes:
            name (str): The name of the function.
            parameters (list): A list of sub-parameters, each being represented as a parameter object.
            output_parameters (list): A list of sub-output parameters, each being represented as an output parameter object.
            aliases (dict): A dictionary of aliases.
            constraints (dict): A dictionary of constraints.
            assignments (dict): A dictionary of assignments.
        
        Returns:
            None
        """
        if 'function' not in description:
            raise ValueError("The 'function' key is missing in the description.")        

        name = str(description['function'])
        parameters = description['parameters'] if 'parameters' in description else None
        logic = description['logic'] if 'logic' in description else None
        labels = description['labels'] if 'labels' in description else []

        allowed_keys = {'function', 'parameters', 'logic'}
        conflicts = {}
        path = '___FUNCTIONS___::' + name
        validate_dict(path, description, allowed_keys, conflicts)

        super().__init__(name=name, parent_path='___FUNCTIONS___', 
            parameters_description=parameters, 
            logic_description=logic, labels=labels)
        
        if parameters is None:
            report_parsing_error(path, ParsingErrorTag.INCOMPLETE_MODEL, f"Function must contain parameters list")
        elif len(parameters) == 0:
            report_parsing_error(path, ParsingErrorTag.INCOMPLETE_MODEL, f"Function must contain at least one parameter")

        self.assignments = []
        if logic:
            for element in logic:
                #if it is an assignment, check if it should be parsed and set name and expression
                if 'assignment' in element:
                    if not should_parse_element(self.path, element, assignments_whitelist, assignments_blacklist):
                        continue
                    self.assignments.append(Assignment(parent_path=self.path, description=element))
                
    def __str__(self):
        return f'{self.name}({[parameter.name for parameter in self.parameters]})'
    
    def get_structures(self):
        return [p for p in self.parameters if p.is_structure()]
    
    def get_generator_input(self):
        return self.get_all_parameter_names(), self.get_leaf_choice_names()

def get_function_names(model, whitelist, blacklist):
    """
    Get all functions in a model file filtered by the black or whitelist.
    
    Args:
        model (dict): The model object.
        whitelist (list): The list of names and labels that are allowed.
        blacklist (list): The list of names and labels that are not allowed.
        
    Returns:
        list: A list of function names.
    """
    return [f['function'] for f in model['functions'] if 'function' in f and should_parse_element('functions', f, whitelist, blacklist)]

def parse_function(model, function_name, **kwargs):
    """ 
    Parse a function from a model file.
    
    Args:
        file (str): The path to the model file.
        function_name (str): The name of the function to parse. Defaults to None.
        **kwargs: Additional keyword arguments.
        
    Returns:
        function: The function object.
    """

    global ignore_constraints, ignore_assignments
    global global_whitelist, global_blacklist
    global parameters_blacklist, parameters_whitelist
    global choices_blacklist, choices_whitelist
    global constraints_blacklist, constraints_whitelist
    global assignments_blacklist, assignments_whitelist
    
    if 'ignore_constraints' in kwargs:
        ignore_constraints = kwargs['ignore_constraints']
    if 'ignore_assignments' in kwargs:
        ignore_assignments = kwargs['ignore_assignments']
    if 'whitelist' in kwargs:
        global_whitelist = kwargs['whitelist']
    if 'blacklist' in kwargs:
        global_blacklist = kwargs['blacklist']
    if 'parameters_blacklist' in kwargs:
        parameters_blacklist = kwargs['parameters_blacklist']
    if 'parameters_whitelist' in kwargs:
        parameters_whitelist = kwargs['parameters_whitelist']
    if 'choices_blacklist' in kwargs:
        choices_blacklist = kwargs['choices_blacklist']
    if 'choices_whitelist' in kwargs:
        choices_whitelist = kwargs['choices_whitelist']
    if 'constraints_blacklist' in kwargs:
        constraints_blacklist = kwargs['constraints_blacklist']
    if 'constraints_whitelist' in kwargs:
        constraints_whitelist = kwargs['constraints_whitelist']
    if 'assignments_blacklist' in kwargs:
        assignments_blacklist = kwargs['assignments_blacklist']
    if 'assignments_whitelist' in kwargs:
        assignments_whitelist = kwargs['assignments_whitelist']            
    
    # Parse parameter objects for global parameters if they exist. Parse 
    # the list only once and store the parameters in a global dictionary.
    # so that they can be reused in the model if more than one function
    # will be parsed. The list is assumed to be already validated.
    if 'global parameters' in model and len(global_params) == 0:
        for parameter in model['global parameters']:
            try:
                global_params[parameter['parameter']] = Parameter(parent_path='___GLOBAL_PARAMETERS___', description=parameter, inherited_labels=[])
            except KeyError:
                pass

    functions = [f for f in model['functions'] if 'function' in f]
    function_names = [f['function'] for f in functions]
    if len(functions) == 0:
        raise Exception('No functions defined in model')
    if function_name is not None and function_name not in function_names:
        raise Exception(f"Function '{function_name}' not found in the model file")

    function_defs = [function for function in functions if function['function'] == function_name]
    if len(function_defs) == 0:
        raise Exception(f"Function '{function_name}' not found in the model file")
    function_def = function_defs[0]
    
    function = Function(description=function_def) 
    return function   

