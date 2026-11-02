import { Outlet } from 'react-router'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const Root = () => {
  return (
    <div className="flex min-h-dvh flex-col bg-[#09090b]">
      <Navbar isAuthenticated={false} user={null} onLogout={function(): void | Promise<void> {
              throw new Error('Function not implemented.')
          } } />

      <main className="flex-1">
        <Outlet />
      </main>

      <Footer />
    </div>
  )
}

export default Root
