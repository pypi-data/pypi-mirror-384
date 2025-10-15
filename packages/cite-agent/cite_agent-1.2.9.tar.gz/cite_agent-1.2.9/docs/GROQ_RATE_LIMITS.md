# Groq API - Rate Limits and Model Specifications

**Source**: Groq Console Documentation (console.groq.com)  
**Last Updated**: Q4 2025

---

## 🎯 Discovery Endpoint

**Get all live models**:
```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

This returns the **complete** current model list (IDs change weekly).

---

## 📊 Rate Limits Overview

Groq uses **per-model, per-tier** rate limiting:

| Tier | Rate Limit | Notes |
|------|------------|-------|
| **Free** | 14,400 requests/day | Per API key |
| **Pay-as-you-go** | Higher limits | Based on usage |
| **Enterprise** | Custom | Contact sales |

### Free Tier Details
- **14,400 requests per day** per API key
- **30 RPM** (requests per minute) for most models
- **6,000 RPM** for faster models (like 8B instant)
- Resets at midnight UTC

### Multiple Keys Strategy
- Each key has independent rate limit
- 4 keys = 57,600 requests/day
- Round-robin to distribute load

---

## 🤖 Model Families

### 1. Meta Llama (Production)

#### llama-3.3-70b-versatile
- **Type**: Chat
- **Context**: 131,072 tokens
- **Rate Limit**: 30 RPM (free tier)
- **Speed**: Fast (~100 tokens/sec)
- **Use**: General queries, high quality
- **Cost**: $0.59/1M input, $0.79/1M output

#### llama-3.1-8b-instant  
- **Type**: Chat
- **Context**: 131,072 tokens
- **Rate Limit**: 6,000 RPM (free tier)
- **Speed**: Ultra-fast (~500 tokens/sec)
- **Use**: Simple queries, speed critical
- **Cost**: $0.05/1M input, $0.08/1M output

#### llama-guard-4-12b
- **Type**: Guardrail/Safety
- **Context**: 131,072 tokens
- **Use**: Content moderation
- **ID**: `meta-llama/llama-guard-4-12b`

---

### 2. Meta Llama 4 (Preview)

#### llama-4-maverick-17b-128e-instruct
- **Type**: Chat (Preview)
- **Context**: 131,072 tokens
- **Status**: Preview/Beta
- **ID**: `meta-llama/llama-4-maverick-17b-128e-instruct`

#### llama-4-scout-17b-16e-instruct
- **Type**: Chat (Preview)
- **Context**: 131,072 tokens
- **Status**: Preview/Beta
- **ID**: `meta-llama/llama-4-scout-17b-16e-instruct`

---

### 3. OpenAI Models (Production)

#### gpt-oss-120b
- **Type**: Chat
- **Context**: 131,072 tokens
- **Rate Limit**: 30 RPM (free tier)
- **Use**: High-quality reasoning
- **ID**: `openai/gpt-oss-120b`

#### gpt-oss-20b
- **Type**: Chat
- **Context**: 131,072 tokens
- **Rate Limit**: 30 RPM (free tier)
- **Use**: Balanced quality/speed
- **ID**: `openai/gpt-oss-20b`

---

### 4. Moonshot AI (Preview)

#### kimi-k2-instruct-0905
- **Type**: Chat (Preview)
- **Context**: 262,144 tokens (largest!)
- **Use**: Very long context tasks
- **ID**: `moonshotai/kimi-k2-instruct-0905`

---

### 5. Qwen (Preview)

#### qwen3-32b
- **Type**: Chat (Preview)
- **Context**: 131,072 tokens
- **Use**: Multilingual, coding
- **ID**: `qwen/qwen3-32b`

---

### 6. Audio Models (Production)

#### whisper-large-v3
- **Type**: ASR (Speech-to-Text)
- **Max File**: 100 MB
- **Use**: High-quality transcription
- **ID**: `whisper-large-v3`

#### whisper-large-v3-turbo
- **Type**: ASR (Speech-to-Text)
- **Max File**: 100 MB
- **Use**: Fast transcription
- **ID**: `whisper-large-v3-turbo`

---

### 7. Systems/Agentic (Compound)

#### groq/compound
- **Type**: Agentic System
- **Context**: 131,072 tokens
- **Use**: Multi-step reasoning
- **ID**: `groq/compound`

#### groq/compound-mini
- **Type**: Agentic System
- **Context**: 131,072 tokens
- **Use**: Lighter agentic tasks
- **ID**: `groq/compound-mini`

---

## 🎯 Recommended Model Selection

### For Nocturnal Archive

**Primary**: `llama-3.3-70b-versatile`
- Best quality for research queries
- Good speed (100 tok/sec)
- 131K context for long papers

**Fast Queries**: `llama-3.1-8b-instant`
- Simple fact lookups
- Ultra-fast (500 tok/sec)
- Use for quick questions

**Vision** (if needed later):
- Groq supports vision via Llama models
- See: console.groq.com/docs/vision

---

## 💡 Rate Limit Optimization

### Strategy 1: Multiple Keys (What You're Doing)
```
4 keys × 14,400 req/day = 57,600 req/day
```

### Strategy 2: Model Selection
- Use 8B for simple queries (6,000 RPM vs 30 RPM!)
- Use 70B only for complex questions
- Saves rate limit budget

### Strategy 3: Request Batching
- Combine multiple questions in one request
- Use conversation history
- Reduces total requests

### Strategy 4: Caching
- Cache common queries
- Cache paper summaries
- Reduces API calls

---

## 📈 Calculating Your Capacity

### With 4 Groq Keys (70B Model)

**Assumptions**:
- 25,000 tokens/day per user
- ~850 tokens per query average
- 29 queries per user per day

**Calculation**:
```
57,600 requests/day ÷ 29 queries/user = 1,986 users
```

### With Smart Model Selection

**Use 8B for 50% of queries** (simple questions):
- 8B: 28,800 queries at 6,000 RPM
- 70B: 28,800 queries at 30 RPM
- Total: 57,600 queries/day
- Capacity: **1,986 users** (same, but faster!)

---

## 🔧 Implementation in Your Backend

Your `llm_providers.py` already handles this:

```python
providers['groq'] = ProviderConfig(
    name='groq',
    keys=groq_keys,  # Your 4 keys
    endpoint='https://api.groq.com/openai/v1/chat/completions',
    models=[
        'llama-3.3-70b-versatile',    # Quality
        'llama-3.1-8b-instant'         # Speed
    ],
    rate_limit_per_day=14400  # Per key
)
```

**Auto-rotate** through keys:
```python
key = provider.keys[provider.current_key_index]
provider.current_key_index = (provider.current_key_index + 1) % len(provider.keys)
```

---

## 🚨 Rate Limit Error Handling

When you hit a limit:

```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "code": 429
  }
}
```

**Your code handles this** by trying the next key:
```python
except Exception as e:
    if "rate limit" in str(e).lower():
        # Try next key
        continue
