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
import AgenticChatPage from './pages/AgenticChatPage'
import UsersPage from './pages/UsersPage'
import AgentTasksPage from './pages/AgentTasksPage'
import AgenciesPage from './pages/AgenciesPage'
import AssessmentsPage from './pages/AssessmentsPage'
import AssessmentDetailPage from './pages/AssessmentDetailPage'
import FindingsPage from './pages/FindingsPage'
import FindingDetailPage from './pages/FindingDetailPage'
import QAReviewPage from './pages/QAReviewPage'

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
        <Route path="/" element={<Navigate to="/agentic-chat" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/assessments" element={<AssessmentsPage />} />
        <Route path="/assessments/:id" element={<AssessmentDetailPage />} />
        <Route path="/findings" element={<FindingsPage />} />
        <Route path="/findings/:id" element={<FindingDetailPage />} />
        <Route path="/qa-review" element={<QAReviewPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/controls" element={<ControlsPage />} />
        <Route path="/evidence" element={<EvidencePage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/rag" element={<RAGPage />} />
        <Route path="/agentic-chat" element={<AgenticChatPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/agent-tasks" element={<AgentTasksPage />} />
        <Route path="/agencies" element={<AgenciesPage />} />
        <Route path="*" element={<Navigate to="/agentic-chat" replace />} />
      </Routes>
    </Layout>
  )
}

export default App