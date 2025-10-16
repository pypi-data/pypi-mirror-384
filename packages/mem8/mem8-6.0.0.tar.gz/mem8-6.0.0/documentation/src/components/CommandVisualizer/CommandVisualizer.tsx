import React, { useState } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import styles from './CommandVisualizer.module.css';

// ============================================================================
// DATA MODELS
// ============================================================================

interface Command {
  id: string;
  name: string;
  complexity: number;
  tier: string;
  description: string;
  parallelization: 'none' | 'light' | 'heavy';
  agents?: string[];
  lines: number;
}

const commands: Command[] = [
  {
    id: 'local-review',
    name: 'm8-local-review',
    complexity: 3,
    tier: 'Setup & Utility',
    description: 'Git worktree setup',
    parallelization: 'none',
    lines: 50,
  },
  {
    id: 'commit',
    name: 'm8-commit',
    complexity: 3,
    tier: 'Setup & Utility',
    description: 'Create commits',
    parallelization: 'none',
    lines: 44,
  },
  {
    id: 'plan',
    name: 'm8-plan',
    complexity: 4,
    tier: 'Workflow Automation',
    description: 'Create plans',
    parallelization: 'none',
    lines: 87,
  },
  {
    id: 'implement',
    name: 'm8-implement',
    complexity: 5,
    tier: 'Implementation',
    description: 'Execute plans',
    parallelization: 'light',
    lines: 71,
  },
  {
    id: 'describe-pr',
    name: 'm8-describe-pr',
    complexity: 6,
    tier: 'Integration',
    description: 'Generate PR docs',
    parallelization: 'light',
    lines: 77,
  },
  {
    id: 'debug',
    name: 'm8-debug',
    complexity: 7,
    tier: 'Investigation',
    description: '3 parallel agents',
    parallelization: 'heavy',
    agents: ['Log Analyzer', 'DB Inspector', 'Git Inspector'],
    lines: 200,
  },
  {
    id: 'validate',
    name: 'm8-validate',
    complexity: 8,
    tier: 'Verification',
    description: '3+ agents',
    parallelization: 'heavy',
    agents: ['DB Verifier', 'Code Verifier', 'Test Verifier'],
    lines: 168,
  },
  {
    id: 'research',
    name: 'm8-research',
    complexity: 9,
    tier: 'Orchestration',
    description: '5+ parallel agents',
    parallelization: 'heavy',
    agents: ['codebase-locator', 'codebase-analyzer', 'pattern-finder', 'memory-locator', 'memory-analyzer', 'web-search-researcher'],
    lines: 201,
  },
];

const workflows = {
  'Full Lifecycle': [
    { from: 'research', to: 'plan' },
    { from: 'plan', to: 'implement' },
    { from: 'implement', to: 'validate' },
    { from: 'validate', to: 'commit' },
    { from: 'commit', to: 'describe-pr' },
  ],
  'Quick Fix': [
    { from: 'debug', to: 'implement' },
    { from: 'implement', to: 'commit' },
    { from: 'commit', to: 'describe-pr' },
  ],
  'Research': [
    { from: 'research', to: 'plan' },
  ],
  'Code Review': [
    { from: 'local-review', to: 'research' },
    { from: 'research', to: 'validate' },
  ],
};

// ============================================================================
// COMPONENTS
// ============================================================================

