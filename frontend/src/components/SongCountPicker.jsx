import React from 'react'
import styles from './SongCountPicker.module.css'

const OPTIONS = [3, 5, 7, 10]

export default function SongCountPicker({ value, onChange }) {
  return (
    <div className={styles.wrapper}>
      <h2 className={styles.heading}>How many songs?</h2>
      <div className={styles.row}>
        {OPTIONS.map((n) => (
          <button
            key={n}
            className={styles.option + (value === n ? ' ' + styles.active : '')}
            onClick={() => onChange(n)}
            type="button"
          >
            {n}
          </button>
        ))}
        <input
          type="number"
          className={styles.custom}
          value={!OPTIONS.includes(value) ? value : ''}
          placeholder="Custom"
          min={1}
          max={25}
          onChange={(e) => {
            const v = parseInt(e.target.value, 10)
            if (!isNaN(v) && v > 0 && v <= 25) onChange(v)
          }}
        />
      </div>
    </div>
  )
}
