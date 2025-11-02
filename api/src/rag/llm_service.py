"""Multi-provider LLM service for RAG system"""

import os
from typing import List, Dict, Any, Optional
from api.src.config import settings

# Try to import all LLM providers, handle gracefully if not available
PROVIDERS_AVAILABLE = {}

try:
    import openai
    PROVIDERS_AVAILABLE['openai'] = True
except ImportError:
    PROVIDERS_AVAILABLE['openai'] = False

try:
    import groq
    PROVIDERS_AVAILABLE['groq'] = True
except ImportError:
    PROVIDERS_AVAILABLE['groq'] = False

try:
    import anthropic
    PROVIDERS_AVAILABLE['anthropic'] = True
except ImportError:
    PROVIDERS_AVAILABLE['anthropic'] = False

try:
    import requests
    PROVIDERS_AVAILABLE['ollama'] = True
except ImportError:
    PROVIDERS_AVAILABLE['ollama'] = False


class LLMService:
    """Multi-provider LLM service with automatic fallback"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.client = None
        self.embedding_client = None
        
        # Initialize clients in order of preference
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on availability and configuration"""
        
        # Try Groq first (free and fast)
        if self._try_groq():
            self.provider = "groq"
            return
        
        # Fall back to OpenAI
        if self._try_openai():
            self.provider = "openai"
            return
        
        # Fall back to Anthropic
        if self._try_anthropic():
            self.provider = "anthropic"
            return
        
        # Fall back to Ollama (local)
        if self._try_ollama():
            self.provider = "ollama"
            return
        
        print("Warning: No LLM providers available. Using mock responses.")
        self.provider = "mock"
    
    def _try_groq(self):
        """Try to initialize Groq client"""
        if not PROVIDERS_AVAILABLE.get('groq'):
            return False
        
        groq_key = settings.GROQ_API_KEY or os.getenv('GROQ_API_KEY')
        if not groq_key:
            print("Groq API key not found. Set GROQ_API_KEY environment variable.")
            return False
        
        try:
            self.client = groq.Groq(api_key=groq_key)
            # Test the client
            self.client.models.list()
            print(f"✅ Groq client initialized successfully with model: {settings.GROQ_MODEL}")
            return True
        except Exception as e:
            print(f"❌ Could not initialize Groq client: {e}")
            return False
    
    def _try_openai(self):
        """Try to initialize OpenAI client"""
        if not PROVIDERS_AVAILABLE.get('openai'):
            return False
        
        openai_key = settings.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("OpenAI API key not found.")
            return False
        
        try:
            self.client = openai.OpenAI(api_key=openai_key)
            self.embedding_client = self.client  # Same client for embeddings
            # Test the client
            self.client.models.list()
            print(f"✅ OpenAI client initialized successfully with model: {settings.OPENAI_MODEL}")
            return True
        except Exception as e:
            print(f"❌ Could not initialize OpenAI client: {e}")
            return False
    
    def _try_anthropic(self):
        """Try to initialize Anthropic client"""
        if not PROVIDERS_AVAILABLE.get('anthropic'):
            return False
        
        anthropic_key = settings.ANTHROPIC_API_KEY or os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_key:
            print("Anthropic API key not found.")
            return False
        
        try:
            self.client = anthropic.Anthropic(api_key=anthropic_key)
            print(f"✅ Anthropic client initialized successfully with model: {settings.ANTHROPIC_MODEL}")
            return True
        except Exception as e:
            print(f"❌ Could not initialize Anthropic client: {e}")
            return False
    
    def _try_ollama(self):
        """Try to initialize Ollama client (local)"""
        if not PROVIDERS_AVAILABLE.get('ollama'):
            return False
        
        try:
            import requests
            response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✅ Ollama client initialized successfully with model: {settings.OLLAMA_MODEL}")
                return True
        except Exception as e:
            print(f"❌ Could not connect to Ollama: {e}")
            return False
        
        return False
    
    async def generate_completion(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Generate text completion using the available provider"""
        
        if self.provider == "groq":
            return await self._groq_completion(messages, max_tokens)
        elif self.provider == "openai":
            return await self._openai_completion(messages, max_tokens)
        elif self.provider == "anthropic":
            return await self._anthropic_completion(messages, max_tokens)
        elif self.provider == "ollama":
            return await self._ollama_completion(messages, max_tokens)
        else:
            return self._mock_completion(messages)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get text embedding using enhanced embedding service with relationship context"""
        # Import here to avoid circular imports
        from .enhanced_embeddings import enhanced_embedding_service
        
        # Use enhanced embeddings with IM8/Singapore context
        return enhanced_embedding_service.get_enhanced_embedding(text, context_type="im8_compliance")
    
    async def _groq_completion(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Generate completion using Groq"""
        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq completion error: {e}")
            return self._mock_completion(messages)
    
    async def _openai_completion(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Generate completion using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI completion error: {e}")
            return self._mock_completion(messages)
    
    async def _anthropic_completion(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Generate completion using Anthropic"""
        try:
            # Convert messages format for Anthropic
            system_msg = ""
            user_msgs = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_msgs.append(msg)
            
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                system=system_msg,
                messages=user_msgs
            )
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic completion error: {e}")
            return self._mock_completion(messages)
    
    async def _ollama_completion(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Generate completion using Ollama (local)"""
        try:
            import requests
            
            # Convert messages to prompt
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n\nAssistant: "
            
            data = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            print(f"Ollama completion error: {e}")
            return self._mock_completion(messages)
    
    async def _openai_embedding(self, text: str) -> List[float]:
        """Get embedding using OpenAI"""
        try:
            response = self.embedding_client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            return self._mock_embedding(text)
    
    def _mock_completion(self, messages: List[Dict[str, str]]) -> str:
        """Generate mock completion for demo purposes"""
        user_message = ""
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"].lower()
                break
        
        if "access control" in user_message or "iam" in user_message:
            return """Based on compliance best practices and regulatory frameworks:

**Access Control Implementation:**

1. **Policy Development**: Establish comprehensive access control policies that define user roles, responsibilities, and access levels based on job functions and least privilege principles.

2. **Identity and Access Management (IAM)**: Implement robust IAM systems that include:
   - User provisioning and deprovisioning processes
   - Role-based access control (RBAC)
   - Multi-factor authentication (MFA)
   - Regular access reviews and certifications

3. **Technical Controls**: Deploy technical safeguards including:
   - Authentication mechanisms
   - Authorization frameworks
   - Session management
   - Audit logging and monitoring

4. **Compliance Alignment**: Ensure implementation meets requirements for ISO 27001, NIST Cybersecurity Framework, and other relevant standards.

**Key Considerations:**
- Regular review and updates of access permissions
- Segregation of duties for sensitive operations
- Monitoring and alerting for unusual access patterns
- Documentation and evidence collection for audit purposes

This implementation should be tailored to your specific organizational needs and regulatory requirements."""

        elif "risk" in user_message:
            return """Risk management is a critical component of cybersecurity compliance:

**Risk Assessment Process:**

1. **Asset Identification**: Catalog all information assets, systems, and processes
2. **Threat Analysis**: Identify potential threats and vulnerabilities
3. **Impact Assessment**: Evaluate potential business impact of security incidents
4. **Risk Calculation**: Determine risk levels using standardized methodologies
5. **Risk Treatment**: Implement appropriate controls and mitigation strategies

**Framework Alignment:**
- ISO 27001 risk management requirements
- NIST RMF (Risk Management Framework)
- Industry-specific guidelines

**Documentation Requirements:**
- Risk registers and assessments
- Treatment plans and timelines
- Regular review and updates
- Executive reporting and approval

Regular risk assessments should be conducted at least annually or when significant changes occur."""

        else:
            return f"""Based on your query about compliance and security practices:

The implementation should follow established frameworks and best practices. Key considerations include:

1. **Regulatory Compliance**: Align with relevant standards (ISO 27001, NIST, SOC 2)
2. **Implementation Planning**: Develop systematic approach with clear timelines
3. **Documentation**: Maintain comprehensive records for audit purposes
4. **Monitoring**: Establish ongoing assessment and improvement processes
5. **Training**: Ensure staff understanding and compliance

For specific guidance on your query, consider consulting with compliance professionals and reviewing applicable regulatory requirements.

*Note: This response is generated using a fallback system. For production use, configure a proper LLM provider (Groq, OpenAI, etc.)*"""
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for demo purposes"""
        import hashlib
        import random
        
        # Use text hash as seed for consistent embeddings
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Generate 1536-dimensional vector (same as OpenAI ada-002)
        embedding = [random.uniform(-1, 1) for _ in range(1536)]
        
        # Normalize vector
        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x/magnitude for x in embedding]
        
        return embedding
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider"""
        return {
            "provider": self.provider,
            "available_providers": {k: v for k, v in PROVIDERS_AVAILABLE.items() if v},
            "model": self._get_current_model(),
            "supports_embeddings": self.provider in ["openai"] or self.provider == "mock"
        }
    
    def _get_current_model(self) -> str:
        """Get the current model name"""
        if self.provider == "groq":
            return settings.GROQ_MODEL
        elif self.provider == "openai":
            return settings.OPENAI_MODEL
        elif self.provider == "anthropic":
            return settings.ANTHROPIC_MODEL
        elif self.provider == "ollama":
            return settings.OLLAMA_MODEL
        else:
            return "mock"


# Global LLM service instance
llm_service = LLMService()