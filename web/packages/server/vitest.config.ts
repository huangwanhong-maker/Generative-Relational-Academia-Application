import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    // Each test opens real projects, and opening one runs `git init` and a
    // commit in a subprocess. That is the behaviour under test, so the timeout
    // moves rather than the behaviour.
    testTimeout: 60_000,
    hookTimeout: 60_000,
    // Serially: several tests spawn git and grrp against the same temporary
    // tree, and Windows will not remove a directory a process still holds.
    fileParallelism: false,
  },
})
