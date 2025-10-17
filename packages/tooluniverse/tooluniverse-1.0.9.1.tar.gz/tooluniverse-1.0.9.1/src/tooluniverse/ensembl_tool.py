import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("EnsemblTool")
class EnsemblTool(BaseTool):
    """
    Local tool wrapper for Ensembl REST API lookups.
    Supports symbol→gene lookup (xrefs/symbol) then lookup/id to
    fetch metadata.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base = "https://rest.ensembl.org"
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )

    def run(self, arguments):
        species = arguments.get("species", "homo_sapiens")
        symbol = arguments.get("symbol")
        if not symbol:
            return {"error": "Missing required parameter: symbol"}

        # 1) symbol -> xref(s) to get Ensembl gene ID
        xref_url = f"{self.base}/xrefs/symbol/{species}/{symbol}"
        xref_resp = self.session.get(xref_url, timeout=20)
        xref_resp.raise_for_status()
        xrefs = xref_resp.json() or []
        gene_id = None
        for item in xrefs:
            if item.get("type") == "gene" and item.get("id"):
                gene_id = item["id"]
                break
        if not gene_id and xrefs:
            gene_id = xrefs[0].get("id")
        if not gene_id:
            return {"error": f"No Ensembl gene found for {symbol}"}

        # 2) lookup by Ensembl ID (expand=1 to include transcripts)
        lookup_url = f"{self.base}/lookup/id/{gene_id}?expand=1"
        look_resp = self.session.get(lookup_url, timeout=30)
        look_resp.raise_for_status()
        data = look_resp.json() or {}

        transcripts = data.get("Transcript") or []
        return {
            "id": data.get("id"),
            "symbol": symbol,
            "display_name": data.get("display_name"),
            "species": data.get("species"),
            "seq_region_name": data.get("seq_region_name"),
            "start": data.get("start"),
            "end": data.get("end"),
            "strand": data.get("strand"),
            "biotype": data.get("biotype"),
            "transcript_count": len(transcripts),
        }
