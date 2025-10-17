import requests
import re
from typing import Dict, Any, List
from .base_tool import BaseTool
from .tool_registry import register_tool

ALPHAFOLD_BASE_URL = "https://alphafold.ebi.ac.uk/api"


@register_tool("AlphaFoldRESTTool")
class AlphaFoldRESTTool(BaseTool):
    """
    AlphaFold Protein Structure Database API tool.
    Generic wrapper for AlphaFold API endpoints defined in alphafold_tools.json.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        fields = tool_config.get("fields", {})
        parameter = tool_config.get("parameter", {})

        self.endpoint_template: str = fields["endpoint"]
        self.required: List[str] = parameter.get("required", [])
        self.output_format: str = fields.get("return_format", "JSON")

    def _build_url(self, arguments: Dict[str, Any]) -> str | Dict[str, Any]:
        # Example: endpoint_template = "/annotations/{qualifier}.json"
        url_path = self.endpoint_template
        # Find placeholders like {qualifier} in the path
        placeholders = re.findall(r"\{([^{}]+)\}", url_path)
        used = set()

        # Replace placeholders with provided arguments
        #   ex. if arguments = {"qualifier": "P69905", "type": "MUTAGEN"}
        for ph in placeholders:
            if ph not in arguments or arguments[ph] is None:
                return {"error": f"Missing required parameter '{ph}'"}
            url_path = url_path.replace(f"{{{ph}}}", str(arguments[ph]))
            used.add(ph)
        # Now url_path = "/annotations/P69905.json"

        # Treat all remaining args as query parameters
        #   "type" wasn’t a placeholder, so it becomes a query param
        query_args = {k: v for k, v in arguments.items() if k not in used}
        if query_args:
            from urllib.parse import urlencode

            url_path += "?" + urlencode(query_args)

        # Final result = "https://alphafold.ebi.ac.uk/api/annotations/P69905.json?type=MUTAGEN"
        return ALPHAFOLD_BASE_URL + url_path

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Perform a GET request and handle common errors."""
        try:
            resp = requests.get(
                url,
                timeout=30,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "ToolUniverse/AlphaFold",
                },
            )
        except Exception as e:
            return {"error": "Request to AlphaFold API failed", "detail": str(e)}

        if resp.status_code == 404:
            return {"error": "Not found", "endpoint": url}
        if resp.status_code != 200:
            return {
                "error": f"AlphaFold API returned {resp.status_code}",
                "detail": resp.text,
                "endpoint": url,
            }

        return {"response": resp}

    def run(self, arguments: Dict[str, Any]):
        """Execute the tool with provided arguments."""
        # Validate required params
        missing = [k for k in self.required if k not in arguments]
        if missing:
            return {"error": f"Missing required parameter(s): {', '.join(missing)}"}

        # Build URL
        url = self._build_url(arguments)
        if isinstance(url, dict) and "error" in url:
            return {**url, "query": arguments}

        # Make request
        result = self._make_request(url)
        if "error" in result:
            return {**result, "query": arguments}

        resp = result["response"]

        # Parse JSON
        if self.output_format.upper() == "JSON":
            try:
                data = resp.json()
                if not data:
                    return {
                        "error": "AlphaFold returned an empty response",
                        "endpoint": url,
                        "query": arguments,
                    }

                return {
                    "data": data,
                    "metadata": {
                        "count": len(data) if isinstance(data, list) else 1,
                        "source": "AlphaFold Protein Structure DB",
                        "endpoint": url,
                        "query": arguments,
                    },
                }
            except Exception as e:
                return {
                    "error": "Failed to parse JSON response",
                    "raw": resp.text,
                    "detail": str(e),
                    "endpoint": url,
                    "query": arguments,
                }

        # Fallback for non-JSON output
        return {"data": resp.text, "metadata": {"endpoint": url, "query": arguments}}
