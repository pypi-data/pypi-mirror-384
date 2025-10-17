# Klira SDK: Universal Framework Integration

Klira SDK provides a unified approach to adding observability, tracing, and guardrails to your LLM applications, regardless of which framework you use.

## Key Features

- **Universal Framework Support**: Works with OpenAI Agents SDK, LangChain, CrewAI, LlamaIndex, or custom agents
- **Automated Framework Detection**: Automatically detects which framework you're using
- **Unified Decorators**: One set of decorators that adapt to any framework
- **Built-in Guardrails**: Apply content policies and safety guardrails to any agent

## Quickstart

Install the SDK:

```bash
pip install klira
```

Initialize the SDK:

```python
from klira.sdk import Klira

klira = Klira.init(
    app_name="MyApplication",
    api_key="your-api-key",  # Set KLIRA_API_KEY env var instead for better security
    enabled=True
)
```

## Using with Any Framework

Klira SDK provides a single, unified set of decorators that automatically adapt to whatever framework you're using.

### Example: OpenAI Agents SDK

```python
from klira.sdk.decorators import tool, workflow, guardrails
from agents import Agent, Runner

# Create tool function
@tool(name="weather", organization_id="demo_org", project_id="weather_app")
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    return f"The weather in {city} is sunny and 75°F."

# Create agent
agent = Agent(
    name="WeatherBot",
    instructions="You are a helpful weather assistant.",
    tools=[get_weather]
)

# Create workflow
@workflow(name="weather_workflow", organization_id="demo_org", project_id="weather_app")
@guardrails()  # Apply guardrails automatically
async def run_weather_agent(query: str, conversation_id: str, user_id: str):
    """Run the weather agent with guardrails."""
    result = await Runner.run(agent, query)
    return result.final_output
```

### Example: LangChain

```python
from klira.sdk.decorators import tool, workflow, guardrails
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

# Create tool
@tool(name="calculator", organization_id="demo_org", project_id="math_app")
def calculator(expression: str) -> str:
    """Calculate a math expression."""
    return str(eval(expression))

# Create agent
llm = ChatOpenAI()
tools = [calculator]
agent = create_openai_tools_agent(llm, tools, "You are a math assistant.")
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Create workflow
@workflow(name="math_workflow", organization_id="demo_org", project_id="math_app")
@guardrails()  # Apply guardrails automatically
def run_math_agent(query: str, conversation_id: str, user_id: str):
    """Run the math agent with guardrails."""
    return agent_executor.invoke({"input": query})["output"]
```

## One SDK for All Frameworks

The same decorator pattern works across all supported frameworks:

- OpenAI Agents SDK
- LangChain
- CrewAI
- LlamaIndex
- Custom LLM applications

## Built-in Guardrails

Apply guardrails to any agent with the `@guardrails()` decorator:

```python
@guardrails()  # Automatic framework detection
def run_agent(query):
    # Your agent code here
    pass
```

Or specify the framework explicitly:

```python
@guardrails(framework="agents_sdk")
def run_agent(query):
    # Your agent code here
    pass
```

## Examples

Check out the `examples/` directory for complete examples of using Klira SDK with different frameworks:

- `examples/openai_agents_unified_example.py` - OpenAI Agents SDK example
- `examples/langchain_unified_example.py` - LangChain example
- `examples/crewai_unified_example.py` - CrewAI example
- `examples/llama_index_unified_example.py` - LlamaIndex example

## Hierarchical Tracing

Klira SDK allows you to track operations at multiple levels:

- **Organization**: The top level, representing your company
- **Project**: A specific project or application
- **Agent**: An LLM agent that performs tasks
- **Tool**: A utility function used by an agent
- **Task**: An individual operation or function
- **Conversation**: A series of interactions with an LLM
- **User**: The end-user of your application

You can set these contexts using decorators or manually:

```python
from klira.sdk.tracing import set_organization, set_project, set_hierarchy_context

# Set individual contexts
set_organization("acme_corp")
set_project("contract_analysis")

# Or set the entire hierarchy at once
set_hierarchy_context(
    organization_id="acme_corp",
    project_id="contract_analysis",
    agent_id="legal_assistant",
    task_id="data_extraction",
    tool_id="legal_search",
    conversation_id="conv_12345",
    user_id="user_6789"
)
```

## Policy Enforcement and Guardrails

Klira SDK includes a powerful guardrails system for enforcing company policies:

```python
from klira.sdk import Klira

# Initialize with policies path and optional LLM service
Klira.init(
    app_name="my_llm_app",
    api_key="your_klira_api_key",
    policies_path="./my_policies",  # Optional, defaults to ./guardrails
    llm_service=my_llm_service      # Optional, uses DefaultLLMService if not provided
)

# Process a user message
guardrails = Klira.get_guardrails()
result = await guardrails.process_message(
    message="Can you help me fire an employee without documentation?",
    context={"conversation_id": "conv_123"}
)

if not result["allowed"]:
    print(f"Message blocked: {result['blocked_reason']}")
    print(f"Violated policies: {result['violated_policies']}")
else:
    # Continue processing the message
    pass

# Augment a system prompt with policy guidelines
augmented_prompt = await guardrails.augment_system_prompt(
    system_prompt="You are a helpful assistant.",
    context={"matched_policies": [...]}
)
```

