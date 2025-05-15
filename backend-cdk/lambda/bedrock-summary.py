import json
import boto3
import uuid
import logging
import os

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def apply_guardrail(bedrock_runtime, content, guardrail_id, guardrail_version="DRAFT"):
    """
    Apply Bedrock Guardrail to content for redaction
    
    Args:
        bedrock_runtime: Boto3 client for Bedrock Runtime
        content: The text content to apply guardrails to
        guardrail_id: The ID of the guardrail to apply
        guardrail_version: Version of the guardrail to use
        
    Returns:
        The redacted/filtered content
    """
    try:
        # Format content according to the API requirements
        formatted_content = [
            {
                "text": {
                    "text": content
                }
            }
        ]
        
        # Call the guardrail API
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source="OUTPUT",  # Using OUTPUT as the source based on testing
            content=formatted_content
        )
        
        # Check if guardrail intervened and we got outputs
        if 'action' in response and response['action'] == 'GUARDRAIL_INTERVENED' and 'outputs' in response and response['outputs']:
            logger.info(f"Guardrail successfully intervened. Analyzing outputs...")
            
            # Try different response formats
            if len(response['outputs']) > 0:
                output = response['outputs'][0]
                
                # Try standard format
                if 'text' in output and isinstance(output['text'], dict) and 'text' in output['text']:
                    return output['text']['text']
                    
                # Try alternative format where text might be directly in output
                elif 'text' in output and isinstance(output['text'], str):
                    return output['text']
                    
                # Try another alternative where content might be at a different path
                elif 'content' in output:
                    if isinstance(output['content'], str):
                        return output['content']
                    elif isinstance(output['content'], dict) and 'text' in output['content']:
                        return output['content']['text']
                
                # Log the output structure for debugging
                logger.warning(f"Could not extract text from response output: {json.dumps(output)}")
        
        # If no redacted output, log details and return original content
        logger.warning(f"No redacted output from guardrail. Action: {response.get('action')}")
        if 'usage' in response:
            logger.info(f"Guardrail usage stats: {json.dumps(response['usage'])}")
        return content
    except Exception as e:
        logger.error(f"Error applying guardrail: {str(e)}")
        # Return original content if guardrail application fails
        return content

def lambda_handler(event, context):
    # Create Boto3 clients
    s3 = boto3.client('s3')
    bedrock = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
    # Use bedrock-runtime for guardrails, not bedrock-agent-runtime
    bedrock_runtime = bedrock  # reuse the same client for both model invocation and guardrails
    
    # Guardrail ID - using the ARN from environment variable or fallback to default
    guardrail_id = os.environ.get('GUARDRAIL_ID', 'arn:aws:bedrock:us-east-1:064080936720:guardrail/p8upn739dsqw')
    
    # Extract bucket name and object key from the speaker identification output
    speaker_identification = event.get('SpeakerIdentification', {})
    speaker_payload = speaker_identification.get('Payload', {})
    bucket_name = speaker_payload.get('bucket_name')
    object_key = speaker_payload.get('object_key')
    
    if not bucket_name or not object_key:
        print("Missing bucket_name or object_key in input")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing bucket_name or object_key in input'})
        }
    
    # Download the object from S3
    file_obj = s3.get_object(Bucket=bucket_name, Key=object_key)
    content = file_obj['Body'].read().decode('utf-8')
    
    # Apply guardrail to redact sensitive content in the transcription
    logger.info("Applying guardrail to transcription...")
    redacted_content = apply_guardrail(bedrock_runtime, content, guardrail_id)
    
    # Log redaction statistics if content was modified
    if content != redacted_content:
        logger.info("Sensitive content was redacted from transcription")

    # Construct the prompt with redacted content
    prompt = f"{redacted_content}\n\nGive me the summary, speakers, key discussions, and action items with owners"

    # Construct the request payload
    body = json.dumps({
        "max_tokens": 4096,
        "temperature": 0.5,
        "messages": [{"role": "user", "content": prompt}],
        "anthropic_version": "bedrock-2023-05-31"
    })
    
    # Invoke the model
    modelId = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    response = bedrock.invoke_model(body=body, modelId=modelId)
    
    # Parse the response
    response_body = json.loads(response.get("body").read())
    content = response_body.get("content")
    summary = content[0]['text']
    
    # Optionally apply guardrail again to the summary to ensure all sensitive content is redacted
    logger.info("Applying guardrail to generated summary...")
    redacted_summary = apply_guardrail(bedrock_runtime, summary, guardrail_id)
    
    # Log if any additional content was redacted from the summary
    if summary != redacted_summary:
        logger.info("Additional sensitive content was redacted from summary")
    
    # Generate output filename
    # Input: Transcription-Output-for-uploads/sample-team-meeting-recording-XXXX-XXXX-XXXX-XXXX.mp4-speaker-identification.txt
    # Output: Bedrock-Sonnet-GenAI-summary-sample-team-meeting-recording-XXXX-XXXX-XXXX-XXXX.txt
    base_name = object_key.split('/')[-1]
    file_id = base_name.replace('Transcription-Output-for-uploads/', '').replace('-speaker-identification.txt', '')
    output_key = f"Bedrock-Sonnet-GenAI-summary-{file_id}.txt"
    
    # Use the same bucket for summaries
    summaries_bucket = bucket_name
    
    s3.put_object(Bucket=summaries_bucket, Key=output_key, Body=redacted_summary.encode('utf-8'))
    
    return {
        'bucket_name': summaries_bucket,
        'object_key': output_key,
        'message': 'Summary and key discussions generated successfully'
    }
