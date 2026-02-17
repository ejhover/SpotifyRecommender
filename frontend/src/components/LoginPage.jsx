import React from 'react'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  return (
    <div className={styles.page}>
      <div className={styles.glow} />
      <div className={styles.card + ' fade-up'}>
        <div className={styles.logo}>
          <SpotifyIcon />
        </div>
        <h1 className={styles.title}>moodify</h1>
        <p className={styles.sub}>
          AI-powered music recommendations<br />tuned to how you actually feel.
        </p>
        <a href="/api/login" className={styles.btn}>
          <SpotifyIcon size={20} />
          Connect with Spotify
        </a>
        <p className={styles.hint}>
          Your listening data stays private and is never stored.
        </p>
      </div>
    </div>
  )
}

function SpotifyIcon({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.492 17.315a.748.748 0 01-1.03.249c-2.818-1.723-6.365-2.113-10.542-1.157a.749.749 0 01-.356-1.454c4.573-1.045 8.495-.595 11.678 1.338a.748.748 0 01.25 1.024zm1.466-3.26a.936.936 0 01-1.287.308c-3.226-1.983-8.143-2.558-11.958-1.399a.937.937 0 01-.543-1.79c4.358-1.322 9.776-.682 13.48 1.594a.936.936 0 01.308 1.287zm.126-3.396C15.655 8.357 9.876 8.17 6.31 9.242a1.124 1.124 0 01-.651-2.148C10.024 5.878 16.44 6.096 20.58 8.475a1.123 1.123 0 01-1.497 1.184z"/>
    </svg>
  )
}
