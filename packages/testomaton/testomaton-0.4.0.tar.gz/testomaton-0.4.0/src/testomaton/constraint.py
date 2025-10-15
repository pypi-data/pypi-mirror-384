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

from pysat.formula import CNF
from pyparsing import *
from copy import deepcopy
import testomaton.errors as errors
from testomaton.errors import ParsingErrorTag
from testomaton.model import Parameter

parsing_error = False

class Context:
    def __init__(self, function, path):
        tokens = path.split('::')
        self.function = function
        self.path = '::'.join(tokens[:-1]) if len(tokens) > 1 else None
        self.name = tokens[-1]

def report_parsing_error(context, tag, message):
    path = context.function.path if context.function is not None else ''
    path = path + '::___PARAMETERS___::' + context.path if context.path is not None else path
    path = path + '::' + '___LOGIC___' + '::' + context.name if context.name is not None else path
    errors.report_parsing_error(path, tag, message)
    global parsing_error 
    parsing_error = True

def parse_expression(expression_tokens, aliases, context):
    """
    A function to parse a logical expression into correct components based on the given tokens, 
    such as 'AND', 'OR', 'NOT', 'IS', 'IN', 'IS NOT', 'NOT IN'. Returning instances of classes, 
    the classes being : NegatedExpression, CompositeExpression, PrimitiveStatement.
    
    Args:
        expression_tokens (list): A list of tokens representing a logical expression.
        aliases (dict): A dictionary of aliases.
        context (str): A context to be used for the expression. The context is either None, meaning that 
                        the expression was defined for a function. Or it is the path to a structure (parameter)
                        where the expression is defined.
    
    Returns:
        OBJECT: An object representing the parsed expression. The object that is returned, must have a toCNF function 
                so it can be converted to CNF form.
    
    Raises:
        Exception: If the expression is made up of a single token which is not an alias.
                Normally there are at least two tokens on the high level(NOT expr), usually 
                three(eg. expr AND/OR expr, or par IS choice). If there is only one token,
                it means that we are useing a previously defined alias.
    """
    # checks if the expression is a single string and if it is an alias, returns the corresponding statement
    if len(expression_tokens) == 1 and isinstance(expression_tokens[0], str):
        alias_name = context.path + '::' + expression_tokens[0] if context.path is not None and len(context.path) else expression_tokens[0]
        if alias_name in aliases:
            return aliases[alias_name].statement
        else:
            report_parsing_error(context, ParsingErrorTag.ALIAS, f'{alias_name} is not a defined alias')

    # if 'expression_tokens' is a single statement, it is believed to be a nested list and unwraps it, loops as long as the 'expression_tokens' is 1
    while len(expression_tokens) == 1:
        expression_tokens = expression_tokens[0]

    # handles expressions starting with 'NOT' and returns a negatedExpression object, removing the 'NOT' token
    if expression_tokens[0] == 'NOT':
        return NegatedExpression(tokens=expression_tokens[1:], aliases=aliases, context=context)
        
    elif any(element in expression_tokens.asList() for element in ['AND', 'OR']) and len(expression_tokens):
        # conjunction or disjunction
        rval_tokens = expression_tokens.pop()
        operator = expression_tokens.pop()
        lval_tokens = expression_tokens
        return CompositeExpression(operator, tokens=[lval_tokens, rval_tokens], aliases=aliases, context=context)

    elif any(element in expression_tokens.asList() for element in ['IS', 'IS NOT', 'IN', 'NOT IN', 'LABEL']) and len(expression_tokens) == 3 or len(expression_tokens) == 4:
        # primitive statement
        statement_type = 'CHOICE'
        if 'LABEL' in expression_tokens.asList():
            statement_type = 'LABEL'
            label_keyword = expression_tokens.pop(1)
        rval_tokens = expression_tokens.pop()
        operator = expression_tokens.pop()
        lval_tokens = expression_tokens
        return PrimitiveStatement(lval_tokens, operator, rval_tokens, context=context, statement_type=statement_type)
    

