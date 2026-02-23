"""
Instagram Reel Archive Manager

A Python script that automatically extracts Instagram Reel links from chat exports,
summarizes them using Gemini AI, and commits the organized summaries to a GitHub repository.

Features:
- Multi-format support (JSON/TXT chat exports)
- AI-powered summarization using Gemini
- Smart categorization by content type
- GitHub integration with automatic commits
- Modular LLM architecture for easy swapping
- Comprehensive error handling and logging
"""

import os
import re
import json
import logging
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime
from abc import ABC, abstractmethod
from dotenv import load_dotenv

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("Warning: PyGithub not installed. GitHub integration disabled.")

import google.generativeai as genai

# ========================
# CONFIGURATION
# ========================

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found in environment variables")
else:
    genai.configure(api_key=GOOGLE_API_KEY)


# ========================
# DATA STRUCTURES
# ========================

@dataclass
class ReelEntry:
    """Represents a single Instagram Reel entry extracted from chat."""
    date: str
    sender: str
    link: str
    caption: str
    summary: Optional[str] = None
    category: Optional[str] = None


# ========================
# ABSTRACT LLM LAYER
# ========================

class LLMSummarizer(ABC):
    """
    Abstract base class for LLM-based summarization.
    
    This allows easy swapping between different LLMs:
    - GeminiSummarizer (current)
    - OpenAISummarizer (OpenAI)
    - ClaudeSummarizer (Anthropic)
    - Custom implementations
    """
    
    @abstractmethod
    async def summarize(self, text: str) -> str:
        """Summarize text into 1-3 sentences."""
        pass
    
    @abstractmethod
    async def categorize(self, text: str) -> str:
        """Categorize text into a content category."""
        pass


# ========================
# GEMINI IMPLEMENTATION
# ========================

class GeminiSummarizer(LLMSummarizer):
    """Uses Google Gemini API for summarization and categorization."""
    
    def __init__(self):
        """Initialize Gemini model."""
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini summarizer initialized")
    
    async def summarize(self, text: str) -> str:
        """
        Summarize text into 1-3 sentences using Gemini.
        
        Args:
            text: The text to summarize
            
        Returns:
            A 1-3 sentence summary
        """
        try:
            prompt = f"""
            Summarize the following Instagram reel caption in 1-3 sentences. 
            Be concise and capture the main idea:
            
            Caption: {text}
            """
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                prompt
            )
            
            summary = response.text.strip()
            logger.info("Successfully summarized text")
            return summary
        
        except Exception as e:
            logger.error(f"Failed to summarize: {str(e)}")
            return f"[Summary unavailable: {str(e)}]"
    
    async def categorize(self, text: str) -> str:
        """
        Categorize text using Gemini.
        
        Args:
            text: The text to categorize
            
        Returns:
            A category name
        """
        try:
            categories = [
                "Technology", "Entertainment", "Education", "Lifestyle",
                "Food", "Travel", "Fitness", "Health", "Art", "Music",
                "News", "Comedy", "Other"
            ]
            
            prompt = f"""
            Categorize this Instagram reel caption into ONE of these categories:
            {', '.join(categories)}
            
            Respond with ONLY the category name, nothing else.
            
            Caption: {text}
            """
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                prompt
            )
            
            category = response.text.strip()
            
            # Ensure category is valid
            if category not in categories:
                category = "Other"
            
            logger.info(f"Categorized text as: {category}")
            return category
        
        except Exception as e:
            logger.error(f"Failed to categorize: {str(e)}")
            return "Other"


# ========================
# CHAT PROCESSING
# ========================

