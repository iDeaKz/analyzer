"""
Fixer to convert .format() calls to f-strings.
"""

import libcst as cst
import re
from typing import Tuple, Union, List, Dict


class FormatToFString(cst.CSTTransformer):
    """
    Transform .format() calls to f-strings.
    """
    
    def __init__(self):
        super().__init__()
        self.changes = 0
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> Union[cst.Call, cst.FormattedString]:
        """Process call nodes to find .format() calls."""
        # Check if this is a .format() call
        if (
            isinstance(original_node.func, cst.Attribute) 
            and isinstance(original_node.func.value, cst.SimpleString)
            and original_node.func.attr.value == "format"
        ):
            # Get the string template and format args
            template = original_node.func.value.value
            
            # Remove quotes from the template string
            if template.startswith(("'", '"')):
                template = template[1:-1]
            
            # Handle different format types:
            # 1. Positional: "{} and {}".format(x, y)
            # 2. Named: "{name} and {age}".format(name=x, age=y)
            # 3. Mixed: "{} and {age}".format(x, age=y)
            
            # Extract args and kwargs
            positional_args = []
            keyword_args = {}
            
            for arg in original_node.args:
                if arg.keyword is None:
                    positional_args.append(arg.value)
                else:
                    keyword_args[arg.keyword.value] = arg.value
            
            # Process template to f-string format
            # This is a simplified implementation - a complete version would need to handle
            # all format specifiers, nested braces, escaping, etc.
            
            # Find all format placeholders
            placeholder_pattern = r'\{([^{}]*)\}'
            placeholders = re.finditer(placeholder_pattern, template)
            
            # Generate f-string pieces
            parts = []
            last_end = 0
            idx = 0
            
            for match in placeholders:
                start, end = match.span()
                placeholder = match.group(1)
                
                # Add text before placeholder
                if start > last_end:
                    parts.append(cst.FormattedStringText(value=template[last_end:start]))
                
                # Process placeholder
                if placeholder == "":
                    # Positional placeholder: {}
                    if idx < len(positional_args):
                        parts.append(cst.FormattedStringExpression(expression=positional_args[idx]))
                        idx += 1
                elif placeholder.isdigit():
                    # Indexed placeholder: {0}
                    index = int(placeholder)
                    if index < len(positional_args):
                        parts.append(cst.FormattedStringExpression(expression=positional_args[index]))
                else:
                    # Named placeholder: {name}
                    if placeholder in keyword_args:
                        parts.append(cst.FormattedStringExpression(expression=keyword_args[placeholder]))
                
                last_end = end
            
            # Add remaining text
            if last_end < len(template):
                parts.append(cst.FormattedStringText(value=template[last_end:]))
            
            # Increment changes counter
            self.changes += 1
            
            # Return a formatted string
            return cst.FormattedString(parts=parts, start="f\"", end="\"")
        
        return updated_node
    
    def apply(self, source_code: str) -> Tuple[str, int]:
        """
        Apply the transformation to source code.
        
        Args:
            source_code: The source code to transform
            
        Returns:
            Tuple of (transformed_code, number_of_changes)
        """
        self.changes = 0
        
        try:
            module = cst.parse_module(source_code)
            modified_module = module.visit(self)
            return modified_module.code, self.changes
        
        except Exception as e:
            print(f"Error transforming code: {e}")
            return source_code, 0