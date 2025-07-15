import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import openai
from collections import Counter
import google.generativeai as genai

class PersonaBuilder:
    """
    A persona builder that analyzes Reddit data using Google's Gemini models
    to generate comprehensive user personas with proper citations.
    
    Attributes:
        client: Gemini client instance
        logger: Logger instance for debugging and error tracking
        model: Gemini model to use for analysis
        max_retries: Maximum number of API retry attempts
    """
    
    def __init__(self, model: str = "gemini-1.5-flash", max_retries: int = 1):
        """
        Initialize the persona builder with Gemini API credentials.
        
        Args:
            model: Gemini model to use (default: gemini-pro)
            max_retries: Maximum retry attempts for API calls
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.max_retries = max_retries
        self.client = self._initialize_gemini()
    
    def _initialize_gemini(self) -> genai.GenerativeModel:
        """
        Initialize Gemini client with API key from environment.
        
        Returns:
            genai.GenerativeModel: Configured Gemini model
            
        Raises:
            ValueError: If API key is not found in environment
        """
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not found in environment variables")
        
        try:
            genai.configure(api_key=api_key)
            client = genai.GenerativeModel(self.model)
            self.logger.info("Successfully initialized Gemini client")
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise
    
    def _make_api_call(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """
        Make API call to Gemini with simple retry logic.
        
        Args:
            messages: List of message dictionaries (OpenAI format)
            temperature: Sampling temperature for response generation
            
        Returns:
            Response content or None if all retries failed
        """
        # Gemini prompt format
        prompt_parts = []
        for message in messages:
            if message["role"] == "system":
                prompt_parts.append(f"System: {message['content']}")
            elif message["role"] == "user":
                prompt_parts.append(f"User: {message['content']}")
            elif message["role"] == "assistant":
                prompt_parts.append(f"Assistant: {message['content']}")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=2000
                    )
                )
                return response.text
                
            except Exception as e:
                self.logger.error(f"API call failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                
        return None
    
    def _prepare_content_for_analysis(self, user_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare Reddit data for LLM analysis with citation tracking.
        
        Args:
            user_data: Dictionary containing user posts and comments
            
        Returns:
            Tuple of (prepared_content, citation_map)
        """
        posts = user_data.get('posts', [])
        comments = user_data.get('comments', [])
        
        # Create citation map
        citation_map = {}
        content_parts = []
        
        # Process posts
        if posts:
            content_parts.append("=== REDDIT POSTS ===")
            for i, post in enumerate(posts[:50]):  # Limit to first 50 posts
                post_id = f"POST_{i+1}"
                citation_map[post_id] = {
                    'type': 'post',
                    'id': post.get('id'),
                    'title': post.get('title', ''),
                    'subreddit': post.get('subreddit', ''),
                    'score': post.get('score', 0),
                    'timestamp': post.get('created_utc', 0),
                    'permalink': post.get('permalink', '')
                }
                
                content_parts.append(f"\n[{post_id}] r/{post.get('subreddit', 'unknown')}")
                content_parts.append(f"Title: {post.get('title', 'No title')}")
                if post.get('selftext'):
                    content_parts.append(f"Content: {post.get('selftext')[:500]}...")
                content_parts.append(f"Score: {post.get('score', 0)}")
        
        # Process comments
        if comments:
            content_parts.append("\n\n=== REDDIT COMMENTS ===")
            for i, comment in enumerate(comments[:100]):  # Limit to first 100 comments
                comment_id = f"COMMENT_{i+1}"
                citation_map[comment_id] = {
                    'type': 'comment',
                    'id': comment.get('id'),
                    'subreddit': comment.get('subreddit', ''),
                    'score': comment.get('score', 0),
                    'timestamp': comment.get('created_utc', 0),
                    'submission_title': comment.get('submission_title', ''),
                    'permalink': comment.get('permalink', '')
                }
                
                content_parts.append(f"\n[{comment_id}] r/{comment.get('subreddit', 'unknown')}")
                content_parts.append(f"In response to: {comment.get('submission_title', 'Unknown post')}")
                content_parts.append(f"Comment: {comment.get('body', '')[:300]}...")
                content_parts.append(f"Score: {comment.get('score', 0)}")
        
        return '\n'.join(content_parts), citation_map
    
    def _generate_demographics_analysis(self, content: str) -> Optional[str]:
        """
        Generate demographics analysis using LLM.
        
        Args:
            content: Prepared Reddit content for analysis
            
        Returns:
            Demographics analysis string or None if failed
        """
        messages = [
            {
                "role": "system",
                "content": """You are an expert demographic analyst. Analyze Reddit user data to infer demographics.
                
                Provide analysis in this format:
                AGE: [Estimated age range with reasoning]
                LOCATION: [Likely geographic location with reasoning]
                OCCUPATION: [Likely profession/field with reasoning]
                EDUCATION: [Likely education level with reasoning]
                
                Base your analysis on:
                - Language patterns and slang usage
                - References to life events, technology, culture
                - Subreddit participation patterns
                - Time zone activity patterns
                - Professional or academic references
                
                Always include specific post/comment references in brackets like [POST_1] or [COMMENT_5] to support your conclusions.
                Be conservative in your estimates and clearly state when evidence is limited."""
            },
            {
                "role": "user",
                "content": f"Analyze this Reddit user's demographics based on their posts and comments:\n\n{content}"
            }
        ]
        
        return self._make_api_call(messages, temperature=0.3)
    
    def _generate_interests_analysis(self, content: str, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate interests analysis using LLM and activity data.
        
        Args:
            content: Prepared Reddit content for analysis
            user_data: Original user data for activity analysis
            
        Returns:
            Interests analysis string or None if failed
        """
        # Calculate subreddit activity
        subreddit_activity = self._calculate_subreddit_activity(user_data)
        top_subreddits = list(subreddit_activity.items())[:10]
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert interest analyst. Analyze Reddit user data to identify interests and hobbies.
                
                Provide analysis in this format:
                PRIMARY INTERESTS: [Top 3-5 interests with evidence]
                SECONDARY INTERESTS: [Additional interests with evidence]
                HOBBY PATTERNS: [Specific hobbies and activities]
                ENTERTAINMENT PREFERENCES: [Media, games, etc.]
                
                Consider:
                - Subreddit participation frequency
                - Content engagement patterns
                - Specific topics discussed
                - Recurring themes and subjects
                
                Always include specific post/comment references in brackets like [POST_1] or [COMMENT_5] to support your conclusions.
                Rank interests by engagement level and consistency."""
            },
            {
                "role": "user",
                "content": f"""Analyze this Reddit user's interests based on their activity:

Top Subreddits by Activity:
{chr(10).join([f"r/{sub}: {count} posts/comments" for sub, count in top_subreddits])}

Posts and Comments:
{content}"""
            }
        ]
        
        return self._make_api_call(messages, temperature=0.4)
    
    def _generate_personality_analysis(self, content: str) -> Optional[str]:
        """
        Generate personality analysis using LLM.
        
        Args:
            content: Prepared Reddit content for analysis
            
        Returns:
            Personality analysis string or None if failed
        """
        messages = [
            {
                "role": "system",
                "content": """You are an expert personality analyst. Analyze Reddit user data to identify personality traits.
                
                Provide analysis in this format:
                COMMUNICATION STYLE: [How they communicate with evidence]
                EMOTIONAL PATTERNS: [Emotional tendencies with evidence]
                SOCIAL BEHAVIOR: [How they interact with others]
                DECISION MAKING: [How they approach decisions]
                VALUES AND BELIEFS: [What seems important to them]
                
                Focus on:
                - Language tone and style
                - Reaction patterns to different topics
                - Conflict resolution approaches
                - Helping/sharing behavior
                - Humor and creativity patterns
                
                Always include specific post/comment references in brackets like [POST_1] or [COMMENT_5] to support your conclusions.
                Be objective and avoid making judgmental statements."""
            },
            {
                "role": "user",
                "content": f"Analyze this Reddit user's personality based on their posts and comments:\n\n{content}"
            }
        ]
        
        return self._make_api_call(messages, temperature=0.5)
    
    def _generate_behavior_analysis(self, content: str, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate behavior analysis using LLM and activity patterns.
        
        Args:
            content: Prepared Reddit content for analysis
            user_data: Original user data for pattern analysis
            
        Returns:
            Behavior analysis string or None if failed
        """
        # Calculate posting patterns
        posting_patterns = self._calculate_posting_patterns(user_data)
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert behavioral analyst. Analyze Reddit user data to identify behavioral patterns.
                
                Provide analysis in this format:
                POSTING FREQUENCY: [How often they post with patterns]
                ENGAGEMENT STYLE: [How they engage with content]
                COMMUNITY PARTICIPATION: [How they participate in discussions]
                CONTENT PREFERENCES: [What type of content they prefer]
                ONLINE HABITS: [Observable online behavior patterns]
                
                Consider:
                - Posting timing and frequency
                - Response patterns to others
                - Content creation vs consumption
                - Subreddit loyalty and exploration
                - Karma-seeking behavior
                
                Always include specific post/comment references in brackets like [POST_1] or [COMMENT_5] to support your conclusions.
                Focus on observable behaviors rather than assumptions."""
            },
            {
                "role": "user",
                "content": f"""Analyze this Reddit user's behavior patterns:

Activity Patterns:
{json.dumps(posting_patterns, indent=2)}

Posts and Comments:
{content}"""
            }
        ]
        
        return self._make_api_call(messages, temperature=0.4)
    
    def _calculate_subreddit_activity(self, user_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate user activity across subreddits.
        
        Args:
            user_data: Dictionary containing user posts and comments
            
        Returns:
            Dictionary mapping subreddit names to activity counts
        """
        activity = Counter()
        
        # Count posts by subreddit
        for post in user_data.get('posts', []):
            subreddit = post.get('subreddit', '')
            if subreddit:
                activity[subreddit] += 1
        
        # Count comments by subreddit
        for comment in user_data.get('comments', []):
            subreddit = comment.get('subreddit', '')
            if subreddit:
                activity[subreddit] += 1
        
        return dict(activity.most_common())
    
    def _calculate_posting_patterns(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate posting patterns and timing analysis.
        
        Args:
            user_data: Dictionary containing user posts and comments
            
        Returns:
            Dictionary containing posting pattern analysis
        """
        posts = user_data.get('posts', [])
        comments = user_data.get('comments', [])
        
        # Combine timestamps
        timestamps = []
        timestamps.extend([post.get('created_utc', 0) for post in posts])
        timestamps.extend([comment.get('created_utc', 0) for comment in comments])
        timestamps = [ts for ts in timestamps if ts > 0]
        
        if not timestamps:
            return {}
        
        timestamps.sort()
        
        # Calculate patterns
        hours = [datetime.fromtimestamp(ts).hour for ts in timestamps]
        days = [datetime.fromtimestamp(ts).weekday() for ts in timestamps]
        
        return {
            'total_posts': len(posts),
            'total_comments': len(comments),
            'total_activity': len(timestamps),
            'most_active_hour': Counter(hours).most_common(1)[0][0] if hours else None,
            'most_active_day': Counter(days).most_common(1)[0][0] if days else None,
            'activity_span_days': (max(timestamps) - min(timestamps)) / 86400 if len(timestamps) > 1 else 0,
            'average_daily_activity': len(timestamps) / max(1, (max(timestamps) - min(timestamps)) / 86400) if len(timestamps) > 1 else 0
        }
    
    def build_persona(self, user_data: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
        """
        Build comprehensive user persona from Reddit data.
        
        Args:
            user_data: Dictionary containing scraped Reddit data
            username: Reddit username
            
        Returns:
            Dictionary containing complete persona analysis or None if failed
        """
        self.logger.info(f"Building persona for user: {username}")
        
        # Prepare content for analysis
        content, citation_map = self._prepare_content_for_analysis(user_data)
        
        if not content.strip():
            self.logger.error(f"No content available for persona analysis for user: {username}")
            return None
        
        # Generate different aspects of the persona
        demographics = self._generate_demographics_analysis(content)
        interests = self._generate_interests_analysis(content, user_data)
        personality = self._generate_personality_analysis(content)
        behavior = self._generate_behavior_analysis(content, user_data)
        
        # Check if any analysis failed
        if not any([demographics, interests, personality, behavior]):
            self.logger.error(f"Failed to generate persona analysis for user: {username}")
            return None
        
        # Calculate additional statistics
        subreddit_activity = self._calculate_subreddit_activity(user_data)
        posting_patterns = self._calculate_posting_patterns(user_data)
        
        # Compile persona
        persona = {
            'username': username,
            'analysis': {
                'demographics': demographics or "Analysis failed",
                'interests': interests or "Analysis failed",
                'personality': personality or "Analysis failed",
                'behavior': behavior or "Analysis failed"
            },
            'statistics': {
                'subreddit_activity': subreddit_activity,
                'posting_patterns': posting_patterns,
                'scraping_stats': user_data.get('scraping_stats', {}),
                'user_info': user_data.get('user_info', {})
            },
            'citations': citation_map,
            'generation_timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Successfully built persona for user: {username}")
        return persona