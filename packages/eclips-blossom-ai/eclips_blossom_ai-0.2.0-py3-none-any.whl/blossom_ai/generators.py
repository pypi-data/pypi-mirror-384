"""
Blossom AI - Generators (Fixed)
Fixed version with proper session handling and temperature parameter support
"""

from urllib.parse import quote
from typing import Optional, Dict, Any, List
import asyncio
import json

from .base_client import BaseAPI, AsyncBaseAPI
from .errors import BlossomError, ErrorType, print_warning


# ============================================================================
# IMAGE GENERATOR
# ============================================================================

class ImageGenerator(BaseAPI):
    """Generate images using Pollinations.AI"""

    def __init__(self, timeout: int = 30, api_token: Optional[str] = None):
        super().__init__("https://image.pollinations.ai", timeout, api_token=api_token)

    def generate(
            self,
            prompt: str,
            model: str = "flux",
            width: int = 1024,
            height: int = 1024,
            seed: Optional[int] = None,
            nologo: bool = False,
            private: bool = False,
            enhance: bool = False,
            safe: bool = False
    ) -> bytes:
        """
        Generate an image from a text prompt

        Args:
            prompt: Text description of the image
            model: Model to use (default: flux)
            width: Image width in pixels
            height: Image height in pixels
            seed: Seed for reproducible results
            nologo: Remove Pollinations logo (requires registration)
            private: Keep image private
            enhance: Enhance prompt with LLM
            safe: Enable strict NSFW filtering

        Returns:
            Image data as bytes
        """
        MAX_PROMPT_LENGTH = 200
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise BlossomError(
                message=f"Prompt exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters.",
                error_type=ErrorType.INVALID_PARAM,
                suggestion="Please shorten your prompt."
            )

        encoded_prompt = quote(prompt)
        url = f"{self.base_url}/prompt/{encoded_prompt}"

        params = {
            "model": model,
            "width": width,
            "height": height,
        }

        if seed is not None:
            params["seed"] = seed
        if nologo:
            params["nologo"] = "true"
        if private:
            params["private"] = "true"
        if enhance:
            params["enhance"] = "true"
        if safe:
            params["safe"] = "true"

        response = self._make_request("GET", url, params=params)
        return response.content

    def save(
            self,
            prompt: str,
            filename: str,
            **kwargs
    ) -> str:
        """
        Generate and save image to file

        Args:
            prompt: Text description of the image
            filename: Path to save the image
            **kwargs: Additional arguments for generate()

        Returns:
            Path to saved file
        """
        image_data = self.generate(prompt, **kwargs)
        with open(filename, 'wb') as f:
            f.write(image_data)
        return str(filename)

    def models(self) -> list:
        """Get list of available image models"""
        url = f"{self.base_url}/models"
        response = self._make_request("GET", url)
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # If the server returns empty response or non-JSON content, return default models
            print_warning(f"Failed to parse models response: {e}")
            return ["flux", "kontext", "turbo", "gptimage"]


class AsyncImageGenerator(AsyncBaseAPI):
    """Generate images using Pollinations.AI asynchronously"""

    def __init__(self, timeout: int = 30, api_token: Optional[str] = None):
        super().__init__("https://image.pollinations.ai", timeout, api_token=api_token)

    async def generate(
            self,
            prompt: str,
            model: str = "flux",
            width: int = 1024,
            height: int = 1024,
            seed: Optional[int] = None,
            nologo: bool = False,
            private: bool = False,
            enhance: bool = False,
            safe: bool = False
    ) -> bytes:
        """
        Generate an image from a text prompt asynchronously
        """
        MAX_PROMPT_LENGTH = 200
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise BlossomError(
                message=f"Prompt exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters.",
                error_type=ErrorType.INVALID_PARAM,
                suggestion="Please shorten your prompt."
            )

        encoded_prompt = quote(prompt)
        url = f"{self.base_url}/prompt/{encoded_prompt}"

        params = {
            "model": model,
            "width": width,
            "height": height,
        }

        if seed is not None:
            params["seed"] = seed
        if nologo:
            params["nologo"] = "true"
        if private:
            params["private"] = "true"
        if enhance:
            params["enhance"] = "true"
        if safe:
            params["safe"] = "true"

        response = await self._make_request("GET", url, params=params)
        return await response.read()

    async def save(
            self,
            prompt: str,
            filename: str,
            **kwargs
    ) -> str:
        """
        Generate and save image to file asynchronously
        """
        image_data = await self.generate(prompt, **kwargs)
        with open(filename, 'wb') as f:
            f.write(image_data)
        return str(filename)

    async def models(self) -> list:
        """Get list of available image models asynchronously"""
        url = f"{self.base_url}/models"
        response = await self._make_request("GET", url)
        try:
            return await response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # If the server returns empty response or non-JSON content, return default models
            print_warning(f"Failed to parse models response: {e}")
            return ["flux", "kontext", "turbo", "gptimage"]


