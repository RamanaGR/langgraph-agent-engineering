USE case - RAG Project Explanation (Talentscreen)

Business Problem and Why This Solution Was Built
• Recruiters and hiring managers were handling large volumes of candidates and had to search across:
 – Resume PDFs
 – ATS candidate profiles
 – Interview feedback notes
 – Job descriptions
 – Hiring rubrics and guidelines
• The existing keyword search system could not understand meaning, so recruiters:
 – Spent a lot of time searching
 – Compared candidates manually
 – Made inconsistent decisions
• The business goal was to:
 – Reduce time to shortlist
 – Improve candidate evaluation quality
 – Make hiring decisions consistent and explainable
• A proof of concept using embeddings, a vector database, and a simple UI showed strong value to recruiters, which led leadership to approve a full production system

Technical Explanation:

Refined RAG Architecture (Innovapath/TalentScreen)

1. Multi-Modal Ingestion & Orchestration
Source: Resumes (PDF/Docx), Job Descriptions, and Interview Videos/Audio.
Storage: Ingested into Google Cloud Storage (GCS).
Dynamic Pipeline: GCS triggers Cloud Functions for immediate processing:
Docling: Utilized for advanced document parsing and layout-aware chunking (preserving tables/headers).
Media Processing: Speech-to-Text for video/audio interview data.
Vectorization: Text chunks are converted into embeddings and stored in Milvus.
Sentence transformer - embeddings
Semantic Chunking and Overlapping
2. Hybrid Storage & Memory Management
Vector Store: Milvus handles semantic embeddings with strict tenant isolation (ensuring data from Company A never leaks to Company B).
Structured Metadata: PostgreSQL (Cloud SQL) stores structured candidate data, metadata, and document pointers.
Persistence Layer: * Firestore: Stores long-term conversational history and RAG logs for auditability.
Redis: Manages short-term session memory to maintain context within a single user session.
3. Retrieval & Reranking Strategy
Hybrid Search: Combines Vector search (semantic meaning) with Keyword search (specific skills/tools) to ensure precision.
Metadata Filtering: Filters results by specific attributes (e.g., location, years of experience) before semantic calculation.
Reranking: A secondary "cross-encoder" model evaluates the top $N$ retrieved chunks, filtering out "weak evidence" and ensuring only the most relevant context reaches the LLM.
4. Generation Layer (Vertex AI)
Model: Gemini 2.0 Flash (orchestrated via Vertex AI) for high-speed, cost-effective reasoning.
Groundedness & Guardrails: * Strict Output Parsers: Ensures responses are in structured formats (JSON) if needed.
Citation Validation: Only generates answers if the evidence exists in the retrieved chunks.
Bias Masking: Active filtering of PII or sensitive demographic data during the generation phase to ensure fair hiring.
5. Platform & Observability
Compute: Deployment on GKE (Google Kubernetes Engine) for scalable, containerized processing.
Tracing: Langfuse captures the latency of specific retrieval steps and tool calls.
Security: Secret Manager for API keys and Cloud Logging for centralized system health monitoring.


Krishnaik - youtube