class CompositeExpression:
    """
    A composite expression represents the union(AND) or disjunction(OR) of two expressions.
    
    Attributes:
        operator (str): The operator of the composite expression.
        lval (object): The left value of the composite expression.
        rval (object): The right value of the composite expression.
        
    Methods:
        to_cnf: A function to convert a composite expression into CNF.
    """

    def __init__(self, operator, 
                 aliases,
                 context,
                 tokens=None, 
                 expr=None):
        """ 
        Initializes the CompositeExpression class and 
        parses the left and right expressions based on the given tokens.
        
        Args:
            operator (str): The operator of the composite expression.
            aliases (dict): A dictionary of aliases.
            tokens (list): A list of tokens representing the composite expression.
            expr (list): A list of expressions representing the composite expression.
            context (str): A context to be used for the expression.
        
        Returns:
            None
        """
        self.operator = operator
        if tokens is not None:
            self.lval = parse_expression(tokens[0], aliases, context)
            self.rval = parse_expression(tokens[1], aliases, context)
        elif expr is not None:
            self.lval = expr[0]
            self.rval = expr[1]
        
    def __str__(self):
        return '(' + str(self.lval) + ' ' + self.operator + ' ' + str(self.rval) + ')'
    
    def to_cnf(self, choice_mapping, top_id):
        """
        A function to convert a composite expression into CNF.
        Handles the 'AND' and 'OR' operators, generating appropriate 
        CNF clauses.
        
        Args:
            choice_mapping (dict): A dictionary of choices.
            top_id (int): The top id of the composite expression.
        
        Returns:
            int: The top id of the composite expression.
            CNF: A CNF representation of the composite expression.
        
        Raises:
            Exception: If the operator is unknown.
        """
        # recursively convert the left and right expressions to CNF       
        lval_id, lval = self.lval.to_cnf(choice_mapping, top_id)
        rval_id, rval = self.rval.to_cnf(choice_mapping, lval_id)
        clauses = lval.clauses + rval.clauses
        my_id = rval_id + 1
        
        # if the operator is 'AND', the CNF clauses are extended, y = A AND B compiles to [A, !y] AND [B, !y] AND [!A, !B, y]
        if self.operator == 'AND':
            clauses.extend([[lval_id, -my_id], [rval_id, -my_id], [-lval_id, -rval_id, my_id]])

        # if the operator is 'OR', the CNF clauses are extended, y = A OR B compiles to [!A, y] AND [!B, y] AND [A, B, !y]    
        elif self.operator == 'OR':
            clauses.extend([[-lval_id, my_id], [-rval_id, my_id], [lval_id, rval_id, -my_id]])            

        # if the operator is not 'AND' or 'OR', raise an exception
        else:
            raise Exception(f'Parsing expression {str(self)}: unknown operator {self.operator}')

        # return the top id and the CNF representation of the composite expression
        cnf = CNF(from_clauses=clauses)
        return my_id, cnf

        
class NegatedExpression:
    """
    A class to represent negated expressions.
    
    Attributes:
        expression (object): The expression to be negated.
    
    Methods:
        to_cnf: A function to convert a negated expression into CNF.
    """
    def __init__(self,
                 context,
                 tokens = None, 
                 expr = None,
                 aliases = None):
        """
        Initializes the NegatedExpression class and parses the expression based on the given tokens.
        
        Args:
            tokens (list): A list of tokens representing the negated expression.
            expr (list): A list of expressions representing the negated expression.
            aliases (dict): A dictionary of aliases.
            context (str): A context to be used for the expression.
        
        Returns:
            None
        """
        # if the tokens are not None, parse the expression based on the given tokens, 
        # else directly assign the expr value to self.expression
        if tokens is not None:
            self.expression = parse_expression(tokens, aliases, context=context)
        elif expr is not None:
            self.expression = expr        

    def __str__(self):
        return '(NOT ' + str(self.expression) + ')'
    
    def to_cnf(self, choice_mapping, top_id):
        """ 
        A function to convert a negated expression into CNF.
        Negates the expression and returns the CNF representation.
        
        Args:
            choice_mapping (dict): A dictionary of choices.
            top_id (int): The top id of the negated expression.
        
        Returns:
            int: The top id of the negated expression.
            CNF: A CNF representation of the negated expression.
        """
        expr_id, expr = self.expression.to_cnf(choice_mapping, top_id)
        my_id = expr_id + 1
        #negate expr
        expr.extend([[my_id, expr_id], [-my_id, -expr_id]])
        
        # return the id and the CNF representation of the negated expression (expr)
        return my_id, expr

