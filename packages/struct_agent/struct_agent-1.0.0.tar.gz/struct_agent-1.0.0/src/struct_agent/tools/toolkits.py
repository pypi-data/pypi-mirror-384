from __future__ import annotations

from typing import Any, Dict, List

from struct_agent.tools.searxng_tools import *
from struct_agent.tools.maths_tools import *
from struct_agent.tools.leann_tools import *

class BaseToolkit:
    """A base class for toolkits to avoid repetitive code."""
    TOOL_FACTORIES = []

    def __init__(self):
        """Initializes the toolkit by creating all the tool instances."""
        self.tools = [factory() for factory in self.TOOL_FACTORIES]
        # The f-string provides a nice confirmation message when a toolkit is created
        print(f"✅ {self.__class__.__name__} initialized with {len(self.tools)} tools.")

    def __iter__(self):
        """Makes the toolkit instance iterable."""
        return iter(self.tools)

class MathsToolkit(BaseToolkit):
    """Toolkit for mathematical operations and symbolic algebra."""
    TOOL_FACTORIES = [
        make_calc_tool,
        make_sympy_solve_equation_tool,
        make_sympy_simplify_expression_tool,
        make_sympy_expand_expression_tool,
        make_sympy_factor_expression_tool,
        make_sympy_differentiate_tool,
        make_sympy_integrate_tool,
        make_sympy_matrix_operation_tool,
    ]

class MetaSearchToolkit(BaseToolkit):
    """Toolkit for performing meta-searches with SearXNG."""
    TOOL_FACTORIES = [
        make_searxng_search_tool,
    ]

class VectorIndexToolkit(BaseToolkit):
    """Toolkit for vector indexing and semantic search operations using LEANN."""
    TOOL_FACTORIES = [
        make_leann_add_text_tool,
        make_leann_search_tool,
        make_leann_chat_tool,
    ]

def create_toolspecs_from_toolkits(toolkits: List[BaseToolkit], verbose: bool = True) -> Dict[str, Any]:
    """Create toolspecs by running all factory functions from specified toolkits."""
    all_tools = []

    for toolkit in toolkits:
        toolkit = toolkit()

        toolkit_tools = list(toolkit)
        all_tools.extend(toolkit_tools)

        if verbose:
            print(f"   ✅ Added {len(toolkit_tools)} tools from {toolkit.__class__.__name__}")

    if verbose:
        print(f"🎯 Total tools loaded: {len(all_tools)}")

    return all_tools

__all__ = [
    "BaseToolkit",
    "MathsToolkit",
    "MetaSearchToolkit",
    "VectorIndexToolkit",
    "create_toolspecs_from_toolkits",
]

if __name__ == "__main__":
    for toolkit in [MathsToolkit(), MetaSearchToolkit(), VectorIndexToolkit()]:
        print(f"{toolkit.__class__.__name__}")
        for tool in toolkit:
            print(f"    {tool.name}")