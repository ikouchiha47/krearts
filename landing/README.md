# Krearts Landing Page

A strategic landing page for Krearts (Creative Arts) - an AI-powered platform that creates character-locked, agent-driven visual narratives for Instagram carousels. Built with vanilla HTML, CSS, and JavaScript using CDN-hosted libraries.

## Strategic Positioning

This landing page addresses three core problems in AI content generation:
1. **Character Consistency** - Solving "facial feature drift" with character-locked generation
2. **Writer's Block** - Using generative agents instead of requiring scripts
3. **AI Fatigue** - Creating emergent narratives that surprise and engage

## Features

- **Problem-Solution Framework** - Clear articulation of user pain points and solutions
- **Real Examples** - Showcases actual noir detective story with character memory and dialogue
- **Agent-Driven Approach** - Emphasizes the unique generative agent architecture
- **Feather Icons** - Clean, professional icon system (no emojis)
- **GSAP Animations** - Smooth scroll-triggered animations
- **CTA Click Tracking** - Built-in analytics for conversion optimization
- **SEO Optimized** - Strategic meta tags and content structure
- **GitHub Pages Ready** - No build process required

## Technologies Used

- HTML5
- CSS3 (Custom Properties, Grid, Flexbox)
- JavaScript (ES6+)
- GSAP 3.12.4 (Animation library)
- Feather Icons (Icon system)
- Google Fonts (Inter & Crimson Pro)

## Quick Start

1. Clone or download this repository
2. Open `index.html` in your browser
3. That's it! No build process needed.

## Deployment to GitHub Pages

1. Create a new repository on GitHub
2. Push these files to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```
3. Go to repository Settings > Pages
4. Select "main" branch as source
5. Your site will be live at `https://YOUR_USERNAME.github.io/YOUR_REPO/`

## File Structure

```
.
├── index.html          # Main HTML file
├── styles.css          # All styles and responsive design
├── script.js           # JavaScript functionality and animations
└── README.md          # This file
```

## CTA Tracking

The landing page includes built-in click tracking for all CTA buttons. Clicks are logged to:
- Browser console (for development)
- LocalStorage (for demo purposes)

To integrate with your analytics service, modify the `trackCTAClick()` function in `script.js`:

```javascript
function trackCTAClick(ctaName) {
    // Send to your analytics service
    fetch('/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            event: 'cta_click',
            cta: ctaName,
            timestamp: new Date().toISOString()
        })
    });
}
```

## Content Strategy

The landing page follows a specific narrative flow:

1. **Hero** - Bold claim: "Stop Writing Stories. Start Generating Drama."
2. **Problem Section** - Three core pain points with solutions
3. **How It Works** - 4-step process from storyline to Instagram carousel
4. **Examples** - Real Blood Red Lotus noir detective story showcasing:
   - Character consistency across panels
   - Memory system (observations, reflections, goals)
   - Emergent agent-generated dialogue
5. **CTA** - "Your Blood Red Lotus Is Waiting"

## Customization

### Colors
Edit CSS variables in `styles.css`:
```css
:root {
    --primary: #dc2626;  /* Red for noir theme */
    --noir-red: #8b0000;
    --noir-gold: #d4af37;
    --dark: #0f172a;
}
```

### Content
All content is in `index.html`. Key sections to customize:
- Hero title and subtitle
- Problem cards (3 pain points)
- Step descriptions (4 steps)
- Example showcase (Blood Red Lotus panels)

### Animations
Modify GSAP animations in `script.js` in the `initAnimations()` function.

## SEO Optimization

The page includes:
- Semantic HTML5 elements
- Meta descriptions and keywords
- Open Graph tags for social sharing
- Twitter Card tags
- Proper heading hierarchy
- Alt text for images (add when using real images)

## Performance

- All external resources loaded via CDN
- Minimal JavaScript bundle
- CSS optimized for performance
- No build process overhead

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

Free to use for personal and commercial projects.

## Credits

- Fonts: Google Fonts (Inter, Playfair Display)
- Animations: GSAP by GreenSock
- Icons: Unicode Emoji

---

Built with ❤️ for content creators
