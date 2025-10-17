# HFStudio

A modern Text-to-Speech studio that supports both local and API-based model execution. Built with Svelte and FastAPI.

## Features

- 🎙️ **Text-to-Speech Generation** - Convert text to natural-sounding speech
- 🔄 **Dual Mode Operation** - Switch between API and local model execution
- 🎛️ **Voice Controls** - Adjust speed, stability, and similarity parameters
- 📦 **Multiple TTS Models** - Support for HuggingFace, Coqui TTS, and more
- 🎵 **Audio Playback** - Built-in audio player with download capability
- 🚀 **Fast & Responsive** - Modern web interface with real-time feedback

## Quick Start

### API Mode (No Installation Required)
1. Visit the web interface
2. Enter your text
3. Select a voice and click "Generate"

### Local Mode

#### Install the Python package:
```bash
pip install hfstudio
```

#### Start the server:
```bash
hfstudio
```

The application will be available at `http://localhost:8000`

## Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Git

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
cd backend
pip install -e .
hfstudio --dev
```

## Architecture

- **Frontend**: SvelteKit + TailwindCSS
- **Backend**: FastAPI + Transformers/Coqui TTS
- **Communication**: REST API with async support

## Configuration

Create a `.env` file in the frontend directory:
```env
PUBLIC_API_URL=http://localhost:8000
PUBLIC_DEFAULT_MODE=api
```

Create a `config.yaml` in the backend directory for advanced settings.

## API Documentation

Once the server is running, visit:
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Roadmap

- [x] Basic TTS functionality
- [x] Mode switching (API/Local)
- [ ] Voice cloning support
- [ ] Batch processing
- [ ] Real-time streaming
- [ ] Desktop application (Electron)

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/yourusername/hfstudio/issues) page.
