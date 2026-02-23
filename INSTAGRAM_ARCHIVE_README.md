# Instagram Reel Archive Manager

A Python script that automatically extracts Instagram Reel links from chat exports, summarizes them using Gemini AI, and commits the organized summaries to a GitHub repository.

## 🎯 Features

✅ **Multi-Format Support**: Reads Instagram chats as JSON or TXT exports  
✅ **Smart Link Extraction**: Automatically detects and extracts Instagram Reel URLs  
✅ **AI-Powered Summaries**: Uses Gemini AI to create 1-3 sentence summaries  
✅ **Auto-Categorization**: Intelligently organizes reels by content type (Tech, Entertainment, etc.)  
✅ **GitHub Integration**: Automatically commits summaries to "The Belmont Archive" repository  
✅ **Modular LLM**: Easy to swap Gemini for OpenAI, Claude, or other LLMs  
✅ **Comprehensive Logging**: Detailed logs for debugging and monitoring  
✅ **Error Handling**: Graceful error handling for missing captions, invalid links, etc.  

---

## 📋 Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- `chat_log.json` or `chat_log.txt` (Instagram chat export)
- GitHub token (for repository access)
- Google API key (for Gemini AI)

---

## 🚀 Installation

### 1. Activate Virtual Environment
```bash
cd friday_jarvis
myjarvis\Scripts\activate  # Windows
# OR
source myjarvis/bin/activate  # macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install PyGithub python-dotenv google-generativeai
```

---

## 🔐 Setup (Environment Variables)

Add the following to your `.env` file:

```env
# Google API (for Gemini AI)
GOOGLE_API_KEY=your_google_api_key_here

# GitHub Access
GITHUB_TOKEN=your_github_personal_access_token_here
```

### How to Get These Tokens:

**GitHub Token:**
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes: `repo` (full control of private repositories)
4. Copy and paste into `.env`

**Google API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Generative AI API
4. Create an API key (Application default credentials)
5. Copy and paste into `.env`

---

## 📝 Preparing Your Chat Export

### Option 1: Export from Instagram (JSON)
1. Use Instagram's built-in export feature (Settings → Data Download)
2. Extract the zip file
3. Find the chat export JSON file
4. Rename to `chat_log.json` in the project directory

### Option 2: Manual TXT Export
Create a `chat_log.txt` file with this format:
```
[2024-01-15 10:30:00] Alice: Check out this reel! https://instagram.com/reels/CX1a2b3c4d5/ Amazing content
[2024-01-15 14:45:00] Bob: This is hilarious 😂 https://instagram.com/reels/CX9z8y7x6w5v/ Watch from the start
```

---

## 🎬 Usage

### Quick Start
```bash
python instagram_archive.py
```

The script will:
1. ✓ Parse your chat file
2. ✓ Extract Reel links and captions
3. ✓ Generate summaries using Gemini AI
4. ✓ Categorize by content type
5. ✓ Push to GitHub repository

### Advanced: Custom Usage

```python
import asyncio
from instagram_archive import process_instagram_chat

# Run with custom repository name
asyncio.run(process_instagram_chat(
    chat_file_path="chat_log.json",
    github_token="your_token",
    repo_name="My Custom Repo",
    file_name="archive.md"
))
```

---

## 📊 Output Example

Your GitHub repository will contain `summaries.md`:

```markdown
# Instagram Reel Archive

*Last Updated: 2024-01-18 15:30:45*

Total Reels: 7

---

## Technology

### Alice

**Date:** 2024-01-15 10:30:00

**Link:** [https://instagram.com/reels/CX1a2b3c4d5/](https://instagram.com/reels/CX1a2b3c4d5/)

**Original Caption:**
```
Check out this amazing tech tutorial! https://instagram.com/reels/CX1a2b3c4d5/ The new features are incredible and easy to follow.
```

**Summary:** This reel is a comprehensive tech tutorial showcasing new features that are easy to understand and implement. The content is engaging and informative for anyone interested in learning cutting-edge technology.

---

## Entertainment

### Bob

**Date:** 2024-01-15 14:45:00

**Link:** [https://instagram.com/reels/CX9z8y7x6w5v/](https://instagram.com/reels/CX9z8y7x6w5v/)

**Original Caption:**
```
This cooking show is hilarious 😂 https://instagram.com/reels/CX9z8y7x6w5v/ You have to watch the part at 45 seconds!
```

**Summary:** A comedic cooking show where the humor peaks at the 45-second mark, providing entertainment and laughs for food and comedy enthusiasts.

---
```

---

## 🔄 Modular LLM Architecture

