from .._sdk import client
from .._sdk.legacy_assess_metadata import LegacyAssessMetadata


def fetch_legacy_assess_model(model_id: str) -> LegacyAssessMetadata:
    response = client.httpx_client.get(f"/assess-legacy/models/{model_id}/")
    if not response.is_success:
        raise ValueError(f"Unable to fetch assess metadata for {model_id}: {response.content}")
    assess_metadata = LegacyAssessMetadata.from_data(response.json()["definition"]).or_die()

    return assess_metadata
