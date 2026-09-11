# 🎟️ Implementation Tickets: Landing Page Tracer Bullet

## [TASK-001] feat(routing): implement root route and basic template structure
**Description & Contexte**
In order to establish the entry point for the application, we need to implement the root URL (`/`) which is currently non-existent. This is the first step of the "tracer bullet" to validate that the routing and Jinja2 integration work as expected.

**Tâches techniques**
- [ ] Modify `main.py`: Add `@app.get("/", response_class=HTMLResponse)`.
- [ ] Create `templates/landing.html` with a minimal HTML skeleton.
- [ ] Ensure the route returns `templates.TemplateResponse(request=request, name="landing.html")`.

**Tests & Critères d'acceptation**
- [x] Navigating to `http://localhost:8000/` returns a 200 OK status.
- [x] The page renders a valid HTML structure (no 500 error).
- [x] The route is clearly visible in the FastAPI documentation (Swagger UI).

**Dépendances**
- None (Prerequisite for all other tasks).

**Labels suggérés**
`backend`, `infrastructure`, `feature`

---

## [TASK-002] feat(frontend): implement landing page content and styling
**Description & Contexte**
Once the routing is functional, we need to populate the landing page with the content defined in `docs/spec.md`. This includes the Hero section, Features, and the Call to Action, using a minimalist CSS approach to ensure no regressions on existing pages.

**Tâches techniques**
- [ ] Update `templates/landing.html`:
    - Add **Hero Section**: Title "E-Portfolio", Subtitle "Valorisez vos compétences...", and a "Commencer" button.
    - Add **Features Section**: List the 3 features defined in the spec.
    - Add **CTA Section**: "Prêt à créer votre vitrine ?" with a "Se connecter" link.
- [ ] Implement styling:
    - Either use existing CSS or create `static/css/landing.css`.
    - Ensure the "Commencer" button links to `/login`.
    - Ensure the design is responsive (mobile/desktop).

**Tests & Critères d'acceptation**
- [x] The "Commencer" button correctly redirects to `/login`.
- [x] All text content matches the requirements in `docs/spec.md`.
- [x] The page is visually coherent and does not break on mobile viewports.

**Dépendances**
- [TASK-001]

**Labels suggagés**
`frontend`, `feature`, `ui`

---

## [TASK-003] test(qa): verify landing page integration and regression testing
**Description & Contexte**
Final validation step to ensure the new landing page is correctly integrated and, most importantly, that it has not broken the existing functionality of the application (specifically the `/login` and `/portfolios/` routes).

**Tâches techniques**
- [ ] Manual test: Verify the landing page loads at `/`.
- [ ] Manual test: Verify the redirection from `/` to `/login` works.
- [ ] Regression test: Verify that `/login` still allows authentication.
- [ ] Regression test: Verify that `/portfolios/` still displays the list of portfolios.

**Tests & Critables d'acceptation**
- [x] The landing page is accessible without errors.
- [x] No regressions found on existing routes (`/login`, `/portfolios/`, `/portfolios/{id}`).

**Dépendances**
- [TASK-002]

**Labels suggérés**
`qa`, `testing`

**Blocking relationships**
| Task | Blocked by | Blocks | Can start when |
| --- | --- | --- | --- |
| TASK-001 – Root route and template structure | Nothing | TASK-002 and, transitively, TASK-003 | Immediately |
| TASK-002 – Landing-page content and styling | TASK-001 | TASK-003 | The / route and landing.html template exist and work |
| TASK-003 – Integration and regression testing | TASK-002; transitively TASK-001 | Nothing | The complete landing page is implemented |