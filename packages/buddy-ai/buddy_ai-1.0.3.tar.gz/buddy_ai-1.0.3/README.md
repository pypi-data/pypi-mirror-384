# 🤖 Buddy AI Framework

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![PyPI version](https://img.shields.io/badge/PyPI-buddy--ai-blue.svg)](https://pypi.org/project/buddy-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/esasrir91/buddy-ai)

**Production-ready Python framework for building intelligent AI agents with enterprise-grade capabilities**

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-comprehensive-documentation) • [💻 Examples](#-examples) • [🔧 API Reference](#-api-reference) • [🤝 Contributing](#-contributing)

</div>

---

## 🌟 **What is Buddy AI?**

**Buddy AI** is a comprehensive Python framework that empowers developers to build, deploy, and scale intelligent AI agents. Whether you're creating chatbots, automation tools, or complex multi-agent systems, Buddy AI provides the infrastructure and tools you need.

### **Why Choose Buddy AI?**

✅ **Multi-Model Support** - Works with 25+ AI providers (OpenAI, Anthropic, Google, AWS, Azure, etc.)  
✅ **Rich Tool Ecosystem** - 50+ built-in tools for real-world tasks  
✅ **Knowledge Management** - Advanced RAG with vector databases  
✅ **Memory & Context** - Persistent conversations across sessions  
✅ **Team Workflows** - Multi-agent collaboration and orchestration  
✅ **Production Ready** - Enterprise features, monitoring, and deployment options  
✅ **Easy Integration** - FastAPI, CLI, Slack, Discord, and more  

---

## 🚀 **Quick Start**

### **Installation**

```bash
# Install the core framework
pip install buddy-ai

# Install with all providers and tools
pip install buddy-ai[all]

# Install specific providers
pip install buddy-ai[openai,anthropic,google]
```

### **Your First Agent in 30 Seconds**

```python
from buddy import Agent
from buddy.models.openai import OpenAIChat

# Create an intelligent agent
agent = Agent(
    name="Assistant",
    model=OpenAIChat(id="gpt-4"),
    instructions="You are a helpful AI assistant."
)

# Start chatting
response = agent.run("Hello! What can you help me with?")
print(response.content)
```

### **Agent with Tools**

```python
from buddy import Agent
from buddy.models.openai import OpenAIChat
from buddy.tools.calculator import CalculatorTools
from buddy.tools.python import PythonTools

agent = Agent(
    name="DataAnalyst", 
    model=OpenAIChat(id="gpt-4"),
    tools=[CalculatorTools(), PythonTools()],
    instructions="You are a data analyst who can perform calculations and write Python code.",
    show_tool_calls=True
)

# The agent can now use tools
response = agent.run("Calculate the compound interest for $10,000 at 5% annually for 3 years, then create a Python visualization of the growth")
```

---

## 🏗️ **Core Concepts**

### **1. Agents**
Agents are the core building blocks - intelligent entities that can reason, use tools, and maintain context.

### **2. Models** 
LLM providers that power your agents. Support for OpenAI, Anthropic, Google, and many more.

### **3. Tools**
Functions that agents can call to interact with the world - from simple calculations to complex API integrations.

### **4. Knowledge**
Information sources that agents can search and reference using RAG (Retrieval-Augmented Generation).

### **5. Memory**
Persistent storage for conversations, user preferences, and learned information.

### **6. Teams**
Collections of specialized agents working together on complex tasks.

### **7. Training**
Built-in model training capabilities for fine-tuning and custom models.

### **8. Reasoning**
Advanced reasoning systems with step-by-step logic and chain-of-thought processing.

### **9. Reranking**
Intelligent result reranking for improved search and retrieval accuracy.

### **10. Workspaces**
Project management and organization tools for complex AI workflows.

### **11. Playground**
Interactive development environment for testing and experimenting with agents.

---

## 🎯 **Examples**

### **Customer Support Agent**

```python
from buddy import Agent
from buddy.models.openai import OpenAIChat
from buddy.tools.email import EmailTools
from buddy.tools.knowledge import KnowledgeTools
from buddy.memory.agent import AgentMemory

# Setup persistent memory
memory = AgentMemory(
    db_url="sqlite:///customer_support.db",
    create_user_memories=True
)

# Create specialized customer support agent
support_agent = Agent(
    name="CustomerSupport",
    model=OpenAIChat(id="gpt-4"),
    tools=[EmailTools(), KnowledgeTools()],
    memory=memory,
    instructions="""
    You are a helpful customer support agent. Your role is to:
    - Answer customer questions clearly and professionally
    - Search the knowledge base for accurate information
    - Escalate complex issues when needed
    - Remember customer preferences and history
    """,
    show_tool_calls=True
)

# Customer conversation
response = support_agent.run(
    message="I'm having trouble with my order #12345",
    user_id="customer_789"
)
```

### **Research and Analysis Team**

```python
from buddy import Team, Agent
from buddy.models.openai import OpenAIChat
from buddy.tools.googlesearch import GoogleSearchTools
from buddy.tools.website import WebsiteTools
from buddy.tools.python import PythonTools

# Create specialized agents
researcher = Agent(
    name="WebResearcher",
    role="Research information from the web",
    model=OpenAIChat(id="gpt-4"),
    tools=[GoogleSearchTools(), WebsiteTools()],
    instructions="Search for comprehensive information and gather relevant data."
)

analyst = Agent(
    name="DataAnalyst", 
    role="Analyze data and create insights",
    model=OpenAIChat(id="gpt-4"),
    tools=[PythonTools()],
    instructions="Analyze data, create visualizations, and provide insights."
)

writer = Agent(
    name="ReportWriter",
    role="Create well-structured reports",
    model=OpenAIChat(id="gpt-4"),
    instructions="Write clear, comprehensive reports based on research and analysis."
)

# Create and run team workflow
team = Team(
    name="ResearchTeam",
    agents=[researcher, analyst, writer],
    workflow="researcher -> analyst -> writer",
    show_tool_calls=True
)

result = team.run("Research the current state of renewable energy adoption and create a comprehensive market analysis")
```

### **Knowledge-Enhanced Agent**

```python
from buddy import Agent
from buddy.models.anthropic import AnthropicChat
from buddy.knowledge.document import DocumentKnowledgeBase
from buddy.embedder.openai import OpenAIEmbedder
from buddy.vectordb.chroma import ChromaDb

# Setup knowledge base with vector storage
knowledge = DocumentKnowledgeBase(
    path="./company_docs",
    vector_db=ChromaDb(path="./vector_db"),
    embedder=OpenAIEmbedder(),
    formats=[".pdf", ".md", ".txt", ".docx"]
)
knowledge.load()

# Create knowledge-enhanced agent
knowledge_agent = Agent(
    name="CompanyExpert",
    model=AnthropicChat(id="claude-3-opus"),
    knowledge=knowledge,
    search_knowledge=True,
    instructions="""
    You are an expert on our company's policies, procedures, and documentation.
    Always search the knowledge base first before answering questions.
    Provide accurate, up-to-date information with references.
    """
)

response = knowledge_agent.run("What is our company's remote work policy?")
```

### **Structured Output Agent**

```python
from buddy import Agent
from buddy.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from typing import List, Optional

# Define structured output model
class ProductAnalysis(BaseModel):
    product_name: str = Field(description="Name of the product")
    strengths: List[str] = Field(description="Key product strengths")
    weaknesses: List[str] = Field(description="Areas for improvement")
    market_position: str = Field(description="Position in the market")
    recommendations: List[str] = Field(description="Strategic recommendations")
    confidence_score: float = Field(description="Analysis confidence (0-1)")

# Create agent with structured output
analyst_agent = Agent(
    name="ProductAnalyst",
    model=OpenAIChat(id="gpt-4"),
    response_model=ProductAnalysis,
    instructions="Analyze products thoroughly and provide structured insights."
)

# Get structured response
result = analyst_agent.run("Analyze the iPhone 15 Pro")
analysis = result.content

print(f"Product: {analysis.product_name}")
print(f"Strengths: {', '.join(analysis.strengths)}")
print(f"Confidence: {analysis.confidence_score}")
```

---

## 🎨 **Available Models**

Buddy AI supports 25+ AI model providers:

### **Tier 1 Providers**
```python
# OpenAI Models
from buddy.models.openai import OpenAIChat
model = OpenAIChat(id="gpt-4", temperature=0.7)

# Anthropic Models  
from buddy.models.anthropic import AnthropicChat
model = AnthropicChat(id="claude-3-opus", max_tokens=4000)

# Google Models
from buddy.models.google import GoogleChat
model = GoogleChat(id="gemini-pro", temperature=0.5)
```

### **Cloud Providers**
```python
# AWS Bedrock
from buddy.models.aws import AWSChat
model = AWSChat(id="anthropic.claude-3-sonnet")

# Azure OpenAI
from buddy.models.azure import AzureOpenAIChat
model = AzureOpenAIChat(id="gpt-4", deployment_name="gpt-4-deployment")

# Google Vertex AI
from buddy.models.google import VertexChat
model = VertexChat(id="gemini-pro", project="your-project")
```

### **Open Source & Alternative Providers**
```python
# Ollama (Local models)
from buddy.models.ollama import OllamaChat
model = OllamaChat(id="llama2", host="http://localhost:11434")

# Groq (Fast inference)
from buddy.models.groq import GroqChat
model = GroqChat(id="mixtral-8x7b-32768")

# Together AI
from buddy.models.together import TogetherChat
model = TogetherChat(id="meta-llama/Llama-2-70b-chat-hf")

# Hugging Face
from buddy.models.huggingface import HuggingFaceChat
model = HuggingFaceChat(id="microsoft/DialoGPT-medium")

# Additional Providers
from buddy.models.xai import XAIChat
model = XAIChat(id="grok-beta")  # X.AI Grok

from buddy.models.deepseek import DeepSeekChat  
model = DeepSeekChat(id="deepseek-coder")

from buddy.models.cerebras import CerebrasChat
model = CerebrasChat(id="llama3.1-8b")  # Ultra-fast inference

from buddy.models.perplexity import PerplexityChat
model = PerplexityChat(id="llama-3.1-sonar-large-128k-online")

from buddy.models.sambanova import SambaNovaChat
model = SambaNovaChat(id="Meta-Llama-3.1-405B-Instruct")

from buddy.models.fireworks import FireworksChat
model = FireworksChat(id="accounts/fireworks/models/llama-v3p1-405b-instruct")

from buddy.models.lmstudio import LMStudioChat
model = LMStudioChat(base_url="http://localhost:1234/v1")

from buddy.models.vllm import VLLMChat
model = VLLMChat(base_url="http://localhost:8000")

from buddy.models.litellm import LiteLLMChat
model = LiteLLMChat(id="bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
```

---

## 🛠️ **Built-in Tools**

Buddy AI comes with 50+ production-ready tools:

### **Development & Code**
```python
from buddy.tools.python import PythonTools          # Execute Python code
from buddy.tools.shell import ShellTools            # Run shell commands  
from buddy.tools.github import GithubTools          # GitHub integration
from buddy.tools.docker import DockerTools          # Docker operations
```

### **Data & Analytics**
```python
from buddy.tools.calculator import CalculatorTools  # Mathematical calculations
from buddy.tools.pandas import PandasTools          # Data manipulation
from buddy.tools.sql import SQLTools               # Database queries
from buddy.tools.csv_toolkit import CSVTools       # CSV operations
```

### **Web & Search**
```python
from buddy.tools.googlesearch import GoogleSearchTools    # Google search
from buddy.tools.website import WebsiteTools             # Web scraping
from buddy.tools.playwright_tool import PlaywrightTools  # Browser automation
from buddy.tools.serpapi import SerpApiTools             # Search engine APIs
```

### **Communication & Productivity**
```python
from buddy.tools.email import EmailTools           # Email operations
from buddy.tools.slack import SlackTools           # Slack integration
from buddy.tools.calendar import CalendarTools     # Calendar management
from buddy.tools.gmail import GmailTools           # Gmail integration
```

### **File & Storage**
```python
from buddy.tools.file import FileTools                    # File operations
from buddy.tools.local_file_system import LocalFileTools  # Local file system
from buddy.tools.s3 import S3Tools                       # AWS S3 operations
from buddy.tools.postgres import PostgresTools           # PostgreSQL
```

### **AI & Media**
```python
from buddy.tools.dalle import DalleTools                 # Image generation
from buddy.tools.eleven_labs import ElevenLabsTools      # Text-to-speech
from buddy.tools.openai import OpenAITools              # OpenAI integrations
from buddy.tools.cartesia import CartesiaTools          # Voice AI
```

### **Custom Tool Creation**

```python
from buddy.tools.function import Function
from typing import Dict, Any

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analyze the sentiment of given text."""
    # Your custom logic here
    return {"sentiment": "positive", "confidence": 0.85}

# Register as a tool
sentiment_tool = Function(
    name="analyze_sentiment",
    description="Analyze text sentiment",
    func=analyze_sentiment
)

agent = Agent(
    name="SentimentAnalyst",
    model=OpenAIChat(id="gpt-4"),
    tools=[sentiment_tool]
)
```

---

## 💾 **Knowledge Management**

### **Document Knowledge Base**

```python
from buddy.knowledge.document import DocumentKnowledgeBase
from buddy.embedder.openai import OpenAIEmbedder
from buddy.vectordb.pinecone import PineconeDb

# Vector-based knowledge
knowledge = DocumentKnowledgeBase(
    path="./documents",
    vector_db=PineconeDb(
        api_key="your-pinecone-key",
        index_name="buddy-knowledge"
    ),
    embedder=OpenAIEmbedder(),
    formats=[".pdf", ".md", ".txt", ".docx", ".pptx"]
)

# Load and process documents
knowledge.load()

agent = Agent(
    name="KnowledgeAgent",
    model=OpenAIChat(id="gpt-4"),
    knowledge=knowledge,
    search_knowledge=True
)
```

### **SQL Knowledge Base**

```python
from buddy.knowledge.sql_knowledge import SQLKnowledgeBase

# SQL-based knowledge with full-text search
sql_knowledge = SQLKnowledgeBase(
    path="./code_docs",
    db_path="./knowledge.db",
    formats=[".py", ".js", ".md", ".json"]
)

sql_knowledge.load()

agent = Agent(
    name="CodeExpert",
    model=OpenAIChat(id="gpt-4"),
    knowledge=sql_knowledge,
    search_knowledge=True
)
```

### **Supported Vector Databases**

```python
# Pinecone
from buddy.vectordb.pinecone import PineconeDb
db = PineconeDb(api_key="key", index_name="index")

# Chroma
from buddy.vectordb.chroma import ChromaDb
db = ChromaDb(path="./chroma_db")

# Weaviate
from buddy.vectordb.weaviate import WeaviateDb
db = WeaviateDb(url="http://localhost:8080")

# Qdrant
from buddy.vectordb.qdrant import QdrantDb
db = QdrantDb(host="localhost", port=6333)

# PGVector (PostgreSQL)
from buddy.vectordb.pgvector import PGVectorDb
db = PGVectorDb(connection="postgresql://user:pass@localhost/db")

# Additional Vector Databases
from buddy.vectordb.milvus import MilvusDb
db = MilvusDb(host="localhost", port=19530)

from buddy.vectordb.lancedb import LanceDb  
db = LanceDb(path="./lance_db")

from buddy.vectordb.cassandra import CassandraDb
db = CassandraDb(hosts=["127.0.0.1"], keyspace="buddy")

from buddy.vectordb.clickhouse import ClickHouseDb
db = ClickHouseDb(host="localhost", port=8123)

from buddy.vectordb.surrealdb import SurrealDb
db = SurrealDb(url="ws://localhost:8000/rpc")

from buddy.vectordb.upstashdb import UpstashDb
db = UpstashDb(url="your-upstash-url", token="your-token")

from buddy.vectordb.couchbase import CouchbaseDb
db = CouchbaseDb(connection_string="couchbase://localhost")

from buddy.vectordb.singlestore import SingleStoreDb
db = SingleStoreDb(host="localhost", port=3306, database="buddy")
```

### **Embedder Options**

```python
# OpenAI Embeddings (default)
from buddy.embedder.openai import OpenAIEmbedder
embedder = OpenAIEmbedder(model="text-embedding-3-large")

# Alternative Embedders
from buddy.embedder.cohere import CohereEmbedder
embedder = CohereEmbedder(model="embed-english-v3.0")

from buddy.embedder.google import GoogleEmbedder
embedder = GoogleEmbedder(model="models/embedding-001")

from buddy.embedder.huggingface import HuggingFaceEmbedder
embedder = HuggingFaceEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")

from buddy.embedder.sentence_transformer import SentenceTransformerEmbedder
embedder = SentenceTransformerEmbedder(model="all-mpnet-base-v2")

from buddy.embedder.azure_openai import AzureOpenAIEmbedder
embedder = AzureOpenAIEmbedder(
    deployment="text-embedding-ada-002",
    endpoint="https://your-resource.openai.azure.com"
)

from buddy.embedder.aws_bedrock import AWSBedrockEmbedder
embedder = AWSBedrockEmbedder(model="amazon.titan-embed-text-v1")

from buddy.embedder.ollama import OllamaEmbedder
embedder = OllamaEmbedder(model="nomic-embed-text")

from buddy.embedder.fastembed import FastEmbedEmbedder
embedder = FastEmbedEmbedder(model="BAAI/bge-small-en-v1.5")

from buddy.embedder.jina import JinaEmbedder
embedder = JinaEmbedder(model="jina-embeddings-v2-base-en")

from buddy.embedder.voyageai import VoyageAIEmbedder
embedder = VoyageAIEmbedder(model="voyage-large-2")

from buddy.embedder.mistral import MistralEmbedder
embedder = MistralEmbedder(model="mistral-embed")
```

---

## 🧠 **Memory & Context**

### **Agent Memory**

```python
from buddy.memory.agent import AgentMemory

# Persistent conversation memory
memory = AgentMemory(
    db_url="postgresql://user:pass@localhost/buddy",
    create_user_memories=True,      # Remember user-specific info
    create_session_summary=True,    # Summarize long conversations
    num_memories=10                 # Keep top 10 relevant memories
)

agent = Agent(
    name="PersonalAssistant",
    model=OpenAIChat(id="gpt-4"),
    memory=memory,
    user_id="user_123"  # Track conversations by user
)

# The agent remembers across sessions
response1 = agent.run("My name is John and I work in marketing")
response2 = agent.run("What do you remember about me?")  # Recalls previous info
```

### **Team Memory**

```python
from buddy.memory.team import TeamMemory

# Shared memory across team members
team_memory = TeamMemory(
    db_url="postgresql://user:pass@localhost/buddy",
    shared_memories=True
)

team = Team(
    name="ResearchTeam",
    agents=[researcher, analyst, writer],
    memory=team_memory
)
```

---

## 💾 **Storage & Persistence**

Comprehensive storage options for different use cases:

### **Agent Storage**

```python
# SQLite (default - simple, local)
from buddy.storage.agent.sqlite import SQLiteAgentStorage
storage = SQLiteAgentStorage(db_path="./agents.db")

# PostgreSQL (production)
from buddy.storage.agent.postgres import PostgresAgentStorage
storage = PostgresAgentStorage(
    host="localhost",
    port=5432,
    database="buddy",
    user="buddy_user", 
    password="password"
)

# MongoDB (document-based)
from buddy.storage.agent.mongodb import MongoAgentStorage
storage = MongoAgentStorage(
    connection_string="mongodb://localhost:27017",
    database="buddy"
)

# JSON (file-based)
from buddy.storage.agent.json import JSONAgentStorage
storage = JSONAgentStorage(file_path="./agent_data.json")

# YAML (human-readable)
from buddy.storage.agent.yaml import YAMLAgentStorage
storage = YAMLAgentStorage(file_path="./agent_data.yaml")

# DynamoDB (AWS)
from buddy.storage.agent.dynamodb import DynamoDBAgentStorage
storage = DynamoDBAgentStorage(
    table_name="buddy-agents",
    region="us-east-1"
)

# SingleStore (high-performance)
from buddy.storage.agent.singlestore import SingleStoreAgentStorage
storage = SingleStoreAgentStorage(
    host="localhost",
    port=3306,
    database="buddy"
)

# Use storage with agent
agent = Agent(
    name="PersistentAgent",
    model=OpenAIChat(id="gpt-4"),
    storage=storage
)
```

### **Memory Storage**

```python
# In-memory (fastest, not persistent)
from buddy.storage.in_memory import InMemoryStorage
memory_storage = InMemoryStorage()

# Redis (fast, distributed)
from buddy.storage.redis import RedisStorage
memory_storage = RedisStorage(
    host="localhost",
    port=6379,
    db=0,
    password="your-redis-password"
)

# Firestore (Google Cloud)
from buddy.storage.firestore import FirestoreStorage
memory_storage = FirestoreStorage(
    project_id="your-project",
    collection="buddy_memory"
)

# MySQL
from buddy.storage.mysql import MySQLStorage
memory_storage = MySQLStorage(
    host="localhost",
    port=3306,
    database="buddy",
    user="buddy_user",
    password="password"
)

# GCS JSON (Google Cloud Storage)
from buddy.storage.gcs_json import GCSJSONStorage
memory_storage = GCSJSONStorage(
    bucket_name="buddy-storage",
    file_path="memory/agent_memory.json"
)

agent = Agent(
    name="CloudAgent",
    model=OpenAIChat(id="gpt-4"),
    memory=AgentMemory(storage=memory_storage)
)
```

### **Session Storage**

```python
# Different storage for different session types
from buddy.storage.session.agent import AgentSessionStorage
from buddy.storage.session.team import TeamSessionStorage  
from buddy.storage.session.workflow import WorkflowSessionStorage

# Agent sessions
agent_sessions = AgentSessionStorage(
    storage_type="postgresql",
    connection_string="postgresql://user:pass@localhost/buddy"
)

# Team sessions  
team_sessions = TeamSessionStorage(
    storage_type="mongodb",
    connection_string="mongodb://localhost:27017/buddy"
)

# Workflow sessions (v2)
from buddy.storage.session.v2.workflow import WorkflowSessionStorageV2
workflow_sessions = WorkflowSessionStorageV2(
    storage_type="sqlite",
    db_path="./workflow_sessions.db"
)
```

---

## 🔄 **Advanced Workflows**

Build complex, automated workflows with multiple agents:

### **Workflow V2 (Latest)**

```python
from buddy.workflow.v2 import Workflow, Step, Condition, Loop, Parallel
from buddy.workflow.v2.router import WorkflowRouter

# Define complex workflow with conditions and loops
workflow = Workflow(
    name="DocumentProcessingWorkflow",
    description="Process documents with quality checks and revisions",
    steps=[
        Step(
            id="extract",
            agent="document_processor",
            task="extract_text_and_metadata",
            input_mapping={"file": "input.document"}
        ),
        
        Condition(
            id="quality_check",
            condition="extracted_text.confidence > 0.8",
            true_step="analyze",
            false_step="manual_review"
        ),
        
        Step(
            id="analyze", 
            agent="content_analyzer",
            task="analyze_content_structure",
            depends_on=["extract"]
        ),
        
        Parallel(
            id="parallel_processing",
            steps=[
                Step(
                    id="summarize",
                    agent="summarizer", 
                    task="create_summary"
                ),
                Step(
                    id="classify",
                    agent="classifier",
                    task="classify_document_type"
                ),
                Step(
                    id="extract_entities",
                    agent="entity_extractor",
                    task="extract_named_entities"
                )
            ]
        ),
        
        Loop(
            id="review_loop",
            condition="quality_score < 0.9",
            max_iterations=3,
            steps=[
                Step(
                    id="review",
                    agent="reviewer",
                    task="review_and_improve"
                ),
                Step(
                    id="validate", 
                    agent="validator",
                    task="validate_quality"
                )
            ]
        ),
        
        Step(
            id="finalize",
            agent="finalizer",
            task="prepare_final_output",
            depends_on=["parallel_processing", "review_loop"]
        )
    ]
)

# Execute workflow
from buddy.run.v2.workflow import WorkflowRunner

runner = WorkflowRunner(workflow=workflow)
result = runner.execute(
    input_data={"document": "path/to/document.pdf"},
    context={"user_id": "user123", "project": "doc_processing"}
)

print(f"Workflow completed in {result.execution_time} seconds")
print(f"Final result: {result.output}")
```

### **Dynamic Workflow Routing**

```python
from buddy.workflow.v2.router import DynamicRouter

# Create dynamic routing based on content
router = DynamicRouter(
    routes={
        "technical": ["tech_analyzer", "code_reviewer", "documentation_generator"],
        "legal": ["legal_analyst", "compliance_checker", "contract_generator"], 
        "marketing": ["market_researcher", "content_creator", "seo_optimizer"],
        "financial": ["financial_analyst", "risk_assessor", "report_generator"]
    },
    classifier_agent="content_classifier",
    fallback_route="general"
)

# Workflow with dynamic routing
dynamic_workflow = Workflow(
    name="SmartDocumentWorkflow",
    router=router,
    steps=[
        Step(
            id="classify",
            agent="content_classifier",
            task="classify_document_type"
        ),
        
        # Router automatically selects appropriate agents based on classification
        Step(
            id="process",
            router="dynamic",
            task="process_based_on_type"
        ),
        
        Step(
            id="quality_assurance",
            agent="qa_agent", 
            task="final_quality_check"
        )
    ]
)
```

### **Workflow with Human-in-the-Loop**

```python
from buddy.workflow.v2.types import HumanApproval, UserInput

workflow_with_human = Workflow(
    name="ContentApprovalWorkflow",
    steps=[
        Step(
            id="draft",
            agent="content_writer",
            task="create_draft_content"
        ),
        
        HumanApproval(
            id="human_review",
            message="Please review the draft content",
            timeout=3600,  # 1 hour timeout
            required_approvers=["manager@company.com"],
            approval_threshold=1
        ),
        
        Condition(
            id="check_approval",
            condition="human_review.approved == true",
            true_step="publish",
            false_step="revise"
        ),
        
        Step(
            id="revise",
            agent="content_editor",
            task="revise_based_on_feedback",
            input_mapping={"feedback": "human_review.feedback"}
        ),
        
        UserInput(
            id="get_preferences",
            prompt="What style preferences do you have?",
            input_type="text",
            required=False
        ),
        
        Step(
            id="publish",
            agent="publisher",
            task="publish_content"
        )
    ]
)
```

### **Workflow Monitoring & Analytics**

```python
from buddy.workflow.v2.monitoring import WorkflowMonitor
from buddy.workflow.v2.analytics import WorkflowAnalytics

# Monitor workflow execution
monitor = WorkflowMonitor(
    webhook_url="https://your-app.com/webhook",
    enable_step_tracking=True,
    enable_performance_metrics=True,
    alert_on_failures=True
)

# Analyze workflow performance
analytics = WorkflowAnalytics(
    storage="postgresql://user:pass@localhost/buddy_analytics"
)

workflow.add_monitor(monitor)
workflow.add_analytics(analytics)

# Get workflow insights
insights = analytics.get_workflow_insights("DocumentProcessingWorkflow")
print(f"Average execution time: {insights.avg_execution_time}")
print(f"Success rate: {insights.success_rate}")
print(f"Bottleneck steps: {insights.bottleneck_steps}")
```

---

## 📊 **Evaluation & Analytics**

Comprehensive evaluation tools for measuring agent performance:

### **Agent Evaluation**

```python
from buddy.eval.accuracy import AccuracyEvaluator
from buddy.eval.performance import PerformanceEvaluator
from buddy.eval.reliability import ReliabilityEvaluator

# Accuracy evaluation
accuracy_eval = AccuracyEvaluator(
    test_cases=[
        {"input": "What is 2+2?", "expected": "4"},
        {"input": "Capital of France?", "expected": "Paris"},
        {"input": "Who wrote Romeo and Juliet?", "expected": "Shakespeare"}
    ],
    similarity_threshold=0.8,
    use_llm_judge=True,  # Use LLM to judge accuracy
    judge_model="gpt-4"
)

accuracy_score = accuracy_eval.evaluate(agent)
print(f"Accuracy: {accuracy_score:.2%}")

# Performance evaluation
performance_eval = PerformanceEvaluator(
    metrics=["response_time", "token_usage", "cost", "throughput"],
    benchmark_queries=[
        "Simple question requiring direct answer",
        "Complex multi-step reasoning problem", 
        "Tool usage scenario",
        "Knowledge retrieval task"
    ]
)

performance_report = performance_eval.evaluate(agent)
print(f"Avg Response Time: {performance_report.avg_response_time}ms")
print(f"Token Efficiency: {performance_report.tokens_per_response}")

# Reliability evaluation
reliability_eval = ReliabilityEvaluator(
    test_duration=3600,  # 1 hour stress test
    concurrent_requests=10,
    error_tolerance=0.05,  # 5% error rate acceptable
    consistency_checks=True
)

reliability_score = reliability_eval.evaluate(agent)
print(f"Reliability: {reliability_score:.2%}")
```

### **A/B Testing**

```python
from buddy.eval.utils import ABTestFramework

# Compare two agents
ab_test = ABTestFramework(
    agent_a=agent_v1,
    agent_b=agent_v2,
    test_queries=evaluation_dataset,
    metrics=["accuracy", "response_time", "user_satisfaction"],
    sample_size=1000,
    significance_level=0.05
)

results = ab_test.run_test()
print(f"Winner: {results.winning_agent}")
print(f"Confidence: {results.confidence:.2%}")
print(f"Improvement: {results.improvement_percentage:.1%}")
```

### **Custom Evaluation Metrics**

```python
from buddy.eval.utils import CustomEvaluator

def domain_specific_accuracy(response: str, expected: str, context: dict) -> float:
    """Custom evaluation logic for domain-specific accuracy."""
    # Your custom evaluation logic
    return similarity_score

def response_relevance(response: str, query: str) -> float:
    """Evaluate how relevant the response is to the query."""
    # Your relevance scoring logic
    return relevance_score

custom_eval = CustomEvaluator(
    metrics={
        "domain_accuracy": domain_specific_accuracy,
        "relevance": response_relevance,
        "conciseness": lambda resp, _: len(resp.split()) / 100  # Prefer shorter responses
    }
)

scores = custom_eval.evaluate(agent, test_cases)
```

---

## 🔌 **API Integration**

### **RESTful API Server**

```python
from buddy.api import create_buddy_api
from buddy.api.schemas import AgentResponse, ChatRequest

# Create comprehensive API
api = create_buddy_api(
    agents={
        "assistant": general_assistant,
        "support": customer_support_agent, 
        "analyst": data_analyst_agent
    },
    authentication="jwt",  # or "api_key", "oauth2"
    rate_limiting=True,
    enable_swagger=True,
    enable_metrics=True
)

# Custom endpoints
@api.post("/custom/analyze")
async def custom_analyze(request: AnalysisRequest) -> AnalysisResponse:
    """Custom analysis endpoint."""
    result = await analyst_agent.arun(request.query)
    return AnalysisResponse(analysis=result.content)

# Start API server
api.run(host="0.0.0.0", port=8000)
```

### **WebSocket Support**

```python
from buddy.api.websocket import WebSocketManager

# Real-time agent interactions
ws_manager = WebSocketManager(
    agents={"assistant": assistant_agent},
    enable_streaming=True,
    max_connections=100
)

@api.websocket("/ws/chat/{agent_name}")
async def websocket_chat(websocket: WebSocket, agent_name: str):
    await ws_manager.handle_connection(websocket, agent_name)
```

### **API Client SDK**

```python
from buddy.api.client import BuddyAPIClient

# Connect to Buddy AI API
client = BuddyAPIClient(
    base_url="https://your-buddy-api.com",
    api_key="your-api-key"
)

# Use remote agents
response = await client.chat(
    agent="assistant",
    message="Hello, how can you help me?",
    user_id="user123"
)

# Stream responses
async for chunk in client.stream_chat(
    agent="assistant", 
    message="Write a long story",
    user_id="user123"
):
    print(chunk.content, end="")

# List available agents
agents = await client.list_agents()
print("Available agents:", [agent.name for agent in agents])
```

---

## 🎯 **Specialized Use Cases**

### **Code Generation & Development**

```python
from buddy import Agent
from buddy.models.openai import OpenAIChat
from buddy.tools.python import PythonTools
from buddy.tools.github import GithubTools
from buddy.tools.shell import ShellTools

# Specialized coding agent
coding_agent = Agent(
    name="CodeGenius",
    model=OpenAIChat(id="gpt-4", temperature=0.1),  # Lower temperature for code
    tools=[PythonTools(), GithubTools(), ShellTools()],
    instructions="""
    You are an expert software developer. You can:
    - Write clean, efficient code in multiple languages
    - Debug and fix issues
    - Create unit tests
    - Review code for best practices
    - Integrate with Git workflows
    Always follow coding best practices and include proper error handling.
    """
)

# Generate and test code
response = coding_agent.run("""
Create a Python class for managing a TODO list with the following features:
1. Add, remove, and update tasks
2. Mark tasks as complete
3. Filter tasks by status
4. Save/load from JSON file
5. Include comprehensive unit tests
""")
```

### **Data Science & Analytics**

```python
from buddy.tools.pandas import PandasTools
from buddy.tools.sql import SQLTools
from buddy.tools.visualization import VisualizationTools

data_scientist = Agent(
    name="DataScientist",
    model=OpenAIChat(id="gpt-4"),
    tools=[PandasTools(), SQLTools(), VisualizationTools()],
    instructions="""
    You are a senior data scientist. You excel at:
    - Data cleaning and preprocessing  
    - Statistical analysis and hypothesis testing
    - Machine learning model development
    - Data visualization and storytelling
    - SQL query optimization
    Always validate your analysis and provide clear insights.
    """
)

# Comprehensive data analysis
analysis = data_scientist.run("""
Analyze the sales data in the database:
1. Load data from the 'sales' table
2. Clean and preprocess the data
3. Perform exploratory data analysis
4. Identify trends and patterns
5. Create visualizations
6. Provide business recommendations
""")
```

### **Content Creation & Marketing**

```python
from buddy.tools.googlesearch import GoogleSearchTools
from buddy.tools.dalle import DalleTools
from buddy.tools.seo import SEOTools

content_creator = Agent(
    name="ContentCreator",
    model=OpenAIChat(id="gpt-4"),
    tools=[GoogleSearchTools(), DalleTools(), SEOTools()],
    instructions="""
    You are a creative content marketing expert. You specialize in:
    - SEO-optimized blog posts and articles
    - Social media content across platforms
    - Visual content creation
    - Market research and trend analysis
    - Brand voice and messaging
    Create engaging, authentic content that drives results.
    """
)

# Content campaign creation
campaign = content_creator.run("""
Create a complete content marketing campaign for a new eco-friendly water bottle:
1. Research market trends and competitors
2. Develop key messaging and positioning
3. Create blog post outlines (5 posts)
4. Generate social media content (Instagram, LinkedIn, Twitter)
5. Design visual concepts for the bottle
6. Develop email marketing sequence
""")
```

---

## 🚀 **Deployment Options**

### **FastAPI Web Service**

```python
from buddy.app.fastapi import create_buddy_app
from buddy import Agent
from buddy.models.openai import OpenAIChat

# Create your agent
agent = Agent(
    name="WebAgent",
    model=OpenAIChat(id="gpt-4"),
    instructions="You are a helpful web assistant."
)

# Create FastAPI app
app = create_buddy_app(
    agents=[agent],
    enable_playground=True,    # Built-in chat interface
    enable_cors=True,         # Enable CORS
    enable_metrics=True       # Enable monitoring
)

# Run with: uvicorn main:app --host 0.0.0.0 --port 8000
```

### **CLI Application**

```python
from buddy.cli import BuddyCLI
from buddy import Agent
from buddy.models.openai import OpenAIChat

agent = Agent(
    name="CLI Assistant",
    model=OpenAIChat(id="gpt-4"),
    instructions="You are a helpful CLI assistant."
)

cli = BuddyCLI(
    agent=agent,
    title="My AI Assistant",
    description="AI-powered command line tool"
)

# Run the CLI
if __name__ == "__main__":
    cli.run()
```

### **Slack Integration**

```python
from buddy.app.slack import SlackApp
from buddy import Agent

agent = Agent(
    name="SlackBot",
    model=OpenAIChat(id="gpt-4"),
    instructions="You are a helpful Slack assistant."
)

slack_app = SlackApp(
    agent=agent,
    bot_token="xoxb-your-bot-token",
    signing_secret="your-signing-secret"
)

# Run with: python slack_bot.py
if __name__ == "__main__":
    slack_app.start()
```

### **Discord Bot**

```python
from buddy.app.discord import DiscordBot
from buddy import Agent

agent = Agent(
    name="DiscordBot",
    model=OpenAIChat(id="gpt-4"),
    instructions="You are a friendly Discord bot."
)

bot = DiscordBot(
    agent=agent,
    token="your-discord-token",
    command_prefix="!"
)

# Run with: python discord_bot.py
if __name__ == "__main__":
    bot.run()
```

---

## 🧠 **Advanced Reasoning**

Buddy AI includes sophisticated reasoning capabilities for complex problem-solving:

### **Chain-of-Thought Reasoning**

```python
from buddy import Agent
from buddy.models.openai import OpenAIChat
from buddy.reasoning.openai import OpenAIReasoning

# Create agent with reasoning capabilities
reasoning_agent = Agent(
    name="LogicExpert",
    model=OpenAIChat(id="gpt-4"),
    reasoning=OpenAIReasoning(
        enable_step_by_step=True,
        show_reasoning_steps=True,
        max_reasoning_steps=10
    ),
    instructions="""
    You are an expert problem solver. Break down complex problems into logical steps.
    Show your reasoning process clearly before providing the final answer.
    """
)

# Complex reasoning example
response = reasoning_agent.run("""
If a train leaves New York at 3 PM traveling at 80 mph toward Chicago (800 miles away),
and another train leaves Chicago at 4 PM traveling at 90 mph toward New York,
at what time will they meet and how far from New York?
""")

print("Reasoning Steps:")
for step in response.reasoning_steps:
    print(f"Step {step.number}: {step.thought}")
print(f"\nFinal Answer: {response.content}")
```

### **Multi-Step Problem Solving**

```python
from buddy.reasoning.step import ReasoningStep
from buddy.reasoning.default import DefaultReasoning

# Define custom reasoning steps
steps = [
    ReasoningStep(
        name="problem_analysis",
        description="Analyze and break down the problem",
        required=True
    ),
    ReasoningStep(
        name="solution_planning", 
        description="Plan the solution approach",
        depends_on=["problem_analysis"]
    ),
    ReasoningStep(
        name="execution",
        description="Execute the planned solution",
        depends_on=["solution_planning"]
    ),
    ReasoningStep(
        name="verification",
        description="Verify and validate the solution",
        depends_on=["execution"]
    )
]

reasoning_system = DefaultReasoning(steps=steps)

agent = Agent(
    name="StructuredThinker",
    model=OpenAIChat(id="gpt-4"),
    reasoning=reasoning_system,
    instructions="Follow the structured reasoning process for all complex problems."
)
```

### **Reasoning with Different Providers**

```python
# OpenAI Reasoning
from buddy.reasoning.openai import OpenAIReasoning
openai_reasoning = OpenAIReasoning(model="gpt-4o-reasoning")

# Groq Reasoning (Fast)
from buddy.reasoning.groq import GroqReasoning  
groq_reasoning = GroqReasoning(model="llama-3.1-70b-reasoning")

# DeepSeek Reasoning
from buddy.reasoning.deepseek import DeepSeekReasoning
deepseek_reasoning = DeepSeekReasoning(model="deepseek-r1")

# Azure AI Foundry Reasoning
from buddy.reasoning.azure_ai_foundry import AzureReasoning
azure_reasoning = AzureReasoning(deployment="reasoning-model")
```

---

## 🎯 **Model Training & Fine-tuning**

Train and fine-tune your own models locally:

### **Simple Model Training**

```python
from buddy.train import train_model, test_model, list_models

# Train a model in one line!
train_model(
    data_path="./training_data",
    model_name="my-custom-model",
    base_model="llama-3.1-8b",  # Base model to fine-tune
    epochs=3,
    learning_rate=1e-4
)

# Test your trained model
response = test_model("my-custom-model", "Hello, how are you?")
print(response)

# List all your trained models
models = list_models()
print("Available models:", models)
```

### **Advanced Training Configuration**

```python
from buddy.train.trainer import BuddyTrainer
from buddy.train.data_processor import DataProcessor
from buddy.train.model_manager import ModelManager

# Prepare your data
processor = DataProcessor(
    input_format="jsonl",  # or "csv", "txt", "parquet"
    validation_split=0.2,
    max_sequence_length=2048,
    tokenizer="llama"
)

training_data = processor.process("./raw_data.jsonl")

# Configure trainer
trainer = BuddyTrainer(
    model_name="my-specialized-agent",
    base_model="meta-llama/Llama-3.1-8B-Instruct",
    training_config={
        "epochs": 5,
        "batch_size": 4,
        "learning_rate": 2e-5,
        "weight_decay": 0.01,
        "warmup_steps": 100,
        "gradient_accumulation_steps": 4,
        "fp16": True,  # Mixed precision training
        "deepspeed": True  # Distributed training
    }
)

# Train the model
trainer.train(
    train_data=training_data["train"],
    val_data=training_data["validation"],
    save_steps=500,
    eval_steps=100,
    output_dir="./models/my-specialized-agent"
)

# Integrate trained model with agent
from buddy.models.local import LocalModel

custom_model = LocalModel(
    model_path="./models/my-specialized-agent",
    tokenizer_path="./models/my-specialized-agent"
)

agent = Agent(
    name="CustomAgent",
    model=custom_model,
    instructions="You are a specialized agent trained on domain-specific data."
)
```

### **CLI Training (Super Simple)**

```bash
# Train a model from command line
buddy train ./data --name my-model --epochs 3

# Test your model  
buddy train test my-model "What is AI?"

# List trained models
buddy train list

# Export model for deployment
buddy train export my-model --format onnx
```

### **Training Data Formats**

```python
# JSONL format (recommended)
# Each line: {"input": "question", "output": "answer"}

# CSV format
# columns: input,output

# Text format
# Structured text with separators

# Conversation format
conversations = [
    {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help you?"},
            {"role": "user", "content": "What's the weather?"},
            {"role": "assistant", "content": "I'd need your location to check the weather."}
        ]
    }
]

trainer.train_conversational(conversations)
```

---

## 🔄 **Result Reranking**

Improve search and retrieval accuracy with intelligent reranking:

### **Search Result Reranking**

```python
from buddy.reranker.cohere import CohereReranker
from buddy.reranker.sentence_transformer import SentenceTransformerReranker
from buddy.knowledge.document import DocumentKnowledgeBase

# Setup reranker
reranker = CohereReranker(
    model="rerank-english-v3.0",
    api_key="your-cohere-key"
)

# Alternative: Local reranker
# reranker = SentenceTransformerReranker(
#     model="cross-encoder/ms-marco-MiniLM-L-6-v2"
# )

# Use with knowledge base
knowledge = DocumentKnowledgeBase(
    path="./documents",
    embedder=OpenAIEmbedder(),
    reranker=reranker,
    rerank_top_k=20,  # Rerank top 20 results
    final_top_k=5     # Return top 5 after reranking
)

agent = Agent(
    name="SearchExpert",
    model=OpenAIChat(id="gpt-4"),
    knowledge=knowledge,
    search_knowledge=True,
    instructions="Use the knowledge base to provide accurate, well-sourced answers."
)

# More accurate results due to reranking
response = agent.run("What are the key benefits of renewable energy?")
```

### **Custom Reranking Logic**

```python
from buddy.reranker.base import BaseReranker
from typing import List, Dict, Any

class CustomReranker(BaseReranker):
    def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Custom reranking logic based on your criteria."""
        
        # Example: Boost recent documents
        import datetime
        for doc in documents:
            doc_date = doc.get('date', '2020-01-01')
            date_obj = datetime.datetime.strptime(doc_date, '%Y-%m-%d')
            recency_boost = max(0, (datetime.datetime.now() - date_obj).days / 365)
            doc['score'] = doc.get('score', 0) + recency_boost
        
        # Sort by enhanced score
        return sorted(documents, key=lambda x: x['score'], reverse=True)

# Use custom reranker
custom_reranker = CustomReranker()
knowledge = DocumentKnowledgeBase(
    path="./documents",
    reranker=custom_reranker
)
```

---

## 🏢 **Workspace Management** 

Organize and manage complex AI projects:

### **Project Workspace**

```python
from buddy.workspace import Workspace
from buddy.workspace.config import WorkspaceConfig

# Create a workspace for your project
workspace = Workspace(
    name="CustomerServiceProject",
    description="Complete customer service automation system",
    config=WorkspaceConfig(
        default_model="gpt-4",
        default_temperature=0.7,
        enable_logging=True,
        enable_metrics=True
    )
)

# Add agents to workspace
workspace.add_agent("support_agent", support_agent)
workspace.add_agent("escalation_agent", escalation_agent)
workspace.add_agent("feedback_agent", feedback_agent)

# Add shared resources
workspace.add_knowledge_base("company_kb", company_knowledge)
workspace.add_memory("shared_memory", team_memory)

# Set up workflows
workspace.create_workflow(
    name="customer_support_flow",
    agents=["support_agent", "escalation_agent"],
    trigger_conditions=["customer_inquiry"],
    escalation_rules={"complex_issue": "escalation_agent"}
)

# Deploy workspace
workspace.deploy(
    platform="fastapi",
    host="0.0.0.0", 
    port=8000,
    enable_docs=True
)
```

### **Workspace Configuration**

```yaml
# workspace.yaml
name: "AI Assistant Workspace"
version: "1.0.0"
description: "Production AI assistant system"

agents:
  primary_agent:
    model: "gpt-4"
    tools: ["calculator", "email", "calendar"]
    memory: "shared_memory"
    
  specialist_agent:
    model: "claude-3-opus"
    tools: ["python", "database"]
    knowledge: "technical_kb"

knowledge_bases:
  company_kb:
    type: "document"
    path: "./knowledge/company"
    vector_db: "chroma"
    
  technical_kb:
    type: "sql"
    path: "./knowledge/technical"
    db_path: "./technical.db"

workflows:
  main_flow:
    trigger: "user_input"
    steps:
      - agent: "primary_agent"
        condition: "general_query"
      - agent: "specialist_agent" 
        condition: "technical_query"

deployment:
  platform: "fastapi"
  port: 8000
  enable_playground: true
  enable_metrics: true
```

### **Workspace CLI**

```bash
# Create new workspace
buddy workspace create my-project

# Add agent to workspace
buddy workspace add-agent support-bot --model gpt-4

# Deploy workspace
buddy workspace deploy --platform fastapi --port 8000

# Monitor workspace
buddy workspace status
buddy workspace logs
buddy workspace metrics
```

---

## 🎮 **Interactive Playground**

Built-in development environment for testing and experimentation:

### **Web-based Playground**

```python
from buddy.playground import BuddyPlayground
from buddy import Agent

# Create agents for playground
agents = [
    Agent(name="Assistant", model=OpenAIChat(id="gpt-4")),
    Agent(name="Coder", model=OpenAIChat(id="gpt-4"), tools=[PythonTools()]),
    Agent(name="Researcher", model=OpenAIChat(id="gpt-4"), tools=[GoogleSearchTools()])
]

# Start playground
playground = BuddyPlayground(
    agents=agents,
    title="My AI Playground",
    theme="dark",  # or "light"
    enable_code_execution=True,
    enable_file_upload=True,
    enable_model_switching=True
)

# Launch playground server
playground.serve(
    host="0.0.0.0",
    port=8080,
    auto_open=True  # Opens browser automatically
)

# Access at: http://localhost:8080
```

### **Playground Features**

```python
# Configure playground with advanced features
playground = BuddyPlayground(
    agents=agents,
    features={
        "chat_interface": True,
        "agent_comparison": True,  # Side-by-side agent comparison
        "conversation_export": True,  # Export chat history
        "model_switching": True,  # Switch models on the fly
        "tool_testing": True,  # Test individual tools
        "prompt_templates": True,  # Pre-built prompt templates
        "performance_metrics": True,  # Real-time performance data
        "collaborative_mode": True  # Multi-user collaboration
    },
    settings={
        "max_conversation_length": 100,
        "auto_save_interval": 30,  # seconds
        "enable_syntax_highlighting": True,
        "enable_markdown_rendering": True
    }
)
```

### **Playground Deployment**

```python
# Deploy playground as standalone app
from buddy.playground.deploy import deploy_playground

deploy_playground(
    agents=agents,
    deployment_config={
        "platform": "docker",
        "image_name": "my-buddy-playground",
        "port": 8080,
        "environment": "production",
        "ssl_enabled": True,
        "auth_required": True
    }
)

# Or integrate with existing FastAPI app
from buddy.app.fastapi import create_buddy_app

app = create_buddy_app(
    agents=agents,
    enable_playground=True,
    playground_config={
        "path": "/playground",
        "authentication": "oauth2",
        "admin_users": ["admin@company.com"]
    }
)
```

---

## 🎨 **Advanced UI Components**

### **AGUI (Advanced Gradio UI)**

```python
from buddy.app.agui import create_agui_app

# Create advanced Gradio interface
agui_app = create_agui_app(
    agents=agents,
    interface_config={
        "layout": "tabbed",  # or "sidebar", "modal"
        "theme": "custom",
        "components": {
            "chat_interface": {
                "enable_voice_input": True,
                "enable_file_upload": True,
                "enable_image_generation": True,
                "max_history": 50
            },
            "agent_selector": {
                "display_mode": "dropdown",  # or "radio", "buttons"
                "show_agent_info": True
            },
            "tools_panel": {
                "show_available_tools": True,
                "enable_tool_testing": True
            }
        }
    }
)

# Launch AGUI
agui_app.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True,  # Create public link
    auth=("admin", "password")  # Optional authentication
)
```

### **Streamlit Integration**

```python
from buddy.tools.streamlit import StreamlitComponents
import streamlit as st

# Use Buddy AI components in Streamlit
components = StreamlitComponents()

# Agent chat component
agent_response = components.chat_interface(
    agent=support_agent,
    title="Customer Support Assistant",
    placeholder="How can I help you today?",
    sidebar_info=True
)

# Multi-agent comparison
comparison_result = components.agent_comparison(
    agents=[agent1, agent2, agent3],
    query=st.text_input("Test query"),
    metrics=["response_time", "token_usage", "relevance"]
)

# Tool testing component
tool_result = components.tool_tester(
    available_tools=[CalculatorTools(), PythonTools()],
    enable_input_validation=True
)
```

---

## ⚙️ **Configuration**

### **Environment Variables**

```bash
# AI Model Provider API Keys
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key" 
export GOOGLE_API_KEY="your-google-key"
export COHERE_API_KEY="your-cohere-key"

# Cloud Provider Credentials
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-azure-key"

# Database Configuration
export BUDDY_DB_URL="postgresql://user:pass@localhost/buddy"
export BUDDY_REDIS_URL="redis://localhost:6379"

# Vector Database Settings
export PINECONE_API_KEY="your-pinecone-key"
export WEAVIATE_URL="http://localhost:8080"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"

# Application Settings
export BUDDY_LOG_LEVEL="INFO"
export BUDDY_ENABLE_METRICS="true"
export BUDDY_MAX_TOOL_EXECUTION_TIME="30"
```

### **Configuration File (buddy_config.yaml)**

```yaml
# Model Configuration
models:
  default_provider: "openai"
  default_model: "gpt-4"
  fallback_model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 4000

# Database Settings  
database:
  url: "postgresql://user:pass@localhost/buddy"
  pool_size: 10
  max_overflow: 20
  
memory:
  provider: "postgresql"
  retention_days: 30
  max_memories_per_user: 100

# Vector Database
vectordb:
  provider: "chroma"
  path: "./vector_db"
  collection_name: "buddy_knowledge"

# Security & Performance
security:
  enable_tool_sandboxing: true
  max_tool_execution_time: 30
  allowed_domains: ["api.company.com", "trusted-source.com"]
  
performance:
  enable_caching: true
  cache_ttl: 3600
  max_concurrent_requests: 10

# Monitoring
monitoring:
  enable_metrics: true
  enable_tracing: true
  log_level: "INFO"
  metrics_retention_days: 7

# Development
development:
  debug_mode: false
  show_tool_calls: true
  enable_playground: true
```

### **Loading Configuration**

```python
from buddy.config import load_config

# Load from file
config = load_config("buddy_config.yaml")

# Use in agent
agent = Agent(
    name="ConfiguredAgent",
    model=OpenAIChat(
        id=config.models.default_model,
        temperature=config.models.temperature
    ),
    config=config
)
```

---

## 🔐 **Security & Best Practices**

### **Tool Sandboxing**

```python
from buddy.security import ToolSandbox
from buddy.tools.python import PythonTools

# Create secure sandbox
sandbox = ToolSandbox(
    allowed_modules=["requests", "pandas", "numpy", "matplotlib"],
    blocked_functions=["exec", "eval", "__import__"],
    max_execution_time=30,
    max_memory_mb=512,
    allow_network=False
)

# Apply to tools
secure_python = PythonTools(sandbox=sandbox)

agent = Agent(
    name="SecureAgent",
    model=OpenAIChat(id="gpt-4"),
    tools=[secure_python],
    instructions="You can execute Python code safely within the sandbox."
)
```

### **Input Validation**

```python
from buddy.security import InputValidator

# Comprehensive input validation
validator = InputValidator(
    max_length=10000,
    min_length=1,
    blocked_patterns=["<script>", "javascript:", "data:"],
    allowed_file_types=[".txt", ".pdf", ".docx"],
    sanitize_html=True,
    check_for_injection=True
)

agent = Agent(
    name="PublicAgent",
    model=OpenAIChat(id="gpt-4"),
    input_validator=validator,
    instructions="You handle public user input safely."
)
```

### **Rate Limiting**

```python
from buddy.security import RateLimiter

# Configure rate limits
rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000,
    burst_size=10
)

agent = Agent(
    name="ProductionAgent",
    model=OpenAIChat(id="gpt-4"),
    rate_limiter=rate_limiter
)
```

### **API Key Management**

```python
from buddy.security import SecretManager

# Secure API key storage
secret_manager = SecretManager(
    provider="hashicorp_vault",  # or "aws_secrets", "azure_keyvault"
    vault_url="https://vault.company.com",
    vault_token="your-vault-token"
)

# Use in models
model = OpenAIChat(
    id="gpt-4",
    api_key=secret_manager.get_secret("openai_api_key")
)
```

---

## 📊 **Monitoring & Analytics**

### **Built-in Metrics**

```python
from buddy.monitoring import MetricsCollector, PerformanceMonitor

# Setup comprehensive monitoring
metrics = MetricsCollector(
    provider="prometheus",  # or "datadog", "newrelic"
    endpoint="http://prometheus:9090"
)

performance = PerformanceMonitor(
    track_latency=True,
    track_token_usage=True,
    track_tool_calls=True,
    track_memory_usage=True
)

agent = Agent(
    name="MonitoredAgent",
    model=OpenAIChat(id="gpt-4"),
    metrics=metrics,
    performance_monitor=performance
)

# View real-time metrics
print(metrics.get_agent_stats("MonitoredAgent"))
print(performance.get_performance_report())
```

### **Custom Logging**

```python
import logging
from buddy.utils.log import setup_buddy_logging

# Configure structured logging
setup_buddy_logging(
    level=logging.INFO,
    format="json",  # or "detailed", "simple"
    include_trace_id=True,
    include_user_id=True,
    output_file="buddy.log"
)

# Custom logger
logger = logging.getLogger("buddy.custom")

def custom_tool_function(data: str) -> str:
    logger.info("Processing data", extra={"data_length": len(data)})
    # Your logic here
    return result
```

### **Dashboard Integration**

```python
from buddy.monitoring import Dashboard

# Create monitoring dashboard
dashboard = Dashboard(
    name="Buddy AI Dashboard",
    agents=[agent1, agent2, agent3],
    metrics_provider=metrics,
    update_interval=30
)

# Start dashboard server
dashboard.start(host="0.0.0.0", port=3000)
# Access at: http://localhost:3000
```

---

## 🧪 **Testing**

### **Unit Testing Agents**

```python
import pytest
from buddy import Agent
from buddy.models.openai import OpenAIChat
from buddy.tools.calculator import CalculatorTools

@pytest.fixture
def test_agent():
    return Agent(
        name="TestAgent",
        model=OpenAIChat(id="gpt-3.5-turbo"),
        tools=[CalculatorTools()],
        instructions="You are a test agent."
    )

def test_agent_basic_response(test_agent):
    response = test_agent.run("Hello")
    assert response.content is not None
    assert len(response.content) > 0

def test_agent_calculation(test_agent):
    response = test_agent.run("What is 2+2?")
    assert "4" in response.content

@pytest.mark.asyncio
async def test_agent_async(test_agent):
    response = await test_agent.arun("Calculate 10*5")
    assert "50" in response.content
```

### **Integration Testing**

```python
import pytest
from buddy import Team, Agent
from buddy.models.openai import OpenAIChat

@pytest.fixture
def test_team():
    agent1 = Agent(name="Agent1", model=OpenAIChat(id="gpt-3.5-turbo"))
    agent2 = Agent(name="Agent2", model=OpenAIChat(id="gpt-3.5-turbo"))
    return Team(name="TestTeam", agents=[agent1, agent2])

def test_team_workflow(test_team):
    result = test_team.run("Simple test task")
    assert result is not None
    assert hasattr(result, 'content')
```

### **Mock Testing**

```python
from unittest.mock import Mock, patch
from buddy import Agent
from buddy.models.base import Model

def test_agent_with_mock_model():
    mock_model = Mock(spec=Model)
    mock_model.run.return_value = Mock(content="Mocked response")
    
    agent = Agent(
        name="MockAgent",
        model=mock_model,
        instructions="Test agent"
    )
    
    response = agent.run("Test message")
    assert response.content == "Mocked response"
    mock_model.run.assert_called_once()
```

---

## 📖 **Comprehensive Documentation**

### **Getting Started**
- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [Configuration Guide](docs/configuration.md)
- [Environment Setup](docs/environment.md)

### **Core Concepts**
- [Agents Deep Dive](docs/agents.md)
- [Models & Providers](docs/models.md)
- [Tools & Functions](docs/tools.md)
- [Knowledge Management](docs/knowledge.md)
- [Memory Systems](docs/memory.md)

### **Advanced Features**
- [Multi-Agent Teams](docs/teams.md)
- [Workflow Orchestration](docs/workflows.md)
- [Structured Outputs](docs/structured-outputs.md)
- [Custom Tool Development](docs/custom-tools.md)
- [Security & Sandboxing](docs/security.md)

### **Deployment**
- [FastAPI Deployment](docs/deployment/fastapi.md)
- [Docker Deployment](docs/deployment/docker.md)
- [Cloud Deployment](docs/deployment/cloud.md)
- [Chat Platform Integration](docs/deployment/chat-platforms.md)

### **Examples & Tutorials**
- [Customer Support Bot](examples/customer-support.md)
- [Research Assistant](examples/research-assistant.md)
- [Data Analysis Agent](examples/data-analysis.md)
- [Multi-Agent Workflows](examples/multi-agent.md)

---

## 🔧 **API Reference**

### **Core Classes**

#### **Agent**
```python
class Agent:
    def __init__(
        self,
        name: str,
        model: Model,
        instructions: str = None,
        tools: List[Tool] = None,
        knowledge: Knowledge = None,
        memory: Memory = None,
        user_id: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        show_tool_calls: bool = False,
        response_model: BaseModel = None,
        **kwargs
    ):
        """Initialize an intelligent agent."""
        
    def run(self, message: str, **kwargs) -> AgentResponse:
        """Execute agent with message."""
        
    async def arun(self, message: str, **kwargs) -> AgentResponse:
        """Asynchronously execute agent."""
        
    def add_tool(self, tool: Tool) -> None:
        """Add tool to agent."""
        
    def remove_tool(self, tool_name: str) -> None:
        """Remove tool from agent."""
```

#### **Team**
```python
class Team:
    def __init__(
        self,
        name: str,
        agents: List[Agent],
        workflow: str = None,
        memory: Memory = None,
        show_tool_calls: bool = False,
        **kwargs
    ):
        """Initialize a team of agents."""
        
    def run(self, message: str, **kwargs) -> TeamResponse:
        """Execute team workflow."""
        
    def add_agent(self, agent: Agent) -> None:
        """Add agent to team."""
        
    def set_workflow(self, workflow: str) -> None:
        """Set team workflow."""
```

#### **Tool Development**
```python
from buddy.tools.function import Function

def create_custom_tool(name: str, description: str, func: callable) -> Function:
    """Create a custom tool from a function."""
    return Function(
        name=name,
        description=description,
        func=func
    )

# Decorator approach
from buddy.tools.decorator import tool

@tool
def my_custom_tool(param1: str, param2: int) -> str:
    """Description of what this tool does."""
    # Your implementation
    return result
```

### **Model Providers**

```python
# OpenAI
from buddy.models.openai import OpenAIChat
model = OpenAIChat(
    id="gpt-4",
    api_key="your-key",
    temperature=0.7,
    max_tokens=4000,
    organization="org-id"
)

# Anthropic
from buddy.models.anthropic import AnthropicChat
model = AnthropicChat(
    id="claude-3-opus",
    api_key="your-key",
    max_tokens=4000,
    temperature=0.7
)

# Google
from buddy.models.google import GoogleChat
model = GoogleChat(
    id="gemini-pro",
    api_key="your-key",
    temperature=0.5
)
```

---

## 💡 **Best Practices**

### **Agent Design**
1. **Clear Instructions**: Write specific, detailed instructions for your agents
2. **Tool Selection**: Choose the minimum set of tools needed for the task
3. **Error Handling**: Implement proper error handling and fallbacks
4. **Testing**: Thoroughly test agents with various inputs

### **Performance Optimization**
1. **Model Selection**: Choose appropriate models for your use case
2. **Caching**: Implement caching for repeated requests
3. **Streaming**: Use streaming for long responses
4. **Async Operations**: Use async methods for better concurrency

### **Security**
1. **Input Validation**: Always validate user inputs
2. **Sandboxing**: Use sandboxed execution for code tools
3. **Rate Limiting**: Implement rate limiting for production
4. **Secret Management**: Use secure secret management

### **Production Deployment**
1. **Monitoring**: Implement comprehensive monitoring
2. **Logging**: Use structured logging with trace IDs
3. **Error Recovery**: Implement graceful error recovery
4. **Scaling**: Design for horizontal scaling

---

## 🤝 **Contributing**

We welcome contributions from the community! Buddy AI is built by developers, for developers.

### **Development Setup**

```bash
# Clone the repository
git clone https://github.com/esasrir91/buddy-ai.git
cd buddy-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Run type checking
mypy buddy/

# Run linting
black . && isort . && flake8

# Build documentation
cd docs && make html
```

### **Contributing Guidelines**

1. **🔍 Check Issues**: Look for existing issues before creating new ones
2. **🌿 Feature Branches**: Create feature branches for your changes
3. **✅ Tests**: Add tests for new functionality
4. **📝 Documentation**: Update documentation for API changes
5. **🔄 Pull Requests**: Submit PRs with clear descriptions
6. **📋 Code Style**: Follow the existing code style
7. **⚡ Performance**: Consider performance implications

### **Development Workflow**

```bash
# 1. Create feature branch
git checkout -b feature/new-tool

# 2. Make changes and add tests
# Edit files...
pytest tests/test_new_tool.py

# 3. Run quality checks
black . && isort . && flake8
mypy buddy/

# 4. Commit and push
git add .
git commit -m "Add new tool for X functionality"
git push origin feature/new-tool

# 5. Create pull request
# Use GitHub interface to create PR
```

### **Types of Contributions**

- 🐛 **Bug Fixes**: Fix existing issues
- ✨ **New Features**: Add new tools, models, or capabilities
- 📚 **Documentation**: Improve docs, examples, tutorials
- 🔧 **Tools**: Create new tool integrations
- 🧪 **Tests**: Add or improve test coverage
- 🎨 **UI/UX**: Improve playground and interfaces

---

## 📝 **License**

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Sriram Sangeeth Mantha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👨‍💻 **Author & Maintainer**

<div align="center">

### **Sriram Sangeeth Mantha**

*AI Engineer & Framework Developer*

[![Email](https://img.shields.io/badge/Email-sriram.sangeet%40gmail.com-blue.svg)](mailto:sriram.sangeet@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-esasrir91-181717.svg?logo=github)](https://github.com/esasrir91)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5.svg?logo=linkedin)](https://linkedin.com/in/sriram-mantha)

</div>

---

## 🙏 **Support & Community**

<div align="center">

### **Support the Project**

If you find Buddy AI helpful, please consider:

[![⭐ Star on GitHub](https://img.shields.io/badge/⭐-Star%20on%20GitHub-yellow.svg)](https://github.com/esasrir91/buddy-ai)
[![👀 Follow Updates](https://img.shields.io/badge/👀-Follow%20for%20Updates-blue.svg)](https://github.com/esasrir91)
[![🐛 Report Issues](https://img.shields.io/badge/🐛-Report%20Issues-red.svg)](https://github.com/esasrir91/buddy-ai/issues)
[![💬 Join Discussions](https://img.shields.io/badge/💬-Join%20Discussions-green.svg)](https://github.com/esasrir91/buddy-ai/discussions)

### **Community Resources**

| Resource | Description | Link |
|----------|-------------|------|
| 📖 **Documentation** | Complete guides and API reference | [View Docs](https://github.com/esasrir91/buddy-ai/wiki) |
| 💡 **Examples** | Real-world implementations | [Browse Examples](https://github.com/esasrir91/buddy-ai/tree/main/examples) |
| ❓ **FAQ** | Common questions and solutions | [Read FAQ](https://github.com/esasrir91/buddy-ai/blob/main/docs/faq.md) |
| 🎥 **Tutorials** | Video guides and walkthroughs | [Watch Videos](https://github.com/esasrir91/buddy-ai/blob/main/docs/videos.md) |
| 🔧 **Tools** | Community-contributed tools | [Explore Tools](https://github.com/esasrir91/buddy-ai/tree/main/community-tools) |

</div>

---

## 🚀 **What's Next?**

### **Upcoming Features**

- 🧠 **Advanced Reasoning**: Enhanced chain-of-thought capabilities
- 🔌 **Plugin System**: Extensible plugin architecture
- 🌐 **Multi-Language**: Support for non-English languages
- 📱 **Mobile SDKs**: React Native and Flutter support
- 🎯 **Fine-tuning**: Built-in model fine-tuning capabilities
- 🔄 **Workflow Designer**: Visual workflow builder
- 📊 **Advanced Analytics**: Enhanced monitoring and insights

### **Roadmap**

- **Q1 2024**: Plugin system and enhanced reasoning
- **Q2 2024**: Mobile SDKs and multi-language support
- **Q3 2024**: Visual workflow designer
- **Q4 2024**: Enterprise features and fine-tuning

---

<div align="center">

**Made with ❤️ by the Buddy AI Team**

*Empowering developers to build the future of AI applications*

[![Built with Python](https://img.shields.io/badge/Built%20with-Python-3776AB.svg?logo=python)](https://python.org)
[![Powered by AI](https://img.shields.io/badge/Powered%20by-AI-FF6B6B.svg)](https://github.com/esasrir91/buddy-ai)
[![Open Source](https://img.shields.io/badge/Open%20Source-❤️-red.svg)](https://opensource.org)

**Ready to build something amazing? [Get started now!](#-quick-start)**

</div>
