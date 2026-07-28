# Backend

FastAPI modular-monolith backend for the reservation chatbot.

Run commands from the repository root with `make dev-backend`, `make migrate`,
or the quality commands documented in the root README.

The preferred database is a local MySQL instance configured through
`DATABASE_URL`. A Compose-hosted MySQL is compatible with the same URL while
the backend runs on the host; use hostname `mysql` only when the backend also
runs inside the Compose network.

Conversation state, ordered message history, and reservation drafts are stored
in MySQL. Masked conversation evidence is appended to the configured
`CONVERSATION_LOG_DIR`.
