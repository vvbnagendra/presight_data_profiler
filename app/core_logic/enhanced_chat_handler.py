# app/core_logic/enhanced_chat_handler.py
"""
Enhanced Chat Handler with Natural Conversation Flow
- Maintains conversation context
- Uses LLM to understand intent and generate natural responses
- Combines data retrieval with conversational AI
"""

import streamlit as st
import pandas as pd
from typing import List, Tuple, Dict, Any
import json
from datetime import datetime


class ConversationManager:
    """Manages conversation context and history"""
    
    def __init__(self):
        self.conversation_history = []
        self.data_context = {}
        self.last_query_results = None
        
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.conversation_history.append(message)
        
    def get_conversation_context(self, last_n: int = 10) -> str:
        """Get formatted conversation context for LLM"""
        recent_messages = self.conversation_history[-last_n:]
        context = []
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                context.append(f"User: {msg['content']}")
            elif msg['role'] == 'assistant':
                context.append(f"Assistant: {msg['content']}")
            elif msg['role'] == 'system':
                context.append(f"[System: {msg['content']}]")
                
        return "\n".join(context)
    
    def set_data_context(self, dataframes: List[Tuple[str, pd.DataFrame]]):
        """Store information about available dataframes"""
        self.data_context = {}
        
        for name, df in dataframes:
            self.data_context[name] = {
                'columns': list(df.columns),
                'shape': df.shape,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'sample_values': {col: df[col].dropna().head(3).tolist() for col in df.columns[:5]}
            }
    
    def get_data_context_summary(self) -> str:
        """Get a summary of available data for LLM"""
        if not self.data_context:
            return "No data available."
        
        summary = ["Available datasets and their structure:\n"]
        
        for name, info in self.data_context.items():
            summary.append(f"Dataset: {name}")
            summary.append(f"  - Rows: {info['shape'][0]:,}, Columns: {info['shape'][1]}")
            summary.append(f"  - Columns: {', '.join(info['columns'][:10])}")
            if len(info['columns']) > 10:
                summary.append(f"    ... and {len(info['columns']) - 10} more columns")
            summary.append("")
        
        return "\n".join(summary)
    
    def store_query_results(self, results: Any):
        """Store the last query results for follow-up questions"""
        self.last_query_results = results
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.last_query_results = None


