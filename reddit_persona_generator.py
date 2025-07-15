import os
import sys
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv
from colorama import init, Fore, Style

from utils.scraper import RedditScraper
from utils.persona_builder import PersonaBuilder
from utils.file_writer import FileWriter


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('reddit_persona_generator.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.
    
    Returns:
        bool: True if all required variables are present, False otherwise
    """
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USER_AGENT',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"{Fore.RED}Error: Missing required environment variables:{Style.RESET_ALL}")
        for var in missing_vars:
            print(f"  - {var}")
        print(f"\n{Fore.YELLOW}Please check your .env file and ensure all variables are set.{Style.RESET_ALL}")
        return False
    
    return True


def extract_username_from_url(url: str) -> Optional[str]:
    """
    Extract Reddit username from URL.
    
    Args:
        url: Reddit profile URL
        
    Returns:
        Username if valid URL, None otherwise
    """
    import re
    
    # Support various Reddit URL formats
    patterns = [
        r'reddit\.com/user/([^/]+)',
        r'reddit\.com/u/([^/]+)',
        r'www\.reddit\.com/user/([^/]+)',
        r'www\.reddit\.com/u/([^/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no URL pattern matches, assume it's just a username
    if '/' not in url and url.replace('_', '').replace('-', '').isalnum():
        return url
    
    return None


def main():
    """Main application entry point."""
    # Initialize colorama for cross-platform colored output
    init(autoreset=True)
    
    # Load environment variables
    load_dotenv()
    
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description='Generate detailed user personas from Reddit profiles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reddit_persona_generator.py https://www.reddit.com/user/kojied/
  python reddit_persona_generator.py kojied
  python reddit_persona_generator.py --username kojied --output custom_folder/
  python reddit_persona_generator.py --username kojied --log-level DEBUG
        """
    )
    
    parser.add_argument(
        'profile',
        nargs='?',
        help='Reddit profile URL or username'
    )
    
    parser.add_argument(
        '--username', '-u',
        help='Reddit username (alternative to profile URL)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='sample_outputs',
        help='Output directory for persona files (default: sample_outputs)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--max-posts',
        type=int,
        default=100,
        help='Maximum number of posts to analyze (default: 100)'
    )
    
    parser.add_argument(
        '--max-comments',
        type=int,
        default=50,
        help='Maximum number of comments to analyze (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Determine username
    username = None

    if args.username:
        username = args.username
    elif args.profile:
        username = extract_username_from_url(args.profile)
    
    if not username:
        print(f"{Fore.RED}Error: Please provide a valid Reddit username or profile URL{Style.RESET_ALL}")
        parser.print_help()
        sys.exit(1)
    
    print(f"{Fore.CYAN}🚀 Reddit Persona Generator{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Target User: {username}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Output Directory: {args.output}{Style.RESET_ALL}")
    print("-" * 50)
    
    try:
        # Initialize components
        scraper = RedditScraper()
        persona_builder = PersonaBuilder()
        file_writer = FileWriter(args.output)
        
        # Step 1: Scrape Reddit data
        print(f"{Fore.BLUE}📊 Scraping Reddit data for user: {username}{Style.RESET_ALL}")
        user_data = scraper.scrape_user_data(
            username, 
            max_posts=args.max_posts, 
            max_comments=args.max_comments
        )
        
        if not user_data or (not user_data.get('posts') and not user_data.get('comments')):
            print(f"{Fore.RED}❌ No data found for user: {username}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}This could mean:{Style.RESET_ALL}")
            print("  • User doesn't exist")
            print("  • User has no posts/comments")
            print("  • User account is private/suspended")
            sys.exit(1)
        
        posts_count = len(user_data.get('posts', []))
        comments_count = len(user_data.get('comments', []))
        print(f"{Fore.GREEN}✅ Successfully scraped {posts_count} posts and {comments_count} comments{Style.RESET_ALL}")
        
        # Step 2: Build persona
        print(f"{Fore.BLUE}🧠 Analyzing data and building persona...{Style.RESET_ALL}")
        persona = persona_builder.build_persona(user_data, username)
        
        if not persona:
            print(f"{Fore.RED}❌ Failed to generate persona for user: {username}{Style.RESET_ALL}")
            sys.exit(1)
        
        print(f"{Fore.GREEN}✅ Successfully generated persona{Style.RESET_ALL}")
        
        # Step 3: Write output file
        print(f"{Fore.BLUE}📄 Writing persona to file...{Style.RESET_ALL}")
        output_file = file_writer.write_persona(persona, username)
        
        print(f"{Fore.GREEN}✅ Persona generation complete!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 Output file: {output_file}{Style.RESET_ALL}")
        
        # Display summary
        print("\n" + "="*50)
        print(f"{Fore.CYAN}📋 Generation Summary{Style.RESET_ALL}")
        print(f"User: {username}")
        print(f"Posts analyzed: {posts_count}")
        print(f"Comments analyzed: {comments_count}")
        print(f"Output file: {output_file}")
        print("="*50)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"{Fore.RED}❌ An error occurred: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Check the log file for detailed error information{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()