import boto3
import json

def test_guardrail_with_source(source_type):
    """
    Test the guardrail functionality used in the Lambda function directly.
    This simulates how the Lambda will process content through the guardrail.
    """
    # Create Boto3 client for Bedrock Runtime - same as in Lambda
    bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
    
    # Guardrail ID - same as in Lambda
    guardrail_id = "arn:aws:bedrock:us-east-1:064080936720:guardrail/p8upn739dsqw"
    guardrail_version = "DRAFT"
    
    # Sample text with PII - simulating a transcription
    test_text = """
    Speaker 1: Hello everyone, my name is John Smith and I'm calling from Seattle.
    Speaker 2: Hi John, this is Jane Doe. My phone number is (555) 123-4567.
    Speaker 1: I'll be sending the project files to your email john.doe@example.com.
    Speaker 2: Great, we also need to discuss the quarterly budget of $250,000.
    Speaker 1: I'll share my credit card details for the expenses: 4111-1111-1111-1111.
    Speaker 2: Let's schedule our next meeting for June 15th at my address: 123 Main Street, Seattle, WA 98101.
    """
    
    print("===== ORIGINAL TEXT =====")
    print(test_text)
    
    try:
        # Format content according to the API requirements - same as in Lambda
        formatted_content = [
            {
                "text": {
                    "text": test_text
                }
            }
        ]
        
        # Call the guardrail API with the specified source type
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source=source_type, 
            content=formatted_content
        )
        
        print("\n===== API RESPONSE =====")
        print(f"Action: {response.get('action')}")
        print(f"Has outputs: {'Yes' if 'outputs' in response and response['outputs'] else 'No'}")
        
        # Display redacted text if available - same logic as in Lambda
        if 'outputs' in response and response['outputs'] and len(response['outputs']) > 0:
            if 'text' in response['outputs'][0] and 'text' in response['outputs'][0]['text']:
                redacted_text = response['outputs'][0]['text']['text']
                print("\n===== REDACTED TEXT =====")
                print(redacted_text)
                
                if test_text != redacted_text:
                    print("\n✅ SUCCESS: Guardrail successfully redacted content!")
                else:
                    print("\n⚠️ WARNING: No content was redacted!")
            else:
                print("\n⚠️ No text field in the output")
        else:
            print("\n⚠️ No outputs in the response")
            
        # Show stats from the guardrail
        if 'usage' in response:
            print("\n===== GUARDRAIL STATS =====")
            print(json.dumps(response['usage'], indent=2))
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("Testing Lambda guardrail integration with your configured guardrail...")
    
    print("\n------------------------------------------")
    print("TESTING WITH source=\"INPUT\" (default in Lambda)")
    print("------------------------------------------")
    test_guardrail_with_source("INPUT")
    
    print("\n------------------------------------------")
    print("TESTING WITH source=\"OUTPUT\" (alternative to try)")
    print("------------------------------------------")
    test_guardrail_with_source("OUTPUT")
    
    print("\nIf one of these tests is successful, update your Lambda function to use that source parameter.")
    print("The source parameter that works depends on how you've configured your guardrail in the AWS console.")
