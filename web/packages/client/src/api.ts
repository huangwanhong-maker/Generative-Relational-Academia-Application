/**
 * The one place this client talks to the server.
 *
 * Kept in one file on purpose: the API is the durable artifact here and this
 * client is the disposable one, so it should be obvious at a glance exactly
 * what the browser depends on — and short enough that someone writing a second
 * client can read it in a minute.
 */

export interface Me {
  signedIn: boolean
  registrationOpen: boolean
  name?: string
  party?: string
}

export interface Trajectory {
  trajId: string
  title: string | null
  question: string
  transitionCount: number
  openCount: number
}

export interface Project {
  slug: string
  title: string
  openedBy: string
  /** The account name behind that key here, when this host knows one. */
  openedByName: string | null
  tier: string
  disclosure: string
  openedAt: string
  trajectories: Trajectory[]
}

export interface Hit {
  slug: string
  trajId: string
  question: string
  snippet: string
  where: string
}

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const reply = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    credentials: 'same-origin',
  })
  const body = await reply.json().catch(() => ({}))
  if (!reply.ok) throw new ApiError(body.error ?? `${reply.status} ${reply.statusText}`)
  return body as T
}

export const api = {
  me: () => request<Me>('/api/me'),

  signIn: (name: string, password: string) =>
    request<{ name: string; party: string }>('/api/sign-in', {
      method: 'POST',
      body: JSON.stringify({ name, password }),
    }),

  signOut: () => request<unknown>('/api/sign-out', { method: 'POST' }),

  projects: (mine = false) =>
    request<{ projects: Project[] }>(`/api/projects${mine ? '?mine=1' : ''}`),

  project: (slug: string) => request<Project>(`/api/projects/${encodeURIComponent(slug)}`),

  openProject: (title: string, question: string) =>
    request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ title, question }),
    }),

  /** Widens. There is no counterpart that narrows, and there will not be. */
  disclose: (slug: string) =>
    request<Project>(`/api/projects/${encodeURIComponent(slug)}/disclose`, { method: 'POST' }),

  search: (query: string) =>
    request<{ query: string; hits: Hit[]; ordering: string }>(
      `/api/search?q=${encodeURIComponent(query)}`,
    ),
}