class PrimitiveStatement:
    """
    Primitive statments are the basic construction bricks of a constraint.
    They are expressions in the form "parameters IS/IS NOT choice" or 
    "parameters IN/NOT IN [choice1, choice2, ...]".
    
    Attributes:
        lval (str): The left value of the primitive statement.
        operator (str): The operator of the primitive statement.
        values (list): The values of the primitive statement.
    
    Methods:
        to_cnf: A function to convert a primitive statement into CNF.
    """
    def __init__(self, lval, operator, rval, context, statement_type):
        """
        Initializes the PrimitiveStatement class and assigns the left value, operator, and values based on the given tokens.
        
        Args:
            lval (str): The left value of the primitive statement.
            operator (str): The operator of the primitive statement.
            rval (list): The values of the primitive statement.
            context (str): A context to be used for the expression.
        
        Returns:
            None
        """
        self.negated = False
        if 'NOT' in operator:
            self.negated = True
        
        self.lval = lval[0]

        #To handle label statements differently
        self.statement_type = statement_type

        self.parameter = context.function.get_parameter(self.lval)
        if context.path is not None:
            self.lval = context.path + '::' + self.lval if context.path is not None and len(context.path) else self.lval

        # if the operator is 'IS' set the values to the right value, 
        # else if the operator is 'IN' set the values to the list of values
        if 'IS' in operator:
            if self.statement_type == 'LABEL':
                self.labels = [rval]
            else:
                self.values = [rval]
        elif 'IN' in operator:
            if self.statement_type == 'LABEL':
                self.labels = rval.asList()
            else:
                self.values = rval.asList()

        if context.function.get_parameter(self.lval) is not None:
            parameter = context.function.get_parameter(self.lval)
            if not isinstance(parameter, Parameter):
                report_parsing_error(context, ParsingErrorTag.CONSTRAINT, f'"{self.lval}" is not a parameter')

        if self.statement_type == 'LABEL':
                for label in self.labels:
                    if len(parameter.get_choices_by_label(label)) == 0:
                        report_parsing_error(context, ParsingErrorTag.CONSTRAINT, f'Label: "{label}" is not valid')
                return
        elif self.statement_type == 'CHOICE':
            for value in self.values:
                if parameter.get_choice(value) is None:
                    report_parsing_error(context, ParsingErrorTag.CONSTRAINT, f'Choice: "{value}" is not valid')

    def __str__(self):
        return '(' + str(self.lval) + (' NOT IN ' if self.negated else ' IN ') + str(self.values) + ')'
    
    def to_cnf(self, choice_mapping, top_id):
        """
        A function to convert a primitive statement into CNF.
        
        Args:
            choice_mapping (dict): A dictionary of choices.
            top_id (int): The top id of the primitive statement.

        Returns:
            int: The top id of the primitive statement.
            CNF: A CNF representation of the primitive statement.
        
        """
        parameter_name = self.lval
        parameter_mapping = choice_mapping[parameter_name]

        # do something to check for choice values. so that choices that arent in a parameter are caught and report an error. 
        def filter_labels(choices, labels):
            """ filters the choices based on specified labels."""
            result = []
            for label in labels:
                result.extend(self.parameter.get_choices_by_label(label))
            return result


        def filter_choices(choices, values):
            """ filters the choices based on the values, gotten from the operators."""
            result = []
            for choice in choices:
                for value in values: 
                    if choice == value or choice.startswith(value + '::'):
                        result.append(choice)
            return result
        
        if self.statement_type == 'LABEL':
            selected_choices = filter_labels(parameter_mapping.keys(), self.labels)
        elif self.statement_type == 'CHOICE':
            selected_choices = filter_choices(parameter_mapping.keys(), self.values)

        # if the primitive statement is negated, filter the choices and select those that are not in the 'selected_choices'
        if self.negated:
            selected_choices = [choice for choice in parameter_mapping.keys() if choice not in selected_choices]
        
        # maps the selected choices to the corresponding values in the parameter_mapping
        allowed = [parameter_mapping[choice] for choice in selected_choices]
        clauses = []

        my_id = top_id + 1  
        last_clause = []
        # loops through and for each element in 'allowed', appends the clause 
        # to the 'clauses' list and appends the element to the 'last_clause' list
        for x in allowed:
            clauses.append([-x, my_id])
            last_clause.append(x)
        last_clause.append(-my_id)
        clauses.append(last_clause)
        
        # returns the top id and the CNF representation of the primitive statement
        return my_id, CNF(from_clauses=clauses)

