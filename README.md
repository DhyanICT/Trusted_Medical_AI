# TrustMed AI

**Author: Dhyan Patel**

A medical information assistant that combines trusted medical knowledge graphs with community insights to provide comprehensive, evidence-based answers to medical questions.

## Quick Start

**📖 For complete step-by-step setup instructions, see [SETUP_AND_RUN_GUIDE.md](SETUP_AND_RUN_GUIDE.md)**

### Quick Setup Checklist

1. **Install Neo4j** and start a database
2. **Create `.env` file**: `cp .env.example .env` and configure it
3. **Verify setup**: `python code/verify_setup.py`
4. **Start backend** (Terminal 1): `./code/start_backend.sh`
5. **Start UI** (Terminal 2): `./code/start_ui.sh`

## Features

- Trusted disease & treatment information (Mayo-style knowledge graph)
- Drug & supplement monographs (side effects, warnings, interactions)
- Key Recurring Themes (KRTs) from real patient/community discussions
- Links to similar Reddit threads (for human stories)
- Llama-based answer synthesis with clear sections

## Documentation

- **[SETUP_AND_RUN_GUIDE.md](SETUP_AND_RUN_GUIDE.md)** - Complete setup and run instructions
- **[EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)** - Evaluation framework and metrics
- **[COMMUNITY_EXPERIENCES_FLOW.md](COMMUNITY_EXPERIENCES_FLOW.md)** - How community experiences are integrated

## Important Notes

This is **not** a diagnostic tool and does **not** replace a clinician. Always discuss your situation with a licensed healthcare provider.
