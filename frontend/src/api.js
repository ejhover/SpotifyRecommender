const BASE = '/api'

export async function api(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json()
}

export const getCurrentSong = (sessionId) =>
  api(`/current-song?session_id=${sessionId}`)

export const getRecommendations = (sessionId, currentTrackId, moods, n) =>
  api('/recommend', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, current_track_id: currentTrackId, moods, n }),
  })

export const rejectTrack = (sessionId, rejectedTrackId, currentRecs, recentlyPlayed) =>
  api('/reject', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      rejected_track_id: rejectedTrackId,
      current_recommendations: currentRecs,
      recently_played_ids: recentlyPlayed,
    }),
  })

export const addToQueue = (sessionId, trackIds) =>
  api('/add-to-queue', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, track_ids: trackIds }),
  })
