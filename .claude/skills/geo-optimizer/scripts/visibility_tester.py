#!/usr/bin/env python3
"""GEO Visibility Tester - Test brand visibility in AI search engines.

Supports three backends:
  --engine glm         : GLM via Anthropic-compatible proxy (z-ai/glm-5.1) with tool calling (default)
  --engine perplexity  : Perplexity API (sonar-pro, single-call)
  --engine openai      : OpenAI-compatible endpoint (e.g. gpt-4o-mini) on proxy

Configuration auto-detected from ~/.claude/settings.json:
  - ANTHROPIC_AUTH_TOKEN → API key for GLM & OpenAI engines
  - ANTHROPIC_BASE_URL  → proxy base URL
  - ANTHROPIC_MODEL     → model name for GLM engine

Resolution order: CLI flags → env vars → settings.json → defaults
"""

import argparse
import json
import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    requests = None


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------

def _load_claude_settings():
    """Load Claude Code settings from ~/.claude/settings.json."""
    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _resolve_config(api_key=None, model=None, base_url=None,
                    engine="glm"):
    """Resolve API config: CLI → env → settings.json → defaults.

    Returns (api_key, model, base_url).
    """
    settings = _load_claude_settings()
    s_env = settings.get("env", {}) if settings else {}

    # API key
    if not api_key:
        api_key = os.environ.get("GLM_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = s_env.get("ANTHROPIC_AUTH_TOKEN")
    if not api_key and engine == "perplexity":
        api_key = os.environ.get("PERPLEXITY_API_KEY")

    # Base URL — use as-is from settings, no /v4 auto-append
    if not base_url:
        base_url = os.environ.get("GLM_BASE_URL") or os.environ.get("ANTHROPIC_BASE_URL")
    if not base_url:
        base_url = s_env.get("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    base_url = base_url.rstrip("/")

    # Model
    if not model:
        model = os.environ.get("GLM_MODEL") or os.environ.get("ANTHROPIC_MODEL")
    if not model:
        model = s_env.get("ANTHROPIC_MODEL", "glm-4-flash")

    # Strip proxy prefix (e.g. "z-ai/glm-5.1" → "glm-5.1") for OpenAI endpoint
    # but keep it for Anthropic endpoint
    if engine == "openai" and "/" in model:
        model = model.rsplit("/", 1)[-1]

    return api_key, model, base_url


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

DEFAULT_QUERIES = [
    "推荐{keyword}工具，告诉我你推荐了哪些工具，分别说为什么。",
    "帮我对比一下{keyword}领域的主要产品。",
    "{keyword}哪个品牌最值得选择？为什么？",
]


def _build_prompt(keyword, query_template):
    if query_template:
        return query_template.format(keyword=keyword)
    return DEFAULT_QUERIES[0].format(keyword=keyword)


# ---------------------------------------------------------------------------
# Engine: Perplexity (sonar-pro)
# ---------------------------------------------------------------------------

def test_perplexity(brand, keyword, api_key, query_template=None):
    if requests is None:
        return {"error": "requests library not installed. Run: pip install requests"}

    prompt = _build_prompt(keyword, query_template)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers, json=payload, timeout=60,
        )
        resp.raise_for_status()
        response_text = resp.json()["choices"][0]["message"]["content"]
        mentioned = brand.lower() in response_text.lower()
        # Position metric: where the brand appears relative to other tools
        position = None
        if mentioned:
            pos = response_text.lower().find(brand.lower())
            # Count newlines before the brand as a proxy for "how many items before ours"
            position = response_text[:pos].count("\n") + 1
        return {
            "date": datetime.now().isoformat(),
            "engine": "Perplexity",
            "keyword": keyword,
            "brand": brand,
            "cited": mentioned,
            "position": position,
            "context": response_text[:500] if mentioned else "Not cited",
            "full_response_length": len(response_text),
        }
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {e}", "keyword": keyword}
    except Exception as e:
        return {"error": str(e), "keyword": keyword}


# ---------------------------------------------------------------------------
# Engine: GLM via Anthropic-compatible proxy
# Uses Anthropic Messages API format with tool calling.
# Defines a "web_search" function tool that the model can call;
# we implement the search using the Zhipu Web Search API,
# then feed results back for the model to generate a grounded answer.
# If no Zhipu search key is available, falls back to knowledge-only query.
# ---------------------------------------------------------------------------

def _zhipu_web_search(search_query, api_key, search_engine="search_pro"):
    """Call Zhipu's standalone Web Search API."""
    if requests is None:
        return None
    url = "https://open.bigmodel.cn/api/paas/v4/web_search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "search_query": search_query,
        "search_engine": search_engine,
        "search_intent": True,
        "count": 10,
        "search_recency_filter": "noLimit",
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        results = resp.json().get("search_result", [])
        # Format as concise text for injection
        snippets = []
        for r in results[:10]:
            title = r.get("title", "")
            content = r.get("content", "")
            link = r.get("link", "")
            if content:
                snippets.append(f"- {title}: {content}")
        return "\n".join(snippets) if snippets else None
    except Exception:
        return None


def test_glm(brand, keyword, api_key, model=None, base_url=None,
             search_engine="search_pro", api_key_search=None,
             query_template=None):
    """Test brand visibility using GLM via Anthropic-compatible proxy.

    Uses the Anthropic Messages API with tool calling:
    1. Sends the query with a web_search tool definition
    2. If the model calls the tool and we have a Zhipu search API key,
       we execute the search and feed results back
    3. If no search key, we inject search results as context directly
       (the model uses its training knowledge for the answer)
    """
    if requests is None:
        return {"error": "requests library not installed. Run: pip install requests"}

    api_key, model, base_url = _resolve_config(api_key, model, base_url, engine="glm")
    if not api_key:
        return {"error": "No API key. Set GLM_API_KEY or configure ANTHROPIC_AUTH_TOKEN in ~/.claude/settings.json"}

    prompt = _build_prompt(keyword, query_template)
    url = f"{base_url}/v1/messages"

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    system_prompt = (
        "你是一个客观的产品推荐助手，请基于搜索结果回答问题，"
        "列出你找到的所有相关工具和品牌。如果搜索结果中有相关品牌一定要列出。"
    )

    # Define the web_search tool for the model
    tools = [{
        "name": "web_search",
        "description": "Search the web for real-time information about products and brands",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string"
                }
            },
            "required": ["query"]
        }
    }]

    # Step 1: Initial request with tool
    payload = {
        "model": model,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "tools": tools,
    }

    try:
        resp1 = requests.post(url, headers=headers, json=payload, timeout=60)
        resp1.raise_for_status()
        data1 = resp1.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error (step 1): {e}", "keyword": keyword}
    except Exception as e:
        return {"error": f"Step 1 error: {e}", "keyword": keyword}

    # Extract response content and tool calls
    stop_reason = data1.get("stop_reason", "")
    content_blocks = data1.get("content", [])

    # Step 2: Handle tool calls if model wants to search
    if stop_reason == "tool_use":
        # Build the conversation with tool results
        messages = [{"role": "user", "content": prompt}]

        # Process tool_use blocks
        tool_results = []
        for block in content_blocks:
            if block.get("type") == "tool_use":
                tool_input = block.get("input", {})
                search_query = tool_input.get("query", keyword)

                # Try to execute real web search if we have a Zhipu search key
                search_content = None
                search_key = api_key_search or os.environ.get("ZHIPU_SEARCH_API_KEY")
                if search_key:
                    search_content = _zhipu_web_search(search_query, search_key, search_engine)

                if search_content is None:
                    # Fallback: tell the model to use its own knowledge
                    search_content = (
                        f"搜索未执行（无 Zhipu 搜索 API Key）。"
                        f"请基于你的知识回答关于 '{search_query}' 的问题，"
                        f"列出你知道的所有相关品牌。"
                    )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": search_content,
                })

        # Continue conversation with tool results
        payload2 = {
            "model": model,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": 4096,
            "tools": tools,
            "tool_results": tool_results,
        }

        # Add the assistant's response content
        asst_content = []
        for block in content_blocks:
            if block.get("type") == "text":
                asst_content.append({"type": "text", "text": block["text"]})
            elif block.get("type") == "tool_use":
                asst_content.append(block)
        messages.append({"role": "assistant", "content": asst_content or content_blocks})

        # Add tool result as user message
        messages.append({
            "role": "user",
            "content": tool_results,
        })

        try:
            resp2 = requests.post(url, headers=headers, json={
                "model": model,
                "system": system_prompt,
                "messages": messages,
                "max_tokens": 4096,
            }, timeout=60)
            resp2.raise_for_status()
            data2 = resp2.json()
            final_content = data2.get("content", [])
            response_text = "".join(
                b["text"] for b in final_content if b.get("type") == "text"
            )
        except Exception as e:
            return {"error": f"Step 2 error: {e}", "keyword": keyword}
    else:
        # No tool call — model answered directly
        response_text = "".join(
            b["text"] for b in content_blocks if b.get("type") == "text"
        )

    mentioned = brand.lower() in response_text.lower()
    # Position metric: where the brand appears relative to other tools
    position = None
    if mentioned:
        pos = response_text.lower().find(brand.lower())
        position = response_text[:pos].count("\n") + 1
    return {
        "date": datetime.now().isoformat(),
        "engine": "GLM",
        "model": model,
        "keyword": keyword,
        "brand": brand,
        "cited": mentioned,
        "position": position,
        "context": response_text[:500] if mentioned else "Not cited",
        "full_response_length": len(response_text),
    }


