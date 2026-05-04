import React, { useEffect, useRef } from 'react'
import type { ReasoningStep } from '../App'

interface Props {
  steps: ReasoningStep[]
}

const LAYER_LABELS: Record<number, string> = {
  1: '汇总层',
  2: '冲突识别',
  3: '路径推演',
  4: '决策层',
  5: '输出层',
}

const ReasoningPanel: React.FC<Props> = ({ steps }) => {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  if (!steps || steps.length === 0) {
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

      {steps.map((step, i) => (
        <div
          key={i}
          style={{
            marginBottom: 12,
            padding: '10px 12px',
            background: '#fff',
            border: '1px solid #e8e8e8',
            borderRadius: 6,
            borderLeft: `3px solid ${_layerColor(step.layer)}`,
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
                color: _layerColor(step.layer),
              }}
            >
              Step {step.layer}: {LAYER_LABELS[step.layer] || step.title}
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
      ))}

      <div ref={endRef} />
    </div>
  )
}

function _layerColor(layer: number): string {
  const colors: Record<number, string> = {
    1: '#2563eb',
    2: '#d97706',
    3: '#7c3aed',
    4: '#059669',
    5: '#dc2626',
  }
  return colors[layer] || '#666'
}

export default ReasoningPanel
