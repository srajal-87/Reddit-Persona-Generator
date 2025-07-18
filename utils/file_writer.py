"""
File Writer Module

Handles output formatting and file creation for generated personas.
Creates professional, readable persona files with proper citations.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json


class FileWriter:
    """
    A file writer that formats and saves persona data to structured text files.
    
    Attributes:
        output_dir: Directory for output files
        logger: Logger instance for debugging and error tracking
    """
    
    def __init__(self, output_dir: str = "sample_outputs"):
        """
        Initialize the file writer with output directory.
        
        Args:
            output_dir: Directory to save persona files
        """
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        self._ensure_output_directory()
    
    def _ensure_output_directory(self) -> None:
        """
        Ensure output directory exists, create if it doesn't.
        """
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.info(f"Output directory ready: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            raise
    
    def _format_header(self, username: str, generation_time: str) -> str:
        """
        Format the header section of the persona file.
        
        Args:
            username: Reddit username
            generation_time: Timestamp of persona generation
            
        Returns:
            Formatted header string
        """
        return f"""
{'=' * 80}
                    REDDIT USER PERSONA ANALYSIS
{'=' * 80}

Username: u/{username}
Generated: {generation_time}
Generated by: Reddit Persona Generator

{'=' * 80}
"""
    
    def _format_user_statistics(self, statistics: Dict[str, Any]) -> str:
        """
        Format user statistics section.
        
        Args:
            statistics: Dictionary containing user statistics
            
        Returns:
            Formatted statistics string
        """
        lines = ["\n📊 USER STATISTICS"]
        lines.append("=" * 50)
        
        # User info
        user_info = statistics.get('user_info', {})
        if user_info:
            lines.append(f"Account Age: {user_info.get('account_age_days', 0):.0f} days")
            lines.append(f"Comment Karma: {user_info.get('comment_karma', 0):,}")
            lines.append(f"Link Karma: {user_info.get('link_karma', 0):,}")
            lines.append(f"Has Verified Email: {user_info.get('has_verified_email', False)}")
            lines.append(f"Is Gold Member: {user_info.get('is_gold', False)}")
            lines.append(f"Is Moderator: {user_info.get('is_mod', False)}")
        
        # Scraping stats
        scraping_stats = statistics.get('scraping_stats', {})
        if scraping_stats:
            lines.append(f"\nData Analyzed:")
            lines.append(f"  • Posts: {scraping_stats.get('posts_scraped', 0)}")
            lines.append(f"  • Comments: {scraping_stats.get('comments_scraped', 0)}")
            lines.append(f"  • Scraped: {scraping_stats.get('scraping_timestamp', 'Unknown')}")
        
        # Posting patterns
        posting_patterns = statistics.get('posting_patterns', {})
        if posting_patterns:
            lines.append(f"\nActivity Patterns:")
            lines.append(f"  • Total Activity: {posting_patterns.get('total_activity', 0)}")
            lines.append(f"  • Posts: {posting_patterns.get('total_posts', 0)}")
            lines.append(f"  • Comments: {posting_patterns.get('total_comments', 0)}")
            
            if posting_patterns.get('most_active_hour') is not None:
                lines.append(f"  • Most Active Hour: {posting_patterns['most_active_hour']}:00")
            
            if posting_patterns.get('most_active_day') is not None:
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_name = days[posting_patterns['most_active_day']] if posting_patterns['most_active_day'] < 7 else 'Unknown'
                lines.append(f"  • Most Active Day: {day_name}")
            
            if posting_patterns.get('activity_span_days'):
                lines.append(f"  • Activity Span: {posting_patterns['activity_span_days']:.0f} days")
            
            if posting_patterns.get('average_daily_activity'):
                lines.append(f"  • Average Daily Activity: {posting_patterns['average_daily_activity']:.1f} posts/comments")
        
        return '\n'.join(lines)
    
    def _format_subreddit_activity(self, subreddit_activity: Dict[str, int]) -> str:
        """
        Format subreddit activity section.
        
        Args:
            subreddit_activity: Dictionary mapping subreddit names to activity counts
            
        Returns:
            Formatted subreddit activity string
        """
        lines = ["\n🏘️ SUBREDDIT ACTIVITY"]
        lines.append("=" * 50)
        
        if not subreddit_activity:
            lines.append("No subreddit activity data available")
            return '\n'.join(lines)
        
        # Show top 15 subreddits
        top_subreddits = list(subreddit_activity.items())[:15]
        
        for i, (subreddit, count) in enumerate(top_subreddits, 1):
            lines.append(f"{i:2d}. r/{subreddit:<25} {count:4d} posts/comments")
        
        if len(subreddit_activity) > 15:
            lines.append(f"\n... and {len(subreddit_activity) - 15} more subreddits")
        
        return '\n'.join(lines)
    
    def _format_analysis_section(self, title: str, icon: str, analysis: str) -> str:
        """
        Format an analysis section with title and content.
        
        Args:
            title: Section title
            icon: Emoji icon for the section
            analysis: Analysis content
            
        Returns:
            Formatted analysis section string
        """
        lines = [f"\n{icon} {title}"]
        lines.append("=" * 50)
        
        if analysis and analysis.strip() != "Analysis failed":
            # Clean up the analysis text
            analysis_lines = analysis.strip().split('\n')
            formatted_lines = []
            
            for line in analysis_lines:
                line = line.strip()
                if line:
                    # Bold section headers (lines ending with :)
                    if line.endswith(':') and len(line) < 50:
                        formatted_lines.append(f"\n{line}")
                    else:
                        formatted_lines.append(line)
            
            lines.extend(formatted_lines)
        else:
            lines.append("Analysis could not be generated for this section.")
        
        return '\n'.join(lines)
    
    def _format_citations(self, citations: Dict[str, Any]) -> str:
        """
        Format citations section.
        
        Args:
            citations: Dictionary containing citation mappings
            
        Returns:
            Formatted citations string
        """
        lines = ["\n📚 CITATIONS & REFERENCES"]
        lines.append("=" * 50)
        
        if not citations:
            lines.append("No citations available")
            return '\n'.join(lines)
        
        # Group citations by type
        posts = {}
        comments = {}
        
        for citation_id, citation_data in citations.items():
            if citation_data.get('type') == 'post':
                posts[citation_id] = citation_data
            elif citation_data.get('type') == 'comment':
                comments[citation_id] = citation_data
        
        # Format posts
        if posts:
            lines.append("\nPOSTS:")
            for citation_id, data in sorted(posts.items()):
                lines.append(f"  {citation_id}: r/{data.get('subreddit', 'unknown')}")
                lines.append(f"    Title: {data.get('title', 'No title')}")
                lines.append(f"    Score: {data.get('score', 0)}")
                if data.get('permalink'):
                    lines.append(f"    Link: https://reddit.com{data['permalink']}")
                lines.append("")
        
        # Format comments
        if comments:
            lines.append("\nCOMMENTS:")
            for citation_id, data in sorted(comments.items()):
                lines.append(f"  {citation_id}: r/{data.get('subreddit', 'unknown')}")
                lines.append(f"    In: {data.get('submission_title', 'Unknown post')}")
                lines.append(f"    Score: {data.get('score', 0)}")
                if data.get('permalink'):
                    lines.append(f"    Link: https://reddit.com{data['permalink']}")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _format_footer(self) -> str:
        """
        Format the footer section.
        
        Returns:
            Formatted footer string
        """
        return f"""
{'=' * 80}
                              DISCLAIMER
{'=' * 80}

