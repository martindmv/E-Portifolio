# ADR 0001: Use Jinja2 for Server-Side Rendering (SSR)

## Status
Accepted

## Context
The project requires a way to serve dynamic HTML content (like the Portfolio details and the new Landing Page) to the user's browser. We need a templating engine that integrates seamlessly with FastAPI and allows for easy injection of database models (SQLModel) into the HTML.

## Decision
We will use **Jinja2** as the primary templating engine for server-side rendering.

## Rationale
1. **Native Integration**: Jinja2 has excellent, first-class support in FastAPI via `Jinja2Templates`.
2. **Simplicity**: It allows us to build pages using standard HTML/CSS while injecting Python objects directly into the templates, which is perfect for our "Tracer Bullet" approach.
3. **Performance**: For the current scope of the application (serving portfolios and landing pages), the overhead of SSR is negligible and avoids the complexity of a heavy SPA (Single Page Application) framework like React or Vue during this phase.
4. **Ease of Development**: It allows us to stay within the Python ecosystem and use standard web development patterns (templates, static files).

## Consequences
- **Pros**: Faster initial development, better SEO for public portfolios, and reduced client-side complexity.
- **Cons**: Higher server load compared to a purely static site (though negligible at our current scale) and slightly less "app-like" interactivity compared to a full SPA.
