# 🛠️ robust-json

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Robust JSON extraction and repair utilities for LLM-generated content.**

Parse JSON from messy LLM outputs with confidence. `robust-json` extracts and repairs JSON even when models mix commentary with structured data, use incorrect quotes, add trailing commas, include comments, or truncate responses mid-object.

---

## ✨ Why robust-json?

Large Language Models are powerful but inconsistent when generating JSON. They might:

- 📝 **Mix text and JSON**: Embed JSON inside markdown code blocks or conversational responses
- 💬 **Add comments**: Include `//` or `#` comments that break standard JSON parsers
- 🔤 **Use wrong quotes**: Generate single quotes (`'`) instead of double quotes (`"`)
- 🔚 **Add trailing commas**: Place commas after the last item in arrays/objects
- ✂️ **Truncate output**: Stop mid-JSON due to token limits or errors

`robust-json` handles all these cases automatically, so you can focus on using the data instead of fighting with parser errors.

---

## 🚀 Features

- **🔍 Smart extraction**: Automatically finds JSON objects and arrays within free-form text
- **🔧 Auto-repair**: Fixes common LLM errors including:
  - Single-quoted strings → double quotes
  - Mixed quote types (e.g., `'text"` → `'text'`)
  - Inline comments (`//` and `#`)
  - Trailing commas
  - Unclosed braces and brackets
- **🎯 Multiple parsers**: Falls back through `json` → `pyjson5` → `ast.literal_eval` for maximum compatibility
- **⚡ Performance**: Optional speedups with `re2` (faster regex) and `numba` (JIT-compiled bracket scanning)
- **🌍 Unicode support**: Handles international characters and emoji seamlessly

---

## 📦 Installation

**Basic installation:**
```bash
pip install robust-json-parser
```

**With performance optimizations (numba JIT):**
```bash
pip install robust-json-parser[speedups]
```

**With JSON5 support:**
```bash
pip install robust-json-parser[pyjson5]
```

**With re2 (faster regex, may require compilation on some platforms):**
```bash
pip install robust-json-parser[re2]
```

**All extras:**
```bash
pip install robust-json-parser[speedups,pyjson5,re2]
```

**Requirements:** Python 3.9+

---

## 🎯 Quick Start

### Basic Usage

```python
from robust_json import loads

# LLM output with mixed formatting
llm_response = """
Sure! Here's the data you requested:
```json
{
  "name": "Alice",
  "age": 30,
  "hobbies": ["reading", "coding",],  // trailing comma
  "active": true,  # Python-style comment
}

Hope this helps!
"""

data = loads(llm_response)
print(data)
# {'name': 'Alice', 'age': 30, 'hobbies': ['reading', 'coding'], 'active': True}
```

### Handling Malformed JSON

```python
from robust_json import loads

# Mixed quotes, comments, and Chinese text
message = """
你好，我是招聘顾问。以下是岗位描述，用于你的匹配程度:
```json
{"id": "algo", "position": "大模型算法工程师",
# this is the keywords list used to analyze the candidate
 "keywords": {"positive": ["PEFT", "RLHF"], "negative": ["CNN", "RNN"]}, # negative keywords is supported
 "summary": '候选人具备一定AI背景，但经验不足。"
 }
"""

data = loads(message)
print(data["keywords"]["positive"])
# ['PEFT', 'RLHF']
```

### Truncated/Partial JSON

```python
from robust_json import loads

# JSON cut off mid-object
incomplete = '{"user": {"name": "Bob", "email": "bob@example.com"'

data = loads(incomplete)
print(data)
# {'user': {'name': 'Bob', 'email': 'bob@example.com'}}
```

### Extract Multiple JSON Objects

```python
from robust_json import extract_all, RobustJSONParser

text = """
First result: {"a": 1, "b": 2}
Some text in between...
Second result: {"x": 10, "y": 20}
"""

# Get all extractions with metadata
extractions = extract_all(text)
for extraction in extractions:
    print(f"Found at position {extraction.start}: {extraction.text}")

# Or just get the parsed objects
parser = RobustJSONParser()
objects = parser.parse_all(text)
print(objects)
# [{'a': 1, 'b': 2}, {'x': 10, 'y': 20}]
```

