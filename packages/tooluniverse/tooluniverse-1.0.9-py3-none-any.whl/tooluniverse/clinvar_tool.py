import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("ClinVarTool")
class ClinVarTool(BaseTool):
    """
    Local tool wrapper for ClinVar via NCBI E-utilities.
    Uses esearch + esummary to fetch variant records.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.session = requests.Session()

    def run(self, arguments):
        query = arguments.get("query")
        retmax = arguments.get("retmax", 5)
        if not query:
            return {"error": "Missing required parameter: query"}

        # 1) esearch to get UIDs
        search_url = f"{self.base}/esearch.fcgi"
        search_params = {
            "db": "clinvar",
            "term": query,
            "retmode": "json",
            "retmax": retmax,
        }
        search_resp = self.session.get(search_url, params=search_params, timeout=20)
        search_resp.raise_for_status()
        search_data = search_resp.json()
        uids = search_data.get("esearchresult", {}).get("idlist", [])
        if not uids:
            return []

        # 2) esummary to get details
        summary_url = f"{self.base}/esummary.fcgi"
        summary_params = {
            "db": "clinvar",
            "id": ",".join(uids),
            "retmode": "json",
        }
        summary_resp = self.session.get(summary_url, params=summary_params, timeout=30)
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        results = []
        for uid in uids:
            record = summary_data.get("result", {}).get(uid, {})
            if not record:
                continue

            # Extract key fields
            variation_set = record.get("variation_set", [])
            gene = ""
            chr_name = ""
            start = None
            stop = None
            spdi = ""
            if variation_set:
                var = variation_set[0]
                gene = record.get("genes", [{}])[0].get("symbol", "")
                var_loc = var.get("variation_loc", [{}])[0]
                chr_name = var_loc.get("chr", "")
                start = var_loc.get("start")
                stop = var_loc.get("stop")
                spdi = var.get("canonical_spdi", "")

            clinical_sig = record.get("germline_classification", {}).get(
                "description", ""
            )

            results.append(
                {
                    "uid": uid,
                    "accession": record.get("accession", ""),
                    "title": record.get("title", ""),
                    "gene": gene,
                    "chr": chr_name,
                    "start": start,
                    "stop": stop,
                    "spdi": spdi,
                    "clinical_significance": clinical_sig,
                }
            )

        return results
