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

from itertools import combinations, product
from math import ceil
import random as rand
from copy import copy, deepcopy
import shutil
import sys, time

show_progress = False
progress_format = "simple"
progress_output_mode = "stderr"
step_delay = 0
demo_mode = False

current_progress = 0
total_progress = 0
progress_label = ""

class GeneratorError(Exception):
    pass

def get_terminal_width():
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 120

def clear_progress_long(output=sys.stderr):
    """
    Clear progress lines properly, handling wrapped text and extra long lines.
    Uses ANSI escape codes to clear multiple lines if needed.
    """
    # Move cursor to beginning of line and clear everything from cursor to end of screen
    output.write('\r\033[0J')  # Clear from cursor to end of screen
    output.flush()

def format_candidate_demo(candidate, max_width):
    """
    Smart formatting of candidates that shows useful info widthin specific
    width levels when using demo mode.
    """
    if not candidate:
        return "[]"
    
    # Show only non-None values
    display_items = ["." if val is None else str(val) for val in candidate]
    
    if all(item == "." for item in display_items):
        return "[all None]"
    
    # Try different formatting approaches based on available width
    if max_width > 170:
        # Full display with positions
        items_str = ", ".join(display_items[:40])
        if len(display_items) > 40:
            items_str += f" +{len(display_items)-40} more"
        result = f"[{items_str}]"
    elif max_width > 100:
        # Medium display - just values
        items_str = ", ".join(display_items[:30])
        if len(display_items) > 30:
            items_str += f" +{len(display_items)-30}"
        result = f"[{items_str}]"
    elif max_width > 50:
        items_str = ", ".join(display_items[:10])
        if len(display_items) > 10:
            items_str += f" +{len(display_items)-10}"
        result = f"[{items_str}]"
    else:
        # Compact display - count only
        non_none_count = len([item for item in display_items if item != "."])
        result = f"[{non_none_count}/{len(display_items)} set]"
    
    # Truncate if still too long
    if len(result) > max_width - 3:
        result = result[:max_width-3] + "..."
    
    return result

def print_progress_line(header, current=None, total=None, line=None, output=sys.stderr):
    """
    Prints information about demo level and progress.
    Handles extra long lines by truncating intelligently.
    """
    # Clear any previous progress
    clear_progress_long(output)
    
    terminal_width = get_terminal_width()
    
    if demo_mode and header and header.strip():
        full_header = header
        if line is not None:
            # Calculate remaining space for the line part
            header_part = header + " - "
            remaining_width = terminal_width - len(header_part) - 5  # Leave margin for safety
            if remaining_width > 10:  # Only add line info if we have reasonable space
                if isinstance(line, list):
                    line_str = format_candidate_demo(line, remaining_width)
                else:
                    line_str = str(line)
                    if len(line_str) > remaining_width:
                        line_str = line_str[:remaining_width-3] + "..."
                
                full_header = header_part + line_str
            # If not enough space, just use the header
            
    elif current is not None and total is not None:
        progress_info = f"({current}/{total})"
        full_header = f"{header} - {progress_info}" if header and header.strip() else progress_info
    else:
        full_header = header or ""
    
    # Final safety check - truncate if somehow still too long
    if len(full_header) > terminal_width - 2:
        full_header = full_header[:terminal_width-5] + "..."

    # Write the progress line
    if full_header.strip():
        output.write('\r' + full_header)
        output.flush()

    if step_delay > 0:
        time.sleep(step_delay)

def clear_progress(output=sys.stderr, length=None):
    """
    Clear progress info before writing real data to stdout.
    Now uses the proper clearing function.
    """
    clear_progress_long(output)

