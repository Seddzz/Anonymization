"""
Command Line Interface for Anonymization Agent
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.executor import AnonymizerPipeline

def main():
    parser = argparse.ArgumentParser(description='Anonymization Agent CLI')
    parser.add_argument('--input', '-i', required=True, help='Input text or file path')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--method', '-m', choices=['llm', 'spacy'], default='spacy', help='Detection method')
    parser.add_argument('--entities', '-e', nargs='+', default=['PERSON', 'EMAIL'], help='Entity types to anonymize')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = AnonymizerPipeline(detector=args.method)
    
    # Process input
    if os.path.isfile(args.input):
        # File input
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        # Direct text input
        text = args.input
    
    # Anonymize
    result = pipeline.anonymize(text, args.entities)
    
    if result['success']:
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result['anonymized_text'])
            print(f"Anonymized text saved to: {args.output}")
        else:
            print("Anonymized text:")
            print(result['anonymized_text'])
            
        print(f"\nEntities found: {len(result['replacement_mapping'])}")
        for original, replacement in result['replacement_mapping'].items():
            print(f"  {original} → {replacement}")
    else:
        print(f"Error: {result.get('error_message', 'Unknown error')}")

if __name__ == '__main__':
    main()