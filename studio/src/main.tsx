import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'decius-css/css/decius.bundle.min.css'
import 'react-mosaic-component/react-mosaic-component.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
