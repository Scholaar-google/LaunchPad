import React, { useEffect, useRef } from 'react'
import type { ReasoningStep } from '../App'

interface Props {
  steps: ReasoningStep[]
}

const LAYER_CONFIG: Record<number, { label: string; color: string }> = {
  1: { label: '汇总层', color: '#2563eb' },
  2: { label: '冲突识别', color: '#d97706' },
  3: { label: '路径推演', color: '#7c3aed' },
  4: { label: '决策层', color: '#059669' },
  5: { label: '输出层', color: '#dc2626' },
}

const ReasoningPanel: React.FC<Props> = ({ steps }) => {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  const visibleSteps = steps.filter((s) => s.content && s.content.trim().length > 0)

  if (!visibleSteps || visibleSteps.length === 0) {
    return (
      <div
        style={{
          width: 320,
          borderLeft: '1px solid #e0e0e0',
          background: '#fafafa',
          padding: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
          fontSize: 13,
        }}
      >
        推理过程将在分析开始后实时展示...
      </div>
    )
  }

  return (
    <div
      style={{
        width: 320,
        borderLeft: '1px solid #e0e0e0',
        background: '#fafafa',
        overflow: 'auto',
        padding: 16,
      }}
    >
      <h3 style={{ fontSize: 14, marginBottom: 16, color: '#333' }}>
        推理过程
      </h3>

      {visibleSteps.map((step, i) => {
        const cfg = LAYER_CONFIG[step.layer] || { label: step.title, color: '#666' }
        return (
          <div
            key={i}
            style={{
              marginBottom: 12,
              padding: '10px 12px',
              background: '#fff',
              border: '1px solid #e8e8e8',
              borderRadius: 6,
              borderLeft: `3px solid ${cfg.color}`,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 6,
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: cfg.color,
                }}
              >
                Step {step.layer}: {cfg.label}
              </span>
              {step.confidence < 1.0 && (
                <span style={{ fontSize: 11, color: '#888' }}>
                  {Math.round(step.confidence * 100)}%
                </span>
              )}
            </div>
            <div
              style={{
                fontSize: 12,
                color: '#555',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.5,
              }}
            >
              {step.content}
            </div>
            <div style={{ fontSize: 10, color: '#bbb', marginTop: 4 }}>
              {step.timestamp && new Date(step.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )
      })}

      <div ref={endRef} />
    </div>
  )
}

export default ReasoningPanel
