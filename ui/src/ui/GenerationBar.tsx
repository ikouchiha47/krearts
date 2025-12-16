import React, { useState } from 'react';
import type { ChapterSelection, PageSelection } from './api/ApiClient';

interface GenerationBarProps {
  mode: 'chapters' | 'pages';
  onModeChange: (mode: 'chapters' | 'pages') => void;
  disabled: boolean;
  onRunChapters: (args: { selection: ChapterSelection; batchSize?: number; continueFrom?: boolean }) => void;
  onRunPages: (args: { selection: PageSelection; continueFrom?: boolean }) => void;
}

function parsePositiveInt(value: string, fallback: number): number {
  const n = parseInt(value, 10);
  if (Number.isNaN(n) || n <= 0) return fallback;
  return n;
}

export const GenerationBar: React.FC<GenerationBarProps> = ({
  mode,
  onModeChange,
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

  return (
    <div className="flex flex-col gap-3 text-xs">
      <div className="inline-flex border-2 border-black rounded overflow-hidden">
        <button
          type="button"
          onClick={() => onModeChange('chapters')}
          className={`px-3 py-1 border-r-2 border-black transition-colors font-semibold ${
            mode === 'chapters'
              ? 'bg-black text-white'
              : 'bg-white text-black hover:bg-gray-100'
          }`}
        >
          Chapters
        </button>
        <button
          type="button"
          onClick={() => onModeChange('pages')}
          className={`px-3 py-1 transition-colors font-semibold ${
            mode === 'pages'
              ? 'bg-black text-white'
              : 'bg-white text-black hover:bg-gray-100'
          }`}
        >
          Pages
        </button>
      </div>

      {mode === 'chapters' ? (
        <div className="flex items-center gap-2 flex-wrap">
          <select
            className="px-2 py-1 border-2 border-black rounded bg-white text-black"
            value={chapterTarget}
            onChange={(e) => setChapterTarget(e.target.value as 'all' | 'list')}
            disabled={disabled}
          >
            <option value="all">All chapters</option>
            <option value="list">Only chapters…</option>
          </select>
          {chapterTarget === 'list' && (
            <input
              className="w-24 px-2 py-1 border-2 border-black rounded bg-white text-black placeholder:text-black/40"
              placeholder="1,3,5"
              value={chapterList}
              onChange={(e) => setChapterList(e.target.value)}
              disabled={disabled}
            />
          )}

          <span className="ml-2 text-black/70 font-medium">Batch size</span>
          <input
            className="w-12 px-1 py-1 border-2 border-black rounded bg-white text-black"
            value={chapterBatchSize}
            onChange={(e) => setChapterBatchSize(parsePositiveInt(e.target.value, 2))}
            disabled={disabled}
          />

          <button
            type="button"
            onClick={() => handleRunChapters(false)}
            disabled={disabled}
            className="ml-2 px-3 py-1 border-2 border-black rounded bg-white hover:bg-gray-100 disabled:opacity-40 font-semibold"
          >
            Run
          </button>
          <button
            type="button"
            onClick={() => handleRunChapters(true)}
            disabled={disabled}
            className="px-3 py-1 border-2 border-black rounded bg-white hover:bg-gray-100 disabled:opacity-40 font-semibold"
          >
            Run in batches
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2 flex-wrap">
          <select
            className="px-2 py-1 border-2 border-black rounded bg-white text-black"
            value={pageMode}
            onChange={(e) => setPageMode(e.target.value as 'all' | 'range' | 'firstPerChapter')}
            disabled={disabled}
          >
            <option value="all">All pages</option>
            <option value="range">Range</option>
            <option value="firstPerChapter">First N per chapter</option>
          </select>

          {pageMode === 'range' && (
            <>
              <span className="text-black/70 font-medium">From</span>
              <input
                className="w-14 px-1 py-1 border-2 border-black rounded bg-white text-black"
                value={pageFrom}
                onChange={(e) => setPageFrom(parsePositiveInt(e.target.value, 1))}
                disabled={disabled}
              />
              <span className="text-black/70 font-medium">to</span>
              <input
                className="w-14 px-1 py-1 border-2 border-black rounded bg-white text-black"
                value={pageTo}
                onChange={(e) => setPageTo(parsePositiveInt(e.target.value, pageFrom))}
                disabled={disabled}
              />
            </>
          )}

          {pageMode === 'firstPerChapter' && (
            <>
              <span className="text-black/70 font-medium">First</span>
              <input
                className="w-10 px-1 py-1 border-2 border-black rounded bg-white text-black"
                value={pageFirstCount}
                onChange={(e) => setPageFirstCount(parsePositiveInt(e.target.value, 2))}
                disabled={disabled}
              />
              <span className="text-black/70 font-medium">pages for</span>
              <select
                className="px-2 py-1 border-2 border-black rounded bg-white text-black"
                value={pageChapterScope}
                onChange={(e) => setPageChapterScope(e.target.value as 'all' | 'list')}
                disabled={disabled}
              >
                <option value="all">all chapters</option>
                <option value="list">chapters…</option>
              </select>
              {pageChapterScope === 'list' && (
                <input
                  className="w-24 px-2 py-1 border-2 border-black rounded bg-white text-black placeholder:text-black/40"
                  placeholder="1,3,5"
                  value={pageChapterList}
                  onChange={(e) => setPageChapterList(e.target.value)}
                  disabled={disabled}
                />
              )}
            </>
          )}

          <button
            type="button"
            onClick={handleRunPages}
            disabled={disabled}
            className="ml-auto px-3 py-1 border-2 border-black rounded bg-white hover:bg-gray-100 disabled:opacity-40 font-semibold"
          >
            Run Pages
          </button>
        </div>
      )}
    </div>
  );
};
