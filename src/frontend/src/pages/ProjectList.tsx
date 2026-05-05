import React, { useCallback, useEffect, useState } from 'react'
import type { ProjectData } from '../App'

interface Props {
  onSelectProject: (id: string) => void
}

const ProjectList: React.FC<Props> = ({ onSelectProject }) => {
  const [projects, setProjects] = useState<ProjectData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const res = await fetch('/api/projects')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: ProjectData[] = await res.json()
      setProjects(data)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  if (loading) {
    return (
      <div style={{ padding: 32 }}>
        <div className="skeleton-row" style={{ width: '60%' }} />
        <div className="skeleton-row" style={{ width: '80%' }} />
        <div className="skeleton-row" style={{ width: '50%' }} />
        <div className="skeleton-row" style={{ width: '70%' }} />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{ color: '#c0392b', marginBottom: 12, fontSize: 14 }}>
          加载失败，请检查服务是否启动。
        </div>
        <button
          onClick={fetchProjects}
          style={{
            padding: '8px 20px', background: '#0f3460', color: '#fff',
            border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14,
          }}
        >
          重试
        </button>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div style={{ padding: 32, color: '#888', textAlign: 'center' }}>
        暂无项目记录
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h3 style={{ marginBottom: 16 }}>项目列表</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={thStyle}>项目名称</th>
            <th style={thStyle}>状态</th>
            <th style={thStyle}>阶段</th>
            <th style={thStyle}>待审核</th>
            <th style={thStyle}>时间</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((p) => (
            <tr
              key={p.id}
              style={{ cursor: 'pointer', borderBottom: '1px solid #eee' }}
              onClick={() => onSelectProject(p.id)}
            >
              <td style={tdStyle}>{p.title || '未命名'}</td>
              <td style={tdStyle}>
                <StatusBadge status={p.final_decision || p.phase} />
              </td>
              <td style={tdStyle}>{p.phase}</td>
              <td style={tdStyle}>
                {p.needs_review ? (
                  <span style={{ color: '#f0a500', fontWeight: 600 }}>是</span>
                ) : (
                  '否'
                )}
              </td>
              <td style={tdStyle}>
                {p.created_at
                  ? new Date(p.created_at).toLocaleDateString('zh-CN')
                  : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    approve: '#4caf50', defer: '#ff9800', reject: '#f44336',
    init: '#9e9e9e', intake: '#2196f3', dispatch: '#2196f3',
    parallel_analysis: '#673ab7', synthesis: '#673ab7',
    review: '#ff5722', document: '#009688',
    complete: '#4caf50', error: '#f44336',
  }

  const labelMap: Record<string, string> = {
    approve: '建议立项', defer: '建议缓议', reject: '建议拒绝',
    init: '初始化', intake: '需求澄清', dispatch: '任务拆解',
    parallel_analysis: '并行分析', synthesis: '综合分析',
    review: '审核中', document: '生成文档',
    complete: '已完成', error: '异常',
  }

  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 12,
      background: (colorMap[status] || '#9e9e9e') + '22',
      color: colorMap[status] || '#9e9e9e', fontWeight: 500,
    }}>
      {labelMap[status] || status}
    </span>
  )
}

const thStyle: React.CSSProperties = {
  padding: '10px 12px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: '#555',
}

const tdStyle: React.CSSProperties = {
  padding: '10px 12px', fontSize: 13,
}

export default ProjectList
