import { afterEach, describe, expect, it } from 'vitest'
import { isAbsolute, resolve } from 'node:path'
import { ACADEMIA_ROOT, INFRASTRUCTURE_ROOT, grrpCommand, runtimePaths } from '../src/runtime.js'

const names = ['GRA_RUNTIME', 'GRA_RECORDS', 'GRA_DB', 'GRA_CLIENT', 'GRA_PYTHON', 'GRA_GRRP']
const original = new Map(names.map(name => [name, process.env[name]]))
afterEach(() => { for (const name of names) { const value = original.get(name); if (value === undefined) delete process.env[name]; else process.env[name] = value } })

describe('relocated runtime boundary', () => {
  it('derives data and client paths independently of the working directory', () => {
    for (const name of names) delete process.env[name]
    const paths = runtimePaths()
    expect(paths.recordsRoot).toBe(resolve(INFRASTRUCTURE_ROOT, '.runtime/academia/records'))
    expect(paths.databaseFile).toBe(resolve(INFRASTRUCTURE_ROOT, '.runtime/academia/index.sqlite'))
    expect(paths.clientRoot).toBe(resolve(ACADEMIA_ROOT, 'web_application/packages/client/dist'))
    for (const path of Object.values(paths)) expect(isAbsolute(path)).toBe(true)
  })

  it('passes a configured interpreter containing spaces as one argument', () => {
    process.env.GRA_PYTHON = resolve('an isolated environment', 'python.exe')
    expect(grrpCommand()).toEqual([process.env.GRA_PYTHON, '-m', 'grrp.cli'])
  })

  it('honors explicit runtime locations without rebuilding account state', () => {
    process.env.GRA_RECORDS = resolve('retained-records')
    process.env.GRA_DB = resolve('retained-accounts.sqlite')
    expect(runtimePaths().recordsRoot).toBe(process.env.GRA_RECORDS)
    expect(runtimePaths().databaseFile).toBe(process.env.GRA_DB)
  })
})
