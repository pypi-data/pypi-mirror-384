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
    model="gpt-4",                       # Optional, default: "gpt-4"
    temperature=0.1,                     # Optional, default: 0.1
    max_tokens=2000,                     # Optional, default: 2000
    config_path="config",                # Optional, default: "config"
    session_id="user_123",               # Optional
    debug=False                          # Optional, default: False
)
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

### 0.1.0

- Initial release
- Basic agent functionality
- Intent detection and synonym matching
- Product search and filtering
- Multi-session conversation management
- User preference tracking
- Comprehensive examples and tests
