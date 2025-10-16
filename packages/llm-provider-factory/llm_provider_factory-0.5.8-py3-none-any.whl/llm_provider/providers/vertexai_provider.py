"""Google Cloud Vertex AI/Gen AI provider implementation."""

from typing import Optional, AsyncIterator, List, Dict, Any
import os
import httpx
import asyncio

from ..base_provider import BaseLLMProvider
from ..settings import (
    GenerationRequest, 
    GenerationResponse, 
    StreamChunk, 
    ProviderInfo,
    Message,
    MessageRole
)
from ..utils.config import ProviderConfig, VertexAIConfig
from ..utils.exceptions import (
    InvalidConfigurationError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ModelNotAvailableError,
    GenerationError
)
from ..utils.logger import logger

# Import Google Gen AI SDK with proper error handling
try:
    # YENİ: Google Gen AI SDK - sadece Client'ı kullan
    from google.genai import Client
    from google.genai import types as genai_types 
    from google.cloud import aiplatform # Diğer Vertex AI özellikleri için
    import google.auth
    from google.auth.transport.requests import Request
    
    GENAI_AVAILABLE = True
except ImportError as e:
    GENAI_AVAILABLE = False
    genai_types = None
    Client = None
    logger.warning(f"⚠️ google-genai import hatası: {e}")
    
# Fallback: Eski Vertex AI SDK'sını da deneyebiliriz
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    GenerativeModel = None


