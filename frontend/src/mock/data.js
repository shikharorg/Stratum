export const mockStats = {
  documents: { count: '12,481', delta: '+124 today' },
  connectors: { count: '3', status: 'all active' },
  running: { count: '2', status: 'now' },
};

export const mockActiveNow = [
  { id: '1', name: 'RAG Workflow running', startedAgo: '2m' },
  { id: '2', name: 'Slack synchronizing', startedAgo: '8m' },
];

export const mockNeedsAttention = [
  { id: '1', message: '2 documents stuck in processing', href: '/knowledge' },
  { id: '2', message: "Jira hasn't synced in 6 hours", href: '/integrations' },
];

export const mockRecentEvents = [
  { id: '1', primary: 'test_doc.md indexed', secondary: null, time: '2m ago', status: 'success' },
  { id: '2', primary: 'Search completed', secondary: '"What is Stratum?"', time: '5m ago', status: 'success' },
  { id: '3', primary: 'RAG Workflow completed', secondary: null, time: '12m ago', status: 'success' },
  { id: '4', primary: 'Slack synchronized', secondary: null, time: '1h ago', status: 'success' },
  { id: '5', primary: 'RAG Workflow failed', secondary: null, time: '3h ago', status: 'error' },
];

export const mockWorkflows = [
  { id: 'ff00a735', name: 'RAG Workflow', description: 'Retrieves and generates answers from ingested documents', status: 'active', lastRun: '2m ago', successRate: '98%', totalRuns: 247 },
  { id: 'ab12cd34', name: 'Document Summary', description: 'Summarizes newly ingested documents automatically', status: 'active', lastRun: '1h ago', successRate: '100%', totalRuns: 89 },
  { id: 'ef56gh78', name: 'Slack Digest', description: 'Generates daily digest from Slack channel activity', status: 'inactive', lastRun: '2d ago', successRate: '91%', totalRuns: 34 },
];

export const mockWorkflowRuns = [
  { id: 'cd8432af', workflow: 'RAG Workflow', status: 'completed', duration: '5.3s', startedAt: '2m ago' },
  { id: 'aa886fd9', workflow: 'RAG Workflow', status: 'completed', duration: '2.1s', startedAt: '15m ago' },
  { id: '13432136', workflow: 'Document Summary', status: 'completed', duration: '1.8s', startedAt: '1h ago' },
  { id: '5ba792f4', workflow: 'RAG Workflow', status: 'failed', duration: '1.2s', startedAt: '3h ago' },
  { id: 'bb991cc2', workflow: 'Slack Digest', status: 'completed', duration: '8.7s', startedAt: '2d ago' },
];

export const mockDocuments = [
  { id: '14f6b9a6', name: 'test_doc.md', sourceType: 'markdown', status: 'completed', chunkCount: 2, fileSize: '2.4 KB', uploadedAt: '2m ago' },
  { id: 'bc23ef45', name: 'engineering_handbook.pdf', sourceType: 'pdf', status: 'completed', chunkCount: 47, fileSize: '1.2 MB', uploadedAt: '1h ago' },
  { id: 'de34gh56', name: 'product_roadmap.pdf', sourceType: 'pdf', status: 'completed', chunkCount: 23, fileSize: '840 KB', uploadedAt: '3h ago' },
  { id: 'fg45ij67', name: 'slack_export.json', sourceType: 'slack', status: 'processing', chunkCount: null, fileSize: '156 KB', uploadedAt: '5m ago' },
  { id: 'gh56kl78', name: 'api_docs.md', sourceType: 'markdown', status: 'failed', chunkCount: null, fileSize: '18 KB', uploadedAt: '1d ago' },
];

export const mockSearchResult = {
  query: 'What is Stratum?',
  answer: 'Stratum is an enterprise-grade AI Operations Platform. It acts as the AI operational layer for a company — retrieving enterprise knowledge, automating workflows, coordinating agents, and integrating with external systems like Slack, Jira, and GitHub.',
  latency: '116ms',
  chunks: [
    { text: '# What is Stratum\n\nStratum is an enterprise-grade AI Operations Platform. It acts as the AI operational layer for a company — retrieving enterprise knowledge, automating workflows, coordinating agents, and integrating with external systems like Slack, Jira, and GitHub.', source: 'test_doc.md', sourceType: 'markdown' },
    { text: '# Core Features\n\nStratum provides hybrid RAG retrieval using dense and sparse vectors, multi-tenant isolation, async workflow orchestration via LangGraph, and full observability of every LLM call and retrieval operation.', source: 'test_doc.md', sourceType: 'markdown' },
  ],
};

export const mockConnectors = [
  { id: 'sl001', name: 'Engineering Slack', type: 'slack', status: 'active', lastSync: '8m ago', documentsIngested: 1240 },
  { id: 'ji001', name: 'Product Jira', type: 'jira', status: 'error', lastSync: '6h ago', documentsIngested: 384, errorMessage: 'Authentication failed' },
  { id: 'gh001', name: 'Backend GitHub', type: 'github', status: 'active', lastSync: '32m ago', documentsIngested: 891 },
  { id: 'sl002', name: 'Marketing Slack', type: 'slack', status: 'inactive', lastSync: '3d ago', documentsIngested: 203 },
];

export const mockAvailableIntegrations = [
  { type: 'slack', name: 'Slack', description: 'Workspace messages' },
  { type: 'jira', name: 'Jira', description: 'Project tickets' },
  { type: 'github', name: 'GitHub', description: 'Issues and PRs' },
];

export const mockTeamMembers = [
  { id: '1', name: 'Alex Chen', email: 'admin@test.com', role: 'Admin' },
  { id: '2', name: 'John Smith', email: 'john@test.com', role: 'Member' },
  { id: '3', name: 'Sarah Park', email: 'sarah@test.com', role: 'Member' },
];

export const mockTenant = {
  name: 'Stratum Test',
  slug: 'stratum-test',
  apiKeyPreview: 'sk_live_',
};

export const mockProfile = {
  email: 'admin@test.com',
  role: 'Admin',
};