# ---------------------------------------------------------------------------
# Engine: OpenAI-compatible (fallback — e.g. gpt-4o-mini on proxy)
# ---------------------------------------------------------------------------

def test_openai(brand, keyword, api_key, model="gpt-4o-mini", base_url=None,
                query_template=None):
    """Test using OpenAI-compatible endpoint (simple chat, no web search)."""
    if requests is None:
        return {"error": "requests library not installed. Run: pip install requests"}

    _, resolved_model, resolved_base = _resolve_config(api_key, model, base_url, engine="openai")
    api_key = resolved_base  # reuse resolved
    api_key, resolved_model, resolved_base = _resolve_config(api_key, model, base_url, engine="openai")

    prompt = _build_prompt(keyword, query_template)
    url = f"{resolved_base}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": "你是一个客观的产品推荐助手，列出你知道的所有相关工具和品牌。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        response_text = resp.json()["choices"][0]["message"]["content"]
        mentioned = brand.lower() in response_text.lower()
        # Position metric: where the brand appears relative to other tools
        position = None
        if mentioned:
            pos = response_text.lower().find(brand.lower())
            position = response_text[:pos].count("\n") + 1
        return {
            "date": datetime.now().isoformat(),
            "engine": "OpenAI",
            "model": resolved_model,
            "keyword": keyword,
            "brand": brand,
            "cited": mentioned,
            "position": position,
            "context": response_text[:500] if mentioned else "Not cited",
            "full_response_length": len(response_text),
        }
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {e}", "keyword": keyword}
    except Exception as e:
        return {"error": str(e), "keyword": keyword}


