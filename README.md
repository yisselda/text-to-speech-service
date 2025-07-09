# Text-to-Speech Service

Microservice providing speech synthesis using Facebook's MMS-TTS model.

## Features
- Support for 1000+ languages with Haitian Creole model
- Multiple voice options
- Streaming audio generation
- Various audio format outputs

## Quick Start

```bash
docker-compose up
```

## API Endpoints

- `POST /api/v1/synthesize` - Convert text to speech
- `GET /api/v1/voices/{language}` - Get available voices

## License
MIT
