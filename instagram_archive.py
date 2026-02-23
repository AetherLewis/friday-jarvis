"""
Instagram Reel Archive Manager

This script reads Instagram chat exports, extracts Reel links and captions,
summarizes them using Gemini AI, and automatically commits the summaries to
a GitHub repository.

Features:
- Reads JSON and TXT chat exports
- Extracts Instagram Reel links and captions
- Summarizes captions using AI (swappable LLM)
- Organizes summaries by category
- Auto-commits to GitHub repository
- Comprehensive error handling and logging
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import asyncio
import warnings

# Suppress FutureWarning about google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from github import Github, GithubException

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ReelEntry:
    """Represents a single Instagram Reel entry from the chat."""
    date: str
    sender: str
    link: str
    caption: str
    summary: Optional[str] = None
    category: Optional[str] = None


# ============================================================================
# ABSTRACT LLM CLASS (For modularity)
# ============================================================================

class LLMSummarizer(ABC):
    """Abstract base class for LLM summarizers. Can be swapped with other LLMs."""
    
    @abstractmethod
    async def summarize(self, text: str) -> str:
        """
        Summarize the given text into 1-3 sentences.
        
        Args:
            text: The text to summarize
            
        Returns:
            Summary string (1-3 sentences)
        """
        pass
    
    @abstractmethod
    async def categorize(self, text: str) -> str:
        """
        Determine the category of the given text.
        
        Args:
            text: The text to categorize
            
        Returns:
            Category name (e.g., "Technology", "Entertainment", etc.)
        """
        pass


# ============================================================================
# GEMINI IMPLEMENTATION
# ============================================================================

class GeminiSummarizer(LLMSummarizer):
    """Gemini-based implementation of the LLM summarizer."""
    
    def __init__(self):
        """Initialize Gemini model."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini summarizer initialized")
    
    async def summarize(self, text: str) -> str:
        """Summarize text using Gemini."""
        try:
            prompt = f"Summarize the following Instagram Reel caption in 1-3 sentences:\n\n{text}"
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.model.generate_content,
                prompt
            )
            summary = response.text.strip()
            logger.info(f"Successfully summarized text")
            return summary
        except Exception as e:
            logger.error(f"Error summarizing: {e}")
            return f"[Failed to summarize: {str(e)}]"
    
    async def categorize(self, text: str) -> str:
        """Categorize text using Gemini."""
        try:
            prompt = f"""Categorize the following Instagram Reel caption into ONE of these categories:
Technology, Entertainment, Education, Lifestyle, Food, Travel, Sports, Art, Music, News, Comedy, Other

Caption: {text}

Respond with only the category name."""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.model.generate_content,
                prompt
            )
            category = response.text.strip()
            logger.info(f"Categorized text as: {category}")
            return category
        except Exception as e:
            logger.error(f"Error categorizing: {e}")
            return "Other"


# ============================================================================
# CHAT FILE PARSER
# ============================================================================

class ChatParser:
    """Parses Instagram chat exports from JSON or TXT formats."""
    
    # Regex pattern for Instagram Reel URLs
    REEL_PATTERN = r'(?:https?://)?(?:www\.)?instagram\.com/reels?/([a-zA-Z0-9_-]+)'
    
    @staticmethod
    def parse_json_chat(file_path: str) -> List[Dict]:
        """
        Parse Instagram chat from JSON export.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of message dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(data, dict) and 'messages' in data:
                messages = data['messages']
            elif isinstance(data, list):
                messages = data
            else:
                logger.warning("Unexpected JSON structure")
                messages = []
            
            logger.info(f"Parsed {len(messages)} messages from {file_path}")
            return messages
        
        except Exception as e:
            logger.error(f"Error parsing JSON file {file_path}: {e}")
            return []
    
    @staticmethod
    def parse_txt_chat(file_path: str) -> List[Dict]:
        """
        Parse Instagram chat from TXT export.
        Expected format: [Date] Sender: Message
        
        Args:
            file_path: Path to the TXT file
            
        Returns:
            List of message dictionaries
        """
        messages = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse format: [Date] Sender: Message
                    match = re.match(r'\[(.+?)\]\s+(.+?):\s+(.+)', line)
                    if match:
                        messages.append({
                            'date': match.group(1),
                            'sender': match.group(2),
                            'text': match.group(3)
                        })
            
            logger.info(f"Parsed {len(messages)} messages from {file_path}")
            return messages
        
        except Exception as e:
            logger.error(f"Error parsing TXT file {file_path}: {e}")
            return []
    
    @staticmethod
    def parse_chat_file(file_path: str) -> List[Dict]:
        """
        Auto-detect and parse chat file (JSON or TXT).
        
        Args:
            file_path: Path to the chat file
            
        Returns:
            List of message dictionaries
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        
        if file_path.endswith('.json'):
            return ChatParser.parse_json_chat(file_path)
        elif file_path.endswith('.txt'):
            return ChatParser.parse_txt_chat(file_path)
        else:
            logger.warning(f"Unknown file format: {file_path}")
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
            # Support different message formats
            text = msg.get('text') or msg.get('message') or msg.get('content', '')
            
            # Find all Reel links in the message
            links = re.findall(ChatParser.REEL_PATTERN, text)
            
            if links:
                reel_entry = ReelEntry(
                    date=msg.get('date') or msg.get('timestamp') or datetime.now().isoformat(),
                    sender=msg.get('sender') or msg.get('from') or "Unknown",
                    link=f"https://instagram.com/reels/{links[0]}",
                    caption=text
                )
                reels.append(reel_entry)
                logger.info(f"Extracted Reel from {reel_entry.sender}: {reel_entry.link}")
        
        logger.info(f"Found {len(reels)} Reel entries in messages")
        return reels


