import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import { motion } from 'framer-motion';
import ShimmerButton from '@site/src/components/AnimatedComponents/ShimmerButton';
import GradientText from '@site/src/components/AnimatedComponents/GradientText';
import GlitchText from '@site/src/components/AnimatedComponents/GlitchText';
import CopyButton from '@site/src/components/AnimatedComponents/CopyButton';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Heading as="h1" className="hero__title">
            <GradientText>{siteConfig.title}</GradientText>
          </Heading>
          <motion.p
            className="hero__subtitle"
            style={{fontSize: '1.5rem', marginBottom: '1rem'}}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            Context Management for AI Development
          </motion.p>
          <motion.p
            style={{fontSize: '1.1rem', maxWidth: '800px', margin: '0 auto 2rem', color: '#c9d1d9'}}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            A toolkit for managing AI context windows, memory, and development workflows with <GlitchText />.<br/>
            Features include memory management, toolbelt integration, and intelligent port management.
          </motion.p>
        </motion.div>

        <motion.div
          className={styles.buttons}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
        >
          <ShimmerButton href="/mem8/docs">
            Get Started →
          </ShimmerButton>
          <ShimmerButton
            href="https://github.com/killerapp/mem8"
            variant="outline"
          >
            View on GitHub
          </ShimmerButton>
        </motion.div>

        <motion.div
          className={styles.installCodeContainer}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center', maxWidth: '600px', margin: '0 auto' }}
        >
          <motion.div
            className={styles.installCode}
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
          >
            <code>uv tool install mem8</code>
            <CopyButton text="uv tool install mem8" />
          </motion.div>
          <motion.p
            style={{ fontSize: '0.85rem', color: '#7d8590', marginTop: '0.5rem', textAlign: 'center' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.0, duration: 0.6 }}
          >
            Run in any git repository to set up mem8 workspace with Claude Code integration
          </motion.p>
        </motion.div>
      </div>
    </header>
  );
}

