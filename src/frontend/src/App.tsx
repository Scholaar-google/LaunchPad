import React, { useCallback, useState } from 'react'
import ChatPanel from './components/ChatPanel'
import ReasoningPanel from './components/ReasoningPanel'
import ProjectList from './pages/ProjectList'

export interface ReasoningStep {
  layer: number
  title: string
  content: string
  timestamp: string
  confidence: number
}

export interface ProjectData {
  id: string
  title: string
  status: string
  phase: string
  needs_review: boolean
  final_decision: string | null
  reasoning_chain: ReasoningStep[]
}

const App: React.FC = () => {
  const [page, setPage] = useState<'new' | 'list' | 'detail'>('new')
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([])
  const [phase, setPhase] = useState<string>('init')
  const [needsReview, setNeedsReview] = useState(false)
  const [documentPath, setDocumentPath] = useState<string | null>(null)

  const handleProjectCreated = useCallback((projectId: string) => {
    setCurrentProjectId(projectId)
    setPage('detail')
  }, [])

  const handleSelectProject = useCallback((projectId: string) => {
    setCurrentProjectId(projectId)
    setPage('detail')
  }, [])

  const handleBackToList = useCallback(() => {
    setPage('list')
  }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      {/* Sidebar */}
      <div style={{ width: 220, background: '#1a1a2e', color: '#eee', padding: 16 }}>
        <h2 style={{ fontSize: 18, marginBottom: 24 }}>LaunchPad</h2>
        <nav>
          <button
            onClick={() => setPage('new')}
            style={navBtnStyle(page === 'new')}
          >
            新建项目
          </button>
          <button
            onClick={() => setPage('list')}
            style={navBtnStyle(page === 'list')}
          >
            项目列表
          </button>
        </nav>
        {currentProjectId && (
          <div style={{ marginTop: 24 }}>
            <button
              onClick={() => setPage('detail')}
              style={navBtnStyle(page === 'detail')}
            >
              当前项目
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <header
          style={{
            background: '#16213e',
            color: '#fff',
            padding: '12px 20px',
            fontSize: 14,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>
            Phase: <strong>{phase}</strong>
            {needsReview && (
              <span style={{ color: '#f0a500', marginLeft: 12 }}>
                [等待人工审核]
              </span>
            )}
          </span>
          {documentPath && (
            <span style={{ color: '#4ecca3' }}>
              文档已生成: {documentPath.split('/').pop()}
            </span>
          )}
        </header>

        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <div style={{ flex: 1, overflow: 'auto' }}>
            {page === 'new' && (
              <ChatPanel
                onProjectCreated={handleProjectCreated}
                projectId={currentProjectId}
                onPhaseUpdate={setPhase}
                onNeedsReview={setNeedsReview}
                onDocumentPath={setDocumentPath}
              />
            )}
            {page === 'list' && (
              <ProjectList
                onSelectProject={handleSelectProject}
              />
            )}
            {page === 'detail' && currentProjectId && (
              <ChatPanel
                projectId={currentProjectId}
                onProjectCreated={handleProjectCreated}
                onPhaseUpdate={setPhase}
                onNeedsReview={setNeedsReview}
                onDocumentPath={setDocumentPath}
              />
            )}
          </div>
          <ReasoningPanel steps={reasoningSteps} />
        </div>
      </div>
    </div>
  )
}

function navBtnStyle(active: boolean): React.CSSProperties {
  return {
    display: 'block',
    width: '100%',
    padding: '10px 12px',
    marginBottom: 4,
    background: active ? '#0f3460' : 'transparent',
    color: '#eee',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    textAlign: 'left',
    fontSize: 14,
  }
}

export default App
