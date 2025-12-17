import React, { useEffect, useMemo, useState } from 'react';
import { useApi } from './api/ApiProvider';
import { GenerationBar } from './GenerationBar';
import type {
  ChapterSummary,
  PageSummary,
  StoryTemplateSummary,
  WorkflowSummary,
  CharacterSummary,
  ChapterSelection,
  PageSelection,
} from './api/ApiClient';

type MainTab = 'chapters' | 'pages';
type ViewMode = 'dashboard' | 'workflow';

export const App: React.FC = () => {
  const api = useApi();

  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [templates, setTemplates] = useState<StoryTemplateSummary[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [pages, setPages] = useState<PageSummary[]>([]);
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [activeTab, setActiveTab] = useState<MainTab>('chapters');
  const [selectedChapterForDetail, setSelectedChapterForDetail] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastJobType, setLastJobType] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [newTemplateId, setNewTemplateId] = useState<string | undefined>(undefined);

  // Helper to get count from array or number
  const getCount = (val: any): number => {
    if (Array.isArray(val)) return val.length;
    if (typeof val === 'number') return val;
    return 0;
  };

  const selectedWorkflow = useMemo(
    () => workflows.find((w) => w.id === selectedWorkflowId) ?? null,
    [workflows, selectedWorkflowId],
  );

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const [wf, tmpl] = await Promise.all([
          api.listWorkflows(),
          api.listTemplates(),
        ]);
        setWorkflows(wf);
        setTemplates(tmpl);
        if (wf.length > 0 && !selectedWorkflowId) {
          setSelectedWorkflowId(wf[0].id);
        }
      } finally {
        setIsLoading(false);
      }
    };
    void load();
  }, [api, selectedWorkflowId]);

  useEffect(() => {
    if (!selectedWorkflowId) {
      setChapters([]);
      setPages([]);
      setCharacters([]);
      return;
    }
    const load = async () => {
      setIsLoading(true);
      try {
        const [ch, pg, chars] = await Promise.all([
          api.listChapters(selectedWorkflowId),
          api.listPages(selectedWorkflowId),
          api.listCharacters(selectedWorkflowId),
        ]);
        setChapters(ch);
        setPages(pg);
        setCharacters(chars);
      } finally {
        setIsLoading(false);
      }
    };
    void load();
  }, [api, selectedWorkflowId]);

  const onCreateWorkflow = async () => {
    if (!newTitle.trim()) {
      return;
    }
    setIsLoading(true);
    try {
      const job = await api.initBook({
        title: newTitle.trim(),
        templateId: newTemplateId,
      });
      setLastJobType(job.type);
      const wf = await api.listWorkflows();
      setWorkflows(wf);
      setSelectedWorkflowId(job.workflowId);
      setNewTitle('');
      setNewTemplateId(undefined);
    } finally {
      setIsLoading(false);
    }
  };

  const onGenerateChaptersAll = async () => {
    if (!selectedWorkflowId) return;
    setIsLoading(true);
    try {
      const job = await api.generateChapters({
        workflowId: selectedWorkflowId,
        selection: { kind: 'all' },
      });
      setLastJobType(job.type);
    } finally {
      setIsLoading(false);
    }
  };

  const onGenerateChaptersBatch = async (batchSize: number) => {
    if (!selectedWorkflowId) return;
    setIsLoading(true);
    try {
      const job = await api.generateChapters({
        workflowId: selectedWorkflowId,
        selection: { kind: 'all' },
        batchSize,
      });
      setLastJobType(job.type);
    } finally {
      setIsLoading(false);
    }
  };

  const onGeneratePages = async () => {
    if (!selectedWorkflowId) return;
    setIsLoading(true);
    try {
      const job = await api.generatePages({
        workflowId: selectedWorkflowId,
        selection: { kind: 'all' },
      });
      setLastJobType(job.type);
    } finally {
      setIsLoading(false);
    }
  };

  const runChapters = async (args: {
    selection: ChapterSelection;
    batchSize?: number;
    continueFrom?: boolean;
  }) => {
    if (!selectedWorkflowId) return;
    setIsLoading(true);
    try {
      const job = await api.generateChapters({
        workflowId: selectedWorkflowId,
        selection: args.selection,
        batchSize: args.batchSize,
        continueFrom: args.continueFrom,
      });
      setLastJobType(job.type);
    } finally {
      setIsLoading(false);
    }
  };

  const runPages = async (args: { selection: PageSelection; continueFrom?: boolean }) => {
    if (!selectedWorkflowId) return;
    setIsLoading(true);
    try {
      const job = await api.generatePages({
        workflowId: selectedWorkflowId,
        selection: args.selection,
        continueFrom: args.continueFrom,
      });
      setLastJobType(job.type);
    } finally {
      setIsLoading(false);
    }
  };

  if (viewMode === 'dashboard') {
    // Backend already filters out incomplete workflows
    const featuredWorkflow = workflows[0];
    const recentWorkflows = workflows.slice(0, 6);
    
    return (
      <div className="min-h-screen flex flex-col">
        <header className="comic-header px-10 py-6 flex items-center justify-between">
          <h1 className="text-4xl">COMICS BOOK</h1>
          <span className="comic-badge px-3 py-1 rounded">
            {isLoading ? 'SYNCING…' : 'READY'}
          </span>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-[1fr,360px] gap-6 p-6 h-full">
            {/* Left: Hero + Content Rails */}
            <div className="flex flex-col gap-6">
              {/* Hero Section */}
              {featuredWorkflow ? (
                <div 
                  className="comic-card p-8 cursor-pointer transition-all"
                  onClick={() => window.location.href = `/workflow/${featuredWorkflow.id}`}
                >
                  <div className="flex items-start gap-6">
                    <div className="flex-shrink-0 w-48 h-64 border-4 border-[var(--ink)] rounded bg-gradient-to-br from-[var(--yellow)] to-[var(--orange)] flex items-center justify-center relative">
                      <div className="text-center">
                        <div className="text-6xl font-black">📖</div>
                        <div className="text-xs font-bold mt-2 tracking-wider uppercase">COVER</div>
                      </div>
                      {/* Show spinner for in-progress workflows */}
                      {(!featuredWorkflow.contentDone || !featuredWorkflow.storylineDone) && (
                        <div className="absolute top-3 right-3 w-8 h-8 bg-[var(--orange)] border-2 border-[var(--ink)] rounded-full flex items-center justify-center">
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--muted)' }}>Featured Workflow</div>
                      <h2 className="text-5xl font-black uppercase leading-tight mb-4">{featuredWorkflow.title}</h2>
                      <div className="flex gap-4 mb-4">
                        <div className="comic-badge px-3 py-1 rounded">
                          {featuredWorkflow.currentStage.toUpperCase()}
                        </div>
                        <div className="border-2 border-[var(--ink)] rounded px-3 py-1 text-xs font-bold uppercase">
                          {getCount(featuredWorkflow.chaptersGenerated)} CH
                        </div>
                        <div className="border-2 border-[var(--ink)] rounded px-3 py-1 text-xs font-bold uppercase">
                          {getCount(featuredWorkflow.pagesGenerated)} PG
                        </div>
                      </div>
                      <p className="text-base font-bold mb-6" style={{ color: 'var(--muted)' }}>
                        {(!featuredWorkflow.storylineDone || !featuredWorkflow.contentDone) 
                          ? 'Workflow is generating... Check back soon to continue working on your story.'
                          : 'Continue working on this storyline. Generate more chapters, refine pages, or export your comic book.'
                        }
                      </p>
                      <button
                        className="comic-button px-6 py-3 rounded text-sm"
                        onClick={() => window.location.href = `/workflow/${featuredWorkflow.id}`}
                      >
                        {(!featuredWorkflow.storylineDone || !featuredWorkflow.contentDone) ? 'VIEW PROGRESS →' : 'OPEN WORKFLOW →'}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="comic-card p-8">
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">📚</div>
                    <h2 className="text-3xl font-black uppercase mb-2">NO WORKFLOWS YET</h2>
                    <p className="text-base font-bold" style={{ color: 'var(--muted)' }}>Create your first book workflow using the panel on the right.</p>
                  </div>
                </div>
              )}

              {/* Recent Workflows Rail */}
              {workflows.length > 0 && (
                <div className="comic-card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-black uppercase tracking-wide">Your Stories</h3>
                    <span className="text-xs font-bold" style={{ color: 'var(--muted)' }}>{workflows.length} BOOKS</span>
                  </div>
                  <div className="grid grid-cols-4 gap-4">
                    {recentWorkflows.map((wf, idx) => {
                      const gradients = [
                        'from-purple-500 to-pink-500',
                        'from-blue-500 to-cyan-500',
                        'from-orange-500 to-red-500',
                        'from-green-500 to-teal-500',
                        'from-yellow-500 to-orange-500',
                        'from-indigo-500 to-purple-500',
                      ];
                      return (
                        <button
                          key={wf.id}
                          type="button"
                          onClick={() => window.location.href = `/workflow/${wf.id}`}
                          className="text-left transition-all hover:scale-105 relative"
                        >
                          <div className="aspect-[2/3] mb-3 relative">
                            <div className={`w-full h-full bg-gradient-to-br ${gradients[idx % gradients.length]} rounded-lg border-2 border-[var(--ink)] flex items-center justify-center shadow-md`}>
                              <div className="text-white text-4xl font-black">📖</div>
                            </div>
                            {/* Show spinner badge for in-progress workflows */}
                            {(!wf.contentDone || !wf.storylineDone) && (
                              <div className="absolute top-2 right-2 w-6 h-6 bg-[var(--orange)] border-2 border-[var(--ink)] rounded-full flex items-center justify-center">
                                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              </div>
                            )}
                          </div>
                          <div className="text-sm font-black uppercase leading-tight mb-1 line-clamp-2 min-h-[2.5rem]">{wf.title}</div>
                          <div className="flex gap-2 text-[10px] font-bold" style={{ color: 'var(--muted)' }}>
                            <span>{getCount(wf.chaptersGenerated)} CH</span>
                            <span>·</span>
                            <span>{getCount(wf.pagesGenerated)} PG</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Templates Rail */}
              {templates.length > 0 && (
                <div className="comic-card p-6">
                  <h3 className="text-lg font-black uppercase tracking-wide mb-4">Story Templates</h3>
                  <div className="flex gap-3 overflow-x-auto pb-2">
                    {templates.map((tmpl) => (
                      <div
                        key={tmpl.id}
                        className="flex-shrink-0 w-48 border-2 border-[var(--ink)] rounded bg-[var(--paper)] p-3 hover:border-[var(--orange)] transition-colors"
                      >
                        <div className="text-xs font-black uppercase mb-2">{tmpl.name}</div>
                        <div className="text-[10px] font-bold" style={{ color: 'var(--muted)' }}>{tmpl.genre}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right Sidebar: Create New */}
            <aside className="flex flex-col gap-4">
              <div className="comic-card p-6 sticky top-6 max-h-[calc(100vh-3rem)] overflow-y-auto">
                <h2 className="text-lg font-black uppercase tracking-wide mb-4">Create New Workflow</h2>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-bold uppercase tracking-wide mb-1 block">Title (Optional)</label>
                    <input
                      className="w-full px-3 py-2 border-2 border-[var(--ink)] rounded text-sm bg-white focus:outline-none focus:border-[var(--orange)]"
                      placeholder="Leave blank for auto-title..."
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold uppercase tracking-wide mb-1 block">Template</label>
                    <select
                      className="w-full px-3 py-2 border-2 border-[var(--ink)] rounded text-xs bg-white focus:outline-none focus:border-[var(--orange)]"
                      value={newTemplateId ?? ''}
                      onChange={(e) => setNewTemplateId(e.target.value || undefined)}
                    >
                      <option value="">No template</option>
                      {templates.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={onCreateWorkflow}
                    className="comic-button w-full py-3 rounded text-xs"
                  >
                    INIT WORKFLOW
                  </button>
                </div>
                
                <div className="mt-6 pt-4 border-t-2 border-[var(--ink)]">
                  <div className="font-bold mb-2 uppercase tracking-wide text-xs">Quick Start</div>
                  <ul className="space-y-1 text-[11px] font-bold" style={{ color: 'var(--muted)' }}>
                    <li>• Title is optional (auto-generated from story)</li>
                    <li>• Pick a template or start fresh</li>
                    <li>• Click to initialize workflow</li>
                    <li>• Begin generating content</li>
                  </ul>
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      <div
        className={`${
          isSidebarCollapsed ? 'w-10' : 'w-72'
        } border-r-4 border-[var(--ink)] bg-[var(--cream-dark)] p-2 flex flex-col h-screen overflow-y-auto transition-all duration-200`}
      >
        <div className="flex items-center justify-between mb-2">
          <button
            type="button"
            onClick={() => setIsSidebarCollapsed((v) => !v)}
            className="w-6 h-6 flex items-center justify-center border-2 border-[var(--ink)] rounded bg-[var(--paper)] hover:bg-[var(--orange)] text-xs font-bold"
          >
            {isSidebarCollapsed ? '»' : '«'}
          </button>
          {!isSidebarCollapsed && (
            <button
              type="button"
              onClick={() => setViewMode('dashboard')}
              className="ml-2 px-2 py-1 border-2 border-[var(--ink)] rounded bg-[var(--paper)] hover:bg-[var(--orange)] text-[10px] font-bold uppercase tracking-wide"
            >
              Dashboard
            </button>
          )}
        </div>

        <div className="space-y-2 mt-1">
          <h2 className="text-xs font-bold uppercase tracking-wide">Existing</h2>
          <div className="space-y-2 pr-1">
            {workflows.map((wf) => (
              <button
                key={wf.id}
                type="button"
                onClick={() => setSelectedWorkflowId(wf.id)}
                className={`w-full text-left px-3 py-2 border-2 border-[var(--ink)] rounded text-sm transition-colors ${
                  wf.id === selectedWorkflowId
                    ? 'bg-[var(--orange)] text-white'
                    : 'bg-[var(--paper)] hover:bg-[var(--cream)]'
                }`}
              >
                <div className="font-semibold truncate">{wf.title}</div>
                <div className="text-[10px] uppercase mt-1 flex justify-between">
                  <span>{wf.currentStage}</span>
                  <span>
                    Ch {getCount(wf.chaptersGenerated)} · Pg {getCount(wf.pagesGenerated)}
                  </span>
                </div>
              </button>
            ))}
            {workflows.length === 0 && (
              <div className="text-xs font-bold border-2 border-dashed border-[var(--ink)] rounded px-3 py-2 bg-[var(--paper)]" style={{ color: 'var(--muted)' }}>
                No workflows yet. Create one below.
              </div>
            )}
          </div>
        </div>

        <div className="mt-2 space-y-2">
          <h2 className="text-xs font-bold uppercase tracking-wide">New Storyline</h2>
          <input
            className="w-full px-2 py-1 border-2 border-[var(--ink)] rounded text-sm bg-white focus:outline-none focus:border-[var(--orange)]"
            placeholder="Story title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
          />
          <select
            className="w-full px-2 py-1 border-2 border-[var(--ink)] rounded text-xs bg-white focus:border-[var(--orange)]"
            value={newTemplateId ?? ''}
            onChange={(e) => setNewTemplateId(e.target.value || undefined)}
          >
            <option value="">No template</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={onCreateWorkflow}
            className="comic-button w-full py-2 rounded text-xs"
          >
            INIT WORKFLOW
          </button>
        </div>

        {lastJobType && (
          <div className="mt-auto text-[10px] border-t-2 border-[var(--ink)] pt-2 font-bold" style={{ color: 'var(--muted)' }}>
            Last job:
            <span className="ml-1">{lastJobType}</span>
          </div>
        )}
      </div>

      <div className="flex-1 flex flex-col p-6 gap-6">
        <div className="flex gap-6 h-[calc(100vh-3rem)]">
          <div className="flex-1 flex flex-col gap-4 comic-card p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-black uppercase tracking-tight">
                  {selectedWorkflow ? selectedWorkflow.title : 'Story Canvas'}
                </h2>
                {selectedWorkflow && (
                  <span className="comic-badge px-2 py-1 rounded text-xs">
                    {selectedWorkflow.currentStage.toUpperCase()}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setActiveTab('chapters')}
                  className={`px-4 py-2 border-2 font-bold text-xs uppercase transition-all ${
                    activeTab === 'chapters'
                      ? 'comic-button'
                      : 'border-[var(--ink)] bg-[var(--paper)] hover:bg-[var(--cream-dark)]'
                  }`}
                >
                  CHAPTERS
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('pages')}
                  className={`px-4 py-2 border-2 font-bold text-xs uppercase transition-all ${
                    activeTab === 'pages'
                      ? 'comic-button'
                      : 'border-[var(--ink)] bg-[var(--paper)] hover:bg-[var(--cream-dark)]'
                  }`}
                >
                  PAGES
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
                {activeTab === 'chapters' ? (
                  <div className="grid grid-cols-3 gap-4">
                    {chapters.map((ch) => {
                      const chapterPages = pages.filter((p) => p.chapterNumber === ch.chapterNumber);
                      const isSelected = selectedChapterForDetail === ch.chapterNumber;
                      return (
                        <div
                          key={ch.chapterNumber}
                          onClick={() => {
                            setSelectedChapterForDetail(ch.chapterNumber);
                            setActiveTab('pages');
                          }}
                          className={`cursor-pointer border-3 border-[var(--ink)] rounded p-4 transition-all ${
                            isSelected
                              ? 'bg-[var(--orange)] border-[var(--orange)]'
                              : 'bg-[var(--paper)] hover:border-[var(--orange)]'
                          }`}
                          style={{ aspectRatio: '2/3' }}
                        >
                          <div className="flex flex-col h-full">
                            <div className="text-xs font-black uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>
                              Chapter {ch.chapterNumber}
                            </div>
                            <div className="text-lg font-black uppercase leading-tight mb-auto">
                              {ch.title}
                            </div>
                            <div className="mt-4 pt-3 border-t-2 border-[var(--ink)] text-xs space-y-1 font-bold">
                              <div className="flex justify-between">
                                <span>Scenes:</span>
                                <span>{ch.scenes}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Pages:</span>
                                <span>{ch.pages}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Generated:</span>
                                <span>{chapterPages.length}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {chapters.length === 0 && (
                      <div className="col-span-3 text-center py-12 border-2 border-dashed border-[var(--ink)] rounded">
                        <p className="text-sm font-bold">No chapters yet.</p>
                        <p className="text-xs mt-1 font-bold" style={{ color: 'var(--muted)' }}>Use the generation controls in the sidebar to create chapters.</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col gap-3">
                    {/* Filter bar */}
                    {selectedChapterForDetail !== null && (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setSelectedChapterForDetail(null)}
                          className="px-3 py-1 border-2 border-[var(--ink)] rounded text-[10px] font-bold hover:bg-[var(--cream-dark)]"
                        >
                          7 All Chapters
                        </button>
                        <div className="text-xs font-black">Showing Chapter {selectedChapterForDetail}</div>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3">
                      {pages
                        .filter((pg) => selectedChapterForDetail === null || pg.chapterNumber === selectedChapterForDetail)
                        .map((pg, idx) => (
                          <div
                            key={`${pg.chapterNumber}-${pg.sceneNumber}-${pg.number}-${idx}`}
                            className="border-2 border-[var(--ink)] rounded bg-[var(--paper)] px-4 py-3 text-xs flex flex-col gap-2"
                          >
                            <div className="font-black text-sm uppercase">
                              Page {pg.number ?? idx + 1}
                            </div>
                            <div className="text-[10px] font-bold space-x-2" style={{ color: 'var(--muted)' }}>
                              <span>CH {pg.chapterNumber}</span>
                              <span> B7</span>
                              <span>SC {pg.sceneNumber}</span>
                            </div>
                            {pg.description && (
                              <div className="line-clamp-3 text-[11px] font-bold" style={{ color: 'var(--muted)' }}>
                                {pg.description}
                              </div>
                            )}
                          </div>
                        ))}

                      {pages.filter((pg) => selectedChapterForDetail === null || pg.chapterNumber === selectedChapterForDetail).length === 0 && (
                        <div className="col-span-2 text-center py-12 border-2 border-dashed border-[var(--ink)] rounded">
                          <p className="text-sm font-bold">No pages yet.</p>
                          <p className="text-xs mt-1 font-bold" style={{ color: 'var(--muted)' }}>Generate pages to see panel prompts.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
            </div>
          </div>

          <div className="w-80 flex flex-col gap-4">
            <div className="comic-card p-4">
              <h3 className="text-sm font-black uppercase tracking-wide mb-3">Generation Controls</h3>
              <GenerationBar
                mode={activeTab === 'pages' ? 'pages' : 'chapters'}
                onModeChange={(m) => setActiveTab(m === 'pages' ? 'pages' : 'chapters')}
                disabled={!selectedWorkflowId || isLoading}
                onRunChapters={(args) => {
                  void runChapters(args);
                }}
                onRunPages={(args) => {
                  void runPages(args);
                }}
              />
            </div>
            <div className="flex-1 comic-card p-4 text-xs space-y-3 overflow-auto">
              <h3 className="text-sm font-black uppercase tracking-wide">Inspector</h3>
              {selectedWorkflow ? (
                <>
                  <div>
                    <div className="font-bold text-xs mb-1 uppercase">Workflow</div>
                    <div className="space-y-0.5 text-[11px] font-bold" style={{ color: 'var(--muted)' }}>
                      <div>
                        <span className="font-black">ID:</span> {selectedWorkflow.id}
                      </div>
                      <div>
                        <span className="font-black">Stage:</span> {selectedWorkflow.currentStage}
                      </div>
                      <div>
                        <span className="font-black">Chapters:</span> {getCount(selectedWorkflow.chaptersGenerated)}
                      </div>
                      <div>
                        <span className="font-black">Pages:</span> {getCount(selectedWorkflow.pagesGenerated)}
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-dotted border-[var(--ink)]">
                    <div className="font-bold text-xs mb-1 uppercase">Template</div>
                    {selectedWorkflow.templateId ? (
                      (() => {
                        const tmpl = templates.find((t) => t.id === selectedWorkflow.templateId);
                        if (!tmpl) return <div className="text-[11px] font-bold" style={{ color: 'var(--muted)' }}>Unknown template.</div>;
                        return (
                          <div className="space-y-0.5 text-[11px] font-bold" style={{ color: 'var(--muted)' }}>
                            <div className="font-black">{tmpl.name}</div>
                            {tmpl.genre && (
                              <div>
                                <span className="font-black">Genre:</span> {tmpl.genre}
                              </div>
                            )}
                            {tmpl.artStyle && (
                              <div>
                                <span className="font-black">Art Style:</span> {tmpl.artStyle}
                              </div>
                            )}
                            {tmpl.description && (
                              <div className="text-[10px] mt-1">{tmpl.description}</div>
                            )}
                          </div>
                        );
                      })()
                    ) : (
                      <div className="text-[11px] font-bold" style={{ color: 'var(--muted)' }}>No template associated.</div>
                    )}
                  </div>

                  <div className="pt-2 border-t border-dotted border-[var(--ink)]">
                    <div className="font-bold text-xs mb-1 uppercase">Characters</div>
                    {characters.length > 0 ? (
                      <div className="space-y-0.5 max-h-32 overflow-y-auto text-[11px] font-bold" style={{ color: 'var(--muted)' }}>
                        {characters.map((c) => (
                          <div key={c.id} className="flex items-center justify-between">
                            <span className="font-black">{c.name}</span>
                            <span className="text-[10px] uppercase">{c.role}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-[11px] font-bold" style={{ color: 'var(--muted)' }}>
                        No character data loaded yet.
                      </div>
                    )}
                  </div>

                  {selectedChapterForDetail !== null && (
                    <div className="pt-2 border-t border-dotted border-[var(--ink)]">
                      <div className="font-bold text-xs mb-1 uppercase">Selected Chapter</div>
                      <div className="text-[11px] font-bold" style={{ color: 'var(--muted)' }}>
                        {(() => {
                          const ch = chapters.find((c) => c.chapterNumber === selectedChapterForDetail);
                          if (!ch) return null;
                          const chPages = pages.filter((p) => p.chapterNumber === ch.chapterNumber);
                          return (
                            <div className="space-y-1">
                              <div className="font-black">Chapter {ch.chapterNumber}: {ch.title}</div>
                              <div>Scenes: {ch.scenes}</div>
                              <div>Pages: {ch.pages}</div>
                              <div>Generated: {chPages.length}</div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-xs font-bold" style={{ color: 'var(--muted)' }}>
                  Select or create a workflow to inspect storyline, template, and generation controls.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
