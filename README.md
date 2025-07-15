# Reddit User Persona Generator

A production-ready tool that analyzes Reddit users' posts and comments to create detailed user personas with citations. This project uses Reddit API for data extraction and Google Gemini for intelligent persona analysis.

## Features

- **Complete Reddit Profile Analysis**: Scrapes all available posts and comments from a Reddit user
- **AI-Powered Persona Generation**: Uses Google Gemini to create detailed user personas
- **Citation System**: Every insight in the persona is backed by specific post/comment references
- **Robust Error Handling**: Comprehensive error handling and logging
- **Rate Limiting**: Respects Reddit API rate limits
- **Modular Architecture**: Clean, maintainable code structure
- **Security**: Secure API key management with environment variables

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd reddit-persona-generator
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
```

4. **Configure your API credentials** in `.env`:
```bash
# Reddit API Credentials (get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=PersonaGenerator/1.0 by YourUsername

# GEMINI API Credentials (get from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_openai_api_key_here
```

## API Setup

### Reddit API Setup

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Fill in the required fields:
   - Name: Your app name
   - Description: Brief description
   - About URL: (optional)
   - Redirect URI: http://localhost:8080 (required but not used)
5. Copy the client ID (below the app name) and client secret

### GEMINI API Setup

1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key
3. Copy the API key (keep it secure!)

## Usage

### Basic Usage

```bash
python reddit_persona_generator.py https://www.reddit.com/user/username/
```

### Advanced Usage

```bash
python reddit_persona_generator.py https://www.reddit.com/user/username/ \
    --output-dir custom_outputs \
    --max-posts 150 \
    --max-comments 300
```

### Command Line Options

- `url`: Reddit profile URL (required)
- `--output-dir`: Output directory for persona files (default: outputs)
- `--max-posts`: Maximum number of posts to analyze (default: 100)
- `--max-comments`: Maximum number of comments to analyze (default: 200)

## Examples

### Example 1: Basic Analysis
```bash
python reddit_persona_generator.py https://www.reddit.com/user/kojied/
```

### Example 2: Deep Analysis
```bash
python reddit_persona_generator.py https://www.reddit.com/user/Hungry-Move-6603/ \
    --max-posts 200 \
    --max-comments 500
```

## Output Format

The generated persona files include:

### User Profile
- Reddit username and account age
- Karma scores and activity level
- Account creation date

### Demographics
- Estimated age range
- Potential location indicators
- Occupation/profession hints

### Interests & Hobbies
- Primary topics of interest
- Activity levels in different areas
- Specific subreddit preferences

### Personality Analysis
- Communication style
- Emotional patterns
- Social behavior indicators

### Behavioral Patterns
- Posting frequency and timing
- Content preferences
- Interaction style

### Citations
- Each insight is backed by specific post/comment references
- Direct links to source content
- Timestamp information

## Project Structure

```
reddit-persona-generator/
├── README.md                    # Project documentation
├── requirements.txt            # Python dependencies
├── reddit_persona_generator.py # Main executable script
├── utils/                     # Utility modules
│   ├── scraper.py            # Reddit data extraction
│   ├── persona_builder.py    # LLM-powered persona generation
│   └── file_writer.py        # Output formatting and file creation
├── sample_outputs/           # Example outputs
│   ├── kojied_persona.txt
│   └── Hungry-Move-6603_persona.txt
└── reddit_persona_generator.log # Application logs
```

## Error Handling

The application includes comprehensive error handling for:

- Invalid Reddit URLs
- Missing API credentials
- Network connectivity issues
- Rate limiting
- Private/suspended accounts
- API quota exceeded
- Missing user data

## Rate Limiting

The application respects Reddit's API rate limits:
- Maximum 60 requests per minute
- Automatic retry with exponential backoff
- Graceful handling of rate limit errors

## Security

- All API keys are stored in environment variables
- No sensitive data is logged
- Secure credential management
- Input validation and sanitization

## Troubleshooting

### Common Issues

1. **Invalid Reddit URL**: Ensure the URL follows the format `https://www.reddit.com/user/username/`
2. **API Credentials**: Verify all API keys are correctly set in the `.env` file
3. **Rate Limiting**: If you hit rate limits, wait a few minutes before retrying
4. **Private Users**: The tool cannot analyze private or suspended accounts

### Error Messages

- `Missing required environment variables`: Check your `.env` file
- `Invalid Reddit profile URL`: Verify the URL format
- `No posts or comments found`: User might be private or have no content
- `API quota exceeded`: Wait before making more requests


## Disclaimer

This tool is for educational and research purposes. Please respect Reddit's terms of service and user privacy. Always obtain proper consent before analyzing user data in production environments.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `reddit_persona_generator.log`
3. Open an issue on GitHub

---