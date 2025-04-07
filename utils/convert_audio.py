import os
import sys
import subprocess
import argparse
import tempfile
import uuid
import boto3
from botocore.exceptions import ClientError


def check_ffmpeg():
    """Check if FFmpeg is available in the environment."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True
        return False
    except Exception:
        return False


def convert_mp4_to_wav(input_file, output_file=None):
    """
    Convert MP4 to WAV format using FFmpeg.
    
    Args:
        input_file (str): Path to input MP4 file
        output_file (str, optional): Path to output WAV file. If not provided, 
                                    one will be generated based on input filename.
    
    Returns:
        str: Path to the converted WAV file
    """
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not available in PATH.")
        print("Please install FFmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # If output file is not specified, create one based on input file
    if not output_file:
        basename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{basename}.wav"
    
    try:
        cmd = ['ffmpeg', '-i', input_file, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', output_file]
        print(f"Running conversion command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print(f"Successfully converted {input_file} to {output_file}")
            return output_file
        else:
            print(f"Error converting file: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return None


def upload_to_s3(file_path, bucket_name, object_key=None):
    """
    Upload file to S3 bucket.
    
    Args:
        file_path (str): Path to file to upload
        bucket_name (str): Name of S3 bucket
        object_key (str, optional): S3 object key. If not provided, one will be generated.
        
    Returns:
        str: S3 object key if successful, None otherwise
    """
    s3 = boto3.client('s3')
    
    # If object key is not specified, create one based on file path
    if not object_key:
        file_name = os.path.basename(file_path)
        base, ext = os.path.splitext(file_name)
        unique_name = f'{base}-{str(uuid.uuid4())}{ext}'
        object_key = f'uploads/{unique_name}'
    
    try:
        s3.upload_file(file_path, bucket_name, object_key)
        print(f"Successfully uploaded {file_path} to s3://{bucket_name}/{object_key}")
        return object_key
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        return None


def process_media_file(input_file, bucket_name=None, object_key=None, keep_wav=False):
    """
    Process media file: convert to WAV if it's an MP4, then upload to S3.
    
    Args:
        input_file (str): Path to input media file
        bucket_name (str, optional): Name of S3 bucket. If not provided, file won't be uploaded.
        object_key (str, optional): S3 object key. If not provided, one will be generated.
        keep_wav (bool): Whether to keep the converted WAV file or delete it after upload
        
    Returns:
        dict: Result with status and relevant information
    """
    result = {
        "status": "error",
        "input_file": input_file,
        "message": ""
    }
    
    # Check if file exists
    if not os.path.exists(input_file):
        result["message"] = f"Input file {input_file} does not exist"
        return result
    
    # Get file extension
    _, ext = os.path.splitext(input_file)
    ext = ext.lower()
    
    # Process based on file extension
    if ext == '.mp4':
        print(f"Detected MP4 file: {input_file}")
        # Convert to WAV
        wav_file = convert_mp4_to_wav(input_file)
        if not wav_file:
            result["message"] = "Failed to convert MP4 to WAV"
            return result
        
        result["converted_file"] = wav_file
        
        # Upload to S3 if bucket name is provided
        if bucket_name:
            s3_key = upload_to_s3(wav_file, bucket_name, object_key)
            if not s3_key:
                result["message"] = "Failed to upload WAV file to S3"
                return result
            
            result["status"] = "success"
            result["bucket"] = bucket_name
            result["object_key"] = s3_key
            result["message"] = f"Successfully converted MP4 to WAV and uploaded to S3"
            
            # Clean up temporary WAV file if keep_wav is False
            if not keep_wav and os.path.exists(wav_file):
                os.remove(wav_file)
                print(f"Deleted temporary WAV file: {wav_file}")
        else:
            result["status"] = "success"
            result["message"] = f"Successfully converted MP4 to WAV"
        
    elif ext == '.wav':
        print(f"Detected WAV file: {input_file}")
        # No conversion needed, upload directly if bucket name is provided
        if bucket_name:
            s3_key = upload_to_s3(input_file, bucket_name, object_key)
            if not s3_key:
                result["message"] = "Failed to upload WAV file to S3"
                return result
            
            result["status"] = "success"
            result["bucket"] = bucket_name
            result["object_key"] = s3_key
            result["message"] = f"Successfully uploaded WAV file to S3"
        else:
            result["status"] = "success"
            result["message"] = f"No conversion needed for WAV file"
    
    else:
        result["message"] = f"Unsupported file format: {ext}. Supported formats: .mp4, .wav"
    
    return result


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Convert audio/video files and upload to S3.")
    parser.add_argument("input_file", help="Path to input media file (MP4 or WAV)")
    parser.add_argument("--bucket", help="S3 bucket name for upload")
    parser.add_argument("--key", help="S3 object key (optional)")
    parser.add_argument("--keep-wav", action="store_true", help="Keep converted WAV file after upload")
    
    args = parser.parse_args()
    
    result = process_media_file(
        args.input_file,
        bucket_name=args.bucket,
        object_key=args.key,
        keep_wav=args.keep_wav
    )
    
    if result["status"] == "success":
        print(f"Success: {result['message']}")
        if "bucket" in result and "object_key" in result:
            print(f"File available at: s3://{result['bucket']}/{result['object_key']}")
        sys.exit(0)
    else:
        print(f"Error: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
