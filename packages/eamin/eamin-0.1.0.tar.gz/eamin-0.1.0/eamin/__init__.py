"""
eamin - A fun Python package for dynamic attribute access
Allows any attribute call to output its name
"""

import sys


class EaminModule:
    """A magical module class that dynamically responds to any attribute access"""
    
    def __getattr__(self, name):
        """
        When accessing any attribute, return a function
        This function accepts a callable (like print) and uses it to output the attribute name
        """
        def magic_func(func=print):
            """
            Magic function: calls the provided function with the attribute name
            
            Args:
                func: A callable object, defaults to print
            
            Returns:
                The result of calling func(name)
            """
            return func(name)
        
        return magic_func


# Replace the current module with our custom class instance
sys.modules[__name__] = EaminModule()

