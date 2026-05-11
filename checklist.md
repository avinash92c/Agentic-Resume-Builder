# Resume Builder — Task Breakdown

## Project Setup
- [ ] Poetry init + dependencies
- [ ] Docker + Docker Compose (app + LaTeX + MariaDB containers)
- [ ] Folder structure

## Data Layer
- [ ] Pydantic schema for base resume
- [ ] MariaDB setup + connection pooling
- [ ] Table per section (personal, summary, skills, experience, certifications)
- [ ] Read/write helpers per section
- [ ] File paths config (PDFs on disk)

## Conversation Layer
- [ ] Claude API integration
- [ ] Session state machine (section flow)
- [ ] Prompt templates per section
- [ ] Refinement loop logic (2 max for skills/summary, 5 max for work history)
- [ ] Response → structured model parser
- [ ] Cross-section context fetch (for Final Draft)

## Section Flows
- [ ] Personal Details flow
- [ ] Educational Qualifications flow
- [ ] Professional Summary flow (LLM generated, 2 refinements)
- [ ] Skills flow (LLM categorized, 2 refinements)
- [ ] Work History flow (per project, 5 refinement loops)
- [ ] Certifications flow
- [ ] Final Draft flow (consolidate + cross-reference all sections)

## Templates
- [ ] minimal.tex
- [ ] modern.tex
- [ ] classic.tex
- [ ] academic.tex
- [ ] creative.tex
- [ ] Jinja2 rendering pipeline

## PDF Export
- [ ] pdflatex runner in Docker
- [ ] PDF generation endpoint
- [ ] Error handling

## API
- [ ] Chat endpoint
- [ ] Resume CRUD endpoints
- [ ] Template selection endpoint
- [ ] PDF download endpoint

## Frontend
- [ ] Chat UI
- [ ] Resume preview
- [ ] Template switcher