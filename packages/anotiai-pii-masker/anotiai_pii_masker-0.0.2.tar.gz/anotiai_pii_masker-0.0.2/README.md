# AnotiAI PII Masker - Cloud-Powered Privacy Protection

A lightweight Python package for detecting and masking personally identifiable information (PII) in text using cloud-based AI models with optional local fallback.

[![PyPI version](https://badge.fury.io/py/anotiai-pii-masker.svg)](https://badge.fury.io/py/anotiai-pii-masker)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **☁️ Cloud-Powered**: Uses state-of-the-art AI models hosted on RunPod for maximum accuracy
- **⚡ Lightning Fast**: ~2-3 seconds inference time (after model warm-up)
- **💡 Intelligent**: Combines multiple detection approaches (rule-based, ML, transformers)
- **🔄 Reversible**: Mask and unmask PII while preserving data structure
- **🛡️ Privacy-First**: No data storage - all processing is ephemeral
- **📦 Lightweight**: Minimal dependencies for cloud mode (~10MB vs ~5GB local)
- **🔧 Flexible**: Support for both cloud and local inference modes
- **🎯 Simple API**: Just provide your user API key - no complex setup required

## 🔧 Installation

### Cloud Mode (Recommended)
```bash
pip install anotiai-pii-masker
```

### Local Mode (Full Dependencies)
```bash
pip install anotiai-pii-masker[local]
```

### Development
```bash
pip install anotiai-pii-masker[dev]
```

## 🚀 Quick Start

### Cloud Inference (Default)

```python
from anotiai_pii_masker import WhosePIIGuardian

# Simple setup - just provide your user API key
guardian = WhosePIIGuardian(
    user_api_key="your_jwt_api_key"
)

# Mask PII in text
text = "Hi, I'm John Doe and my email is john.doe@company.com"
result = guardian.mask_text(text)

print(f"Original: {text}")
print(f"Masked: {result['masked_text']}")
# Output: "Hi, I'm [REDACTED_NAME_1] and my email is [REDACTED_EMAIL_1]"

# Unmask when needed
unmask_result = guardian.unmask_text(result['masked_text'], result['pii_map'])
print(f"Unmasked: {unmask_result['unmasked_text']}")
```

### Local Inference (Fallback)

```python
# Requires pip install anotiai-pii-masker[local]
guardian = WhosePIIGuardian(local_mode=True)

# Same API as cloud mode
result = guardian.mask_text(text)
print(f"Masked: {result['masked_text']}")
```

### Cloud with Local Fallback

```python
# Automatically falls back to local if cloud fails
guardian = WhosePIIGuardian(
    user_api_key="your_jwt_api_key",
    local_fallback=True
)
```

## 🔑 Getting API Credentials

1. **Get your JWT API key** from AnotiAI 
2. **No RunPod setup required** - credentials are handled automatically
3. **Simple usage** - just provide your user API key

```python
# That's it! No complex setup needed
guardian = WhosePIIGuardian(user_api_key="your_jwt_api_key")
```

## 📖 Advanced Usage

### Detection Only
```python
# Get detected entities without masking
result = guardian.detect_pii(text)
print(f"Found {result['entities_found']} PII entities")

for entity in result['pii_results']:
    print(f"- {entity['type']}: {entity['value']} (confidence: {entity['confidence']})")
```

### Confidence Thresholds
```python
# Adjust sensitivity (0.0 = very sensitive, 1.0 = very strict)
result = guardian.mask_text(text, confidence_threshold=0.8)
```

### Token Usage Tracking
```python
# All methods return detailed token usage information
result = guardian.mask_text(text)
print(f"Input tokens: {result['usage']['input_tokens']}")
print(f"Output tokens: {result['usage']['output_tokens']}")
print(f"Total tokens: {result['usage']['total_tokens']}")

# Usage tracking for unmasking
unmask_result = guardian.unmask_text(masked_text, pii_map)
print(f"Unmasked tokens: {unmask_result['usage']['output_tokens']}")
```

### Error Handling
```python
from anotiai_pii_masker import WhosePIIGuardian, APIError

try:
    guardian = WhosePIIGuardian(user_api_key="your_jwt_api_key")
    result = guardian.mask_text(text)
except APIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

### Health Check
```python
# Check if the service is healthy
health = guardian.health_check()
print(f"Service status: {health['status']}")
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your App      │    │  anotiai-pii-    │    │   RunPod Cloud  │
│                 │───▶│     masker       │───▶│                 │
│ guardian.mask() │    │   (lightweight)  │    │ GPU Models      │
└─────────────────┘    └──────────────────┘    │ • DeBERTa       │
                                               │ • RoBERTa       │
                                               │ • Presidio      │
                                               │ • spaCy         │
                                               └─────────────────┘
```

## 🔧 Technical Implementation

### **Token Counting Algorithm**
The package uses a sophisticated token counting system:

```python
def count_tokens(data: Any) -> int:
    """
    Calculates token count based on character length:
    - Strings: Character count
    - Dicts/Lists: JSON serialization length
    - Other types: String representation length
    """
```

### **Usage Tracking Flow**
1. **Input Processing**: Counts original text characters
2. **Output Processing**: Counts masked text + PII map JSON
3. **Total Calculation**: Sums input and output tokens
4. **Billing Integration**: Returns structured usage data

### **API Response Format**
```python
{
    "masked_text": "My name is [REDACTED_NAME_1]",
    "pii_map": {"__TOKEN_1__": {...}},
    "entities_found": 1,
    "confidence_threshold": 0.5,
    "usage": {
        "input_tokens": 15,      # Original text length
        "output_tokens": 25,     # Masked text + PII map JSON
        "total_tokens": 40       # Total for billing
    }
}
```

## 📊 Supported PII Types

- **Personal**: Names, dates of birth, addresses
- **Contact**: Email addresses, phone numbers, URLs
- **Financial**: Credit card numbers, bank accounts
- **Government**: SSNs, passport numbers, license numbers
- **Healthcare**: Medical license numbers
- **Technical**: IP addresses, crypto addresses

## 🔒 Security & Privacy

- **No Data Storage**: All processing is ephemeral
- **Encrypted Transit**: HTTPS/TLS for all API communications
- **Reversible Masking**: Original data can be restored when needed
- **Configurable Thresholds**: Adjust sensitivity based on your needs

## 🚨 Migration from v1.x

Version 2.0 introduces cloud-first architecture with simplified API. To migrate:

```python
# v1.x (local only)
from anotiai_pii_masker import WhosePIIGuardian
guardian = WhosePIIGuardian()
masked_text, pii_map = guardian.mask_text(text)

# v2.x (cloud-first with simplified API)
guardian = WhosePIIGuardian(user_api_key="your_jwt_api_key")
result = guardian.mask_text(text)
masked_text = result['masked_text']
pii_map = result['pii_map']
```

## 📈 Performance

| Mode | Setup Time | Inference Time | Memory Usage | Accuracy |
|------|------------|----------------|--------------|----------|
| Cloud | ~1s | ~2-3s | ~50MB | 99.5% |
| Local | ~30s | ~5-10s | ~8GB | 99.5% |

## 📊 Token Usage & Billing

The package provides comprehensive token usage tracking for accurate billing and monitoring:

### **Automatic Token Counting**
- **Input tokens**: Counted from original text
- **Output tokens**: Counted from masked text + PII map
- **Total tokens**: Sum of input and output tokens
- **JSON serialization**: PII maps are counted as JSON character length

### **Usage Examples**
```python
# Masking with token tracking
result = guardian.mask_text("My name is John Doe")
print(f"Input: {result['usage']['input_tokens']} tokens")
print(f"Output: {result['usage']['output_tokens']} tokens") 
print(f"Total: {result['usage']['total_tokens']} tokens")

# Unmasking with token tracking
unmask_result = guardian.unmask_text(masked_text, pii_map)
print(f"Restored: {unmask_result['usage']['output_tokens']} tokens")
```

### **Billing Integration**
```python
# Track usage across multiple operations
total_input_tokens = 0
total_output_tokens = 0

for text in texts:
    result = guardian.mask_text(text)
    total_input_tokens += result['usage']['input_tokens']
    total_output_tokens += result['usage']['output_tokens']

print(f"Total processed: {total_input_tokens + total_output_tokens} tokens")
```

## 🎯 Key Benefits

- **Simplified Setup**: Just provide your JWT API key - no complex RunPod configuration
- **Automatic Fallback**: Seamlessly switches to local mode if cloud is unavailable
- **Production Ready**: Battle-tested on RunPod Serverless infrastructure
- **Cost Effective**: Pay-per-use pricing with no idle costs
- **Enterprise Grade**: Built for scale with proper error handling and monitoring
- **Usage Tracking**: Comprehensive token counting for accurate billing

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📚 Documentation

- **[API Reference](docs/API_REFERENCE.md)**: Complete API documentation with examples
- **[Quick Reference](docs/QUICK_REFERENCE.md)**: Developer quick reference guide
- **[GitHub README](https://github.com/anotiai/anotiai-pii-masker#readme)**: Main documentation

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/anotiai/anotiai-pii-masker/issues)
- **Email**: ask@anotiai.com

---

**Protect your users' privacy with AnotiAI PII Masker** 🛡️
