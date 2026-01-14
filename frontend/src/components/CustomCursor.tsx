import { useState, useEffect } from 'react'

function CustomCursor() {
  const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 })
  const [isVisible, setIsVisible] = useState(false)
  const [trailPositions, setTrailPositions] = useState<Array<{ x: number; y: number }>>([])
  const [isHovering, setIsHovering] = useState(false)

  // Check if device supports hover (desktop)
  const isTouchDevice = typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)

  useEffect(() => {
    if (isTouchDevice) return

    const handleMouseMove = (e: MouseEvent) => {
      setCursorPosition({ x: e.clientX, y: e.clientY })
      if (!isVisible) setIsVisible(true)

      const target = e.target as HTMLElement
      const isClickable = target.tagName === 'A' ||
                         target.tagName === 'BUTTON' ||
                         !!target.closest('a') ||
                         !!target.closest('button') ||
                         window.getComputedStyle(target).cursor === 'pointer'
      setIsHovering(isClickable)
    }

    const handleMouseLeave = () => {
      setIsVisible(false)
    }

    window.addEventListener('mousemove', handleMouseMove)
    document.body.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      document.body.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [isVisible, isTouchDevice])

  useEffect(() => {
    if (isTouchDevice) return

    const trailLength = 35
    const speeds = Array.from({ length: trailLength }, (_, i) => 0.92 - (i * 0.022))

    if (trailPositions.length === 0) {
      setTrailPositions(Array(trailLength).fill({ x: cursorPosition.x, y: cursorPosition.y }))
      return
    }

    let animationFrameId: number
    const animate = () => {
      setTrailPositions(prev => {
        const newPositions = [...prev]

        newPositions[0] = {
          x: newPositions[0].x + (cursorPosition.x - newPositions[0].x) * speeds[0],
          y: newPositions[0].y + (cursorPosition.y - newPositions[0].y) * speeds[0]
        }

        for (let i = 1; i < trailLength; i++) {
          newPositions[i] = {
            x: newPositions[i].x + (newPositions[i - 1].x - newPositions[i].x) * speeds[i],
            y: newPositions[i].y + (newPositions[i - 1].y - newPositions[i].y) * speeds[i]
          }
        }

        return newPositions
      })

      animationFrameId = requestAnimationFrame(animate)
    }

    animationFrameId = requestAnimationFrame(animate)

    return () => cancelAnimationFrame(animationFrameId)
  }, [cursorPosition, trailPositions.length, isTouchDevice])

  if (isTouchDevice) return null

  return (
    <>
      {trailPositions.map((pos, index) => {
        const distance = Math.sqrt(
          Math.pow(pos.x - cursorPosition.x, 2) + Math.pow(pos.y - cursorPosition.y, 2)
        )
        const maxDistance = 200
        const distanceFactor = Math.max(0, 1 - (distance / maxDistance))
        const baseOpacity = (1 - (index / trailPositions.length)) * 2.5
        const size = 40 - (index * 0.8)

        return (
          <div
            key={index}
            className={`spotlight-trail ${isHovering ? 'hovering' : ''}`}
            style={{
              position: 'fixed',
              left: `${pos.x}px`,
              top: `${pos.y}px`,
              width: `${size}px`,
              height: `${size}px`,
              opacity: isVisible ? baseOpacity * distanceFactor : 0,
              pointerEvents: 'none',
              transform: 'translate(-50%, -50%)',
              zIndex: 9999,
              transition: 'opacity 0.3s ease',
            }}
          />
        )
      })}
      <div
        className={`spotlight ${isHovering ? 'hovering' : ''}`}
        style={{
          position: 'fixed',
          left: `${cursorPosition.x}px`,
          top: `${cursorPosition.y}px`,
          opacity: isVisible ? 1 : 0,
          pointerEvents: 'none',
          transform: 'translate(-50%, -50%)',
          zIndex: 10000,
        }}
      />
      <style>{`
        .spotlight {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 30%, rgba(180, 220, 255, 1) 40%, rgba(100, 200, 255, 1) 50%, rgba(100, 200, 255, 0.3) 70%, rgba(100, 200, 255, 0.1) 85%, transparent 100%);
          transition: width 0.15s ease, height 0.15s ease, background 0.15s ease;
        }

        .spotlight.hovering {
          width: 40px;
          height: 40px;
          background: radial-gradient(circle, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 30%, rgba(100, 220, 200, 1) 40%, rgba(50, 200, 180, 1) 50%, rgba(50, 200, 180, 0.3) 70%, rgba(50, 200, 180, 0.1) 85%, transparent 100%);
        }

        [data-theme='dark'] .spotlight {
          background: radial-gradient(circle, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 30%, rgba(220, 220, 220, 1) 40%, rgba(200, 200, 200, 1) 50%, rgba(200, 200, 200, 0.3) 70%, rgba(200, 200, 200, 0.1) 85%, transparent 100%);
        }

        [data-theme='dark'] .spotlight.hovering {
          background: radial-gradient(circle, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 30%, rgba(230, 230, 230, 1) 40%, rgba(210, 210, 210, 1) 50%, rgba(210, 210, 210, 0.3) 70%, rgba(210, 210, 210, 0.1) 85%, transparent 100%);
        }

        .spotlight-trail {
          border-radius: 50%;
          background: radial-gradient(circle, rgba(80, 190, 255, 0.28) 0%, rgba(80, 190, 255, 0.14) 25%, rgba(80, 190, 255, 0.04) 45%, transparent 65%);
        }

        .spotlight-trail.hovering {
          background: radial-gradient(circle, rgba(50, 200, 180, 0.28) 0%, rgba(50, 200, 180, 0.14) 25%, rgba(50, 200, 180, 0.04) 45%, transparent 65%);
        }

        [data-theme='dark'] .spotlight-trail {
          background: radial-gradient(circle, rgba(190, 190, 190, 0.20) 0%, rgba(190, 190, 190, 0.10) 25%, rgba(190, 190, 190, 0.03) 45%, transparent 65%);
        }

        [data-theme='dark'] .spotlight-trail.hovering {
          background: radial-gradient(circle, rgba(230, 230, 230, 0.20) 0%, rgba(230, 230, 230, 0.10) 25%, rgba(230, 230, 230, 0.03) 45%, transparent 65%);
        }
      `}</style>
    </>
  )
}

export default CustomCursor
