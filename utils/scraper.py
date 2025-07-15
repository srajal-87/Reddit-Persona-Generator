import os
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import praw
from praw.exceptions import RedditAPIException
from tqdm import tqdm


class RedditScraper:
    """
    A Reddit data scraper that extracts user posts and comments using PRAW.
    
    Attributes:
        reddit: PRAW Reddit instance
        logger: Logger instance for debugging and error tracking
    """
    
    def __init__(self):
        """Initialize the Reddit scraper with API credentials."""
        self.logger = logging.getLogger(__name__)
        self.reddit = self._initialize_reddit()
    
    def _initialize_reddit(self) -> praw.Reddit:
        """
        Initialize PRAW Reddit instance with environment variables.
        
        Returns:
            praw.Reddit: Configured Reddit instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        try:
            reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'PersonaGenerator/1.0 by /u/yourusername')
            )
            
            # Test the connection
            reddit.user.me()
            self.logger.info("Successfully initialized Reddit API connection")
            return reddit
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit API: {str(e)}")
            raise ValueError("Failed to initialize Reddit API connection") from e
    
    def _safe_get_attribute(self, obj: Any, attr: str, default: Any = None) -> Any:
        """
        Safely get attribute from Reddit object with error handling.
        
        Args:
            obj: Reddit object (post, comment, etc.)
            attr: Attribute name to retrieve
            default: Default value if attribute doesn't exist
            
        Returns:
            Attribute value or default
        """
        try:
            return getattr(obj, attr, default)
        except (AttributeError, RedditAPIException):
            return default
    
    def _extract_post_data(self, post) -> Dict[str, Any]:
        """
        Extract relevant data from a Reddit post.
        
        Args:
            post: PRAW Submission object
            
        Returns:
            Dictionary containing post data
        """
        return {
            'id': self._safe_get_attribute(post, 'id'),
            'title': self._safe_get_attribute(post, 'title', ''),
            'selftext': self._safe_get_attribute(post, 'selftext', ''),
            'subreddit': str(self._safe_get_attribute(post, 'subreddit', '')),
            'score': self._safe_get_attribute(post, 'score', 0),
            'upvote_ratio': self._safe_get_attribute(post, 'upvote_ratio', 0.0),
            'num_comments': self._safe_get_attribute(post, 'num_comments', 0),
            'created_utc': self._safe_get_attribute(post, 'created_utc', 0),
            'url': self._safe_get_attribute(post, 'url', ''),
            'permalink': self._safe_get_attribute(post, 'permalink', ''),
            'is_self': self._safe_get_attribute(post, 'is_self', False),
            'link_flair_text': self._safe_get_attribute(post, 'link_flair_text', ''),
            'over_18': self._safe_get_attribute(post, 'over_18', False)
        }
    
    def _extract_comment_data(self, comment) -> Dict[str, Any]:
        """
        Extract relevant data from a Reddit comment.
        
        Args:
            comment: PRAW Comment object
            
        Returns:
            Dictionary containing comment data
        """
        return {
            'id': self._safe_get_attribute(comment, 'id'),
            'body': self._safe_get_attribute(comment, 'body', ''),
            'subreddit': str(self._safe_get_attribute(comment, 'subreddit', '')),
            'score': self._safe_get_attribute(comment, 'score', 0),
            'created_utc': self._safe_get_attribute(comment, 'created_utc', 0),
            'permalink': self._safe_get_attribute(comment, 'permalink', ''),
            'parent_id': self._safe_get_attribute(comment, 'parent_id', ''),
            'submission_title': self._safe_get_attribute(
                self._safe_get_attribute(comment, 'submission'), 'title', ''
            ),
            'is_submitter': self._safe_get_attribute(comment, 'is_submitter', False),
            'stickied': self._safe_get_attribute(comment, 'stickied', False)
        }
    
    def _scrape_posts(self, username: str, max_posts: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape user's posts.
        
        Args:
            username: Reddit username
            max_posts: Maximum number of posts to scrape
            
        Returns:
            List of post dictionaries
        """
        posts = []
        
        try:
            user = self.reddit.redditor(username)
            submissions = user.submissions.new(limit=max_posts)
            
            self.logger.info(f"Scraping posts for user: {username}")
            
            for post in tqdm(submissions, desc="Scraping posts", unit="post"):
                try:
                    post_data = self._extract_post_data(post)
                    posts.append(post_data)
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing post {post.id}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(posts)} posts")
            return posts
            
        except RedditAPIException as e:
            # Handle user not found or private profile
            if "NOT_FOUND" in str(e) or "SUBREDDIT_NOTFOUND" in str(e):
                self.logger.error(f"User {username} not found")
            elif "FORBIDDEN" in str(e) or "SUSPENDED" in str(e):
                self.logger.error(f"User {username} profile is private or suspended")
            else:
                self.logger.error(f"Reddit API error for {username}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Error scraping posts for {username}: {str(e)}")
            return []
    
    def _scrape_comments(self, username: str, max_comments: int = 200) -> List[Dict[str, Any]]:
        """
        Scrape user's comments.
        
        Args:
            username: Reddit username
            max_comments: Maximum number of comments to scrape
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        try:
            user = self.reddit.redditor(username)
            user_comments = user.comments.new(limit=max_comments)
            
            self.logger.info(f"Scraping comments for user: {username}")
            
            for comment in tqdm(user_comments, desc="Scraping comments", unit="comment"):
                try:
                    # Skip deleted or removed comments
                    if comment.body in ['[deleted]', '[removed]']:
                        continue
                    
                    comment_data = self._extract_comment_data(comment)
                    comments.append(comment_data)
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing comment {comment.id}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(comments)} comments")
            return comments
            
        except RedditAPIException as e:
            # Handle user not found or private profile
            if "NOT_FOUND" in str(e) or "SUBREDDIT_NOTFOUND" in str(e):
                self.logger.error(f"User {username} not found")
            elif "FORBIDDEN" in str(e) or "SUSPENDED" in str(e):
                self.logger.error(f"User {username} profile is private or suspended")
            else:
                self.logger.error(f"Reddit API error for {username}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Error scraping comments for {username}: {str(e)}")
            return []
    
    def _get_user_info(self, username: str) -> Dict[str, Any]:
        """
        Get basic user information.
        
        Args:
            username: Reddit username
            
        Returns:
            Dictionary containing user information
        """
        try:
            user = self.reddit.redditor(username)
            
            return {
                'username': username,
                'id': self._safe_get_attribute(user, 'id'),
                'created_utc': self._safe_get_attribute(user, 'created_utc', 0),
                'comment_karma': self._safe_get_attribute(user, 'comment_karma', 0),
                'link_karma': self._safe_get_attribute(user, 'link_karma', 0),
                'is_gold': self._safe_get_attribute(user, 'is_gold', False),
                'is_mod': self._safe_get_attribute(user, 'is_mod', False),
                'has_verified_email': self._safe_get_attribute(user, 'has_verified_email', False),
                'account_age_days': (
                    (datetime.now().timestamp() - self._safe_get_attribute(user, 'created_utc', 0)) / 86400
                ) if self._safe_get_attribute(user, 'created_utc') else 0
            }
            
        except RedditAPIException as e:
            # Handle user not found or private profile
            if "NOT_FOUND" in str(e) or "FORBIDDEN" in str(e) or "SUSPENDED" in str(e):
                self.logger.error(f"User {username} not found or inaccessible")
            else:
                self.logger.error(f"Reddit API error for {username}: {str(e)}")
            return {'username': username}
        except Exception as e:
            self.logger.error(f"Error getting user info for {username}: {str(e)}")
            return {'username': username}
    
    def scrape_user_data(self, username: str, max_posts: int = 100, max_comments: int = 200) -> Dict[str, Any]:
        """
        Scrape comprehensive user data including posts, comments, and profile info.
        
        Args:
            username: Reddit username
            max_posts: Maximum number of posts to scrape
            max_comments: Maximum number of comments to scrape
            
        Returns:
            Dictionary containing all user data
        """
        self.logger.info(f"Starting data scraping for user: {username}")
        
        # Get user info
        user_info = self._get_user_info(username)
        
        # Scrape posts and comments
        posts = self._scrape_posts(username, max_posts)
        comments = self._scrape_comments(username, max_comments)
        
        # Compile all data
        user_data = {
            'user_info': user_info,
            'posts': posts,
            'comments': comments,
            'scraping_stats': {
                'posts_scraped': len(posts),
                'comments_scraped': len(comments),
                'scraping_timestamp': datetime.now().isoformat()
            }
        }
        
        self.logger.info(f"Completed data scraping for {username}: {len(posts)} posts, {len(comments)} comments")
        return user_data
    
    def get_subreddit_activity(self, posts: List[Dict], comments: List[Dict]) -> Dict[str, int]:
        """
        Analyze subreddit activity from posts and comments.
        
        Args:
            posts: List of post dictionaries
            comments: List of comment dictionaries
            
        Returns:
            Dictionary mapping subreddit names to activity counts
        """
        subreddit_activity = {}
        
        # Count posts by subreddit
        for post in posts:
            subreddit = post.get('subreddit', '')
            if subreddit:
                subreddit_activity[subreddit] = subreddit_activity.get(subreddit, 0) + 1
        
        # Count comments by subreddit
        for comment in comments:
            subreddit = comment.get('subreddit', '')
            if subreddit:
                subreddit_activity[subreddit] = subreddit_activity.get(subreddit, 0) + 1
        
        # Sort by activity level
        return dict(sorted(subreddit_activity.items(), key=lambda x: x[1], reverse=True))
    
    def get_posting_patterns(self, posts: List[Dict], comments: List[Dict]) -> Dict[str, Any]:
        """
        Analyze posting patterns and activity levels.
        
        Args:
            posts: List of post dictionaries
            comments: List of comment dictionaries
            
        Returns:
            Dictionary containing posting pattern analysis
        """
        if not posts and not comments:
            return {}
        
        # Combine timestamps
        timestamps = []
        timestamps.extend([post.get('created_utc', 0) for post in posts])
        timestamps.extend([comment.get('created_utc', 0) for comment in comments])
        timestamps = [ts for ts in timestamps if ts > 0]
        
        if not timestamps:
            return {}
        
        # Calculate patterns
        timestamps.sort()
        
        # Time-based analysis
        hours = [datetime.fromtimestamp(ts).hour for ts in timestamps]
        days = [datetime.fromtimestamp(ts).weekday() for ts in timestamps]
        
        hour_distribution = {}
        for hour in hours:
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        
        day_distribution = {}
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days:
            day_name = day_names[day]
            day_distribution[day_name] = day_distribution.get(day_name, 0) + 1
        
        return {
            'total_activity': len(timestamps),
            'most_active_hour': max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None,
            'most_active_day': max(day_distribution.items(), key=lambda x: x[1])[0] if day_distribution else None,
            'hour_distribution': hour_distribution,
            'day_distribution': day_distribution,
            'activity_timespan_days': (max(timestamps) - min(timestamps)) / 86400 if len(timestamps) > 1 else 0
        }