def random(function, solver, length=0, duplicates=False, adaptive=False):
    """
    A function which generates random test cases for a given function and solver.
    It can work in either adaptive or random mode: in adaptive mode it will make
    use of previous test cases to influence future ones, while in random mode it
    will not use any previous test cases and generate purely new random test cases.

    Args:
        function: The function to generate test cases for.
        solver: The solver to use for generating the test cases.
        length: The number of test cases to generate. If set to 0, it will generate
            test cases indefinitely.
        duplicates: Whether to allow duplicates in the generated test cases.
        adaptive: Whether to use adaptive mode or not.
    
    Yields:
        test_case: A test case generated by the function.
    """
    ADAPTIVE_HISTORY_SIZE = 100
    params, input_list = function.get_generator_input()

    assigner = solver
    generated_tests = 0
    recent_tests = []
    
    def best_choice(test_case, solver, i, candidate_choices, generated_tests):
        """ 
        Used for adaptive random generation, where it takes info from previously 
        generated test cases in order to generate the ideal/best test case based on a 
        candidate score
        """
        def score(choice, index, generated_tests):
            return sum([1 if test[index] != choice else 0 for test in generated_tests])
        
        best_score = -1
        for choice in candidate_choices:
            candidate_score = score(choice, i, generated_tests)
            if candidate_score > best_score:
                best_score = candidate_score
                best_choice = choice
        return best_choice
        
    def random_choice(test_case, solver, i, candidate_choices):
        for choice in candidate_choices:
            candidate = list(copy(test_case))
            candidate[i] = choice
                
            if solver.test(candidate):
                return choice
        return None
        
    while ((generated_tests < length) or (length == 0)):
        indices = list(range(len(input_list)))
        rand.shuffle(indices)
        for i in indices:
            rand.shuffle(input_list[i])

        #Call the solver to initialize a new test case in the solver
        solver.new_test_case()
        test_case = [None] * len(input_list)

        #Iterates over each index in 'indeces' and calls the respective function for random/adaptive random generation
        for i in indices:
            if adaptive:
                test_case[i] = best_choice(test_case, solver, i, input_list[i], recent_tests)
            else:
                test_case[i] = random_choice(test_case, solver, i, input_list[i])

        #If any choice in 'test_case' is None, break the loop    
        if any([choice is None for choice in test_case]):
            break
        
        #adapt the state of the solver to the test case, increment 'generated_tests' and yield it
        assigner.adapt(test_case)

        # must be after adapt, if not solver will not be able to restrict the test case correctly
        if duplicates == False:
            solver.restrict_test_case(test_case)

        generated_tests += 1
        recent_tests.append(test_case)
        if len(recent_tests) > ADAPTIVE_HISTORY_SIZE:
            recent_tests = recent_tests[1:]

        if show_progress:
            if progress_output_mode == "stdout":
                if length > 0:
                    progress_percentage = (generated_tests / length) * 100
                    yield f"PROGRESS:({generated_tests}/{length}):{progress_percentage}%"
            else:
                print_progress_line("", generated_tests, length)

        if demo_mode:
            print_progress_line(f"(test cases to go: {length - generated_tests})")
        if progress_output_mode == "stderr":
            clear_progress()

        yield test_case

def cartesian(function, solver):
    """
    A function which generates all valid test cases for a given function and solver.
    
    Args:
        function: The function to generate test cases for.
        solver: The solver to use for generating the test cases.
    
    yields:
        test_case: A test case generated by the function.
    """
    assigner = solver
    params, input_list = function.get_generator_input()

    total_combinations = 1
    for choices in input_list:
        total_combinations *= len(choices)
    
    current_combination = 0
    #set combinations to the Cartesian product of the input list
    combinations = product(*input_list)
    #Iterates over each combination in the combinations and yields the valid test cases
    for combination in combinations:
        current_combination += 1
        if solver.test(combination):
            test_case = assigner.adapt(list(combination))
            if show_progress:
                if progress_output_mode == "stdout":
                    progress_percentage = (current_combination / total_combinations) * 100
                    yield f"PROGRESS:({current_combination}/{total_combinations}):{progress_percentage:.1f}%"
                else:
                    print_progress_line("", current_combination, total_combinations)
            if demo_mode:
                print_progress_line(f"(Test cases to go: {total_combinations - current_combination})")
            
            if progress_output_mode == "stderr":
                clear_progress()

            yield test_case