# ============================================================================
# REEL PROCESSOR (Summarization & Categorization)
# ============================================================================

class ReelProcessor:
    """Processes Reels by summarizing and categorizing them."""
    
    def __init__(self, summarizer: LLMSummarizer):
        """
        Initialize the processor with an LLM summarizer.
        
        Args:
            summarizer: LLMSummarizer instance (Gemini, OpenAI, etc.)
        """
        self.summarizer = summarizer
        logger.info("ReelProcessor initialized")
    
    async def process_reels(self, reels: List[ReelEntry]) -> List[ReelEntry]:
        """
        Process reels by summarizing and categorizing them.
        
        Args:
            reels: List of ReelEntry objects
            
        Returns:
            List of processed ReelEntry objects
        """
        processed_reels = []
        
        for i, reel in enumerate(reels, 1):
            logger.info(f"Processing reel {i}/{len(reels)}...")
            
            try:
                # Summarize caption
                reel.summary = await self.summarizer.summarize(reel.caption)
                
                # Categorize reel
                reel.category = await self.summarizer.categorize(reel.caption)
                
                processed_reels.append(reel)
                logger.info(f"Successfully processed reel: {reel.link}")
            
            except Exception as e:
                logger.error(f"Error processing reel {reel.link}: {e}")
                reel.summary = f"[Error: {str(e)}]"
                reel.category = "Error"
                processed_reels.append(reel)
        
        logger.info(f"Processed {len(processed_reels)} reels")
        return processed_reels


# ============================================================================
# MARKDOWN GENERATOR
# ============================================================================

class MarkdownGenerator:
    """Generates markdown summaries of reels, organized by category."""
    
    @staticmethod
    def generate_markdown(reels: List[ReelEntry]) -> str:
        """
        Generate markdown content from processed reels.
        
        Args:
            reels: List of processed ReelEntry objects
            
        Returns:
            Markdown-formatted string
        """
        # Group reels by category
        categories = {}
        for reel in reels:
            category = reel.category or "Uncategorized"
            if category not in categories:
                categories[category] = []
            categories[category].append(reel)
        
        # Generate markdown
        md_content = f"# Instagram Reel Archive\n\n"
        md_content += f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        md_content += f"Total Reels: {len(reels)}\n\n"
        md_content += "---\n\n"
        
        # Add sections for each category
        for category in sorted(categories.keys()):
            reels_in_category = categories[category]
            md_content += f"## {category}\n\n"
            
            for reel in reels_in_category:
                md_content += f"### {reel.sender}\n\n"
                md_content += f"**Date:** {reel.date}\n\n"
                md_content += f"**Link:** [{reel.link}]({reel.link})\n\n"
                md_content += f"**Original Caption:**\n```\n{reel.caption}\n```\n\n"
                md_content += f"**Summary:** {reel.summary}\n\n"
                md_content += "---\n\n"
        
        logger.info("Generated markdown content")
        return md_content


# ============================================================================
# GITHUB MANAGER
# ============================================================================

