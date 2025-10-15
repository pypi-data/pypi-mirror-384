import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import AnimatedCard from '@site/src/components/AnimatedComponents/AnimatedCard';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  description: ReactNode;
  link: string;
};

const FeatureList: FeatureItem[] = [
  {
    title: '🎯 Interactive Command Visualizer',
    description: (
      <>
        Explore mem8's command ecosystem through interactive visualizations.
        See complexity pyramids, workflow patterns, dependency matrices, and scatter plots.
        Understand how commands chain together and which ones fit your development workflow.
      </>
    ),
    link: '/docs/workflows/visualizer',
  },
  {
    title: '🧠 Context Window Management',
    description: (
      <>
        A memory system for Claude Code to help manage context, with structured memory and searchable documentation.
        <code>/m8-research</code> helps agents explore your code. As a new feature, we're actively improving it and welcome contributions!
      </>
    ),
    link: '/docs/workflows/research',
  },
  {
    title: '🤝 External Templates & Team Collaboration',
    description: (
      <>
        Share Claude Code prompts and workflows using <a href="https://github.com/killerapp/mem8-plugin" target="_blank" rel="noopener noreferrer">external templates</a>.
        Install from <code>killerapp/mem8-plugin</code> or create your own.
        Standardize development practices across teams and organizations.
      </>
    ),
    link: 'https://github.com/killerapp/mem8-plugin',
  },
];

function Feature({title, description, link}: FeatureItem, index: number) {
  const isExternal = link.startsWith('http');

  return (
    <div className={clsx('col col--4')}>
      <a
        href={link}
        style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}
        {...(isExternal ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
      >
        <AnimatedCard delay={index * 0.2}>
          <div className="text--center padding-horiz--md">
            <Heading as="h3">{title}</Heading>
            <p>{description}</p>
          </div>
        </AnimatedCard>
      </a>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} index={idx} />
          ))}
        </div>
      </div>
    </section>
  );
}
