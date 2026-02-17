import React from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import SongRow from './SongRow'
import styles from './RecommendationsList.module.css'

export default function RecommendationsList({
  songs,
  onReject,
  onReorder,
  onAddToQueue,
  replacingIds,
  isAddingToQueue,
  addedToQueue,
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  function handleDragEnd(event) {
    const { active, over } = event
    if (active.id !== over?.id) {
      const oldIndex = songs.findIndex((s) => s.id === active.id)
      const newIndex = songs.findIndex((s) => s.id === over.id)
      onReorder(arrayMove(songs, oldIndex, newIndex))
    }
  }

  if (songs.length === 0) return null

  return (
    <div className={styles.wrapper + ' fade-in'}>
      <div className={styles.header}>
        <h2 className={styles.heading}>Your Queue</h2>
        <span className={styles.count}>{songs.length} songs</span>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={songs.map((s) => s.id)} strategy={verticalListSortingStrategy}>
          <div className={styles.list}>
            {songs.map((song) => (
              <SongRow
                key={song.id}
                song={song}
                onReject={onReject}
                isReplacing={replacingIds.has(song.id)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      <div className={styles.actions}>
        {addedToQueue ? (
          <div className={styles.success}>
            <CheckIcon />
            Added to Spotify queue!
          </div>
        ) : (
          <button
            className={styles.queueBtn}
            onClick={onAddToQueue}
            disabled={isAddingToQueue}
            type="button"
          >
            {isAddingToQueue ? (
              <span className={styles.spinner} />
            ) : (
              <QueueIcon />
            )}
            {isAddingToQueue ? 'Adding…' : 'Add to Queue'}
          </button>
        )}
      </div>
    </div>
  )
}

function QueueIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z"/>
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
    </svg>
  )
}
