![POMA AI Logo](https://raw.githubusercontent.com/poma-ai/.github/main/assets/POMA_AI_Logo_Pink.svg)
# 📚 POMA: Preserving Optimal Markdown Architecture

## 🚀Quick-Start Guide

### Installation

Requires Python 3.10+. Install the core packages:
```bash
pip install poma
```

For integrations into LangChain and LlamaIndex:
```bash
pip install poma[integrations]
# Or LangChain/LlamaIndex including example extras:
pip install poma[integration-examples]
```


- You may also want: `pip install python-dotenv` to load API keys from a .env file.
- API keys required (POMA_API_KEY) for the POMA AI client via environment variables.
- **To request a POMA_API_KEY, please contact us at api@poma-ai.com**


### Example Implementations — all examples, integrations, and additional information can be found in our GitHub repository: [poma-ai/poma](https://github.com/poma-ai/)

We provide four example implementations to help you get started with POMA AI:
- example.py — A standalone implementation for documents, showing the basic POMA AI workflow with simple keyword-based retrieval
- example_langchain.py — Integration with LangChain, demonstrating how easy it is to use POMA AI with LangChain
- example_llamaindex.py — Integration with LlamaIndex, showing how simple it is to use POMA AI with LlamaIndex

*Note: The integration examples use OpenAI embeddings. Make sure to set your OPENAI_API_KEY environment variable, or replace the embeddings with your preferred ones.*


All examples follow the same two-phase process (ingest → retrieve) but demonstrate different integration options for your RAG pipeline.

! Please do NOT send any sensitive and/or personal information to POMA AI endpoints without having a signed contract & DPA !