class ChatParser:
    """Parses chat exports in JSON or TXT format."""
    
    INSTAGRAM_REEL_PATTERN = r'(?:https?://)?(?:www\.)?instagram\.com/reels/([A-Za-z0-9_\-]+)'
    
    @staticmethod
    def parse_chat_file(file_path: str) -> List[Dict]:
        """
        Parse chat file in JSON or TXT format.
        
        Args:
            file_path: Path to chat file
            
        Returns:
            List of message dictionaries
        """
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, dict):
                    if 'messages' in data:
                        return data['messages']
                    elif 'conversations' in data:
                        return data['conversations']
                    else:
                        return [data]
                elif isinstance(data, list):
                    return data
            
            elif file_path.endswith('.txt'):
                messages = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Parse format: [datetime] sender: message
                        match = re.match(r'\[(.*?)\]\s+(.+?):\s+(.*)', line)
                        if match:
                            messages.append({
                                'date': match.group(1),
                                'sender': match.group(2),
                                'text': match.group(3)
                            })
                
                return messages
            
            else:
                logger.error(f"Unsupported file format: {file_path}")
                return []
        
        except FileNotFoundError:
            logger.error(f"Chat file not found: {file_path}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON file: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error parsing chat file: {str(e)}")
            return []
    
    @staticmethod
    def extract_reels(messages: List[Dict]) -> List[ReelEntry]:
        """
        Extract Instagram Reel entries from messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of ReelEntry objects
        """
        reels = []
        
        for msg in messages:
            # Handle different message structures
            text = msg.get('text') or msg.get('body') or str(msg)
            
            # Find Instagram Reel links
            match = re.search(ChatParser.INSTAGRAM_REEL_PATTERN, text)
            if match:
                reel_id = match.group(1)
                link = f"https://instagram.com/reels/{reel_id}/"
                
                # Extract metadata
                date = msg.get('date', msg.get('timestamp', 'Unknown'))
                sender = msg.get('sender', msg.get('from', 'Unknown'))
                
                # Extract caption (everything after the link)
                caption = re.sub(ChatParser.INSTAGRAM_REEL_PATTERN, '', text).strip()
                if not caption:
                    caption = "No caption provided"
                
                reel = ReelEntry(
                    date=date,
                    sender=sender,
                    link=link,
                    caption=caption
                )
                reels.append(reel)
        
        logger.info(f"Extracted {len(reels)} reel entries from {len(messages)} messages")
        return reels


# ========================
# REEL PROCESSING
# ========================

class ReelProcessor:
    """Processes reels with AI summarization and categorization."""
    
    def __init__(self, summarizer: LLMSummarizer):
        """Initialize with an LLM summarizer."""
        self.summarizer = summarizer
    
    async def process_reels(self, reels: List[ReelEntry]) -> List[ReelEntry]:
        """
        Process reels: summarize and categorize each one.
        
        Args:
            reels: List of ReelEntry objects
            
        Returns:
            Updated list with summaries and categories
        """
        logger.info(f"Processing {len(reels)} reels with AI")
        
        for i, reel in enumerate(reels, 1):
            logger.info(f"Processing reel {i}/{len(reels)}")
            
            try:
                # Summarize caption
                reel.summary = await self.summarizer.summarize(reel.caption)
                
                # Categorize
                reel.category = await self.summarizer.categorize(reel.caption)
            
            except Exception as e:
                logger.error(f"Error processing reel {i}: {str(e)}")
                reel.summary = f"[Error: {str(e)}]"
                reel.category = "Other"
        
        return reels


# ========================
# OUTPUT GENERATION
# ========================

class MarkdownGenerator:
    """Generates markdown output from reel data."""
    
    @staticmethod
    def generate_markdown(reels: List[ReelEntry]) -> str:
        """
        Generate markdown document from reels.
        
        Args:
            reels: List of ReelEntry objects
            
        Returns:
            Formatted markdown string
        """
        # Group by category
        by_category = {}
        for reel in reels:
            cat = reel.category or "Other"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(reel)
        
        # Generate markdown
        md = "# Instagram Reel Archive\n\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        md += "---\n\n"
        
        # Add reels by category
        for category in sorted(by_category.keys()):
            reels_in_cat = by_category[category]
            md += f"## {category}\n\n"
            
            for i, reel in enumerate(reels_in_cat, 1):
                md += f"### {category} #{i}\n\n"
                md += f"**Date:** {reel.date}\n"
                md += f"**Sender:** {reel.sender}\n"
                md += f"**Link:** [{reel.link}]({reel.link})\n\n"
                md += f"**Caption:** {reel.caption}\n\n"
                md += f"**Summary:** {reel.summary}\n\n"
                md += "---\n\n"
        
        return md


# ========================
# GITHUB INTEGRATION
# ========================

