import { createRoot } from 'react-dom/client'
import './style.css'
import { RouterProvider } from 'react-router'
import router from './routes/Routes.tsx'

const rootElement = document.getElementById('app')

if (!rootElement) {
  throw new Error('Root element #app was not found.')
}

createRoot(rootElement).render(<RouterProvider router={router} />)
