#!/usr/bin/env python3
"""
Redaction Guesser Demo
Uses Ollama API with Llama3 to guess redacted names in text
"""

import json
import requests
import sys
import re

def dedact_text(redacted_text, ollama_url="http://localhost:11434"):
    """
    Send redacted text to Ollama and get dedacted version
    """
    
    # The prompt that instructs the model how to dedact
    system_prompt = """You are an intelligent dedactor submodule - you take redacted text with <<ReDActiONs>> in double brackets and return your most educated guess for the real names.

Like:
  "... and then <<57326hf>> became the highest scoring basketball player of all time." --> "... and then LeBron James became the highest scoring basketball player of all time."

or:

"<<75i83>> was the president of the USA when the Confederacy was defeated. He was later assassinated by <<8349jfu>> in a theater." --> "Abraham Lincoln was the president of the USA when the Confederacy was defeated. He was later assassinated by John Wilkes Booth in a theater."

Only return the dedacted text, nothing else."""

    # Prepare the request
    payload = {
        "model": "llama3",
        "prompt": f"{system_prompt}\n\nRedacted text: {redacted_text}\n\nDedacted text: ",
        "stream": False,
        "temperature": 0.7
    }
    
    try:
        # Make the API call
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Error: No response from model")
        else:
            return f"Error: API returned status code {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Is it running on localhost:11434?"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # Check if filename provided
    if len(sys.argv) != 2:
        print("Usage: python dedact.py <input_file>")
        print("\nExample input file content:")
        print('The famous scientist <<abc123>> developed the theory of relativity.')
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Read the redacted text
    try:
        with open(input_file, 'r') as f:
            redacted_text = f.read().strip()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Check if text contains redactions
    if not re.search(r'<<[^>]+>>', redacted_text):
        print("Warning: No redactions found in the input text (looking for <<...>> pattern)")
    
    print("Original redacted text:")
    print("-" * 50)
    print(redacted_text)
    print("-" * 50)
    
    print("\nSending to Ollama for dedaction...")
    
    # Get dedacted version
    dedacted_text = dedact_text(redacted_text)
    
    print("\nDedacted text:")
    print("-" * 50)
    print(dedacted_text)
    print("-" * 50)
    
    # Optionally save to output file
    output_file = input_file.replace('.txt', '_dedacted.txt')
    if output_file == input_file:
        output_file = input_file + '_dedacted'
    
    try:
        with open(output_file, 'w') as f:
            f.write(dedacted_text)
        print(f"\nDedacted text saved to: {output_file}")
    except Exception as e:
        print(f"\nCould not save output file: {e}")

if __name__ == "__main__":
    main()