import requests
from typing import Any, Dict
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("UniProtRESTTool")
class UniProtRESTTool(BaseTool):
    def __init__(self, tool_config: Dict):
        super().__init__(tool_config)
        self.endpoint = tool_config["fields"]["endpoint"]
        self.extract_path = tool_config["fields"].get("extract_path")
        self.timeout = 15  # Increase timeout for large entries

    def _build_url(self, args: Dict[str, Any]) -> str:
        url = self.endpoint
        for k, v in args.items():
            url = url.replace(f"{{{k}}}", str(v))
        return url

    def _extract_data(self, data: Dict, extract_path: str) -> Any:
        """Custom data extraction with support for filtering"""

        # Handle specific UniProt extraction patterns
        if extract_path == "comments[?(@.commentType=='FUNCTION')].texts[*].value":
            # Extract function comments
            result = []
            for comment in data.get("comments", []):
                if comment.get("commentType") == "FUNCTION":
                    for text in comment.get("texts", []):
                        if "value" in text:
                            result.append(text["value"])
            return result

        elif (
            extract_path
            == "comments[?(@.commentType=='SUBCELLULAR LOCATION')].subcellularLocations[*].location.value"
        ):
            # Extract subcellular locations
            result = []
            for comment in data.get("comments", []):
                if comment.get("commentType") == "SUBCELLULAR LOCATION":
                    for location in comment.get("subcellularLocations", []):
                        if "location" in location and "value" in location["location"]:
                            result.append(location["location"]["value"])
            return result

        elif extract_path == "features[?(@.type=='VARIANT')]":
            # Extract variant features (correct type is "Natural variant")
            result = []
            for feature in data.get("features", []):
                if feature.get("type") == "Natural variant":
                    result.append(feature)
            return result

        elif (
            extract_path
            == "features[?(@.type=='MODIFIED RESIDUE' || @.type=='SIGNAL')]"
        ):
            # Extract PTM and signal features (correct types are "Modified residue" and "Signal")
            result = []
            for feature in data.get("features", []):
                if feature.get("type") in ["Modified residue", "Signal"]:
                    result.append(feature)
            return result

        elif (
            extract_path
            == "comments[?(@.commentType=='ALTERNATIVE PRODUCTS')].isoforms[*].isoformIds[*]"
        ):
            # Extract isoform IDs
            result = []
            for comment in data.get("comments", []):
                if comment.get("commentType") == "ALTERNATIVE PRODUCTS":
                    for isoform in comment.get("isoforms", []):
                        for isoform_id in isoform.get("isoformIds", []):
                            result.append(isoform_id)
            return result

        # For simple paths, use jsonpath_ng
        try:
            from jsonpath_ng import parse

            expr = parse(extract_path)
            matches = expr.find(data)
            extracted_data = [m.value for m in matches]

            # Return single item if only one match, otherwise return list
            if len(extracted_data) == 0:
                return {"error": f"No data found for JSONPath: {extract_path}"}
            elif len(extracted_data) == 1:
                return extracted_data[0]
            else:
                return extracted_data

        except ImportError:
            return {"error": "jsonpath_ng library is required for data extraction"}
        except Exception as e:
            return {
                "error": f"Failed to extract UniProt fields using JSONPath '{extract_path}': {e}"
            }

    def run(self, arguments: Dict[str, Any]) -> Any:
        # Build URL
        url = self._build_url(arguments)
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                return {
                    "error": f"UniProt API returned status code: {resp.status_code}",
                    "detail": resp.text,
                }
            data = resp.json()
        except requests.exceptions.Timeout:
            return {"error": "Request to UniProt API timed out"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request to UniProt API failed: {e}"}
        except ValueError as e:
            return {"error": f"Failed to parse JSON response: {e}"}

        # If extract_path is configured, extract the corresponding subset
        if self.extract_path:
            result = self._extract_data(data, self.extract_path)

            # Handle empty results
            if isinstance(result, list) and len(result) == 0:
                return {"error": f"No data found for path: {self.extract_path}"}
            elif isinstance(result, dict) and "error" in result:
                return result

            return result

        return data

    # Method bindings for backward compatibility
    def get_entry_by_accession(self, accession: str) -> Any:
        return self.run({"accession": accession})

    def get_function_by_accession(self, accession: str) -> Any:
        return self.run({"accession": accession})

    def get_names_taxonomy_by_accession(self, accession: str) -> Any:
        return self.run({"accession": accession})

    def get_subcellular_location_by_accession(self, accession: str) -> Any:
        return self.run({"accession": accession})

    def get_disease_variants_by_accession(self, accession: str) -> Any:
        return self.run({"accession": accession})

    def get_ptm_processing_by_accession(self, accession: str) -> Any:
        return self.run({"accession": accession})

    def get_sequence_isoforms_by_accession(self, accession: str) -> Any:
        return self.run({"accession": accession})
