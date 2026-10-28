#!/bin/bash
PDF_NAME="the-coaches-guide-to-teaching.pdf"
HOST_PDF_DIR="/Users/tahjholden/mppd/basketball"
RESULTS_DIR="/Users/tahjholden/mppd/PageIndex/results"

# Ensure results directory exists
mkdir -p "$RESULTS_DIR"

echo "Checking for PDF..."
if [ ! -f "$HOST_PDF_DIR/$PDF_NAME" ]; then
    echo "Error: PDF not found at $HOST_PDF_DIR/$PDF_NAME"
    exit 1
fi

# Check for .env file and source it
if [ -f "/Users/tahjholden/mppd/.env" ]; then
    echo "Loading .env file..."
    set -a
    source "/Users/tahjholden/mppd/.env"
    set +a
fi

# Map standard OPENAI_API_KEY to PageIndex's CHATGPT_API_KEY if needed
if [ -z "$CHATGPT_API_KEY" ] && [ -n "$OPENAI_API_KEY" ]; then
    echo "Mapping OPENAI_API_KEY to CHATGPT_API_KEY..."
    export CHATGPT_API_KEY="$OPENAI_API_KEY"
fi

# Check for API Key
if [ -z "$CHATGPT_API_KEY" ]; then
    echo "Error: CHATGPT_API_KEY (or OPENAI_API_KEY) environment variable is not set."
    echo "Please set it in /Users/tahjholden/mppd/.env or export it."
    exit 1
fi

echo "Running extraction on $PDF_NAME..."

# Cleanup previous run if exists
docker rm -f pageindex_pilot 2>/dev/null || true

# Run in detached mode to prevent timeouts
echo "Starting extraction container..."
docker run -d \
    --name pageindex_pilot \
    -v "$HOST_PDF_DIR:/data" \
    -v "$RESULTS_DIR:/app/results" \
    -v "/Users/tahjholden/mppd/PageIndex/run_pageindex.py:/app/run_pageindex.py" \
    -e CHATGPT_API_KEY="$CHATGPT_API_KEY" \
    pageindex \
    --pdf_path "/data/$PDF_NAME" \
    --model "gpt-4o-2024-11-20" > "$RESULTS_DIR/container_id.txt"

echo "Container started. Logs available via 'docker logs -f pageindex_pilot'"
# Tail logs for a bit to ensure start
sleep 2
docker logs pageindex_pilot
