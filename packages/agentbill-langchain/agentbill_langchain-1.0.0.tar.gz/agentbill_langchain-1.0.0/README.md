# AgentBill LangChain Integration

Automatic usage tracking for LangChain applications.

## Installation

```bash
pip install langchain langchain-openai
# Copy agentbill_langchain/ to your project
```

## Usage

```python
from agentbill_langchain import AgentBillCallback
from langchain_openai import ChatOpenAI

# Initialize callback
callback = AgentBillCallback(
    api_key="agb_...",
    base_url="https://your-instance.supabase.co",
    customer_id="customer-123"
)

# Add to LangChain
llm = ChatOpenAI(callbacks=[callback])
result = llm.invoke("Hello!")  # Auto-tracked!
```