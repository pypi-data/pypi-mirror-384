"""
LLM provider abstraction layer for VRIN hybrid cloud architecture.

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-4o-mini)
- Azure OpenAI Service
- Customer-hosted models (future)
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 2000)
        self.timeout = config.get('timeout', 30)
        
    @abstractmethod
    def extract_facts(self, content: str, user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract facts from content using LLM."""
        pass
        
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text list."""
        pass
        
    @abstractmethod
    def synthesize_response(self, query: str, context: List[Dict[str, Any]], user_specialization: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synthesize response using retrieved context."""
        pass
        
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check LLM provider health."""
        pass
        
    def _make_request(self, url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make HTTP request to LLM provider."""
        try:
            default_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'VRIN-Enterprise/1.0'
            }
            
            if headers:
                default_headers.update(headers)
                
            response = requests.post(
                url,
                json=payload,
                headers=default_headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout to {url}")
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            return {"error": "Invalid JSON response"}


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.embedding_model = config.get('embedding_model', 'text-embedding-3-small')
        
    def extract_facts(self, content: str, user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract facts using OpenAI GPT."""
        if not self.api_key:
            logger.error("OpenAI API key not configured")
            return []
            
        extraction_prompt = self._build_extraction_prompt(content, user_context)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a specialized fact extraction expert. Extract clear, verifiable facts from text and return them as JSON with confidence scores."
                },
                {
                    "role": "user",
                    "content": extraction_prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        response = self._make_request(
            f"{self.base_url}/chat/completions",
            payload,
            headers
        )
        
        if "error" in response:
            logger.error(f"Fact extraction failed: {response['error']}")
            return []
            
        try:
            content_text = response['choices'][0]['message']['content']
            
            # Try to extract JSON from response
            if '```json' in content_text:
                json_start = content_text.find('```json') + 7
                json_end = content_text.find('```', json_start)
                json_text = content_text[json_start:json_end].strip()
            else:
                # Look for array start
                start_idx = content_text.find('[')
                end_idx = content_text.rfind(']') + 1
                if start_idx != -1 and end_idx != 0:
                    json_text = content_text[start_idx:end_idx]
                else:
                    json_text = content_text
                    
            facts = json.loads(json_text)
            
            # Validate fact structure
            validated_facts = []
            for fact in facts:
                if all(key in fact for key in ['subject', 'predicate', 'object']):
                    fact['confidence'] = fact.get('confidence', 0.8)
                    fact['extracted_at'] = datetime.utcnow().isoformat()
                    fact['model'] = self.model
                    fact['provider'] = 'openai'
                    validated_facts.append(fact)
                    
            return validated_facts
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse fact extraction response: {str(e)}")
            return []
            
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        if not self.api_key:
            logger.error("OpenAI API key not configured") 
            return []
            
        # Batch texts to avoid rate limits
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            payload = {
                "input": batch,
                "model": self.embedding_model
            }
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = self._make_request(
                f"{self.base_url}/embeddings",
                payload,
                headers
            )
            
            if "error" in response:
                logger.error(f"Embedding generation failed: {response['error']}")
                return []
                
            try:
                embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(embeddings)
            except KeyError:
                logger.error("Invalid embedding response format")
                return []
                
        return all_embeddings
        
    def synthesize_response(self, query: str, context: List[Dict[str, Any]], user_specialization: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synthesize response using retrieved context."""
        if not self.api_key:
            return {"error": "OpenAI API key not configured"}
            
        synthesis_prompt = self._build_synthesis_prompt(query, context, user_specialization)
        
        # Use GPT-4 for complex synthesis
        synthesis_model = "gpt-4" if "gpt-4" in self.model else self.model
        
        payload = {
            "model": synthesis_model,
            "messages": [
                {
                    "role": "system",
                    "content": self._get_synthesis_system_prompt(user_specialization)
                },
                {
                    "role": "user", 
                    "content": synthesis_prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 3000
        }
        
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        response = self._make_request(
            f"{self.base_url}/chat/completions",
            payload, 
            headers
        )
        
        if "error" in response:
            return {"error": response["error"]}
            
        try:
            content_text = response['choices'][0]['message']['content']
            
            return {
                "response": content_text,
                "model": synthesis_model,
                "provider": "openai", 
                "context_used": len(context),
                "specialized": user_specialization is not None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except (KeyError, IndexError) as e:
            return {"error": f"Failed to parse synthesis response: {str(e)}"}
            
    def health_check(self) -> Dict[str, Any]:
        """Check OpenAI service health.""" 
        if not self.api_key:
            return {"status": "unhealthy", "error": "No API key"}
            
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = self._make_request(
                f"{self.base_url}/chat/completions",
                payload,
                headers
            )
            
            if "error" in response:
                return {
                    "status": "unhealthy",
                    "provider": "openai",
                    "error": response["error"]
                }
                
            return {
                "status": "healthy",
                "provider": "openai", 
                "model": self.model,
                "embedding_model": self.embedding_model
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "provider": "openai",
                "error": str(e)
            }
            
    def _build_extraction_prompt(self, content: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Build fact extraction prompt."""
        base_prompt = f"""
Extract factual triplets from the following text. Focus on clear, verifiable facts.
Return ONLY a JSON array of facts in this exact format:

[
  {{"subject": "entity1", "predicate": "relationship", "object": "entity2", "confidence": 0.9}},
  {{"subject": "entity2", "predicate": "property", "object": "value", "confidence": 0.8}}
]

Requirements:
- Each fact must have subject, predicate, object, and confidence (0.0-1.0)
- Focus on entities, relationships, and concrete facts
- Avoid opinions, speculation, or uncertain statements
- Use confidence scores: 0.9+ for explicit facts, 0.7-0.8 for implied facts

Content to analyze:
{content}
        """
        
        if user_context and user_context.get('domain_keywords'):
            keywords = ", ".join(user_context['domain_keywords'])
            base_prompt += f"\n\nPay special attention to terms related to: {keywords}"
            
        return base_prompt.strip()
        
    def _build_synthesis_prompt(self, query: str, context: List[Dict[str, Any]], user_specialization: Optional[Dict[str, Any]] = None) -> str:
        """Build response synthesis prompt."""
        context_text = self._format_context(context)
        
        base_prompt = f"""
Query: {query}

Relevant Context:
{context_text}

Based on the context provided, provide a comprehensive analysis that addresses the query. 
Include reasoning chains and cite specific facts from the context.
        """
        
        if user_specialization:
            reasoning_focus = user_specialization.get('reasoning_focus', [])
            if reasoning_focus:
                focus_text = ", ".join(reasoning_focus)
                base_prompt += f"\n\nAnalysis Focus: {focus_text}"
                
        return base_prompt.strip()
        
    def _get_synthesis_system_prompt(self, user_specialization: Optional[Dict[str, Any]] = None) -> str:
        """Get system prompt for synthesis."""
        base_prompt = "You are an expert analyst skilled at synthesizing information and providing clear, evidence-based insights."
        
        if user_specialization and user_specialization.get('custom_prompts', {}).get('user_specialization'):
            return user_specialization['custom_prompts']['user_specialization']
            
        return base_prompt
        
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context for prompt."""
        formatted_context = []
        
        for i, item in enumerate(context, 1):
            if 'content' in item:
                formatted_context.append(f"[{i}] {item['content']}")
            elif 'subject' in item and 'predicate' in item and 'object' in item:
                formatted_context.append(f"[{i}] {item['subject']} {item['predicate']} {item['object']}")
            else:
                formatted_context.append(f"[{i}] {str(item)}")
                
        return "\n\n".join(formatted_context)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI Service provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.resource_name = config.get('resource_name')
        self.deployment_name = config.get('deployment_name')
        self.api_version = config.get('api_version', '2023-12-01-preview')
        self.base_url = f"https://{self.resource_name}.openai.azure.com/openai/deployments/{self.deployment_name}"
        
    def extract_facts(self, content: str, user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract facts using Azure OpenAI."""
        if not all([self.api_key, self.resource_name, self.deployment_name]):
            logger.error("Azure OpenAI configuration incomplete")
            return []
            
        extraction_prompt = self._build_extraction_prompt(content, user_context)
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a specialized fact extraction expert. Extract clear, verifiable facts from text and return them as JSON with confidence scores."
                },
                {
                    "role": "user", 
                    "content": extraction_prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        headers = {
            'api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/chat/completions?api-version={self.api_version}"
        
        response = self._make_request(url, payload, headers)
        
        if "error" in response:
            logger.error(f"Azure fact extraction failed: {response['error']}")
            return []
            
        # Process response similar to OpenAI
        try:
            content_text = response['choices'][0]['message']['content']
            facts = self._parse_facts_response(content_text)
            
            for fact in facts:
                fact['provider'] = 'azure_openai'
                fact['model'] = self.deployment_name
                
            return facts
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Azure response: {str(e)}")
            return []
            
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Azure OpenAI."""
        # Similar implementation to OpenAI but with Azure endpoint format
        if not all([self.api_key, self.resource_name]):
            logger.error("Azure OpenAI configuration incomplete")
            return []
            
        # Use text-embedding-ada-002 deployment
        embedding_url = f"https://{self.resource_name}.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version={self.api_version}"
        
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            payload = {"input": batch}
            headers = {'api-key': self.api_key}
            
            response = self._make_request(embedding_url, payload, headers)
            
            if "error" in response:
                logger.error(f"Azure embedding failed: {response['error']}")
                return []
                
            try:
                embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(embeddings)
            except KeyError:
                logger.error("Invalid Azure embedding response")
                return []
                
        return all_embeddings
        
    def synthesize_response(self, query: str, context: List[Dict[str, Any]], user_specialization: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synthesize response using Azure OpenAI."""
        if not all([self.api_key, self.resource_name, self.deployment_name]):
            return {"error": "Azure OpenAI configuration incomplete"}
            
        synthesis_prompt = self._build_synthesis_prompt(query, context, user_specialization)
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": self._get_synthesis_system_prompt(user_specialization)
                },
                {
                    "role": "user",
                    "content": synthesis_prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 3000
        }
        
        headers = {'api-key': self.api_key}
        url = f"{self.base_url}/chat/completions?api-version={self.api_version}"
        
        response = self._make_request(url, payload, headers)
        
        if "error" in response:
            return {"error": response["error"]}
            
        try:
            content_text = response['choices'][0]['message']['content']
            
            return {
                "response": content_text,
                "model": self.deployment_name,
                "provider": "azure_openai",
                "context_used": len(context),
                "specialized": user_specialization is not None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except (KeyError, IndexError) as e:
            return {"error": f"Failed to parse Azure response: {str(e)}"}
            
    def health_check(self) -> Dict[str, Any]:
        """Check Azure OpenAI health."""
        if not all([self.api_key, self.resource_name, self.deployment_name]):
            return {"status": "unhealthy", "error": "Configuration incomplete"}
            
        try:
            payload = {
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            headers = {'api-key': self.api_key}
            url = f"{self.base_url}/chat/completions?api-version={self.api_version}"
            
            response = self._make_request(url, payload, headers)
            
            if "error" in response:
                return {
                    "status": "unhealthy",
                    "provider": "azure_openai", 
                    "error": response["error"]
                }
                
            return {
                "status": "healthy",
                "provider": "azure_openai",
                "resource": self.resource_name,
                "deployment": self.deployment_name
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "azure_openai",
                "error": str(e)
            }
            
    # Reuse prompt building methods from OpenAI provider
    def _build_extraction_prompt(self, content: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Build fact extraction prompt (reuse OpenAI implementation)."""
        return OpenAIProvider._build_extraction_prompt(self, content, user_context)
        
    def _build_synthesis_prompt(self, query: str, context: List[Dict[str, Any]], user_specialization: Optional[Dict[str, Any]] = None) -> str:
        """Build synthesis prompt (reuse OpenAI implementation)."""
        return OpenAIProvider._build_synthesis_prompt(self, query, context, user_specialization)
        
    def _get_synthesis_system_prompt(self, user_specialization: Optional[Dict[str, Any]] = None) -> str:
        """Get system prompt (reuse OpenAI implementation)."""
        return OpenAIProvider._get_synthesis_system_prompt(self, user_specialization)
        
    def _parse_facts_response(self, content_text: str) -> List[Dict[str, Any]]:
        """Parse facts from response text."""
        try:
            # Try to extract JSON from response
            if '```json' in content_text:
                json_start = content_text.find('```json') + 7
                json_end = content_text.find('```', json_start)
                json_text = content_text[json_start:json_end].strip()
            else:
                start_idx = content_text.find('[')
                end_idx = content_text.rfind(']') + 1
                if start_idx != -1 and end_idx != 0:
                    json_text = content_text[start_idx:end_idx]
                else:
                    json_text = content_text
                    
            facts = json.loads(json_text)
            
            validated_facts = []
            for fact in facts:
                if all(key in fact for key in ['subject', 'predicate', 'object']):
                    fact['confidence'] = fact.get('confidence', 0.8)
                    fact['extracted_at'] = datetime.utcnow().isoformat()
                    validated_facts.append(fact)
                    
            return validated_facts
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse facts: {str(e)}")
            return []