# 🎵 SpotifyRecommender — Context-Aware AI Spotify Recommendations

SpotifyRecommender is a full-stack web application that generates real-time, mood-aware music recommendations using Spotify data and a PyTorch autoencoder.

It combines:

- 🎧 Your current or last played song  
- 📚 Your recent listening history  
- 😊 Your selected moods  
- ❌ Live rejection feedback  

To generate dynamic, embedding-based recommendations that can be added directly to your Spotify queue.

---

## 🚀 Overview

SpotifyRecommender is built around a **content-based recommendation system** powered by a learned embedding space.

Instead of relying on collaborative filtering or external datasets, the system:

1. Pulls Spotify audio features
2. Trains a PyTorch autoencoder
3. Uses encoder outputs as song embeddings
4. Performs cosine similarity in embedding space
5. Adjusts recommendations dynamically based on session feedback

---

## 🏗️ Architecture

```
spotify-ai/
├── backend/          # FastAPI server + ML inference
│   ├── main.py       # API routes (auth, recommend, reject, queue)
│   ├── model.py      # PyTorch autoencoder definition
│   ├── recommender.py # Embedding math + recommendation logic
│   ├── requirements.txt
│   └── .env.example
├── frontend/         # React app
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── training/         # One-time scripts
    ├── build_dataset.py  # Pull track features from Spotify
    └── train_model.py    # Train autoencoder, save artifacts
```