# Examples Directory

This directory contains example scripts demonstrating various use cases of the `openai-without-pydantic` package.

## Running Examples

Make sure you have:
1. Installed the package: `pip install openai-without-pydantic`
2. Set your API key: `export OPENAI_API_KEY='your-key-here'`

## Available Examples

### 1. basic_usage.py
**Basic usage and simple Q&A**

Demonstrates the fundamental usage of the package:
- Simple question answering
- Document analysis
- Text summarization

```bash
python examples/basic_usage.py
```

### 2. advanced_usage.py
**Advanced features and customization**

Shows advanced features:
- Using different models (GPT-4, GPT-4o-mini)
- Setting custom temperature values
- Limiting response length with max_tokens
- Custom timeout settings
- Error handling patterns

```bash
python examples/advanced_usage.py
```

### 3. batch_processing.py
**Processing multiple questions efficiently**

Demonstrates batch processing:
- Asking multiple questions about the same context
- Processing multiple documents sequentially
- Collecting and summarizing results
- Error handling in batch operations

```bash
python examples/batch_processing.py
```

## Tips for Using Examples

### Environment Variables
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

### Installing Development Dependencies
```bash
pip install python-dotenv
```

### Modifying Examples
Feel free to modify these examples to experiment with:
- Different input texts and questions
- Various model parameters
- Your own use cases

## Cost Considerations

These examples make API calls to OpenAI which incur costs based on:
- Number of tokens processed
- Model used (GPT-4 is more expensive than GPT-4o-mini)

**Recommended for testing:**
- Use `gpt-4o-mini` (default) for cost-effective testing
- Set `max_tokens` to limit response length
- Monitor your OpenAI API usage dashboard

## Common Issues

**"API key not found"**
- Ensure `OPENAI_API_KEY` environment variable is set
- Or pass `api_key` parameter to `ask_ai_question()`

**"Rate limit exceeded"**
- Wait a few seconds between requests
- Check your OpenAI account rate limits

**"Timeout error"**
- Increase the `timeout` parameter
- Check your network connection

## More Resources

- [Main README](../README.md)
- [Publishing Guide](../PUBLISHING.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
