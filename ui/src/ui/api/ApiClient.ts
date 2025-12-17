export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Job {
  id: string;
  workflowId: string;
  type: string;
  status: JobStatus;
  error?: string | null;
  metadata: Record<string, unknown>;
}

export interface WorkflowSummary {
  id: string;
  title: string;
  templateId?: string;
  currentStage: string;
  chaptersGenerated: number;
  pagesGenerated: number;
}

export interface ChapterSummary {
  chapterNumber: number;
  title: string;
  scenes: number;
  pages: number;
}

export interface PageSummary {
  chapterNumber: number;
  sceneNumber: number;
  pageNumber: number;
  globalIndex: number;
  prompt?: string;
}

export interface CharacterSummary {
  id: string;
  name: string;
  role: string;
  imageUrl?: string;
}

export interface StoryTemplateSummary {
  id: string;
  name: string;
  description?: string;
  genre?: string;
  artStyle?: string;
}

export interface InitBookPayload {
  templateId?: string;
  title?: string;
  art_styles?: string[];  // Multiple art styles selected by user
  user_requirements?: string;  // Optional seed/requirements text
}

export type ChapterSelection =
  | { kind: 'all' }
  | { kind: 'list'; chapters: number[] };

export interface GenerateChaptersPayload {
  workflowId: string;
  selection: ChapterSelection;
  continueFrom?: boolean;
  batchSize?: number;
}

export type PageSelection =
  | { kind: 'all' }
  | { kind: 'range'; from: number; to: number }
  | { kind: 'firstPerChapter'; count: number; chapters: 'all' | number[] };

export interface GeneratePagesPayload {
  workflowId: string;
  selection: PageSelection;
  continueFrom?: boolean;
}

export interface ApiClient {
  listWorkflows(): Promise<WorkflowSummary[]>;
  getWorkflow(jobId: string): Promise<WorkflowSummary | null>;
  listChapters(workflowId: string): Promise<ChapterSummary[]>;
  listPages(workflowId: string): Promise<PageSummary[]>;
  listCharacters(workflowId: string): Promise<CharacterSummary[]>;
  listTemplates(): Promise<StoryTemplateSummary[]>;
  initBook(payload: InitBookPayload): Promise<Job>;
  generateChapters(payload: GenerateChaptersPayload): Promise<Job>;
  generatePages(payload: GeneratePagesPayload): Promise<Job>;
}
