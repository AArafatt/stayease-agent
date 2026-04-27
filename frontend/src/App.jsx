import { useState, useRef, useEffect } from 'react'

const API_BASE = 'http://localhost:8000'

function generateId() {
  return crypto.randomUUID()
}

function PropertyCard({ property }) {
  return (
    <div style={styles.propertyCard}>
      <div style={styles.propertyHeader}>
        <h4 style={styles.propertyTitle}>{property.title}</h4>
        <span style={styles.propertyRating}>
          {property.rating?.toFixed(1)} / 5
        </span>
      </div>
      <div style={styles.propertyDetails}>
        <span style={styles.propertyTag}>{property.location}</span>
        <span style={styles.propertyTag}>{property.max_guests} guests</span>
        <span style={styles.propertyTag}>{property.bedrooms} bed</span>
      </div>
      <div style={styles.propertyPricing}>
        <span style={styles.propertyPrice}>
          ৳{property.price_per_night?.toLocaleString()}
          <small style={styles.perNight}>/night</small>
        </span>
        {property.total_price && (
          <span style={styles.totalPrice}>
            Total: ���{property.total_price?.toLocaleString()}
          </span>
        )}
      </div>
    </div>
  )
}

function BookingCard({ booking }) {
  return (
    <div style={styles.bookingCard}>
      <div style={styles.bookingIcon}>&#10003;</div>
      <h4 style={styles.bookingTitle}>Booking Confirmed!</h4>
      <p style={styles.bookingDetail}>{booking.listing_title}</p>
      <div style={styles.bookingMeta}>
        <span>{booking.check_in} to {booking.check_out}</span>
        <span>{booking.num_guests} guests</span>
      </div>
      <p style={styles.bookingTotal}>Total: ৳{booking.total_price?.toLocaleString()}</p>
    </div>
  )
}

function ChatMessage({ msg }) {
  const isUser = msg.role === 'human'

  return (
    <div style={{
      ...styles.messageRow,
      justifyContent: isUser ? 'flex-end' : 'flex-start',
    }}>
      {!isUser && (
        <div style={styles.avatar}>S</div>
      )}
      <div style={{
        ...styles.messageBubble,
        ...(isUser ? styles.userBubble : styles.aiBubble),
      }}>
        <p style={{
          ...styles.messageText,
          color: isUser ? '#ffffff' : 'var(--text)',
        }}>
          {msg.content}
        </p>

        {msg.data?.properties && (
          <div style={styles.cardsContainer}>
            {msg.data.properties.map((p, i) => (
              <PropertyCard key={i} property={p} />
            ))}
          </div>
        )}

        {msg.data?.booking && (
          <BookingCard booking={msg.data.booking} />
        )}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ ...styles.messageRow, justifyContent: 'flex-start' }}>
      <div style={styles.avatar}>S</div>
      <div style={{ ...styles.messageBubble, ...styles.aiBubble }}>
        <div style={styles.typing}>
          <span style={{ ...styles.dot, animationDelay: '0ms' }} />
          <span style={{ ...styles.dot, animationDelay: '150ms' }} />
          <span style={{ ...styles.dot, animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId] = useState(generateId)
  const [guestName] = useState('Guest')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const sendMessage = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'human', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(
        `${API_BASE}/api/chat/${conversationId}/message`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text,
            guest_name: guestName,
          }),
        }
      )

      if (!res.ok) throw new Error('Request failed')

      const data = await res.json()
      const aiMsg = {
        role: 'ai',
        content: data.reply,
        data: data.data || null,
      }
      setMessages(prev => [...prev, aiMsg])
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'ai', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>S</div>
          <div>
            <h1 style={styles.headerTitle}>StayEase</h1>
            <p style={styles.headerSub}>AI Booking Assistant</p>
          </div>
        </div>
        <div style={styles.statusBadge}>
          <span style={styles.statusDot} />
          Online
        </div>
      </div>

      {/* Messages */}
      <div style={styles.messagesArea}>
        {messages.length === 0 && (
          <div style={styles.welcome}>
            <div style={styles.welcomeIcon}>S</div>
            <h2 style={styles.welcomeTitle}>Welcome to StayEase</h2>
            <p style={styles.welcomeText}>
              I can help you find and book short-term rentals across Bangladesh.
              Try asking me something like:
            </p>
            <div style={styles.suggestions}>
              {[
                "Find me a place in Cox's Bazar for 2 guests",
                'I need a room in Sylhet for 3 nights',
                'Show me listings in Dhaka under ৳5,000/night',
              ].map((s, i) => (
                <button
                  key={i}
                  style={styles.suggestion}
                  onClick={() => {
                    setInput(s)
                    inputRef.current?.focus()
                  }}
                  onMouseEnter={e => e.target.style.borderColor = 'var(--primary)'}
                  onMouseLeave={e => e.target.style.borderColor = 'var(--border)'}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} msg={msg} />
        ))}

        {loading && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} style={styles.inputArea}>
        <div style={styles.inputWrapper}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type your message..."
            style={styles.input}
            disabled={loading}
          />
          <button
            type="submit"
            style={{
              ...styles.sendBtn,
              opacity: input.trim() && !loading ? 1 : 0.5,
            }}
            disabled={!input.trim() || loading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p style={styles.disclaimer}>
          Powered by AI. Prices in BDT.
        </p>
      </form>

      <style>{keyframes}</style>
    </div>
  )
}

