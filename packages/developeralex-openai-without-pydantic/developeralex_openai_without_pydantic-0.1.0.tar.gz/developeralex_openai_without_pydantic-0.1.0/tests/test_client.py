"""
Unit tests for openai_wrapper package
"""
import pytest
import os
from unittest.mock import patch, Mock
from openai_wrapper import ask_ai_question


class TestAskAIQuestion:
    """Test suite for ask_ai_question function"""
    
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key must be provided"):
                ask_ai_question("test input", "test question")
    
    def test_api_key_from_parameter(self):
        """Test that API key can be passed as parameter"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test answer"}}]
            }
            mock_post.return_value = mock_response
            
            result = ask_ai_question(
                input_text="Test input",
                question_asked="Test question?",
                api_key="test-key-123"
            )
            
            assert result == "Test answer"
            assert mock_post.called
            
            # Verify Authorization header
            call_args = mock_post.call_args
            headers = call_args.kwargs['headers']
            assert headers['Authorization'] == 'Bearer test-key-123'
    
    def test_api_key_from_environment(self):
        """Test that API key is read from environment variable"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key-456'}):
            with patch('openai_wrapper.client.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Answer from env"}}]
                }
                mock_post.return_value = mock_response
                
                result = ask_ai_question("Input", "Question?")
                
                assert result == "Answer from env"
                call_args = mock_post.call_args
                headers = call_args.kwargs['headers']
                assert headers['Authorization'] == 'Bearer env-key-456'
    
    def test_custom_model_parameter(self):
        """Test using a custom model"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "GPT-4 response"}}]
            }
            mock_post.return_value = mock_response
            
            result = ask_ai_question(
                input_text="Test",
                question_asked="Question?",
                api_key="test-key",
                model="gpt-4o"
            )
            
            # Verify model in payload
            call_args = mock_post.call_args
            payload = call_args.kwargs['json']
            assert payload['model'] == 'gpt-4o'
    
    def test_default_model(self):
        """Test that default model is used when not specified"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}]
            }
            mock_post.return_value = mock_response
            
            ask_ai_question(
                input_text="Test",
                question_asked="Question?",
                api_key="test-key"
            )
            
            call_args = mock_post.call_args
            payload = call_args.kwargs['json']
            assert payload['model'] == 'gpt-4o-mini'
    
    def test_custom_temperature(self):
        """Test setting custom temperature"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}]
            }
            mock_post.return_value = mock_response
            
            ask_ai_question(
                input_text="Test",
                question_asked="Question?",
                api_key="test-key",
                temperature=0.2
            )
            
            call_args = mock_post.call_args
            payload = call_args.kwargs['json']
            assert payload['temperature'] == 0.2
    
    def test_max_tokens_parameter(self):
        """Test setting max_tokens"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}]
            }
            mock_post.return_value = mock_response
            
            ask_ai_question(
                input_text="Test",
                question_asked="Question?",
                api_key="test-key",
                max_tokens=150
            )
            
            call_args = mock_post.call_args
            payload = call_args.kwargs['json']
            assert payload['max_tokens'] == 150
    
    def test_timeout_error(self):
        """Test timeout handling"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.Timeout()
            
            with pytest.raises(Exception, match="Request timed out after"):
                ask_ai_question(
                    input_text="Test",
                    question_asked="Question?",
                    api_key="test-key",
                    timeout=5
                )
    
    def test_http_error_handling(self):
        """Test HTTP error handling"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            import requests
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "error": {"message": "Invalid API key"}
            }
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="OpenAI API error: Invalid API key"):
                ask_ai_question(
                    input_text="Test",
                    question_asked="Question?",
                    api_key="invalid-key"
                )
    
    def test_empty_response_handling(self):
        """Test handling of empty API response"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": ""}}]
            }
            mock_post.return_value = mock_response
            
            result = ask_ai_question(
                input_text="Test",
                question_asked="Question?",
                api_key="test-key"
            )
            
            assert result == ""
    
    def test_message_format(self):
        """Test that messages are formatted correctly"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}]
            }
            mock_post.return_value = mock_response
            
            ask_ai_question(
                input_text="Python is a language",
                question_asked="What is Python?",
                api_key="test-key"
            )
            
            call_args = mock_post.call_args
            payload = call_args.kwargs['json']
            messages = payload['messages']
            
            # Check system message
            assert messages[0]['role'] == 'system'
            assert 'helpful assistant' in messages[0]['content']
            
            # Check user message contains context and question
            assert messages[1]['role'] == 'user'
            assert 'Python is a language' in messages[1]['content']
            assert 'What is Python?' in messages[1]['content']
    
    def test_request_headers(self):
        """Test that request headers are set correctly"""
        with patch('openai_wrapper.client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}]
            }
            mock_post.return_value = mock_response
            
            ask_ai_question(
                input_text="Test",
                question_asked="Question?",
                api_key="test-key"
            )
            
            call_args = mock_post.call_args
            headers = call_args.kwargs['headers']
            
            assert headers['Content-Type'] == 'application/json'
            assert headers['Authorization'] == 'Bearer test-key'
    
    def test_environment_variable_model(self):
        """Test reading model from environment variable"""
        with patch.dict(os.environ, {'OPENAI_MODEL': 'gpt-4'}):
            with patch('openai_wrapper.client.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Response"}}]
                }
                mock_post.return_value = mock_response
                
                ask_ai_question(
                    input_text="Test",
                    question_asked="Question?",
                    api_key="test-key"
                )
                
                call_args = mock_post.call_args
                payload = call_args.kwargs['json']
                assert payload['model'] == 'gpt-4'
    
    def test_environment_variable_temperature(self):
        """Test reading temperature from environment variable"""
        with patch.dict(os.environ, {'OPENAI_TEMPERATURE': '0.5'}):
            with patch('openai_wrapper.client.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Response"}}]
                }
                mock_post.return_value = mock_response
                
                ask_ai_question(
                    input_text="Test",
                    question_asked="Question?",
                    api_key="test-key"
                )
                
                call_args = mock_post.call_args
                payload = call_args.kwargs['json']
                assert payload['temperature'] == 0.5
