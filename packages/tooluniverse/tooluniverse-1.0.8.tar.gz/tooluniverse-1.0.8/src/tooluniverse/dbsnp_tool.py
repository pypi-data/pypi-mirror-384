import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("DbSnpTool")
class DbSnpTool(BaseTool):
    """
    Local tool wrapper for dbSNP via NCBI Variation Services.
    Fetches variant by rsID using the refsnp endpoint.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base = "https://api.ncbi.nlm.nih.gov/variation/v0"
        self.session = requests.Session()

    def run(self, arguments):
        rsid = arguments.get("rsid")
        if not rsid:
            return {"error": "Missing required parameter: rsid"}

        # Clean rsid (remove 'rs' prefix if present)
        if rsid.startswith("rs"):
            rsid = rsid[2:]

        url = f"{self.base}/refsnp/{rsid}"
        resp = self.session.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        # Extract key fields from primary snapshot
        primary = data.get("primary_snapshot_data", {})
        placements = primary.get("placements_with_allele", [])

        chrom = ""
        pos = None
        alleles = []
        hgvs = []

        if placements:
            placement = placements[0]
            chrom = (
                placement.get("seq_id", "").replace("NC_0000", "").replace(".11", "")
            )
            if chrom.startswith("0"):
                chrom = chrom[1:]
            chrom = f"chr{chrom}"

            allele_data = placement.get("alleles", [])
            for allele in allele_data:
                spdi = allele.get("allele", {}).get("spdi", {})
                if spdi:
                    ref = spdi.get("deleted_sequence", "")
                    alt = spdi.get("inserted_sequence", "")
                    if ref and alt:
                        alleles.append(f"{ref}>{alt}")
                    elif ref:
                        alleles.append(ref)

                hgvs_val = allele.get("hgvs", "")
                if hgvs_val:
                    hgvs.append(hgvs_val)

        return {
            "refsnp_id": f"rs{rsid}",
            "chrom": chrom,
            "pos": pos,
            "alleles": alleles,
            "hgvs": hgvs,
        }
