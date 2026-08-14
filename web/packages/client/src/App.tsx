/**
 * The shell.
 *
 * The front page is public. You can read what people have shared and search
 * across it without an account, because an account is access to this host and
 * not permission to look — and a system whose front door demanded a login
 * before it would show you anything has already decided it is the authority.
 *
 * Signing in adds exactly one thing: your own projects, and the ability to
 * open one.
 */

import { useCallback, useEffect, useState } from 'react'
import { Link, NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'

import { api, type Me } from './api'
import { Home } from './pages/Home'
import { MyProjects } from './pages/MyProjects'
import { ProjectPage } from './pages/Project'
import { SearchPage } from './pages/Search'
import { SignIn } from './pages/SignIn'

export function App() {
  const [me, setMe] = useState<Me | null>(null)
  const navigate = useNavigate()

  const refresh = useCallback(async () => {
    setMe(await api.me().catch(() => ({ signedIn: false, registrationOpen: false })))
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  if (!me) return <main />

  const signOut = async () => {
    await api.signOut()
    await refresh()
    navigate('/')
  }

  return (
    <main>
      <header className="bar">
        <Link to="/" className="mark">
          GRA
        </Link>
        <nav>
          {me.signedIn && (
            <NavLink to="/projects" className={({ isActive }) => (isActive ? 'on' : '')}>
              Your projects
            </NavLink>
          )}
          <NavLink to="/search" className={({ isActive }) => (isActive ? 'on' : '')}>
            Search
          </NavLink>
        </nav>
        <div className="who">
          {me.signedIn ? (
            <>
              <span>
                signing as <strong>{me.name}</strong>
              </span>
              <button className="quiet" onClick={signOut}>
                sign out
              </button>
            </>
          ) : (
            <Link to="/sign-in">sign in</Link>
          )}
        </div>
      </header>

      <Routes>
        <Route path="/" element={<Home me={me} />} />
        <Route path="/search" element={<SearchPage me={me} />} />
        <Route path="/p/:slug" element={<ProjectPage me={me} />} />
        <Route path="/sign-in" element={<SignIn me={me} onSignedIn={refresh} />} />
        <Route
          path="/projects"
          element={me.signedIn ? <MyProjects me={me} /> : <Navigate to="/sign-in" replace />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <footer>
        A host for projects, not their authority. The record underneath is plain files: you can
        hold a copy, continue it under any implementation, and verify it with no account here.
        Nothing on this server is counted, scored or ranked.
      </footer>
    </main>
  )
}