class GitHubManager:
    """Manages GitHub repository operations."""
    
    def __init__(self, github_token: str, repo_name: str = "The Belmont Archive"):
        """
        Initialize GitHub manager.
        
        Args:
            github_token: GitHub personal access token
            repo_name: Repository name
        """
        if not GITHUB_AVAILABLE:
            logger.warning("PyGithub not installed. GitHub operations disabled.")
            self.github = None
            return
        
        try:
            self.github = Github(github_token)
            self.user = self.github.get_user()
            self.repo_name = repo_name
            logger.info("GitHub manager initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize GitHub: {str(e)}")
            self.github = None
    
    def push_summaries(self, markdown_content: str, file_name: str = "summaries.md") -> str:
        """
        Push markdown summaries to GitHub repository.
        
        Args:
            markdown_content: Markdown content to push
            file_name: File name in repository
            
        Returns:
            Success or error message
        """
        if not self.github:
            return "GitHub not available"
        
        try:
            # Try to get existing repo, create if doesn't exist
            try:
                repo = self.user.get_repo(self.repo_name)
                logger.info(f"Found existing repository: {self.repo_name}")
            except:
                logger.info(f"Creating new repository: {self.repo_name}")
                repo = self.user.create_repo(
                    name=self.repo_name,
                    description="Archive of Instagram Reels with AI summaries",
                    private=False
                )
            
            # Try to get existing file content
            try:
                existing_file = repo.get_contents(file_name)
                # Append to existing content
                new_content = existing_file.decoded_content.decode() + "\n" + markdown_content
                repo.update_file(
                    path=file_name,
                    message=f"Update summaries - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    content=new_content,
                    sha=existing_file.sha
                )
                logger.info(f"Updated {file_name} in repository")
            
            except:
                # Create new file
                repo.create_file(
                    path=file_name,
                    message=f"Initial commit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    content=markdown_content
                )
                logger.info(f"Created {file_name} in repository")
            
            repo_url = f"https://github.com/{self.user.login}/{self.repo_name}"
            success_msg = f"✓ Successfully pushed summaries to {repo_url}"
            logger.info(success_msg)
            return success_msg
        
        except Exception as e:
            error_msg = f"Failed to push to GitHub: {str(e)}"
            logger.error(error_msg)
            return error_msg


# ========================
# MAIN ORCHESTRATION
# ========================

async def process_instagram_chat(
    chat_file_path: str = "chat_log.json",
    repo_name: str = "The Belmont Archive",
    file_name: str = "summaries.md"
) -> None:
    """
    Main orchestration function.
    
    Processes Instagram chat file end-to-end:
    1. Parse chat file
    2. Extract reel entries
    3. Summarize and categorize with AI
    4. Generate markdown
    5. Push to GitHub
    
    Args:
        chat_file_path: Path to chat export file
        repo_name: GitHub repository name
        file_name: File name for summaries in repo
    """
    
    print("\n" + "="*70)
    print("Instagram Reel Archive Manager")
    print("="*70 + "\n")
    
    # Step 1: Parse chat file
    print("[1/5] Parsing chat file...")
    messages = ChatParser.parse_chat_file(chat_file_path)
    if not messages:
        logger.error("No messages parsed from chat file")
        return
    print(f"✓ Parsed {len(messages)} messages")
    
    # Step 2: Extract reels
    print("\n[2/5] Extracting Reel entries...")
    reels = ChatParser.extract_reels(messages)
    if not reels:
        print("✗ No reel entries found!")
        return
    print(f"Found {len(reels)} Reel entries")
    
    # Step 3: Summarize and categorize
    print("\n[3/5] Summarizing and categorizing reels (using Gemini)...")
    summarizer = GeminiSummarizer()
    processor = ReelProcessor(summarizer)
    reels = await processor.process_reels(reels)
    print("✓ Summarization and categorization complete")
    
    # Step 4: Generate markdown
    print("\n[4/5] Generating markdown content...")
    markdown_content = MarkdownGenerator.generate_markdown(reels)
    print("✓ Markdown generated")
    
    # Step 5: Push to GitHub
    print("\n[5/5] Pushing to GitHub repository...")
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.warning("GITHUB_TOKEN not found. Skipping GitHub push.")
        print("✗ GITHUB_TOKEN not found in .env")
        print("\nMarkdown content preview:")
        print("-" * 70)
        print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)
    else:
        github_mgr = GitHubManager(github_token, repo_name)
        result = github_mgr.push_summaries(markdown_content, file_name)
        print(result)
    
    print("\n" + "="*70)
    print("✓ Process completed successfully!")
    print("="*70 + "\n")


# ========================
# ENTRY POINT
# ========================

if __name__ == "__main__":
    # Run the main process
    asyncio.run(process_instagram_chat())