const keyframes = `
  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-4px); }
  }
`

const styles = {
  container: {
    width: '100%',
    maxWidth: 520,
    height: '100%',
    maxHeight: 720,
    display: 'flex',
    flexDirection: 'column',
    background: 'var(--surface)',
    borderRadius: 16,
    boxShadow: 'var(--shadow-lg)',
    overflow: 'hidden',
    border: '1px solid var(--border)',
  },

  /* Header */
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    borderBottom: '1px solid var(--border)',
    background: 'var(--surface)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  logo: {
    width: 40,
    height: 40,
    borderRadius: 10,
    background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: 18,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: 700,
    color: 'var(--text)',
    lineHeight: 1.2,
  },
  headerSub: {
    fontSize: 12,
    color: 'var(--text-secondary)',
  },
  statusBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    color: 'var(--success)',
    fontWeight: 500,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: 'var(--success)',
  },

  /* Messages area */
  messagesArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    background: '#f8fafc',
  },

  /* Welcome */
  welcome: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    padding: '40px 20px',
    flex: 1,
  },
  welcomeIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: 24,
    marginBottom: 16,
  },
  welcomeTitle: {
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 8,
    color: 'var(--text)',
  },
  welcomeText: {
    fontSize: 14,
    color: 'var(--text-secondary)',
    lineHeight: 1.5,
    maxWidth: 340,
    marginBottom: 20,
  },
  suggestions: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    width: '100%',
    maxWidth: 360,
  },
  suggestion: {
    padding: '10px 16px',
    border: '1px solid var(--border)',
    borderRadius: 10,
    background: 'var(--surface)',
    cursor: 'pointer',
    fontSize: 13,
    color: 'var(--text)',
    textAlign: 'left',
    transition: 'border-color 0.2s',
    fontFamily: 'inherit',
  },

  /* Message bubbles */
  messageRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 8,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 8,
    background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 600,
    fontSize: 13,
    flexShrink: 0,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: '10px 14px',
    borderRadius: 14,
    lineHeight: 1.5,
  },
  userBubble: {
    background: 'var(--user-bubble)',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    background: 'var(--ai-bubble)',
    border: '1px solid var(--border)',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 14,
    margin: 0,
    whiteSpace: 'pre-wrap',
  },

  /* Property cards */
  cardsContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    marginTop: 10,
  },
  propertyCard: {
    background: '#f8fafc',
    border: '1px solid var(--border)',
    borderRadius: 10,
    padding: 12,
  },
  propertyHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  propertyTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text)',
  },
  propertyRating: {
    fontSize: 12,
    color: '#d97706',
    fontWeight: 600,
  },
  propertyDetails: {
    display: 'flex',
    gap: 6,
    marginBottom: 8,
    flexWrap: 'wrap',
  },
  propertyTag: {
    fontSize: 11,
    padding: '2px 8px',
    background: 'var(--primary-light)',
    color: 'var(--primary)',
    borderRadius: 6,
    fontWeight: 500,
  },
  propertyPricing: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  propertyPrice: {
    fontSize: 15,
    fontWeight: 700,
    color: 'var(--text)',
  },
  perNight: {
    fontSize: 11,
    color: 'var(--text-secondary)',
    fontWeight: 400,
  },
  totalPrice: {
    fontSize: 12,
    color: 'var(--text-secondary)',
    fontWeight: 500,
  },

  /* Booking card */
  bookingCard: {
    background: '#ecfdf5',
    border: '1px solid #a7f3d0',
    borderRadius: 10,
    padding: 16,
    marginTop: 10,
    textAlign: 'center',
  },
  bookingIcon: {
    width: 36,
    height: 36,
    borderRadius: '50%',
    background: 'var(--success)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 8px',
    fontSize: 18,
    fontWeight: 700,
  },
  bookingTitle: {
    fontSize: 15,
    fontWeight: 700,
    color: 'var(--success)',
    marginBottom: 4,
  },
  bookingDetail: {
    fontSize: 14,
    fontWeight: 600,
    color: 'var(--text)',
    marginBottom: 6,
  },
  bookingMeta: {
    display: 'flex',
    justifyContent: 'center',
    gap: 12,
    fontSize: 12,
    color: 'var(--text-secondary)',
    marginBottom: 6,
  },
  bookingTotal: {
    fontSize: 16,
    fontWeight: 700,
    color: 'var(--text)',
  },

  /* Typing indicator */
  typing: {
    display: 'flex',
    gap: 4,
    padding: '4px 0',
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: '50%',
    background: 'var(--text-secondary)',
    animation: 'bounce 1s infinite',
    display: 'inline-block',
  },

  /* Input area */
  inputArea: {
    padding: '12px 16px 16px',
    borderTop: '1px solid var(--border)',
    background: 'var(--surface)',
  },
  inputWrapper: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    borderRadius: 12,
    border: '1px solid var(--border)',
    fontSize: 14,
    outline: 'none',
    background: '#f8fafc',
    color: 'var(--text)',
    fontFamily: 'inherit',
    transition: 'border-color 0.2s',
  },
  sendBtn: {
    width: 42,
    height: 42,
    borderRadius: 12,
    border: 'none',
    background: 'var(--primary)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    transition: 'opacity 0.2s, background 0.2s',
  },
  disclaimer: {
    fontSize: 11,
    color: 'var(--text-secondary)',
    textAlign: 'center',
    marginTop: 8,
  },
}
