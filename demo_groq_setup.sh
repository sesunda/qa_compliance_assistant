#!/bin/bash

echo "🚀 QCA Free LLM Setup Demo"
echo "=========================="
echo ""

echo "📋 Current Provider Status:"
echo "curl http://localhost:8000/rag/provider-info"
echo ""

echo "🔑 To set up Groq (Free & Fast):"
echo "1. Get API key from: https://console.groq.com/"
echo "2. Run these commands:"
echo ""
echo "   export GROQ_API_KEY=\"gsk_your-api-key-here\""
echo "   export LLM_PROVIDER=\"groq\""
echo "   docker-compose restart api"
echo ""

echo "🏠 To set up Ollama (Completely Free):"
echo "1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
echo "2. Download model: ollama pull llama2"
echo "3. Start server: ollama serve"
echo "4. Configure QCA:"
echo ""
echo "   export LLM_PROVIDER=\"ollama\""
echo "   export OLLAMA_BASE_URL=\"http://localhost:11434\""
echo "   docker-compose restart api"
echo ""

echo "💰 Cost Comparison:"
echo "   Groq:    FREE (30 req/min, 6000/day)"
echo "   Ollama:  FREE (unlimited, local)"
echo "   OpenAI:  PAID (~$0.002 per request)"
echo ""

echo "🧪 Test after setup:"
echo "   ./test_api.sh"
echo "   # or visit http://localhost:3000"
echo ""

echo "📖 Full guide: ./FREE_LLM_SETUP.md"