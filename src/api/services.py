"""
High-level API operations live here.
Keep HTTP details inside ApiClient; expose simple functions for callers.
"""

import asyncio
from typing import Any, Mapping

from . import api_client, openai_client, OPENAI_MODEL, OPENAI_IMAGE_MODEL
from ..tokens import get_token


async def fetch_status() -> str:
    """
    Example status call. Replace path/handling with your real endpoint.
    """
    if not api_client.is_configured:
        return "API client not configured; using stub status."

    try:
        token = get_token("status")
        payload: Mapping[str, Any] = await api_client.get_json(
            "/status", api_key=token
        )
    except Exception as exc:
        return f"Status check failed: {exc}"

    return str(payload.get("message") or payload or "Status endpoint responded")


async def search_web(query: str, *, max_results: int = 5) -> list[dict[str, str]]:
    """
    Lightweight search powered by duckduckgo-search.
    Runs in a thread to avoid blocking the event loop.
    """
    query = (query or "").strip()
    if not query:
        return []

    try:
        from duckduckgo_search import DDGS
    except Exception as exc:  # ImportError or runtime errors
        return [
            {
                "title": "Search unavailable",
                "url": "",
                "snippet": f"Install duckduckgo-search: {exc}",
            }
        ]

    def _search():
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    try:
        results = await asyncio.to_thread(_search)
    except Exception as exc:
        return [
            {
                "title": "Search failed",
                "url": "",
                "snippet": str(exc),
            }
        ]

    formatted: list[dict[str, str]] = []
    for item in results:
        formatted.append(
            {
                "title": str(item.get("title") or item.get("heading") or "Result"),
                "url": item.get("href") or item.get("url") or item.get("link") or "",
                "snippet": str(
                    item.get("body")
                    or item.get("snippet")
                    or item.get("abstract")
                    or ""
                ).strip(),
            }
        )
    return formatted


async def _refine_prompt_with_chatgpt(prompt: str) -> str:
    """
    Optional helper that nudges the prompt with ChatGPT/Copilot style guidance.
    Falls back to the original prompt on error or missing client.
    """
    if not openai_client:
        return prompt

    try:
        completion = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You turn short ideas into vivid, specific image prompts. "
                        "Reply with a single sentence that is concrete and visual."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=120,
            temperature=0.8,
        )
        content = completion.choices[0].message.content
        refined = (content or "").strip()
        return refined or prompt
    except Exception:
        return prompt


async def generate_image(prompt: str) -> dict[str, str] | str:
    """
    Generate an image via the OpenAI Images API.
    Returns either a dict with url + revised prompt or an error string.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return "Please supply a prompt to generate art."

    if not openai_client:
        return "Image generation is not configured; set OPENAI_API_KEY."

    vivid_prompt = await _refine_prompt_with_chatgpt(prompt)

    try:
        response = await openai_client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=vivid_prompt,
            size="1024x1024",
            n=1,
        )
    except Exception as exc:
        return f"Image generation failed: {exc}"

    data = response.data[0]
    return {
        "url": getattr(data, "url", "") or "",
        "revised_prompt": getattr(data, "revised_prompt", "") or vivid_prompt,
    }
