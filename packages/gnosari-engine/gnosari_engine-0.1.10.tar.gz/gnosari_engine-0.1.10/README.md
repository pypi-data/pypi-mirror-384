<div align="center">
  <img src="docs/static/img/logo.png" alt="Gnosari Logo" width="200">
  
  # Gnosari AI Workforce
  
  📚 **[Documentation](https://docs.gnosari.com)**
</div>

**Gnosari AI Workforce** is a powerful framework for orchestrating multi-agent teams using Large Language Models. Create intelligent AI agent swarms that collaborate through streaming delegation and dynamic tool discovery.

## What is Gnosari AI Workforce?

Gnosari AI Workforce enables you to build sophisticated multi-agent systems where AI agents can:

- 🤝 **Delegate tasks** to specialized agents in real-time
- 🔧 **Discover and use tools** dynamically through MCP servers
- 📚 **Query knowledge bases** for context-aware responses
- 🌐 **Make API calls** to external services
- 🗄️ **Query databases** for data-driven decisions
- 📊 **Stream responses** for real-time collaboration

## Key Features

### Multi-Provider LLM Support
Each agent can use different models from various providers:
- OpenAI (GPT-4, GPT-4o, etc.)
- Anthropic (Claude)
- DeepSeek
- Google (Gemini)
- And more...

### Task Delegation & Handoffs
Agents can both delegate tasks and transfer control with configurable instructions:
- **Delegation**: Use the delegate_agent tool to send tasks to other agents and get their responses
- **Handoffs**: Transfer control to other agents when they should take over the conversation
- **Configurable Instructions**: Specify exactly when and how agents should delegate or transfer control
- **Auto-Tool Injection**: The delegate_agent tool is automatically added when delegation is configured

### Agent Personality Traits
Give your agents unique personalities with the comprehensive traits system:
- **Personality Traits**: Configure traits like "funny", "serious", "analytical", "helpful", and more
- **Weight-Based Control**: Fine-tune trait intensity with weight values (0.0 to 2.0)
- **Natural Expression**: Traits flow naturally through agent responses without forcing behavior
- **Conflict Detection**: Automatic warnings for conflicting trait combinations
- **Rich Prompts**: Trait instructions are dynamically integrated into agent system prompts

### Tool Integration
- Built-in tools (delegate_agent, api_request, knowledge_query, mysql_query, website_content, file_operations)
- MCP (Model Context Protocol) server integration
- Dynamic tool discovery

### Knowledge Bases
Embedchain integration for RAG capabilities with support for:
- Websites
- YouTube videos
- Documents
- And more...

## Quick Start

### Prerequisites
- **Python 3.12+** installed on your system
- **Poetry** for dependency management
- **API Keys** for the LLM providers you want to use

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/neomanex/gnosari-engine.git
cd gnosari-engine
```

2. **Install Dependencies**
```bash
poetry install
```

3. **Set Up Environment Variables**
Create a `.env` file in the project root:
```bash
# OpenAI (required for most examples)
OPENAI_API_KEY=your-openai-api-key

# Optional: Other providers
ANTHROPIC_API_KEY=your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key
```

### Your First Team

Create a file called `my-first-team.yaml`:

```yaml
name: My First Team

# Define tools for the team
tools:
  - name: delegate_agent
    module: gnosari.tools.delegate_agent
    class: DelegateAgentTool
    args:
      pass

# Define agents
agents:
  - name: Coordinator
    instructions: >
      You are a helpful coordinator who manages tasks and delegates work to specialists.
      When you receive a request, analyze it and delegate to the appropriate specialist.
      Always provide a summary of the work completed.
    orchestrator: true
    model: gpt-4o
    tools:
      - delegate_agent

  - name: Writer
    instructions: >
      You are a professional writer who creates clear, engaging content.
      When given a writing task, focus on clarity, structure, and engaging the reader.
      Always ask for clarification if the requirements are unclear.
    model: gpt-4o

  - name: Researcher
    instructions: >
      You are a thorough researcher who gathers and analyzes information.
      When given a research task, provide comprehensive, well-sourced information.
      Always cite your sources and note any limitations in the information.
    model: gpt-4o
```

### Run Your Team

```bash
# Run entire team
poetry run gnosari --config "my-first-team.yaml" --message "Write a blog post about the benefits of renewable energy"

# Run specific agent
poetry run gnosari --config "my-first-team.yaml" --message "Research renewable energy trends" --agent "Researcher"

# With streaming output
poetry run gnosari --config "my-first-team.yaml" --message "Your message" --stream

# With debug mode
poetry run gnosari --config "my-first-team.yaml" --message "Your message" --debug
```

## Advanced Configuration

### Session Configuration

Gnosari supports persistent conversation memory through a custom `GnosariContextSession` implementation that extends the OpenAI Agents SDK session functionality. This custom implementation provides enhanced context storage, multi-backend support, and API integration capabilities. Configure session persistence using environment variables:

#### Environment Variables

- **`SESSION_PROVIDER`**: Session storage provider (default: `file`)
  - `file`: SQLite file-based storage (suitable for development and single-instance deployments)
  - `database`: External database storage (suitable for production and multi-instance deployments)  
  - `gnosari_api`: API-based distributed storage (suitable for distributed deployments)

- **`SESSION_DATABASE_URL`**: Database connection URL (required for `database` provider)
- **`GNOSARI_API_BASE_URL`**: Base URL for API provider (required for `gnosari_api`)
- **`GNOSARI_API_KEY`**: Authentication key for API provider (required for `gnosari_api`)

#### File-Based Sessions (Default)

For development and simple deployments, sessions are stored in local SQLite files:

```bash
# Optional: Specify custom SQLite file location
export SESSION_PROVIDER=file
export SESSION_DATABASE_URL=sqlite+aiosqlite:///my_conversations.db

# Run your team with session persistence
poetry run gnosari --config "team.yaml" --message "Hello" --session-id "user-123"
```

**Supported SQLite URLs:**
- `sqlite+aiosqlite:///conversations.db` (relative path)
- `sqlite+aiosqlite:////absolute/path/to/conversations.db` (absolute path)
- `sqlite+aiosqlite:///:memory:` (in-memory database)

#### Database-Based Sessions

For production deployments with multiple instances, use external databases:

```bash
# PostgreSQL (Recommended for production)
export SESSION_PROVIDER=database
export SESSION_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/gnosari_sessions

# MySQL/MariaDB
export SESSION_PROVIDER=database
export SESSION_DATABASE_URL=mysql+aiomysql://username:password@localhost:3306/gnosari_sessions

# Run your team with persistent sessions
poetry run gnosari --config "team.yaml" --message "Hello" --session-id "user-123"
```

**Supported Database URLs:**

| Database | URL Format | Notes |
|----------|------------|-------|
| **PostgreSQL** | `postgresql+asyncpg://user:pass@host:port/db` | Recommended for production |
| **MySQL** | `mysql+aiomysql://user:pass@host:port/db` | Good alternative for production |
| **SQLite** | `sqlite+aiosqlite:///path/to/file.db` | Development and single-instance |

#### API-Based Sessions

For distributed deployments, sessions can be stored via the Gnosari API backend:

```bash
# API-based sessions (distributed storage)
export SESSION_PROVIDER=gnosari_api
export GNOSARI_API_BASE_URL=http://localhost:8001
export GNOSARI_API_KEY=your-api-key-here

# Run your team with API-backed persistent sessions
poetry run gnosari --config "team.yaml" --message "Hello" --session-id "user-123"
```

**API Session Features:**
- **Distributed**: Multiple engine instances share session storage
- **Context Aware**: Automatically stores account, team, and agent context
- **REST API**: Uses standard HTTP REST API for session operations  
- **Authentication**: Secured with API key authentication
- **Fallback Ready**: Can fall back to local storage if API is unavailable

#### Database Setup

For external databases, ensure the session tables exist before running:

1. **Create the database** (if it doesn't exist)
2. **Run migrations** using your database migration tool, or
3. **Create tables manually**:

```sql
-- PostgreSQL/MySQL
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE agent_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_agent_messages_session_time ON agent_messages(session_id, created_at);
```

#### Session Usage

Sessions enable conversation continuity across multiple interactions:

```bash
# First conversation
poetry run gnosari --config "team.yaml" --message "My name is Alice" --session-id "user-123"

# Later conversation (remembers previous context)  
poetry run gnosari --config "team.yaml" --message "What's my name?" --session-id "user-123"
```

### Delegation and Handoff Instructions

Configure specific delegation and handoff behavior with detailed instructions:

```yaml
name: Advanced Coordination Team

# The delegate_agent tool is automatically added when delegation is configured
tools:
  - name: delegate_agent
    module: gnosari.tools.delegate_agent
    class: DelegateAgentTool
    args:
      pass

agents:
  - name: Coordinator
    instructions: >
      You are a coordinator who manages conversations and tasks with multiple specialized agents.
      You have two main mechanisms for working with other agents:
      1. DELEGATION: Use the delegate_agent tool to send tasks to other agents and get their responses
      2. HANDOFFS: Transfer control to other agents when they should take over the conversation
    orchestrator: true
    model: gpt-4o
    # Configure which agents to delegate to and when
    delegation:
      - agent: Alice
        instructions: Delegate to Alice for questions about fruits, especially apples, or when detailed fruit knowledge is needed
      - agent: Bob
        instructions: Delegate to Bob for general questions, math problems, or when Alice cannot help
    # Configure which agents to transfer control to and when
    can_transfer_to: 
      - agent: Alice
        instructions: Transfer to Alice when the user wants to have an ongoing conversation about fruits or gardening
      - agent: Bob
        instructions: Transfer to Bob for complex problem-solving sessions or when extended technical discussion is needed
    # Note: delegate_agent tool is automatically added due to delegation configuration
    # tools:
    #   - delegate_agent

  - name: Alice
    model: gpt-4o
    instructions: >
      You are Alice, a fruit specialist with deep knowledge about apples, orchards, and fruit cultivation.
      Provide detailed, accurate information about fruits and respond helpfully to questions in your domain.
    can_transfer_to:
      - agent: Bob
        instructions: Transfer to Bob if asked about topics outside fruit/gardening expertise
      - agent: Coordinator
        instructions: Transfer back to Coordinator when the conversation should be coordinated with multiple agents

  - name: Bob
    model: gpt-4o
    instructions: >
      You are Bob, a general-purpose assistant skilled in mathematics, problem-solving, and general knowledge.
      Provide clear, accurate responses and help with a wide range of topics.
    can_transfer_to:
      - agent: Alice
        instructions: Transfer to Alice for any fruit, apple, or gardening related questions
      - agent: Coordinator
        instructions: Transfer back to Coordinator when complex multi-agent coordination is needed
```

### Team with Agent Personality Traits

Create agents with unique personalities using the traits system:

```yaml
name: Personality-Enhanced Team

tools:
  - name: delegate_agent
    module: gnosari.tools.delegate_agent
    class: DelegateAgentTool
    args:
      pass

agents:
  - name: Comedy Assistant
    instructions: You are a helpful assistant that provides information and support.
    orchestrator: true
    model: gpt-4o
    temperature: 0.8
    tools: [delegate_agent]
    traits:
      - name: funny
        description: Uses humor and wit in responses
        instructions: Incorporate appropriate humor, puns, and lighthearted comments into your responses. Use emoji occasionally. Make interactions enjoyable while staying helpful.
        weight: 1.2
      - name: optimistic
        description: Maintains a positive, upbeat attitude
        instructions: Always look on the bright side of situations. Provide encouraging responses and focus on possibilities rather than limitations.

  - name: Serious Analyst
    instructions: You analyze data and provide detailed reports.
    model: gpt-4o
    temperature: 0.1
    traits:
      - name: analytical
        description: Focuses on data-driven analysis
        instructions: Approach problems methodically. Provide detailed analysis with supporting evidence. Ask clarifying questions to ensure thorough understanding.
      - name: formal
        description: Maintains professional, formal communication
        instructions: Use formal language and professional tone. Structure responses clearly with proper headings and bullet points. Avoid casual expressions and emoji.

  - name: Supportive Helper
    instructions: You provide emotional support and encouragement.
    model: gpt-4o
    temperature: 0.5
    traits:
      - name: empathetic
        description: Shows understanding and emotional support
        instructions: Demonstrate empathy and understanding. Acknowledge user feelings and provide emotional support. Use encouraging language and validate concerns.
      - name: patient
        description: Exhibits patience and understanding
        instructions: Remain calm and patient even with repetitive or difficult questions. Take time to explain concepts thoroughly. Never show frustration.
```

### Team with Knowledge Bases and Tools

```yaml
name: Advanced Content Team

# Knowledge bases (automatically adds knowledge_query tool)
knowledge:
  - name: "company_docs"
    type: "website"
    data: ["https://docs.yourcompany.com"]

# Tools configuration
tools:
  - name: delegate_agent
    module: gnosari.tools.delegate_agent
    class: DelegateAgentTool
    args:
      pass

  - name: api_request
    module: gnosari.tools.api_request
    class: APIRequestTool
    args:
      base_url: https://api.example.com
      base_headers:
        Authorization: Bearer ${API_TOKEN}
        Content-Type: application/json
      timeout: 30
      verify_ssl: true

  - name: mysql_query
    module: gnosari.tools.mysql_query
    class: MySQLQueryTool
    args:
      host: ${DB_HOST}
      port: 3306
      database: ${DB_NAME}
      username: ${DB_USER}
      password: ${DB_PASSWORD}
      pool_size: 5
      query_timeout: 30

# Agents configuration
agents:
  - name: Content Manager
    instructions: >
      You are a content manager who coordinates content creation workflows.
      You can delegate tasks to specialists and use various tools to gather information.
      Always ensure content is accurate, engaging, and meets quality standards.
    orchestrator: true
    model: gpt-4o
    tools:
      - delegate_agent
      - knowledge_query
    knowledge: ["company_docs"]

  - name: Data Analyst
    instructions: >
      You are a data analyst who works with databases and APIs to gather insights.
      Use the mysql_query tool to analyze data and the api_request tool to fetch external data.
      Always provide clear, actionable insights based on the data.
    model: gpt-4o
    tools:
      - mysql_query
      - api_request

  - name: Content Writer
    instructions: >
      You are a professional content writer who creates engaging, well-researched content.
      Use the knowledge_query tool to access company documentation and ensure accuracy.
      Focus on creating content that resonates with the target audience.
    model: gpt-4o
    tools:
      - knowledge_query
    knowledge: ["company_docs"]
```

## Built-in Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| **delegate_agent** | Delegate tasks to other agents in the team | Multi-agent coordination |
| **api_request** | Make HTTP requests to external APIs | External service integration |
| **knowledge_query** | Query knowledge bases for information | RAG and information retrieval |
| **mysql_query** | Execute SQL queries against MySQL databases | Database operations |
| **website_content** | Fetch content from websites via API | Web content retrieval |
| **file_operations** | Read, write, and manage files in a sandboxed directory | Local file management |

## Knowledge Base Support

Gnosari AI Workforce supports various knowledge sources through Embedchain:

- **Websites**: Crawl and index content from websites
- **YouTube**: Extract and index content from YouTube videos
- **Documents**: Process PDF, text, CSV, and JSON files
- **Direct Text**: Q&A content and structured information

## CLI Options

```bash
# Basic team execution
poetry run gnosari --config "team.yaml" --message "Your message"

# Run specific agent from team
poetry run gnosari --config "team.yaml" --message "Your message" --agent "AgentName"

# With streaming output
poetry run gnosari --config "team.yaml" --message "Your message" --stream

# With debug mode
poetry run gnosari --config "team.yaml" --message "Your message" --debug

# With custom model and temperature
poetry run gnosari --config "team.yaml" --message "Your message" --model "gpt-4o" --temperature 0.7

# View generated system prompts (useful for debugging and understanding agent behavior)
poetry run gnosari --config "team.yaml" --show-prompts

# View prompts with specific model/temperature settings
poetry run gnosari --config "team.yaml" --show-prompts --model "gpt-4o" --temperature 0.5

# Prompt Template Management
poetry run gnosari prompts list                              # List available templates
poetry run gnosari prompts view planning                     # View template with rich formatting
poetry run gnosari prompts view planning --format markdown   # View as plain markdown
poetry run gnosari prompts view planning variables           # Show only variables
poetry run gnosari prompts use planning "Create feature" --feature_name "search"  # Process template
poetry run gnosari prompts create planning "./plan.md" "New feature" --var "value"  # Create file from template
```

## Architecture

### Core Components
- **Team Builder**: Builds teams from YAML configs using OpenAI Agents SDK with handoffs
- **Team Runner**: Executes team workflows using OpenAI Agents SDK Runner with streaming support
- **Agent System**: Uses OpenAI's official Agents SDK with native handoff support
- **Tool Integration**: Native OpenAI tool calling with MCP server integration
- **Knowledge Bases**: Embedchain integration for RAG capabilities

### Key Directories
- **`src/gnosari/`**: Main source code
  - **`agents/`**: Agent implementations  
  - **`engine/`**: Team orchestration and execution
  - **`tools/`**: Built-in tools (delegation, API requests, etc.)
  - **`prompts/`**: Prompt engineering utilities
  - **`schemas/`**: Pydantic schemas and base classes
  - **`utils/`**: LLM client, tool manager, knowledge manager
- **`examples/`**: Team configuration examples
- **`tests/`**: Test files
- **`docs/`**: Documentation

## Development

### Testing
```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_specific.py

# Run tests with coverage
poetry run pytest --cov=gnosari
```

### Alternative Execution
If experiencing pyenv shim issues, use the wrapper script:
```bash
./scripts/run-gnosari team run --config "examples/team.yaml" --message "Your message"
```

## Documentation

For comprehensive documentation, visit the [docs folder](docs/) which includes:

- [Quickstart Guide](docs/docs/quickstart.md) - Get up and running in minutes
- [Agents](docs/docs/agents.md) - Learn about agent configuration and capabilities
- [Teams](docs/docs/teams.md) - Understand team structure and coordination
- [Orchestration](docs/docs/orchestration.md) - Learn about agent coordination and workflow management
- [Knowledge Bases](docs/docs/knowledge.md) - Set up knowledge bases for RAG capabilities
- [Tools Overview](docs/docs/tools/intro.md) - Learn about built-in tools and how to use them

## Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit issues and pull requests.

## License

This project is licensed under the Creative Commons Attribution 4.0 International License - see the LICENSE file for details.

**You are free to:**
- Share and redistribute the code
- Modify and adapt the code  
- Use the code for any purpose, including commercial purposes
- Use the code in commercial products or services

**You must:**
- Provide proper attribution when using the code
- Indicate any changes made
- Link to the license

---

Ready to build your first AI workforce? Start with the [Quickstart Guide](docs/docs/quickstart.md) and create intelligent multi-agent teams that can tackle complex tasks through collaboration and specialization! 🚀