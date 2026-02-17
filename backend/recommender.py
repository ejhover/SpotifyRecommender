"""
Recommendation engine.
All math lives here; no Spotify / HTTP concerns.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity

from model import SongAutoencoder, load_model

# ── Audio feature column order (must match training) ─────────────────────────
FEATURE_COLS = [
    "danceability", "energy", "key", "loudness", "mode",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo",
]

# ── Mood → raw feature delta mappings ────────────────────────────────────────
MOOD_FEATURE_DELTAS: dict[str, dict[str, float]] = {
    "happy":   {"valence": +0.3, "energy": +0.1},
    "sad":     {"valence": -0.3, "energy": -0.1},
    "hype":    {"energy": +0.3, "tempo": +0.2, "danceability": +0.2},
    "chill":   {"acousticness": +0.3, "energy": -0.2, "tempo": -0.1},
    "dark":    {"valence": -0.25, "mode": -0.2, "energy": +0.1},
    "focus":   {"instrumentalness": +0.3, "speechiness": -0.2, "energy": +0.1},
    "romantic":{"valence": +0.2, "acousticness": +0.2, "danceability": -0.1},
    "angry":   {"energy": +0.35, "valence": -0.2, "tempo": +0.2},
}


class Recommender:
    """Stateless recommender; session state is passed in from the caller."""

    def __init__(
        self,
        model_path: str,
        scaler_path: str,
        embeddings_path: str,
        track_ids_path: str,
    ):
        self.model: SongAutoencoder = load_model(model_path)
        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)

        self.embeddings: np.ndarray = np.load(embeddings_path)   # (N, 16)
        with open(track_ids_path, "rb") as f:
            self.track_ids: List[str] = pickle.load(f)

        self._id_to_idx = {tid: i for i, tid in enumerate(self.track_ids)}

    # ── Feature helpers ───────────────────────────────────────────────────────

    def features_to_embedding(self, feature_dict: dict) -> np.ndarray:
        """Convert raw Spotify audio feature dict → 16-dim embedding."""
        raw = np.array([[feature_dict.get(c, 0.0) for c in FEATURE_COLS]], dtype=np.float32)
        scaled = self.scaler.transform(raw)
        tensor = torch.tensor(scaled, dtype=torch.float32)
        emb = self.model.encode(tensor).numpy()
        return emb[0]  # shape (16,)

    def mood_to_embedding(self, moods: List[str]) -> np.ndarray:
        """Build a mood-space embedding by summing feature deltas → encode."""
        delta = {c: 0.0 for c in FEATURE_COLS}
        for mood in moods:
            for feat, val in MOOD_FEATURE_DELTAS.get(mood.lower(), {}).items():
                delta[feat] += val
        # Encode the delta vector (centre of scaler + deltas, then encode)
        base = np.zeros((1, len(FEATURE_COLS)), dtype=np.float32)
        for i, col in enumerate(FEATURE_COLS):
            base[0, i] = delta.get(col, 0.0)
        tensor = torch.tensor(base, dtype=torch.float32)
        emb = self.model.encode(tensor).numpy()
        return emb[0]

    # ── Core recommendation ───────────────────────────────────────────────────

    def recommend(
        self,
        history_features: List[dict],
        current_features: dict,
        moods: List[str],
        n: int,
        exclude_ids: Optional[List[str]] = None,
        session_embedding: Optional[np.ndarray] = None,
    ) -> tuple[List[str], np.ndarray]:
        """
        Returns (list_of_track_ids, updated_session_embedding).

        Parameters
        ----------
        history_features   List of audio-feature dicts for recent tracks.
        current_features   Audio-feature dict for the currently playing track.
        moods              List of mood strings chosen by the user.
        n                  Number of recommendations to return.
        exclude_ids        Track IDs to never recommend (played + already shown).
        session_embedding  Pass existing embedding to continue a session.
        """
        exclude = set(exclude_ids or [])

        # Build sub-embeddings
        if history_features:
            history_embs = np.stack([self.features_to_embedding(f) for f in history_features])
            long_term_emb = history_embs.mean(axis=0)
        else:
            long_term_emb = np.zeros(16, dtype=np.float32)

        current_emb = self.features_to_embedding(current_features)
        mood_emb = self.mood_to_embedding(moods) if moods else np.zeros(16, dtype=np.float32)

        if session_embedding is not None:
            final_emb = session_embedding
        else:
            final_emb = (
                0.5 * long_term_emb
                + 0.3 * current_emb
                + 0.2 * mood_emb
            )

        sims = cosine_similarity(final_emb.reshape(1, -1), self.embeddings)[0]

        # Zero out excluded tracks
        for tid in exclude:
            idx = self._id_to_idx.get(tid)
            if idx is not None:
                sims[idx] = -2.0

        top_indices = np.argsort(sims)[::-1][:n]
        recommended_ids = [self.track_ids[i] for i in top_indices]
        return recommended_ids, final_emb

    # ── Rejection adjustment ──────────────────────────────────────────────────

    def reject(
        self,
        session_embedding: np.ndarray,
        rejected_features: dict,
        exclude_ids: List[str],
        n: int = 1,
    ) -> tuple[List[str], np.ndarray]:
        """
        Adjust session embedding away from rejected song; return 1 replacement.
        """
        rejected_emb = self.features_to_embedding(rejected_features)
        new_emb = session_embedding - 0.1 * rejected_emb

        sims = cosine_similarity(new_emb.reshape(1, -1), self.embeddings)[0]
        for tid in exclude_ids:
            idx = self._id_to_idx.get(tid)
            if idx is not None:
                sims[idx] = -2.0

        top_indices = np.argsort(sims)[::-1][:n]
        replacement_ids = [self.track_ids[i] for i in top_indices]
        return replacement_ids, new_emb
