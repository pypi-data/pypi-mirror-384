# ii-slide

AI-powered PowerPoint synchronization backend that enables bidirectional editing between AI and user interfaces.

## Project Structure

```
ii-slide/
├── src/ii_slide/           # Main package source code
│   ├── __init__.py          # Package exports
│   ├── models.py            # Data models for PowerPoint elements
│   ├── sync_manager.py      # File watcher and sync logic
│   └── backend.py           # FastAPI server with WebSocket support
├── examples/                # Example files and demos
│   ├── test_parser.py       # Test script for parsing PowerPoint JSON
│   ├── frontend_example.html # WebSocket client demo
│   └── updated_presentation.json # Sample output
├── pyproject.toml          # Modern Python packaging configuration
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Installation

### Development Installation

```bash
cd ii-slide
pip install -e .
```

### Production Installation

```bash
pip install .
```

## Quick Start

### 1. Start the Backend Server

```bash
cd ii-slide
python -m ii_slide.backend
```

The server runs on `http://localhost:8000`

### 2. Test with Example

Open `examples/frontend_example.html` in your browser to test the WebSocket connection.

### 3. Parse PowerPoint JSON

```bash
cd examples
python test_parser.py
```

## How It Works

### Two-Layer Architecture

1. **Full PowerPoint JSON** - Complete presentation with styling and positioning
2. **AI Skeleton** - Simplified content structure for AI editing

### Data Flow

1. **Frontend → Backend**: User edits trigger updates to both presentation and skeleton
2. **AI → Backend**: AI modifies skeleton file, changes sync to presentation
3. **Real-time Sync**: All clients receive updates via WebSocket

### Example Skeleton Format

```json
{
  "presentationType": "traditional",
  "slideCount": 1,
  "slides": [
    {
      "id": "slide_id",
      "type": "end",
      "texts": [
        {
          "type": "text",
          "id": "element_id",
          "content": "Hello World",
          "role": "title"
        }
      ],
      "images": [
        {
          "type": "image",
          "id": "img_id",
          "src": "https://example.com/image.png"
        }
      ]
    }
  ]
}
```

## API Usage

### REST Endpoints

- `GET /api/status` - Get sync status
- `GET /api/presentation` - Get full presentation JSON
- `GET /api/skeleton` - Get AI-friendly skeleton
- `POST /api/frontend-change` - Submit frontend changes
- `POST /api/sync-from-skeleton` - Force sync from skeleton
- `POST /api/reset-skeleton` - Reset skeleton from presentation

### WebSocket

Connect to `ws://localhost:8000/ws` for real-time updates.

#### Send Message (Frontend → Backend)
```javascript
ws.send(JSON.stringify({
  type: 'frontend_change',
  element_id: 'text_element_id',
  change_type: 'content_edit',
  changes: { content: 'New text content' }
}));
```

#### Receive Message (Backend → Frontend)
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'skeleton_update') {
    // AI has updated the skeleton
    console.log('AI updated content');
  }
};
```

## File Watching

The system automatically watches `skeleton.json` for changes:

1. AI writes to `skeleton.json`
2. File watcher detects change
3. Backend applies changes to presentation
4. All clients receive updates

## Supported Elements

Currently supports:
- **Text**: Title, body text with HTML formatting
- **Image**: Images with URLs and positioning
- **Shape**: Basic shapes with optional text content

### Adding New Element Types

When you encounter unsupported elements:

1. Check error logs for full element structure
2. Add new element class in `src/ii_slide/models.py`
3. Update `Slide.from_dict()` to handle the new type
4. Implement `to_skeleton()` and `update_from_skeleton()` methods

## Configuration

### Change Sync Behavior

Edit `sync_manager.py` to modify:
- Debounce timing
- Conflict resolution strategy
- File paths

### Customize Skeleton Format

Modify the `to_skeleton()` methods in `models.py` to change how content is represented for AI.

## Development

### Running Examples

```bash
# Test JSON parsing
cd examples && python test_parser.py

# Start server and open frontend example
python -m ii_slide.backend &
open examples/frontend_example.html
```

### Package Structure

- `src/ii_slide/models.py` - Data models and JSON parsing
- `src/ii_slide/sync_manager.py` - File watching and sync logic
- `src/ii_slide/backend.py` - FastAPI server with WebSocket
- `src/ii_slide/__init__.py` - Package exports

The package follows modern Python packaging standards with `pyproject.toml` and the `src/` layout.