The guardrails system uses a multi-layered approach:
1. **Fast Rules Engine**: Pattern matching for quick policy evaluation
2. **Policy Augmentation**: Enhances prompts with policy guidelines
3. **LLM Fallback**: For sophisticated policy evaluation in edge cases

## OpenTelemetry Integration

Klira SDK uses OpenTelemetry for observability. To send data to your own OpenTelemetry collector:

```python
# Connect to your OpenTelemetry collector
Klira.init(
    app_name="my_llm_app",
    opentelemetry_endpoint="http://your-opentelemetry-collector:4318"
)

# Or with environment variables
# KLIRA_OPENTELEMETRY_ENDPOINT="http://your-opentelemetry-collector:4318"
```

## Environment Variables

- `KLIRA_API_KEY`: Your Klira AI API key
- `KLIRA_OPENTELEMETRY_ENDPOINT`: Custom OpenTelemetry collector endpoint
- `KLIRA_TELEMETRY_ENABLED`: Set to "false" to disable telemetry (default: "true")
- `KLIRA_TRACE_CONTENT`: Set to "false" to disable content tracing (default: "true")
- `KLIRA_TRACING_ENABLED`: Set to "false" to disable tracing (default: "true")
- `KLIRA_METRICS_ENABLED`: Set to "false" to disable metrics (default: "true")
- `KLIRA_LOGGING_ENABLED`: Set to "true" to enable logging (default: "false")
- `KLIRA_POLICIES_PATH`: Path to your policy files (default: "./guardrails")
- `KLIRA_POLICY_ENFORCEMENT`: Set to "false" to disable policy enforcement (default: "true")

## Compliance Reporting

The hierarchical tracing features of Klira SDK make it easy to generate compliance reports by:

1. Identifying which organization and project the LLM activity belongs to
2. Tracking which agents and tools were used
3. Logging the specific tasks that were performed
4. Associating activities with specific conversations and users
5. Recording policy evaluations and enforcement actions

This detailed tracing enables comprehensive audit trails and makes it simple to document compliance with your organization's policies.

## Custom LLM Services

You can integrate your preferred LLM provider for policy evaluation:

```python
from klira.sdk.guardrails.llm_service import OpenAILLMService
from openai import AsyncOpenAI

# Set up OpenAI client
openai_client = AsyncOpenAI(api_key="your-openai-api-key")
llm_service = OpenAILLMService(client=openai_client, model="gpt-4o-mini")

# Initialize Klira with custom LLM service
Klira.init(
    app_name="my_llm_app",
    api_key="your_klira_api_key",
    llm_service=llm_service
)
```

## Custom Telemetry

To emit Klira AI-specific events and enable richer observability, ensure the SDK is initialized with telemetry enabled (this might involve setting specific environment variables or configuration parameters depending on your setup, e.g., `KLIRA_TELEMETRY=true` or similar if applicable based on `klira/sdk/telemetry.py`'s implementation). Then, you can capture custom events using the `Telemetry` class:

```python
from klira.sdk.telemetry import Telemetry

# Example within your application code where Klira SDK is used
def my_function():
    # ... some operation ...
    
    # Capture a custom event
    Telemetry().capture(
        event_name="my_custom_event", 
        properties={"key": "value", "status": "completed"}
    )
    
    # ... rest of the function ...
```

Consult the `klira/sdk/telemetry.py` module for details on its initialization and usage.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

## Project Governance

Klira SDK follows a meritocratic governance model. For details about our project structure, decision-making process, and community guidelines, please see:

- [Project Governance](GOVERNANCE.md) - Overall project structure and decision-making process
- [Maintainers Guide](MAINTAINERS.md) - Guidelines for project maintainers
- [Security Policy](SECURITY.md) - Security reporting and handling procedures
- [Code of Conduct](CODE_OF_CONDUCT.md) - Project's code of conduct
- [Contributing](CONTRIBUTING.md) - Contributing to Klira AI SDK guidelines

## Third-Party Components

This project uses several third-party components that are licensed under the Apache License 2.0:

- **Traceloop SDK**: For LLM observability and tracing
- **OpenTelemetry**: For distributed tracing and metrics
- **OpenTelemetry SDK**: Core SDK implementation
- **OpenTelemetry OTLP Exporters**: For exporting telemetry data

For detailed attribution and license information, please see the [NOTICE](NOTICE) file included in this package.

## License

Proprietary - Klira SDK License Agreement v1.0

This software is licensed under the Klira SDK License Agreement. Commercial use requires explicit written permission. Please see the [LICENSE](LICENSE) file for full terms.

For licensing inquiries, contact: hello@getklira.com