class GitHubManager:
    """Manages GitHub repository operations (commit, push, etc.)."""
    
    def __init__(self, github_token: str, repo_name: str = "The Belmont Archive"):
        """
        Initialize GitHub manager.
        
        Args:
            github_token: GitHub personal access token
            repo_name: Repository name
        """
        try:
            self.github = Github(github_token)
            self.user = self.github.get_user()
            self.repo_name = repo_name
            
            # Try to get existing repo or create new one
            try:
                self.repo = self.user.get_repo(repo_name)
                logger.info(f"Connected to existing repository: {repo_name}")
            except GithubException:
                logger.info(f"Repository {repo_name} not found, creating new one...")
                self.repo = self.user.create_repo(
                    name=repo_name,
                    description="Archive of Instagram Reel summaries",
                    private=False,
                    auto_init=True
                )
                logger.info(f"Created new repository: {repo_name}")
        
        except Exception as e:
            logger.error(f"Error initializing GitHub: {e}")
            raise
    
    def push_summaries(self, markdown_content: str, file_name: str = "summaries.md") -> bool:
        """
        Push summary markdown to GitHub repository.
        
        Args:
            markdown_content: Markdown content to push
            file_name: Name of the file in the repository
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to get existing file
            try:
                file_content = self.repo.get_contents(file_name)
                # Append to existing file
                new_content = file_content.decoded_content.decode() + "\n\n" + markdown_content
                commit_message = f"Update {file_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.repo.update_file(
                    file_content.path,
                    commit_message,
                    new_content,
                    file_content.sha
                )
                logger.info(f"Updated {file_name} in repository")
            
            except GithubException:
                # File doesn't exist, create new one
                commit_message = f"Create {file_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.repo.create_file(
                    file_name,
                    commit_message,
                    markdown_content
                )
                logger.info(f"Created new file {file_name} in repository")
            
            return True
        
        except Exception as e:
            logger.error(f"Error pushing to GitHub: {e}")
            return False
    
    def get_repo_url(self) -> str:
        """Get the repository URL."""
        return self.repo.html_url


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

async def process_instagram_chat(
    chat_file_path: str,
    github_token: str,
    repo_name: str = "The Belmont Archive",
    file_name: str = "summaries.md"
) -> bool:
    """
    Main orchestrator: reads chat, extracts reels, summarizes, and pushes to GitHub.
    
    Args:
        chat_file_path: Path to the Instagram chat export file
        github_token: GitHub personal access token
        repo_name: GitHub repository name
        file_name: Output file name in repository
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("=" * 70)
        logger.info("Starting Instagram Reel Archive Process")
        logger.info("=" * 70)
        
        # Step 1: Parse chat file
        logger.info("\n[1/5] Parsing chat file...")
        messages = ChatParser.parse_chat_file(chat_file_path)
        if not messages:
            logger.error("No messages found in chat file")
            return False
        
        # Step 2: Extract reels
        logger.info("\n[2/5] Extracting Reel entries...")
        reels = ChatParser.extract_reels(messages)
        if not reels:
            logger.warning("No Reel entries found in chat")
            return False
        
        logger.info(f"Found {len(reels)} Reel entries")
        
        # Step 3: Summarize and categorize
        logger.info("\n[3/5] Summarizing and categorizing reels (using Gemini)...")
        summarizer = GeminiSummarizer()
        processor = ReelProcessor(summarizer)
        processed_reels = await processor.process_reels(reels)
        
        # Step 4: Generate markdown
        logger.info("\n[4/5] Generating markdown content...")
        markdown_content = MarkdownGenerator.generate_markdown(processed_reels)
        
        # Step 5: Push to GitHub
        logger.info("\n[5/5] Pushing to GitHub repository...")
        github_manager = GitHubManager(github_token, repo_name)
        success = github_manager.push_summaries(markdown_content, file_name)
        
        if success:
            logger.info("=" * 70)
            logger.info("✓ Process completed successfully!")
            logger.info(f"Repository: {github_manager.get_repo_url()}")
            logger.info("=" * 70)
            return True
        else:
            logger.error("Failed to push to GitHub")
            return False
    
    except Exception as e:
        logger.error(f"Fatal error in process: {e}")
        return False


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """
    Example main function demonstrating the workflow.
    Replace values with your actual paths and tokens.
    """
    print("\n" + "=" * 70)
    print("Instagram Reel Archive Manager")
    print("=" * 70 + "\n")
    
    # Configuration
    chat_file_path = "chat_log.json"  # Change to your chat file
    github_token = os.getenv("GITHUB_TOKEN")  # Set as environment variable
    repo_name = "The Belmont Archive"
    file_name = "summaries.md"
    
    # Validation
    if not os.path.exists(chat_file_path):
        print(f"❌ Chat file not found: {chat_file_path}")
        print("Please export your Instagram chat and save it as 'chat_log.json'")
        return
    
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment variables")
        print("Set it with: export GITHUB_TOKEN='your_token'")
        return
    
    # Run the process
    success = await process_instagram_chat(
        chat_file_path=chat_file_path,
        github_token=github_token,
        repo_name=repo_name,
        file_name=file_name
    )
    
    if success:
        print("\n✓ All done! Check your GitHub repository.")
    else:
        print("\n❌ Process failed. Check logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
