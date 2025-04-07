import json
import boto3
import datetime
import codecs
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
        # Log the incoming event structure for debugging
        logger.info(f"Event received: {json.dumps(event)}")
        
        # Lambda Invoke tasks in Step Functions wrap outputs in a 'Payload' field
        # Access TranscriptFileUri from the correct path in the event structure
        transcription_job = event.get('TranscriptionJob', {}).get('Payload', {})
        transcription_job_details = transcription_job.get('TranscriptionJob', {})
        transcript = transcription_job_details.get('Transcript', {})
        transcript_file_uri = transcript.get('TranscriptFileUri', None)
        
        # If TranscriptFileUri is still not found, try direct path as fallback
        if not transcript_file_uri and 'TranscriptionJob' in event:
            direct_job = event['TranscriptionJob']
            if 'TranscriptionJob' in direct_job:
                direct_transcript = direct_job['TranscriptionJob'].get('Transcript', {})
                transcript_file_uri = direct_transcript.get('TranscriptFileUri', None)
        
        session = boto3.Session()
        region = session.region_name
         
        if not transcript_file_uri:
            logger.error(f"TranscriptFileUri not found in event structure: {json.dumps(event)}")
            raise ValueError("TranscriptFileUri is missing from the event")
            
        # Extract the bucket name and key from the S3 URI
        # URI format: https://s3.us-west-1.amazonaws.com/bucket-name/key
        parts = transcript_file_uri.split('/')
        bucket_name = parts[3]
        object_key = '/'.join(parts[4:])
        
        # Set up S3 client
        s3_client = boto3.client('s3')

        # Retrieve the object
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        # Get the object content
        object_content = response['Body'].read().decode('utf-8')
        
        logger.info(f'Object content: {object_content}')

        data =  json.loads(object_content)  
        
        # Extract the necessary data
        labels = data['results']['speaker_labels']['segments']
        speaker_start_times = {}
        for label in labels:
            for item in label['items']:
                speaker_start_times[item['start_time']] = item['speaker_label']
        items = data['results']['items']
    
        # Process the data
        lines = []
        line = ''
        time = 0
        speaker = 'null'
        for item in items:
            content = item['alternatives'][0]['content']
            if item.get('start_time'):
                current_speaker = speaker_start_times[item['start_time']]
            elif item['type'] == 'punctuation':
                line = line + content
            if current_speaker != speaker:
                if speaker:
                    lines.append({'speaker': speaker, 'line': line, 'time': time})
                line = content
                speaker = current_speaker
                time = item['start_time']
            elif item['type'] != 'punctuation':
                line = line + ' ' + content
        lines.append({'speaker': speaker, 'line': line, 'time': time})
        sorted_lines = sorted(lines, key=lambda k: float(k['time']))
    
        # Create the output
        output = []
        for line_data in sorted_lines:
            line = '[' + str(datetime.timedelta(seconds=int(round(float(line_data['time']))))) + '] ' + line_data.get('speaker') + ': ' + line_data.get('line')
            output.append(line)
    
        # Save the output to S3
        s3 = boto3.client('s3')
        output_key = object_key.rsplit('.', 1)[0]
        
        object_key = output_key +'-speaker-identification.txt'
        output_text = '\n\n'.join(output)
        s3.put_object(Bucket=bucket_name, Key=object_key, Body=output_text.encode('utf-8'))
    
        return {
            'bucket_name': bucket_name,
            'object_key': object_key,
            'message': 'Speaker identification completed successfully'
        }