const ComplexityPyramid: React.FC<{ onSelect: (id: string) => void; selected: string | null }> = ({ onSelect, selected }) => {
  const levels = [
    { commands: ['research'], label: 'Orchestration' },
    { commands: ['validate'], label: 'Verification' },
    { commands: ['debug'], label: 'Investigation' },
    { commands: ['describe-pr'], label: 'Integration' },
    { commands: ['implement'], label: 'Implementation' },
    { commands: ['plan'], label: 'Automation' },
    { commands: ['commit', 'local-review'], label: 'Utility' },
  ];

  return (
    <div className={styles.pyramid}>
      {levels.map((level, idx) => (
        <div key={idx} className={styles.pyramidLevel} style={{ width: `${100 - idx * 10}%` }}>
          {level.commands.map((cmdId) => {
            const cmd = commands.find((c) => c.id === cmdId)!;
            const isSelected = selected === cmdId;
            return (
              <motion.div
                key={cmdId}
                className={clsx(styles.pyramidBlock, isSelected && styles.selected)}
                onClick={() => onSelect(cmdId)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                style={{ opacity: 1 - idx * 0.08 }}
              >
                <div className={styles.pyramidBlockName}>{cmd.name}</div>
                <div className={styles.pyramidBlockComplexity}>({cmd.complexity})</div>
              </motion.div>
            );
          })}
        </div>
      ))}
    </div>
  );
};

const WorkflowDiagram: React.FC<{ workflow: string }> = ({ workflow }) => {
  const flow = workflows[workflow as keyof typeof workflows];
  if (!flow) return null;

  return (
    <div className={styles.workflow}>
      {flow.map((edge, idx) => {
        const fromCmd = commands.find((c) => c.id === edge.from);
        const toCmd = commands.find((c) => c.id === edge.to);

        return (
          <React.Fragment key={idx}>
            <motion.div
              className={styles.workflowNode}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              {fromCmd?.name}
            </motion.div>
            <div className={styles.workflowArrow}>↓</div>
            {idx === flow.length - 1 && (
              <motion.div
                className={clsx(styles.workflowNode, styles.workflowNodeFinal)}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: (idx + 1) * 0.1 }}
              >
                {toCmd?.name}
              </motion.div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

const InteractionMatrix: React.FC = () => {
  const matrix: Record<string, string[]> = {
    'local-review': ['validate', 'research'],
    commit: ['describe-pr'],
    plan: ['implement'],
    implement: ['commit', 'describe-pr', 'debug', 'validate'],
    debug: ['plan', 'implement'],
    validate: ['commit', 'describe-pr', 'debug'],
    research: ['plan', 'implement'],
  };

  return (
    <div className={styles.matrixWrapper}>
      <table className={styles.matrix}>
        <thead>
          <tr>
            <th>Creates →</th>
            {commands.map((cmd) => (
              <th key={cmd.id}>{cmd.name.replace('m8-', '')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {commands.map((rowCmd) => (
            <tr key={rowCmd.id}>
              <td className={styles.matrixRowHeader}>{rowCmd.name}</td>
              {commands.map((colCmd) => (
                <td
                  key={colCmd.id}
                  className={clsx(
                    rowCmd.id === colCmd.id && styles.matrixSelf,
                    matrix[rowCmd.id]?.includes(colCmd.id) && styles.matrixActive
                  )}
                >
                  {rowCmd.id === colCmd.id ? '-' : matrix[rowCmd.id]?.includes(colCmd.id) ? '✓' : ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const ScatterPlot: React.FC<{ onSelect: (id: string) => void; selected: string | null }> = ({ onSelect, selected }) => {
  return (
    <div className={styles.scatter}>
      <div className={styles.scatterYLabel}>Autonomy</div>
      <div className={styles.scatterXLabel}>Complexity</div>
      <div className={styles.scatterPlot}>
        {/* Grid lines */}
        {[...Array(11)].map((_, i) => (
          <React.Fragment key={i}>
            <div className={styles.scatterGridH} style={{ bottom: `${(i / 10) * 100}%` }} />
            <div className={styles.scatterGridV} style={{ left: `${(i / 10) * 100}%` }} />
          </React.Fragment>
        ))}
        {/* Data points */}
        {commands.map((cmd) => (
          <motion.div
            key={cmd.id}
            className={clsx(styles.scatterPoint, selected === cmd.id && styles.selected)}
            style={{
              left: `${(cmd.complexity / 10) * 100}%`,
              bottom: `${(cmd.complexity / 10) * 100}%`,
            }}
            onClick={() => onSelect(cmd.id)}
            whileHover={{ scale: 1.5 }}
            whileTap={{ scale: 0.9 }}
          >
            <div className={styles.scatterLabel}>{cmd.name}</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function CommandVisualizer() {
  const [activeView, setActiveView] = useState<'pyramid' | 'workflows' | 'matrix' | 'scatter'>('pyramid');
  const [selectedCommand, setSelectedCommand] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('Full Lifecycle');

  const selectedCmd = commands.find((c) => c.id === selectedCommand);

  return (
    <div className={styles.container}>
      {/* View selector */}
      <div className={styles.tabs}>
        {['pyramid', 'workflows', 'matrix', 'scatter'].map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view as any)}
            className={clsx(styles.tab, activeView === view && styles.tabActive)}
          >
            {view === 'pyramid' && '📊 Pyramid'}
            {view === 'workflows' && '🔄 Workflows'}
            {view === 'matrix' && '📋 Matrix'}
            {view === 'scatter' && '📈 Scatter'}
          </button>
        ))}
      </div>

      {/* Main visualization */}
      <div className={styles.visualization}>
        {activeView === 'pyramid' && (
          <div>
            <h3>Complexity Pyramid</h3>
            <p className={styles.subtitle}>Commands arranged by complexity level</p>
            <ComplexityPyramid onSelect={setSelectedCommand} selected={selectedCommand} />
          </div>
        )}

        {activeView === 'workflows' && (
          <div>
            <h3>Workflow Patterns</h3>
            <div className={styles.workflowTabs}>
              {Object.keys(workflows).map((workflow) => (
                <button
                  key={workflow}
                  onClick={() => setSelectedWorkflow(workflow)}
                  className={clsx(
                    styles.workflowTab,
                    selectedWorkflow === workflow && styles.workflowTabActive
                  )}
                >
                  {workflow}
                </button>
              ))}
            </div>
            <WorkflowDiagram workflow={selectedWorkflow} />
          </div>
        )}

        {activeView === 'matrix' && (
          <div>
            <h3>Command Dependencies</h3>
            <p className={styles.subtitle}>Which commands create input for others</p>
            <InteractionMatrix />
          </div>
        )}

        {activeView === 'scatter' && (
          <div>
            <h3>Complexity vs Autonomy</h3>
            <p className={styles.subtitle}>Higher values = more complex & autonomous</p>
            <ScatterPlot onSelect={setSelectedCommand} selected={selectedCommand} />
          </div>
        )}
      </div>

      {/* Selected command info */}
      {selectedCmd && (
        <motion.div
          className={styles.info}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className={styles.infoHeader}>
            <span className={styles.infoName}>{selectedCmd.name}</span>
            <button className={styles.infoClose} onClick={() => setSelectedCommand(null)}>
              ×
            </button>
          </div>
          <div className={styles.infoContent}>
            <div className={styles.infoItem}>
              <strong>Complexity:</strong> {selectedCmd.complexity}/10
            </div>
            <div className={styles.infoItem}>
              <strong>Description:</strong> {selectedCmd.description}
            </div>
            <div className={styles.infoItem}>
              <strong>Parallelization:</strong>{' '}
              <span className={clsx(styles.badge, styles[`badge${selectedCmd.parallelization}`])}>
                {selectedCmd.parallelization}
              </span>
            </div>
            {selectedCmd.agents && (
              <div className={styles.infoItem}>
                <strong>Agents:</strong> {selectedCmd.agents.join(', ')}
              </div>
            )}
            <div className={styles.infoItem}>
              <strong>Lines:</strong> {selectedCmd.lines}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
