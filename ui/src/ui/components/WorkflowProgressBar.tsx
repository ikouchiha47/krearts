import React from 'react';

interface Stage {
  id: string;
  label: string;
  completed: boolean;
  active: boolean;
}

interface WorkflowProgressBarProps {
  stages: Stage[];
}

export const WorkflowProgressBar: React.FC<WorkflowProgressBarProps> = ({ stages }) => {
  return (
    <div className="px-10 py-3 bg-[var(--cream-dark)] border-b-2 border-[var(--ink)]">
      <div className="max-w-4xl mx-auto">
        <svg width="100%" height="40" viewBox="0 0 1000 40" preserveAspectRatio="xMidYMid meet">
          {/* Draw connecting lines */}
          {stages.map((stage, index) => {
            if (index === stages.length - 1) return null;
            const x1 = 80 + index * 190;
            const x2 = 80 + (index + 1) * 190;
            const isCompleted = stage.completed;
            
            return (
              <line
                key={`line-${index}`}
                x1={x1}
                y1="12"
                x2={x2}
                y2="12"
                stroke={isCompleted ? 'var(--ink)' : '#94a3b8'}
                strokeWidth="2"
              />
            );
          })}
          
          {/* Draw dots and labels */}
          {stages.map((stage, index) => {
            const x = 80 + index * 190;
            let fillColor = '#e2e8f0'; // light gray - not started
            let strokeColor = '#94a3b8';
            
            if (stage.completed) {
              fillColor = 'var(--ink)'; // black - completed
              strokeColor = 'var(--ink)';
            } else if (stage.active) {
              fillColor = 'var(--orange)'; // orange - active
              strokeColor = 'var(--ink)';
            }
            
            return (
              <g key={stage.id}>
                {/* Dot */}
                <circle
                  cx={x}
                  cy="12"
                  r="6"
                  fill={fillColor}
                  stroke={strokeColor}
                  strokeWidth="2"
                />
                
                {/* Checkmark for completed */}
                {stage.completed && (
                  <text
                    x={x}
                    y="15"
                    textAnchor="middle"
                    fill="white"
                    fontSize="8"
                    fontWeight="bold"
                  >
                    ✓
                  </text>
                )}
                
                {/* Label */}
                <text
                  x={x}
                  y="32"
                  textAnchor="middle"
                  fill="var(--ink)"
                  fontSize="10"
                  fontWeight="bold"
                  style={{ textTransform: 'uppercase', letterSpacing: '0.5px' }}
                >
                  {stage.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};
