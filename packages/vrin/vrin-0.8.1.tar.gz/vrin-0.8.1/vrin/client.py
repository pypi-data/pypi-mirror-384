"""
VRIN Client - Main interface for interacting with the VRIN Hybrid RAG system
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

class VRINClient:
    """VRIN Hybrid RAG Client"""
    
    def __init__(self, api_key: str):
        """
        Initialize VRIN client
        
        Args:
            api_key: Your VRIN API key
        """
        self.api_key = api_key
        self.rag_base_url = "https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev"  # VRIN Main API Gateway
        self.auth_base_url = "https://gp7g651udc.execute-api.us-east-1.amazonaws.com/Prod"  # Auth API Gateway URL
        
        # Headers for all requests
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def insert_text(self, text: str, title: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """
        Insert plain text into the knowledge base with fact extraction
        
        Args:
            text: The text content to insert
            title: Optional title for the content
            tags: Optional list of tags
            
        Returns:
            Dict containing job information and extracted facts
        """
        try:
            payload = {
                'content': text,
                'title': title or 'Untitled',
                'tags': tags or []
            }
            
            response = requests.post(
                f"{self.rag_base_url}/insert",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': result.get('success', True),
                    'chunk_id': result.get('chunk_id'),
                    'facts_extracted': result.get('facts_count', result.get('facts_extracted', 0)),
                    'facts': result.get('facts', []),
                    'message': result.get('message', 'Text processed successfully'),
                    'storage_optimization': result.get('storage_optimization'),
                    'chunk_stored': result.get('chunk_stored'),
                    'chunk_storage_reason': result.get('chunk_storage_reason', 'unknown'),
                    'storage_details': result.get('storage_details', ''),
                    'processing_time': result.get('processing_time'),
                    'storage_result': result.get('storage_result', {})
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def insert(self, content: str, title: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """
        Insert structured content into the knowledge base
        
        Args:
            content: The content to insert
            title: Optional title for the content
            tags: Optional list of tags
            
        Returns:
            Dict containing job information
        """
        return self.insert_text(content, title, tags)
    
    def insert_and_wait(self, content: str, title: str = None, tags: List[str] = None, timeout: int = 300) -> Dict[str, Any]:
        """
        Insert content and wait for processing to complete
        
        Args:
            content: The content to insert
            title: Optional title for the content
            tags: Optional list of tags
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dict containing processing results
        """
        # Insert content
        result = self.insert(content, title, tags)
        
        if not result['success']:
            return result
        
        # Wait for processing (fact extraction is synchronous)
        return result
    
    def batch_insert(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Insert multiple pieces of content
        
        Args:
            contents: List of dicts with 'content', 'title', and 'tags' keys
            
        Returns:
            List of results for each insertion
        """
        results = []
        
        for content_dict in contents:
            result = self.insert(
                content=content_dict.get('content', ''),
                title=content_dict.get('title'),
                tags=content_dict.get('tags', [])
            )
            results.append(result)
        
        return results
    
    def query(self, query: str, include_summary: bool = True, include_raw_results: bool = False) -> Dict[str, Any]:
        """
        Query the knowledge base with optimized Hybrid RAG retrieval
        
        Args:
            query: The query string
            include_summary: Whether to include AI-generated summary (default: True)
            include_raw_results: Whether to include raw graph facts and vector results (default: False)
            
        Returns:
            Dict containing comprehensive query results with summary and metadata
        """
        try:
            payload = {
                'query': query,
                'include_summary': include_summary
            }
            
            response = requests.post(
                f"{self.rag_base_url}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Prepare clean response for the client
                search_time = result.get('search_time', 0)
                if isinstance(search_time, str):
                    search_time_str = search_time
                else:
                    search_time_str = f"{float(search_time):.2f}s"
                
                response_data = {
                    'success': result.get('success', True),
                    'query': result.get('query', query),
                    'summary': result.get('summary', 'No relevant information found.'),
                    'search_time': search_time_str,
                    'entities_found': result.get('entities', []),
                    'total_facts': result.get('total_facts', 0),
                    'total_chunks': result.get('total_chunks', 0),
                    'combined_results': len(result.get('combined_results', [])),
                    'multi_hop_chains': result.get('multi_hop_chains', 0),
                    'cross_document_patterns': result.get('cross_document_patterns', 0),
                    'reasoning_confidence': result.get('reasoning_confidence', 0.0),
                    'reasoning_depth': result.get('reasoning_depth', 0.0),
                    'multi_document_coverage': result.get('multi_document_coverage', 0),
                    # NEW v0.7.0: Constraint solver metadata
                    'constraints': result.get('constraints', {}),
                    'constraints_applied': result.get('constraints_applied', 0),
                    'temporal_filtering_applied': result.get('temporal_filtering_applied', False),
                    'facts_before_filtering': result.get('facts_before_filtering', 0),
                    'facts_after_filtering': result.get('facts_after_filtering', 0)
                }
                
                # Add raw results if requested (for advanced users)
                if include_raw_results:
                    response_data.update({
                        'graph_facts': result.get('graph_facts', []),
                        'vector_results': result.get('vector_results', []),
                        'combined_results': result.get('combined_results', [])
                    })
                
                return response_data
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def get_raw_results(self, query: str) -> Dict[str, Any]:
        """
        Get raw query results with full graph facts and vector chunks
        
        Args:
            query: The query string
            
        Returns:
            Dict containing all raw results from the optimized hybrid system
        """
        return self.query(query, include_summary=True, include_raw_results=True)
    
    def get_facts(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Get detailed facts and raw search results without summary generation (fastest response)
        
        Args:
            query: The query string
            max_results: Maximum number of results to return
            
        Returns:
            Dict containing detailed facts, graph traversal data, and raw results without summary
        """
        try:
            payload = {
                'query': query,
                'include_summary': False,  # Skip summary for fastest response
                'max_results': max_results
            }
            
            response = requests.post(
                f"{self.rag_base_url}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse search time
                search_time = result.get('search_time', 0)
                if isinstance(search_time, str) and search_time.endswith('s'):
                    search_time_num = float(search_time.replace('s', ''))
                else:
                    search_time_num = float(search_time) if search_time else 0
                
                return {
                    'success': True,
                    'query': query,
                    'entry_points': result.get('entry_points', []),
                    'optimal_hops': result.get('optimal_hops', 2),
                    'graph_facts': result.get('graph_facts', []),
                    'vector_results': result.get('vector_results', []),
                    'combined_results': result.get('combined_results', []),
                    'search_time': search_time,
                    'search_time_seconds': search_time_num,
                    'total_facts': result.get('total_facts', 0),
                    'total_chunks': result.get('total_chunks', 0),
                    'entities': result.get('entities', []),
                    'multi_hop_chains': result.get('multi_hop_chains', 0),
                    'cross_document_patterns': result.get('cross_document_patterns', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def get_raw_facts_only(self, query: str) -> Dict[str, Any]:
        """
        Get raw facts ONLY without any summary generation for timing benchmarks
        
        Args:
            query: The query string
            
        Returns:
            Dict containing only fact retrieval results and timing
        """
        return self.query(query, include_summary=False, include_raw_results=True)
    
    def get_knowledge_graph(self) -> Dict[str, Any]:
        """
        Get knowledge graph visualization data
        
        Returns:
            Dict containing knowledge graph nodes and edges
        """
        try:
            response = requests.get(
                f"{self.rag_base_url}/graph",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a processing job
        
        Args:
            job_id: The job ID to check
            
        Returns:
            Dict containing job status information
        """
        try:
            response = requests.get(
                f"{self.rag_base_url}/job-status/{job_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login to get an API key
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict containing API key and user information
        """
        try:
            payload = {
                'email': email,
                'password': password
            }
            
            response = requests.post(
                f"{self.auth_base_url}/login",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'api_key': result.get('api_key'),
                    'user_id': result.get('user_id'),
                    'message': 'Login successful'
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def register(self, email: str, password: str, name: str = None) -> Dict[str, Any]:
        """
        Register a new user account
        
        Args:
            email: User email
            password: User password
            name: Optional user name
            
        Returns:
            Dict containing registration result
        """
        try:
            payload = {
                'email': email,
                'password': password,
                'name': name or email.split('@')[0]
            }
            
            response = requests.post(
                f"{self.auth_base_url}/register",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'api_key': result.get('api_key'),
                    'user_id': result.get('user_id'),
                    'message': 'Registration successful'
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }     
    def _generate_summary(self, query: str, result: Dict) -> str:
        """
        Generate an intelligent summary from search results
        
        Args:
            query: The original query
            result: Raw search results from the backend
            
        Returns:
            Curated summary text
        """
        # Extract key information from results
        graph_facts = result.get('graph_facts', [])
        vector_results = result.get('vector_results', [])
        combined_results = result.get('combined_results', [])
        
        # If we have results, create a summary
        if not (graph_facts or vector_results or combined_results):
            return f"I couldn't find specific information about '{query}' in the knowledge base. You may want to add more knowledge on this topic or try a different query."
        
        # Build summary from available information
        summary_parts = []
        
        # Add key facts from graph traversal
        if graph_facts:
            top_facts = graph_facts[:3]  # Top 3 most relevant facts
            for fact in top_facts:
                if isinstance(fact, dict):
                    subject = fact.get('subject', '')
                    predicate = fact.get('predicate', '')
                    obj = fact.get('object', '')
                    if subject and predicate and obj:
                        summary_parts.append(f"{subject} {predicate} {obj}")
        
        # Add information from vector search results
        if vector_results:
            top_chunks = vector_results[:2]  # Top 2 most relevant chunks
            for chunk in top_chunks:
                if isinstance(chunk, dict):
                    content = chunk.get('content', '')
                    if content and len(content) > 50:
                        # Extract the most relevant sentence
                        sentences = content.split('.')
                        if sentences:
                            summary_parts.append(sentences[0].strip() + '.')
        
        # Combine and format the summary
        if summary_parts:
            summary = "Based on the available knowledge: " + " ".join(summary_parts[:3])
            # Ensure reasonable length
            if len(summary) > 300:
                summary = summary[:297] + "..."
            return summary
        else:
            return f"Found {len(graph_facts + vector_results)} relevant sources for '{query}', but couldn't extract clear information. Try using get_facts() for detailed results."
    
    def _calculate_confidence(self, result: Dict) -> float:
        """
        Calculate confidence score based on search results quality
        
        Args:
            result: Raw search results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence factors
        graph_facts_count = len(result.get('graph_facts', []))
        vector_results_count = len(result.get('vector_results', []))
        search_time = result.get('search_time', 0)
        
        # Calculate confidence based on multiple factors
        confidence = 0.5  # Base confidence
        
        # Boost confidence with more facts
        if graph_facts_count > 0:
            confidence += min(0.3, graph_facts_count * 0.1)
        
        # Boost confidence with vector results
        if vector_results_count > 0:
            confidence += min(0.2, vector_results_count * 0.05)
        
        # Penalize very fast searches (might indicate no deep search)
        if search_time > 0.5:
            confidence += 0.1
        
        # Cap confidence at 1.0
        return min(1.0, confidence)
    
    def specialize(self, custom_prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Configure VRIN's reasoning approach using your custom prompt engineering
        
        Args:
            custom_prompt: Your custom prompt that describes how VRIN should analyze and reason
                          for your specific use case. This will be used as additional prompt 
                          engineering layer during backend operations.
            **kwargs: Optional additional configuration parameters:
                - reasoning_focus: List of reasoning types to prioritize
                - analysis_depth: "surface", "detailed", or "expert" 
                - confidence_threshold: Minimum confidence for insights (0-1)
                - max_reasoning_chains: Maximum reasoning paths to explore (1-20)
        
        Returns:
            Dict containing specialization result
        """
        # Build specialization config with user's custom prompt
        specialization_config = {
            "custom_prompt": custom_prompt,
            "reasoning_focus": kwargs.get("reasoning_focus", ["entity_relationships", "cross_document_synthesis"]),
            "analysis_depth": kwargs.get("analysis_depth", "detailed"),
            "confidence_threshold": kwargs.get("confidence_threshold", 0.6),
            "max_reasoning_chains": kwargs.get("max_reasoning_chains", 8)
        }
        
        try:
            response = requests.post(
                f"{self.rag_base_url}/specialize",
                headers=self.headers,
                json=specialization_config,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def get_specialization(self) -> Dict[str, Any]:
        """
        Get current user specialization settings
        
        Returns:
            Dict containing current specialization configuration
        """
        try:
            response = requests.get(
                f"{self.rag_base_url}/specialize",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
