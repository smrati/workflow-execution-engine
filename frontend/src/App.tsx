import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import { TimezoneProvider } from './hooks/useTimezone'
import { ToastProvider } from './hooks/useToast'
import ProtectedRoute from './components/common/ProtectedRoute'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Workflows from './pages/Workflows'
import WorkflowDetail from './pages/WorkflowDetail'
import Runs from './pages/Runs'
import RunDetail from './pages/RunDetail'
import Login from './pages/Login'
import UserManagement from './pages/UserManagement'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <TimezoneProvider>
          <ToastProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/workflows" element={<Workflows />} />
                        <Route path="/workflows/:name" element={<WorkflowDetail />} />
                        <Route path="/runs" element={<Runs />} />
                        <Route path="/runs/:id" element={<RunDetail />} />
                        <Route path="/admin/users" element={<UserManagement />} />
                      </Routes>
                    </Layout>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </ToastProvider>
        </TimezoneProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