class IntentClassifier:
    """Classifies user intent to determine how to handle the query"""
    
    INTENT_TYPES = {
        'data_query': 'User wants to query or analyze data',
        'follow_up': 'User is asking a follow-up question about previous results',
        'clarification': 'User is asking for clarification or explanation',
        'greeting': 'User is greeting or having casual conversation',
        'help': 'User needs help or guidance',
        'visualization': 'User wants to create a chart or visualization',
        'comparison': 'User wants to compare data points',
        'summary': 'User wants a summary or overview'
    }
    
    def classify_intent(self, user_message: str, conversation_context: str, model_backend: str, 
                       model_name: str, api_key: str) -> Dict[str, Any]:
        """Classify the intent of the user's message"""
        
        # Build classification prompt
        prompt = self._build_classification_prompt(user_message, conversation_context)
        
        # Get LLM classification
        try:
            classification = self._call_llm_for_classification(
                prompt, model_backend, model_name, api_key
            )
            return classification
        except Exception as e:
            # Fallback to rule-based classification
            return self._rule_based_classification(user_message, conversation_context)
    
    def _build_classification_prompt(self, user_message: str, conversation_context: str) -> str:
        """Build prompt for intent classification"""
        
        intent_descriptions = "\n".join([f"- {key}: {desc}" for key, desc in self.INTENT_TYPES.items()])
        
        prompt = f"""You are an intent classifier for a data analysis chatbot. Analyze the user's message and classify their intent.

Available Intent Types:
{intent_descriptions}

Conversation Context:
{conversation_context}

Current User Message: "{user_message}"

Analyze the message and respond with ONLY a JSON object in this exact format:
{{
    "intent": "one of: data_query, follow_up, clarification, greeting, help, visualization, comparison, summary",
    "confidence": 0.0 to 1.0,
    "requires_data_access": true or false,
    "is_follow_up": true or false,
    "key_entities": ["list", "of", "key", "terms"],
    "reasoning": "brief explanation"
}}

DO NOT include any text before or after the JSON object."""
        
        return prompt
    
    def _call_llm_for_classification(self, prompt: str, model_backend: str, 
                                     model_name: str, api_key: str) -> Dict[str, Any]:
        """Call LLM to classify intent"""
        
        if model_backend == "ollama":
            return self._call_ollama(prompt, model_name)
        elif model_backend == "huggingface":
            return self._call_huggingface(prompt, model_name, api_key)
        elif model_backend == "google":
            return self._call_google(prompt, model_name, api_key)
        else:
            raise ValueError(f"Unsupported backend: {model_backend}")
    
    def _call_ollama(self, prompt: str, model: str) -> Dict[str, Any]:
        """Call Ollama API for classification"""
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=30
        )
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        # Extract JSON from response
        return self._parse_json_response(response_text)
    
    def _call_huggingface(self, prompt: str, model: str, api_key: str) -> Dict[str, Any]:
        """Call HuggingFace API for classification"""
        import requests
        
        response = requests.post(
            "https://router.huggingface.co/novita/v3/openai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            },
            timeout=30
        )
        
        result = response.json()
        response_text = result["choices"][0]["message"]["content"]
        
        return self._parse_json_response(response_text)
    
    def _call_google(self, prompt: str, model: str, api_key: str) -> Dict[str, Any]:
        """Call Google API for classification"""
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(model)
        
        response = model_obj.generate_content(prompt)
        response_text = response.text.strip()
        
        return self._parse_json_response(response_text)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        # Remove markdown code blocks if present
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # Fallback
            return self._create_default_classification()
    
    def _rule_based_classification(self, user_message: str, conversation_context: str) -> Dict[str, Any]:
        """Fallback rule-based classification"""
        
        message_lower = user_message.lower()
        
        # Greeting patterns
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return {
                'intent': 'greeting',
                'confidence': 0.9,
                'requires_data_access': False,
                'is_follow_up': False,
                'key_entities': [],
                'reasoning': 'Greeting detected'
            }
        
        # Help patterns
        if any(word in message_lower for word in ['help', 'how to', 'what can you', 'guide']):
            return {
                'intent': 'help',
                'confidence': 0.8,
                'requires_data_access': False,
                'is_follow_up': False,
                'key_entities': [],
                'reasoning': 'Help request detected'
            }
        
        # Follow-up patterns
        if any(word in message_lower for word in ['that', 'it', 'them', 'those', 'these', 'more', 'also']):
            if conversation_context:
                return {
                    'intent': 'follow_up',
                    'confidence': 0.7,
                    'requires_data_access': True,
                    'is_follow_up': True,
                    'key_entities': [],
                    'reasoning': 'Follow-up question with context'
                }
        
        # Visualization patterns
        if any(word in message_lower for word in ['plot', 'chart', 'graph', 'visualize', 'show me']):
            return {
                'intent': 'visualization',
                'confidence': 0.8,
                'requires_data_access': True,
                'is_follow_up': False,
                'key_entities': [],
                'reasoning': 'Visualization request'
            }
        
        # Default to data query
        return {
            'intent': 'data_query',
            'confidence': 0.6,
            'requires_data_access': True,
            'is_follow_up': False,
            'key_entities': [],
            'reasoning': 'Default classification'
        }
    
    def _create_default_classification(self) -> Dict[str, Any]:
        """Create default classification"""
        return {
            'intent': 'data_query',
            'confidence': 0.5,
            'requires_data_access': True,
            'is_follow_up': False,
            'key_entities': [],
            'reasoning': 'Default fallback'
        }


class NaturalResponseGenerator:
    """Generates natural, conversational responses"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conversation_manager = conversation_manager
    
    def generate_response(self, user_message: str, intent: Dict[str, Any], 
                         data_results: Any, model_backend: str, 
                         model_name: str, api_key: str) -> str:
        """Generate a natural response based on intent and data results"""
        
        # Build response prompt
        prompt = self._build_response_prompt(user_message, intent, data_results)
        
        try:
            # Get LLM response
            response = self._call_llm_for_response(
                prompt, model_backend, model_name, api_key
            )
            return response
        except Exception as e:
            return self._generate_fallback_response(intent, data_results, str(e))
    
    def _build_response_prompt(self, user_message: str, intent: Dict[str, Any], 
                               data_results: Any) -> str:
        """Build prompt for response generation"""
        
        conversation_context = self.conversation_manager.get_conversation_context()
        data_context = self.conversation_manager.get_data_context_summary()
        
        # Convert data results to text description
        data_description = self._describe_data_results(data_results)
        
        prompt = f"""You are a friendly and helpful data analysis assistant. Generate a natural, conversational response.

