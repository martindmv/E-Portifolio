# 📄 Specification: Landing Page Tracer Bullet

## 🎯 Objective
Implement a minimal, functional landing page at the root URL (`/`) to serve as the entry point for the E-Portfolio application. This is a **tracer bullet**: the goal is to validate the routing, templating, and static file serving infrastructure without over-engineering the design or content.

## 🛠 Technical Context
- **Framework**: FastAPI
- **Templating Engine**: Jinja2
- **Routing**: Addition of a new GET route at `/` in `main.py`.
- **Styling**: Use existing project CSS or a dedicated minimal `static/css/landing.css` to avoid side effects on existing pages.
- **Deployment**: Must be compatible with the existing Render.com setup.

## 🏗 Implementation Details

### 1. Routing (`main.py`)
- Add a new endpoint: `@app.get("/", response_class=HTMLResponse)`.
- The endpoint must render `templates/landing.html`.
- Context passed to template: None (minimalist).

### 2. Template (`templates/landing.html`)
The template will follow the existing structure of `home.html` (for consistency) and include:
- **Hero Section**: 
    - Title: "E-Portfolio"
    - Subtitle: "Valorisez vos compétences et vos expériences en un clin d'œil."
    - Primary Action: A button labeled "Commencer" linking to `/login`.
- **Features Section (Minimalist)**:
    - Feature 1: "Gestion des expériences"
    - Feature 2: "Présentation de projets"
    - Feature 3: "Mise en avant des compétences"
- **Call to Action (CTA) Section**:
    - Text: "Prêt à créer votre vitrine ?"
    - Link: "Se connecter" (pointing to `/login`).

### 3. Styling
- **Constraint**: Do not modify existing CSS files used by `home.html` or `login.html`.
- **Approach**: 
    - Create `static/css/landing.css` if necessary.
    - Use a simple, clean layout (Flexbox/Grid) that mirrors the current app's aesthetic (clean, professional).

## 🚀 Definition of Done (DoD)
- [ ] The URL `http://localhost:8000/` (and production URL) loads the new page.
- [ ] The "Commencer" button successfully redirects the user to the `/login` route.
- [ ] The page is responsive (works on mobile and desktop).
- [ ] No regressions are introduced in the existing `/portfolios/` or `/login` routes.

## 🚫 Out of Scope
- Detailed marketing copywriting.
- Advanced animations or interactive elements.
- Integration of dynamic data from the database (e.g., "X portfolios already created").
- Implementation of a new frontend framework.