class Invariant:
    """
    A inveriant expression is a logical statement that must be fulfilled for all test cases
    for them to be valid.
    
    Attributes:
        expression (object): The expression of the invariant.
        context (str): The context of the invariant.
    
    Methods:
        __init__: Initializes the Invariant class and parses the expression based on the given tokens.
        __str__: Returns a string representation of the invariant.
        negated: A function to negate the invariant.
        to_cnf: A function to convert an invariant into CNF.
        to_invariant: A function to return the invariant.
        expression: A function to return the expression of the invariant.
        __and__: A function to logically AND two invariants.
        __or__: A function to logically OR two invariants.
    """
    def __init__(self, expression_tokens, aliases, context, expression=None):
        """
        Initializes the Invariant class.
        
        Args:
            expression_tokens (list): A list of tokens representing the expression.
            aliases (dict): A dictionary of aliases.
            context (str): The context of the invariant.
            expression (object): The expression of the invariant. (optional)
            
        Returns:   
            None
        """
        self.context = context
        # if the expression is not None, assign the expression to self.expression, else parse the expression based on the given tokens and arguments
        if expression is not None:
            self.expression = expression
        else:
            self.expression = parse_expression(expression_tokens, aliases, context=self.context)

    def __str__(self):
        return str(self.expression)
    
    def negated(self):
        expression = NegatedExpression(expr=self.expression, context=self.context)
        return Invariant(None, None, expression=expression, context=self.context)

    #returns top_id and CNF
    def to_cnf(self, choice_mapping, top_id):
        """ 
        A function to convert an invariant into CNF.
        
        Args:
            choice_mapping (dict): A dictionary of choices.
            top_id (int): The top id of the invariant.
        
        Returns:
            int: The top id of the invariant.
            CNF: A CNF representation of the invariant.
        """
        invariant_id, result = self.expression.to_cnf(choice_mapping, top_id)
        result.append([invariant_id])

        return invariant_id, result

    def to_invariant(self):
        return self

    """ Returns the underlying expression of the invariant."""
    def expression(self):
        return self.expression    
    
    """ Creates a new 'invariant' object representing the logical AND of two invariants, (current invariant and another)."""
    def __and__(self, other):
        expression = CompositeExpression('AND', None, expr=[self.expression, other.expression], context=self.context)
        result = Invariant(None, None, context=self.context, expression=expression)
        return result
    
    """ Creates a new 'invariant' object representing the logical OR of two invariants, (current invariant and another)."""
    def __or__(self, other):
        self.expression = CompositeExpression('OR', None, expr=[self.expression, other.expression], context=self.context)
        return self
        
class Implication:
    """ 
    Implication is a expression in the form of 'IF precondition THEN postcondition'.
    Which indicates that if the precondition is satisfied in a test case, then the 
    postcondition must also be satisfied. If not, the test case is not valid.
    An implication can be converted into an invariant expression, in the form
    of 'NOT precondition OR postcondition'.

    Attributes:
        precondition (object): The precondition of the implication.
        postcondition (object): The postcondition of the implication.
        context (str): The context of the implication.
    
    Methods:   
        to_invariant: A function to convert the implication into an invariant.
        negated: A function to negate the implication.
        to_cnf: A function to convert the implication into CNF.
        expression: A function to return the expression of the implication.
    """
    def __init__(self, precondition_tokens, postcondition_tokens, aliases, context):
        """
        Initializes the Implication class and parses the precondition and postcondition based on the given tokens.
        
        Args:
            precondition_tokens (list): A list of tokens representing the precondition.
            postcondition_tokens (list): A list of tokens representing the postcondition.
            aliases (dict): A dictionary of aliases.
            context (str): The context of the implication.
            
        Returns:
            None
        """
        self.precondition = parse_expression(precondition_tokens, aliases, context=context)
        self.postcondition = parse_expression(postcondition_tokens, aliases, context=context)
        self.context = context

    def __str__(self):
        return 'IF ' + str(self.precondition) + ' THEN ' + str(self.postcondition)

    def to_invariant(self):
        """ Converts the implication into an invariant."""
        negated_precondition = NegatedExpression(expr=self.precondition, context=self.context)
        equivalent_expr = CompositeExpression('OR', None, expr=[negated_precondition, self.postcondition], context=self.context)
        return Invariant(None, None, context=self.context, expression=equivalent_expr)

    def negated(self):        
        return self.to_invariant().negated()
    
    #returns top_id and CNF
    def to_cnf(self, choice_mapping, top_id):
        """
        A function to convert the implication into CNF.
        
        Args:
            choice_mapping (dict): A dictionary of choices.
            top_id (int): The top id of the implication.
        """
        precondition_id, precondition_cnf = self.precondition.to_cnf(choice_mapping, top_id)
        postcondition_id, postcondition_cnf = self.postcondition.to_cnf(choice_mapping, precondition_id)

        return postcondition_id, CNF(from_clauses=[[-precondition_id, postcondition_id]] + precondition_cnf.clauses + postcondition_cnf.clauses)
    
    """ Returns the expression of the implication."""
    def expression(self):
        return self.to_invariant().expression
    
