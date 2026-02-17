import React, { useState, useEffect, useCallback } from 'react'
import LoginPage from './components/LoginPage'
import CurrentSongCard from './components/CurrentSongCard'
import MoodSelector from './components/MoodSelector'
import SongCountPicker from './components/SongCountPicker'
import RecommendationsList from './components/RecommendationsList'
import {
  getCurrentSong,
  getRecommendations,
  rejectTrack,
  addToQueue,
} from './api'
import styles from './App.module.css'

// ── Helpers ──────────────────────────────────────────────────────────────────
function getSessionId() {
  const params = new URLSearchParams(window.location.search)
  const id = params.get('session')
  if (id) {
    sessionStorage.setItem('session_id', id)
    // Clean the URL
    window.history.replaceState({}, '', '/')
    return id
  }
  return sessionStorage.getItem('session_id')
}

export default function App() {
  const [sessionId] = useState(getSessionId)
  const [currentSong, setCurrentSong] = useState(null)
  const [moods, setMoods] = useState([])
  const [songCount, setSongCount] = useState(5)
  const [recommendations, setRecommendations] = useState([])
  const [recentlyPlayedIds, setRecentlyPlayedIds] = useState([])
  const [replacingIds, setReplacingIds] = useState(new Set())
  const [isLoadingSong, setIsLoadingSong] = useState(false)
  const [isLoadingRecs, setIsLoadingRecs] = useState(false)
  const [isAddingToQueue, setIsAddingToQueue] = useState(false)
  const [addedToQueue, setAddedToQueue] = useState(false)
  const [error, setError] = useState(null)

  // ── Fetch current song on mount ───────────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return
    setIsLoadingSong(true)
    getCurrentSong(sessionId)
      .then(setCurrentSong)
      .catch((e) => setError('Could not fetch current song: ' + e.message))
      .finally(() => setIsLoadingSong(false))
  }, [sessionId])

  // ── Generate recommendations ──────────────────────────────────────────────
  const handleGenerate = useCallback(async () => {
    if (!currentSong || !sessionId) return
    setError(null)
    setIsLoadingRecs(true)
    setAddedToQueue(false)
    setRecommendations([])
    try {
      const data = await getRecommendations(sessionId, currentSong.id, moods, songCount)
      setRecommendations(data.recommendations)
      setRecentlyPlayedIds(data.recently_played_ids ?? [])
    } catch (e) {
      setError('Could not get recommendations: ' + e.message)
    } finally {
      setIsLoadingRecs(false)
    }
  }, [sessionId, currentSong, moods, songCount])

  // ── Reject a song ─────────────────────────────────────────────────────────
  const handleReject = useCallback(async (trackId) => {
    setReplacingIds((prev) => new Set([...prev, trackId]))
    const currentIds = recommendations.map((r) => r.id)
    try {
      const data = await rejectTrack(sessionId, trackId, currentIds, recentlyPlayedIds)
      setRecommendations((prev) =>
        prev.map((r) => (r.id === trackId ? data.replacement : r))
      )
    } catch (e) {
      setError('Could not replace track: ' + e.message)
    } finally {
      setReplacingIds((prev) => {
        const next = new Set(prev)
        next.delete(trackId)
        return next
      })
    }
  }, [sessionId, recommendations, recentlyPlayedIds])

  // ── Add to queue ──────────────────────────────────────────────────────────
  const handleAddToQueue = useCallback(async () => {
    setIsAddingToQueue(true)
    try {
      await addToQueue(sessionId, recommendations.map((r) => r.id))
      setAddedToQueue(true)
    } catch (e) {
      setError('Could not add to queue: ' + e.message)
    } finally {
      setIsAddingToQueue(false)
    }
  }, [sessionId, recommendations])

  // ── Reorder ───────────────────────────────────────────────────────────────
  const handleReorder = useCallback((newList) => {
    setRecommendations(newList)
    setAddedToQueue(false)
  }, [])

  // ── Not logged in ─────────────────────────────────────────────────────────
  if (!sessionId) return <LoginPage />

  return (
    <div className={styles.app}>
      <div className={styles.bg} />

      <div className={styles.container}>
        {/* Header */}
        <header className={styles.header + ' fade-up'}>
          <h1 className={styles.logo}>moodify</h1>
          <p className={styles.tagline}>powered by your taste</p>
        </header>

        {/* Error banner */}
        {error && (
          <div className={styles.error + ' fade-in'}>
            <span>{error}</span>
            <button onClick={() => setError(null)} className={styles.errorClose}>✕</button>
          </div>
        )}

        {/* Current song */}
        {isLoadingSong ? (
          <div className={styles.songSkeleton + ' fade-in'}>
            <div className={styles.skeletonImg} />
            <div className={styles.skeletonLines}>
              <div className={styles.skeletonLine} style={{ width: '60%' }} />
              <div className={styles.skeletonLine} style={{ width: '40%' }} />
            </div>
          </div>
        ) : (
          <CurrentSongCard song={currentSong} />
        )}

        {/* Controls (only shown when we have a song) */}
        {currentSong && (
          <>
            <MoodSelector selected={moods} onChange={setMoods} />
            <SongCountPicker value={songCount} onChange={setSongCount} />

            <button
              className={styles.generateBtn + (isLoadingRecs ? ' ' + styles.loading : '')}
              onClick={handleGenerate}
              disabled={isLoadingRecs}
              type="button"
            >
              {isLoadingRecs ? (
                <>
                  <span className={styles.spinner} />
                  Finding songs…
                </>
              ) : (
                <>
                  <SparkleIcon />
                  {recommendations.length > 0 ? 'Regenerate' : 'Find My Songs'}
                </>
              )}
            </button>
          </>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <RecommendationsList
            songs={recommendations}
            onReject={handleReject}
            onReorder={handleReorder}
            onAddToQueue={handleAddToQueue}
            replacingIds={replacingIds}
            isAddingToQueue={isAddingToQueue}
            addedToQueue={addedToQueue}
          />
        )}
      </div>
    </div>
  )
}

function SparkleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L9.5 9.5 2 12l7.5 2.5L12 22l2.5-7.5L22 12l-7.5-2.5z"/>
    </svg>
  )
}
