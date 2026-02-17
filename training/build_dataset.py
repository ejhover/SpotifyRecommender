import os
import time
import random
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in your .env file")

FEATURE_COLS = [
    "danceability", "energy", "key", "loudness", "mode",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo",
]

TARGET_TOTAL = 5000

# Seed artists — one or two well-known names per genre so searches are reliable
SEED_ARTISTS = [
    # Pop
    "Taylor Swift", "Ed Sheeran", "Ariana Grande", "Dua Lipa", "Harry Styles",
    # Hip-hop / Rap
    "Drake", "Kendrick Lamar", "J. Cole", "Travis Scott", "Nicki Minaj",
    # R&B / Soul
    "Frank Ocean", "SZA", "The Weeknd", "Beyonce", "Usher",
    # Rock
    "Radiohead", "Arctic Monkeys", "Foo Fighters", "Red Hot Chili Peppers", "Nirvana",
    # Indie
    "Tame Impala", "Vampire Weekend", "Bon Iver", "Sufjan Stevens", "Phoebe Bridgers",
    # Electronic / Dance
    "Daft Punk", "Calvin Harris", "Flume", "Aphex Twin", "Four Tet",
    # Metal
    "Metallica", "Tool", "Black Sabbath", "Slipknot", "Mastodon",
    # Country
    "Johnny Cash", "Dolly Parton", "Luke Combs", "Kacey Musgraves", "Chris Stapleton",
    # Jazz
    "Miles Davis", "John Coltrane", "Herbie Hancock", "Thelonious Monk", "Bill Evans",
    # Classical / Instrumental
    "Hans Zimmer", "Ludovico Einaudi", "Yiruma", "Max Richter", "Johann Sebastian Bach",
    # Latin
    "Bad Bunny", "J Balvin", "Shakira", "Ozuna", "Maluma",
    # Reggae
    "Bob Marley", "Damian Marley", "Chronixx", "Protoje", "Toots and the Maytals",
    # Blues
    "B.B. King", "Muddy Waters", "Robert Johnson", "Gary Clark Jr.", "John Mayer",
    # Folk / Acoustic
    "Fleet Foxes", "Iron and Wine", "Nick Drake", "Simon and Garfunkel", "James Taylor",
    # Punk
    "The Clash", "Ramones", "Green Day", "Bad Brains", "Descendents",
    # Trap / Modern Hip-hop
    "Future", "Young Thug", "Gunna", "Lil Baby", "21 Savage",
    # Alternative
    "Billie Eilish", "Lorde", "Lana Del Rey", "Halsey", "Twenty One Pilots",
]


def search_artist_id(sp: spotipy.Spotify, name: str) -> str | None:
    try:
        res = sp.search(q=name, type="artist", limit=1, market="US")
        items = res.get("artists", {}).get("items", [])
        return items[0]["id"] if items else None
    except Exception as e:
        print(f"  ⚠️  Artist search failed for {name!r}: {e}")
        return None


def get_top_tracks(sp: spotipy.Spotify, artist_id: str) -> list[str]:
    try:
        res = sp.artist_top_tracks(artist_id, country="US")
        return [t["id"] for t in res.get("tracks", []) if t.get("id")]
    except Exception:
        return []


def get_related_artist_ids(sp: spotipy.Spotify, artist_id: str) -> list[str]:
    try:
        res = sp.artist_related_artists(artist_id)
        return [a["id"] for a in res.get("artists", [])[:6]]
    except Exception:
        return []


def get_artist_albums_tracks(sp: spotipy.Spotify, artist_id: str, max_tracks: int = 30) -> list[str]:
    """Grab tracks from up to 2 albums for more variety beyond top-10."""
    track_ids = []
    try:
        albums = sp.artist_albums(artist_id, album_type="album", limit=2, country="US")
        for album in albums.get("items", [])[:2]:
            tracks = sp.album_tracks(album["id"], limit=20)
            for t in tracks.get("items", []):
                if t and t.get("id"):
                    track_ids.append(t["id"])
            if len(track_ids) >= max_tracks:
                break
    except Exception:
        pass
    return track_ids[:max_tracks]


def fetch_audio_features(sp: spotipy.Spotify, ids: list[str]) -> list[dict]:
    records = []
    for i in range(0, len(ids), 100):
        batch = ids[i:i + 100]
        try:
            features = sp.audio_features(batch)
            for f in features:
                if f and all(f.get(c) is not None for c in FEATURE_COLS):
                    records.append({col: f[col] for col in ["id"] + FEATURE_COLS})
        except Exception as e:
            print(f"  ⚠️  Audio features batch failed: {e}")
        time.sleep(0.15)
    return records


def main():
    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        ),
        requests_timeout=15,
    )

    all_track_ids: set[str] = set()
    visited_artist_ids: set[str] = set()
    artist_queue: list[str] = []  # artist IDs to process

    # ── Phase 1: resolve seed artist names → IDs ─────────────────────────────
    print("Resolving seed artists...")
    seeds = list(SEED_ARTISTS)
    random.shuffle(seeds)
    for name in seeds:
        aid = search_artist_id(sp, name)
        if aid and aid not in visited_artist_ids:
            artist_queue.append(aid)
        time.sleep(0.1)
    print(f"  {len(artist_queue)} seed artists found\n")

    # ── Phase 2: crawl artists → top tracks + album tracks + related ─────────
    print(f"Collecting tracks (target: {TARGET_TOTAL})...")
    while artist_queue and len(all_track_ids) < TARGET_TOTAL:
        artist_id = artist_queue.pop(0)
        if artist_id in visited_artist_ids:
            continue
        visited_artist_ids.add(artist_id)

        before = len(all_track_ids)

        # Top tracks (up to 10)
        top = get_top_tracks(sp, artist_id)
        all_track_ids.update(top)

        # Album tracks (up to 30 more)
        album_tracks = get_artist_albums_tracks(sp, artist_id)
        all_track_ids.update(album_tracks)

        added = len(all_track_ids) - before
        if added > 0:
            print(f"  artists visited={len(visited_artist_ids):3d}  "
                  f"+{added:3d} tracks  total={len(all_track_ids)}")

        # Queue related artists for expansion
        if len(all_track_ids) < TARGET_TOTAL:
            related = get_related_artist_ids(sp, artist_id)
            for rid in related:
                if rid not in visited_artist_ids:
                    artist_queue.append(rid)

        time.sleep(0.2)

    print(f"\nTotal unique track IDs: {len(all_track_ids)}")

    if not all_track_ids:
        print("\n❌ No tracks collected. Check your CLIENT_ID / CLIENT_SECRET.")
        return

    # ── Phase 3: fetch audio features ────────────────────────────────────────
    print("\nFetching audio features (may take a minute)...")
    ids_list = list(all_track_ids)
    random.shuffle(ids_list)
    records = fetch_audio_features(sp, ids_list)

    if not records:
        print("\n❌ Audio features empty. Check API permissions.")
        return

    df = pd.DataFrame(records).drop_duplicates(subset="id").dropna()
    df.to_csv("dataset.csv", index=False)
    print(f"\n✅ Saved {len(df)} tracks to dataset.csv")
    print(f"   Columns: id, {', '.join(FEATURE_COLS)}")


if __name__ == "__main__":
    main()
