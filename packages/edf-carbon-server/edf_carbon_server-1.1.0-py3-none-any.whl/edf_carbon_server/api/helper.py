"""API Helper"""

from aiohttp.web import Request
from edf_fusion.concept import Identity
from edf_fusion.server.auth import get_fusion_auth_api
from edf_fusion.server.storage import get_fusion_storage

from ..storage import Storage


async def prologue(
    request: Request, operation: str, context: dict
) -> tuple[Identity, Storage]:
    """Retrieve identity and storage and perform authorization checks"""
    fusion_auth_api = get_fusion_auth_api(request)
    identity = await fusion_auth_api.authorize(
        request, operation, context=context
    )
    storage = get_fusion_storage(request)
    return identity, storage
