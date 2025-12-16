import React, { useState, useRef } from 'react';
import { BookOpen, Sparkles, Play, ZoomIn, ZoomOut, Move, Plus, Image, Wand2, Grid, Download, Settings, ArrowRight, Edit2, Save, X, ChevronRight, List, LayoutGrid, Trash2, Copy } from 'lucide-react';

const KreArtsStudio = () => {
  const [view, setView] = useState('canvas'); // canvas | timeline | gallery
  const [leftPanel, setLeftPanel] = useState('input'); // input | chapters | settings
  const [rightPanel, setRightPanel] = useState('images'); // images | inspector
  
  // Canvas controls
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [editingChapter, setEditingChapter] = useState(null);
  
  // User input state
  const [storyInput, setStoryInput] = useState({
    title: '',
    genre: 'Mystery',
    artStyles: ['Cinematic'],
    plotOutline: '',
    numChapters: 3
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStage, setGenerationStage] = useState(''); // planning | critique | generating | storyboarding

  // Story structure
  const [chapters, setChapters] = useState([
    {
      id: 'ch1',
      num: 1,
      title: 'The Beginning',
      prompt: 'Introduce the protagonist in their ordinary world, hint at the coming conflict',
      storyline: '',
      status: 'draft',
      x: 100,
      y: 200,
      scenes: [
        { id: 's1', title: 'Opening scene', prompt: 'Morning routine', images: ['img1', 'img2'] },
        { id: 's2', title: 'Inciting incident', prompt: 'Discovery moment', images: ['img3'] }
      ]
    },
    {
      id: 'ch2',
      num: 2,
      title: 'Rising Action',
      prompt: 'Protagonist faces challenges and obstacles',
      storyline: '',
      status: 'draft',
      x: 100,
      y: 500,
      scenes: []
    },
    {
      id: 'ch3',
      num: 3,
      title: 'Climax & Resolution',
      prompt: 'Final confrontation and resolution',
      storyline: '',
      status: 'draft',
      x: 100,
      y: 800,
      scenes: []
    }
  ]);

  const [allImages, setAllImages] = useState({
    img1: { id: 'img1', chapterId: 'ch1', sceneId: 's1', x: 750, y: 100, prompt: 'Dawn breaking over city', url: null, status: 'generated' },
    img2: { id: 'img2', chapterId: 'ch1', sceneId: 's1', x: 750, y: 220, prompt: 'Character close-up', url: null, status: 'generated' },
    img3: { id: 'img3', chapterId: 'ch1', sceneId: 's2', x: 750, y: 340, prompt: 'Moment of realization', url: null, status: 'generated' }
  });

  const toggleArtStyle = (style) => {
    setStoryInput(prev => ({
      ...prev,
      artStyles: prev.artStyles.includes(style)
        ? prev.artStyles.filter(s => s !== style)
        : [...prev.artStyles, style]
    }));
  };

  const genres = ['Mystery', 'Romance', 'Sci-Fi', 'Fantasy', 'Thriller', 'Drama', 'Adventure', 'Horror'];
  const artStyles = ['Cinematic', 'Film Noir', 'Comic Book', 'Anime', 'Watercolor', 'Oil Painting', 'Digital Art', 'Photorealistic'];

  const startGeneration = () => {
    setIsGenerating(true);
    setGenerationStage('planning');
    
    // Simulate flow
    setTimeout(() => setGenerationStage('critique'), 2000);
    setTimeout(() => setGenerationStage('generating'), 4000);
    setTimeout(() => setGenerationStage('storyboarding'), 6000);
    setTimeout(() => {
      setIsGenerating(false);
      setGenerationStage('');
      // Update chapters with generated content
      setChapters(prev => prev.map(ch => ({ ...ch, status: 'complete' })));
    }, 8000);
  };

  const addChapter = () => {
    const newNum = chapters.length + 1;
    setChapters([...chapters, {
      id: `ch${newNum}`,
      num: newNum,
      title: `Chapter ${newNum}`,
      prompt: '',
      storyline: '',
      status: 'draft',
      x: 100,
      y: 200 + (newNum - 1) * 300,
      scenes: []
    }]);
  };

  const updateChapter = (id, updates) => {
    setChapters(prev => prev.map(ch => ch.id === id ? { ...ch, ...updates } : ch));
  };

  const deleteChapter = (id) => {
    setChapters(prev => prev.filter(ch => ch.id !== id));
  };

  const handleCanvasMouseDown = (e) => {
    if (e.target.closest('.node')) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleCanvasMouseMove = (e) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleCanvasMouseUp = () => {
    setIsDragging(false);
  };

  const drawConnection = (x1, y1, x2, y2, color = '#8b5cf6') => {
    return (
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={color}
        strokeWidth="2"
        strokeDasharray="5,5"
        opacity="0.4"
      />
    );
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white flex flex-col overflow-hidden">
      {/* Top Toolbar */}
      <header className="h-14 border-b border-white/10 backdrop-blur-xl bg-black/40 flex items-center justify-between px-6 z-50">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              KreArts
            </span>
          </div>
          
          <div className="h-6 w-px bg-white/20" />
          
          <input
            type="text"
            value={storyInput.title || 'Untitled Story'}
            onChange={(e) => setStoryInput({ ...storyInput, title: e.target.value })}
            className="bg-transparent text-white font-medium focus:outline-none focus:bg-white/5 px-3 py-1 rounded"
            placeholder="Story Title"
          />
        </div>

        <div className="flex items-center gap-2">
          {/* View Switcher */}
          <div className="flex items-center gap-1 bg-white/5 rounded-lg p-1">
            <button
              onClick={() => setView('canvas')}
              className={`px-3 py-1.5 rounded text-sm flex items-center gap-2 transition-all ${view === 'canvas' ? 'bg-purple-500/30 text-purple-300' : 'text-gray-400 hover:bg-white/5'}`}
            >
              <LayoutGrid className="w-4 h-4" />
              Canvas
            </button>
            <button
              onClick={() => setView('timeline')}
              className={`px-3 py-1.5 rounded text-sm flex items-center gap-2 transition-all ${view === 'timeline' ? 'bg-purple-500/30 text-purple-300' : 'text-gray-400 hover:bg-white/5'}`}
            >
              <List className="w-4 h-4" />
              Timeline
            </button>
          </div>

          <div className="h-6 w-px bg-white/20" />

          {/* Zoom Controls (canvas only) */}
          {view === 'canvas' && (
            <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5">
              <button onClick={() => setZoom(z => Math.max(0.1, z - 0.1))}>
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-sm w-12 text-center">{Math.round(zoom * 100)}%</span>
              <button onClick={() => setZoom(z => Math.min(3, z + 0.1))}>
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
          )}

          <button
            onClick={startGeneration}
            disabled={isGenerating}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 rounded-lg flex items-center gap-2 font-medium transition-all"
          >
            {isGenerating ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {generationStage}
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Generate Story
              </>
            )}
          </button>

          <button className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5">
            <Download className="w-5 h-5" />
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Input & Chapters */}
        <aside className="w-80 border-r border-white/10 bg-black/20 flex flex-col">
          {/* Panel Tabs */}
          <div className="flex border-b border-white/10">
            <button
              onClick={() => setLeftPanel('input')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-all ${leftPanel === 'input' ? 'bg-purple-500/20 text-purple-300 border-b-2 border-purple-500' : 'text-gray-400 hover:bg-white/5'}`}
            >
              Story Input
            </button>
            <button
              onClick={() => setLeftPanel('chapters')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-all ${leftPanel === 'chapters' ? 'bg-purple-500/20 text-purple-300 border-b-2 border-purple-500' : 'text-gray-400 hover:bg-white/5'}`}
            >
              Chapters
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {leftPanel === 'input' && (
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Title</label>
                  <input
                    type="text"
                    value={storyInput.title}
                    onChange={(e) => setStoryInput({ ...storyInput, title: e.target.value })}
                    className="w-full bg-white/5 rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-purple-500 focus:outline-none"
                    placeholder="Enter story title..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Genre</label>
                    <select
                      value={storyInput.genre}
                      onChange={(e) => setStoryInput({ ...storyInput, genre: e.target.value })}
                      className="w-full bg-white/5 rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-purple-500 focus:outline-none"
                    >
                      {genres.map(g => <option key={g} value={g}>{g}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400 mb-2 block">Chapters</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={storyInput.numChapters}
                      onChange={(e) => setStoryInput({ ...storyInput, numChapters: parseInt(e.target.value) })}
                      className="w-full bg-white/5 rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-purple-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Art Styles (select multiple)</label>
                  <div className="grid grid-cols-2 gap-2">
                    {artStyles.map(style => (
                      <button
                        key={style}
                        onClick={() => toggleArtStyle(style)}
                        className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          storyInput.artStyles.includes(style)
                            ? 'bg-purple-500/30 text-purple-200 border border-purple-500/50'
                            : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {style}
                      </button>
                    ))}
                  </div>
                  {storyInput.artStyles.length === 0 && (
                    <p className="text-xs text-red-400 mt-2">Select at least one art style</p>
                  )}
                </div>

                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Plot Outline</label>
                  <textarea
                    value={storyInput.plotOutline}
                    onChange={(e) => setStoryInput({ ...storyInput, plotOutline: e.target.value })}
                    className="w-full h-48 bg-white/5 rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-purple-500 focus:outline-none resize-none"
                    placeholder="Describe your story idea, main characters, setting, and key plot points..."
                  />
                </div>

                <div className="pt-4 border-t border-white/10">
                  <button
                    onClick={startGeneration}
                    disabled={isGenerating || !storyInput.plotOutline || storyInput.artStyles.length === 0}
                    className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium flex items-center justify-center gap-2"
                  >
                    <Wand2 className="w-4 h-4" />
                    Generate Full Story
                  </button>
                  {storyInput.artStyles.length > 0 && (
                    <p className="text-xs text-gray-400 mt-2 text-center">
                      Using: {storyInput.artStyles.join(', ')}
                    </p>
                  )}
                </div>
              </div>
            )}

            {leftPanel === 'chapters' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold">Chapters ({chapters.length})</h3>
                  <button
                    onClick={addChapter}
                    className="px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 rounded-lg text-sm flex items-center gap-2"
                  >
                    <Plus className="w-3 h-3" />
                    Add
                  </button>
                </div>

                {chapters.map(chapter => (
                  <div key={chapter.id} className="bg-white/5 rounded-lg border border-white/10 p-3">
                    {editingChapter === chapter.id ? (
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={chapter.title}
                          onChange={(e) => updateChapter(chapter.id, { title: e.target.value })}
                          className="w-full bg-black/30 rounded px-2 py-1 text-sm border border-white/10 focus:border-purple-500 focus:outline-none"
                        />
                        <textarea
                          value={chapter.prompt}
                          onChange={(e) => updateChapter(chapter.id, { prompt: e.target.value })}
                          className="w-full h-24 bg-black/30 rounded px-2 py-1 text-xs border border-white/10 focus:border-purple-500 focus:outline-none resize-none"
                          placeholder="Chapter prompt..."
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingChapter(null)}
                            className="flex-1 px-3 py-1.5 bg-green-500/20 hover:bg-green-500/30 rounded text-xs font-medium flex items-center justify-center gap-1"
                          >
                            <Save className="w-3 h-3" />
                            Save
                          </button>
                          <button
                            onClick={() => setEditingChapter(null)}
                            className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded text-xs"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs text-purple-400 font-semibold">CH {chapter.num}</span>
                              <span className={`px-2 py-0.5 text-xs rounded-full ${
                                chapter.status === 'complete' ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-400'
                              }`}>
                                {chapter.status}
                              </span>
                            </div>
                            <h4 className="font-medium text-sm">{chapter.title}</h4>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => setEditingChapter(chapter.id)}
                              className="p-1 hover:bg-white/10 rounded"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => deleteChapter(chapter.id)}
                              className="p-1 hover:bg-red-500/20 rounded text-red-400"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                        {chapter.prompt && (
                          <p className="text-xs text-gray-400 line-clamp-2">{chapter.prompt}</p>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                          <span>{chapter.scenes.length} scenes</span>
                          <span>•</span>
                          <span>{chapter.scenes.reduce((sum, s) => sum + s.images.length, 0)} images</span>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 relative overflow-hidden">
          {view === 'canvas' && (
            <div
              className="w-full h-full cursor-grab active:cursor-grabbing"
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              onMouseLeave={handleCanvasMouseUp}
            >
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <circle cx="1" cy="1" r="1" fill="#ffffff" opacity="0.03" />
                  </pattern>
                </defs>
                <rect width="10000" height="10000" fill="url(#grid)" />
                
                <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                  {chapters.map(chapter =>
                    chapter.scenes.map(scene => (
                      <g key={scene.id}>
                        {drawConnection(chapter.x + 250, chapter.y + 60, chapter.x + 400, scene.y + 40)}
                        {scene.images.map(imgId => {
                          const img = allImages[imgId];
                          return img ? drawConnection(chapter.x + 400, scene.y + 40, img.x, img.y + 60, '#ec4899') : null;
                        })}
                      </g>
                    ))
                  )}
                </g>
              </svg>

              <div
                className="absolute inset-0"
                style={{
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                  transformOrigin: '0 0'
                }}
              >
                {chapters.map(chapter => (
                  <div
                    key={chapter.id}
                    className="absolute node"
                    style={{ left: chapter.x, top: chapter.y }}
                  >
                    <div className="w-64 bg-slate-900/90 backdrop-blur-lg rounded-xl border-2 border-purple-500/30 shadow-xl shadow-purple-500/10">
                      <div className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <span className="text-xs font-bold text-purple-400">CHAPTER {chapter.num}</span>
                            <h3 className="font-bold text-lg mt-1">{chapter.title}</h3>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            chapter.status === 'complete' ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-400'
                          }`}>
                            {chapter.status}
                          </span>
                        </div>
                        {chapter.prompt && (
                          <p className="text-xs text-gray-400 line-clamp-3 mb-3">{chapter.prompt}</p>
                        )}
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{chapter.scenes.length} scenes</span>
                          <button
                            onClick={() => setEditingChapter(chapter.id)}
                            className="text-purple-400 hover:text-purple-300"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {view === 'timeline' && (
            <div className="w-full h-full overflow-y-auto p-8">
              <div className="max-w-4xl mx-auto space-y-6">
                <h2 className="text-2xl font-bold mb-6">Story Timeline</h2>
                {chapters.map((chapter, idx) => (
                  <div key={chapter.id} className="relative pl-12">
                    {/* Timeline line */}
                    {idx < chapters.length - 1 && (
                      <div className="absolute left-6 top-16 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 to-pink-500" />
                    )}
                    
                    {/* Chapter node */}
                    <div className="absolute left-3 top-6 w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 border-4 border-slate-950" />
                    
                    <div className="bg-slate-900/50 backdrop-blur-lg rounded-xl border border-purple-500/20 p-6 mb-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <span className="text-sm text-purple-400 font-semibold">CHAPTER {chapter.num}</span>
                          <h3 className="text-xl font-bold mt-1">{chapter.title}</h3>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingChapter(chapter.id)}
                            className="p-2 hover:bg-white/10 rounded"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <span className={`px-3 py-1 text-xs rounded-full ${
                            chapter.status === 'complete' ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-400'
                          }`}>
                            {chapter.status}
                          </span>
                        </div>
                      </div>

                      {chapter.prompt && (
                        <div className="mb-4 p-3 bg-white/5 rounded-lg">
                          <label className="text-xs text-gray-400 mb-1 block">Chapter Prompt</label>
                          <p className="text-sm text-gray-300">{chapter.prompt}</p>
                        </div>
                      )}

                      {chapter.storyline && (
                        <div className="mb-4 p-3 bg-white/5 rounded-lg">
                          <label className="text-xs text-gray-400 mb-1 block">Generated Storyline</label>
                          <p className="text-sm text-gray-300 whitespace-pre-wrap">{chapter.storyline}</p>
                        </div>
                      )}

                      {/* Scenes */}
                      {chapter.scenes.length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-sm font-semibold mb-3 text-gray-400">Scenes</h4>
                          <div className="grid grid-cols-2 gap-3">
                            {chapter.scenes.map(scene => (
                              <div key={scene.id} className="bg-black/30 rounded-lg p-3">
                                <h5 className="font-medium text-sm mb-1">{scene.title}</h5>
                                <p className="text-xs text-gray-400 mb-2">{scene.prompt}</p>
                                <div className="flex flex-wrap gap-1">
                                  {scene.images.map(imgId => (
                                    <div key={imgId} className="w-12 h-12 bg-slate-800 rounded border border-white/10" />
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>

        {/* Right Panel - Image Gallery */}
        <aside className="w-80 border-l border-white/10 bg-black/20 flex flex-col">
          <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <h3 className="font-semibold">Image Gallery</h3>
            <span className="text-xs text-gray-400">{Object.keys(allImages).length} images</span>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {Object.keys(allImages).length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Image className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p className="text-sm">No images yet</p>
                <p className="text-xs mt-1">Generate your story to create images</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {Object.values(allImages).map(img => (
                  <div
                    key={img.id}
                    onClick={() => setSelectedNode(img)}
                    className={`aspect-square rounded-lg overflow-hidden border-2 cursor-pointer transition-all ${
                      selectedNode?.id === img.id ? 'border-pink-500 shadow-lg shadow-pink-500/30' : 'border-white/10 hover:border-pink-500/50'
                    }`}
                  >
                    {img.url ? (
                      <img src={img.url} alt={img.prompt} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-purple-900/30 to-pink-900/30 flex items-center justify-center">
                        <Wand2 className="w-6 h-6 text-white/20" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {selectedNode && (
            <div className="border-t border-white/10 p-4 bg-black/30">
              <h4 className="text-sm font-semibold mb-2">Selected Image</h4>
              <p className="text-xs text-gray-400 mb-3">{selectedNode.prompt}</p>
              <div className="flex gap-2">
                <button className="flex-1 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-xs font-medium flex items-center justify-center gap-1">
                  <Wand2 className="w-3 h-3" />
                  Regenerate
                </button>
                <button className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg">
                  <Copy className="w-3 h-3" />
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};

export default KreArtsStudio;