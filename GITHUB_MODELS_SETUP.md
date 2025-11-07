# GitHub Models Setup Guide (FREE Alternative)

## Overview

GitHub Models provides **free access** to state-of-the-art AI models including GPT-4o, Llama 3.1, and Phi-3. This is an excellent alternative to Groq for the QA Compliance Assistant.

---

## Available Models (November 2025)

| Model | Provider | Best For | Free Tier Limit |
|-------|----------|----------|-----------------|
| **gpt-4o-mini** ⭐ | OpenAI | General use, fast | 150 req/day |
| **gpt-4o** | OpenAI | Complex reasoning | 50 req/day |
| **Llama-3.1-70B-Instruct** | Meta | Open source, compliance | 100 req/day |
| **Llama-3.1-405B-Instruct** | Meta | Largest open model | 50 req/day |
| **Phi-3-medium-128k-instruct** | Microsoft | Long context | 200 req/day |
| **Mistral-large** | Mistral AI | Structured output | 50 req/day |
| **Cohere-command-r-plus** | Cohere | RAG tasks | 100 req/day |

**⭐ Recommended:** `gpt-4o-mini` for best balance of quality, speed, and rate limits.

---

## Setup Instructions

### Step 1: Get Your GitHub Token

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `QA Compliance Assistant`
4. Select scopes:
   - ✅ **`repo`** (if using private repos)
   - ✅ **`read:org`** (optional)
   - **Note:** GitHub Models doesn't require special scopes, standard token works
