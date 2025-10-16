# Catalog Agent

AI-powered catalog agent for product discovery and recommendations using LangChain, Pydantic, and Supabase.

## Features

- **Intelligent Product Search**: AI-powered semantic search and filtering
- **Intent Detection**: Advanced intent recognition with synonym matching
- **Conversation Management**: Multi-session conversation tracking
- **User Preferences**: Personalized recommendations based on user preferences
- **LangChain Integration**: Built on LangChain for robust AI agent capabilities
- **Type Safety**: Full type safety with Pydantic models
- **Supabase Integration**: Seamless integration with Supabase for product data

## Installation

### From PyPI (Recommended)

```bash
pip install catalog-agent
```

### From Source

```bash
git clone https://github.com/komatadi/catalog-agent.git
cd catalog-agent
pip install -e .
```

## Quick Start

### Basic Usage

```python
from catalog_agent import CatalogAgent, AgentConfig

# Initialize the agent
config = AgentConfig(
    openai_api_key="your_openai_api_key",
    supabase_functions_url="your_supabase_functions_url",
    gpt_actions_api_key="your_gpt_actions_api_key"
)

agent = CatalogAgent(config)

# Chat with the agent
response = agent.chat("I need a red dress for a wedding")
print(response.message)

# Access product results
if response.products:
    for product in response.products:
        print(f"- {product.title}: {product.url}")
```

### Environment Variables

Set the following environment variables:

```bash
export OPENAI_API_KEY="your_openai_api_key"
export SUPABASE_FUNCTIONS_URL="your_supabase_functions_url"
export GPT_ACTIONS_API_KEY="your_gpt_actions_api_key"
```

Or create a `.env` file:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_FUNCTIONS_URL=your_supabase_functions_url_here
GPT_ACTIONS_API_KEY=your_gpt_actions_api_key_here
```

## Configuration

### Agent Configuration

```python
from catalog_agent import AgentConfig

config = AgentConfig(
    openai_api_key="your_key",           # Required
    supabase_functions_url="your_url",   # Required
    gpt_actions_api_key="your_key",      # Required
    model="gpt-4o-mini",                 # Optional, default: "gpt-4"
    temperature=0.1,                     # Optional, default: 0.1
    max_tokens=2000,                     # Optional, default: 2000
    config_path="config",                # Optional, default: "config"
    session_id="user_123",               # Optional
    debug=False,                         # Optional, default: False
    max_iterations=3,                    # Optional, default: 3
    max_execution_time=30,               # Optional, default: 30
    early_stopping_method="generate",    # Optional, default: "generate"
    log_level="INFO",                    # Optional, default: "INFO"
    enable_agent_verbose=False           # Optional, default: None
)
```

### Performance & Configuration

#### Model Selection

For optimal performance and cost, we recommend:

- **gpt-4o-mini**: Best balance of cost, speed, and capability (~90% cheaper than GPT-4)
- **gpt-3.5-turbo**: Lowest cost, good for simple queries
- **gpt-4-turbo**: Higher cost but better for complex reasoning

#### Agent Execution Limits

Control agent behavior with these settings:

- `max_iterations=3`: Limits reasoning loops (prevents infinite loops)
- `max_execution_time=30`: Timeout in seconds (prevents runaway execution)
- `early_stopping_method="generate"`: Returns best available response when hitting limits

#### Logging Configuration

- `log_level="INFO"`: Production logging (shows important events)
- `log_level="DEBUG"`: Development logging (shows all internal processing)
- `enable_agent_verbose=False`: Suppresses LangChain's step-by-step reasoning
- `enable_agent_verbose=True`: Shows tool calls and agent decision-making

#### Environment Variables

Set these in your `.env` file:

```bash
# Model Configuration
OPENAI_MODEL=gpt-4o-mini

# Agent Execution Limits
MAX_AGENT_ITERATIONS=3
MAX_EXECUTION_TIME=30
EARLY_STOPPING_METHOD=generate

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_AGENT_VERBOSE=false
```

## Execution Modes

The agent supports two execution modes:

### Direct Mode (Default, Recommended)

Fast, predictable, and cost-effective for product discovery:

```python
config = AgentConfig(
    # ... other config
    use_direct_mode=True,           # Default
    use_llm_formatting=False        # Optional natural language formatting
)
```

**Characteristics:**
- Token usage: < 2K tokens per request
- Response time: < 500ms
- Cost: ~$0.001 per request with gpt-4o-mini
- Behavior: Deterministic tool calling based on intent

**Best for:** Product search, filtering, recommendations

### AgentExecutor Mode

LangChain agentic reasoning for complex scenarios:

```python
config = AgentConfig(
    # ... other config
    use_direct_mode=False,
    max_iterations=3,
    max_execution_time=30,
    enable_agent_verbose=False
)
```

**Characteristics:**
- Token usage: 5K-10K tokens per request (with limits)
- Response time: 2-5 seconds
- Cost: ~$0.01-0.02 per request with gpt-4o-mini
- Behavior: Agent decides which tools to use and can loop

**Best for:** Future features like emotion detection, complex multi-step reasoning

### Environment Variables

```bash
# Execution Mode
USE_DIRECT_MODE=true              # Use direct mode (recommended)

# Direct Mode Options
USE_LLM_FORMATTING=false          # Natural language formatting

