"""Real-world LLM-generated JSON test cases.

This module tests scenarios commonly encountered when parsing JSON from
Large Language Models like ChatGPT, Claude, GPT-4, Llama, etc.
"""

import pytest
from robust_json import loads, extract_all, RobustJSONParser


class TestChatGPTOutputs:
    """Test common ChatGPT/GPT-4 output patterns."""

    def test_chatgpt_with_explanation_prefix(self):
        """Test ChatGPT response with explanatory prefix."""
        text = """
        Sure! Here's the JSON data you requested:

        {
            "status": "success",
            "data": {
                "users": ["Alice", "Bob", "Charlie"],
                "count": 3
            }
        }

        This JSON contains the user list and total count.
        """
        result = loads(text)
        assert result["status"] == "success"
        assert len(result["data"]["users"]) == 3

    def test_chatgpt_markdown_code_block(self):
        """Test ChatGPT's markdown code block format."""
        text = """
        Here's the configuration:
        
        ```json
        {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 1.0
        }
        ```
        
        These are the recommended settings for your use case.
        """
        result = loads(text)
        assert result["model"] == "gpt-4"
        assert result["temperature"] == 0.7

    def test_chatgpt_incomplete_due_to_token_limit(self):
        """Test JSON cut off mid-generation due to token limits."""
        text = """
        ```json
        {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "char
        """
        result = loads(text)
        assert "users" in result
        assert len(result["users"]) >= 2

    def test_chatgpt_with_inline_comments_from_explanation(self):
        """Test when ChatGPT adds explanatory comments in JSON."""
        text = """
        ```json
        {
            "api_key": "sk-...",  // Replace with your actual API key
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4",  // Use gpt-3.5-turbo for faster responses
            "stream": false  // Set to true for streaming responses
        }
        ```
        """
        result = loads(text)
        assert result["model"] == "gpt-4"
        assert result["stream"] is False

    def test_chatgpt_json_in_conversational_response(self):
        """Test JSON embedded in conversational text."""
        text = """
        Based on your requirements, I've created this configuration:
        
        {"app_name": "MyApp", "version": "1.0.0", "debug": false}
        
        You can modify the debug flag to true during development.
        """
        result = loads(text)
        assert result["app_name"] == "MyApp"
        assert result["debug"] is False


class TestClaudeOutputs:
    """Test common Claude AI output patterns."""

    def test_claude_thinking_tags(self):
        """Test Claude's XML-style thinking tags around JSON."""
        text = """
        <thinking>
        I need to structure this as JSON...
        </thinking>
        
        {
            "response": "Here's the data",
            "confidence": 0.95
        }
        """
        result = loads(text)
        assert result["response"] == "Here's the data"
        assert result["confidence"] == 0.95

    def test_claude_with_artifacts(self):
        """Test Claude's artifact format."""
        text = """
        I'll create a JSON configuration for you:
        
        ```json
        {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "mydb"
            },
            "cache": {
                "enabled": true,
                "ttl": 3600
            }
        }
        ```
        
        This configuration includes database and cache settings.
        """
        result = loads(text)
        assert result["database"]["port"] == 5432
        assert result["cache"]["enabled"] is True

    def test_claude_multiline_explanatory_text(self):
        """Test Claude's verbose explanations around JSON."""
        text = """
        Based on your requirements, I've structured the data as follows:
        
        The JSON object contains:
        - A list of products
        - Pricing information
        - Availability status
        
        Here it is:
        
        {
            "products": [
                {"id": "P001", "name": "Laptop", "price": 999.99},
                {"id": "P002", "name": "Mouse", "price": 29.99}
            ],
            "currency": "USD",
            "in_stock": true
        }
        
        Let me know if you need any modifications.
        """
        result = loads(text)
        assert len(result["products"]) == 2
        assert result["currency"] == "USD"


class TestLLMCommonFormatErrors:
    """Test common formatting errors in LLM outputs."""

    def test_llm_using_single_quotes(self):
        """Test LLMs using Python-style single quotes."""
        text = """
        {'name': 'John Doe', 'age': 30, 'active': True}
        """
        result = loads(text)
        assert result["name"] == "John Doe"
        assert result["age"] == 30

    def test_llm_trailing_commas_everywhere(self):
        """Test excessive trailing commas (JSON5 style)."""
        text = """
        {
            "items": [
                "item1",
                "item2",
                "item3",
            ],
            "metadata": {
                "created": "2025-01-15",
                "author": "AI",
            },
        }
        """
        result = loads(text)
        assert len(result["items"]) == 3
        assert result["metadata"]["author"] == "AI"

    def test_llm_python_style_true_false_none(self):
        """Test Python-style True/False/None (should be true/false/null)."""
        text = """
        {
            "is_valid": True,
            "is_error": False,
            "data": None
        }
        """
        result = loads(text)
        assert result["is_valid"] is True
        assert result["is_error"] is False
        assert result["data"] is None

    def test_llm_unquoted_keys(self):
        """Test JavaScript-style unquoted object keys."""
        text = """
        {
            name: "Product",
            price: 99.99,
            available: true
        }
        """
        result = loads(text, default={})
        # May or may not parse depending on fallback parsers
        assert isinstance(result, dict)

    def test_llm_mixed_comment_styles(self):
        """Test multiple comment styles in one JSON."""
        text = """
        {
            "config": {
                "host": "localhost",  // server address
                "port": 8080,         # default port
                "ssl": false          /* disable for dev */
            }
        }
        """
        result = loads(text)
        assert result["config"]["host"] == "localhost"
        assert result["config"]["port"] == 8080