# ---------------------------------------------------------------------------
# History & orchestration
# ---------------------------------------------------------------------------

def save_history(result, history_file):
    history = []
    if os.path.exists(history_file):
        with open(history_file, encoding="utf-8") as f:
            history = json.load(f)
    history.append(result)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    return history


ENGINES = {
    "glm": {
        "func": test_glm,
        "extra_args": ["model", "base_url", "search_engine", "api_key_search"],
    },
    "perplexity": {"func": test_perplexity, "extra_args": []},
    "openai": {
        "func": test_openai,
        "extra_args": ["model", "base_url"],
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="GEO Visibility Tester (GLM / Perplexity / OpenAI)"
    )
    parser.add_argument("--brand", required=True, help="Brand name to test")
    parser.add_argument("--keywords", nargs="+", required=True, help="Keywords to search")
    parser.add_argument("--engine", default="glm",
                        choices=["glm", "perplexity", "openai"],
                        help="Search engine backend (default: glm)")
    parser.add_argument("--api-key", help="API key (auto-read from ~/.claude/settings.json)")
    parser.add_argument("--model", default=None,
                        help="Model name (auto-detected from settings)")
    parser.add_argument("--base-url", default=None,
                        help="API base URL (auto-detected from settings)")
    parser.add_argument("--search-engine", default="search_pro",
                        choices=["search_std", "search_pro", "search_pro_sogou", "search_pro_quark"],
                        help="GLM search engine type (default: search_pro)")
    parser.add_argument("--api-key-search", default=None,
                        help="Zhipu search API key (for real web search in GLM engine)")
    parser.add_argument("--query", help="Custom query template (use {keyword} placeholder)")
    parser.add_argument("--history", default="visibility_history.json", help="History file path")
    parser.add_argument("--no-save", action="store_true", help="Don't save to history")
    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key
    if not api_key:
        _, _, _ = _resolve_config()
        settings = _load_claude_settings()
        s_env = settings.get("env", {})
        if args.engine == "perplexity":
            api_key = os.environ.get("PERPLEXITY_API_KEY")
        else:
            api_key = os.environ.get("GLM_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                api_key = s_env.get("ANTHROPIC_AUTH_TOKEN")
    if not api_key:
        print("Error: No API key. Set --api-key, GLM_API_KEY env, or ANTHROPIC_AUTH_TOKEN in ~/.claude/settings.json", file=sys.stderr)
        sys.exit(1)

    engine_conf = ENGINES[args.engine]
    test_func = engine_conf["func"]

    all_results = []
    for kw in args.keywords:
        print(f"Testing [{args.engine}]: {kw} ...", file=sys.stderr)

        kwargs = {"brand": args.brand, "keyword": kw, "api_key": api_key, "query_template": args.query}
        if args.engine == "glm":
            kwargs["model"] = args.model
            kwargs["base_url"] = args.base_url
            kwargs["search_engine"] = args.search_engine
            kwargs["api_key_search"] = args.api_key_search
        elif args.engine == "openai":
            kwargs["model"] = args.model
            kwargs["base_url"] = args.base_url

        result = test_func(**kwargs)

        if "error" in result:
            print(f"  Error: {result['error']}", file=sys.stderr)
        else:
            status = f"CITED ✅ (position ~{result.get('position', '?')})" if result["cited"] else "NOT CITED ❌"
            print(f"  {status}", file=sys.stderr)
        all_results.append(result)

        if not args.no_save and "error" not in result:
            save_history(result, args.history)

    print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
