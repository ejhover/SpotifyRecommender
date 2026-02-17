import React from 'react'
import styles from './CurrentSongCard.module.css'

export default function CurrentSongCard({ song }) {
  if (!song) return null

  return (
    <div className={styles.card + ' fade-up'}>
      <div className={styles.label}>
        {song.is_playing ? (
          <span className={styles.playing}>
            <span className={styles.dot} />
            Now Playing
          </span>
        ) : (
          <span className={styles.recent}>Last Played</span>
        )}
      </div>

      <div className={styles.inner}>
        {song.album_art ? (
          <img
            src={song.album_art}
            alt={song.name}
            className={styles.art}
          />
        ) : (
          <div className={styles.artFallback}>
            <MusicIcon />
          </div>
        )}
        <div className={styles.info}>
          <p className={styles.name}>{song.name}</p>
          <p className={styles.artist}>{song.artists.join(', ')}</p>
        </div>
      </div>
    </div>
  )
}

function MusicIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" opacity="0.3">
      <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
    </svg>
  )
}
