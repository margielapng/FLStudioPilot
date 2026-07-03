const { app, BrowserWindow, Tray, Menu, nativeImage } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

const isDev = process.env.NODE_ENV === 'development'
const DEV_URL = 'http://localhost:5180'
const ICON_PATH = path.join(__dirname, '..', 'build', 'icon.ico')

let mainWindow = null
let tray = null
let backendProcess = null

function startBackend() {
  const backendDir = path.join(__dirname, '..', '..', 'backend')
  backendProcess = spawn('python', ['main.py'], {
    cwd: backendDir,
    stdio: 'inherit',
    windowsHide: true,
  })
  backendProcess.on('error', (err) => {
    console.error('[FL Copilot] Failed to start backend:', err.message)
  })
  backendProcess.on('exit', (code) => {
    console.log(`[FL Copilot] Backend exited with code ${code}`)
    backendProcess = null
  })
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill()
    backendProcess = null
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 480,
    height: 640,
    minWidth: 360,
    minHeight: 480,
    title: 'FL Copilot',
    icon: ICON_PATH,
    autoHideMenuBar: true,
    backgroundColor: '#0d0d0f',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (isDev) {
    mainWindow.loadURL(DEV_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault()
      mainWindow.hide()
    }
  })
}

function createTray() {
  const icon = nativeImage.createFromPath(ICON_PATH)
  tray = new Tray(icon.resize({ width: 16, height: 16 }))
  tray.setToolTip('FL Copilot')

  const menu = Menu.buildFromTemplate([
    { label: 'Show FL Copilot', click: () => mainWindow?.show() },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true
        app.quit()
      },
    },
  ])
  tray.setContextMenu(menu)
  tray.on('click', () => mainWindow?.show())
}

app.whenReady().then(() => {
  startBackend()
  createWindow()
  createTray()
})

app.on('window-all-closed', () => {
  // Keep the app alive in the tray — don't quit on window close.
})

app.on('before-quit', () => {
  app.isQuitting = true
  stopBackend()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
  else mainWindow?.show()
})