```

---

## 📊 Monitoring Rate Limits

### Check Headers
Groq returns rate limit info in response headers:
```
X-RateLimit-Limit-Requests: 30
X-RateLimit-Remaining-Requests: 29
X-RateLimit-Reset-Requests: 2025-10-08T12:00:00Z
```

### Track in Database
```sql
SELECT 
  DATE(timestamp) as date,
  model,
  COUNT(*) as queries,
  COUNT(*) FILTER (WHERE error LIKE '%rate limit%') as rate_limited
FROM queries
GROUP BY date, model
ORDER BY date DESC;
```

---

## 🎯 Best Practices

1. **Use Multiple Keys**: 4 keys = 4x capacity
2. **Smart Model Selection**: 8B for simple, 70B for complex
3. **Cache Aggressively**: Reduce duplicate queries
4. **Monitor Usage**: Track per-key usage
5. **Implement Fallback**: Use Cerebras/Cloudflare when rate limited
6. **Sync Models Weekly**: Model IDs change, use discovery endpoint

---

## 📚 Resources

- **Models List**: https://console.groq.com/docs/models
- **API Reference**: https://console.groq.com/docs/api-reference
- **Vision Support**: https://console.groq.com/docs/vision
- **Rate Limits**: https://console.groq.com/settings/limits

---

## 🔄 Model Discovery Code

Auto-sync latest models on startup:

```python
async def sync_groq_models():
    """Fetch latest Groq models"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
        )
        models = response.json()
        
        # Cache to database
        for model in models['data']:
            await cache_model(
                provider='groq',
                model_id=model['id'],
                context_length=model.get('context_window', 131072)
            )
```

---

**Summary**: With 4 Groq keys, you have 57,600 req/day = 1,986 users capacity for FREE!

