import requests
import json
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("GnomadTool")
class GnomadTool(BaseTool):
    """
    Local tool wrapper for gnomAD GraphQL API.
    Queries variant information including allele frequencies.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base = "https://gnomad.broadinstitute.org/api"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def run(self, arguments):
        variant_id = arguments.get("variant_id")
        dataset = arguments.get("dataset", "gnomad_r4")

        if not variant_id:
            return {"error": "Missing required parameter: variant_id"}

        # GraphQL query for variant with genome frequencies
        query = """
        query($variant: String!, $dataset: DatasetId!) {
            variant(variantId: $variant, dataset: $dataset) {
                variantId
                genome {
                    ac
                    an
                    af
                }
            }
        }
        """

        payload = {
            "query": query,
            "variables": {
                "variant": variant_id,
                "dataset": dataset,
            },
        }

        resp = self.session.post(self.base, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            return {"error": f"GraphQL errors: {data['errors']}"}

        variant = data.get("data", {}).get("variant")
        if not variant:
            return {"error": "Variant not found"}

        return {
            "variantId": variant.get("variantId"),
            "genome": variant.get("genome", {}),
        }
