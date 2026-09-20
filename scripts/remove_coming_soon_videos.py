"""Remove coming_soon event videos that have no real recording (no URL, no thumbnail)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import ContentVideo

IDS_TO_REMOVE = [
    "poets-and-friends-2",
    "poets-and-friends-1",
    "ahoy-cabaret-2",
    "ahoy-cabaret-1",
]

with get_session() as session:
    rows = session.query(ContentVideo).filter(ContentVideo.video_id.in_(IDS_TO_REMOVE)).all()
    if not rows:
        print("No matching records found — already clean.")
    else:
        for row in rows:
            print(f"Deleting: {row.video_id} — {row.title}")
            session.delete(row)
        session.commit()
        print(f"Deleted {len(rows)} record(s).")