5. Click **"Generate token"**
6. **Copy the token** (you won't see it again!)

### Step 2: Configure Azure Container App

Run in Azure Cloud Shell:

```bash
# Set environment variables
az containerapp update \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --set-env-vars \
    "LLM_PROVIDER=github" \
    "GITHUB_TOKEN=ghp_your_token_here" \
    "GITHUB_MODEL=gpt-4o-mini"
```

### Step 3: Verify Configuration

```bash
# Check if variables are set
az containerapp show \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --query "properties.template.containers[0].env[?name=='LLM_PROVIDER' || name=='GITHUB_MODEL']" \
  --output table
```

### Step 4: Test the AI Assistant

1. Login to your application
2. Go to **AI Compliance Assistant** page
3. Upload a document or ask a question
4. You should see responses powered by GitHub Models!

---

## Configuration Options

### Option 1: GitHub Models (Recommended for DEV)

```bash
LLM_PROVIDER=github
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_MODEL=gpt-4o-mini  # or gpt-4o, Llama-3.1-70B-Instruct
```

**Pros:**
- ✅ **FREE** (generous rate limits)
- ✅ GPT-4 quality
- ✅ No credit card required
- ✅ Good for development/testing

**Cons:**
- ❌ Rate limits (150 req/day for gpt-4o-mini)
- ❌ Requires GitHub account

---

### Option 2: Groq (Fast & Free)

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
```

**Pros:**
- ✅ **FREE** (30 req/min, 14,400/day)
- ✅ Very fast inference
- ✅ Good for high-volume testing

**Cons:**
- ❌ Some models deprecated frequently
- ❌ Quality varies by model

---

### Option 3: OpenAI (Production)

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

**Pros:**
- ✅ Highest quality
- ✅ Most reliable
- ✅ Best for production

**Cons:**
- ❌ **PAID** ($0.15 per 1M input tokens)
- ❌ Requires credit card

---

## Model Selection Guide

### For Development/Testing:
```bash
GITHUB_MODEL=gpt-4o-mini  # Best balance
```

### For Complex Compliance Analysis:
```bash
GITHUB_MODEL=gpt-4o  # Higher quality, slower
```

### For Privacy/Open Source:
```bash
GITHUB_MODEL=Llama-3.1-70B-Instruct  # Meta's model
```

### For Long Documents (>100K tokens):
```bash
GITHUB_MODEL=Phi-3-medium-128k-instruct  # 128K context window
```

---

## Rate Limits & Cost Optimization

### Monitor Usage

GitHub Models tracks usage on your GitHub account:
1. Go to https://github.com/settings/copilot
2. View **"GitHub Models"** section
3. See usage stats

### Optimize for Rate Limits

**If hitting limits:**

1. **Switch models:**
   ```bash
   # From gpt-4o (50/day) to gpt-4o-mini (150/day)
   az containerapp update ... --set-env-vars "GITHUB_MODEL=gpt-4o-mini"
   ```

2. **Enable caching:**
   - System already caches conversation context
   - Reduces redundant API calls

3. **Use multiple providers:**
   ```bash
   # Primary: GitHub Models
   # Fallback: Groq (if GitHub rate limit hit)
   ```

4. **Implement queue:**
   - For batch processing, queue requests
   - Spread across 24 hours

---

## Troubleshooting

### Error: "401 Unauthorized"

**Cause:** Invalid or expired GitHub token

**Solution:**
```bash
# Generate new token and update
az containerapp update \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --set-env-vars "GITHUB_TOKEN=ghp_NEW_TOKEN"
```

### Error: "429 Too Many Requests"

**Cause:** Rate limit exceeded

**Solutions:**
1. Wait for reset (limits reset every 24 hours)
2. Switch to different model
3. Add Groq as fallback:
   ```bash
   # Set fallback provider
   az containerapp update ... --set-env-vars \
     "LLM_PROVIDER=groq" \
     "GROQ_API_KEY=gsk_xxx"
   ```

### Error: "Model not found"

**Cause:** Typo in model name

**Solution:**
```bash
# Use exact model name (case-sensitive)
GITHUB_MODEL=gpt-4o-mini
# NOT: GPT-4o-mini or gpt4omini
```

### AI Assistant Returns HTML Instead of JSON

**Cause:** API routing issue or authentication

**Solution:**
1. Check logs:
   ```bash
   az containerapp logs show --name ca-api-qca-dev --resource-group rg-qca-dev --tail 50
   ```

2. Verify environment variables are set
3. Restart container app

---

## Performance Comparison

| Model | Speed | Quality | Cost | Rate Limit |
|-------|-------|---------|------|------------|
| **gpt-4o-mini** | Fast | Excellent | Free | 150/day |
| **gpt-4o** | Medium | Best | Free | 50/day |
| **Llama-3.1-70B** | Medium | Very Good | Free | 100/day |
| **Phi-3-medium** | Very Fast | Good | Free | 200/day |
| **groq/llama-3.1** | Fastest | Good | Free | 14,400/day |

---

## Production Recommendations

### For DEV Environment:
```bash
LLM_PROVIDER=github
GITHUB_MODEL=gpt-4o-mini
```

### For STAGING:
```bash
LLM_PROVIDER=github
GITHUB_MODEL=gpt-4o  # Better quality for testing
```

### For PRODUCTION:
```bash
LLM_PROVIDER=openai  # Most reliable
OPENAI_MODEL=gpt-4o-mini
```

Or keep GitHub Models with higher limits:
```bash
# Use organization token for higher limits
LLM_PROVIDER=github
GITHUB_TOKEN=ghp_ORG_TOKEN  # Org tokens have higher limits
GITHUB_MODEL=gpt-4o-mini
```

---

## Example: Switching Providers

### Switch to GitHub Models:
```bash
az containerapp update \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --set-env-vars \
    "LLM_PROVIDER=github" \
    "GITHUB_TOKEN=ghp_xxxxxxxxxxxxx" \
    "GITHUB_MODEL=gpt-4o-mini"
```

### Switch Back to Groq:
```bash
az containerapp update \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --set-env-vars \
    "LLM_PROVIDER=groq"
```

### Switch to OpenAI (Paid):
```bash
az containerapp update \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --set-env-vars \
    "LLM_PROVIDER=openai" \
    "OPENAI_API_KEY=sk-xxxxxxxxxxxxx" \
    "OPENAI_MODEL=gpt-4o-mini"
```

---

## FAQ

**Q: Is GitHub Models really free?**
A: Yes! Free tier with generous rate limits. No credit card required.

**Q: Which model is best for compliance tasks?**
A: `gpt-4o-mini` for balanced performance, or `gpt-4o` for complex analysis.

**Q: Can I use multiple providers simultaneously?**
A: Not currently, but we can implement fallback logic.

**Q: What happens if I hit rate limits?**
A: Requests will fail with 429 error. Switch providers or wait for reset.

**Q: How do I check my usage?**
A: Go to https://github.com/settings/copilot → GitHub Models section

---

## Next Steps

1. **Get GitHub Token:** https://github.com/settings/tokens
2. **Configure Container App** with environment variables
3. **Test AI Assistant** in your application
4. **Monitor usage** and adjust model as needed

For questions, see the main `FREE_LLM_SETUP.md` guide.
