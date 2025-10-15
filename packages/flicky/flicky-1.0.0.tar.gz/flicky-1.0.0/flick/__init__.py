"""
Flick - ChatGPT Widget Framework

A zero-boilerplate framework for building interactive ChatGPT widgets.

Example:
    from flick import BaseWidget, Field
    from typing import Dict, Any
    
    class MyWidget(BaseWidget):
        identifier = "my_widget"
        title = "My Widget"
        
        async def execute(self, input_data) -> Dict[str, Any]:
            return {"message": "Hello from Flick!"}
"""

__version__ = "1.0.0"
__author__ = "Flick Team"

from .core.widget import BaseWidget
from .core.server import WidgetMCPServer
from .builder.compiler import WidgetBuilder, WidgetBuildResult
from .types.schema import Field, ConfigDict

__all__ = [
    "BaseWidget",
    "WidgetMCPServer",
    "WidgetBuilder",
    "WidgetBuildResult",
    "Field",
    "ConfigDict",
]

