"""
Real-Time Event Streaming Router using Server-Sent Events (SSE).
Streams live seismic events and operational status without page refresh.
Includes heartbeats and graceful reconnection handling.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from api.src.database import get_db
from api.src.auth import get_current_user

logger = logging.getLogger("sismowatch.stream")

router = APIRouter(prefix="/api/stream", tags=["Real-Time Stream"])

async def event_generator(username: str):
    """
    Asynchronous SSE generator.
    Periodically checks for newly synced events and delivers updates to connected clients.
    """
    last_checked_time = datetime.now(timezone.utc)
    
    # Send initial connected message
    initial_payload = {
        "type": "connection_established",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connected_user": username
    }
    yield f"event: connect\ndata: {json.dumps(initial_payload)}\n\n"
    
    while True:
        try:
            # Query recent events synced since last check
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            event_id, mag, place, event_time, updated_time, tsunami, sig,
                            status, mag_type, event_type, url, longitude, latitude, depth_km,
                            last_synced_at
                        FROM curated.earthquakes
                        WHERE last_synced_at >= %s
                        ORDER BY last_synced_at DESC
                        LIMIT 15;
                    """, (last_checked_time,))
                    new_events = cur.fetchall()

            last_checked_time = datetime.now(timezone.utc)

            if new_events:
                events_data = [
                    {
                        "event_id": r["event_id"],
                        "mag": float(r["mag"]),
                        "place": r["place"],
                        "event_time": r["event_time"].isoformat(),
                        "tsunami": int(r["tsunami"]),
                        "longitude": float(r["longitude"]),
                        "latitude": float(r["latitude"]),
                        "depth_km": float(r["depth_km"]),
                        "last_synced_at": r["last_synced_at"].isoformat()
                    }
                    for r in new_events
                ]
                message = {
                    "type": "earthquake_batch",
                    "count": len(events_data),
                    "events": events_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                yield f"event: earthquake_update\ndata: {json.dumps(message)}\n\n"

            # Periodic heartbeat ping to keep HTTP connection alive through proxies
            yield f": heartbeat {datetime.now(timezone.utc).isoformat()}\n\n"

            # Sleep 5 seconds before next polling cycle
            await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info(f"SSE stream client {username} disconnected.")
            break
        except Exception as e:
            logger.error(f"Error in SSE generator: {e}")
            await asyncio.sleep(5)

@router.get("")
def stream_events(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Server-Sent Events endpoint for real-time monitoring.
    Reconnection supported via EventSource.
    """
    return StreamingResponse(
        event_generator(current_user["username"]),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Prevents Nginx from buffering SSE events
        }
    )
