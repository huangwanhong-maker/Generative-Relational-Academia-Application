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
  /** Development aids are available. Off in production, deliberately. */
  dev?: boolean
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
  /** What the project says about itself. A README, not a database column. */
  description: string
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

export interface TransitionView {
  id: string
  act: string | null
  target: string | null
  relation: string | null
  trigger: string | null
  disposition: string | null
  parents: string[]
  priorState: string | null
  posteriorState: string | null
  performer: string
  performed: string
  attested: boolean
  body: string | null
  artefacts: unknown[]
}

export interface TrajectoryDetail {
  trajId: string
  title: string | null
  question: string
  transitions: TransitionView[]
  /** SVG, drawn by the reference implementation. Null if it could not run. */
  graph: string | null
}

export interface ProjectFile {
  name: string
  size: number
  /** state:sha256:… over the bytes. What a transition would cite. */
  digest: string
  modified: string
}

export interface Commit {
  hash: string
  when: string
  subject: string
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

  /** Development only: the substrate's history, which is not the record. */
  gitHistory: (slug: string) =>
    request<{ isRepository: boolean; commits: Commit[]; note?: string }>(
      `/api/projects/${encodeURIComponent(slug)}/git`,
    ),

  createProject: (title: string, description = '') =>
    request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    }),

  /** Open a question, which is what actually starts a line of work. */
  openQuestion: (slug: string, question: string) =>
    request<Project>(`/api/projects/${encodeURIComponent(slug)}/questions`, {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  /** Widens. There is no counterpart that narrows, and there will not be. */
  disclose: (slug: string) =>
    request<Project>(`/api/projects/${encodeURIComponent(slug)}/disclose`, { method: 'POST' }),

  trajectory: (slug: string, trajId: string) =>
    request<TrajectoryDetail>(
      `/api/projects/${encodeURIComponent(slug)}/trajectories/${encodeURIComponent(trajId)}`,
    ),

  files: (slug: string) =>
    request<{ files: ProjectFile[] }>(`/api/projects/${encodeURIComponent(slug)}/files`),

  fileUrl: (slug: string, name: string) =>
    `/api/projects/${encodeURIComponent(slug)}/files/${encodeURIComponent(name)}`,

  /** Stores a file. Records nothing — see the note the server sends back. */
  upload: (slug: string, name: string, contentBase64: string) =>
    request<ProjectFile & { note: string }>(`/api/projects/${encodeURIComponent(slug)}/files`, {
      method: 'POST',
      body: JSON.stringify({ name, contentBase64 }),
    }),

  search: (query: string) =>
    request<{ query: string; hits: Hit[]; ordering: string }>(
      `/api/search?q=${encodeURIComponent(query)}`,
    ),
}
