import React from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import styles from './SongRow.module.css'

export default function SongRow({ song, onReject, isReplacing }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: song.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={styles.row + (isReplacing ? ' ' + styles.loading : '') + ' slide-in'}
    >
      {/* Drag handle */}
      <button
        className={styles.handle}
        {...attributes}
        {...listeners}
        aria-label="Drag to reorder"
        type="button"
      >
        <DragIcon />
      </button>

      {/* Album art */}
      {song.album_art ? (
        <img src={song.album_art} alt={song.name} className={styles.art} />
      ) : (
        <div className={styles.artFallback} />
      )}

      {/* Song info */}
      <div className={styles.info}>
        {isReplacing ? (
          <span className={styles.replacing}>Finding replacement…</span>
        ) : (
          <>
            <p className={styles.name}>{song.name}</p>
            <p className={styles.artist}>{song.artists.join(', ')}</p>
          </>
        )}
      </div>

      {/* Reject */}
      <button
        className={styles.reject}
        onClick={() => onReject(song.id)}
        disabled={isReplacing}
        aria-label={`Remove ${song.name}`}
        type="button"
      >
        <CloseIcon />
      </button>
    </div>
  )
}

function DragIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <rect x="3" y="3" width="10" height="1.5" rx="0.75"/>
      <rect x="3" y="7.25" width="10" height="1.5" rx="0.75"/>
      <rect x="3" y="11.5" width="10" height="1.5" rx="0.75"/>
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <path d="M13 1L1 13M1 1l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  )
}
