from rcsbapi.data import DataQuery
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("RCSBTool")
class RCSBTool(BaseTool):
    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.name = tool_config.get("name")
        self.description = tool_config.get("description")
        self.input_type = tool_config.get("input_type")
        self.search_fields = tool_config.get("fields", {}).get("search_fields", {})
        self.return_fields = tool_config.get("fields", {}).get("return_fields", [])
        self.parameter_schema = tool_config.get("parameter", {}).get("properties", {})

    def validate_params(self, params: dict):
        for param_name, param_info in self.parameter_schema.items():
            if param_info.get("required", False) and param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")
        return True

    def prepare_input_ids(self, params: dict):
        for param_name in self.search_fields:
            if param_name in params:
                val = params[param_name]
                return val if isinstance(val, list) else [val]
        raise ValueError("No valid search parameter provided")

    def run(self, params: dict):
        self.validate_params(params)
        input_ids = self.prepare_input_ids(params)
        query = DataQuery(
            input_type=self.input_type,
            input_ids=input_ids,
            return_data_list=self.return_fields,
        )
        return query.exec()