# AgentExecutor Mode Options (when USE_DIRECT_MODE=false)
MAX_AGENT_ITERATIONS=3
MAX_EXECUTION_TIME=30
ENABLE_AGENT_VERBOSE=false
```

### Configuration Files

The agent uses configuration files in the `config/` directory:

- `instructions.yaml`: Agent instructions and prompts
- `actions.yaml`: Available actions and tools
- `intent-synonyms.json`: Intent detection synonyms
- `DiscoverProducts.json`: Product discovery configuration
- `tool-playbook.md`: Tool usage guidelines

## Advanced Usage

### Multi-User Chatbot Integration

```python
class MyChatbot:
    def __init__(self):
        self.agent = CatalogAgent(config)
        self.user_sessions = {}
    
    def process_message(self, user_id, message):
        session_id = self.user_sessions.get(user_id, f"user_{user_id}")
        response = self.agent.chat(message, session_id)
        return response
    
    def update_preferences(self, user_id, preferences):
        session_id = self.user_sessions.get(user_id)
        if session_id:
            self.agent.update_user_preferences(preferences, session_id)
```

### User Preferences

```python
# Update user preferences
agent.update_user_preferences({
    "sizes": ["M", "L"],
    "colors": ["red", "blue"],
    "brands": ["Nike", "Adidas"],
    "occasions": ["casual", "formal"]
}, session_id)

# Get conversation context
context = agent.get_conversation_context(session_id)
print(f"User preferences: {context.user_preferences}")
```

### Session Management

```python
# Reset conversation
agent.reset_conversation(session_id)

# Get conversation context
context = agent.get_conversation_context(session_id)

# Check agent health
is_healthy = agent.health_check()
```

## Examples

### Interactive Chat

Run the interactive chat example:

```bash
python examples/simple_chat.py
```

### Chatbot Integration

See the chatbot integration example:

```bash
python examples/chatbot_integration.py
```

## Testing

### Smoke Test

Run the complete smoke test:

```bash
python tests/smoke_test.py
```

### Intent Service Test

Test intent detection in isolation:

```bash
python tests/intent_smoke.py
```

### Configuration Health Check

Validate configuration files:

```bash
python tests/config_health.py
```

## API Reference

### CatalogAgent

Main agent class for product discovery and recommendations.

#### Methods

- `chat(message: str, session_id: Optional[str] = None) -> AgentResponse`
- `stream_chat(message: str, session_id: Optional[str] = None) -> Iterator[str]`
- `reset_conversation(session_id: Optional[str] = None) -> None`
- `get_conversation_context(session_id: Optional[str] = None) -> Optional[ConversationContext]`
- `update_user_preferences(preferences: Dict[str, Any], session_id: Optional[str] = None) -> None`
- `health_check() -> bool`

### AgentResponse

Response from the agent containing message, products, and metadata.

#### Fields

- `message: str` - Response message
- `products: Optional[List[ProductResult]]` - Found products
- `metadata: Optional[Dict[str, Any]]` - Response metadata
- `success: bool` - Whether the response was successful

### ProductResult

Product information from search results.

#### Fields

- `handle: str` - Product handle
- `title: str` - Product title
- `url: str` - Product URL
- `image_url: Optional[str]` - Product image URL
- `score: Optional[float]` - Search relevance score
- `boosted: Optional[bool]` - Whether product is boosted

## Development

### Setup Development Environment

```bash
git clone https://github.com/komatadi/catalog-agent.git
cd catalog-agent
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/smoke_test.py

# Run with coverage
pytest --cov=catalog_agent
```

### Code Quality

```bash
# Format code
black catalog_agent/

# Lint code
ruff catalog_agent/

# Type checking
mypy catalog_agent/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the examples in the `examples/` directory
- Review the test files for usage patterns

## Changelog

### 0.1.4

- Added Dual Mode Architecture: Direct Mode (default) and AgentExecutor Mode
- Direct Mode: 95% cost reduction, < 2K tokens, < 500ms response time
- Fixed bug: max_iterations=0 now works correctly in AgentExecutor mode
- Fixed bug: Verbose logging properly suppressed when disabled
- Added USE_DIRECT_MODE and USE_LLM_FORMATTING configuration options
- Enhanced config health check to validate environment variables
- Updated documentation with execution mode comparison and best practices
- AgentExecutor mode preserved for future complex reasoning features

### 0.1.3

- Added configurable agent execution limits (max_iterations, max_execution_time, early_stopping_method)
- Added structured logging with configurable log levels (LOG_LEVEL)
- Added ENABLE_AGENT_VERBOSE flag for controlling LangChain's internal logging
- Optimized system prompt to reduce token usage (~70% reduction)
- Added support for production-grade logging control
- Performance improvements and token budget management
- Recommended model: gpt-4o-mini or gpt-3.5-turbo for cost/speed optimization
- Fixed token overflow issue causing rate limit errors with GPT-4

### 0.1.2

- **BREAKING**: Relaxed Pydantic dependency constraints for better compatibility
- Changed `pydantic==2.9.2` to `pydantic>=2.9.2,<3.0.0`
- Changed `pydantic-settings==2.6.1` to `pydantic-settings>=2.6.1,<3.0.0`
- Resolves dependency conflicts with `openai-chatkit` and `openai-agents` packages
- Maintains backward compatibility with Pydantic 2.9.2+
- All existing functionality preserved with improved package compatibility

### 0.1.1

- Bug fixes and improvements
- Enhanced error handling
- Better session management

### 0.1.0

- Initial release
- Basic agent functionality
- Intent detection and synonym matching
- Product search and filtering
- Multi-session conversation management
- User preference tracking
- Comprehensive examples and tests
