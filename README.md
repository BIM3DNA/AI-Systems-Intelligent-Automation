AI (In Development)– the AI Agent / ModelMind Codex System represents the next generation intelligence core of the BIM3DNA ecosystem — a unified interface where
local AI interference, code synthesis, and autonomous Revit task execution merge into a
single pyRevit environment.
The system now integrates a dedicated “AI Agent” tab within pyRevit, enabling direct
access to local Codex runtime in VS Code for secure Python/C# code generation,
validation, and execution. This two-layered setup bridges user intent, AI reasoning, and
Revit API operations in a fully traceable and offline workflow.
Core Components:

- Ollama Chatbox – a conversational AI workspace powered by locally hosted LLMs
  (e.g. phi3, phi3:mini, gemma, llama3, etc.), designed for general BIM and code
  discussions, quick help, and prompt experimentation.
- ModelMind – a Revit-integrated assistant that interprets user prompts to run
  hardcoded automation commands (e.g., “select all ducts,” “total roof volume,”
  “health check”) or auto-generate new Revit API scripts through AI code synthesis.
- AI Agent Tab – a new extension that connects Revit directly to the VS Code Codex
  environment allowing code generation, static analysis, transaction sandboxing,
  and rollback directly from the chat interface.
  17
  Its unique dual-mode architecture allows real-time collaboration between the AI model
  and the live Revit document (doc, uidoc), enabling both deterministic command
  execution and generative experimentation. Users can review, approve, and execute
  generated code safely within Revit — bridging human intent, AI reasoning, and BIM data
  manipulation.
  Key features include:
- Dynamic model-context retrieval (active document, selected elements,
  categories).
- Safe, isolated execution of AI-generated Python/C# scripts within Revit.
- Automatic detection of invalid or risky API calls via the Codex static analyzer.
- Dual interaction models – Deterministic Commands (known automation) and
  Generative Experiments (code synthesis).
- Local model management and adaptive prompt tuning for higher accuracy.