def nwise(function, solver, n, tuples_from = None, coverage=100):
    """
    A function which generates test cases that covers all n-wise combinations of 
    input parameters provided by a given function. It ensures that the test cases 
    achieve the desired covereage percentage which is specified in the input parameter.
    
    Args:
        function: The function to generate test cases for.
        solver: The solver to use for generating the test cases.
        n: The number of parameters to consider in each combination.
        coverage: The desired coverage percentage to achieve.
    
    Yields:
        test_case: A test case generated by the function.
    """
    assigner = solver
    params, input_list = function.get_generator_input()

    def is_proper_tuples_from_element(element):
        if function.get_parameter(element) is not None:
            return True        
        elif len(function.get_parameters_by_labels(element)) > 0:
            return True
        return False
    
    unrecognized = [e for e in tuples_from if not is_proper_tuples_from_element(e)] if tuples_from is not None else []
    if len(unrecognized) > 0:
        raise ValueError(f"The elements {unrecognized} of the tuples-from list are not valid parameter names or labels")

    def is_parameter_in_tuples_from(parameter):
        while parameter:
            if parameter in tuples_from:
                return True
            # Remove the last part of the path to check if the parent is in the tuples_from
            parameter = "::".join(parameter.split("::")[:-1])
        return False

    def is_parameter_label_in_tuples(parameter):
        return parameter in function.get_parameters_by_labels(tuples_from)

    if tuples_from:
        tuple_parameters_filter = [p for p in params if is_parameter_in_tuples_from(parameter=p) or is_parameter_label_in_tuples(parameter=p)]
    else:
        tuple_parameters_filter = params

    tuple_parameters_filter = [True if parameter in tuple_parameters_filter else False for parameter in params]
    tuple_parameters_filter_length = len([True for x in tuple_parameters_filter if x])

    if tuple_parameters_filter_length < n:
        raise ValueError(f"The number of parameters to consider in each combination must not be less than n ({n})")

    #If n is greater than the length of the input list, raise a ValueError
    if n >= len(input_list):
        raise ValueError("n must be lower than the length of the input list")

    def filter_template(template):
        intersection = [a and b for a, b in zip(template, tuple_parameters_filter)]
        return sum(template) == sum(intersection)

    def tuples_covered(test_case, n):
        if n > len(test_case):
            raise ValueError("n cannot be greater than the size of the test case")

        indices = [i for i, _ in enumerate(test_case) if test_case[i] is not None]
        
        combinations_ = combinations(indices, n)
        def uncompress(indices):
            return tuple([test_case[i] if i in indices else None for i in range(len(test_case))])
        yield from [uncompress(test) for test in combinations_]
        
    def tuples(input_list, n):
        """ Returns all possible tuples of length n from a given 'input_list'."""
        def tuple_template(n, input_size):
            """ Generates templates that indicate whch positions in 'input_list' should be selected to form tuples of length 'n'."""
            if n > input_size:
                raise ValueError("n cannot be greater than m")

            #Iterates over all compinations from the range of 'n' and yields the template. 
            #First a template list of 'False' values, then sets the position of current combination to true.
            for combination in combinations(range(input_size), n):
                template = [False] * input_size
                for index in combination:
                    template[index] = True
                yield template

        def tuples_from_template(input_list, template):
            """ Generates tuples from a given 'input_list' and 'template'."""
            len_input_list = len(input_list)
            if len_input_list != len(template):
                raise ValueError("Input list and template must have the same length")

            #Creates a list of selected indices from the template where it has the value 'True'
            selected_indices = [i for i, is_selected in enumerate(template) if is_selected]

            #Iterates over the product of the input list at the selected indices and yields the tuple from the current combination
            for combination in product(*[input_list[i] for i in selected_indices]):
                result = [None] * len_input_list
                for i, index in enumerate(selected_indices):
                    result[index] = combination[i]
                yield tuple(result) # tuple is hashable, list is not

        #If n is greater than the length of the input list, raise a ValueError        
        if n > len(input_list):
            raise ValueError("n cannot be greater than the length of the input list")

        #Iterates over each template generated and yields the tuples from the template one by one
        for template in tuple_template(n, len(input_list)):
            if filter_template(template):
                yield from tuples_from_template(input_list, template)

    #Generates set of tuples length 'n' that meet the solver.test
    tuples_to_cover = {t for t in tuples(input_list, n) if solver.test(t)}
    #Calculate how many tuples can be left uncovered to meet the coverage criteria
    end_tuples_count = ceil(len(tuples_to_cover) * ((100 - coverage) / 100))
    #Define the end condition to see if criteria has been met
    end_condition = lambda: len(tuples_to_cover) <= end_tuples_count
    #Sets initial tuples count to the length of tuples to cover
    initial_tuples_count = len(tuples_to_cover)

    def tuple_score(candidate):
        """ Evaluates how well a candidate test case covers the required tuples."""
        #If the candidate test case does not meet the solver.test, return -1
        if not solver.test(candidate):
            return -1
        #Otherwise, get the tuples covered by the candidate test case and return the score
        else:
            covered_tuples = tuples_covered(candidate, n)
            score = len(tuples_to_cover.intersection(covered_tuples))
            return score

    #Iteratively generates test cases as long as the end condition is not met
    while not end_condition():
        solver.new_test_case()
        tuple_to_cover = rand.choice(list(tuples_to_cover))
        solver.tuple_selected(tuple_to_cover)
        #Get the indices of the tuple to cover that are None and randomize them to ensure different orerings in each iteration
        indices = [i for i, x in enumerate(tuple_to_cover) if x is None]
        rand.shuffle(indices)
        
        #Create a copy of the tuple to begin constructing the test case
        constructed_test_case = copy(tuple_to_cover)

        #Iterates over each position in in the tuple that need values, evaluate all possible values 
        #and select the one with the highest score from tuple_score
        for i in indices:
            best_choice, best_candidate, best_score = None, None, -1
            choices = input_list[i]
            rand.shuffle(choices)
            for choice in choices:
                candidate = list(copy(constructed_test_case))
                candidate[i] = choice
                if demo_mode:
                    print_progress_line(str(len(tuples_to_cover)) + " tuples to go", line=candidate)

                score = tuple_score(candidate)                    
                if score > best_score:
                    best_candidate = candidate
                    best_score = tuple_score(candidate)
                    best_choice = choice

            #Updates the constructed test case to the best candidate        
            constructed_test_case = best_candidate
            solver.choice_selected(i, best_choice)
            
            #Removes the tuples covered by the constructed test case from the tuples to cover
            for t in tuples_covered(constructed_test_case, n):
                tuples_to_cover.discard(t) 
        #Adapts the state of the solver to the constructed test case and yields it
        test_case = assigner.adapt(constructed_test_case)
        
        current_remaining = len(tuples_to_cover)
        current_completed = initial_tuples_count - current_remaining
        
        if show_progress:
            if progress_output_mode == "stdout":
                progress_percentage = (current_completed / initial_tuples_count) * 100
                yield f"PROGRESS:({current_completed}/{initial_tuples_count}):{progress_percentage:.1f}%"
            else:
                print_progress_line("", current_completed, initial_tuples_count)

        if progress_output_mode == "stderr":
            clear_progress()

        yield test_case

