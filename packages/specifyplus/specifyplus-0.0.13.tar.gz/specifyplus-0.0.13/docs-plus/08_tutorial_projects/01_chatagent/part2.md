# Step 8: Capstone – SDD Chatbot Project (Part 2)

**Spec 2, Branch 2, PR 2** - NextJS15 + Tailwind + Shadcc + ThreeJS/Framer Implementation

**Goal:** Extend the ChatWait chatbot with a modern, interactive frontend focusing on exceptional UX and visual appeal.

## Overview

This implementation builds upon the backend architecture from Spec 1 (OpenAI Agents SDK + FastAPI) but replaces Chainlit with a sophisticated NextJS15 frontend featuring:
- **NextJS15** with App Router and Server Components
- **Tailwind CSS** for utility-first styling
- **ShadCN/UI** for accessible, customizable components
- **ThreeJS** for 3D visualizations and interactive elements
- **Framer Motion** for smooth animations and micro-interactions

### 1. `/sp.constitution`

Update principles to **favor CLI setup + UX-first flow**:

* Always initialize projects with CLI (`pnpm create next-app@latest`, `pnpm dlx shadcn@latest init`).
* Use **pnpm** package manager (not npm).
* Enforce **UX-first design** (mobile-first layouts, accessibility, animations).
* Minimize boilerplate by leaning on `shadcn/ui`.
* Avoid generating placeholder tests until real UX flows exist.

---

### 2. `/sp.spec`

> Define **what the user experiences**, not file structure.

Example spec:

* User lands on `/chat` → sees responsive chat window.
* Can type messages in input, hit enter/send → message appears instantly in bubble.
* Assistant responds via `/chat/streaming` SSE → token-by-token typing effect.
* Errors (500/network) show inline in chat, not console-only.
* Works smoothly on desktop + mobile.
* Clear entry/exit animations for new messages.

---

### 3. `/sp.clarify`

Ask UX-critical questions:

* Should streaming show a **typing indicator bubble** or raw token-by-token?
* Retry on disconnect: auto or user-triggered?
* Message history: scrollable with auto-scroll to bottom, or static?
* Do we want **session persistence** in v1, or just in-memory?

---

### 4. `/sp.plan`
We are going to implement using nextJS15, Tailwind CSS, ShadCN and Framer Motion. Instead of file dump, generate **step-by-step CLI + integration plan**:

```bash
# Bootstrap app
pnpm create next-app@latest chat-ui --ts --eslint --tailwind --app

# Init shadcn/ui
cd chat-ui
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button input card scroll-area

# Install extras
pnpm add framer-motion
```

Then:

1. Layout: create `app/chat/page.tsx` with `<ChatContainer />`.
2. Components:

   * `ChatInput` (shadcn input + button).
   * `ChatMessage` (variants: user, assistant).
3. Streaming: `useChatStream` hook (SSE → state).
4. Animations: framer-motion for bubble fade/slide-in + typing cursor.
5. Error banner component.
6. E2E test (Playwright) only after UX is working.

---

### 5. `/sp.tasks`

Atomic, UX-first tasks (not tests-first):

1. Bootstrap Next.js + Tailwind + shadcn via CLI.
2. Create chat layout container with responsive design.
3. Implement ChatInput.
4. Implement ChatMessage bubbles with roles.
5. Implement SSE streaming hook.
6. Display assistant messages token-by-token.
7. Add Framer animations.
8. Add error banner.
9. Add reconnect flow.
10. Write minimal e2e test for full chat flow.

Understand first spec to know the API Integration tasks@001-develop-a-scoped/ we will use the stremaing apoi here and username can bt econtext_id used for perssostence

Streaminf Endpoint: /api/v1/chat/streaming

Streaming chat endpoint - returns Server-Sent Events with incremental tokens.

Args: message: User message (required) context_id: Optional conversation context identifier last_token_index: Last token index for reconnection (default: 0)

Returns: StreamingResponse: SSE stream with incremental tokens

### 6. `/sp.analyze`

Now I want you to go and audit the implementation plan and the implementation detail files.
Read through it with an eye on determining whether or not there is a sequence of tasks that you need
to be doing that are obvious from reading this. Because I don't know if there's enough here. For example,
when I look at the core implementation, it would be useful to reference the appropriate places in the implementation
details where it can find the information as it walks through each step in the core implementation or in the refinement.

### 6. `/sp.implement`

## References

- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- PyPI package: https://pypi.org/project/specifyplus/
- Original Spec Kit repo: https://github.com/github/spec-kit