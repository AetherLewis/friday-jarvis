# Quick Start Guide - Instagram Reel Archive

## 5-Minute Setup

### Step 1: Prepare Your Environment
```bash
cd c:\Users\User\friday_jarvis
myjarvis\Scripts\activate
```

### Step 2: Get Your Tokens

**GitHub Token:**
1. Visit: https://github.com/settings/tokens/new
2. Name: "Instagram Archive"
3. Select scope: `repo` (all)
4. Copy the token

**Google API Key:**
1. Visit: https://console.cloud.google.com/
2. Create new project
3. Enable "Generative AI API"
4. Create API key
5. Copy the key

### Step 3: Update .env File

Add these lines to your `.env`:
```env
GITHUB_TOKEN=your_copied_github_token_here
GOOGLE_API_KEY=your_copied_google_key_here
```

### Step 4: Prepare Chat Export

Option A - Sample Data:
- Use the included `chat_log.json` (has 7 sample reels)

Option B - Real Data:
- Export from Instagram: Settings → Download Your Data
- Extract the zip
- Find the conversations.json
- Copy to `chat_log.json` in this directory

### Step 5: Run It!
```bash
python instagram_archive.py
```

### Expected Output:
```
======================================================================
Instagram Reel Archive Manager
======================================================================

[1/5] Parsing chat file...
[2/5] Extracting Reel entries...
Found 7 Reel entries
[3/5] Summarizing and categorizing reels (using Gemini)...
Processing reel 1/7...
Processing reel 2/7...
...
[4/5] Generating markdown content...
[5/5] Pushing to GitHub repository...

======================================================================
✓ Process completed successfully!
Repository: https://github.com/YOUR_USERNAME/The%20Belmont%20Archive
======================================================================
```

### Check Your Results:
1. Go to: https://github.com/YOUR_USERNAME
2. Find "The Belmont Archive" repository
3. Open `summaries.md` to see all your Reel summaries organized by category!

---

## Troubleshooting

**"GITHUB_TOKEN not found"**
```bash
echo $env:GITHUB_TOKEN  # Check if set
# If empty, add to .env file again and restart terminal
```

**"GOOGLE_API_KEY not found"**
```bash
# Verify it's in .env with correct format:
GOOGLE_API_KEY=AIzaSy...
```

**No reels extracted**
- Make sure chat_log.json contains messages with links like:
- `https://instagram.com/reels/ABC123...` or
- `instagram.com/reels/ABC123...`

**GitHub push failed**
- Check token has `repo` scope: https://github.com/settings/tokens
- Verify token hasn't expired (check email)
- Check internet connection

---

## What Happens Next?

Each time you run the script:
1. ✅ It reads your chat file
2. ✅ Finds all Reel links
3. ✅ Summarizes with AI (1-3 sentences each)
4. ✅ Groups by category (Tech, Entertainment, Food, etc.)
5. ✅ Updates your GitHub repository with new summaries

The file on GitHub keeps growing with each run - old summaries stay, new ones are added!

---

## Customization

**Change repository name:**
```python
asyncio.run(process_instagram_chat(
    chat_file_path="chat_log.json",
    github_token=os.getenv("GITHUB_TOKEN"),
    repo_name="My Amazing Reels",  # Changed!
    file_name="summaries.md"
))
```

**Use different chat file:**
```python
process_instagram_chat(
    chat_file_path="chat_backup.json",  # Different file
    ...
)
```

**Change output filename:**
```python
process_instagram_chat(
    ...,
    file_name="reel_archive.md"  # Changed!
)
```

---

## Sample Output (summaries.md)

```markdown
# Instagram Reel Archive

Total Reels: 7

## Technology

### Alice
**Date:** 2024-01-15 10:30:00
**Link:** https://instagram.com/reels/CX1a2b3c4d5/
**Summary:** A cutting-edge tech tutorial that clearly explains new features in an engaging way.

## Entertainment

### Bob
**Date:** 2024-01-15 14:45:00
**Link:** https://instagram.com/reels/CX9z8y7x6w5v/
**Summary:** A hilarious cooking show with comedy gold at the 45-second mark.

...
```

---

## Need Help?

- Check `instagram_archive.py` for detailed documentation
- Read `INSTAGRAM_ARCHIVE_README.md` for complete guide
- All operations are logged to console with timestamps

Enjoy your AI-powered Reel archive! 🎬✨
