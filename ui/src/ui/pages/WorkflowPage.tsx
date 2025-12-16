import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useApi } from '../api/ApiProvider';
import ReactMarkdown from 'react-markdown';
import { useJobPoller } from '../hooks/useJobPoller';

type ViewTab = 'story' | 'pages' | 'timeline' | 'graph';

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

  const loadWorkflowData = async () => {
    if (!workflowId) return;
    
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
          <Link to="/dashboard" className="text-[var(--cream)] hover:text-[var(--orange)] text-2xl font-black">←</Link>
          <strong className="text-3xl uppercase">{workflow.title}</strong>
          <span className="comic-badge px-3 py-1 rounded">
            {workflow.currentStage.toUpperCase()}
          </span>
        </div>
        <div className="text-sm font-bold uppercase tracking-wide">
          {chapters.length} CH · {pages.length} PG
        </div>
      </header>

      <div className="grid grid-cols-[260px_1fr_320px] h-[calc(100vh-80px)]">
        {/* LEFT SIDEBAR - Chapters */}
        <aside className="bg-[var(--cream-dark)] border-r-4 border-[var(--ink)] p-4 overflow-y-auto">
          <h3 className="text-sm font-black uppercase tracking-wider mb-3">CHAPTERS</h3>
          {chapters.length === 0 ? (
            <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>No chapters yet</div>
          ) : (
            chapters.map((chapter, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setSelectedChapter(chapter.chapterNumber);
                  setActiveTab('pages');
                }}
                className={`rounded border-2 mb-3 cursor-pointer transition-all overflow-hidden ${
                  selectedChapter === chapter.chapterNumber
                    ? 'border-[var(--orange)] ring-2 ring-[var(--orange)] ring-opacity-50'
                    : 'border-[var(--ink)] hover:border-[var(--orange)]'
                }`}
              >
                {/* Chapter preview image */}
                <div className="h-32 bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center">
                  <div className="text-6xl font-black opacity-20">{chapter.chapterNumber || idx + 1}</div>
                </div>
                
                {/* Chapter info */}
                <div className="p-3 bg-[var(--paper)]">
                  <div className="text-xs font-black uppercase mb-1" style={{ color: 'var(--orange)' }}>
                    Chapter {chapter.chapterNumber || idx + 1}
                  </div>
                  <div className="text-sm font-bold leading-tight mb-2">
                    {chapter.title || 'Untitled'}
                  </div>
                  <div className="text-xs font-bold" style={{ color: 'var(--muted)' }}>
                    {chapter.scenes || 0} scenes · {chapter.pages || 0} pages
                  </div>
                </div>
              </div>
            ))
          )}
        </aside>

        {/* CENTER CANVAS */}
        <main className="p-6 overflow-y-auto">
          {/* View Tabs */}
          <div className="flex gap-2 mb-6 border-b-2 border-[var(--ink)] pb-2">
            {(['story', 'pages', 'timeline', 'graph'] as ViewTab[]).map((tab) => (
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

          {/* Story View - Show screenplay/storyline content */}
          {activeTab === 'story' && (
            <div className="p-6">
              {workflow.screenplay || workflow.storyline ? (
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
                    {workflow.screenplay || workflow.storyline}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-lg font-black uppercase mb-2">No Story Content</div>
                  <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>
                    Generate chapters to create the screenplay.
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
                {chapters.length === 0 ? (
                  <div className="text-center py-12 border-2 border-dashed border-[var(--ink)] rounded">
                    <div className="text-lg font-black uppercase mb-2">No chapters yet.</div>
                    <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>
                      Use the generation controls in the sidebar to create chapters.
                    </div>
                  </div>
                ) : (
                  chapters.map((chapter, idx) => {
                    const chapterNum = chapter.chapterNumber || chapter.number || idx + 1;
                    const totalPagesInChapter = chapter.pages || 0;
                    const pagesGenerated = workflow.pagesGenerated || [];
                    
                    // Calculate which pages in this chapter are generated
                    // Assuming pages are numbered sequentially across chapters
                    const startPage = chapters.slice(0, idx).reduce((sum, ch) => sum + (ch.pages || 0), 0) + 1;
                    const endPage = startPage + totalPagesInChapter - 1;
                    
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
                  })
                )}
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
                  className={`px-2 py-1 text-[10px] font-bold uppercase border-2 border-[var(--ink)] rounded transition-colors ${
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
                        setCharJobId(data.job_id);
                      } else {
                        setCharJobId(data.job_id);
                      }
                    } catch (error) {
                      setIsGenerating(false);
                      alert('Failed to start character generation');
                    }
                  }}
                >
                  {isGenerating ? '⏳ Generating...' : '🎨 Generate'}
                </button>
                <button
                  className="px-2 py-1 text-[10px] font-bold uppercase border-2 border-[var(--ink)] rounded hover:bg-[var(--red)] transition-colors"
                  onClick={async () => {
                    try {
                      setIsGenerating(true);
                      const response = await fetch(`http://localhost:8000/workflows/${workflowId}/characters/retry`, {
                        method: 'POST',
                      });
                      const data = await response.json();
                      setCharJobId(data.job_id);
                      console.log('Retry response:', data);
                    } catch (error) {
                      setIsGenerating(false);
                      alert('Failed to retry');
                    }
                  }}
                >
                  🔄 Retry
                </button>
              </div>
            )}
          </div>
          <div className="space-y-4">
            {characters.length === 0 ? (
              <div className="text-sm font-bold" style={{ color: 'var(--muted)' }}>No character data loaded yet</div>
            ) : (
              characters.map((char, idx) => (
                <div key={idx} className="bg-[var(--paper)] border-2 border-[var(--ink)] rounded overflow-hidden">
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
