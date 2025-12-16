import type { 
  ApiClient, 
  WorkflowSummary, 
  ChapterSummary, 
  PageSummary, 
  CharacterSummary,
  StoryTemplateSummary,
  Job,
  InitBookPayload,
  GenerateChaptersPayload,
  GeneratePagesPayload
} from './ApiClient';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class RealApiClient implements ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async listWorkflows(): Promise<WorkflowSummary[]> {
    return this.fetch<WorkflowSummary[]>('/workflows');
  }

  async getWorkflow(id: string): Promise<WorkflowSummary | null> {
    try {
      return await this.fetch<WorkflowSummary>(`/workflows/${id}`);
    } catch {
      return null;
    }
  }

  async listTemplates(): Promise<StoryTemplateSummary[]> {
    // Templates endpoint doesn't exist yet, return empty array
    return Promise.resolve([]);
  }

  async initBook(payload: InitBookPayload): Promise<Job> {
    return this.fetch<Job>('/workflows/book/init', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async generateChapters(payload: GenerateChaptersPayload): Promise<Job> {
    return this.fetch<Job>(`/workflows/book/${payload.workflowId}/chapters`, {
      method: 'POST',
      body: JSON.stringify({
        selection: payload.selection,
        continueFrom: payload.continueFrom,
        batchSize: payload.batchSize,
      }),
    });
  }

  async generatePages(payload: GeneratePagesPayload): Promise<Job> {
    return this.fetch<Job>(`/workflows/book/${payload.workflowId}/pages`, {
      method: 'POST',
      body: JSON.stringify({
        selection: payload.selection,
        continueFrom: payload.continueFrom,
      }),
    });
  }


  async listChapters(workflowId: string): Promise<ChapterSummary[]> {
    return this.fetch<ChapterSummary[]>(`/workflows/${workflowId}/chapters`);
  }

  async listPages(workflowId: string): Promise<PageSummary[]> {
    // The backend returns: { number, chapterNumber, sceneNumber, pageInScene, description, imageUrl }
    // Map to PageSummary shape used by UI
    const raw = await this.fetch<any[]>(`/workflows/${workflowId}/pages`);
    return raw.map((p) => ({
      chapterNumber: p.chapterNumber,
      sceneNumber: p.sceneNumber,
      pageNumber: p.pageInScene ?? p.number,
      globalIndex: p.number,
      prompt: p.description,
    }));
  }

  async listCharacters(workflowId: string): Promise<CharacterSummary[]> {
    try {
      const response = await this.fetch<{ [key: string]: CharacterSummary }>(
        `/workflows/${workflowId}/characters`
      );
      return Object.values(response);
    } catch {
      return [];
    }
  }
}
