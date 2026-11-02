import { createBrowserRouter } from 'react-router'
import Root from '../layout/Root.tsx'
import Home from '../pages/Home.tsx'
import Login from '../pages/Login.tsx'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Root />,
    children: [
      {
        path: '/',
        element: <Home />,
      },
      {
        path: '/login',
        element: <Login />,
      },
    ],
  },
])

export default router
