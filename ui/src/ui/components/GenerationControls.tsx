import React, { useState } from 'react';
import type { ChapterSelection, PageSelection } from '../api/ApiClient';

interface GenerationControlsProps {
  stage: string;
  disabled: boolean;
  onRunChapters: (args: { selection: ChapterSelection; batchSize?: number; continueFrom?: boolean }) => void;
  onRunPages: (args: { selection: PageSelection; continueFrom?: boolean }) => void;
}

function parsePositiveInt(value: string, fallback: number): number {
  const n = parseInt(value, 10);
  if (Number.isNaN(n) || n <= 0) return fallback;
  return n;
}

export const GenerationControls: React.FC<GenerationControlsProps> = ({
  stage,
  disabled,
  onRunChapters,
  onRunPages,
}) => {
  const [chapterTarget, setChapterTarget] = useState<'all' | 'list'>('all');
  const [chapterList, setChapterList] = useState('');
  const [chapterBatchSize, setChapterBatchSize] = useState(2);

  const [pageMode, setPageMode] = useState<'all' | 'range' | 'firstPerChapter'>('all');
  const [pageFrom, setPageFrom] = useState(1);
  const [pageTo, setPageTo] = useState(20);
  const [pageFirstCount, setPageFirstCount] = useState(2);
  const [pageChapterScope, setPageChapterScope] = useState<'all' | 'list'>('all');
  const [pageChapterList, setPageChapterList] = useState('');

  const buildChapterSelection = (): ChapterSelection => {
    if (chapterTarget === 'all') {
      return { kind: 'all' };
    }
    const chapters = chapterList
      .split(',')
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !Number.isNaN(n) && n > 0);
    if (chapters.length === 0) {
      return { kind: 'all' };
    }
    return { kind: 'list', chapters };
  };

  const handleRunChapters = (asBatches: boolean) => {
    const selection = buildChapterSelection();
    const batchSize = asBatches ? chapterBatchSize || 1 : undefined;
    onRunChapters({ selection, batchSize, continueFrom: false });
  };

  const buildPageSelection = (): PageSelection => {
    if (pageMode === 'all') {
      return { kind: 'all' };
    }
    if (pageMode === 'range') {
      const from = Math.max(1, pageFrom);
      const to = Math.max(from, pageTo);
      return { kind: 'range', from, to };
    }
    const count = Math.max(1, pageFirstCount);
    if (pageChapterScope === 'all') {
      return { kind: 'firstPerChapter', count, chapters: 'all' };
    }
    const chapters = pageChapterList
      .split(',')
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !Number.isNaN(n) && n > 0);
    return { kind: 'firstPerChapter', count, chapters: chapters.length ? chapters : 'all' };
  };

  const handleRunPages = () => {
    const selection = buildPageSelection();
    onRunPages({ selection, continueFrom: false });
  };

  // Show chapter controls when in content/novel stage or chapters stage
  if (stage === 'content' || stage === 'chapters') {
    return (
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase text-[var(--ink)] border-b border-[var(--border)] pb-2 mb-3">
          📖 Chapter Generation
        </h4>
        
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-[var(--muted)] mb-1">Target:</label>
            <select
              className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)] font-medium"
              value={chapterTarget}
              onChange={(e) => setChapterTarget(e.target.value as 'all' | 'list')}
              disabled={disabled}
            >
              <option value="all">All chapters</option>
              <option value="list">Specific chapters</option>
            </select>
          </div>
          
          {chapterTarget === 'list' && (
            <div>
              <label className="block text-xs font-medium text-[var(--muted)] mb-1">Chapters:</label>
              <input
                className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)] placeholder:text-[var(--muted)]"
                placeholder="e.g., 1,3,5,7"
                value={chapterList}
                onChange={(e) => setChapterList(e.target.value)}
                disabled={disabled}
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-[var(--muted)] mb-1">Batch size:</label>
            <input
              className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)]"
              value={chapterBatchSize}
              onChange={(e) => setChapterBatchSize(parsePositiveInt(e.target.value, 2))}
              disabled={disabled}
            />
          </div>

          <button
            type="button"
            onClick={() => handleRunChapters(false)}
            disabled={disabled}
            className="w-full px-4 py-3 text-xs font-bold uppercase border-2 border-[var(--ink)] rounded bg-[var(--paper)] hover:bg-[var(--orange)] hover:text-[var(--ink)] transition-colors disabled:opacity-50"
          >
            Generate
          </button>
        </div>
      </div>
    );
  }

  // Show page controls when in pages stage
  if (stage === 'pages') {
    return (
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase text-[var(--ink)] border-b border-[var(--border)] pb-2 mb-3">
          🎨 Page Generation
        </h4>
        
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-[var(--muted)] mb-1">Mode:</label>
            <select
              className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)] font-medium"
              value={pageMode}
              onChange={(e) => setPageMode(e.target.value as 'all' | 'range' | 'firstPerChapter')}
              disabled={disabled}
            >
              <option value="all">All pages</option>
              <option value="range">Page range</option>
              <option value="firstPerChapter">First N per chapter</option>
            </select>
          </div>

          {pageMode === 'range' && (
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-[var(--muted)] mb-1">From:</label>
                <input
                  className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)]"
                  value={pageFrom}
                  onChange={(e) => setPageFrom(parsePositiveInt(e.target.value, 1))}
                  disabled={disabled}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--muted)] mb-1">To:</label>
                <input
                  className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)]"
                  value={pageTo}
                  onChange={(e) => setPageTo(parsePositiveInt(e.target.value, pageFrom))}
                  disabled={disabled}
                />
              </div>
            </div>
          )}

          {pageMode === 'firstPerChapter' && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-[var(--muted)] mb-1">Pages per chapter:</label>
                <input
                  className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)]"
                  value={pageFirstCount}
                  onChange={(e) => setPageFirstCount(parsePositiveInt(e.target.value, 2))}
                  disabled={disabled}
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-[var(--muted)] mb-1">For chapters:</label>
                <select
                  className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)] font-medium"
                  value={pageChapterScope}
                  onChange={(e) => setPageChapterScope(e.target.value as 'all' | 'list')}
                  disabled={disabled}
                >
                  <option value="all">All chapters</option>
                  <option value="list">Specific chapters</option>
                </select>
              </div>
              
              {pageChapterScope === 'list' && (
                <div>
                  <label className="block text-xs font-medium text-[var(--muted)] mb-1">Chapters:</label>
                  <input
                    className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)] placeholder:text-[var(--muted)]"
                    placeholder="e.g., 1,3,5,7"
                    value={pageChapterList}
                    onChange={(e) => setPageChapterList(e.target.value)}
                    disabled={disabled}
                  />
                </div>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={handleRunPages}
            disabled={disabled}
            className="w-full px-4 py-3 text-xs font-bold uppercase border-2 border-[var(--ink)] rounded bg-[var(--paper)] hover:bg-[var(--orange)] hover:text-[var(--ink)] transition-colors disabled:opacity-50"
          >
            Generate
          </button>
        </div>
      </div>
    );
  }

  return null;
};