# ============================================================================
# TEXT GENERATOR
# ============================================================================

class TextGenerator(BaseAPI):
    """Generate text using Pollinations.AI"""

    def __init__(self, timeout: int = 30, api_token: Optional[str] = None):
        super().__init__("https://text.pollinations.ai", timeout, api_token=api_token)

    def generate(
            self,
            prompt: str,
            model: str = "openai",
            system: Optional[str] = None,
            seed: Optional[int] = None,
            temperature: Optional[float] = None,
            json_mode: bool = False,
            private: bool = False
    ) -> str:
        """
        Generate text from a prompt

        Args:
            prompt: Text prompt to generate from
            model: Model to use (default: openai)
            system: System message to guide generation
            seed: Seed for reproducible results
            temperature: Sampling temperature (0.0-2.0, default: 1.0)
            json_mode: Force JSON output format
            private: Keep generation private

        Returns:
            Generated text
        """
        MAX_PROMPT_LENGTH = 10000
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise BlossomError(
                message=f"Prompt exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters.",
                error_type=ErrorType.INVALID_PARAM,
                suggestion="Please shorten your prompt."
            )

        encoded_prompt = quote(prompt)
        url = f"{self.base_url}/{encoded_prompt}"

        params = {
            "model": model,
        }

        if system:
            params["system"] = system
        if seed is not None:
            params["seed"] = seed
        if temperature is not None:
            params["temperature"] = temperature
        if json_mode:
            params["json"] = "true"
        if private:
            params["private"] = "true"

        response = self._make_request("GET", url, params=params)
        return response.text

    def chat(
            self,
            messages: List[Dict[str, Any]],
            model: str = "openai",
            temperature: Optional[float] = None,
            stream: bool = False,
            json_mode: bool = False,
            private: bool = False
    ) -> str:
        """
        Chat completion using OpenAI-compatible endpoint (POST method)
        """
        url = f"{self.base_url}/openai"

        body = {
            "model": model,
            "messages": messages
        }

        # FIXED: Only add temperature if it's the default value (1.0) or not specified
        # The API only supports temperature=1.0
        if temperature is not None:
            if temperature != 1.0:
                print_warning(f"Temperature {temperature} is not supported. Using default value 1.0")
            body["temperature"] = 1.0

        if stream:
            body["stream"] = stream
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if private:
            body["private"] = private

        try:
            response = self._make_request(
                "POST",
                url,
                json=body,
                headers={"Content-Type": "application/json"}
            )

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            # Fallback to GET method if POST fails
            user_message = None
            system_message = None

            for msg in messages:
                if msg.get("role") == "user":
                    user_message = msg.get("content")
                elif msg.get("role") == "system":
                    system_message = msg.get("content")

            if user_message:
                return self.generate(
                    prompt=user_message,
                    model=model,
                    system=system_message,
                    # FIXED: Don't pass temperature to GET fallback since it's not supported
                    json_mode=json_mode,
                    private=private
                )
            raise

    def models(self) -> List[str]:
        """Get list of available text models"""
        url = f"{self.base_url}/models"
        response = self._make_request("GET", url)
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # If the server returns empty response or non-JSON content, return default models
            print_warning(f"Failed to parse models response: {e}")
            return ["deepseek", "gemini", "mistral", "openai", "qwen-coder"]


