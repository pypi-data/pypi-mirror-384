import packageJson from '../package.json'

// Get version from environment variable (set during build/deploy from Python backend)
// Falls back to package.json if not available
export const getVersion = () => {
  if (typeof window !== 'undefined') {
    // Client-side: check if version was injected during build
    return (window as any).__MEM8_VERSION__ || process.env.NEXT_PUBLIC_VERSION || packageJson.version
  }
  
  // Server-side: use environment variable set during startup
  return process.env.NEXT_PUBLIC_VERSION || packageJson.version
}

export const getAppName = () => {
  return 'mem8'
}

export const getAppTitle = () => {
  return `${getAppName()} v${getVersion()}`
}