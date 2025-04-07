import boto3
import json
import time
import os
from botocore.exceptions import ClientError

class StepFunctionTester:
    def __init__(self, region='us-west-1', state_machine_name='VoiceProcessingStateMachine', 
                 upload_bucket=None, summaries_bucket=None):
        self.s3 = boto3.client('s3')
        self.region = region
        self.sfn = boto3.client('stepfunctions', region_name=region)
        
        # Try to get the state machine ARN if only name is provided
        if state_machine_name and ':' not in state_machine_name:  # If not already an ARN
            try:
                response = self.sfn.list_state_machines()
                for machine in response['stateMachines']:
                    if machine['name'] == state_machine_name:
                        self.state_machine_arn = machine['stateMachineArn']
                        break
                else:
                    raise ValueError(f"Could not find state machine named {state_machine_name}")
            except Exception as e:
                print(f"Error retrieving state machine ARN: {e}")
                self.state_machine_arn = None
        else:
            # If an ARN was directly provided
            self.state_machine_arn = state_machine_name
            
        # Set bucket names - these should be provided by the user
        self.upload_bucket = upload_bucket
        self.summaries_bucket = summaries_bucket
        
        # Validate required configuration
        if not self.state_machine_arn:
            print("WARNING: No state machine ARN provided or found")
        if not self.upload_bucket:
            print("WARNING: No upload bucket specified. File uploads will fail.")
        
    def upload_test_file(self, file_path):
        """Upload a test file to S3"""
        import uuid
        file_name = os.path.basename(file_path)
        base, ext = os.path.splitext(file_name)
        unique_name = f'{base}-{str(uuid.uuid4())}{ext}'
        object_key = f'uploads/{unique_name}'
        
        try:
            self.s3.upload_file(file_path, self.upload_bucket, object_key)
            print(f"Successfully uploaded {file_name} to {self.upload_bucket}/{object_key}")
            return object_key
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return None

    def wait_for_execution(self, execution_arn, timeout=300):
        """Wait for step function execution to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.sfn.describe_execution(executionArn=execution_arn)
            status = response['status']
            
            if status in ['SUCCEEDED', 'FAILED']:
                return status, response.get('output')
            
            print(f"Execution status: {status}")
            time.sleep(10)
        
        return 'TIMEOUT', None

    def get_execution_history(self, execution_arn):
        """Get the full execution history"""
        try:
            response = self.sfn.get_execution_history(
                executionArn=execution_arn,
                maxResults=100
            )
            return response['events']
        except ClientError as e:
            print(f"Error getting execution history: {e}")
            return []

    def analyze_failure(self, events):
        """Analyze execution history to find failure points"""
        for event in events:
            if event['type'] == 'ExecutionFailed':
                error = event.get('executionFailedEventDetails', {})
                print(f"\nExecution failed:")
                print(f"Error: {error.get('error')}")
                print(f"Cause: {error.get('cause')}")
                return error
            
            elif event['type'] == 'TaskFailed':
                error = event.get('taskFailedEventDetails', {})
                print(f"\nTask failed:")
                print(f"Resource: {error.get('resource')}")
                print(f"Error: {error.get('error')}")
                print(f"Cause: {error.get('cause')}")
                return error
        
        return None

    def run_test(self, file_path):
        """Run a complete test with a given file"""
        print(f"\n=== Starting test with {file_path} ===")
        print(f"Using Whisper for transcription")
        
        # Upload file
        object_key = self.upload_test_file(file_path)
        if not object_key:
            return False
        
        # Prepare input for step function
        input_data = {
            "detail": {
                "bucket": {"name": self.upload_bucket},
                "object": {"key": object_key}
            }
        }
        
        # Start execution
        try:
            response = self.sfn.start_execution(
                stateMachineArn=self.state_machine_arn,
                input=json.dumps(input_data)
            )
            execution_arn = response['executionArn']
            print(f"Started execution: {execution_arn}")
        except ClientError as e:
            print(f"Error starting execution: {e}")
            return False
        
        # Wait for completion
        status, output = self.wait_for_execution(execution_arn)
        print(f"\nExecution completed with status: {status}")
        
        if status == 'FAILED':
            events = self.get_execution_history(execution_arn)
            self.analyze_failure(events)
            return False
        elif status == 'SUCCEEDED':
            print("Test passed successfully!")
            if output:
                print(f"Output: {output}")
            return True
        else:
            print(f"Unexpected status: {status}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test AWS Step Functions for audio processing')
    parser.add_argument('--file', '-f', required=True, help='Path to the audio file to process (WAV format recommended)')
    parser.add_argument('--region', default='us-west-1', help='AWS region for the Step Function')
    parser.add_argument('--state-machine', default='VoiceProcessingStateMachine', 
                        help='Name or ARN of the Step Function state machine')
    parser.add_argument('--upload-bucket', required=True, help='S3 bucket for uploading audio files')
    parser.add_argument('--summaries-bucket', help='S3 bucket for resulting summaries')
    args = parser.parse_args()
    
    test_file = args.file
    
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found!")
        print("Please provide your own audio file using the --file parameter")
        return
    
    tester = StepFunctionTester(
        region=args.region,
        state_machine_name=args.state_machine,
        upload_bucket=args.upload_bucket,
        summaries_bucket=args.summaries_bucket
    )
    
    success = tester.run_test(test_file)
    print(f"\nTest {'passed' if success else 'failed'}")

if __name__ == "__main__":
    main()
