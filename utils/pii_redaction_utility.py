import json
import boto3
import re
import argparse

def regex_pii_redaction(text):
    """
    A reliable function to redact common PII patterns using regex
    """
    # Redact names (common patterns like "my name is..." or "I am...")
    text = re.sub(r'(?i)(my name is|I am|I\'m|This is) ([A-Z][a-z]+ [A-Z][a-z]+)', r'\1 [NAME REDACTED]', text)
    
    # Redact email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]', text)
    
    # Redact phone numbers (various formats)
    text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[PHONE REDACTED]', text)
    
    # Redact credit card numbers
    text = re.sub(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[CREDIT CARD REDACTED]', text)
    
    # Redact SSNs
    text = re.sub(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', '[SSN REDACTED]', text)
    
    # Redact addresses (basic pattern)
    text = re.sub(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Terrace|Ter|Way),?\s+[A-Za-z\s]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?\b', '[ADDRESS REDACTED]', text)
    
    return text

def bedrock_guardrail_redaction(text, guardrail_id):
    """
    Apply Bedrock Guardrail to content for redaction
    """
    try:
        # Create Boto3 client for Bedrock Runtime
        bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
        
        # Format content according to the API requirements
        formatted_content = [
            {
                "text": {
                    "text": text
                }
            }
        ]
        
        # Call the guardrail API
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion="DRAFT",
            source="INPUT",
            content=formatted_content
        )
        
        # Extract redacted text from the response
        if 'outputs' in response and response['outputs'] and len(response['outputs']) > 0:
            if 'text' in response['outputs'][0] and 'text' in response['outputs'][0]['text']:
                return response['outputs'][0]['text']['text']
        
        # If no redacted output, use regex fallback
        print("No redacted output from guardrail. Using regex fallback.")
        return regex_pii_redaction(text)
    except Exception as e:
        print(f"Error applying guardrail: {str(e)}")
        # Return regex-redacted content if guardrail application fails
        print("Using regex fallback due to error.")
        return regex_pii_redaction(text)

def process_file(input_file, output_file, guardrail_id=None):
    """Process a file containing text to redact PII"""
    with open(input_file, 'r') as f:
        text = f.read()
    
    print(f"Processing file: {input_file}")
    print(f"Original length: {len(text)} characters")
    
    if guardrail_id:
        redacted_text = bedrock_guardrail_redaction(text, guardrail_id)
        print(f"Using Bedrock Guardrail: {guardrail_id}")
    else:
        redacted_text = regex_pii_redaction(text)
        print("Using regex-based redaction")
    
    print(f"Redacted length: {len(redacted_text)} characters")
    
    with open(output_file, 'w') as f:
        f.write(redacted_text)
    
    print(f"Redacted text written to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Redact PII from text content')
    parser.add_argument('input_file', nargs='?', help='Input file containing text to redact')
    parser.add_argument('output_file', nargs='?', help='Output file to write redacted text')
    parser.add_argument('--guardrail', help='Bedrock Guardrail ID (ARN)')
    parser.add_argument('--demo', action='store_true', help='Run demonstration with sample text')
    
    args = parser.parse_args()
    
    # If demo flag is set, run the demo regardless of other arguments
    if args.demo:
        sample_text = """
        Hello, my name is John Smith and I work at Amazon.
        My personal email is john.smith@example.com and my phone number is (123) 456-7890.
        My credit card number is 4111-1111-1111-1111 and my SSN is 123-45-6789.
        I live at 123 Main Street, Seattle, WA 98101.
        
        We discussed violence and harmful activities during our meeting.
        The project budget is $500,000 and we need to complete it by June 2025.
        """
        
        print("===== ORIGINAL TEXT =====")
        print(sample_text)
        
        print("\n===== REGEX REDACTED TEXT =====")
        regex_result = regex_pii_redaction(sample_text)
        print(regex_result)
        
        if args.guardrail:
            print("\n===== BEDROCK GUARDRAIL REDACTED TEXT =====")
            guardrail_result = bedrock_guardrail_redaction(sample_text, args.guardrail)
            print(guardrail_result)
    else:
        # Check if required arguments are provided for normal operation
        if not args.input_file or not args.output_file:
            parser.print_help()
            print("\nError: input_file and output_file are required unless --demo is used")
            return
        process_file(args.input_file, args.output_file, args.guardrail)

if __name__ == "__main__":
    main()