class VertexAIProvider(BaseLLMProvider):
    """Google Cloud Vertex AI/Gen AI LLM sağlayıcısı (Gemini ve Mistral modelleri)"""
    
    SUPPORTED_MODELS = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro", 
        "text-bison", # Bu modeller de eski/deprecated olabilir, Gemini'ye geçilmesi önerilir
        "text-bison-32k",
        "chat-bison",
        "chat-bison-32k",
        "mistral-large-2411",
        "mistral-7b-instruct"
    ]
    
    def __init__(self, config: Optional[VertexAIConfig] = None) -> None:
        """Initialize Vertex AI/Gen AI provider."""
        if config is None:
            config = VertexAIConfig.from_env()
        
        super().__init__(config)
        self.config: VertexAIConfig = config
        self.provider_name = "vertexai"
        self.project_id = config.project_id
        self.location = config.location
        self.model_name = config.model
        self.temperature = config.temperature
        self.max_output_tokens = config.max_tokens
        self.client: Optional[Any] = None # Gen AI Client objesi
        self.model: Optional[Any] = None # GenerativeModel objesi
        
        # Set credentials if provided
        if config.credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.credentials_path
        
        logger.info(f"🔧 Gen AI Provider oluşturuldu: model={self.model_name}, project={self.project_id}")
    
    async def initialize(self) -> None:
        """Initialize Vertex AI client."""
        if not VERTEXAI_AVAILABLE:
            raise InvalidConfigurationError("Vertex AI paketi yüklenmemiş.", "vertexai")
        
        if not self.project_id:
            raise InvalidConfigurationError("Google Cloud Project ID gereklidir.", "vertexai")
        
        try:
            # Google Gen AI Client kullan (yeni API)
            from google import genai
            
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            
            logger.info(f"✅ Gen AI Client başlatıldı: {self.project_id}, location: {self.location}, model: {self.model_name}")
            
        except Exception as e:
            if "authentication" in str(e).lower() or "credentials" in str(e).lower():
                raise AuthenticationError(f"Vertex AI authentication failed: {str(e)}", "vertexai")
            else:
                raise APIError(f"Failed to initialize Vertex AI client: {str(e)}", "vertexai")
    
    def validate_config(self) -> bool:
        """Validate Gen AI configuration."""
        if not self.config.project_id:
            raise InvalidConfigurationError("Google Cloud Project ID gereklidir", "genai")
        
        if self.config.model not in self.SUPPORTED_MODELS:
            logger.warning(f"Model '{self.config.model}' tam desteklenmeyebilir. Desteklenenler: {', '.join(self.SUPPORTED_MODELS)}")
        
        # Check credentials
        if not self.config.credentials_path and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # Bu kontrol Google'ın varsayılan kimlik doğrulama (default authentication) mekanizmasını atlayabilir.
            # Normalde 'gcloud auth application-default login' ile de çalışmalıdır.
            pass
        
        return True
    
    def is_available(self) -> bool:
        """Sağlayıcı kullanılabilir mi?"""
        return GENAI_AVAILABLE and self.model_name is not None and self.project_id is not None

    # Mistral için kullanılan yardımcı fonksiyonlar (değişmedi)
    # _get_credentials_token ve _build_mistral_endpoint_url olduğu gibi kalabilir.
    # ...

    def _convert_messages_to_genai(self, messages: List[Dict], system_prompt: Optional[str] = None) -> List[Any]:
        """Convert a list of generic message dicts to Gen AI SDK Content objects."""
        
        genai_messages = []
        
        # System prompt'u ayrı bir GenerationConfig (veya model oluşturma) parametresi olarak iletmek daha iyidir,
        # ancak mevcut kod yapısını korumak için burada tutuyoruz. Gen AI SDK'da 
        # system instruction'lar için özel bir alan vardır.
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # System mesajları skip et (zaten conversation başında eklendi)
            if role == "system":
                continue
            
            # Gen AI SDK'da 'user' ve 'model' rolleri kullanılır.
            # Sizin MessageRole tanımınıza göre bir eşleme yapalım.
            if role in ["user", "tool"]:
                genai_role = "user"
            elif role in ["assistant"]:
                genai_role = "model"
            else:
                genai_role = "user" # Bilinmeyen roller için varsayılan
                
            genai_messages.append(
                genai_types.Content(
                    role=genai_role,
                    parts=[genai_types.Part(text=content)]
                )
            )
            
        return genai_messages

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response using VertexAI/GenAI.
        
        Args:
            request: The generation request
            
        Returns:
            Generated response
            
        Raises:
            GenerationError: If generation fails
        """
        try:
            await self.ensure_initialized()
            
            # Convert history to internal format if provided
            history = []
            if request.history:
                for msg in request.history:
                    history.append({
                        "role": str(msg.role) if hasattr(msg.role, 'value') else str(msg.role),
                        "content": msg.content
                    })
            
            # Mistral modelleri için özel rawPredict API kullan
            if "mistral" in self.model_name.lower():
                # Get credentials
                credentials, project_id = google.auth.default(
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                credentials.refresh(Request())
                
                # Build endpoint URL
                endpoint = self._build_mistral_endpoint_url()
                
                # Prepare messages
                messages = []
                system_prompt = getattr(request, 'system_prompt', None)
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                if history:
                    for msg in history:
                        messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })
                
                messages.append({"role": "user", "content": request.prompt})
                
                # Prepare request payload
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": self.max_output_tokens,
                    "temperature": self.temperature,
                    "stream": False
                }
                
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json"
                }
                
                logger.info(f"🚀 Mistral API çağrısı: {endpoint}")
                
                # Make HTTP request
                async with httpx.AsyncClient() as client:
                    mistral_response = await client.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=30.0
                    )
                    
                logger.info(f"✅ Mistral API response: {mistral_response.status_code}")
                    
                if mistral_response.status_code != 200:
                    logger.error(f"❌ Mistral API error: {mistral_response.text}")
                    raise APIError(f"Mistral API error: {mistral_response.status_code} - {mistral_response.text}", "vertexai")
                    
                result = mistral_response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    response_text = result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"❌ Unexpected Mistral response: {result}")
                    raise GenerationError("Mistral API response format unexpected", "vertexai")
                
            else:
                # Gemini modelleri için standart Gen AI Client API
                response_text = await self.generate_response(
                    text=request.prompt,
                    system_prompt=getattr(request, 'system_prompt', None),
                    history=history
                )
            
            return GenerationResponse(
                content=response_text,
                provider=self.provider_name,
                model=self.model_name,
                usage={
                    "prompt_tokens": len(request.prompt.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(request.prompt.split()) + len(response_text.split())
                }
            )
            
        except Exception as e:
            logger.error(f"VertexAI generation failed: {e}")
            raise GenerationError(f"VertexAI generation failed: {str(e)}", "vertexai")

    async def generate_response(self, text: str, system_prompt: str = None, history: List[Dict] = None) -> str:
        """Gen AI ile cevap oluştur (Gemini modelleri için)"""
        try:
            await self.ensure_initialized()
            
            # Basit content listesi oluştur
            contents = []
            
            # System prompt varsa başa ekle
            if system_prompt:
                contents.append(f"System: {system_prompt}")
            
            # History varsa ekle
            if history:
                for msg in history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "system":
                        continue  # System zaten eklendi
                    contents.append(f"{role.capitalize()}: {content}")
            
            # Ana mesajı ekle
            contents.append(text)
            
            # Generation config
            config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
            }
            
            logger.info(f"Gen AI'ya gönderiliyor: {len(contents)} content")
            
            # Gen AI Client ile generate et
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Response'u parse et
            if response and response.text:
                answer = response.text.strip()
                logger.info(f"✅ Gen AI cevabı alındı: {len(answer)} karakter")
                return answer
            else:
                logger.warning("⚠️ Gen AI boş cevap döndü")
                return "Üzgünüm, şu anda bir cevap üretemedim."
                
        except Exception as e:
            logger.error(f"❌ Gen AI error: {e}")
            raise GenerationError(f"Gen AI error: {str(e)}", "vertexai")

    async def stream_generate(self, request: GenerationRequest) -> AsyncIterator[StreamChunk]:
        """Stream generate response using Gen AI."""
        # ... Gen AI SDK'ya geçiş yaptıktan sonra, aslında burası da güncellenerek
        # Gen AI SDK'nın kendi stream_generate_content metodu kullanılabilir.
        # Ancak basitlik için mevcut tam cevap üretip parçalama mantığını koruyoruz.
        
        # Tam yanıtı al ve parçala (Eski Mantık)
        try:
            # Mistral için özel stream API'si varsa buraya eklenebilir.
            
            # Gemini/Gen AI için asıl streaming metodu kullanılabilir
            # YENİ: Gen AI SDK streaming metodu
            if "mistral" not in self.model_name.lower() and self.model:
                await self.ensure_initialized()
                
                conversation_history = []
                system_prompt = "Sen yardımcı bir asistansın."

                if request.messages:
                    for msg in request.messages:
                        role_value = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                        if role_value == "system":
                            system_prompt = msg.content
                        else:
                            conversation_history.append({
                                "role": role_value,
                                "content": msg.content
                            })
                    text = conversation_history[-1]["content"] if conversation_history else ""
                elif request.prompt:
                    text = request.prompt
                else:
                    raise GenerationError("Prompt or messages must be provided", "genai")
                
                # System prompt'u conversation başına ekle (eğer henüz yoksa)
                if system_prompt and (not conversation_history or conversation_history[0].get("role") != "system"):
                    conversation_history.insert(0, {"role": "system", "content": system_prompt})
                
                # Son kullanıcı mesajını ekle
                conversation_history.append({"role": "user", "content": text})
                genai_content = self._convert_messages_to_genai(conversation_history)
                
                # Config - Dictionary format kullan
                generation_config = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                }
                
                response_stream = self.model.generate_content_stream(
                    genai_content,
                    generation_config=generation_config
                )
                
                async for chunk in response_stream:
                    if chunk.text:
                        yield StreamChunk(
                            content=chunk.text,
                            model=self.model_name,
                            finish_reason="partial"
                        )
                
                # Son chunk için complete işareti
                yield StreamChunk(content="", model=self.model_name, finish_reason="complete")
                return
            
            # Mistral veya Fallback için (Eski Mantık)
            response = await self.generate(request)
            
            words = response.content.split()
            chunk_size = 5
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                
                yield StreamChunk(
                    content=chunk_text + (" " if i + chunk_size < len(words) else ""),
                    model=self.model_name,
                    finish_reason="partial" if i + chunk_size < len(words) else "complete"
                )
                
        except Exception as e:
            logger.error(f"❌ Gen AI stream generation error: {e}")
            raise GenerationError(f"Gen AI stream generation failed: {str(e)}", "genai")
    
    def get_provider_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name="vertexai",
            display_name="Google Vertex AI",
            description="Google Cloud Vertex AI provider supporting Gemini and Mistral models",
            supported_models=self.SUPPORTED_MODELS,
            capabilities=["text_generation", "conversation", "streaming", "system_messages"],
            is_available=self.is_available()
        )
    
    async def _generate_mistral_response(self, messages: List[Dict]) -> str:
        """Generate response using Mistral model via rawPredict API."""
        try:
            # Get credentials with correct scopes
            credentials, project_id = google.auth.default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            credentials.refresh(Request())
            
            endpoint = self._build_mistral_endpoint_url()
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_output_tokens,
                "temperature": self.temperature
            }
            
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Making Mistral API call to: {endpoint}")
            
            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
            logger.info(f"Mistral API response status: {response.status_code}")
                
            if response.status_code != 200:
                logger.error(f"Mistral API error response: {response.text}")
                raise APIError(f"Mistral API error: {response.status_code} - {response.text}", "vertexai")
                
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected Mistral response format: {result}")
                raise GenerationError("Mistral API response format unexpected", "vertexai")
                
        except Exception as e:
            logger.error(f"Mistral generation failed: {e}")
            raise GenerationError(f"Mistral generation failed: {str(e)}", "vertexai")
    
    def _build_mistral_endpoint_url(self) -> str:
        """Build Mistral endpoint URL for rawPredict API."""
        return (
            f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/"
            f"locations/{self.location}/publishers/mistralai/models/{self.model_name}:rawPredict"
        )