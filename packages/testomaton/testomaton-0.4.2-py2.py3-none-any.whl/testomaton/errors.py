from enum import Enum

parsing_errors = []

path_types = {
    '___FUNCTIONS___' : 'function',
    '___PARAMETERS___' : 'parameter',
    '___CHOICES___' : 'choice',
    '___GLOBAL_PARAMETERS___' : 'global parameter',
    '___LOGIC___' : 'logic element',
}


def report_parsing_error(path, tag, message):
    # this is used in a test code, when individual elements like choices are parsed
    if path.startswith('::'):
        path = path[2:]
    parsing_errors.append(ParsingError(path, tag, message))


class ParsingErrorTag(Enum):
    NAME = 1
    CHILDREN = 2
    VALUE = 3
    LABEL = 4
    ASSIGNMENT = 5
    CONSTRAINT = 6
    ALIAS = 7
    SOLVER = 8
    INCOMPLETE_MODEL = 9

    def __str__(self) -> str:
        return self.name

class ParsingError:
    def __init__(self, path, tag, message):        
        self.path = path
        self.tag = tag
        self.message = message

    def __str__(self):
        def decompose_path(path):
            result = {}
            current_type = None
            current_path = []
            
            for token in path:
                if token in path_types:
                    if current_type:
                        result[path_types[current_type]] = '::'.join(current_path)
                    current_type = token
                    current_path = []
                elif current_type:
                    current_path.append(token)
            
            if current_type and current_path:
                result[path_types[current_type]] = '::'.join(current_path)
            
            return result
        path_tokens = self.path.split('::')
        decomposed = decompose_path(path_tokens)
        return f"{decomposed} - {self.tag} - {self.message}"

    def __repr__(self):
        return str(self)

class ExitCodes(Enum):
    SUCCESS = 0

    CONFLICTING_PROGRAM_ARGS = 1
    MODEL_FILE_NOT_FOUND = 2
    YAML_PARSING_ERROR = 3
    MODEL_PARSING_ERROR = 4
    MODEL_VALIDATION_ERROR = 5
    TEST_FILE_NOT_FOUND = 6
    TEST_PARSING_ERROR = 7
    GENERATION_ERROR = 8

    def __str__(self):
        return str(self.value)

    def __int__(self):
        return self.value


