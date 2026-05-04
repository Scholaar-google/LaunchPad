import React, { useCallback, useEffect, useRef, useState } from 'react'
import type { ReasoningStep } from '../App'

interface Props {
  projectId: string | null
  onProjectCreated: (id: string) => void
  onPhaseUpdate: (phase: string) => void
  onNeedsReview: (flag: boolean) => void
  onDocumentPath: (path: string | null) => void
  onReasoningSteps: (steps: ReasoningStep[]) => void
}

interface Message {
  role: 'system' | 'user' | 'assistant'
  content: string
  questions?: QuestionItem[]
}

interface QuestionItem {
  id: string
  text: string
  dimension: string
}

interface DialogResponse {
  project_id: string
  questions: QuestionItem[]
  status: string
  phase: string
}

interface ConfirmResponse {
  project_id: string
  phase: string
  final_decision: string
  final_recommendation: string
  document_path: string | null
}

const ChatPanel: React.FC<Props> = ({
  projectId,
  onProjectCreated,
  onPhaseUpdate,
  onNeedsReview,
  onDocumentPath,
  onReasoningSteps,
}) => {
  const [requirement, setRequirement] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [questions, setQuestions] = useState<QuestionItem[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, questions])

  useEffect(() => {
    if (projectId) {
      startSSEStream(projectId)
      fetchProjectDetail(projectId)
    }
    return () => {
      eventSourceRef.current?.close()
    }
  }, [projectId])

  const startSSEStream = (id: string) => {
    eventSourceRef.current?.close()
    const es = new EventSource(`/api/projects/${id}/stream`)
    eventSourceRef.current = es

    es.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'reasoning_step' && data.step) {
          onReasoningSteps((prev: ReasoningStep[]) => [...prev, data.step])
        } else if (data.type === 'done') {
          onPhaseUpdate(data.phase)
        }
      } catch {
        console.warn('SSE parse error')
      }
    })

    es.onerror = () => {
      es.close()
    }
  }

  const fetchProjectDetail = async (id: string) => {
    try {
      const res = await fetch(`/api/projects/${id}`)
      if (!res.ok) return
      const data = await res.json()
      onPhaseUpdate(data.phase)
      onNeedsReview(data.needs_review)
      onDocumentPath(data.document_path)
      if (data.reasoning_chain?.length > 0) {
        onReasoningSteps(data.reasoning_chain)
      }
    } catch {
      console.warn('Failed to fetch project detail')
    }
  }

  const handleSubmit = useCallback(async () => {
    if (!requirement.trim()) return
    setLoading(true)

    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirement }),
      })
      const data: DialogResponse = await res.json()

      onProjectCreated(data.project_id)
      onReasoningSteps([])
      setMessages([
        { role: 'user', content: requirement },
      ])

      if (data.questions && data.questions.length > 0) {
        setQuestions(data.questions)
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '', questions: data.questions },
        ])
      }

      onPhaseUpdate(data.phase)
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '请求失败，请检查服务是否启动。' },
      ])
    } finally {
      setLoading(false)
    }
  }, [requirement, onProjectCreated, onPhaseUpdate, onReasoningSteps])

  const handleAnswerSubmit = useCallback(async () => {
    if (!projectId || Object.keys(answers).length === 0) return
    setLoading(true)

    const answerText = Object.entries(answers)
      .map(([k, v]) => `${k}: ${v}`)
      .join('\n')

    setMessages((prev) => [
      ...prev,
      { role: 'user', content: answerText },
    ])

    try {
      const res = await fetch(`/api/projects/${projectId}/dialog`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(answers),
      })
      const data: DialogResponse = await res.json()

      if (data.questions && data.questions.length > 0) {
        setQuestions(data.questions)
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '', questions: data.questions },
        ])
      } else {
        setQuestions([])
      }

      setAnswers({})
      onPhaseUpdate(data.phase)
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '请求失败。' },
      ])
    } finally {
      setLoading(false)
    }
  }, [projectId, answers, onPhaseUpdate])

  const handleConfirm = useCallback(async () => {
    if (!projectId) return
    setLoading(true)

    try {
      const res = await fetch(`/api/projects/${projectId}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, confirmed: true }),
      })
      const data: ConfirmResponse = await res.json()

      setMessages((prev) => [
        ...prev,
        { role: 'system', content: `审核已通过，决策: ${data.final_decision}` },
        { role: 'system', content: data.final_recommendation },
      ])
      onPhaseUpdate(data.phase)
      onNeedsReview(false)
      onDocumentPath(data.document_path)
    } catch {
      setMessages((prev) => [...prev, { role: 'system', content: '确认失败。' }])
    } finally {
      setLoading(false)
    }
  }, [projectId, onPhaseUpdate, onNeedsReview, onDocumentPath])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {messages.length === 0 && !projectId && (
          <div style={{ textAlign: 'center', paddingTop: 60, color: '#888' }}>
            <h3>企业智能需求分析与立项系统</h3>
            <p>在下方输入您的项目需求，系统将通过多轮对话帮您转化为标准立项文档。</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: 12,
              padding: '10px 14px',
              borderRadius: 8,
              background:
                msg.role === 'user'
                  ? '#e3f2fd'
                  : msg.role === 'system'
                  ? '#fff3e0'
                  : '#f5f5f5',
              maxWidth: '80%',
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
              {msg.role === 'user' ? '您' : msg.role === 'system' ? '系统' : '需求分析助手'}
            </div>
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            {msg.questions && (
              <div style={{ marginTop: 8 }}>
                {msg.questions.map((q) => (
                  <div key={q.id} style={{ marginBottom: 8 }}>
                    <div style={{ fontWeight: 500, marginBottom: 4 }}>
                      {q.text}
                      <span style={{ fontSize: 11, color: '#888', marginLeft: 8 }}>
                        [{q.dimension}]
                      </span>
                    </div>
                    <input
                      type="text"
                      value={answers[q.id] || ''}
                      onChange={(e) =>
                        setAnswers((prev) => ({
                          ...prev,
                          [q.id]: e.target.value,
                        }))
                      }
                      placeholder="请输入您的回答..."
                      style={{
                        width: '100%',
                        padding: '6px 10px',
                        border: '1px solid #ddd',
                        borderRadius: 4,
                        fontSize: 13,
                      }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ color: '#888', fontSize: 13, padding: 8 }}>
            正在分析...
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <div
        style={{
          borderTop: '1px solid #e0e0e0',
          padding: '12px 16px',
          background: '#fff',
        }}
      >
        {questions.length > 0 ? (
          <div>
            <button
              onClick={handleAnswerSubmit}
              disabled={loading || Object.keys(answers).length === 0}
              style={primaryBtnStyle}
            >
              提交回答
            </button>
          </div>
        ) : projectId ? (
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              placeholder="输入补充信息或新需求..."
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: 6,
                fontSize: 14,
              }}
            />
            <button
              onClick={handleSubmit}
              disabled={loading || !requirement.trim()}
              style={primaryBtnStyle}
            >
              发送
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder="请描述您的项目需求，例如：我们需要做一个内部考勤管理系统..."
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: 6,
                fontSize: 14,
              }}
            />
            <button
              onClick={handleSubmit}
              disabled={loading || !requirement.trim()}
              style={primaryBtnStyle}
            >
              提交
            </button>
          </div>
        )}

        {projectId && (
          <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
            <button
              onClick={handleConfirm}
              disabled={loading}
              style={{
                ...primaryBtnStyle,
                background: '#f0a500',
              }}
            >
              人工确认审核
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const primaryBtnStyle: React.CSSProperties = {
  padding: '8px 20px',
  background: '#0f3460',
  color: '#fff',
  border: 'none',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 14,
}

export default ChatPanel