### Default: Gemini
```python
from instagram_archive import GeminiSummarizer, ReelProcessor

summarizer = GeminiSummarizer()
processor = ReelProcessor(summarizer)
```

### Custom: Implement Your Own LLM

```python
from instagram_archive import LLMSummarizer

class OpenAISummarizer(LLMSummarizer):
    async def summarize(self, text: str) -> str:
        # Your OpenAI implementation
        pass
    
    async def categorize(self, text: str) -> str:
        # Your categorization logic
        pass

# Use your custom summarizer
summarizer = OpenAISummarizer()
processor = ReelProcessor(summarizer)
```

---

## 📂 Project Structure

```
friday_jarvis/
├── instagram_archive.py      # Main script
├── chat_log.json            # Sample/your chat export
├── email_module.py          # Email utilities
├── tools.py                 # LiveKit agent tools
├── agent.py                 # Friday AI agent
├── prompts.py               # Agent instructions
├── requirements.txt         # Dependencies
└── .env                     # Configuration (keep secret!)
```

---

## 🛠️ Logging

All operations are logged to the console with timestamps:

```
2024-01-18 15:30:00 - instagram_archive - INFO - Starting Instagram Reel Archive Process
2024-01-18 15:30:01 - instagram_archive - INFO - Parsing chat file...
2024-01-18 15:30:02 - instagram_archive - INFO - Found 7 Reel entries in messages
2024-01-18 15:30:03 - instagram_archive - INFO - Processing reel 1/7...
...
```

---

## ⚠️ Error Handling

The script gracefully handles:
- ❌ Missing API keys → Logs and exits
- ❌ Invalid chat file → Skips and logs error
- ❌ Failed Gemini requests → Logs error message in summary
- ❌ GitHub push failures → Logs detailed error
- ❌ Malformed messages → Skips invalid entries

---

## 🔐 Security Notes

⚠️ **Never commit your `.env` file to GitHub!**

```bash
# Add to .gitignore
.env
.env.local
secrets.json
```

Tokens and secrets are stored locally and never exposed.

---

## 📝 Chat File Formats

### JSON Format (Instagram Export)
```json
{
  "messages": [
    {
      "date": "2024-01-15 10:30:00",
      "sender": "Alice",
      "text": "Caption with link https://instagram.com/reels/..."
    }
  ]
}
```

### TXT Format
```
[2024-01-15 10:30:00] Alice: Caption with link https://instagram.com/reels/...
[2024-01-15 14:45:00] Bob: Another caption https://instagram.com/reels/...
```

---

## 🚨 Troubleshooting

### No Reels Found
- Check that your chat file contains Instagram Reel links
- Verify the link format: `instagram.com/reels/` or `instagram.com/reel/`

### GitHub Push Failed
- Verify your `GITHUB_TOKEN` is valid and has `repo` scope
- Ensure the token hasn't expired
- Check GitHub API rate limits

### Gemini Summarization Failed
- Verify `GOOGLE_API_KEY` is correct
- Check if your quota is exhausted
- Ensure the API is enabled in Google Cloud Console

### Encoding Issues
- Make sure your chat file is saved as UTF-8
- Some export formats may require manual conversion

---

## 📚 API Classes Reference

### `ReelEntry` (Dataclass)
```python
@dataclass
class ReelEntry:
    date: str                    # Message timestamp
    sender: str                  # Who sent it
    link: str                    # Reel URL
    caption: str                 # Original caption
    summary: Optional[str] = None  # AI summary
    category: Optional[str] = None # Content category
```

### `LLMSummarizer` (Abstract)
```python
class LLMSummarizer(ABC):
    async def summarize(text: str) -> str  # 1-3 sentence summary
    async def categorize(text: str) -> str # Content category
```

### `ChatParser`
```python
ChatParser.parse_chat_file(path) -> List[Dict]     # Auto-detect format
ChatParser.extract_reels(messages) -> List[ReelEntry]  # Extract links
```

### `GitHubManager`
```python
GitHubManager(token, repo_name)
manager.push_summaries(content, filename)  # Commit to repo
manager.get_repo_url() -> str  # Get repo URL
```

---

## 🤝 Contributing

Want to add support for other LLMs? Create a new class that extends `LLMSummarizer`:

```python
class ClaudeSummarizer(LLMSummarizer):
    # Implement summarize() and categorize()
    pass
```

---

## 📄 License

This project is part of the Friday Jarvis AI Assistant suite.

---

## 🎯 Next Steps

1. ✅ Export your Instagram chat
2. ✅ Set up environment variables
3. ✅ Run: `python instagram_archive.py`
4. ✅ Check your GitHub repository!

---

**Questions?** Check the logs for detailed error messages or review the inline code comments.
