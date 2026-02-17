import React from 'react'
import styles from './MoodSelector.module.css'

const MOODS = [
  { id: 'happy',    label: 'Happy',    emoji: '☀️' },
  { id: 'sad',      label: 'Sad',      emoji: '🌧' },
  { id: 'hype',     label: 'Hype',     emoji: '⚡' },
  { id: 'chill',    label: 'Chill',    emoji: '🌊' },
  { id: 'dark',     label: 'Dark',     emoji: '🌑' },
  { id: 'focus',    label: 'Focus',    emoji: '🎯' },
  { id: 'romantic', label: 'Romantic', emoji: '✨' },
  { id: 'angry',    label: 'Angry',    emoji: '🔥' },
]

export default function MoodSelector({ selected, onChange }) {
  function toggle(id) {
    if (selected.includes(id)) {
      onChange(selected.filter((m) => m !== id))
    } else {
      onChange([...selected, id])
    }
  }

  return (
    <div className={styles.wrapper}>
      <h2 className={styles.heading}>How are you feeling?</h2>
      <p className={styles.sub}>Pick as many as you want.</p>
      <div className={styles.grid}>
        {MOODS.map(({ id, label, emoji }) => (
          <button
            key={id}
            className={styles.tag + (selected.includes(id) ? ' ' + styles.active : '')}
            onClick={() => toggle(id)}
            type="button"
            aria-pressed={selected.includes(id)}
          >
            <span className={styles.emoji}>{emoji}</span>
            <span className={styles.label}>{label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
