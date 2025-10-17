from dataclasses import dataclass
import logging
from typing import List, Optional

from ..adapters.base_adapter import LLMAdapterBase
from ..errors.llm_api_error import LLMAPIError
from ..llms.google.sync_client import GeminiSyncClient
from ..models.messages.chat_message import Message
from ..models.responses.chat_response import ChatResponse

logger = logging.getLogger(__name__)


@dataclass
class GoogleAdapter(LLMAdapterBase):
    company: str = "google"

    def generate_chat_answer(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        top_p: float = 1.0
    ) -> ChatResponse:
        temperature = self._validate_parameter(
            name="temperature", value=temperature, min_value=0, max_value=2
        )
        top_p = self._validate_parameter(
            name="top_p", value=top_p, min_value=0, max_value=1
        )
        try:
            transformed_messages = []
            prompt = None
            for msg in messages:
                if hasattr(msg, "role") and hasattr(msg, "content"):
                    if msg.role == "system" or isinstance(msg, ()):
                        pass
                    if isinstance(msg, type) and msg == "Prompt":
                        prompt = {
                            "parts": [{"text": msg.content}]
                        }
                    else:
                        transformed_messages.append({
                            "role": "user" if msg.role == "user" else "model",
                            "parts": [{"text": msg.content}]
                        })
            payload = {
                "contents": transformed_messages,
                **({"system_instruction": prompt} if prompt else {}),
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p,
                },
            }
            client = GeminiSyncClient(self.api_key)
            response_json = client.chat_completion(
                model=self.model,
                **payload
            )
            chat_response = ChatResponse.from_google_response(response_json)
            if self.pricing:
                chat_response.apply_pricing(
                    price_input_per_token=self.pricing.in_per_token,
                    price_output_per_token=self.pricing.out_per_token,
                    currency=self.pricing.currency
                )
            return chat_response
        except LLMAPIError as e:
            self.handle_error(e)
        except Exception as e:
            error_message = getattr(e, "text", None) or str(e)
            self.handle_error(error=e, error_message=error_message)
