"""
Chat service for RAG chatbot
Handles conversation flow and LLM integration
"""

import logging
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os
from dotenv import load_dotenv

from openai import OpenAI
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

from src.services.chatbot.retrieval_service import RetrievalService
from src.services.chatbot.embedding_service import EmbeddingService
from src.db.database_conn import NewsDatabase

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat conversations with RAG"""

    def __init__(self,
                 openai_api_key: Optional[str] = None,
                 anthropic_api_key: Optional[str] = None,
                 retrieval_service: Optional[RetrievalService] = None):
        """
        Initialize chat service

        Args:
            openai_api_key: OpenAI API key (will try to get from env if not provided)
            anthropic_api_key: Anthropic API key (will try to get from env if not provided)
            retrieval_service: Optional retrieval service instance
        """
        # Initialize AI clients (prefer Claude/Anthropic, fallback to OpenAI)
        anthropic_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        self.anthropic_client = None
        self.openai_client = None

        if anthropic_key:
            try:
                self.anthropic_client = Anthropic(api_key=anthropic_key)
                logger.info("Initialized Claude/Anthropic client successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

        if openai_key and not self.anthropic_client:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("Initialized OpenAI client successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        if not self.anthropic_client and not self.openai_client:
            logger.warning("No AI API keys provided. Chatbot will use mock responses.")

        # Initialize services
        self.retrieval_service = retrieval_service or RetrievalService()
        self.db = NewsDatabase()

        # Configuration
        self.model_name = "gpt-3.5-turbo"
        self.max_tokens = 500
        self.temperature = 0.7

    def create_session(self, user_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """
        Create a new chat session

        Args:
            user_id: Optional user identifier
            title: Optional session title

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        success = self.db.save_chat_session(
            session_id=session_id,
            user_id=user_id,
            title=title or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        if success:
            logger.info(f"Created new chat session: {session_id}")
            return session_id
        else:
            logger.error(f"Failed to create chat session")
            raise Exception("Failed to create chat session")

    def chat(self, session_id: str, user_message: str,
             category_filter: Optional[str] = None) -> Dict:
        """
        Process a chat message and generate response

        Args:
            session_id: Chat session ID
            user_message: User's message
            category_filter: Optional category to filter context

        Returns:
            Dictionary with response and metadata
        """
        try:
            logger.info(f"Processing chat message in session {session_id}")

            # Save user message
            self.db.save_chat_message(session_id, 'user', user_message)

            # Retrieve relevant context
            context_articles = self.retrieval_service.retrieve_context(
                user_message, max_articles=5, category_filter=category_filter
            )

            # Get conversation history
            chat_history = self.db.get_chat_messages(session_id, limit=10)

            # Generate response (prefer Claude, fallback to OpenAI, then mock)
            if self.anthropic_client:
                response_content, sources = self._generate_claude_response(
                    user_message, context_articles, chat_history
                )
            elif self.openai_client:
                response_content, sources = self._generate_llm_response(
                    user_message, context_articles, chat_history
                )
            else:
                response_content, sources = self._generate_mock_response(
                    user_message, context_articles
                )

            # Save assistant message
            response_metadata = {
                'sources': sources,
                'context_articles_count': len(context_articles),
                'model': self.model_name if self.openai_client else 'mock'
            }

            self.db.save_chat_message(
                session_id, 'assistant', response_content, response_metadata
            )

            return {
                'response': response_content,
                'sources': sources,
                'context_articles': context_articles[:3],  # Return top 3 for reference
                'session_id': session_id
            }

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            error_response = "I apologize, but I encountered an error while processing your question. Please try again."

            # Save error response
            self.db.save_chat_message(session_id, 'assistant', error_response, {'error': str(e)})

            return {
                'response': error_response,
                'sources': [],
                'context_articles': [],
                'session_id': session_id,
                'error': str(e)
            }

    def _generate_claude_response(self, user_message: str, context_articles: List[Dict],
                                 chat_history: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        Generate response using Claude/Anthropic API

        Args:
            user_message: User's question
            context_articles: Retrieved context articles
            chat_history: Previous conversation messages

        Returns:
            Tuple of (response_content, sources_used)
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt()

            # Build context from articles
            context_text = self._build_context_section(context_articles)

            # Build conversation history
            messages = []

            # Add recent chat history
            for msg in chat_history[-6:]:  # Last 6 messages for context
                role = "user" if msg['role'] == 'user' else "assistant"
                messages.append({
                    "role": role,
                    "content": msg['content']
                })

            # Add current user message with context
            user_content = f"""Context from recent Australian news articles:
{context_text}

User question: {user_message}"""

            messages.append({
                "role": "user",
                "content": user_content
            })

            # Generate response using Claude
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Latest Claude model
                max_tokens=1024,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )

            response_content = response.content[0].text

            # Extract sources used (articles that were provided as context)
            sources_used = [
                {
                    'title': article['title'],
                    'url': article['url'],
                    'source': article['source'],
                    'published_date': article.get('published_date', ''),
                    'summary': article.get('summary', '')
                }
                for article in context_articles[:5]  # Limit to first 5 sources
            ]

            return response_content, sources_used

        except Exception as e:
            logger.error(f"Error generating Claude response: {e}")
            # Fallback to mock response if Claude fails
            return self._generate_mock_response(user_message, context_articles)

    def _generate_llm_response(self, user_message: str, context_articles: List[Dict],
                              chat_history: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        Generate response using OpenAI LLM

        Args:
            user_message: User's question
            context_articles: Retrieved context articles
            chat_history: Previous conversation messages

        Returns:
            Tuple of (response_content, sources_used)
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt()

            # Build context section
            context_section = self._build_context_section(context_articles)

            # Build conversation history
            messages = [{"role": "system", "content": system_prompt}]

            # Add relevant chat history (last few messages)
            for msg in chat_history[-6:]:  # Last 3 exchanges
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add current context and user message
            current_prompt = f"""
Context from Australian News Articles:
{context_section}

User Question: {user_message}

Please provide a helpful and accurate response based on the news context provided above.
"""

            messages.append({"role": "user", "content": current_prompt})

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            response_content = response.choices[0].message.content

            # Extract sources used in response
            sources = self._extract_sources_from_articles(context_articles)

            logger.info(f"Generated LLM response with {len(sources)} sources")
            return response_content, sources

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise

    def _generate_mock_response(self, user_message: str,
                               context_articles: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        Generate mock response when OpenAI is not available

        Args:
            user_message: User's question
            context_articles: Retrieved context articles

        Returns:
            Tuple of (response_content, sources_used)
        """
        if not context_articles:
            return (
                "I don't have enough current news information to answer your question. "
                "Please try asking about recent Australian news topics.",
                []
            )

        # Create a simple response based on article titles and summaries
        response_parts = [
            f"Based on recent Australian news, here's what I found about your query:"
        ]

        sources = []
        for i, article in enumerate(context_articles[:3], 1):
            response_parts.append(
                f"{i}. {article['title']} - {article['summary'][:100]}..."
            )
            sources.append({
                'title': article['title'],
                'source': article['source'],
                'url': article['url'],
                'category': article['category']
            })

        response_parts.append(
            "\n(Note: This is a demo response. Full AI responses require OpenAI API configuration.)"
        )

        return "\n\n".join(response_parts), sources

    def _build_system_prompt(self) -> str:
        """Build system prompt for the AI assistant"""
        return """You are an AI assistant specialized in Australian news and current events.
Your role is to help users understand and discuss recent news from major Australian sources
including ABC News, The Guardian Australia, Sydney Morning Herald, and News.com.au.

Guidelines:
- Provide accurate, helpful responses based on the provided news context
- If you don't have enough information, say so clearly
- Cite your sources when possible by mentioning the news outlet
- Keep responses concise but informative
- Focus on facts from the articles provided
- If asked about topics not covered in the context, explain that limitation
- Be conversational but professional
- Help users understand complex news topics when needed

Remember: You only have access to recent Australian news articles provided as context."""

    def _build_context_section(self, context_articles: List[Dict]) -> str:
        """
        Build context section from retrieved articles

        Args:
            context_articles: List of relevant articles

        Returns:
            Formatted context string
        """
        if not context_articles:
            return "No relevant news articles found for this query."

        context_parts = []

        for i, article in enumerate(context_articles, 1):
            context_parts.append(f"""
Article {i}:
Title: {article['title']}
Source: {article['source']} ({article['category']})
Summary: {article['summary']}
Relevance Score: {article.get('final_score', article.get('relevance_score', 0)):.2f}
""")

        return "\n".join(context_parts)

    def _extract_sources_from_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Extract source information from articles

        Args:
            articles: List of articles

        Returns:
            List of source dictionaries
        """
        sources = []
        for article in articles:
            sources.append({
                'title': article['title'],
                'source': article['source'],
                'url': article['url'],
                'category': article['category'],
                'relevance_score': article.get('final_score', article.get('relevance_score', 0))
            })
        return sources

    def get_session_history(self, session_id: str) -> List[Dict]:
        """
        Get chat history for a session

        Args:
            session_id: Session ID

        Returns:
            List of messages
        """
        return self.db.get_chat_messages(session_id)

    def clear_session(self, session_id: str) -> bool:
        """
        Clear chat session (for future implementation)

        Args:
            session_id: Session ID to clear

        Returns:
            Success status
        """
        # Note: This would require a database method to delete session and messages
        # For now, just log the intent
        logger.info(f"Session clear requested for {session_id}")
        return True

    def get_chat_stats(self) -> Dict:
        """Get statistics about the chat system"""
        try:
            import sqlite3

            with sqlite3.connect(self.db.db_path, timeout=30.0) as conn:
                # Count sessions
                cursor = conn.execute("SELECT COUNT(*) FROM chat_sessions")
                total_sessions = cursor.fetchone()[0]

                # Count messages
                cursor = conn.execute("SELECT COUNT(*) FROM chat_messages")
                total_messages = cursor.fetchone()[0]

                # Count by role
                cursor = conn.execute("""
                    SELECT role, COUNT(*) as count
                    FROM chat_messages
                    GROUP BY role
                """)
                message_counts = dict(cursor.fetchall())

                # Get retrieval stats
                retrieval_stats = self.retrieval_service.get_retrieval_stats()

                return {
                    'total_sessions': total_sessions,
                    'total_messages': total_messages,
                    'message_counts': message_counts,
                    'openai_configured': self.openai_client is not None,
                    'model_name': self.model_name,
                    'retrieval_stats': retrieval_stats
                }

        except Exception as e:
            logger.error(f"Error getting chat stats: {e}")
            return {'error': str(e)}