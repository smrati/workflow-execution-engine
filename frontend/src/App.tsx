import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Workflows from './pages/Workflows'
import WorkflowDetail from './pages/WorkflowDetail'
import Runs from './pages/Runs'
import RunDetail from './pages/RunDetail'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/workflows/:name" element={<WorkflowDetail />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/runs/:id" element={<RunDetail />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
