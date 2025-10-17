# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vibe Reader is a web application for reading terminal output and code files on eink devices during vibe coding sessions. It provides eink-optimized UI with scrollback history, visual scrollbars, and configuration options.

## Development Commands

### Running the Server

```bash
# Development with auto-reload
uv run uvicorn backend.main:app --host 0.0.0.0 --port 28000 --reload

# Production
uv run uvicorn backend.main:app --host 0.0.0.0 --port 28000
```

### Dependency Management

If you encounter network issues, use the proxy:
```bash
HTTP_PROXY=http://127.0.0.1:9082 HTTPS_PROXY=http://127.0.0.1:9082 uv sync
```

## Architecture

### Backend (FastAPI + libtmux)

- **Modular routers**:
  - `backend/main.py` - Main app with router includes
  - `backend/tmux.py` - Tmux endpoints (APIRouter)
  - `backend/files.py` - File browser endpoints (APIRouter)
- **Static file serving**: FastAPI serves frontend from `/frontend` directory at `/static`
- **Tmux integration**: Uses libtmux library to access tmux server with 1000-line scrollback

### Frontend (Vanilla JS)

- **Single-page application**: All UI in `frontend/index.html`
- **Three views**: Tmux, Files, and Config (toggle via navbar)
- **Layout**: Collapsible sidebar + main content area + visual scrollbars
- **Config persistence**: localStorage for scrollback lines and font size settings
- **Eink optimizations**: No animations, high contrast, instant updates (`scroll-behavior: auto`, `transition: none`)

### Critical Implementation Details

**Tmux Window/Pane Indexing**:
- Tmux uses actual indices (can be non-contiguous: 2, 3, 4, 5, 6)
- DO NOT use array positions to access windows/panes
- Always iterate to find matching `window.index` or `pane.index`
- See `backend/tmux.py:47-94` for correct implementation

**Tmux Scrollback History**:
- Backend captures last N lines (default 1000, configurable)
- Uses `pane.capture_pane(start='-1000')` to get scrollback
- Returns only `content` string

**Scrollbar Implementation**:
- Traditional scrollbar design with thumb showing viewport size
- Tmux: Bar represents total scrollback, thumb shows viewport position
- Files: Bar represents file length, thumb shows viewport position
- Position calculation uses scroll ratio: `currentScrollRatio = scrollTop / maxScrollTop`
- Thumb position: `thumbTop = (scrollbarHeight - thumbHeight) * currentScrollRatio`

**Single-pane Window Handling**:
- Windows with one pane show window name as clickable (no pane list)
- Detect via `window.panes.length === 1` in frontend
- Apply `.single-pane` class for special styling

**Auto-scroll Behavior**:
- Tmux: Auto-scroll to end of content when enabled, preserve scroll position when disabled
- File content: Always scrolls to top when loaded
- Manual scrolling: Page up/down buttons scroll 90% of viewport height

**Configuration**:
- Settings stored in localStorage as JSON
- `scrollbackLines`: 100-10000 (default 1000)
- `fontSize`: 12-20px (default 14px)
- Applied dynamically via `element.style.fontSize`

## API Endpoints

### Tmux (backend/tmux.py)
- `GET /api/tmux/tree` - Returns full session/window/pane hierarchy
- `GET /api/tmux/pane/{session}/{window}/{pane}` - Captures pane content with scrollback
  - Returns: `content` (string)

### Files (backend/files.py)
- `GET /api/files?path=<path>` - Lists directory contents
- `GET /api/files/content?path=<path>` - Returns file content

## Design Constraints

1. **Eink-first**: No animations, transitions, or smooth scrolling
2. **Single-page viewport**: All content must fit without page scrolling
3. **High contrast**: Black/white color scheme only
4. **Space-efficient**: Collapsible sidebar, compact controls
