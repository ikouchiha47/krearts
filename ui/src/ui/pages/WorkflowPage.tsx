import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useApi } from '../api/ApiProvider';
import { ChapterSelection, PageSelection, GenerateChaptersPayload, GeneratePagesPayload } from '../api/ApiClient';
import ReactMarkdown from 'react-markdown';
import { useJobPoller } from '../hooks/useJobPoller';
import { WorkflowProgressBar } from '../components/WorkflowProgressBar';
import { RunningJobProgress } from '../components/RunningJobProgress';
import { WorkflowConfig } from '../components/WorkflowConfig';
import { GenerationControls } from '../components/GenerationControls';

type ViewTab = 'story' | 'plot' | 'pages' | 'timeline' | 'graph';

export const WorkflowPage: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const api = useApi();
  const [activeTab, setActiveTab] = useState<ViewTab>('story');
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null);
  const [workflow, setWorkflow] = useState<any>(null);
  const [chapters, setChapters] = useState<any[]>([]);
  const [pages, setPages] = useState<any[]>([]);
  const [characters, setCharacters] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [charJobId, setCharJobId] = useState<string | null>(null);
  const [lastSeenChapters, setLastSeenChapters] = useState<number[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Poll for character generation job status
  const charJobStatus = useJobPoller({
    workflowId: workflowId || '',
    jobType: charJobId || '',
    enabled: isGenerating && !!charJobId,
    onComplete: () => {
      setIsGenerating(false);
      // Reload characters
      if (workflowId) {
        api.listCharacters(workflowId).then(setCharacters);
      }
    },
    onError: (error) => {
      setIsGenerating(false);
      alert(`Character generation failed: ${error}`);
    },
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (workflowId) {
      loadWorkflowData();
    }
  }, [workflowId]);

  const handleJobProgress = useCallback((job: any) => {
    const currentChapters = job.metadata?.chapters_generated || [];
    
    // Detect new chapters by comparing arrays
    const newChapters = currentChapters.filter(
      (ch: number) => !lastSeenChapters.includes(ch)
    );
    
    if (newChapters.length > 0) {
      console.log(`[Polling] New chapters detected: ${newChapters.join(', ')}`);
      console.log(`[Polling] Previous chapters: ${lastSeenChapters.join(', ')}`);
      console.log(`[Polling] Current chapters: ${currentChapters.join(', ')}`);
      
      // Update last seen state
      setLastSeenChapters(currentChapters);
      
      // Trigger data refresh to get new chapters/pages
      console.log('[Polling] Triggering data refresh');
      loadWorkflowData();
    }
  }, [lastSeenChapters]);

  const loadWorkflowData = async () => {
    if (!workflowId) return;
    
    // Prevent overlapping refreshes
    if (isRefreshing) {
      console.log('[Polling] Refresh already in progress, skipping');
      return;
    }
    
    setIsRefreshing(true);
    try {
      setLoading(true);
      const [wf, chs, pgs, chars] = await Promise.all([
        api.getWorkflow(workflowId),
        api.listChapters(workflowId).catch(() => []),
        api.listPages(workflowId).catch(() => []),
        api.listCharacters(workflowId).catch(() => []),
      ]);
      setWorkflow(wf);
      setChapters(chs);
      setPages(pgs);
      setCharacters(chars);

      // Check DB for an already-running character generation job and resume polling
      try {
        const resp = await fetch(
          `http://localhost:8000/workflows/${workflowId}/jobs?type=character_generation&status=running`
        );
        if (resp.ok) {
          const jobs = await resp.json();
          if (Array.isArray(jobs) && jobs.length > 0) {
            setIsGenerating(true);
            setCharJobId(jobs[0].id);
          }
        }
      } catch (e) {
        // ignore job lookup errors; UI can still start a new job
        console.warn('Job lookup failed', e);
      }
    } catch (err) {
      console.error('Failed to load workflow:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRunChapters = async (args: { selection: ChapterSelection; batchSize?: number; continueFrom?: boolean }) => {
    if (!workflowId) return;
    
    try {
      const payload: GenerateChaptersPayload = {
        workflowId,
        selection: args.selection,
        continueFrom: args.continueFrom,
        batchSize: args.batchSize,
      };
      
      const job = await api.generateChapters(payload);
      alert(`✓ Chapter generation started\nJob ID: ${job.id}`);
      loadWorkflowData();
    } catch (error) {
      alert(`Failed to start chapter generation: ${error}`);
    }
  };

  const handleRunPages = async (args: { selection: PageSelection; continueFrom?: boolean }) => {
    if (!workflowId) return;
    
    try {
      const payload: GeneratePagesPayload = {
        workflowId,
        selection: args.selection,
        continueFrom: args.continueFrom,
      };
      
      const job = await api.generatePages(payload);
      alert(`✓ Page generation started\nJob ID: ${job.id}`);
      loadWorkflowData();
    } catch (error) {
      alert(`Failed to start page generation: ${error}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-black uppercase tracking-wider">Loading...</div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-black text-[var(--red)]">Workflow not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="comic-header px-10 py-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="text-[var(--cream)] hover:text-[var(--orange)] p-2 rounded-lg transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <strong className="text-3xl uppercase">{workflow.title}</strong>
          <span className="comic-badge px-3 py-1 rounded">
            {workflow.currentStage.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* Continue button - only show if workflow can continue */}
          {workflow.currentStage !== 'pages' && (
            <button
              onClick={async () => {
                try {
                  const response = await fetch(`http://localhost:8000/workflows/${workflowId}/continue`, {
                    method: 'POST',
                  });
                  const data = await response.json();
                  if (response.ok) {
                    alert(`✓ ${data.message}\nJob ID: ${data.job_id}`);
                    loadWorkflowData();
                  } else {
                    alert(`✗ ${data.detail || 'Failed to continue workflow'}`);
                  }
                } catch (error) {
                  alert('Failed to continue workflow');
                }
              }}
              disabled={!workflow.storylineDone && workflow.currentStage === 'init'}
              className="px-4 py-2 text-xs font-bold uppercase border-2 border-[var(--ink)] rounded hover:bg-[var(--orange)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <span className="text-lg">▶</span> Continue
            </button>
          )}
          
          {/* Retry Stage Dropdown */}
          <div className="relative">
            <select
              onChange={async (e) => {
                const stage = e.target.value;
                if (!stage) return;
                
                const stageLabels: Record<string, string> = {
                  'init': 'Plot generation',
                  'content': 'Novel generation',
                  'chapters': 'Chapters',
                  'pages': 'Pages'
                };
                
                const stageName = stage === 'current' ? workflow.currentStage : stage;
                const label = stageLabels[stageName] || stageName;
                
                if (!confirm(`Reset workflow to ${label}? This will abort current jobs and restart from this stage.`)) {
                  e.target.value = '';
                  return;
                }
                
                try {
                  const body = stage === 'current' ? {} : { stage };
                  const response = await fetch(`http://localhost:8000/workflows/${workflowId}/retry-stage`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                  });
                  const data = await response.json();
                  if (response.ok) {
                    alert(`✓ ${data.message}\nJob ID: ${data.new_job_id}`);
                    loadWorkflowData();
                  } else {
                    alert(`✗ ${data.detail || 'Failed to retry stage'}`);
                  }
                } catch (error) {
                  alert('Failed to retry stage');
                }
                e.target.value = '';
              }}
              className="px-4 py-2 text-xs font-bold uppercase text-[var(--ink)] bg-[var(--paper)] border-2 border-[var(--ink)] rounded hover:bg-[var(--red)] hover:text-[var(--paper)] transition-colors cursor-pointer"
              defaultValue=""
            >
              <option value="" disabled>🔄 Retry Stage...</option>
              <option value="current">
                🔄 {workflow.currentStage === 'init' ? 'Plot' : 
                     workflow.currentStage === 'content' ? 'Novel' : 
                     workflow.currentStage === 'chapters' ? 'Chapters' : 
                     workflow.currentStage === 'pages' ? 'Pages' : 
                     workflow.currentStage.toUpperCase()} (Current)
              </option>
              <option value="init">📝 Plot</option>
              <option value="content">📚 Novel</option>
              <option value="chapters">📖 Chapters</option>
              <option value="pages">🎨 Pages</option>
            </select>
          </div>
          <div className="text-sm font-bold uppercase tracking-wide">
            {chapters.length} CH · {pages.length} PG
          </div>
        </div>
      </header>

      {/* Progress Timeline */}
      <WorkflowProgressBar stages={workflow.stages || []} />

      {/* Running Job Progress Banner */}
      <RunningJobProgress 
        workflowId={workflowId || ''} 
        onComplete={loadWorkflowData}
        onProgress={handleJobProgress}
      />

      <div className="grid grid-cols-[260px_1fr_320px] h-[calc(100vh-80px)]">
        {/* LEFT SIDEBAR - Chapters */}
        <aside className="bg-[var(--cream-dark)] border-r-4 border-[var(--ink)] p-4 overflow-y-auto">
          <h3 className="text-sm font-black uppercase tracking-wider mb-3">CHAPTERS</h3>
          
          {/* Config Panel - show when plot is done but novel not started yet */}
          {workflow.storyline && workflow.currentStage === 'content' && !workflow.screenplay && (
            <div className="bg-[var(--paper)] border-2 border-[var(--ink)] rounded p-3 mb-4">
              <WorkflowConfig
                disabled={false}
                onSave={async (config) => {
                  try {
                    const response = await fetch(`http://localhost:8000/workflows/book/${workflowId}/comic-config`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        total_chapters: config.totalChapters,
                        pages_per_chapter: config.pagesPerChapter,
                      }),
                    });
                    
                    if (response.ok) {
                      alert(`✓ Settings saved!\n${config.totalChapters} chapters\n${config.pagesPerChapter} pages per chapter\n\nClick Continue to proceed with novel generation.`);
                    } else {
                      const data = await response.json();
                      alert(`✗ Failed to save: ${data.detail || 'Unknown error'}`);
                    }
                  } catch (error) {
                    alert(`✗ Failed to save settings: ${error}`);
                  }
                }}
              />
            </div>
          )}
          
          {/* Generation Controls - show when chapters exist and we can generate pages */}
          {(workflow.currentStage === 'chapters' || workflow.currentStage === 'pages') && chapters.length > 0 && (
            <div className="bg-[var(--paper)] border-2 border-[var(--ink)] rounded p-3 mb-4">
              <GenerationControls
                stage={workflow.currentStage}
                disabled={false}
                onRunChapters={handleRunChapters}
                onRunPages={handleRunPages}
              />
            </div>
          )}
          {(() => {
            // Get expected chapter count from novel (default 15)
            const expectedChapters = workflow?.screenplay ? 15 : 0;
            if (expectedChapters === 0) {
              return <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>No chapters yet</div>;
            }
            
            // Create map of existing chapters
            const chapterMap = new Map(chapters.map(ch => [ch.chapterNumber, ch]));
            
            // Render all expected chapters (existing + missing)
            return Array.from({ length: expectedChapters }, (_, i) => {
              const chapterNum = i + 1;
              const chapter = chapterMap.get(chapterNum);
              const isMissing = !chapter;
              
              return (
                <div
                  key={chapterNum}
                  onClick={() => {
                    if (!isMissing) {
                      setSelectedChapter(chapterNum);
                      setActiveTab('pages');
                    }
                  }}
                  className={`rounded border-2 mb-3 transition-all overflow-hidden ${
                    isMissing 
                      ? 'border-[var(--red)] border-dashed opacity-60'
                      : selectedChapter === chapterNum
                        ? 'border-[var(--orange)] ring-2 ring-[var(--orange)] ring-opacity-50 cursor-pointer'
                        : 'border-[var(--ink)] hover:border-[var(--orange)] cursor-pointer'
                  }`}
                >
                  {/* Chapter preview */}
                  <div className={`h-32 flex items-center justify-center ${
                    isMissing 
                      ? 'bg-gradient-to-br from-red-900 to-red-950' 
                      : 'bg-gradient-to-br from-slate-700 to-slate-900'
                  }`}>
                    <div className="text-6xl font-black opacity-20">{chapterNum}</div>
                    {isMissing && (
                      <div className="absolute text-2xl">❌</div>
                    )}
                  </div>
                  
                  {/* Chapter info */}
                  <div className="p-3 bg-[var(--paper)]">
                    <div className="text-xs font-black uppercase mb-1" style={{ 
                      color: isMissing ? 'var(--red)' : 'var(--orange)' 
                    }}>
                      Chapter {chapterNum} {isMissing && '(FAILED)'}
                    </div>
                    {isMissing ? (
                      <>
                        <div className="text-sm font-bold leading-tight mb-2" style={{ color: 'var(--red)' }}>
                          Generation Failed
                        </div>
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            if (!confirm(`Regenerate Chapter ${chapterNum}?`)) return;
                            try {
                              const response = await fetch(`http://localhost:8000/workflows/book/${workflowId}/chapters`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ chapters: String(chapterNum) }),
                              });
                              const data = await response.json();
                              if (response.ok) {
                                alert(`✓ Started regeneration\nJob: ${data.id}`);
                                loadWorkflowData();
                              } else {
                                alert(`✗ ${data.detail}`);
                              }
                            } catch (error) {
                              alert('Failed to start regeneration');
                            }
                          }}
                          className="w-full px-2 py-1 text-xs font-bold uppercase bg-[var(--red)] text-[var(--paper)] border-2 border-[var(--ink)] rounded hover:bg-[var(--orange)] transition-colors"
                        >
                          🔄 Regenerate
                        </button>
                      </>
                    ) : (
                      <>
                        <div className="text-sm font-bold leading-tight mb-2">
                          {chapter.title || 'Untitled'}
                        </div>
                        <div className="text-xs font-bold" style={{ color: 'var(--muted)' }}>
                          {chapter.scenes || 0} scenes · {chapter.pages || 0} pages
                        </div>
                      </>
                    )}
                  </div>
                </div>
              );
            });
          })()}
        </aside>

        {/* CENTER CANVAS */}
        <main className="p-6 overflow-y-auto">
          {/* View Tabs */}
          <div className="flex gap-2 mb-6 border-b-2 border-[var(--ink)] pb-2">
            {(['plot', 'story', 'pages', 'timeline', 'graph'] as ViewTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 text-sm font-black uppercase tracking-wide border-2 rounded transition-all ${
                  activeTab === tab
                    ? 'bg-[var(--orange)] border-[var(--orange)] text-[var(--ink)]'
                    : 'border-[var(--ink)] bg-[var(--paper)] hover:bg-[var(--cream-dark)]'
                }`}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Story View - Show screenplay (novel) content only */}
          {activeTab === 'story' && (
            <div className="p-6">
              {workflow.screenplay ? (
                <div className="prose prose-sm max-w-none leading-relaxed">
                  <ReactMarkdown
                    components={{
                      h1: ({node, ...props}) => <h1 className="text-3xl font-black uppercase mb-4" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-2xl font-black uppercase mb-3 mt-6" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-xl font-bold uppercase mb-2 mt-4" {...props} />,
                      p: ({node, ...props}) => <p className="mb-4 leading-relaxed" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc ml-6 mb-4" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal ml-6 mb-4" {...props} />,
                      li: ({node, ...props}) => <li className="mb-1" {...props} />,
                      strong: ({node, ...props}) => <strong className="font-black" {...props} />,
                    }}
                  >
                    {workflow.screenplay}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-lg font-black uppercase mb-2">No Screenplay Yet</div>
                  <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>
                    The novel/screenplay will appear here after content generation completes.
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Plot View - Show storyline (detective structure) */}
          {activeTab === 'plot' && (
            <div className="p-6">
              {workflow.storyline ? (
                <div className="prose prose-sm max-w-none leading-relaxed">
                  <ReactMarkdown
                    components={{
                      h1: ({node, ...props}) => <h1 className="text-3xl font-black uppercase mb-4" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-2xl font-black uppercase mb-3 mt-6" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-xl font-bold uppercase mb-2 mt-4" {...props} />,
                      p: ({node, ...props}) => <p className="mb-4 leading-relaxed" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc ml-6 mb-4" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal ml-6 mb-4" {...props} />,
                      li: ({node, ...props}) => <li className="mb-1" {...props} />,
                      strong: ({node, ...props}) => <strong className="font-black" {...props} />,
                    }}
                  >
                    {workflow.storyline}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-lg font-black uppercase mb-2">No Plotline Yet</div>
                  <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>
                    The detective story structure will appear here after plot generation completes.
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Pages View */}
          {activeTab === 'pages' && (
            <div>
              {selectedChapter && (
                <div className="mb-4 flex items-center gap-2">
                  <button
                    onClick={() => setSelectedChapter(null)}
                    className="px-3 py-1 text-xs font-bold border-2 border-[var(--ink)] rounded hover:bg-[var(--cream-dark)]"
                  >
                    ← All Chapters
                  </button>
                  <span className="text-sm font-black">
                    Showing Chapter {selectedChapter}
                  </span>
                </div>
              )}
              
              <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-4">
                {pages
                  .filter(page => !selectedChapter || page.chapterNumber === selectedChapter)
                  .map((page, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden cursor-pointer hover:border-amber-500 transition-colors"
                >
                  <div className="h-40 flex items-center justify-center text-4xl bg-indigo-400">
                    {page.number || idx + 1}
                  </div>
                  <div className="p-2.5 text-xs text-slate-400">
                    Scene {page.scene || 1} · Page {page.number || idx + 1}
                  </div>
                </div>
              ))}
              
                {pages.filter(page => !selectedChapter || page.chapterNumber === selectedChapter).length === 0 && (
                  <div className="col-span-full text-center py-12 text-slate-500">
                    No pages generated yet
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Timeline View */}
          {activeTab === 'timeline' && (
            <div className="comic-card p-6">
              {/* Progress Stats */}
              <div className="flex justify-between items-center mb-6 pb-6 border-b-2 border-[var(--ink)]">
                <h2 className="text-2xl font-black uppercase">Generation Progress</h2>
                <div className="flex gap-8">
                  <div className="text-center">
                    <div className="text-4xl font-black" style={{ color: 'var(--orange)' }}>
                      {workflow.chaptersGenerated?.length || 0}/{workflow.totalChapters || 0}
                    </div>
                    <div className="text-xs font-bold uppercase tracking-wide mt-1" style={{ color: 'var(--muted)' }}>
                      Chapters
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-black" style={{ color: 'var(--orange)' }}>
                      {workflow.pagesGenerated?.length || 0}/{workflow.totalPages || 0}
                    </div>
                    <div className="text-xs font-bold uppercase tracking-wide mt-1" style={{ color: 'var(--muted)' }}>
                      Pages
                    </div>
                  </div>
                </div>
              </div>

              {/* GitHub-Style Activity Grid */}
              <div className="space-y-4">
                {(() => {
                  const expectedChapters = workflow?.screenplay ? 15 : 0;
                  if (expectedChapters === 0) {
                    return (
                      <div className="text-center py-12 border-2 border-dashed border-[var(--ink)] rounded">
                        <div className="text-lg font-black uppercase mb-2">No chapters yet.</div>
                        <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>
                          Use the generation controls in the sidebar to create chapters.
                        </div>
                      </div>
                    );
                  }
                  
                  const chapterMap = new Map(chapters.map(ch => [ch.chapterNumber, ch]));
                  
                  return Array.from({ length: expectedChapters }, (_, idx) => {
                    const chapterNum = idx + 1;
                    const chapter = chapterMap.get(chapterNum);
                    const isMissing = !chapter;
                    if (isMissing) {
                      // Failed chapter
                      return (
                        <div key={idx} className="bg-red-950 border-2 border-[var(--red)] border-dashed rounded p-4 opacity-75">
                          <div className="flex justify-between items-center mb-3">
                            <div className="font-black text-sm uppercase" style={{ color: 'var(--red)' }}>
                              ❌ Chapter {chapterNum}: GENERATION FAILED
                            </div>
                            <button
                              onClick={async () => {
                                if (!confirm(`Regenerate Chapter ${chapterNum}?`)) return;
                                try {
                                  const response = await fetch(`http://localhost:8000/workflows/book/${workflowId}/chapters`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ chapters: String(chapterNum) }),
                                  });
                                  const data = await response.json();
                                  if (response.ok) {
                                    alert(`✓ Started regeneration\nJob: ${data.id}`);
                                    loadWorkflowData();
                                  } else {
                                    alert(`✗ ${data.detail}`);
                                  }
                                } catch (error) {
                                  alert('Failed');
                                }
                              }}
                              className="px-3 py-1 text-xs font-bold uppercase bg-[var(--red)] text-[var(--paper)] border-2 border-[var(--ink)] rounded hover:bg-[var(--orange)] transition-colors"
                            >
                              🔄 Regenerate
                            </button>
                          </div>
                          <div className="text-xs font-bold" style={{ color: 'var(--red)' }}>
                            This chapter failed validation during generation. Click regenerate to retry.
                          </div>
                        </div>
                      );
                    }
                    
                    // Successful chapter
                    const totalPagesInChapter = chapter.pages || 0;
                    const pagesGenerated = workflow.pagesGenerated || [];
                    const startPage = Array.from({ length: idx }).reduce((sum: number, _, i) => {
                      const ch = chapterMap.get(i + 1);
                      return sum + (ch?.pages || 0);
                    }, 0) + 1;
                    
                    return (
                      <div key={idx} className="bg-[var(--cream-dark)] border-2 border-[var(--ink)] rounded p-4">
                        <div className="flex justify-between items-center mb-3">
                          <div className="font-black text-sm uppercase">
                            Chapter {chapterNum}: {chapter.title || 'Untitled'}
                          </div>
                          <div className="text-xs font-bold" style={{ color: 'var(--muted)' }}>
                            {Array.from({ length: totalPagesInChapter }).filter((_, i) => 
                              pagesGenerated.includes(startPage + i)
                            ).length} / {totalPagesInChapter} pages
                          </div>
                        </div>
                        
                        {/* Page boxes - GitHub style */}
                        <div className="flex gap-1 flex-wrap">
                          {Array.from({ length: totalPagesInChapter }).map((_, i) => {
                            const pageNum = startPage + i;
                            const isGenerated = pagesGenerated.includes(pageNum);
                            
                            return (
                              <div
                                key={i}
                                className={`w-5 h-5 rounded border-2 transition-all ${
                                  isGenerated
                                    ? 'bg-[var(--orange)] border-[var(--orange)]'
                                    : 'bg-[var(--paper)] border-[var(--ink)]'
                                }`}
                                title={`Page ${pageNum}${isGenerated ? ' (generated)' : ' (pending)'}`}
                              />
                            );
                          })}
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            </div>
          )}

          {/* Story Graph View */}
          {activeTab === 'graph' && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 relative h-[520px]">
              <div className="absolute top-10 left-[40%] bg-slate-950 border-2 border-amber-500 rounded-xl p-3 min-w-[160px] text-center">
                <div className="font-bold text-slate-200">Main Story</div>
                <div className="text-xs text-slate-500 mt-1">{workflow.title}</div>
              </div>
              
              {chapters.slice(0, 3).map((chapter, idx) => (
                <div
                  key={idx}
                  className="absolute bg-slate-950 border-2 border-cyan-400 rounded-xl p-3 min-w-[160px] text-center"
                  style={{
                    top: `${180}px`,
                    left: `${20 + idx * 25}%`,
                  }}
                >
                  <div className="font-bold text-slate-200">
                    Chapter {chapter.number || idx + 1}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    {chapter.title || 'Untitled'}
                  </div>
                </div>
              ))}
              
              {chapters.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                  No story graph available
                </div>
              )}
            </div>
          )}
        </main>

        {/* RIGHT SIDEBAR - Characters */}
        <aside className="bg-[var(--cream-dark)] border-l-4 border-[var(--ink)] p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-black uppercase tracking-wider">CHARACTERS</h3>
            {characters.length > 0 && (
              <div className="flex gap-2">
                <button
                  className={`px-2 py-1 text-[10px] font-bold uppercase border-2 border-[var(--ink)] rounded transition-colors flex items-center gap-1 ${
                    isGenerating ? 'bg-[var(--yellow)] cursor-wait' : 'hover:bg-[var(--orange)]'
                  }`}
                  disabled={isGenerating}
                  onClick={async () => {
                    try {
                      setIsGenerating(true);
                      const response = await fetch(`http://localhost:8000/workflows/${workflowId}/characters/generate`, {
                        method: 'POST',
                      });
                      const data = await response.json();
                      if (data.status === 'already_running') {
                        // Resume polling the existing job
                        setCharJobId(data.id);
                      } else {
                        setCharJobId(data.id);
                      }
                    } catch (error) {
                      setIsGenerating(false);
                      alert('Failed to start character generation');
                    }
                  }}
                  title="Generate all characters"
                >
                  {isGenerating ? (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                      </svg>
                      <span>Generate</span>
                    </>
                  )}
                </button>
                <button
                  className="px-2 py-1 text-[10px] font-bold uppercase border-2 border-[var(--ink)] rounded hover:bg-[var(--red)] transition-colors flex items-center gap-1"
                  onClick={async () => {
                    try {
                      setIsGenerating(true);
                      const response = await fetch(`http://localhost:8000/workflows/${workflowId}/characters/retry`, {
                        method: 'POST',
                      });
                      const data = await response.json();
                      setCharJobId(data.id);
                      console.log('Retry response:', data);
                    } catch (error) {
                      setIsGenerating(false);
                      alert('Failed to retry');
                    }
                  }}
                  title="Retry all characters"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Retry</span>
                </button>
              </div>
            )}
          </div>
          <div className="space-y-4">
            {characters.length === 0 ? (
              <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>No character data loaded yet</div>
            ) : (
              characters.map((char, idx) => (
                <div key={idx} className="bg-[var(--paper)] border-2 border-[var(--ink)] rounded overflow-hidden relative">
                  {/* Character portrait */}
                  <div className="relative h-48 bg-gradient-to-br from-orange-900 to-red-900 flex items-center justify-center">
                    {char.imageUrl ? (
                      <img
                        src={char.imageUrl}
                        alt={char.name}
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="text-6xl font-black opacity-30">
                        {char.name?.charAt(0) || '?'}
                      </div>
                    )}
                    
                    {/* Regenerate button */}
                    <button
                      onClick={async () => {
                        if (!confirm(`Regenerate image for ${char.name}?`)) return;
                        try {
                          const response = await fetch(`/workflows/${workflowId}/characters/${char.id}/regenerate`, {
                            method: 'POST'
                          });
                          if (response.ok) {
                            alert(`Regenerating ${char.name}...`);
                            // Refresh characters after a delay
                            setTimeout(() => window.location.reload(), 2000);
                          }
                        } catch (error) {
                          console.error('Failed to regenerate character:', error);
                          alert('Failed to regenerate character');
                        }
                      }}
                      className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors"
                      title={`Regenerate ${char.name}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                  
                  {/* Character info */}
                  <div className="p-3">
                    <strong className="block font-black uppercase text-sm">{char.name || 'Unknown'}</strong>
                    <span className="text-xs font-bold uppercase" style={{ color: 'var(--muted)' }}>
                      {char.role || 'Character'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
