#!/usr/bin/env python3
"""Simple document redactor using Ollama to identify and hash named entities."""

import argparse
import hashlib
import re
import requests
import sys
from pathlib import Path

def get_entity_hash(entity, salt):
    """Generate consistent hash for an entity."""
    return hashlib.sha256(f"{entity}{salt}".encode()).hexdigest()[:8]

def mark_entities_with_ollama(text, model="llama3"):
    """Ask Ollama to mark named entities in text."""
    prompt = f"""Mark all proper names (people, organizations, places) with <E> tags.
Return the same text with only tags added.

Example: John Smith works at Google → <E>John Smith</E> works at <E>Google</E>

Text: {text}"""
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30
        )
        return response.json().get("response", text)
    except:
        print("Warning: Ollama unavailable, returning original text", file=sys.stderr)
        return text

def redact_document(input_path, output_path, salt, model="llama3"):
    """Redact named entities in a document."""
    # Read input
    text = Path(input_path).read_text(encoding='utf-8')
    
    # Get marked text from Ollama
    marked = mark_entities_with_ollama(text, model)
    
    # Replace marked entities with hashes
    entity_map = {}
    def replace_entity(match):
        entity = match.group(1)
        if entity not in entity_map:
            entity_map[entity] = f"[REDACTED_{get_entity_hash(entity, salt)}]"
        return entity_map[entity]
    
    redacted = re.sub(r'<E>(.*?)</E>', replace_entity, marked)
    
    # Write output
    Path(output_path).write_text(redacted, encoding='utf-8')
    
    return len(entity_map)

def main():
    parser = argparse.ArgumentParser(description="Redact named entities using Ollama")
    parser.add_argument("input", help="Input document")
    parser.add_argument("-o", "--output", help="Output document (default: input_redacted)")
    parser.add_argument("-s", "--salt", required=True, help="Secret salt for hashing")
    parser.add_argument("-m", "--model", default="llama3", help="Ollama model (default: llama3)")
    
    args = parser.parse_args()
    
    # Set default output path
    if not args.output:
        p = Path(args.input)
        args.output = p.with_name(f"{p.stem}_redacted{p.suffix}")
    
    # Check input exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return 1
    
    # Check Ollama is running
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
    except:
        print("Error: Ollama not running. Start with: ollama serve", file=sys.stderr)
        return 1
    
    # Redact document
    try:
        count = redact_document(args.input, args.output, args.salt, args.model)
        print(f"Redacted {count} unique entities → {args.output}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())