Conversation Context:
{conversation_context}

Available Data:
{data_context}

User's Current Message: "{user_message}"

Detected Intent: {intent['intent']} (confidence: {intent['confidence']:.2f})

Data Query Results:
{data_description}

Guidelines for your response:
1. Be conversational and natural (avoid robotic language)
2. Reference the data results in a clear, human-friendly way
3. If showing numbers, format them nicely (e.g., "1,234" not "1234")
4. Provide context and insights, not just raw data
5. Suggest follow-up questions if relevant
6. Keep responses concise but informative
7. Use emojis sparingly for emphasis (max 1-2)
8. If data shows interesting patterns, point them out

Generate a helpful, natural response:"""
        
        return prompt
    
    def _describe_data_results(self, data_results: Any) -> str:
        """Convert data results to text description"""
        
        if data_results is None:
            return "No data results available."
        
        # Handle different types of results
        if isinstance(data_results, pd.DataFrame):
            if len(data_results) == 0:
                return "The query returned no results."
            
            description = [
                f"Query returned {len(data_results)} rows.",
                f"Columns: {', '.join(data_results.columns)}",
                "\nFirst few rows:"
            ]
            
            # Show first 5 rows
            for idx, row in data_results.head(5).iterrows():
                row_desc = ", ".join([f"{col}={val}" for col, val in row.items()])
                description.append(f"  - {row_desc}")
            
            if len(data_results) > 5:
                description.append(f"  ... and {len(data_results) - 5} more rows")
            
            return "\n".join(description)
        
        elif isinstance(data_results, (int, float)):
            return f"The calculation resulted in: {data_results:,}"
        
        elif isinstance(data_results, str):
            return f"Result: {data_results}"
        
        elif isinstance(data_results, dict):
            if 'type' in data_results and 'content' in data_results:
                result_type = data_results['type']
                content = data_results['content']
                
                if result_type == 'dataframe' and isinstance(content, pd.DataFrame):
                    return self._describe_data_results(content)
                elif result_type == 'image':
                    return f"Generated a visualization/chart at: {content}"
                elif result_type == 'error':
                    return f"Error occurred: {content}"
                else:
                    return f"Result: {content}"
        
        return str(data_results)
    
    def _call_llm_for_response(self, prompt: str, model_backend: str, 
                               model_name: str, api_key: str) -> str:
        """Call LLM to generate response"""
        
        if model_backend == "ollama":
            return self._call_ollama(prompt, model_name)
        elif model_backend == "huggingface":
            return self._call_huggingface(prompt, model_name, api_key)
        elif model_backend == "google":
            return self._call_google(prompt, model_name, api_key)
        else:
            raise ValueError(f"Unsupported backend: {model_backend}")
    
    def _call_ollama(self, prompt: str, model: str) -> str:
        """Call Ollama API for response generation"""
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "top_p": 0.9}
            },
            timeout=60
        )
        
        result = response.json()
        return result.get("response", "").strip()
    
    def _call_huggingface(self, prompt: str, model: str, api_key: str) -> str:
        """Call HuggingFace API for response generation"""
        import requests
        
        response = requests.post(
            "https://router.huggingface.co/novita/v3/openai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            },
            timeout=60
        )
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _call_google(self, prompt: str, model: str, api_key: str) -> str:
        """Call Google API for response generation"""
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(model)
        
        response = model_obj.generate_content(prompt)
        return response.text.strip()
    
    def _generate_fallback_response(self, intent: Dict[str, Any], 
                                   data_results: Any, error: str) -> str:
        """Generate fallback response if LLM fails"""
        
        if intent['intent'] == 'greeting':
            return "Hello! I'm here to help you analyze your data. What would you like to explore?"
        
        elif intent['intent'] == 'help':
            return """I can help you analyze your data in several ways:
            
