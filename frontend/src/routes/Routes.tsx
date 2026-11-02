import { createBrowserRouter } from 'react-router'
import Root from '../layout/Root.tsx'
import Home from '../pages/Home.tsx'
import Login from '../pages/Login.tsx'
import SignUp from '../pages/SignUpPage.tsx'

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
      {
        path: '/signup',
        element: <SignUp />,
      },
    ],
  },
])

export default router