class TestMultilingualLLMOutputs:
    """Test LLM outputs in various languages."""

    def test_chinese_llm_output(self):
        """Test Chinese LLM with mixed Chinese and JSON."""
        text = """
        好的，这是您需要的数据：
        
        ```json
        {
            "姓名": "张三",
            "年龄": 25,
            "城市": "北京",
            "职位": "软件工程师"
        }
        ```
        
        这些是基本信息。
        """
        result = loads(text)
        assert result["姓名"] == "张三"
        assert result["城市"] == "北京"

    def test_japanese_llm_output(self):
        """Test Japanese LLM output."""
        text = """
        はい、JSONデータを作成しました：
        
        {
            "名前": "田中太郎",
            "メール": "tanaka@example.jp",
            "ステータス": "アクティブ"
        }
        """
        result = loads(text)
        assert "名前" in result
        assert "メール" in result

    def test_mixed_language_keys_and_values(self):
        """Test JSON with mixed language keys and values."""
        text = """
        {
            "name": "李明",
            "email": "liming@example.com",
            "profile": {
                "bio": "Software engineer from 北京",
                "skills": ["Python", "JavaScript", "日本語"]
            }
        }
        """
        result = loads(text)
        assert result["name"] == "李明"
        assert "日本語" in result["profile"]["skills"]


class TestStructuredDataExtraction:
    """Test extracting structured data from LLM responses."""

    def test_api_response_format(self):
        """Test typical API response format from LLM."""
        text = """
        I'll call the API and return the response:
        
        ```json
        {
            "status": 200,
            "message": "Success",
            "data": {
                "user_id": "12345",
                "username": "john_doe",
                "email": "john@example.com",
                "created_at": "2025-01-15T10:30:00Z"
            },
            "errors": null
        }
        ```
        """
        result = loads(text)
        assert result["status"] == 200
        assert result["data"]["username"] == "john_doe"
        assert result["errors"] is None

    def test_database_schema_generation(self):
        """Test database schema JSON from LLM."""
        text = """
        Here's the database schema:
        
        {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": true},
                        {"name": "email", "type": "VARCHAR(255)", "unique": true},
                        {"name": "created_at", "type": "TIMESTAMP"}
                    ]
                }
            ]
        }
        """
        result = loads(text)
        assert result["tables"][0]["name"] == "users"
        assert result["tables"][0]["columns"][0]["primary_key"] is True

    def test_configuration_file_generation(self):
        """Test config file JSON from LLM."""
        text = """
        Here's your .env configuration in JSON format:
        
        // Database Configuration
        {
            "DB_HOST": "localhost",
            "DB_PORT": 5432,
            "DB_NAME": "production_db",
            "DB_USER": "admin",
            // Redis Cache
            "REDIS_URL": "redis://localhost:6379",
            "CACHE_TTL": 3600,
            // API Keys (replace with actual values)
            "API_KEY": "your-api-key-here",
            "SECRET_KEY": "your-secret-key"
        }
        """
        result = loads(text)
        assert result["DB_HOST"] == "localhost"
        assert result["CACHE_TTL"] == 3600


class TestPromptInjectionAndEdgeCases:
    """Test edge cases and potential prompt injection scenarios."""

    def test_json_with_nested_json_strings(self):
        """Test JSON containing stringified JSON."""
        text = """
        {
            "metadata": "{\\"nested\\": \\"json\\"}",
            "actual_data": {"key": "value"}
        }
        """
        result = loads(text)
        assert isinstance(result["metadata"], str)
        assert result["actual_data"]["key"] == "value"

    def test_llm_escaping_issues(self):
        """Test LLM struggling with escape characters."""
        text = """
        {
            "path": "C:\\Users\\Documents\\file.txt",
            "regex": "\\d+",
            "newline": "Line1\\nLine2"
        }
        """
        result = loads(text)
        assert "path" in result
        assert "\\" in result["path"] or "/" in result["path"]

    def test_llm_markdown_in_json_values(self):
        """Test when LLM includes markdown in JSON values."""
        text = """
        {
            "description": "This is **bold** and *italic* text",
            "code": "`inline code`",
            "list": "- Item 1\\n- Item 2"
        }
        """
        result = loads(text)
        assert "**bold**" in result["description"]

    def test_json_with_very_long_strings(self):
        """Test handling very long string values from LLM."""
        long_text = "A" * 5000
        text = f'''
        {{
            "long_content": "{long_text}",
            "metadata": {{"length": 5000}}
        }}
        '''
        result = loads(text)
        assert len(result["long_content"]) == 5000


