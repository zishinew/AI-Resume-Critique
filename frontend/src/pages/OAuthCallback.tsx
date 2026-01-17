import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export default function OAuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    // Supabase automatically handles the OAuth callback and sets the session
    // We just need to wait for it and redirect
    const checkSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()

      if (session) {
        navigate('/', { replace: true })
      } else {
        // Wait a bit for Supabase to process the callback
        setTimeout(async () => {
          const { data: { session: retrySession } } = await supabase.auth.getSession()
          if (retrySession) {
            navigate('/', { replace: true })
          } else {
            navigate('/login', { replace: true })
          }
        }, 1000)
      }
    }

    checkSession()
  }, [navigate])

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        color: 'var(--text-primary)',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            border: '3px solid var(--border-color)',
            borderTop: '3px solid var(--accent-color)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px',
          }}
        />
        <p>Completing sign in...</p>
      </div>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
