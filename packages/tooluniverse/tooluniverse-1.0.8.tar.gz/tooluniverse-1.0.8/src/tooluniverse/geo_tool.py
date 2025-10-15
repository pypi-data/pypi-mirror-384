"""
GEO Database REST API Tool

This tool provides access to gene expression data from the GEO database.
GEO is a public repository that archives and freely distributes microarray,
next-generation sequencing, and other forms of high-throughput functional
genomics data.
"""

import requests
from typing import Dict, Any, List
from .base_tool import BaseTool
from .tool_registry import register_tool

GEO_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@register_tool("GEORESTTool")
class GEORESTTool(BaseTool):
    """
    GEO Database REST API tool.
    Generic wrapper for GEO API endpoints defined in expression_tools.json.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        fields = tool_config.get("fields", {})
        parameter = tool_config.get("parameter", {})

        self.endpoint_template: str = fields.get("endpoint", "/esearch.fcgi")
        self.required: List[str] = parameter.get("required", [])
        self.output_format: str = fields.get("return_format", "JSON")

    def _build_url(self, arguments: Dict[str, Any]) -> str | Dict[str, Any]:
        """Build URL for GEO API request."""
        url_path = self.endpoint_template
        return GEO_BASE_URL + url_path

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build parameters for GEO API request."""
        params = {"db": "gds", "retmode": "json", "retmax": 50}

        # Build search query
        query_parts = []
        if "query" in arguments:
            query_parts.append(arguments["query"])

        if "organism" in arguments:
            organism = arguments["organism"]
            if organism.lower() == "homo sapiens":
                query_parts.append("Homo sapiens[organism]")
            elif organism.lower() == "mus musculus":
                query_parts.append("Mus musculus[organism]")
            else:
                query_parts.append(f'"{organism}"[organism]')

        if "study_type" in arguments:
            study_type = arguments["study_type"]
            query_parts.append(f'"{study_type}"[study_type]')

        if "platform" in arguments:
            platform = arguments["platform"]
            query_parts.append(f'"{platform}"[platform]')

        if "date_range" in arguments:
            date_range = arguments["date_range"]
            if ":" in date_range:
                start_year, end_year = date_range.split(":")
                query_parts.append(f'"{start_year}"[PDAT] : "{end_year}"[PDAT]')

        if query_parts:
            params["term"] = " AND ".join(query_parts)

        if "limit" in arguments:
            params["retmax"] = min(arguments["limit"], 500)

        if "sort" in arguments:
            sort = arguments["sort"]
            if sort == "date":
                params["sort"] = "relevance"
            elif sort == "title":
                params["sort"] = "title"
            else:
                params["sort"] = "relevance"

        return params

    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a GET request and handle common errors."""
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            if self.output_format == "JSON":
                return response.json()
            else:
                return {"data": response.text}

        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given arguments."""
        # Validate required parameters
        for param in self.required:
            if param not in arguments:
                return {"error": f"Missing required parameter: {param}"}

        url = self._build_url(arguments)
        if isinstance(url, dict) and "error" in url:
            return url

        params = self._build_params(arguments)
        return self._make_request(url, params)
