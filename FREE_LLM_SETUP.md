# Free LLM Provider Setup Guide

This guide shows you how to set up free alternatives to avoid OpenAI charges.

## 🚀 **Recommended: Groq (Free & Fast)**

Groq offers excellent free tier with very fast inference:

### **Free Tier Limits:**
- ✅ **30 requests per minute**
- ✅ **6,000 requests per day** 
- ✅ **No monthly limits**
- ✅ **Very fast response times**

### **Setup Steps:**

1. **Get API Key:**
   - Go to https://console.groq.com/
   - Create a free account
   - Navigate to API Keys section
   - Create a new API key

2. **Configure Environment:**
   ```bash
   export GROQ_API_KEY="gsk_your-api-key-here"
   export LLM_PROVIDER="groq"
   ```

3. **Update Docker Environment:**
   ```bash
   # Add to your .env file
   GROQ_API_KEY=gsk_your-api-key-here
   LLM_PROVIDER=groq
   ```

4. **Restart Services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### **Available Models:**
- `llama3-8b-8192` (recommended, fast)
- `mixtral-8x7b-32768` (larger context)
- `gemma-7b-it` (Google's model)

---

## 🏠 **Completely Free: Ollama (Local)**

Run models locally with no API limits:

### **Benefits:**
- ✅ **Completely free**
- ✅ **No rate limits**
- ✅ **Privacy - runs locally**
- ✅ **No internet required**

### **Setup Steps:**

1. **Install Ollama:**
   ```bash
   # On macOS
   brew install ollama
   
   # On Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # On Windows
   # Download from https://ollama.ai/download
   ```

2. **Download a Model:**
   ```bash
   ollama pull llama2
   # or
   ollama pull codellama
   ollama pull mistral
   ```

3. **Start Ollama Server:**
   ```bash
   ollama serve
   ```

4. **Configure QCA:**
   ```bash
   export LLM_PROVIDER="ollama"
   export OLLAMA_BASE_URL="http://localhost:11434"
   export OLLAMA_MODEL="llama2"
   ```

---

## 🔮 **Alternative: Anthropic Claude**

Claude offers some free credits for new users:

### **Setup Steps:**

1. **Get API Key:**
   - Go to https://console.anthropic.com/
   - Create account and get free credits
   - Generate API key

2. **Configure:**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   export LLM_PROVIDER="anthropic"
   ```

---

## 🛠 **Quick Setup Commands**

### **For Groq (Recommended):**
```bash
# Set environment variables
export GROQ_API_KEY="your-groq-key"
export LLM_PROVIDER="groq"

# Restart QCA
cd /workspaces/qa_compliance_assistant
docker-compose down
docker-compose up -d
```

### **Test the Setup:**
```bash
# Check provider status
curl -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')" \
  http://localhost:8000/rag/provider-info | jq .

# Test RAG query
curl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are access controls?"}' \
  http://localhost:8000/rag/ask | jq .answer
```

---

## 📊 **Provider Comparison**

| Provider | Cost | Speed | Rate Limits | Setup Difficulty |
|----------|------|--------|-------------|------------------|
| **Groq** | Free | Very Fast | 30/min, 6k/day | Easy |
| **Ollama** | Free | Medium | None | Medium |
| **Anthropic** | Limited Free | Fast | Limited credits | Easy |
| **OpenAI** | Paid | Fast | Depends on plan | Easy |

---

## 🎯 **Recommendation**

**For development and demos:** Use **Groq** - it's free, fast, and has generous limits.

**For production with privacy concerns:** Use **Ollama** locally.

**For production with budget:** Consider OpenAI's pay-per-use pricing.

---

## 🔍 **Verification**

After setup, you can verify the provider is working by:

1. **Check logs:** `docker-compose logs api | grep "initialized successfully"`
2. **Test endpoint:** Visit http://localhost:8000/rag/provider-info
3. **Try RAG query:** Use the AI Assistant in the frontend

The system will automatically fall back to mock responses if no provider is configured.