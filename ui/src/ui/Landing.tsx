import React from 'react';
import { useNavigate } from 'react-router-dom';

export const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-[var(--ink)] px-10 py-6 flex items-center justify-between border-b-4 border-[var(--orange)]">
        <h1 className="text-4xl font-black uppercase tracking-wider text-[var(--cream)]">COMICS BOOK</h1>
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/app')}
            className="bg-transparent text-[var(--cream)] px-6 py-2 rounded-lg font-bold uppercase text-sm hover:text-[var(--orange)] transition-colors"
          >
            Dashboard
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* Hero Banner */}
          <div className="bg-[var(--paper)] rounded-2xl p-16 mb-12 shadow-lg border-2 border-[var(--ink)]">
            <div className="grid grid-cols-[1.5fr_1fr] gap-12 items-center">
              <div>
                <h2 className="text-7xl font-black uppercase leading-none mb-6">Create Comic Books with AI</h2>
                <p className="text-xl font-bold mb-8 leading-relaxed" style={{ color: 'var(--muted)' }}>
                  Design chapters, generate illustrated pages, and bring your graphic novels to life. 
                  From story outline to final panels—all powered by AI workflows.
                </p>
                <button
                  onClick={() => navigate('/app')}
                  className="bg-[var(--orange)] text-[var(--ink)] px-10 py-5 rounded-lg font-black uppercase text-lg border-2 border-[var(--ink)] hover:bg-[var(--yellow)] transition-colors shadow-md"
                >
                  Start Creating →
                </button>
              </div>
              <div className="bg-gradient-to-br from-[var(--yellow)] to-[var(--orange)] rounded-xl border-2 border-[var(--ink)] aspect-[3/4] flex items-center justify-center shadow-lg">
                <div className="text-center text-[var(--ink)]">
                  <div className="text-8xl mb-4">📖</div>
                  <div className="text-2xl font-black uppercase">Your Story</div>
                </div>
              </div>
            </div>
          </div>

          {/* Features Section */}
          <div className="mb-12">
            <h3 className="text-4xl font-black uppercase mb-8 text-center">How It Works</h3>
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-[var(--paper)] rounded-xl p-8 border-2 border-[var(--ink)] shadow-md">
                <div className="text-5xl mb-4">✍️</div>
                <h4 className="text-2xl font-black uppercase mb-3">1. Write Your Story</h4>
                <p className="font-bold" style={{ color: 'var(--muted)' }}>
                  Define your narrative, characters, and chapter structure. Our AI helps you organize your story arc.
                </p>
              </div>
              <div className="bg-[var(--paper)] rounded-xl p-8 border-2 border-[var(--ink)] shadow-md">
                <div className="text-5xl mb-4">🎨</div>
                <h4 className="text-2xl font-black uppercase mb-3">2. Generate Panels</h4>
                <p className="font-bold" style={{ color: 'var(--muted)' }}>
                  AI creates detailed panel descriptions and visual prompts for each scene in your comic book.
                </p>
              </div>
              <div className="bg-[var(--paper)} rounded-xl p-8 border-2 border-[var(--ink)] shadow-md">
                <div className="text-5xl mb-4">📚</div>
                <h4 className="text-2xl font-black uppercase mb-3">3. Publish & Share</h4>
                <p className="font-bold" style={{ color: 'var(--muted)' }}>
                  Export your complete comic book workflow and bring your graphic novel to life.
                </p>
              </div>
            </div>
          </div>

          {/* Art Styles Section */}
          <div className="mb-12">
            <h3 className="text-4xl font-black uppercase mb-8 text-center">Multiple Art Styles</h3>
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-md">
                <div className="aspect-square bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg mb-4 border-2 border-[var(--ink)] flex items-center justify-center">
                  <span className="text-white text-sm font-bold">Noir</span>
                </div>
                <h5 className="font-black uppercase text-center">Film Noir</h5>
              </div>
              <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-md">
                <div className="aspect-square bg-gradient-to-br from-blue-400 to-purple-600 rounded-lg mb-4 border-2 border-[var(--ink)] flex items-center justify-center">
                  <span className="text-white text-sm font-bold">Manga</span>
                </div>
                <h5 className="font-black uppercase text-center">Manga Style</h5>
              </div>
              <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-md">
                <div className="aspect-square bg-gradient-to-br from-red-500 to-yellow-400 rounded-lg mb-4 border-2 border-[var(--ink)] flex items-center justify-center">
                  <span className="text-white text-sm font-bold">Superhero</span>
                </div>
                <h5 className="font-black uppercase text-center">Superhero</h5>
              </div>
              <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-md">
                <div className="aspect-square bg-gradient-to-br from-green-400 to-teal-600 rounded-lg mb-4 border-2 border-[var(--ink)] flex items-center justify-center">
                  <span className="text-white text-sm font-bold">Indie</span>
                </div>
                <h5 className="font-black uppercase text-center">Indie Comics</h5>
              </div>
            </div>
          </div>

          {/* Paneling Layouts Section */}
          <div className="mb-12">
            <h3 className="text-4xl font-black uppercase mb-8 text-center">Flexible Panel Layouts</h3>
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-md">
                <div className="aspect-[3/4] border-2 border-[var(--ink)] rounded-lg mb-4 p-2 bg-white">
                  <div className="grid grid-rows-3 gap-2 h-full">
                    <div className="bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                    <div className="bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                    <div className="bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                  </div>
                </div>
                <h5 className="font-black uppercase text-center">Classic 3-Panel</h5>
              </div>
              <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-md">
                <div className="aspect-[3/4] border-2 border-[var(--ink)] rounded-lg mb-4 p-2 bg-white">
                  <div className="grid grid-cols-2 grid-rows-2 gap-2 h-full">
                    <div className="bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                    <div className="bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                    <div className="col-span-2 bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                  </div>
                </div>
                <h5 className="font-black uppercase text-center">Grid Layout</h5>
              </div>
              <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-md">
                <div className="aspect-[3/4] border-2 border-[var(--ink)] rounded-lg mb-4 p-2 bg-white">
                  <div className="grid grid-rows-4 gap-2 h-full">
                    <div className="row-span-2 bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                    <div className="bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                    <div className="bg-[var(--cream-dark)] border border-[var(--ink)] rounded"></div>
                  </div>
                </div>
                <h5 className="font-black uppercase text-center">Dynamic Flow</h5>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="bg-[var(--paper)] rounded-2xl p-12 text-center border-2 border-[var(--ink)] shadow-lg">
            <h3 className="text-5xl font-black uppercase mb-4">Ready to Create?</h3>
            <p className="text-xl font-bold mb-8" style={{ color: 'var(--muted)' }}>
              Start your first comic book workflow and bring your stories to life.
            </p>
            <button
              onClick={() => navigate('/app')}
              className="bg-[var(--orange)] text-[var(--ink)] px-12 py-5 rounded-lg font-black uppercase text-lg border-2 border-[var(--ink)] hover:bg-[var(--yellow)] transition-colors shadow-md"
            >
              Launch Dashboard →
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t-4 border-[var(--ink)] p-8 text-center">
        <p className="text-sm font-bold" style={{ color: 'var(--muted)' }}>
          © 2025 COMICS BOOK · Built for creators
        </p>
      </footer>
    </div>
  );
};
