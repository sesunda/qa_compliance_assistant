import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ProjectsPage from './pages/ProjectsPage'
import ControlsPage from './pages/ControlsPage'
import EvidencePage from './pages/EvidencePage'
import ReportsPage from './pages/ReportsPage'
import RAGPage from './pages/RAGPage'
import UsersPage from './pages/UsersPage'
import AgentTasksPage from './pages/AgentTasksPage'

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/controls" element={<ControlsPage />} />
        <Route path="/evidence" element={<EvidencePage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/rag" element={<RAGPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/agent-tasks" element={<AgentTasksPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}

export default App