Multi-Agent (Agentic AI) Project Explanation
Problem Statement: While the Phase 1 RAG pipeline solved information retrieval, recruiters still faced a bottleneck of manual, multi-step workflows, such as comparing candidates against rubrics, scheduling interviews based on complex availability, and synthesizing feedback from multiple stakeholders.
The Goal: Transition from a "Read-Only" Q&A system to an Agentic AI capable of planning, executing actions, and automating end-to-end hiring workflows with "Human-in-the-Loop" oversight.
Design, Architecture, and End-to-End Flow (Google ADK Focus)
Overall Architecture:
We transitioned to a Hierarchical Multi-Agent Orchestration framework built on Google ADK.
Instead of a flat graph, the system uses ADK’s deterministic routing to manage agent lifecycles and handoffs, ensuring strict boundaries between the "Planner" and "Executor" layers.
We integrated the Phase 1 RAG pipeline as a Reusable Tool within the ADK registry, making it accessible to any agent for grounding.
Orchestrator (Planner-Executor Pattern):
I implemented the Planner-Executor pattern using ADK.
The Planner Agent/coordinator agent accepts high-level goals (e.g., "Find a Java dev and schedule an interview") and decomposes them into a structured list of atomic sub-goals.
The Executor then dynamically routes these sub-goals to the specific agent best suited to handle them, maintaining a clean separation of concerns.
Main Execution Flow:
Intent Classification & Dispatch:
The Orchestrator Agent acts as the ingress, using ADK’s routing logic to classify user intent and dispatch the request to the correct domain context (Hiring, Mobility, or Policy).
Task Decomposition & State:
The execution plan is written to a shared context, persisted in Redis (for session speed) and Firestore (for auditability).
The system identifies required Specialized Agents:
Recruiter Agent: For candidate fit analysis.
Policy Agent: For visa checks.
Scheduling Agent: For calendar API actions.
Agent Execution:
Each agent functions as an autonomous unit within the ADK framework, executing its assigned sub-goal using ReAct-style reasoning.
Agents invoke managed Tools (RAG retrieval, external APIs) and validate their own outputs before reporting back "Goal Achieved."
Synthesis & Human Review:
The Orchestrator aggregates the results from all agents into a final response.
For sensitive actions (like sending an offer), we configured a Human-in-the-Loop gate, pausing the ADK workflow until recruiter approval is received.
Domain Agents
• Resume Analysis Agent
 • Uses structured parsing and RAG to normalize skills and experience
• Candidate Fit Agent
 • Evaluates strengths, gaps, and confidence score versus job description
• Interview Design Assistant Agent
 • Generates role-specific interview questions and avoids repetition
• Feedback Synthesis Agent
 • Merges interviewer notes and detects contradictions
• Bias and Fairness Agent
 • Flags biased language and inconsistent evaluations
• Hiring Decision Agent
 • Aggregates agent outputs and produces explainable recommendations

Communication and Memory Strategy
State Management (Shared Blackboard):
Adopted a Shared Blackboard pattern where agents do not communicate directly.
We utilized Redis as a high-speed "scratchpad" to store the current Execution Plan and atomic task status (e.g., "Pending," "Completed") which the Orchestrator reads to decide the next step.
Tooling & Interfaces:
Standardized tool access using Google ADK’s Tool Registry (Model Context Protocol), ensuring consistent interfaces for APIs (ServiceNow, Gmail) and RAG retrieval across all specialized agents.
Tri-Layer Memory Architecture:
Short-Term (Session): leveraged Google ADK’s native Session Management to maintain immediate conversation history and context variables (like candidate_id) during the active turn.
Mid-Term (Summary): Implemented a background Summarization Service that compresses lengthy ADK session logs into concise summaries to prevent context window overflow.
Long-Term (Semantic): Leveraged Milvus (Vector DB) to store and retrieve semantic memories, allowing agents to recall candidate details or recruiter preferences across different sessions.
Safety, Control, and Evaluation (GCP Native)
Security & Guardrails:
Input Sandboxing: Implemented pre-execution guardrails to block prompt injection and enforce PII masking before data touches the Vertex AI models.
IAM & RBAC: Enforced strict Role-Based Access Control (RBAC) using GCP IAM, ensuring agents could only access specific datasets (e.g., Salary Data vs. Resume Data) authorized for their service account.
Observability & Tracing:
Deployed Langfuse for end-to-end tracing, capturing every Google ADK tool call, latency metric, and agent reasoning step.
Maintained a full audit trail in Cloud Logging for compliance and explainability.
Evaluation Framework (LLM-as-a-Judge):
Utilized LLM-as-a-Judge workflows to score agent responses against "Golden Datasets" of ideal recruiter interactions.
Conducted Ablation Studies to test system resilience specifically measuring how the Orchestrator handles failure when a specialized tool (like the Scheduler) is unavailable.
Tiered Autonomy:
Designed the system with Tiered Autonomy: Low-risk tasks (scheduling) were fully automated, while high-impact decisions (sending offers) triggered a "Human-in-the-Loop" interrupt, pausing the ADK session until recruiter approval was received.






