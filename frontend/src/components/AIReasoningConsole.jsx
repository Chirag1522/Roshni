import { useEffect, useState } from 'react'

export default function AIReasoningConsole({ reasoning, isVisible = true }) {
  const [displayText, setDisplayText] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    if (!reasoning || !isVisible) {
      setDisplayText('')
      return
    }

    setIsTyping(true)
    setDisplayText('')

    const text = typeof reasoning === 'string' ? reasoning : JSON.stringify(reasoning, null, 2)
    let index = 0

    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayText(text.substring(0, index + 1))
        index++
      } else {
        setIsTyping(false)
        clearInterval(interval)
      }
    }, 15) // Typing speed

    return () => clearInterval(interval)
  }, [reasoning, isVisible])

  if (!isVisible || !reasoning) return null

  return (
    <div className="ai-reasoning-console">
      <div className="console-header">
        <span style={{ color: '#00ff00' }}>🤖 AI Thinking</span>
        <span style={{ color: '#666', fontSize: '0.85rem' }}>
          {isTyping ? '● Analyzing...' : '● Complete'}
        </span>
      </div>
      <div className="console-body">
        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
          {displayText}
          {isTyping && <span style={{ animation: 'blink 1s infinite' }}>▋</span>}
        </pre>
      </div>
    </div>
  )
}
