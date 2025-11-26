# Market Researcher

AI-powered multi-agent system for news, market research, and stock analysis.

## Features

- **News Agent**: Latest news, headlines, and events
- **Market Research Agent**: Product research, prices, features, and reviews
- **Stock Analyst**: Stock prices, market analysis, and trading information
- **General Assistant**: General knowledge queries

## Setup

### Prerequisites

- Python 3.11+
- API Keys:
  - GROQ_API_KEY (from https://console.groq.com/)
  - NEWS_API_KEY (from https://newsapi.org/)
  - RAPIDAPI_KEY (from https://rapidapi.com/)

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   NEWS_API_KEY=your_news_api_key_here
   RAPIDAPI_KEY=your_rapidapi_key_here
   ```

4. Run the server:
   ```bash
   python api/run_server.py
   ```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Docker Deployment

### Using Docker Compose (Recommended)

1. Set environment variables in your shell or create a `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   NEWS_API_KEY=your_news_api_key_here
   RAPIDAPI_KEY=your_rapidapi_key_here
   ```

2. Build and run:
   ```bash
   docker-compose up -d
   ```

### Using Docker directly

1. Build the image:
   ```bash
   docker build -t market-researcher .
   ```

2. Run the container with environment variables:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e GROQ_API_KEY=your_groq_api_key_here \
     -e NEWS_API_KEY=your_news_api_key_here \
     -e RAPIDAPI_KEY=your_rapidapi_key_here \
     --name market-researcher \
     market-researcher
   ```

Or use a `.env` file:
   ```bash
   docker run -d \
     -p 8000:8000 \
     --env-file .env \
     --name market-researcher \
     market-researcher
   ```

## API Endpoints

- `POST /api/v1/query` - Process a query through the multi-agent system
- `GET /api/v1/query/{query_id}` - Get a specific query by ID
- `GET /api/v1/history` - Get query history with filtering and pagination
- `GET /api/v1/history/stats` - Get query statistics
- `DELETE /api/v1/history/{query_id}` - Delete a specific query
- `DELETE /api/v1/history?confirm=true` - Clear all history
- `GET /health` - Health check endpoint

## Configuration

Environment variables are loaded from:
1. System environment variables (highest priority)
2. `.env` file in the project root
3. Docker environment variables (when running in Docker)

The application validates that all required API keys are present at startup. If any keys are missing, the application will fail to start with a clear error message.

## License

MIT