Talentscreen - Graduate AI Research assistant:
I can break my work down into two specific phases:
First, I did a POC on a RAG-based assistant.
Phase 1: The Enterprise RAG System I built the end-to-end pipeline for processing unstructured recruiting data (PDF Resumes, Video Interviews).
Ingestion: I designed an Event-Driven Pipeline on Google Cloud. 
When Uploads to Cloud Storage trigger Cloud Functions that route files to specific processors (OCR for PDFs, Speech-to-Text for videos). 
I used Docling for preprocessing to strictly preserve complex table structures in resumes.
Retrieval: I implemented a Hybrid Retriever (Semantic + Keyword) using Milvus as the Vector DB and Sentence Transformers for embeddings.
Generation: We used Vertex AI (Gemini 2.0 Flash) as the reasoning engine, orchestrated via LangChain.
Evaluation: I implemented 'LLM-as-a-Judge' pipelines to evaluate retrieval quality against ground truth datasets.
Full Stack: The application runs on React (Frontend) - StreamLit and FastAPI (Backend), deployed on GCP GKE (Kubernetes) for scalability.
Phase 2: The Agentic Evolution (Current Work) We realized simple RAG wasn't enough for complex reasoning, so I migrated to a Multi-Agent System using Google ADK (implementing the Supervisor/Coordinator Pattern).
Orchestration: I built a 'Router' that detects user intent and delegates tasks to domain-specific agents, specifically:
The Resume Analysis Agent: Which scores and compares candidates.
The Governance Agent: Which ensures compliance and prevents bias.
Memory: I implemented a dual-memory architecture: Redis for short-term conversation state and Milvus for long-term candidate recall.
Tooling (MCP): I used the Model Context Protocol (MCP) to connect agents to our PostgreSQL database. This allows agents to execute read-only SQL queries while strictly enforcing Role-Based Access Control (RBAC) based on the recruiter's permissions."



resume points to jusify :
Graduate AI Research Assistant
Atlantis University
Miami, FL, USA
Jan 2025 – Oct 2025
◦ Built an AI powered talent management platform using Retrieval Augmented Generation and multi agent orchestration
to standardize hiring workflows, reduce bias, and decrease time to hire.
◦ Designed and implemented multi agent workflows in LangGraph, with specialized agents for conversation management,
retrieval, candidate matching, routing, and orchestration.
◦ Developed MCP based tool calling infrastructure by creating custom MCP servers and reusable tools to support agent
actions, external integrations, and workflow execution.
◦ Built a document ingestion and preprocessing pipeline using Unstructured.io and Docling to clean source content,
normalize formats, extract metadata, and prepare enterprise documents for downstream retrieval.
◦ Implemented semantic chunking in Docling with overlap strategies to preserve context across chunks, and generated
embeddings using Amazon Titan Text Embeddings for high quality retrieval.
◦ Engineered a Milvus based vector search layer using collections, metadata filtering, keyword search, and hybrid retrieval;
configured HNSW indexing for low latency approximate nearest neighbor search at scale.
◦ Improved retrieval quality by implementing cross encoder reranking and post retrieval evaluation metrics, including F1
score at K and related ranking measures, to track relevance and system performance.
◦ Built a query optimization pipeline with query rewriting and balancing techniques to improve retrieval precision and
generation quality; integrated Presidio for PII detection and redaction.
◦ Implemented semantic query caching with Redis vector storage to identify similar historical queries and reuse optimized
retrieval paths, reducing latency and compute cost.
◦ Applied advanced prompting strategies, including few shot prompting, dynamic prompting, and structured reasoning
patterns, and used Promptfoo to test and compare prompt performance across tasks.
◦ Used Amazon Bedrock with Claude Sonnet for text generation, and implemented prompt caching to improve response
time and reduce inference costs.
Ramana Gangarao – 1/2
◦ Developed CI and CD based evaluation pipelines with DeepEval to validate faithfulness, context recall, answer relevance,
retrieval quality, and regression safety across RAG and agent workflows before release.
◦ Implemented guardrails for safety and compliance using AWS services and Hugging Face libraries to detect and control
PII exposure, toxicity, and tone related issues.
◦ Developed backend APIs, API Gateway integrations, and a React frontend to deliver recruiter facing and candidate facing
workflows through a scalable full stack application.
◦ Integrated Langfuse for end to end observability, including prompt versioning, tool call tracing, retrieval context tracking,
agent transition monitoring, and latency analysis.

