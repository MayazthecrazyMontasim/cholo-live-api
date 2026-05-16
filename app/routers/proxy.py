"""
Proxy router — forwards third-party API calls server-side so API keys
are never exposed in frontend source code.
"""

import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from ..config import FOURSQUARE_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proxy", tags=["Proxy"])

FSQ_BASE = "https://api.foursquare.com/v3/places/search"


@router.get("/places")
async def foursquare_places(
    ll: str = Query(..., description="lat,lon e.g. 21.43,91.98"),
    categories: str = Query(..., description="Foursquare category IDs, comma-separated"),
    radius: int = Query(15000, ge=100, le=50000),
    limit: int = Query(20, ge=1, le=50),
    fields: str = Query("fsq_id,name,location,rating,price,distance,geocodes"),
):
    if not FOURSQUARE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Places service not configured. Set FOURSQUARE_API_KEY on the server."
        )

    params = {
        "ll":         ll,
        "categories": categories,
        "radius":     radius,
        "limit":      limit,
        "fields":     fields,
    }
    headers = {
        "Authorization": FOURSQUARE_API_KEY,
        "Accept":        "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(FSQ_BASE, params=params, headers=headers)

        if resp.status_code == 401:
            logger.error("Foursquare 401 — check FOURSQUARE_API_KEY env var")
            raise HTTPException(status_code=502, detail="Places API authentication failed")

        if not resp.is_success:
            logger.warning("Foursquare %s: %s", resp.status_code, resp.text[:200])
            raise HTTPException(status_code=502, detail="Places API error")

        return resp.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Places API timed out")
    except httpx.RequestError as exc:
        logger.error("Foursquare request error: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach Places API")
