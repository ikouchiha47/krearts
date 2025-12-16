import type {
  ApiClient,
  ChapterSummary,
  GenerateChaptersPayload,
  GeneratePagesPayload,
  InitBookPayload,
  Job,
  PageSummary,
  StoryTemplateSummary,
  WorkflowSummary,
  CharacterSummary,
} from './ApiClient';

const mockTemplates: StoryTemplateSummary[] = [
  {
    id: 'altered_carbon_detective',
    name: 'Altered Carbon Detective',
    description: 'Cyberpunk noir detective story in a neon-drenched city.',
    genre: 'detective',
    artStyle: 'gritty_cyberpunk',
  },
  {
    id: 'akira_style_story',
    name: 'Akira-style Cyberpunk',
    description: 'High-energy psychic teens and motorcycles in a decaying megacity.',
    genre: 'action',
    artStyle: 'retro_anime',
  },
];

const mockWorkflows: WorkflowSummary[] = [
  {
    id: 'wf-001',
    title: 'Neon Crossroads Case File',
    templateId: 'altered_carbon_detective',
    currentStage: 'chapters',
    chaptersGenerated: 4,
    pagesGenerated: 32,
  },
  {
    id: 'wf-002',
    title: 'Akira-Style Uprising',
    templateId: 'akira_style_story',
    currentStage: 'content',
    chaptersGenerated: 0,
    pagesGenerated: 0,
  },
];

const mockChapters: ChapterSummary[] = [
  { chapterNumber: 1, title: 'The Body in the Rain', scenes: 3, pages: 8 },
  { chapterNumber: 2, title: 'Ghosts in the Data', scenes: 4, pages: 10 },
  { chapterNumber: 3, title: 'Neon Confession', scenes: 3, pages: 7 },
  { chapterNumber: 4, title: 'Exit Wounds', scenes: 2, pages: 7 },
];

const mockPages: PageSummary[] = Array.from({ length: 32 }, (_, i) => {
  const idx = i + 1;
  const chapterNumber = Math.ceil(idx / 8);
  const localIndex = idx - (chapterNumber - 1) * 8;
  return {
    chapterNumber,
    sceneNumber: Math.ceil(localIndex / 2),
    pageNumber: localIndex,
    globalIndex: idx,
    prompt: `Key panel beats for page ${idx}`,
  };
});

let jobCounter = 1;

function makeJob(type: string, metadata: Record<string, unknown>): Job {
  const id = `job-${jobCounter++}`;
  return {
    id,
    workflowId: (metadata.workflowId as string) ?? 'wf-001',
    type,
    status: 'running',
    error: null,
    metadata,
  };
}

const mockCharacters: CharacterSummary[] = [
  {
    id: 'char-1',
    name: 'Detective Morgan',
    role: 'detective',
    imageUrl: undefined,
  },
  {
    id: 'char-2',
    name: 'James Butler',
    role: 'killer',
    imageUrl: undefined,
  },
  {
    id: 'char-3',
    name: 'Victor Ashford',
    role: 'victim',
    imageUrl: undefined,
  },
];

export class MockApiClient implements ApiClient {
  async listWorkflows(): Promise<WorkflowSummary[]> {
    return mockWorkflows;
  }

  async getWorkflow(id: string): Promise<WorkflowSummary | null> {
    return mockWorkflows.find((w) => w.id === id) ?? null;
  }

  async listChapters(workflowId: string): Promise<ChapterSummary[]> {
    void workflowId;
    return mockChapters;
  }

  async listPages(workflowId: string): Promise<PageSummary[]> {
    void workflowId;
    return mockPages;
  }

  async listCharacters(workflowId: string): Promise<CharacterSummary[]> {
    void workflowId;
    return mockCharacters;
  }

  async listTemplates(): Promise<StoryTemplateSummary[]> {
    return mockTemplates;
  }

  async initBook(payload: InitBookPayload): Promise<Job> {
    const wfId = `wf-${String(mockWorkflows.length + 1).padStart(3, '0')}`;
    mockWorkflows.push({
      id: wfId,
      title: payload.title || 'Untitled Case File',
      templateId: payload.templateId,
      currentStage: 'init',
      chaptersGenerated: 0,
      pagesGenerated: 0,
    });
    return makeJob('book_init', { workflowId: wfId, ...payload });
  }

  async generateChapters(payload: GenerateChaptersPayload): Promise<Job> {
    return makeJob('book_chapters', payload as unknown as Record<string, unknown>);
  }

  async generatePages(payload: GeneratePagesPayload): Promise<Job> {
    return makeJob('book_pages', payload as unknown as Record<string, unknown>);
  }
}
