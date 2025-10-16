import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("UCSCTool")
class UCSCTool(BaseTool):
    """
    Local tool wrapper for UCSC Genome Browser track API.
    Queries knownGene track for genomic regions.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base = "https://api.genome.ucsc.edu/getData/track"
        self.session = requests.Session()

    def run(self, arguments):
        genome = arguments.get("genome", "hg38")
        chrom = arguments.get("chrom")
        start = arguments.get("start")
        end = arguments.get("end")
        track = arguments.get("track", "knownGene")

        if not all([chrom, start is not None, end is not None]):
            return {"error": "Missing required parameters: chrom, start, end"}

        params = {
            "genome": genome,
            "track": track,
            "chrom": chrom,
            "start": start,
            "end": end,
        }

        resp = self.session.get(self.base, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        features = data.get(track, [])
        items_returned = len(features)

        # Extract key fields from each feature
        processed_features = []
        for feature in features:
            processed_features.append(
                {
                    "name": feature.get("name", ""),
                    "geneName": feature.get("geneName", ""),
                    "chrom": feature.get("chrom", ""),
                    "chromStart": feature.get("chromStart"),
                    "chromEnd": feature.get("chromEnd"),
                    "strand": feature.get("strand", ""),
                }
            )

        return {
            "itemsReturned": items_returned,
            "features": processed_features,
        }
