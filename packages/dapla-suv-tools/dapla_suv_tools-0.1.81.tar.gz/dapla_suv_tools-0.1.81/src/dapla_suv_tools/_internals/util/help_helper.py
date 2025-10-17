from typing import Callable


class HelpAssistant:
    function_help: dict

    def __init__(self):
        self.function_help = {}

    def register_function(self, function: Callable):
        self.function_help[function.__name__] = function.__doc__

    def register_functions(self, functions: list[Callable]):
        for func in functions:
            self.function_help[func.__name__] = func.__doc__

    def get_function_help_entry(self, name: str):
        return self.function_help.get(name, None)
