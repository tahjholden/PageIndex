"""
Ollama-compatible utilities for PageIndex
This module provides Ollama support by using OpenAI-compatible API endpoints
"""
import tiktoken
import openai
import logging
import os
from datetime import datetime
import time
import json
import PyPDF2
import copy
import asyncio
import pymupdf
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()
import logging
import yaml
from pathlib import Path
from types import SimpleNamespace as config

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")  # Ollama doesn't require auth, but some clients need a key
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"

# Fallback to OpenAI if not using Ollama
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY") if not USE_OLLAMA else OLLAMA_API_KEY

def get_openai_client(api_key=None, base_url=None):
    """Get OpenAI client configured for either OpenAI or Ollama"""
    if USE_OLLAMA:
        return openai.OpenAI(
            api_key=OLLAMA_API_KEY,
            base_url=OLLAMA_BASE_URL
        )
    else:
        return openai.OpenAI(api_key=api_key or CHATGPT_API_KEY)

def get_async_openai_client(api_key=None, base_url=None):
    """Get async OpenAI client configured for either OpenAI or Ollama"""
    if USE_OLLAMA:
        return openai.AsyncOpenAI(
            api_key=OLLAMA_API_KEY,
            base_url=OLLAMA_BASE_URL
        )
    else:
        return openai.AsyncOpenAI(api_key=api_key or CHATGPT_API_KEY)

def count_tokens(text, model=None):
    """Count tokens - for Ollama models, use a simple approximation"""
    if not text:
        return 0
    
    # For Ollama models, use a simple character-based approximation
    # (1 token ≈ 4 characters for most models)
    if USE_OLLAMA or (model and not model.startswith("gpt")):
        return len(text) // 4
    
    # For OpenAI models, use tiktoken
    try:
        enc = tiktoken.encoding_for_model(model or "gpt-4o-2024-11-20")
        tokens = enc.encode(text)
        return len(tokens)
    except Exception:
        # Fallback to approximation if tiktoken fails
        return len(text) // 4

def ChatGPT_API_with_finish_reason(model, prompt, api_key=CHATGPT_API_KEY, chat_history=None):
    max_retries = 10
    client = get_openai_client(api_key=api_key)
    for i in range(max_retries):
        try:
            if chat_history:
                messages = chat_history
                messages.append({"role": "user", "content": prompt})
            else:
                messages = [{"role": "user", "content": prompt}]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )
            if response.choices[0].finish_reason == "length":
                return response.choices[0].message.content, "max_output_reached"
            else:
                return response.choices[0].message.content, "finished"

        except Exception as e:
            print('************* Retrying *************')
            logging.error(f"Error: {e}")
            if i < max_retries - 1:
                time.sleep(1)  # Wait for 1秒 before retrying
            else:
                logging.error('Max retries reached for prompt: ' + prompt)
                return "Error"

def ChatGPT_API(model, prompt, api_key=CHATGPT_API_KEY, chat_history=None):
    max_retries = 10
    client = get_openai_client(api_key=api_key)
    for i in range(max_retries):
        try:
            if chat_history:
                messages = chat_history
                messages.append({"role": "user", "content": prompt})
            else:
                messages = [{"role": "user", "content": prompt}]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )
   
            return response.choices[0].message.content
        except Exception as e:
            print('************* Retrying *************')
            logging.error(f"Error: {e}")
            if i < max_retries - 1:
                time.sleep(1)  # Wait for 1秒 before retrying
            else:
                logging.error('Max retries reached for prompt: ' + prompt)
                return "Error"

async def ChatGPT_API_async(model, prompt, api_key=CHATGPT_API_KEY):
    max_retries = 10
    messages = [{"role": "user", "content": prompt}]
    for i in range(max_retries):
        try:
            async with get_async_openai_client(api_key=api_key) as client:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0,
                )
                return response.choices[0].message.content
        except Exception as e:
            print('************* Retrying *************')
            logging.error(f"Error: {e}")
            if i < max_retries - 1:
                await asyncio.sleep(1)  # Wait for 1s before retrying
            else:
                logging.error('Max retries reached for prompt: ' + prompt)
                return "Error"

# Re-export other utility functions that don't need modification
from .utils import (
    get_json_content,
    extract_json,
    get_page_tokens,
    # Add other functions as needed
)