---

## 📚 API Reference

### `loads(source, *, allow_partial=True, default=None, strict=False)`

Parse the first JSON object found in the source text.

**Parameters:**
- `source` (str): Text containing JSON
- `allow_partial` (bool): If `True`, auto-complete truncated JSON (default: `True`)
- `default` (Optional): Return this value if no JSON found (default: `None` raises error)
- `strict` (bool): If `True`, only extract from code blocks and brace-delimited content (default: `False`)

**Returns:** Parsed Python object (dict, list, etc.)

**Raises:** `ValueError` if no JSON found and no default provided

---

### `extract(source, *, allow_partial=True)`

Extract the first JSON-like fragment with metadata.

**Returns:** `Extraction` object or `None`

---

### `extract_all(source, *, allow_partial=True)`

Extract all JSON-like fragments from text.

**Returns:** List of `Extraction` objects

---

### `RobustJSONParser`

Main parser class for advanced usage.

**Methods:**
- `extract(source, limit=None)`: Find JSON fragments (returns list of `Extraction` objects)
- `parse_first(source)`: Parse first JSON object (returns parsed object or `None`)
- `parse_all(source)`: Parse all JSON objects (returns list of parsed objects)

**Parameters:**
- `allow_partial` (bool): Auto-complete truncated JSON (default: `True`)
- `strict` (bool): Only extract from explicit JSON contexts (default: `False`)
- `prefer_json5` (bool): Try JSON5 parser before `ast.literal_eval` (default: `True`)

---

### `Extraction`

Dataclass representing an extracted JSON candidate.

**Attributes:**
- `text` (str): The extracted text
- `start` (int): Starting position in source
- `end` (int): Ending position in source
- `is_partial` (bool): Whether the extraction appears truncated
- `repaired` (Optional[str]): The repaired version after processing

---

## 🔧 How It Works

1. **🔎 Extraction**: Scans text for JSON patterns using:
   - Markdown code blocks (`` ```json ... ``` ``)
   - Brace-balanced regions (`{...}`, `[...]`)

2. **🛠️ Repair**: Applies fixes in order:
   - Strip `//` and `#` comments
   - Fix mixed quote types (e.g., `'text"` → `'text'`)
   - Normalize single quotes to double quotes
   - Remove trailing commas
   - Balance unclosed braces (if `allow_partial=True`)

3. **✅ Parse**: Attempts parsing with:
   - `json.loads()` (standard JSON)
   - `pyjson5.decode()` (if installed, for JSON5 support)
   - `ast.literal_eval()` (Python literals)

4. **📊 Return**: Returns first successful parse or continues to next candidate

---

## 🎨 Use Cases

- **🤖 LLM Integration**: Parse structured output from ChatGPT, Claude, Llama, etc.
- **📊 Data Extraction**: Extract JSON from logs, documentation, or mixed-format files
- **🔄 API Responses**: Handle malformed API responses gracefully
- **🧪 Testing**: Validate and repair JSON in test fixtures
- **📝 Data Migration**: Clean up inconsistent JSON during migrations

---

## ⚡ Performance Tips

1. **Install speedups** for large-scale processing:
   ```bash
   pip install robust-json-parser[speedups]  # numba JIT compilation
   pip install robust-json-parser[re2]  # faster regex (may require C++ compiler)
   ```

2. **Use strict mode** when JSON is always in code blocks:
   ```python
   loads(text, strict=True)  # Faster, skips fallback attempts
   ```

3. **Disable partial completion** if you know JSON is complete:
   ```python
   loads(text, allow_partial=False)  # Skips brace-balancing step
   ```

4. **Reuse parser instance** for multiple parses:
   ```python
   parser = RobustJSONParser()
   for text in texts:
       data = parser.parse_first(text)
   ```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

**Development setup:**
```bash
git clone https://github.com/callzhang/robust-json.git
cd robust-json
pip install -e ".[speedups,pyjson5,dev]"  # or add [re2] if you have a C++ compiler
pytest tests/
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built for developers working with LLM-generated content who need reliability without sacrificing flexibility.

---

**Made with ❤️ for the AI/LLM community**
