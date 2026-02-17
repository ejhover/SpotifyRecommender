"""
PyTorch Autoencoder for song embedding generation.
Encoder output (16-dim) is used as the song embedding.
"""

import torch
import torch.nn as nn


class SongAutoencoder(nn.Module):
    def __init__(self, input_dim: int = 11, embedding_dim: int = 16):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, embedding_dim),
        )

        self.decoder = nn.Sequential(
            nn.Linear(embedding_dim, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
        )

    def forward(self, x: torch.Tensor):
        embedding = self.encoder(x)
        reconstruction = self.decoder(embedding)
        return reconstruction, embedding

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Return embedding only (used at inference time)."""
        with torch.no_grad():
            return self.encoder(x)


def load_model(weights_path: str, input_dim: int = 11, embedding_dim: int = 16) -> SongAutoencoder:
    """Load trained model weights from disk."""
    model = SongAutoencoder(input_dim=input_dim, embedding_dim=embedding_dim)
    state = torch.load(weights_path, map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    return model