class Assignment:
    """
    Assignments represent expressions that modify output parameters of a function, 
    if precondition is satisfied.
    
    Attributes:
        function (object): The function of the assignment.
        precondition (object): The precondition of the assignment.
        assignments (dict): The assignments of the assignment.
    
    Methods:
        apply: A function to apply the assignment to a test case.
    """
    def __init__(self, context, precondition_tokens, assignments_tokens, aliases):
        """
        Initializes the Assignment class and parses the precondition and assignments based on the given tokens.
        
        Args:
            function (object): The function of the assignment.
            precondition_tokens (list): A list of tokens representing the precondition.
            assignments_tokens (list): A list of tokens representing the assignments.
            aliases (dict): A dictionary of aliases.
        
        Returns:
            None
        """
        self.function = context.function
        self.precondition = parse_expression(precondition_tokens, aliases, context=context)
        self.assignments = {}
        # get the output parameters of the function
        output_parameters = [p.name for p in self.function.output_parameters]
        # loop through the assignments and assign the values to the corresponding output parameters
        for assignment in assignments_tokens:
            name = assignment[0]
            value = assignment[1]
            if name not in output_parameters:
                report_parsing_error(context=context, tag=ParsingErrorTag.ASSIGNMENT, message=f'Unknown output parameter: {name}')
            self.assignments[name] = value
    
    def __str__(self):
        return 'IF ' + str(self.precondition) + ' THEN ' + str(self.assignments)  
    
    def apply(self, test_case):
        """ Applies the assignment to a test case."""
        for name, value in self.assignments.items():
            test_case[self.function.get_parameter_index(name)] = value

class StatementAlias:
    """
    A class to represent statement aliases, allowing complex statements 
    to be referenced with simpler names.
    
    Attributes:
        statement (object): The statement of the alias.
    """
    def __init__(self, statement_tokens, aliases, context):
        """ 
        Initializes the StatementAlias class and parses the statement based on the given tokens.
        Creates the corresponding logical expressions through parsing the statement.
        
        Args:
            statement_tokens (list): A list of tokens representing the statement.
            aliases (dict): A dictionary of aliases.
            context (str): A context to be used for the statement, provides additional information for parsing.
        
        Returns:
            None
        """
        self.statement = parse_expression(statement_tokens, aliases, context=context)
    
    def __str__(self):
        return "Alias: " + str(self.statement)

