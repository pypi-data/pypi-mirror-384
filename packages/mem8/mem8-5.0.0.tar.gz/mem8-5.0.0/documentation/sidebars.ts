import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    'installation',
    {
      type: 'category',
      label: 'Workflows',
      link: {
        type: 'doc',
        id: 'workflows/index',
      },
      items: [
        'workflows/research',
        'workflows/plan',
        'workflows/implement',
        'workflows/commit',
        'workflows/advanced',
        'workflows/best-practices',
        'workflows/utility',
      ],
    },
    'concepts',
    {
      type: 'category',
      label: 'User Guide',
      items: [
        'user-guide/getting-started',
        'user-guide/cli-commands',
        'user-guide/workflows',
        'user-guide/troubleshooting',
      ],
    },
    'external-templates',
    {
      type: 'category',
      label: 'Contributing',
      link: {
        type: 'doc',
        id: 'contributing/index',
      },
      items: [
        'contributing/setup',
        'contributing/architecture',
      ],
    },
  ],
};

export default sidebars;
