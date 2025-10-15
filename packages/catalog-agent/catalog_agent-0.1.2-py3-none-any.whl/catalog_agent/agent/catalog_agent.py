"""Main catalog agent implementation using LangChain."""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..types.core import AgentConfig, Message, ConversationContext, ProductResult, ConfigurationError
from ..types.agent import AgentResponse, AgentState
from ..config import ConfigLoader
from .supabase_client import SupabaseClient
from .tools import create_catalog_tools
from ..intent import IntentService


class CatalogAgent:
    """AI-powered catalog agent for product discovery and recommendations."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the catalog agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.session_states: Dict[str, AgentState] = {}
        self.instructions: Dict[str, Any] = {}
        self.catalog_data: Dict[str, Any] = {}
        self.intent_service: Optional[IntentService] = None
        self.supabase_client: Optional[SupabaseClient] = None
        self.llm: Optional[ChatOpenAI] = None
        self.agent_executor: Optional[AgentExecutor] = None
        
        # Initialize the agent
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """Initialize the agent components."""
        try:
            # Load configuration
            config_loader = ConfigLoader(self.config.config_path)
            all_configs = config_loader.get_all_configs()
            
            self.instructions = all_configs.get('instructions', {})
            self.catalog_data = all_configs.get('discover_products', {})
            
            # Initialize Supabase client
            self.supabase_client = SupabaseClient(
                supabase_functions_url=self.config.supabase_functions_url,
                gpt_actions_api_key=self.config.gpt_actions_api_key
            )
            
            # Initialize intent service
            self.intent_service = IntentService(
                catalog_data=self.catalog_data,
                synonyms=all_configs.get('intent_synonyms', {}),
                top_n=10
            )
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=self.config.openai_api_key
            )
            
            # Create tools
            tools = create_catalog_tools(self.supabase_client)
            
            # Create agent prompt
            prompt = self._create_agent_prompt()
            
            # Create agent
            agent = create_openai_tools_agent(self.llm, tools, prompt)
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=self.config.debug,
                handle_parsing_errors=True
            )
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize CatalogAgent: {str(e)}"
            )
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template."""
        system_message = self.instructions.get('system', '')
        if not system_message:
            system_message = """You are a helpful AI assistant for product discovery and recommendations. 
            You help users find products by understanding their needs and searching through the catalog.
            Use the available tools to search, filter, and discover products based on user queries."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        return prompt
    
    def chat(self, message: str, session_id: Optional[str] = None) -> AgentResponse:
        """Process a user message and return an agent response.
        
        Args:
            message: User message
            session_id: Optional session ID
            
        Returns:
            Agent response
        """
        start_time = time.time()
        effective_session_id = session_id or self.config.session_id or 'default'
        session_state = self._get_or_create_session(effective_session_id)
        session_state.conversation_context.last_activity = datetime.now()
        
        # Record user message
        self._record_user_message(session_state, message, effective_session_id)
        
        try:
            # Check for info request
            info_request = self.intent_service.detect_info_request(message)
            if info_request:
                response = self._handle_info_request(
                    session_state, info_request, start_time, effective_session_id
                )
                self._record_assistant_message(session_state, response.message, effective_session_id)
                return response
            
            # Analyze intent
            analysis = self.intent_service.analyze(message)
            
            if not analysis.high_confidence:
                response = self._handle_low_confidence_intent(
                    session_state, analysis, message, start_time, effective_session_id
                )
                self._record_assistant_message(session_state, response.message, effective_session_id)
                return response
            
            # Reset failure counter on success
            session_state.retry_count = 0
            session_state.last_query = analysis.normalized_query
            session_state.current_intent = "product_search"
            
            # Run agent with tools
            response = self._run_agent_with_tools(
                message, analysis, start_time, effective_session_id
            )
            self._record_assistant_message(session_state, response.message, effective_session_id)
            return response
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            if self.config.debug:
                print(f"[CatalogAgent] Error: {e}")
            
            return AgentResponse(
                message="I ran into an unexpected issue reaching the catalog. Please try again in a moment.",
                success=False,
                metadata={
                    "session_id": effective_session_id,
                    "duration_ms": duration,
                    "workflow": "error"
                }
            )
    
    def stream_chat(self, message: str, session_id: Optional[str] = None):
        """Stream chat response (placeholder for future implementation).
        
        Args:
            message: User message
            session_id: Optional session ID
            
        Yields:
            Streaming response chunks
        """
        # For now, just return the regular chat response
        response = self.chat(message, session_id)
        yield response.message
    
    def reset_conversation(self, session_id: Optional[str] = None) -> None:
        """Reset conversation for a session.
        
        Args:
            session_id: Optional session ID
        """
        effective_session_id = session_id or self.config.session_id or 'default'
        if effective_session_id in self.session_states:
            del self.session_states[effective_session_id]
    
    def get_conversation_context(self, session_id: Optional[str] = None) -> Optional[ConversationContext]:
        """Get conversation context for a session.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            Conversation context or None
        """
        effective_session_id = session_id or self.config.session_id or 'default'
        session_state = self.session_states.get(effective_session_id)
        if session_state:
            return session_state.conversation_context
        return None
    
    def update_user_preferences(
        self, 
        preferences: Dict[str, Any], 
        session_id: Optional[str] = None
    ) -> None:
        """Update user preferences for a session.
        
        Args:
            preferences: User preferences
            session_id: Optional session ID
        """
        effective_session_id = session_id or self.config.session_id or 'default'
        session_state = self._get_or_create_session(effective_session_id)
        
        if not session_state.conversation_context.user_preferences:
            session_state.conversation_context.user_preferences = {}
        
        session_state.conversation_context.user_preferences.update(preferences)
    
    def _get_or_create_session(self, session_id: str) -> AgentState:
        """Get or create session state."""
        if session_id not in self.session_states:
            self.session_states[session_id] = AgentState(
                conversation_context=ConversationContext(session_id=session_id)
            )
        return self.session_states[session_id]
    
    def _record_user_message(self, session_state: AgentState, content: str, session_id: str) -> None:
        """Record user message in session."""
        message = Message(
            role="user",
            content=content,
            timestamp=datetime.now(),
            session_id=session_id
        )
        session_state.conversation_context.messages.append(message)
    
    def _record_assistant_message(self, session_state: AgentState, content: str, session_id: str) -> None:
        """Record assistant message in session."""
        message = Message(
            role="assistant",
            content=content,
            timestamp=datetime.now(),
            session_id=session_id
        )
        session_state.conversation_context.messages.append(message)
    
    def _handle_info_request(
        self, 
        session_state: AgentState, 
        request: str, 
        start_time: float, 
        session_id: str
    ) -> AgentResponse:
        """Handle information request."""
        entries = self.intent_service.get_top_entries(request)
        
        heading = {
            'vendors': 'our featured vendors',
            'categories': 'popular categories',
            'attributes': 'common product attributes'
        }.get(request, 'information')
        
        lines = [f"{i+1}. {entry}" for i, entry in enumerate(entries)]
        
        message = [
            f"Here are the top {len(entries)} {heading} in our catalog right now:",
            *lines,
            "",
            "Tell me which of these stand out (or add more details) and I'll narrow the search right away."
        ]
        
        duration = (time.time() - start_time) * 1000
        return AgentResponse(
            message="\n".join(message),
            success=False,
            metadata={
                "session_id": session_id,
                "duration_ms": duration,
                "workflow": "info_request",
                "tools_used": []
            }
        )
    
    def _handle_low_confidence_intent(
        self,
        session_state: AgentState,
        analysis,
        user_input: str,
        start_time: float,
        session_id: str
    ) -> AgentResponse:
        """Handle low confidence intent detection."""
        session_state.retry_count += 1
        
        if self.config.debug:
            print(f"[CatalogAgent] Low-confidence intent detected (attempt {session_state.retry_count})")
        
        if session_state.retry_count >= 2:
            # Fallback to semantic search
            session_state.retry_count = 0
            return self._run_semantic_fallback(analysis, user_input, start_time, session_id)
        
        stats = self.intent_service.get_stats_snapshot()
        suggestion_lines = analysis.suggested_facets or [
            "- Mention a category (e.g., dresses, jackets, accessories)",
            "- Share a brand you like",
            "- Include color, size, or occasion keywords"
        ]
        
        message_sections = [
            "I'm close, but I need a bit more detail to lock onto the right products (I only found one catalog area above 90% confidence).",
            f"📦 Catalog snapshot: {stats.total_products or 'many'} products across {stats.total_categories or 'many'} categories and {stats.total_vendors or 'dozens'} vendors." if stats.total_products else None,
            f"Popular categories: {', '.join(stats.top_categories[:5])}" if stats.top_categories else None,
            f"Featured brands: {', '.join(stats.top_vendors[:5])}" if stats.top_vendors else None,
            "",
            "Try one of these ideas to sharpen the search:",
            *[f"- {suggestion}" for suggestion in suggestion_lines],
            "",
            "Once you tell me the key category, brand, or attribute, I'll shortlist matching products right away."
        ]
        
        duration = (time.time() - start_time) * 1000
        return AgentResponse(
            message="\n".join([s for s in message_sections if s]),
            success=False,
            metadata={
                "session_id": session_id,
                "duration_ms": duration,
                "workflow": "intent_clarification",
                "tools_used": []
            }
        )
    
    def _run_semantic_fallback(self, analysis, user_input: str, start_time: float, session_id: str) -> AgentResponse:
        """Run semantic search fallback."""
        try:
            # Use the search_products tool for semantic search
            products = self.supabase_client.search_products(
                query=analysis.query_for_search,
                limit=10
            )
            
            if not products:
                stats = self.intent_service.get_stats_snapshot()
                message = [
                    f"I searched the entire catalog for \"{user_input}\", but nothing matched confidently.",
                    f"Common attributes include: {', '.join(stats.top_attributes[:5])}" if stats.top_attributes else None,
                    "Could you share a specific category, brand, size, or color so I can re-run a more targeted search?"
                ]
                
                duration = (time.time() - start_time) * 1000
                return AgentResponse(
                    message="\n".join([s for s in message if s]),
                    success=False,
                    metadata={
                        "session_id": session_id,
                        "duration_ms": duration,
                        "workflow": "semantic_fallback_empty",
                        "tools_used": ["search_products"]
                    }
                )
            
            message = self._format_product_list(
                f"I broadened the search across the entire catalog for \"{user_input}.\" Here are the closest matches:",
                products
            )
            
            duration = (time.time() - start_time) * 1000
            return AgentResponse(
                message=message,
                success=True,
                products=products,
                metadata={
                    "session_id": session_id,
                    "duration_ms": duration,
                    "workflow": "semantic_fallback",
                    "tools_used": ["search_products"]
                }
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return AgentResponse(
                message=f"Error during semantic search: {str(e)}",
                success=False,
                metadata={
                    "session_id": session_id,
                    "duration_ms": duration,
                    "workflow": "semantic_fallback_error"
                }
            )
    
    def _run_agent_with_tools(
        self, 
        message: str, 
        analysis, 
        start_time: float, 
        session_id: str
    ) -> AgentResponse:
        """Run the agent with tools."""
        try:
            if self.config.debug:
                print(f"[CatalogAgent] Running agent with tools for query: '{message}'")
                print(f"[CatalogAgent] Intent analysis: {analysis.normalized_query}")
            
            # Prepare chat history
            session_state = self._get_or_create_session(session_id)
            chat_history = []
            
            for msg in session_state.conversation_context.messages[-10:]:  # Last 10 messages
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    chat_history.append(AIMessage(content=msg.content))
            
            # Run agent
            result = self.agent_executor.invoke({
                "input": message,
                "chat_history": chat_history
            })
            
            if self.config.debug:
                print(f"[CatalogAgent] Agent result: {result}")
            
            # Extract products from tool results
            products = []
            tools_used = []
            
            # Check if there are intermediate steps (tool calls)
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if isinstance(step, list) and len(step) >= 2:
                        tool_name = step[0].tool if hasattr(step[0], 'tool') else str(step[0])
                        tool_result = step[1]
                        tools_used.append(tool_name)
                        
                        if self.config.debug:
                            print(f"[CatalogAgent] Tool '{tool_name}' result: {tool_result}")
                        
                        # Try to extract products from tool result
                        if isinstance(tool_result, str):
                            try:
                                import json
                                tool_data = json.loads(tool_result)
                                if tool_data.get("success") and "results" in tool_data:
                                    for product_data in tool_data["results"]:
                                        products.append(ProductResult(**product_data))
                            except (json.JSONDecodeError, TypeError, KeyError):
                                pass
            
            if self.config.debug:
                print(f"[CatalogAgent] Extracted {len(products)} products")
                print(f"[CatalogAgent] Tools used: {tools_used}")
            
            duration = (time.time() - start_time) * 1000
            return AgentResponse(
                message=result.get("output", "I couldn't process that request."),
                success=True,
                products=products,
                metadata={
                    "session_id": session_id,
                    "duration_ms": duration,
                    "workflow": "agent_with_tools",
                    "tools_used": tools_used
                }
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            if self.config.debug:
                print(f"[CatalogAgent] Error in _run_agent_with_tools: {e}")
            return AgentResponse(
                message=f"Error processing request: {str(e)}",
                success=False,
                metadata={
                    "session_id": session_id,
                    "duration_ms": duration,
                    "workflow": "agent_error"
                }
            )
    
    def _format_product_list(self, header: str, products: List[ProductResult], more_available: int = 0) -> str:
        """Format product list for display."""
        lines = []
        for i, product in enumerate(products[:5]):
            parts = [
                f"{i+1}. {product.title}",
                product.url or f"https://shop.styledgenie.com/products/{product.handle}"
            ]
            
            if product.score is not None:
                parts.append(f"score {product.score:.2f}")
            
            lines.append(" — ".join(parts))
        
        if more_available > 0:
            lines.append(f"…and {more_available} more matches ready when you're interested.")
        elif len(products) > 5:
            lines.append("…and more matches available—just say the word to see them.")
        
        lines.append("Would you like me to tweak sizes, colors, brands, or show additional options?")
        
        return "\n".join([header, *lines])
    
    def health_check(self) -> bool:
        """Check if the agent is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.supabase_client:
                return False
            return self.supabase_client.health_check()
        except Exception:
            return False
