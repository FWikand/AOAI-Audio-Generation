# AI Audio Generator

Transform documents into natural-sounding audio summaries using Azure OpenAI's GPT-4O and GPT-4O-Audio-Preview capabilities.

![Image of the application](image.png)

## Features

- 📄 Support for PDF, TXT, DOC, and DOCX files
- 🔍 Multiple processing methods (Vision Only or Text + Vision)
- 🎯 Customizable processing goals
- ⏱️ Adjustable summary lengths
- 🌍 Multiple language support with flags
- 🗣️ Various voice options and tones
- 🎨 Modern, responsive UI with intuitive controls
- 💾 PostgreSQL database for reliable history storage
- 🔄 Rerun capability with modified settings
- 🗑️ Easy deletion of history entries
- 📱 Mobile-friendly design with glass morphism effects

## History Management

The application now includes a robust history management system:
- View all processed documents with timestamps
- See processing settings for each entry
- Rerun previous entries with new settings
- Delete individual entries with confirmation
- Clear visual feedback for selected entries
- Automatic audio player updates when selecting entries

## Prerequisites

- Docker and Docker Compose (recommended)
- Or for local development:
  - Python 3.8 or higher
  - Poppler (required for PDF processing)
  - PostgreSQL 15 or higher
  - Azure OpenAI API access
  - Azure OpenAI API key and endpoint

## Quick Start with Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set up environment variables:**
   Create a file named `keys.env` in the project root:
   ```env
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_API_KEY=your_api_key_here
   ```

3. **Configure model settings:**
   If needed, edit `config.py` in the project root with the names of your Azure OpenAI model deployments:
   ```python
   # Model Deployments
   AZURE_MODELS = {
       'text': os.getenv('AZURE_OPENAI_TEXT_DEPLOYMENT', 'gpt-4o'),
       'audio': os.getenv('AZURE_OPENAI_AUDIO_DEPLOYMENT', 'gpt-4o-audio-preview'),
   }
   ```

4. **Start the application:**
   ```bash
   # Default setup (port 5001)
   docker-compose up -d

   # If port 5001 is in use, you can override it:
   PORT=8080 docker-compose up -d
   ```

5. **Access the application:**
   - Default: http://localhost:5001
   - Or if you changed the port: http://localhost:YOUR_PORT

6. **View logs:**
   ```bash
   docker-compose logs -f
   ```

7. **Stop the application:**
   ```bash
   docker-compose down  # Keeps the database data
   docker-compose down -v  # Removes all data (fresh start)
   ```

## Local Development Setup

1. **Install Poppler:**
   
   - **macOS:**
     ```bash
     brew install poppler
     ```
   
   - **Ubuntu/Debian:**
     ```bash
     sudo apt-get install poppler-utils
     ```
   
   - **Windows:**
     - Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)
     - Extract and add `bin` directory to PATH

2. **Install PostgreSQL:**
   - [PostgreSQL Downloads](https://www.postgresql.org/download/)
   - Create a database named `aoai_audio`

3. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment:**
   Create `keys.env` with your Azure OpenAI credentials and database URL:
   ```env
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_API_KEY=your_api_key_here
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aoai_audio
   ```

6. **Run the application:**
   ```bash
   python -m flask run --host=0.0.0.0 --port=5001
   ```

## Troubleshooting

### Port Already in Use
If port 5001 is already in use:

1. **Docker setup:**
   ```bash
   # Use a different port (e.g., 8080)
   PORT=8080 docker-compose up -d
   ```

2. **Local setup:**
   ```bash
   # Use a different port (e.g., 8080)
   python -m flask run --host=0.0.0.0 --port=8080
   ```

### Database Issues
- Ensure PostgreSQL is running
- Check connection string in `keys.env`
- For Docker: `docker-compose logs db` to check database logs

## Best Practices

1. **Environment Variables:**
   - Never commit `keys.env` (it's in .gitignore)
   - Use strong passwords in production

2. **Data Persistence:**
   - Database data persists in Docker volume `postgres_data`
   - Backup regularly in production

3. **Security:**
   - Change default PostgreSQL password in production
   - Use SSL in production
   - Keep dependencies updated

4. **Monitoring:**
   - Check application logs: `docker-compose logs -f web`
   - Check database logs: `docker-compose logs -f db`
