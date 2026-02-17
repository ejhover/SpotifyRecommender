"""
FastAPI backend for Spotify AI Recommendations.
Run with: uvicorn main:app --reload
"""

from __future__ import annotations

import os
import secrets
import base64
import hashlib
from pathlib import Path
from typing import List, Optional

import numpy as np
import spotipy
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from spotipy.oauth2 import SpotifyOAuth

from recommender import Recommender
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────
SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
FRONTEND_URL          = os.getenv("FRONTEND_URL", "http://localhost:5173")

SCOPES = " ".join([
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-modify-playback-state",
    "user-read-playback-state",
])

BASE_DIR        = Path(__file__).parent
MODEL_PATH      = BASE_DIR / "model_weights.pt"
SCALER_PATH     = BASE_DIR / "scaler.pkl"
EMBEDDINGS_PATH = BASE_DIR / "embeddings.npy"
TRACK_IDS_PATH  = BASE_DIR / "track_ids.pkl"

# ── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(title="Spotify AI Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load ML artifacts once at startup ──────────────────────────────────────
recommender: Optional[Recommender] = None


@app.on_event("startup")
def load_model():
    global recommender
    if all(p.exists() for p in [MODEL_PATH, SCALER_PATH, EMBEDDINGS_PATH, TRACK_IDS_PATH]):
        recommender = Recommender(
            model_path=str(MODEL_PATH),
            scaler_path=str(SCALER_PATH),
            embeddings_path=str(EMBEDDINGS_PATH),
            track_ids_path=str(TRACK_IDS_PATH),
        )
        print("✅ Model and embeddings loaded.")
    else:
        print("⚠️  Model artifacts not found. Run training/train_model.py first.")


# ── In-memory session store (swap for Redis in production) ──────────────────
sessions: dict[str, dict] = {}


def get_sp(token_info: dict) -> spotipy.Spotify:
    return spotipy.Spotify(auth=token_info["access_token"])


def get_audio_features(sp: spotipy.Spotify, track_ids: List[str]) -> List[dict]:
    """Batch-fetch audio features from Spotify."""
    if not track_ids:
        return []
    features = sp.audio_features(track_ids)
    return [f for f in features if f is not None]


# ─────────────────────────────────────────────────────────────────────────────
# Auth Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/login")
def login():
    """Redirect user to Spotify's authorization page."""
    state = secrets.token_urlsafe(16)
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPES,
        state=state,
    )
    auth_url = sp_oauth.get_authorize_url()
    response = RedirectResponse(auth_url)
    response.set_cookie("spotify_state", state, httponly=True, samesite="lax")
    return response


@app.get("/callback")
def callback(request: Request, code: str, state: str):
    """Exchange authorization code for tokens."""
    stored_state = request.cookies.get("spotify_state")
    if stored_state != state:
        raise HTTPException(400, "State mismatch")

    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPES,
    )
    token_info = sp_oauth.get_access_token(code, as_dict=True)

    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {"token_info": token_info, "session_embedding": None}

    redirect = RedirectResponse(f"{FRONTEND_URL}?session={session_id}")
    redirect.delete_cookie("spotify_state")
    return redirect


# ─────────────────────────────────────────────────────────────────────────────
# Spotify Data Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/current-song")
def current_song(session_id: str):
    """Return currently playing track (or most recent)."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(401, "Invalid session")

    sp = get_sp(session["token_info"])

    # Try currently playing first
    current = sp.currently_playing()
    if current and current.get("item"):
        track = current["item"]
        return {
            "id": track["id"],
            "name": track["name"],
            "artists": [a["name"] for a in track["artists"]],
            "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "is_playing": True,
        }

    # Fall back to most recently played
    recent = sp.current_user_recently_played(limit=1)
    if recent and recent["items"]:
        track = recent["items"][0]["track"]
        return {
            "id": track["id"],
            "name": track["name"],
            "artists": [a["name"] for a in track["artists"]],
            "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "is_playing": False,
        }

    raise HTTPException(404, "No recent tracks found")


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Routes
# ─────────────────────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    session_id: str
    current_track_id: str
    moods: List[str]
    n: int = 5


class RejectRequest(BaseModel):
    session_id: str
    rejected_track_id: str
    current_recommendations: List[str]
    recently_played_ids: List[str]


class QueueRequest(BaseModel):
    session_id: str
    track_ids: List[str]


@app.post("/recommend")
def recommend(body: RecommendRequest):
    if not recommender:
        raise HTTPException(503, "Model not loaded. Run training first.")

    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(401, "Invalid session")

    sp = get_sp(session["token_info"])

    # Fetch listening history (last 50 tracks)
    recent_data = sp.current_user_recently_played(limit=50)
    history_ids = [item["track"]["id"] for item in recent_data["items"]]

    # Gather audio features
    history_features = get_audio_features(sp, history_ids[:30])
    current_features_list = get_audio_features(sp, [body.current_track_id])

    if not current_features_list:
        raise HTTPException(400, "Could not fetch audio features for current track")

    current_features = current_features_list[0]
    exclude_ids = list(set(history_ids))

    rec_ids, final_emb = recommender.recommend(
        history_features=history_features,
        current_features=current_features,
        moods=body.moods,
        n=body.n,
        exclude_ids=exclude_ids,
        session_embedding=None,
    )

    # Persist session embedding
    session["session_embedding"] = final_emb.tolist()
    session["recently_played_ids"] = history_ids

    # Enrich with Spotify metadata
    tracks = sp.tracks(rec_ids)["tracks"]
    return {
        "recommendations": [
            {
                "id": t["id"],
                "name": t["name"],
                "artists": [a["name"] for a in t["artists"]],
                "album_art": t["album"]["images"][0]["url"] if t["album"]["images"] else None,
            }
            for t in tracks if t
        ]
    }


@app.post("/reject")
def reject_track(body: RejectRequest):
    if not recommender:
        raise HTTPException(503, "Model not loaded. Run training first.")

    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(401, "Invalid session")

    if session["session_embedding"] is None:
        raise HTTPException(400, "No active session embedding. Call /recommend first.")

    sp = get_sp(session["token_info"])
    session_emb = np.array(session["session_embedding"], dtype=np.float32)

    rejected_features_list = get_audio_features(sp, [body.rejected_track_id])
    if not rejected_features_list:
        raise HTTPException(400, "Could not fetch audio features for rejected track")

    rejected_features = rejected_features_list[0]
    exclude_ids = (
        body.current_recommendations
        + body.recently_played_ids
        + [body.rejected_track_id]
    )

    replacement_ids, new_emb = recommender.reject(
        session_embedding=session_emb,
        rejected_features=rejected_features,
        exclude_ids=exclude_ids,
        n=1,
    )

    session["session_embedding"] = new_emb.tolist()

    # Enrich replacement
    tracks = sp.tracks(replacement_ids)["tracks"]
    replacement = tracks[0] if tracks else None
    if not replacement:
        raise HTTPException(500, "Could not find a replacement track")

    return {
        "replacement": {
            "id": replacement["id"],
            "name": replacement["name"],
            "artists": [a["name"] for a in replacement["artists"]],
            "album_art": replacement["album"]["images"][0]["url"] if replacement["album"]["images"] else None,
        }
    }


@app.post("/add-to-queue")
def add_to_queue(body: QueueRequest):
    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(401, "Invalid session")

    sp = get_sp(session["token_info"])

    added = []
    for track_id in body.track_ids:
        try:
            sp.add_to_queue(f"spotify:track:{track_id}")
            added.append(track_id)
        except Exception as e:
            print(f"Failed to queue {track_id}: {e}")

    return {"queued": added, "count": len(added)}
