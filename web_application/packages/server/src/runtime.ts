/** Application locations, resolved independently of the launch working directory. */
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const moduleDirectory = dirname(fileURLToPath(import.meta.url))
export const ACADEMIA_ROOT = resolve(moduleDirectory, '../../../..')
export const INFRASTRUCTURE_ROOT = resolve(ACADEMIA_ROOT, '..')

/** The account database is retained data too; it is not merely a derived index. */
export function runtimePaths() {
  const runtime = resolve(process.env['GRA_RUNTIME'] ?? resolve(INFRASTRUCTURE_ROOT, '.runtime/academia'))
  return {
    recordsRoot: resolve(process.env['GRA_RECORDS'] ?? resolve(runtime, 'records')),
    databaseFile: resolve(process.env['GRA_DB'] ?? resolve(runtime, 'index.sqlite')),
    clientRoot: resolve(process.env['GRA_CLIENT'] ?? resolve(ACADEMIA_ROOT, 'web_application/packages/client/dist')),
  }
}

/** GRA_PYTHON is a single executable path; spaces never require shell parsing. */
export function grrpCommand(): string[] {
  const python = process.env['GRA_PYTHON']
  if (python) return [resolve(python), '-m', 'grrp.cli']
  const legacy = process.env['GRA_GRRP']
  if (legacy) {
    // Retain the old simple command form for existing deployments. New launchers
    // use GRA_PYTHON, which accepts executable paths containing spaces safely.
    return legacy.trim().split(/\s+/)
  }
  return [resolve(INFRASTRUCTURE_ROOT, '.runtime/environments/academia',
    process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'), '-m', 'grrp.cli']
}