class AsyncTextGenerator(AsyncBaseAPI):
    """Generate text using Pollinations.AI asynchronously"""

    def __init__(self, timeout: int = 30, api_token: Optional[str] = None):
        super().__init__("https://text.pollinations.ai", timeout, api_token=api_token)

    async def generate(
            self,
            prompt: str,
            model: str = "openai",
            system: Optional[str] = None,
            seed: Optional[int] = None,
            temperature: Optional[float] = None,
            json_mode: bool = False,
            private: bool = False
    ) -> str:
        """
        Generate text from a prompt asynchronously
        """
        MAX_PROMPT_LENGTH = 10000
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise BlossomError(
                message=f"Prompt exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters.",
                error_type=ErrorType.INVALID_PARAM,
                suggestion="Please shorten your prompt."
            )

        encoded_prompt = quote(prompt)
        url = f"{self.base_url}/{encoded_prompt}"

        params = {
            "model": model,
        }

        if system:
            params["system"] = system
        if seed is not None:
            params["seed"] = seed
        if temperature is not None:
            params["temperature"] = temperature
        if json_mode:
            params["json"] = "true"
        if private:
            params["private"] = "true"

        response = await self._make_request("GET", url, params=params)
        return await response.text()

    async def chat(
            self,
            messages: List[Dict[str, Any]],
            model: str = "openai",
            temperature: Optional[float] = None,
            stream: bool = False,
            json_mode: bool = False,
            private: bool = False,
            use_get_fallback: bool = True
    ) -> str:
        """
        Chat completion using OpenAI-compatible endpoint asynchronously (POST method)
        """
        url = f"{self.base_url}/openai"

        body = {
            "model": model,
            "messages": messages
        }

        # FIXED: Only add temperature if it's the default value (1.0) or not specified
        # The API only supports temperature=1.0
        if temperature is not None:
            if temperature != 1.0:
                print_warning(f"Temperature {temperature} is not supported. Using default value 1.0")
            body["temperature"] = 1.0

        if stream:
            body["stream"] = stream
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if private:
            body["private"] = private

        try:
            response = await self._make_request(
                "POST",
                url,
                json=body,
                headers={"Content-Type": "application/json"}
            )

            result = await response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            if use_get_fallback:
                user_message = None
                system_message = None

                for msg in messages:
                    if msg.get("role") == "user":
                        user_message = msg.get("content")
                    elif msg.get("role") == "system":
                        system_message = msg.get("content")

                if user_message:
                    return await self.generate(
                        prompt=user_message,
                        model=model,
                        system=system_message,
                        # FIXED: Don't pass temperature to GET fallback since it's not supported
                        json_mode=json_mode,
                        private=private
                    )
            raise

    async def models(self) -> List[str]:
        """Get list of available text models asynchronously"""
        url = f"{self.base_url}/models"
        response = await self._make_request("GET", url)
        try:
            return await response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # If the server returns empty response or non-JSON content, return default models
            print_warning(f"Failed to parse models response: {e}")
            return ["deepseek", "gemini", "mistral", "openai", "qwen-coder"]


# ============================================================================
# AUDIO GENERATOR
# ============================================================================

class AudioGenerator(BaseAPI):
    """Generate audio using Pollinations.AI"""

    def __init__(self, timeout: int = 30, api_token: Optional[str] = None):
        super().__init__("https://text.pollinations.ai", timeout, api_token=api_token)

    def generate(
            self,
            text: str,
            voice: str = "alloy",
            model: str = "openai-audio"
    ) -> bytes:
        """
        Generate speech audio from text (Text-to-Speech)
        """
        text = text.rstrip('.!?;:,');

        encoded_text = quote(text)
        # ИСПРАВЛЕНО: используем тот же формат что и для текста (БЕЗ /prompt/)
        url = f"{self.base_url}/{encoded_text}"

        params = {
            "model": model,
            "voice": voice
        }

        response = self._make_request("GET", url, params=params)
        return response.content

    def save(
            self,
            text: str,
            filename: str,
            **kwargs
    ) -> str:
        """
        Generate and save audio to file
        """
        audio_data = self.generate(text, **kwargs)
        with open(filename, 'wb') as f:
            f.write(audio_data)
        return str(filename)

    def voices(self) -> List[str]:
        """Get list of available voices"""
        url = f"{self.base_url}/voices"
        response = self._make_request("GET", url)
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # If the server returns empty response or non-JSON content, return default voices
            print_warning(f"Failed to parse voices response: {e}")
            return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


class AsyncAudioGenerator(AsyncBaseAPI):
    """Generate audio using Pollinations.AI asynchronously"""

    def __init__(self, timeout: int = 30, api_token: Optional[str] = None):
        super().__init__("https://text.pollinations.ai", timeout, api_token=api_token)

    async def generate(
            self,
            text: str,
            voice: str = "alloy",
            model: str = "openai-audio"
    ) -> bytes:
        """
        Generate speech audio from text asynchronously (Text-to-Speech)
        """
        text = text.rstrip('.!?;:,')

        encoded_text = quote(text)
        # ИСПРАВЛЕНО: используем тот же формат что и для текста (БЕЗ /prompt/)
        url = f"{self.base_url}/{encoded_text}"

        params = {
            "model": model,
            "voice": voice
        }

        response = await self._make_request("GET", url, params=params)
        return await response.read()

    async def save(
            self,
            text: str,
            filename: str,
            **kwargs
    ) -> str:
        """
        Generate and save audio to file asynchronously
        """
        audio_data = await self.generate(text, **kwargs)
        with open(filename, 'wb') as f:
            f.write(audio_data)
        return str(filename)

    async def voices(self) -> List[str]:
        """Get list of available voices asynchronously"""
        url = f"{self.base_url}/voices"
        response = await self._make_request("GET", url)
        try:
            return await response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # If the server returns empty response or non-JSON content, return default voices
            print_warning(f"Failed to parse voices response: {e}")
            return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]