• Ask questions about your data (e.g., "What's the average sales?")
• Create visualizations (e.g., "Show me a chart of revenue by month")
• Compare values (e.g., "Which product has the highest sales?")
• Get summaries (e.g., "Summarize the customer data")

Just ask me anything about your data!"""
        
        elif data_results is not None:
            if isinstance(data_results, pd.DataFrame):
                return f"Found {len(data_results)} results. Here's what I found:\n{data_results.head().to_string()}"
            else:
                return f"Here are the results: {data_results}"
        
        return f"I processed your request. The intent was: {intent['intent']}"


class EnhancedChatHandler:
    """Main handler for enhanced conversational chat"""
    
    def __init__(self):
        if 'conversation_manager' not in st.session_state:
            st.session_state.conversation_manager = ConversationManager()
        
        self.conversation_manager = st.session_state.conversation_manager
        self.intent_classifier = IntentClassifier()
        self.response_generator = NaturalResponseGenerator(self.conversation_manager)
    
    def handle_message(self, user_message: str, dataframes: List[Tuple[str, pd.DataFrame]],
                      llm_backend: str, model_backend: str, model_name: str, 
                      user_token: str) -> Dict[str, Any]:
        """Handle a user message with full conversational flow"""
        
        # Update data context
        self.conversation_manager.set_data_context(dataframes)
        
        # Add user message to history
        self.conversation_manager.add_message('user', user_message)
        
        # Get conversation context
        conversation_context = self.conversation_manager.get_conversation_context()
        
        # Classify intent
        intent = self.intent_classifier.classify_intent(
            user_message, conversation_context, model_backend, model_name, user_token
        )
        
        # Handle based on intent
        if intent['intent'] in ['greeting', 'help']:
            # Handle without data access
            response_text = self.response_generator.generate_response(
                user_message, intent, None, model_backend, model_name, user_token
            )
            
            self.conversation_manager.add_message('assistant', response_text)
            
            return {
                'type': 'text',
                'content': response_text,
                'intent': intent,
                'requires_data': False
            }
        
        elif intent['requires_data_access']:
            # Execute data query
            from core_logic.pandasai_handler import handle_pandasai_query
            from core_logic.lotus_handler import handle_lotus_query
            
            # Enhance query with context if it's a follow-up
            enhanced_query = self._enhance_query_with_context(
                user_message, intent, conversation_context
            )
            
            # Execute query
            if llm_backend == "pandasai":
                data_results = handle_pandasai_query(
                    enhanced_query, dataframes, model_backend, 
                    model_name, user_token, ""
                )
            else:  # lotus
                data_results = handle_lotus_query(
                    enhanced_query, dataframes, model_backend, 
                    model_name, user_token
                )
            
            # Store results
            self.conversation_manager.store_query_results(data_results)
            
            # Generate natural response
            response_text = self.response_generator.generate_response(
                user_message, intent, data_results, model_backend, model_name, user_token
            )
            
            self.conversation_manager.add_message('assistant', response_text, {
                'data_results_type': data_results.get('type') if isinstance(data_results, dict) else type(data_results).__name__
            })
            
            return {
                'type': 'enhanced',
                'natural_response': response_text,
                'data_results': data_results,
                'intent': intent,
                'requires_data': True
            }
        
        else:
            # Clarification or other intent
            response_text = self.response_generator.generate_response(
                user_message, intent, None, model_backend, model_name, user_token
            )
            
            self.conversation_manager.add_message('assistant', response_text)
            
            return {
                'type': 'text',
                'content': response_text,
                'intent': intent,
                'requires_data': False
            }
    
    def _enhance_query_with_context(self, user_message: str, intent: Dict[str, Any], 
                                   conversation_context: str) -> str:
        """Enhance query with context for follow-up questions"""
        
        if not intent.get('is_follow_up', False):
            return user_message
        
        # Get last few messages
        recent_context = conversation_context.split('\n')[-6:]  # Last 3 exchanges
        
        # Build enhanced query
        enhanced = f"""Based on our conversation:
{chr(10).join(recent_context)}

User's follow-up question: {user_message}

Please answer the follow-up question using the context from our conversation."""
        
        return enhanced
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_manager.clear_history()
        st.session_state.conversation_manager = ConversationManager()