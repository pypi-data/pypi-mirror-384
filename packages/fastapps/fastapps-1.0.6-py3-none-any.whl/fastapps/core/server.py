from typing import List, Any, Dict, Optional
from fastmcp import FastMCP
from mcp import types
from .widget import BaseWidget, ClientContext


class WidgetMCPServer:
    """
    FastMCP-based MCP server with widget metadata support.
    
    Handles tool registration, resource templates, and widget execution.
    """
    
    def __init__(self, name: str, widgets: List[BaseWidget]):
        self.widgets_by_id = {w.identifier: w for w in widgets}
        self.widgets_by_uri = {w.template_uri: w for w in widgets}
        self.client_locale: Optional[str] = None
        
        self.mcp = FastMCP(name=name)
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all MCP handlers for widget support."""
        server = self.mcp._mcp_server
        
        # Handle MCP initialization to negotiate locale
        original_initialize = server.request_handlers.get(types.InitializeRequest)
        
        async def initialize_handler(req: types.InitializeRequest) -> types.ServerResult:
            # Extract requested locale from _meta
            meta = req.params._meta if hasattr(req.params, '_meta') else {}
            requested_locale = meta.get("openai/locale") or meta.get("webplus/i18n")
            
            # Negotiate locale with each widget
            if requested_locale:
                self.client_locale = requested_locale
                for widget in self.widgets_by_id.values():
                    resolved = widget.negotiate_locale(requested_locale)
                    widget.resolved_locale = resolved
            
            # Call original handler if it exists
            if original_initialize:
                return await original_initialize(req)
            
            # Default response if no original handler
            return types.ServerResult(
                types.InitializeResult(
                    protocolVersion=req.params.protocolVersion,
                    capabilities=types.ServerCapabilities(),
                    serverInfo=types.Implementation(name="FastApps", version="1.0.5")
                )
            )
        
        server.request_handlers[types.InitializeRequest] = initialize_handler
        
        @server.list_tools()
        async def list_tools_handler() -> List[types.Tool]:
            return [
                types.Tool(
                    name=w.identifier,
                    title=w.title,
                    description=w.description or w.title,
                    inputSchema=w.get_input_schema(),
                    _meta=w.get_tool_meta(),
                )
                for w in self.widgets_by_id.values()
            ]
        
        @server.list_resources()
        async def list_resources_handler() -> List[types.Resource]:
            return [
                types.Resource(
                    name=w.title,
                    title=w.title,
                    uri=w.template_uri,
                    description=f"{w.title} widget markup",
                    mimeType="text/html+skybridge",
                    _meta=w.get_resource_meta(),
                )
                for w in self.widgets_by_id.values()
            ]
        
        @server.list_resource_templates()
        async def list_resource_templates_handler() -> List[types.ResourceTemplate]:
            return [
                types.ResourceTemplate(
                    name=w.title,
                    title=w.title,
                    uriTemplate=w.template_uri,
                    description=f"{w.title} widget markup",
                    mimeType="text/html+skybridge",
                    _meta=w.get_resource_meta(),
                )
                for w in self.widgets_by_id.values()
            ]
        
        async def read_resource_handler(req: types.ReadResourceRequest) -> types.ServerResult:
            widget = self.widgets_by_uri.get(str(req.params.uri))
            if not widget:
                return types.ServerResult(
                    types.ReadResourceResult(
                        contents=[],
                        _meta={"error": f"Unknown resource: {req.params.uri}"}
                    )
                )
            
            contents = [
                types.TextResourceContents(
                    uri=widget.template_uri,
                    mimeType="text/html+skybridge",
                    text=widget.build_result.html,
                    _meta=widget.get_resource_meta(),
                )
            ]
            return types.ServerResult(types.ReadResourceResult(contents=contents))
        
        async def call_tool_handler(req: types.CallToolRequest) -> types.ServerResult:
            widget = self.widgets_by_id.get(req.params.name)
            if not widget:
                return types.ServerResult(
                    types.CallToolResult(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"Unknown tool: {req.params.name}"
                            )
                        ],
                        isError=True
                    )
                )
            
            try:
                arguments = req.params.arguments or {}
                input_data = widget.input_schema.model_validate(arguments)
                
                # Extract client context from request metadata
                meta = req.params._meta if hasattr(req.params, '_meta') else {}
                
                # Re-negotiate locale if provided in this request
                requested_locale = meta.get("openai/locale") or meta.get("webplus/i18n")
                if requested_locale:
                    widget.resolved_locale = widget.negotiate_locale(requested_locale)
                
                # Create client context
                context = ClientContext(meta)
                
                # Call execute with context
                result_data = await widget.execute(input_data, context)
            except Exception as exc:
                return types.ServerResult(
                    types.CallToolResult(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"Error: {str(exc)}"
                            )
                        ],
                        isError=True
                    )
                )
            
            widget_resource = widget.get_embedded_resource()
            meta: Dict[str, Any] = {
                "openai.com/widget": widget_resource.model_dump(mode="json"),
                "openai/outputTemplate": widget.template_uri,
                "openai/toolInvocation/invoking": widget.invoking,
                "openai/toolInvocation/invoked": widget.invoked,
                "openai/widgetAccessible": widget.widget_accessible,
                "openai/resultCanProduceWidget": True,
            }
            
            # Add resolved locale to response
            if widget.resolved_locale:
                meta["openai/locale"] = widget.resolved_locale
            
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=widget.invoked
                        )
                    ],
                    structuredContent=result_data,
                    _meta=meta,
                )
            )
        
        server.request_handlers[types.ReadResourceRequest] = read_resource_handler
        server.request_handlers[types.CallToolRequest] = call_tool_handler
    
    def get_app(self):
        """Get FastAPI app with CORS enabled."""
        app = self.mcp.http_app()
        
        try:
            from starlette.middleware.cors import CORSMiddleware
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
                allow_credentials=False
            )
        except Exception:
            pass
        
        return app