class Parser:
    """
    A class to represent a parser, which provides methods for parsing constraints, 
    logical statements and assignments.
    
    Methods:
        parse_statement_alias: A function to parse a statement alias.
        parse_constraint: A function to parse a constraint.
        parse_assignment: A function to parse an assignment.
    """
    def __init__(self):
        global parsing_error
        parsing_error = False

        # create the necessary literals
        self.is_literal = CaselessLiteral("IS")
        self.not_literal = CaselessLiteral("NOT")
        self.in_literal = CaselessLiteral("IN")
        self.label_literal = CaselessLiteral("LABEL")

        # create the necessary relations
        self.is_relation = self.is_literal
        self.is_not_relation = Combine(self.is_literal + self.not_literal, adjacent=False, joinString=' ')
        self.in_relation = self.in_literal
        self.not_in_relation = Combine(self.not_literal + self.in_literal, adjacent=False, joinString=' ')

        self.name = QuotedString('\'', escChar='\\') | QuotedString('"', escChar='\\') 
        # self.name = QuotedString('\'', escChar='\\') | QuotedString('"', escChar='\\') | Word(printables, excludeChars=',')
        # self.name = QuotedString('\'', escChar='\\') | QuotedString('"', escChar='\\') | Word(pyparsing_unicode.printables, excludeChars=',')
        self.aggregated_name = Group(Suppress('[') + self.name + ZeroOrMore(Suppress(',') + self.name) + Suppress(']'))

        # create the necessary statements
        self.simple_choice_statement = self.name + self.is_relation + self.name | self.name + self.is_not_relation + self.name
        self.aggregate_choice_statement = self.name + self.in_relation + self.aggregated_name | self.name + self.not_in_relation + self.aggregated_name
        
        self.simple_label_statement = self.name + self.label_literal + self.is_relation + self.name | \
                          self.name + self.label_literal + self.is_not_relation + self.name
        self.aggregate_label_statement = self.name + self.label_literal + self.in_relation + self.aggregated_name | \
                          self.name + self.label_literal + self.not_in_relation + self.aggregated_name
        
        self.primitive_statement = Group(self.simple_choice_statement | self.aggregate_choice_statement | self.simple_label_statement | self.aggregate_label_statement)
        self.alias = self.name

        # create the necessary logical operators
        self.and_literal = CaselessLiteral("AND")
        self.or_literal = CaselessLiteral("OR")
        self.logical_operator = self.and_literal | self.or_literal
        self.logical_operator.setResultsName('logical_operator')
        # Uses 'infixNotation' to define grammar for logical expressions that can use 'NOT', 'AND', 'OR' operators
        self.expression = Group(infixNotation(self.primitive_statement | self.alias, 
            [
                (self.not_literal, 1, opAssoc.RIGHT), 
                (self.logical_operator, 2, opAssoc.LEFT), 
                (self.or_literal, 2, opAssoc.LEFT)
            ]))

        # creates conditional literals
        self.if_literal = CaselessLiteral("IF")
        self.then_literal = CaselessLiteral("THEN")
        self.implies_literal = CaselessLiteral("=>")

    def parse_statement_alias(self, statement_alias_string, aliases, context):
        try:
            tokens = self.expression.parseString(statement_alias_string, parseAll=True)
            return StatementAlias(tokens, aliases, context)
        except Exception as e:
            report_parsing_error(context, ParsingErrorTag.ALIAS, 'Syntax error')
        return None
              
    def parse_constraint(self, constraint_string, aliases, context):
        implication = self.expression + Suppress(self.implies_literal) + self.expression | Suppress(self.if_literal) + self.expression + Suppress(self.then_literal) + self.expression
        invariant = self.expression
        constraint = implication | invariant
        try:
            tokens = constraint.parseString(constraint_string, parseAll=True)
            if len(tokens) == 1:
                return Invariant(tokens[0], aliases, context)
            if len(tokens) == 2:
                return Implication(tokens[0], tokens[1], aliases, context)
        except Exception:
            report_parsing_error(context, ParsingErrorTag.CONSTRAINT, 'Syntax error')
        return None

    def parse_assignment(self, assignment_string, context, aliases):
        """
        Parses assignment string into an Assignment object.
        
        Args:
            assignment_string (str): The assignment string.
            function (object): The function of the assignment.
            aliases (dict): A dictionary of aliases.
        
        Returns:
            Assignment: An Assignment object.
        
        Raises:
            Exception: If the assignment string cannot be parsed.
        """
        equals_literal = CaselessLiteral("=")
        assignment_value = QuotedString('\'', escChar='\\') | Word(printables, excludeChars=',=')
        # assignment_value = QuotedString('\'', escChar='\\') | Word(pyparsing_unicode.printables, excludeChars=',=')
        assignent_statement = Group(self.name + Suppress(equals_literal) + assignment_value)
        assignents_list = Group(assignent_statement + ZeroOrMore(Suppress(',') + assignent_statement))
        
        # assignment = self.expression + Suppress(self.implies_literal) + assignents_list
        assignment = self.expression + Suppress(self.implies_literal) + assignents_list | Suppress(self.if_literal) + self.expression + Suppress(self.then_literal) + assignents_list

        try:
            tokens = assignment.parseString(assignment_string, parseAll=True)
            return Assignment(context, tokens[0], tokens[1], aliases)
        except Exception:
            report_parsing_error(context, ParsingErrorTag.ASSIGNMENT, 'Syntax error')
        return None
