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

from pysat.card import CardEnc
from pysat.formula import CNF
from pysat.solvers import Solver
import testomaton.constraint as constraint
from testomaton.constraint import Parser
import testomaton.errors as errors
from testomaton.errors import ParsingErrorTag



class TomatoSolver:
    """
    TomatoSolver is a class that is used to determine if a test case (potentially incomplete) is 
    fulfilling defined constraints. It is also used to adapt the values of output parameters according 
    to defined assignment expressions. TomatoSolver class provides a set of functions that are used 
    throughout test generation that allow to dynamically update its state according to current step 
    in generation.

    Attributes:
        function (Function): Function object that represents the function to be tested.
        parser (Parser): Parser object that is used to parse constraints and assignments.
        parameters (list): List of parameter names.
        choices (list): List of lists of choices for each parameter.
        choice_mapping (dict): Dictionary that maps each choice to a unique number.
        top_id (int): The highest number used in clauses that define the model semantics.
        model_semantics (list): List of clauses that represent the model semantics.
        solver (Solver): The solver object that is used to check the test cases.
        assignments (dict): Dictionary that maps each assignment to a parameter name.

    Public methods:
        __init__(self, function, negate_constraints=False, invert_constraints=False): Prepares the solver for a given function.
        restrict_test_case(self, restricted): Adds a clause to the model semantics to restrict a given tuple.
        test(self, test_case): Tests if a given test case satisfies the constraints.
        choice_selected(self, parameter_index, choice): Announces to the solver that a given choice is selected for a given parameter.
        tuple_selected(self, test_tuple): Updates the solver with the choices selected in a given test tuple.
        new_test_case(self): Resets the solver back to the initial model semantics.
        adapt(self, test_case): Modifies a test case based on preconditions and assignments.
    """

    def __init__(self, function, 
                 negate_constraints=False, 
                 invert_constraints=False):
        """
        Prepares the solver for a given function by translating it's constraints and aliases to a format
        that can be used by the solver. The aliases are parsed and stored in a dictionary so they can 
        be used to resolve references in the constraints. The constraints are converted to CNF and added
        to the model semantics. The assignments are parsed and stored in a dictionary. 

        Args:
            function (Function): Function object that represents the function to be tested, containing parameters, choices, aliases and constraints.
            negate_constraints (bool): If True, negates all constraints, which effectively makes valid only tests that violate at least one constraint.
            invert_constraints (bool): If True, inverts all constraints, which effectivelu makes valid only tests that violate all defined constraints.
        
        Returns:
            none
        """
        
        self.function = function
        self.parser = Parser()
        self.parameters = self.function.get_all_parameter_names()
        self.choices = self.function.get_leaf_choice_names()

        # Prepeare choice mapping and model semantics
        self.model_semantics = []
        if(len(self.choices) > 0):
            self.choice_mapping = self.__prepare_choice_mapping()
            ids = [val for mapping in self.choice_mapping.values() for key, val in mapping.items()]
            # self.top_id = max([val for mapping in self.choice_mapping.values() for key, val in mapping.items()])
            self.top_id = max(ids) if len(ids) > 0 else 0
            self.__prepare_model_semantics()

        # Initializes and populates the 'aliases' included in the function, parsing the statement aliases.
        aliases = {}
        aggregated_constraint = None
        constraints_to_process = []

        try:
            for full_name, expression in sorted(self.function.get_aliases(), key=lambda x: len(x[0].split('::')), reverse=True):
                # Aliases are sorted by depth, so an alias that is closer to the root should be able to use aliases
                # that are below it in the hierarchy.
                context = constraint.Context(self.function, full_name)
                candidate = self.parser.parse_statement_alias(expression, aliases, context)
                if candidate is not None:
                    aliases[full_name] = candidate
        except Exception as e:
            pass

        # Goes through global constraints defined in 'self.function' and adds them to the list of constraints to process.
        try:
            for name, expression in self.function.get_constraints():
                context = constraint.Context(self.function, name)        
                candidate = self.parser.parse_constraint(expression, aliases, context)
                if candidate is not None:
                    constraints_to_process.append(candidate.to_invariant())
        except Exception:
            pass
        
        #Initializes and iterates over the 'assignments' and appends the parsed assignments into their respective name list.
        self.assignments = {}
        try:
            for a in self.function.assignments:
                context = constraint.Context(self.function, a.name)
                candidate = self.parser.parse_assignment(a.expression, context, aliases)
                if candidate is not None:
                    self.assignments[a.name] = candidate
        except Exception:
            pass
        
        if constraint.parsing_error:
            return
        
        # Iterates over the constraints to process, aggregating them into a single constraint. And negates the constraint if 'negate_constraints' is True.
        for c in constraints_to_process:
            if invert_constraints:
                c = c.negated()
            if aggregated_constraint is None:
                aggregated_constraint = c
            else:
                aggregated_constraint = aggregated_constraint & c
        
        # If 'negate_constraints' is True, negates the aggregated constraint (inverts its truth value)
        if aggregated_constraint is not None and negate_constraints:
            aggregated_constraint = aggregated_constraint.negated()
        
        # If the aggregated constraint is not None, converts it to CNF and adds it to the model semantics. 
        if aggregated_constraint is not None:
            self.top_id, cnf = aggregated_constraint.to_cnf(self.choice_mapping, self.top_id)
            self.model_semantics.extend(cnf.clauses)
        
        # Initializes the solver with the prepared model semantics. 
        self.solver = Solver(bootstrap_with=self.model_semantics)

    def restrict_test_case(self, restricted):
        """
        Adds a clause to the model semantics to restrict a given tuple (test case).
        This will be NOT (x1 AND x2 AND ... AND xn), 
        that is: NOT x1 OR NOT x2 OR ... OR NOT xn.

        Args:
            restricted (list): List of choices to restrict in the tuple.

        Returns:
            none
        """
        clause = []
        for i, choice in enumerate(restricted):
            if choice != None:
                parameter_name = self.parameters[i]
                # checks if the parameter is an output parameter, if so, it should not be restricted
                is_output = parameter_name in [p.name for p in self.function.output_parameters]
                mapping = self.choice_mapping[self.parameters[i]]
                # if the parameter is not an output paramteter, append the negated choice to the clause list
                if not is_output:
                    clause.append(-mapping[choice])
        # append the clause to the model semantics
        self.model_semantics.append(clause)
                
    def test(self, test_case):
        """ 
        Tests if a given test case satisfies the constraints. Converting it to a clause and uses the solver to check it.

        Args:
            test_case (list): List of choices selected in the test tuple. The choices that are not selected yet are represented as None.

        Returns:
            bool: True if the test case satisfies the constraints, False otherwise.
        """
        return self.solver.solve(assumptions=self.__tuple_to_clause(test_case))
    
    def choice_selected(self, parameter_index, choice):
        """ 
        Announces to the solver that a given choice is selected for a given parameter. Used by constructing 
        a test case choice by choice by a generation algorithm.

        Args:

            parameter_index (int): Index of the parameter in the tuple.
            choice (int): Index of the choice selected for the parameter.

        Returns:
            none

        Example:
            The parameters are : ['colour', 'size']
            The choices are : [['red', 'green'], ['small', 'big']]
            the mapping is : {'colour': {'red': 1, 'green': 2}, 'size': {'small': 3, 'big': 4}}
            If we call choice_selected(0, 'green'), it will add the clause [2] to the solver 
            indicating that the choice 'green' is selected for the parameter 'colour'.
        """
        parameter_name = self.parameters[parameter_index]
        mapping = self.choice_mapping[parameter_name]
        self.solver.add_clause([mapping[choice]])
        
    def tuple_selected(self, test_tuple):
        """
        Updates the solver with the choices selected in a given test tuple.
        
        Args:
            test_tuple (list): List of choices selected in the test tuple.
        
        Returns:
            none
            
        Example:
            The parameters are : ['colour', 'size']
            The choices are : [['red', 'green'], ['small', 'big']]
            the mapping is : {'colour': {'red': 1, 'green': 2}, 'size': {'small': 3, 'big': 4}}
            If we call tuple_selected(['green', 'big']), it will add the clauses [2] and [4] to the solver 
            indicating that the choice 'green' is selected for the parameter 'colour' and the choice 'big' 
            is selected for the parameter 'size'.
        """
        for i, choice in enumerate(test_tuple):
            if choice != None:
                mapping = self.choice_mapping[self.parameters[i]]
                self.solver.add_clause([mapping[choice]])

    def new_test_case(self):
        """ 
        Resets the solver back to the initial model semantics, removing all the choices selected so far. 
        Used when starting a new test case, ensures each test case is evaluated independently.
        """
        self.solver = Solver(bootstrap_with=self.model_semantics)

    def adapt(self, test_case):
        """
        To modify a test case based on preconditions and assignments.

        Args:
            test_case (list): List of choices selected in the test tuple.

        Returns:
            list: List of choices modified based on the preconditions and assignments.
        
        Example:
            The parameters and choices are : ['colour', 'size'], [['red', 'green'], ['small', 'big']]
            The assignments are : "'colour' IS 'red' => 'size' IS 'small'"
            If we call adapt(['red', 'big']), it will check the assignments and modify the test case to ['red', 'small'].
        """
        clause = self.__tuple_to_clause(test_case)
        for assignment in self.assignments.values():
            # for assignment in assignment_group:
            top_id, precondition_cnf = assignment.precondition.to_cnf(self.choice_mapping, self.top_id)
            # Instantiate a new solver with the precondition and model semantics
            solver = Solver(bootstrap_with=self.model_semantics)
            solver.append_formula(precondition_cnf.clauses)
            solver.add_clause([top_id])
            # Check if the precondition is satisfied
            if solver.solve(assumptions=clause):
                assignment.apply(test_case)
        return test_case

    # Private methods below:

    def __tuple_to_clause(self, tested_tuple):
        """
        Converts a test case tuple into a logical clause that can be used by the solver.
        This clause represents the choices selected for each parameter in the test case.
        """
        clause = []
        for n, choice in enumerate(tested_tuple):
            if choice == None:
                continue
            # get the parameter name and the choice representation
            parameter_name = self.parameters[n]
            choice_representation = self.choice_mapping[parameter_name][str(choice)]
            # add the choice representation to the clause
            clause.append(choice_representation)            
        return clause

    def __prepare_choice_mapping(self):
        """
        Creates a dictionary that maps each possible choice for every parameter to a unique number.
        This is used in the conversion of human-readable choices to a format that can be used by the solver.
        """
        choice_mapping = {}
        i = 1

        # iterates over the parameters
        for n, parameter in enumerate(self.parameters):
            try:
                mapping = {}
                choice_mapping[parameter] = mapping
                # iterates over the choices for the parameter and assigns a number to each choice
                for choice in self.choices[n]:
                    mapping[choice] = i
                    i += 1
            except:
                continue

        # returns the dictionary
        return choice_mapping
    
    def __get_parameter_choices_representation(self, parameter):
        """ 
        Returns representation of all choices for a given parameter
        """
        choices = self.choice_mapping[parameter]
        result = [value for key, value in choices.items()]
        return result
    
    def __prepare_model_semantics(self):
        """ 
        Define logical constraints/semantics that ensure only one choice is selected for each parameter. 
        These are added to the model semantics.
        """
        self.model_semantics = CNF()
        
        for parameter in self.parameters:
            choices = self.__get_parameter_choices_representation(parameter)
            #if there are choices for the parameter we add the cardinality constraint
            #otherwise it does not matter, as there is nothing to choose. There should be 
            #an error reported in this case and no generation should be attempted.
            if len(choices) > 0:
                # Define a cardinality constraint, ensuring only one choice is selected for the parameter
                semantics = CardEnc.equals(lits=choices, bound=1, top_id=self.top_id)

                # Add the clauses to the model semantics and update the top_id
                self.model_semantics.extend(semantics.clauses)
                self.top_id = semantics.nv
