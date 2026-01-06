# 🛒 Supermarket Retention Cloud (Agentic AI)

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Streamlit%20%7C%20Groq%20LLM-blue)
![Architecture](https://img.shields.io/badge/Architecture-Headless%20%26%20Agentic-purple)

> **A "Headless" Loyalty AI Agent that observes customer behavior, diagnoses churn reasons, and autonomously executes win-back campaigns.**

---

## 📖 Overview

This project is a Proof-of-Concept (PoC) for an **Agentic Loyalty Platform**, inspired by the architecture of **Antavo Enterprise Loyalty Cloud**. 

Unlike traditional dashboards that only *show* you who left, this AI Agent **thinks** about *why* they left and **acts** to bring them back. It combines behavioral data (RFM analysis) with sentiment data (customer feedback) to generate hyper-personalized recovery strategies.

### 🌟 Key Features
* **🧠 Agentic Reasoning:** Uses `llama-3.3-70b-versatile` (via Groq) to deduce root causes of churn (e.g., distinguishing between "High Price" vs. "Poor Service").
* **📊 Hybrid Analytics:** Merges hard metrics (Days Since Last Shop) with soft metrics (Sentiment Analysis).
* **⚡ Real-Time "Headless" Architecture:** Built with **FastAPI** (Backend) and **Streamlit** (Frontend), mimicking a modern composable commerce stack.
* **🔄 Campaign Persistence:** Automatically logs all agent decisions and generated emails into an audit trail.

---

## 🏗️ Architecture

The system follows a **Headless AI** pattern, separating the "Brain" (API) from the "Face" (Dashboard):

```mermaid
graph LR
    A[Customer Data] -->|Transactions + Feedback| B(FastAPI Backend);
    B -->|Context + Prompt| C{Groq AI Agent};
    C -->|Strategy JSON| B;
    B -->|API Response| D[Streamlit Dashboard];
    B -->|Log Action| E[(History Log)];
