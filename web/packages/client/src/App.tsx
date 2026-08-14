/**
 * The shell, and the four ways in.
 *
 * Nothing in this navigation marks a default, a home or a principal view, and
 * the record list is never ordered by anything derived from the work. The
 * temptation to rank is strongest on a screen, and this is the screen.
 */

import { useCallback, useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'

import { api, type Me } from './api'
import { Community } from './pages/Community'
import { MyRecords } from './pages/MyRecords'
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

  if (!me.signedIn) {
    return (
      <main>
        <Routes>
          <Route path="/sign-in" element={<SignIn onSignedIn={refresh} />} />
          <Route path="*" element={<Navigate to="/sign-in" replace />} />
        </Routes>
      </main>
    )
  }

  const signOut = async () => {
    await api.signOut()
    await refresh()
    navigate('/sign-in')
  }

  return (
    <main>
      <header className="bar">
        <nav>
          <NavLink to="/records" className={({ isActive }) => (isActive ? 'on' : '')}>
            Your records
          </NavLink>
          <NavLink to="/community" className={({ isActive }) => (isActive ? 'on' : '')}>
            Shared here
          </NavLink>
          <NavLink to="/search" className={({ isActive }) => (isActive ? 'on' : '')}>
            Search
          </NavLink>
        </nav>
        <div className="who">
          <span>
            signing as <strong>{me.name}</strong>
          </span>
          <button className="quiet" onClick={signOut}>
            sign out
          </button>
        </div>
      </header>

      <Routes>
        <Route path="/records" element={<MyRecords me={me} />} />
        <Route path="/community" element={<Community me={me} />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/r/:slug" element={<ProjectPage me={me} />} />
        <Route path="*" element={<Navigate to="/records" replace />} />
      </Routes>

      <footer>
        A host for records, not their authority. The record is plain files: you can hold a copy,
        continue it under any implementation, and verify it with no account here. Nothing on this
        server is counted, scored or ranked.
      </footer>
    </main>
  )
}
