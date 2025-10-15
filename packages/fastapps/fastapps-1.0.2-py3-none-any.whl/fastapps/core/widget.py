from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
import mcp.types as types


class BaseWidget(ABC):
    """
    Base class for Flick widgets.
    
    Inherit from this class to create custom ChatGPT widgets.
    """
    identifier: str
    title: str
    input_schema: type[BaseModel]
    description: str = ""
    invoking: str = "Processing..."
    invoked: str = "Completed"
    
    # OpenAI advanced options
    widget_accessible: bool = True
    widget_description: Optional[str] = None
    widget_csp: Optional[Dict[str, List[str]]] = None
    widget_prefers_border: bool = False
    read_only: bool = True
    
    def __init__(self, build_result: 'WidgetBuildResult'):
        self.build_result = build_result
        self.template_uri = f"ui://widget/{self.identifier}.html"
    
    @abstractmethod
    async def execute(self, input_data: BaseModel) -> Dict[str, Any]:
        """Execute the widget logic and return data for the UI."""
        pass
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Convert Pydantic model to JSON Schema."""
        return self.input_schema.model_json_schema()
    
    def get_tool_meta(self) -> Dict[str, Any]:
        """Tool metadata following MCP specification."""
        meta = {
            "openai/outputTemplate": self.template_uri,
            "openai/toolInvocation/invoking": self.invoking,
            "openai/toolInvocation/invoked": self.invoked,
            "openai/widgetAccessible": self.widget_accessible,
            "openai/resultCanProduceWidget": True,
            "annotations": {
                "readOnlyHint": self.read_only,
            }
        }
        return meta
    
    def get_resource_meta(self) -> Dict[str, Any]:
        """Resource metadata (CSP, border settings)."""
        meta = {}
        if self.widget_csp:
            meta["openai/widgetCSP"] = self.widget_csp
        if self.widget_prefers_border:
            meta["openai/widgetPrefersBorder"] = True
        if self.widget_description:
            meta["openai/widgetDescription"] = self.widget_description
        return meta
    
    def get_embedded_resource(self) -> types.EmbeddedResource:
        """Build embedded resource for tool response."""
        return types.EmbeddedResource(
            type="resource",
            resource=types.TextResourceContents(
                uri=self.template_uri,
                mimeType="text/html+skybridge",
                text=self.build_result.html,
                title=self.title,
                _meta=self.get_resource_meta(),
            ),
        )

