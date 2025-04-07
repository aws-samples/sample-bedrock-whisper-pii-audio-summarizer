import boto3
import json
import logging
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def test_phone_redaction(guardrail_id, region="us-east-1", guardrail_version="DRAFT"):
    """
    Test specifically if the guardrail can redact phone numbers
    
    Args:
        guardrail_id (str): The ARN or ID of the Bedrock guardrail
        region (str): AWS region where the guardrail is deployed
        guardrail_version (str): Guardrail version to test, e.g., "DRAFT"
    """
    # Create Boto3 client for Bedrock Runtime
    bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name=region)
    
    # Sample text with phone number only
    test_text = """
    Hello, my phone number is (208)-333-7789. 
    Please call me at this number if you need any assistance.
    """
    
    print("===== ORIGINAL TEXT =====")
    print(test_text)
    
    try:
        # Format content according to API requirements
        formatted_content = [
            {
                "text": {
                    "text": test_text
                }
            }
        ]
        
        # Try with source=OUTPUT
        print("\n===== TESTING WITH source=OUTPUT =====")
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source="OUTPUT",
            content=formatted_content
        )
        
        print(f"Action: {response.get('action')}")
        print(f"Has outputs: {'Yes' if 'outputs' in response and response['outputs'] else 'No'}")
        
        # Print the full response for inspection
        print("\n===== FULL API RESPONSE =====")
        print(json.dumps(response, indent=2))
        
        # Try to extract the redacted text using the same logic as in the Lambda function
        extracted_text = None
        if 'action' in response and response['action'] == 'GUARDRAIL_INTERVENED' and 'outputs' in response and response['outputs']:
            if len(response['outputs']) > 0:
                output = response['outputs'][0]
                
                # Try different formats of where the text might be
                if 'text' in output and isinstance(output['text'], dict) and 'text' in output['text']:
                    extracted_text = output['text']['text']
                elif 'text' in output and isinstance(output['text'], str):
                    extracted_text = output['text']
                elif 'content' in output:
                    if isinstance(output['content'], str):
                        extracted_text = output['content']
                    elif isinstance(output['content'], dict) and 'text' in output['content']:
                        extracted_text = output['content']['text']
        
        if extracted_text:
            print("\n===== EXTRACTED REDACTED TEXT =====")
            print(extracted_text)
            
            if "(208)-333-7789" not in extracted_text:
                print("\n✅ SUCCESS: Phone number was redacted!")
            else:
                print("\n❌ FAILURE: Phone number was NOT redacted.")
        else:
            print("\n❌ Could not extract redacted text from the response")
            
        # Also try with source=INPUT for comparison
        print("\n===== TESTING WITH source=INPUT =====")
        response_input = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source="INPUT",
            content=formatted_content
        )
        
        print(f"Action: {response_input.get('action')}")
        print(f"Has outputs: {'Yes' if 'outputs' in response_input and response_input['outputs'] else 'No'}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Bedrock guardrail phone number redaction capabilities')
    parser.add_argument('--guardrail-id', required=True, help='ARN or ID of your Bedrock guardrail')
    parser.add_argument('--region', default='us-east-1', help='AWS region where your guardrail is deployed')
    parser.add_argument('--version', default='DRAFT', help='Guardrail version to test')
    args = parser.parse_args()
    
    print("Testing phone number redaction with your configured guardrail...\n")
    test_phone_redaction(
        guardrail_id=args.guardrail_id,
        region=args.region,
        guardrail_version=args.version
    )
