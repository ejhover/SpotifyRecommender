"""
training/train_model.py

Trains the SongAutoencoder on the dataset built by build_dataset.py.
Saves model weights, scaler, embeddings, and track IDs to ../backend/.

Usage:
    python train_model.py [--csv dataset.csv] [--epochs 100]
"""

import sys
import pickle
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler

# Allow importing model.py from backend/
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from model import SongAutoencoder

FEATURE_COLS = [
    "danceability", "energy", "key", "loudness", "mode",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo",
]

BACKEND_DIR = Path(__file__).parent.parent / "backend"


def train(csv_path: str, epochs: int, batch_size: int, lr: float):
    df = pd.read_csv(csv_path).dropna(subset=FEATURE_COLS)
    print(f"Loaded {len(df)} tracks from {csv_path}")

    X_raw = df[FEATURE_COLS].values.astype(np.float32)
    track_ids = df["id"].tolist()

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw).astype(np.float32)

    # Save scaler
    with open(BACKEND_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    print("Saved scaler.pkl")

    # Save track IDs
    with open(BACKEND_DIR / "track_ids.pkl", "wb") as f:
        pickle.dump(track_ids, f)
    print("Saved track_ids.pkl")

    # Prepare DataLoader
    tensor = torch.tensor(X_scaled)
    dataset = TensorDataset(tensor, tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Build + train model
    model = SongAutoencoder(input_dim=len(FEATURE_COLS), embedding_dim=16)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        for x_batch, y_batch in loader:
            optimizer.zero_grad()
            reconstruction, _ = model(x_batch)
            loss = criterion(reconstruction, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(x_batch)

        if epoch % 10 == 0 or epoch == 1:
            avg = total_loss / len(dataset)
            print(f"Epoch {epoch:>4}/{epochs}  loss={avg:.6f}")

    # Save weights
    torch.save(model.state_dict(), BACKEND_DIR / "model_weights.pt")
    print("Saved model_weights.pt")

    # Precompute + save all embeddings
    model.eval()
    with torch.no_grad():
        all_embs = model.encode(torch.tensor(X_scaled)).numpy()
    np.save(BACKEND_DIR / "embeddings.npy", all_embs)
    print(f"Saved embeddings.npy  shape={all_embs.shape}")

    print("\n✅ Training complete. Backend artifacts saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv",        default="dataset.csv")
    parser.add_argument("--epochs",     type=int,   default=100)
    parser.add_argument("--batch-size", type=int,   default=256)
    parser.add_argument("--lr",         type=float, default=1e-3)
    args = parser.parse_args()
    train(args.csv, args.epochs, args.batch_size, args.lr)
