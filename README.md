# Streamlit AWS Document Q&A App

A RAG (Retrieval-Augmented Generation) app that lets you ask questions about your PDF documents using Amazon Bedrock Knowledge Bases and a large language model.

---

## Prerequisites

- Python 3.8+
- An AWS account with the following set up:
  - A Bedrock Knowledge Base (managed type) with your PDFs ingested
  - Access to a Bedrock LLM (e.g. `eu.amazon.nova-lite-v1:0`)
  - An IAM user with permissions for `bedrock-agent-runtime`, `bedrock-runtime`, and `s3`
  - An S3 bucket containing your PDF source documents

---

## Setup & Run

### Option 1: Local (virtualenv)

**1. Clone the repo and navigate to the project folder:**
```bash
cd Streamlit-AWS-Document-QA-App
```

**2. Create and activate a virtual environment:**
```bash

python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install streamlit boto3 python-dotenv
```

**4. Create a `.env` file in the project root:**
```
AWS_ACCESS_KEY_ID=<your-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
AWS_REGION=eu-central-1
KB_ID=<your-knowledge-base-id>
MODEL_ID=eu.amazon.nova-lite-v1:0
```

> ⚠️ Never commit `.env` to version control. Add it to `.gitignore`.

**5. Run the app:**
```bash
streamlit run app.py
```

**6. Open your browser at:**
```
http://localhost:8501
```

---

### Option 2: Docker

**1. Create a `.env` file in the project root** (same as above).

**2. Build the image:**
```bash
docker build -t doc-qa .
```

**3. Run the container:**
```bash
docker run -p 8501:8501 --env-file .env doc-qa
```

**4. Open your browser at:**
```
http://localhost:8501
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                         │
│                     (browser / localhost)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ user question
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         app.py                              │
│                                                             │
│   1. retrieve()              2. converse()                  │
│        │                          │                         │
│        ▼                          ▼                         │
│  ┌───────────────┐     ┌─────────────────────┐             │
│  │    Bedrock    │     │      Bedrock         │             │
│  │  Knowledge    │     │      Runtime         │             │
│  │     Base      │     │   (Nova Lite LLM)    │             │
│  └───────┬───────┘     └──────────┬──────────┘             │
│          │ chunks [1][2][3]        │ answer + citations     │
│          └──────────┬─────────────┘                        │
│                     │                                       │
│              3. presign()                                   │
│                     │                                       │
│                     ▼                                       │
│              ┌─────────────┐                               │
│              │  Amazon S3  │                               │
│              │  (PDF docs) │                               │
│              └─────────────┘                               │
└─────────────────────────────────────────────────────────────┘
                          │ answer + source links
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                         │
│              displays reply with clickable links            │
└─────────────────────────────────────────────────────────────┘
```

## Flow

1. User asks a question → `retrieve()` fetches relevant PDF chunks from the Knowledge Base
2. Chunks + question are sent to Nova Lite via `converse()` → generates a cited answer
3. `presign()` generates temporary S3 URLs for the source documents
4. Streamlit renders the answer with clickable source links
