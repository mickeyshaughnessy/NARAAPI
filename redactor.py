############
# THINKING
#🤔🤔🤔🤠
# Need to:
# 1. Switch from spaCy to Ollama client for Llama 3
# 2. Create a structured prompt for Llama 3 to identify named entities
# 3. Parse JSON response from Llama to get entity positions
# 4. Keep hashing and replacement logic similar
# 5. Update dependencies and error handling
# 6. Process text in chunks if needed (large docs)
#</thinking>
############

import argparse
import json
import os
import sys
import re
import requests
from pathlib import Path

def query_llama(text, model="llama3"):
    """Query Ollama API with Llama 3 model for named entity recognition"""
    prompt = f"""
    Identify all proper names (people, organizations, places) in the following text. 
    Return ONLY a JSON array of objects with these properties:
    - text: the entity text
    - start: character position where entity starts
    - end: character position where entity ends
    - type: either "PERSON", "ORG", or "GPE" (geographical/political entity)
    
    Text to analyze:
    {text}
    
    Return ONLY the JSON array without any explanation:
    """
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=30
        )
        response.raise_for_status()
        
        # Extract JSON from Llama's response
        result = response.json()
        content = result.get("response", "")
        
        # Extract JSON array using regex in case model adds extra text
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            entities = json.loads(json_match.group(0))
        else:
            # Try direct parsing if regex fails
            entities = json.loads(content)
            
        return entities
        
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error querying Llama: {e}", file=sys.stderr)
        return []

def redact_document(input_path, output_path, secret_salt, model="llama3", chunk_size=4000):
    """Redact proper names in document using Llama for NER"""
    # Track replacements for consistency
    replacements = {}
    entity_count = 0
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # Process in chunks if text is large
    if len(text) > chunk_size:
        # For simplicity in this version, we'll just process the whole text
        # A more complex solution would handle splitting and position tracking
        pass
    
    # Get entities from Llama
    entities = query_llama(text, model)
    
    # Sort entities by start position (reversed to avoid offset issues)
    entities.sort(key=lambda x: x["start"], reverse=True)
    
    # Redact each entity
    for entity in entities:
        entity_text = entity["text"]
        start = entity["start"]
        end = entity["end"]
        
        if entity_text not in replacements:
            # Create hash for this entity
            replacements[entity_text] = str(hash(entity_text + secret_salt))
        
        # Replace entity with its hash
        text = text[:start] + f"[REDACTED:{replacements[entity_text]}]" + text[end:]
        entity_count += 1
    
    # Write redacted text to output file
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(text)
    
    return entity_count

def main():
    parser = argparse.ArgumentParser(description="Redact proper names in a document using Llama 3")
    parser.add_argument("input", help="Path to input document")
    parser.add_argument("-o", "--output", help="Path to output document")
    parser.add_argument("-s", "--salt", required=True, help="Secret salt for hashing")
    parser.add_argument("-m", "--model", default="llama3", help="Ollama model name (default: llama3)")
    
    args = parser.parse_args()
    
    # Default output filename if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.with_stem(f"{input_path.stem}_redacted"))
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        return 1
    
    try:
        # Check if Ollama is running
        try:
            requests.get("http://localhost:11434/api/tags", timeout=2)
        except requests.RequestException:
            print("Error: Ollama service not found at localhost:11434.", file=sys.stderr)
            print("Make sure Ollama is running and llama3 model is pulled:", file=sys.stderr)
            print("  $ ollama pull llama3", file=sys.stderr)
            return 1
            
        # Redact the document
        count = redact_document(args.input, args.output, args.salt, args.model)
        print(f"Redacted {count} entities. Result saved to {args.output}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())