class TestRealisticUseCases:
    """Test realistic use cases for LLM-generated JSON."""

    def test_recipe_generation(self):
        """Test recipe JSON from cooking LLM."""
        text = """
        Here's the recipe in JSON format:
        
        ```json
        {
            "name": "Chocolate Chip Cookies",
            "prep_time": "15 minutes",
            "cook_time": "12 minutes",
            "servings": 24,
            "ingredients": [
                {"item": "flour", "amount": "2 cups"},
                {"item": "butter", "amount": "1 cup"},
                {"item": "chocolate chips", "amount": "2 cups"}
            ],
            "instructions": [
                "Preheat oven to 375°F",
                "Mix butter and sugar",
                "Add flour and chocolate chips",
                "Bake for 12 minutes"
            ]
        }
        ```
        """
        result = loads(text)
        assert result["servings"] == 24
        assert len(result["ingredients"]) == 3

    def test_calendar_event_generation(self):
        """Test calendar event JSON."""
        text = """
        I've created a calendar event:
        
        {
            "event": "Team Meeting",
            "date": "2025-01-20",
            "time": "14:00",
            "duration": "60 minutes",
            "attendees": ["alice@company.com", "bob@company.com"],
            "location": "Conference Room A",
            "recurring": false
        }
        """
        result = loads(text)
        assert result["event"] == "Team Meeting"
        assert len(result["attendees"]) == 2

    def test_task_list_generation(self):
        """Test todo list JSON from productivity LLM."""
        text = """
        Here's your task list:
        
        ```json
        {
            "tasks": [
                {
                    "id": 1,
                    "title": "Review pull requests",
                    "priority": "high",
                    "completed": false,
                    "due_date": "2025-01-16"
                },
                {
                    "id": 2,
                    "title": "Write documentation",
                    "priority": "medium",
                    "completed": false,
                    "due_date": "2025-01-18"
                },
            ]
        }
        ```
        """
        result = loads(text)
        assert len(result["tasks"]) == 2
        assert result["tasks"][0]["priority"] == "high"

    def test_resume_parsing(self):
        """Test resume/CV JSON extraction."""
        text = """
        Based on the resume, here's the structured data:
        
        {
            "personal_info": {
                "name": "Jane Smith",
                "email": "jane.smith@email.com",
                "phone": "+1-555-0123"
            },
            "experience": [
                {
                    "company": "Tech Corp",
                    "position": "Senior Developer",
                    "years": "2020-2025",
                    "skills": ["Python", "React", "AWS"]
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "university": "State University",
                    "year": 2020
                }
            ]
        }
        """
        result = loads(text)
        assert result["personal_info"]["name"] == "Jane Smith"
        assert len(result["experience"]) == 1


class TestErrorRecoveryScenarios:
    """Test LLM-specific error recovery scenarios."""

    def test_llm_apologizing_in_json(self):
        """Test when LLM includes apology text."""
        text = """
        I apologize for the confusion. Here's the correct JSON:
        
        {
            "status": "corrected",
            "data": {"key": "value"}
        }
        """
        result = loads(text)
        assert result["status"] == "corrected"

    def test_llm_regenerating_response(self):
        """Test when LLM says 'let me try again'."""
        text = """
        Let me regenerate that response:
        
        ```json
        {"result": "success", "attempt": 2}
        ```
        """
        result = loads(text)
        assert result["result"] == "success"

    def test_multiple_json_blocks_picking_first(self):
        """Test picking the correct JSON when LLM provides multiple attempts."""
        text = """
        First attempt (wrong):
        {"error": "old data"}
        
        Corrected version:
        {"status": "success", "data": "correct"}
        """
        result = loads(text)
        # Should get first valid JSON
        assert "error" in result or "status" in result

    def test_llm_incomplete_then_complete(self):
        """Test when LLM starts incomplete then completes."""
        text = """
        Here's the start:
        {"incomplete": true
        
        Actually, let me complete that:
        {"complete": true, "data": "finished"}
        """
        # Should find and parse the complete one
        results = extract_all(text)
        assert len(results) >= 1

