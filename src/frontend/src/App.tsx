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
  created_at: string | null
}

const PHASE_ORDER = [
  'init', 'intake', 'dispatch',
  'parallel_analysis', 'synthesis', 'review',
  'document', 'complete',
] as const

const PHASE_LABELS: Record<string, string> = {
  init: '初始化',
  intake: '需求澄清',
  dispatch: '任务拆解',
  parallel_analysis: '并行分析',
  synthesis: '综合分析',
  review: '审核中',
  document: '生成文档',
  complete: '已完成',
  error: '异常',
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
    setReasoningSteps([])
    setPhase('init')
    setNeedsReview(false)
    setDocumentPath(null)
    setPage('detail')
  }, [])

  const phaseIndex = PHASE_ORDER.indexOf(phase)

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:.2} 50%{opacity:1} }
        @keyframes skeleton { 0%{background-position:-200px 0} 100%{background-position:200px 0} }
        .spinner-dot { display:inline-block;animation:pulse 1.4s ease-in-out infinite;font-size:inherit; }
        .spinner-dot:nth-child(2) { animation-delay:.2s; }
        .spinner-dot:nth-child(3) { animation-delay:.4s; }
        .skeleton-row { height:24px;margin:8px 0;border-radius:4px;
          background:linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%);background-size:200px 100%;
          animation:skeleton 1.5s ease-in-out infinite; }
        .error-banner { background:#fff0f0;color:#c0392b;padding:8px 14px;border-radius:6px;
          display:flex;justify-content:space-between;align-items:center;margin:8px 0;font-size:13px; }
        .error-banner button { background:none;border:none;color:#c0392b;cursor:pointer;font-weight:600;font-size:13px; }
      `}</style>

      {/* Sidebar */}
      <div style={{ width: 220, background: '#1a1a2e', color: '#eee', padding: 16 }}>
        <h2 style={{ fontSize: 18, marginBottom: 24 }}>LaunchPad</h2>
        <nav>
          <button onClick={() => { setPage('new'); setReasoningSteps([]) }} style={navBtnStyle(page === 'new')}>
            新建项目
          </button>
          <button onClick={() => setPage('list')} style={navBtnStyle(page === 'list')}>
            项目列表
          </button>
        </nav>
        {currentProjectId && (
          <div style={{ marginTop: 24 }}>
            <button onClick={() => setPage('detail')} style={navBtnStyle(page === 'detail')}>
              当前项目
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <header style={{
          background: '#16213e', color: '#fff', padding: '12px 20px',
          fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          minHeight: 56,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {PHASE_ORDER.map((p, i) => {
              const isDone = i < phaseIndex
              const isActive = i === phaseIndex
              const isFuture = i > phaseIndex
              return (
                <React.Fragment key={p}>
                  {i > 0 && (
                    <span style={{ color: isDone ? '#4ecca3' : '#444', fontSize: 10 }}>—</span>
                  )}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                    <div style={{
                      width: 10, height: 10, borderRadius: '50%',
                      background: isDone ? '#4ecca3' : isActive ? '#4ecca3' : '#555',
                      boxShadow: isActive ? '0 0 6px #4ecca3' : 'none',
                    }} />
                    <span style={{
                      fontSize: 9, color: isDone ? '#4ecca3' : isActive ? '#4ecca3' : '#777',
                      fontWeight: isActive ? 600 : 400,
                    }}>
                      {PHASE_LABELS[p] || p}
                    </span>
                  </div>
                </React.Fragment>
              )
            })}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            {needsReview && (
              <span style={{ color: '#f0a500', fontWeight: 600 }}>[等待人工审核]</span>
            )}
            {documentPath && (
              <span style={{ color: '#4ecca3' }}>文档已生成: {documentPath.split('/').pop()}</span>
            )}
          </div>
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
                onReasoningSteps={setReasoningSteps}
              />
            )}
            {page === 'list' && (
              <ProjectList onSelectProject={handleSelectProject} />
            )}
            {page === 'detail' && currentProjectId && (
              <ChatPanel
                projectId={currentProjectId}
                onProjectCreated={handleProjectCreated}
                onPhaseUpdate={setPhase}
                onNeedsReview={setNeedsReview}
                onDocumentPath={setDocumentPath}
                onReasoningSteps={setReasoningSteps}
              />
            )}
          </div>
          {page === 'detail' && currentProjectId && (
            <ReasoningPanel steps={reasoningSteps} />
          )}
        </div>
      </div>
    </div>
  )
}

function navBtnStyle(active: boolean): React.CSSProperties {
  return {
    display: 'block', width: '100%', padding: '10px 12px', marginBottom: 4,
    background: active ? '#0f3460' : 'transparent', color: '#eee',
    border: 'none', borderRadius: 6, cursor: 'pointer', textAlign: 'left', fontSize: 14,
  }
}

export default App
