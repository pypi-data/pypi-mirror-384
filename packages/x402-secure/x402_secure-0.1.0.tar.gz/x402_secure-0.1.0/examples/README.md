# x402-secure Examples

This directory contains example implementations demonstrating how to use the x402-secure SDK.

## Prerequisites

1. Install dependencies with examples support:
   ```bash
   cd /path/to/packages/x402-secure
   uv pip install -e ".[examples,signing,otel]"
   ```

2. For OpenAI agent example, install additional dependencies:
   ```bash
   uv pip install -e ".[agent]"
   ```

3. Set up environment variables (copy from `../../env.example`):
   ```bash
   cp ../../env.example .env
   # Edit .env with your configuration
   ```

## Examples

### 1. Upstream Stub (Mock Facilitator)
Mock upstream facilitator for testing.

**Run:**
```bash
uvicorn upstream_stub:app --port 9000
```

### 2. Seller Integration
Seller implementation example for x402 protocol.

**Environment variables:**
- `PROXY_BASE` - Proxy URL (default: http://localhost:8010/x402)
- `NETWORK` - Network (default: base-sepolia)
- `MERCHANT_PAYTO` - Merchant wallet address
- `USDC_ADDRESS` - USDC contract address

**Run:**
```bash
uvicorn seller_integration:app --reload --port 8010
```

**Test endpoint:**
```bash
curl http://localhost:8010/api/market-data?symbol=BTC/USD
```

### 3. Basic Buyer
Simple buyer client example.

**Environment variables:**
- `SELLER_BASE_URL` - Seller API URL (default: http://localhost:8010)
- `AGENT_GATEWAY_URL` - Gateway URL (default: http://localhost:8000)
- `NETWORK` - Network (default: base-sepolia)
- `BUYER_PRIVATE_KEY` - Buyer wallet private key (required)

**Run:**
```bash
python buyer_basic.py
# or
uv run buyer_basic.py
```

### 4. OpenAI Agent Buyer
Advanced buyer with OpenAI agent integration, multi-turn conversation, and full trace collection.

**Additional environment variables:**
- `OPENAI_API_KEY` - OpenAI API key (required)
- `OPENAI_MODEL` - Model name (default: gpt-5-mini)
- All variables from Basic Buyer example

**Run:**
```bash
python buyer_agent_openai.py
# or
uv run buyer_agent_openai.py
```

## Complete Flow Demo

To run a complete end-to-end demo:

1. Start the proxy (from repo root):
   ```bash
   python run_facilitator_proxy.py
   ```

2. Start the seller:
   ```bash
   cd packages/x402-secure/examples
   uvicorn seller_integration:app --reload --port 8010
   ```

3. Run the buyer:
   ```bash
   python buyer_basic.py
   # or for agent demo
   python buyer_agent_openai.py
   ```

## Troubleshooting

### ModuleNotFoundError: No module named 'fastapi'
Install with examples support:
```bash
uv pip install -e ".[examples]"
```

### ModuleNotFoundError: No module named 'openai'
```bash
uv pip install -e ".[agent]"
```

### Missing environment variables
Copy and configure `.env`:
```bash
cp ../../env.example .env
```

## See Also
- [Buyer Integration Guide](../../../docs/BUYER_INTEGRATION.md)
- [Seller Integration Guide](../../../docs/SELLER_INTEGRATION.md)
- [Quickstart](../../../docs/QUICKSTART.md)

