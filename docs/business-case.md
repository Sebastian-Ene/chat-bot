**Objective**

Your task is to design and implement a Proof of Concept (PoC) for a customer support conversational AI chatbot. While this is a PoC, the focus should be on high‑quality implementation, sound architectural decisions, and production‑aware thinking.

**Functional Requirements**

- Implement a chatbot capable of answering customer support questions based on provided documentation.

- The solution must ingest, process, and index documentation into a local vector database.

- Supported document formats:

  - PDF

  - DOCX

  - HTML

- Documents may contain:

  - Unstructured text

  - Mixed layouts

  - Embedded information that requires careful processing (tables & images)

- The solution must support both German and English content.

- You are free to choose the document understanding technology (e.g. OCR, parsing, multimodal approaches) and should justify your decision.

**Retrieval & LLM Integration**

- Select and justify an appropriate:

  - Embedding model

  - Chunking strategy

  - LLM for retrieval

- Integrate a Large Language Model (LLM) via API.

- Implement prompt guardrails, including but not limited to:

  - Protection against prompt injection

  - Clear system instructions and role separation

  - Constraints to keep responses aligned with the provided knowledge base

- The chatbot must deliver:

  - High answer accuracy

  - Consistent and reliable behavior

  - Predictable response quality

**Performance & Concurrency Constraints**

- The backend must support concurrent access (multiple users at the same time).

- You are expected to think about and implement measurements (e.g. logging, timing, metrics) that help ensure good performance.

- Target performance constraint:

  - A single completion should not exceed 5 seconds under normal conditions.

- You do not need to achieve perfect optimization, but your design should clearly show performance awareness.

**Technical Requirements**

- Primary programming language: Python  
  You may use any libraries or frameworks you consider appropriate.

- Apply clean architecture and clean code principles.

  - A microservices-based approach is allowed if it adds clarity or value.

- Implement:

  - A backend containing all AI, retrieval, and orchestration logic

  - A frontend UI connected to the backend

**Frontend Requirements**

- Any technology that renders HTML is allowed.

- Streamlit is not allowed.

- The UI must:

  - Provide a simple chat interface

  - Support streaming responses from the backend

- Visual polish is not required. A minimal, functional chat UI is sufficient.

**Security Considerations**

- Full user authentication is not required.

- Security can be handled at a basic level, but the following is mandatory:

  - Proper API key and secret management

  - No hard‑coded credentials in source code

- Any additional security considerations you include should be documented.

**Documentation & AI Usage Transparency**

- Provide brief but clear documentation covering:

  - Architecture overview

  - Key design decisions and trade‑offs

  - Chosen models, tools, and technologies

- You **must** use any AI assistant during the implementation.

- It is mandatory to include:

  - All prompts used during development

  - Relevant interaction traces with the LLM that contributed to the final solution

**Scope Clarification**

- This assignment is a PoC, not a full production system.

- Emphasis is on:

  - Code quality

  - Architectural reasoning

  - AI system design

  - Clear, explainable decisions  
    rather than feature completeness or UI polish.

- Please provide the whole project in a single zip file.

- In the second interview you have to present your solution.