function FeatureSection1() {
  return (
    <section className={styles.featureSection}>
      <div className="container">
        <motion.div
          className={styles.featureContent}
          initial={{ opacity: 0, x: -60 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
        >
          <div className={styles.featureText}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <h2 className={styles.featureTitle}>
                <GradientText>Context Window Management</GradientText>
              </h2>
              <p className={styles.featureDescription}>
                A memory system for Claude Code to help manage context, with structured memory and searchable documentation.
                The <code>/m8-research</code> command helps AI agents explore your codebase intelligently.
              </p>
              <ul className={styles.featureList}>
                <li>📝 Structured memory storage</li>
                <li>🔍 Intelligent codebase search</li>
                <li>🧠 Context-aware documentation</li>
              </ul>
            </motion.div>
          </div>
          <motion.div
            className={styles.featureVisual}
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
            <div className={styles.codeWindow}>
              <div className={styles.codeWindowHeader}>
                <span></span><span></span><span></span>
              </div>
              <div className={styles.codeWindowContent}>
                <code>$ mem8 search "authentication"</code>
                <div className={styles.codeOutput}>
                  <span className={styles.codeComment}>// Found 12 relevant contexts</span>
                  <span>✓ auth/middleware.py</span>
                  <span>✓ docs/security.md</span>
                  <span>✓ memory/auth-strategy.md</span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

function FeatureSection2() {
  return (
    <section className={styles.featureSectionAlt}>
      <div className="container">
        <motion.div
          className={styles.featureContentReverse}
          initial={{ opacity: 0, x: 60 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
        >
          <motion.div
            className={styles.featureVisual}
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <div className={styles.templateGrid}>
              <div className={styles.templateCard}>
                <div className={styles.templateIcon}>📦</div>
                <div>killerapp/mem8-plugin</div>
              </div>
              <div className={styles.templateCard}>
                <div className={styles.templateIcon}>⚡</div>
                <div>Custom workflows</div>
              </div>
              <div className={styles.templateCard}>
                <div className={styles.templateIcon}>🤝</div>
                <div>Team standards</div>
              </div>
            </div>
          </motion.div>
          <div className={styles.featureText}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.4, duration: 0.6 }}
            >
              <h2 className={styles.featureTitle}>
                <GradientText>External Templates & Team Collaboration</GradientText>
              </h2>
              <p className={styles.featureDescription}>
                Share Claude Code prompts and workflows using external templates.
                Install from community repos or create your own to standardize practices across teams.
              </p>
              <ul className={styles.featureList}>
                <li>🎯 Pre-built workflow templates</li>
                <li>👥 Team-wide standardization</li>
                <li>🚀 One-command deployment</li>
              </ul>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function FeatureSection3() {
  return (
    <section className={styles.featureSection}>
      <div className="container">
        <motion.div
          className={styles.featureContent}
          initial={{ opacity: 0, x: -60 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
        >
          <div className={styles.featureText}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <h2 className={styles.featureTitle}>
                <GradientText>Toolbelt & Port Management</GradientText>
              </h2>
              <p className={styles.featureDescription}>
                A toolbelt system for installing and managing development tools with built-in port conflict detection.
                Keep your development environment organized and conflict-free.
              </p>
              <ul className={styles.featureList}>
                <li>🔧 Unified tool installation</li>
                <li>⚠️ Port conflict detection</li>
                <li>📊 Service monitoring</li>
              </ul>
            </motion.div>
          </div>
          <motion.div
            className={styles.featureVisual}
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
            <div className={styles.portMonitor}>
              <div className={styles.portMonitorHeader}>Port Status</div>
              <div className={styles.portList}>
                <div className={styles.portItem}>
                  <span className={styles.portNumber}>:3000</span>
                  <span className={styles.portService}>Next.js</span>
                  <span className={styles.portStatus}>✓</span>
                </div>
                <div className={styles.portItem}>
                  <span className={styles.portNumber}>:8000</span>
                  <span className={styles.portService}>FastAPI</span>
                  <span className={styles.portStatus}>✓</span>
                </div>
                <div className={styles.portItem}>
                  <span className={styles.portNumber}>:5432</span>
                  <span className={styles.portService}>PostgreSQL</span>
                  <span className={styles.portStatus}>✓</span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

function QuickStart() {
  return (
    <section className={styles.quickStartSection}>
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className={styles.quickStartHeader}>
            <Heading as="h2" className={styles.quickStartTitle}>
              <GradientText>Get Started in Seconds</GradientText>
            </Heading>
          </div>
          <div className={styles.quickStartGrid}>
            <motion.div
              className={styles.quickStartCard}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              <div className={styles.stepNumber}>1</div>
              <h3>Install</h3>
              <div className={styles.codeBlock}>
                <code>uv tool install mem8</code>
              </div>
              <p>Install mem8 using uv package manager</p>
            </motion.div>

            <motion.div
              className={styles.quickStartCard}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.4, duration: 0.5 }}
            >
              <div className={styles.stepNumber}>2</div>
              <h3>Initialize</h3>
              <div className={styles.codeBlock}>
                <code>mem8 init</code>
              </div>
              <p>Set up mem8 in your project directory</p>
            </motion.div>

            <motion.div
              className={styles.quickStartCard}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.6, duration: 0.5 }}
            >
              <div className={styles.stepNumber}>3</div>
              <h3>Start Using</h3>
              <div className={styles.codeBlock}>
                <code>mem8 status</code>
              </div>
              <p>Check your setup and start managing context</p>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="mem8 - Context Management for AI Development"
      description="A CLI tool that enables AI assistants to maintain shared context across projects, teams, and conversations. Features include memory management, external templates, and intelligent port management.">
      <HomepageHeader />
      <main>
        <FeatureSection1 />
        <FeatureSection2 />
        <FeatureSection3 />
        <QuickStart />
      </main>
    </Layout>
  );
}