This persona analysis is generated based on publicly available Reddit data
and should be used for informational purposes only. The analysis represents
patterns and trends in the user's public posting behavior and should not be
considered a definitive psychological profile.

All data is sourced from Reddit's public API and follows Reddit's terms of
service. No private or sensitive information has been accessed.

Generated by Reddit Persona Generator
{'=' * 80}
"""
    
    def write_persona(self, persona: Dict[str, Any], username: str) -> str:
        """
        Write persona data to a formatted text file.
        
        Args:
            persona: Dictionary containing complete persona data
            username: Reddit username
            
        Returns:
            Path to the created file
            
        Raises:
            IOError: If file writing fails
        """
        if not persona:
            raise ValueError("Persona data cannot be empty")
        
        # Generate filename
        safe_username = "".join(c for c in username if c.isalnum() or c in "._-")
        filename = f"{safe_username}_persona.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                generation_time = persona.get('generation_timestamp', datetime.now().isoformat())
                f.write(self._format_header(username, generation_time))
                
                # Write user statistics
                statistics = persona.get('statistics', {})
                f.write(self._format_user_statistics(statistics))
                
                # Write subreddit activity
                subreddit_activity = statistics.get('subreddit_activity', {})
                f.write(self._format_subreddit_activity(subreddit_activity))
                
                # Write analysis sections
                analysis = persona.get('analysis', {})
                
                f.write(self._format_analysis_section(
                    "DEMOGRAPHICS ANALYSIS", "👤", 
                    analysis.get('demographics', '')
                ))
                
                f.write(self._format_analysis_section(
                    "INTERESTS ANALYSIS", "🎯", 
                    analysis.get('interests', '')
                ))
                
                f.write(self._format_analysis_section(
                    "PERSONALITY ANALYSIS", "🧠", 
                    analysis.get('personality', '')
                ))
                
                f.write(self._format_analysis_section(
                    "BEHAVIOR ANALYSIS", "📈", 
                    analysis.get('behavior', '')
                ))
                
                # Write citations
                citations = persona.get('citations', {})
                f.write(self._format_citations(citations))
                
                # Write footer
                f.write(self._format_footer())
            
            self.logger.info(f"Successfully wrote persona file: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to write persona file: {str(e)}")
            raise IOError(f"Failed to write persona file: {str(e)}") from e
    
    def write_debug_data(self, persona: Dict[str, Any], username: str) -> Optional[str]:
        """
        Write debug data to JSON file for troubleshooting.
        
        Args:
            persona: Dictionary containing complete persona data
            username: Reddit username
            
        Returns:
            Path to the debug file or None if failed
        """
        try:
            safe_username = "".join(c for c in username if c.isalnum() or c in "._-")
            filename = f"{safe_username}_debug.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(persona, f, indent=2, default=str)
            
            self.logger.info(f"Debug data written to: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to write debug data: {str(e)}")
            return None
    
    def validate_persona_structure(self, persona: Dict[str, Any]) -> bool:
        """
        Validates the structure of the persona dictionary to ensure all required fields exist.
        
        Args:
            persona: The persona dictionary to validate
            
        Returns:
            True if the structure is valid, False otherwise
        """
        required_keys = ['statistics', 'analysis', 'citations']
        
        for key in required_keys:
            if key not in persona:
                self.logger.warning(f"Missing key in persona data: '{key}'")
                return False

        # Further optional nested validations (can be expanded)
        if not isinstance(persona.get('analysis'), dict):
            self.logger.warning("Persona 'analysis' section is not a dictionary.")
            return False

        return True
