import boto3
import json
import wave
import math
from io import BytesIO
import time
import os
import datetime
import subprocess
import tempfile
import shutil
import sys

def check_ffmpeg():
    """Check if FFmpeg is available in the environment."""
    try:
        # Try to run ffmpeg -version to check if it's installed
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"FFmpeg found: {result.stdout.splitlines()[0] if result.stdout else 'No version info'}")
            return True
        print(f"FFmpeg command failed with return code {result.returncode}")
        print(f"Error: {result.stderr if result.stderr else 'No error output'}")
        return False
    except Exception as e:
        print(f"Exception checking for FFmpeg: {str(e)}")
        return False

def convert_mp4_to_wav(mp4_data):
    """Convert MP4 audio data to WAV format using FFmpeg."""
    print(f"Converting MP4 to WAV. Input data size: {len(mp4_data)} bytes")
    
    # Ensure /tmp directory exists and is writable
    tmp_dir = '/tmp'
    if not os.path.exists(tmp_dir):
        try:
            os.makedirs(tmp_dir)
        except Exception as e:
            print(f"Error creating /tmp directory: {e}")
            tmp_dir = tempfile.gettempdir()
    
    print(f"Using temporary directory: {tmp_dir}")
    
    # Create unique filenames in the tmp directory
    timestamp = int(time.time())
    mp4_path = os.path.join(tmp_dir, f"input_{timestamp}.mp4")
    wav_path = os.path.join(tmp_dir, f"output_{timestamp}.wav")
    
    try:
        # Write the MP4 data to a file
        with open(mp4_path, 'wb') as mp4_file:
            mp4_file.write(mp4_data)
        
        print(f"MP4 file written to {mp4_path}, file exists: {os.path.exists(mp4_path)}, size: {os.path.getsize(mp4_path)} bytes")
        
        # Check FFmpeg is available
        ffmpeg_available = check_ffmpeg()
        print(f"FFmpeg available: {ffmpeg_available}")
        
        # Try several methods for conversion, from best to most basic
        for method in ['ffmpeg', 'ffmpeg_direct', 'custom_header']:
            try:
                if method == 'ffmpeg' and ffmpeg_available:
                    # Show all environment variables to help debug PATH issues
                    print(f"PATH: {os.environ.get('PATH', 'Not set')}")
                    print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
                    
                    # Method 1: Standard FFmpeg conversion
                    cmd = ['ffmpeg', '-i', mp4_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', wav_path]
                    print(f"Running command: {' '.join(cmd)}")
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        print("FFmpeg conversion successful")
                        # Read the converted WAV file
                        with open(wav_path, 'rb') as wav_file:
                            wav_data = wav_file.read()
                            print(f"WAV data size: {len(wav_data)} bytes")
                        return wav_data
                    else:
                        print(f"FFmpeg error: {result.stderr}")
                        # Continue to next method
                
                elif method == 'ffmpeg_direct' and ffmpeg_available:
                    # Method 2: Try direct FFmpeg with explicit path
                    # Find ffmpeg binary in PATH
                    ffmpeg_paths = os.environ.get('PATH', '').split(':') 
                    ffmpeg_path = None
                    for path in ffmpeg_paths:
                        if os.path.exists(os.path.join(path, 'ffmpeg')):
                            ffmpeg_path = os.path.join(path, 'ffmpeg')
                            break
                            
                    if ffmpeg_path:
                        # Direct command with full path to ffmpeg
                        cmd = [ffmpeg_path, '-i', mp4_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', wav_path]
                        print(f"Running direct command: {' '.join(cmd)}")
                        
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        if result.returncode == 0:
                            print("Direct FFmpeg conversion successful")
                            # Read the converted WAV file
                            with open(wav_path, 'rb') as wav_file:
                                wav_data = wav_file.read()
                                print(f"WAV data size: {len(wav_data)} bytes")
                            return wav_data
                        else:
                            print(f"Direct FFmpeg error: {result.stderr}")
                            # Continue to next method
                    else:
                        print("Could not find ffmpeg executable in PATH")
                
                elif method == 'custom_header':
                    # Method 3: Fallback - create a minimal WAV header
                    print("Using fallback WAV header creation")
                    
                    # Try to determine audio properties with ffprobe if available
                    sample_rate = 44100  # Default sample rate
                    channels = 2         # Default channels
                    bits_per_sample = 16 # Default bits per sample
                    
                    if ffmpeg_available:
                        try:
                            # Try to get audio properties with ffprobe
                            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                                    'stream=sample_rate,channels', '-of', 
                                    'default=noprint_wrappers=1', mp4_path]
                            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                            
                            if result.returncode == 0:
                                for line in result.stdout.splitlines():
                                    if '=' in line:
                                        key, value = line.split('=')
                                        if key == 'sample_rate' and value.isdigit():
                                            sample_rate = int(value)
                                        elif key == 'channels' and value.isdigit():
                                            channels = int(value)
                                print(f"Detected audio properties: sample_rate={sample_rate}, channels={channels}")
                        except Exception as e:
                            print(f"Error getting audio properties: {str(e)}")
                    
                    # Create a minimal WAV header
                    header = BytesIO()
                    # RIFF header
                    header.write(b'RIFF')
                    header.write((36 + len(mp4_data)).to_bytes(4, 'little'))  # Chunk size
                    header.write(b'WAVE')
                    # Format subchunk
                    header.write(b'fmt ')
                    header.write((16).to_bytes(4, 'little'))  # Subchunk size
                    header.write((1).to_bytes(2, 'little'))  # PCM format
                    header.write((channels).to_bytes(2, 'little'))
                    header.write((sample_rate).to_bytes(4, 'little'))
                    header.write((sample_rate * channels * bits_per_sample // 8).to_bytes(4, 'little'))  # Byte rate
                    header.write((channels * bits_per_sample // 8).to_bytes(2, 'little'))  # Block align
                    header.write((bits_per_sample).to_bytes(2, 'little'))
                    # Data subchunk
                    header.write(b'data')
                    header.write((len(mp4_data)).to_bytes(4, 'little'))
                    
                    # Treat MP4 data as raw PCM (this is not ideal but a fallback)
                    # Try to extract only audio data if possible
                    data_start = 0
                    for i in range(len(mp4_data) - 4):
                        if mp4_data[i:i+4] == b'mdat':
                            data_start = i + 8  # Skip 'mdat' and size fields
                            print(f"Found mdat box at position {i}, using data from position {data_start}")
                            break
                    
                    # Use either extracted audio data or limit to 30 seconds to avoid excessive memory usage
                    audio_data = mp4_data[data_start:] if data_start > 0 else mp4_data
                    max_size = sample_rate * channels * bits_per_sample // 8 * 30  # 30 seconds max
                    audio_data = audio_data[:max_size] if len(audio_data) > max_size else audio_data
                    
                    wav_data = header.getvalue() + audio_data
                    print(f"Created WAV with manual header. Size: {len(wav_data)} bytes")
                    return wav_data
            
            except Exception as method_error:
                print(f"Error in conversion method '{method}': {str(method_error)}")
                # Continue to next method
        
        # If we reach here, all methods failed
        raise Exception("All MP4 to WAV conversion methods failed")
        
    except Exception as e:
        print(f"Error in convert_mp4_to_wav: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup temporary files
        try:
            if os.path.exists(mp4_path):
                os.remove(mp4_path)
                print(f"Removed temporary MP4 file: {mp4_path}")
            if os.path.exists(wav_path):
                os.remove(wav_path)
                print(f"Removed temporary WAV file: {wav_path}")
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")

def is_wav_format(audio_data):
    """Check if the audio data is in WAV format (starts with RIFF header)."""
    return audio_data.startswith(b'RIFF')


def detect_audio_format(audio_data):
    """Detect the audio/video format based on file signatures."""
    # Check for common file signatures
    signatures = {
        b'RIFF': 'wav',  # WAV files
        b'\xff\xfb': 'mp3',  # MP3 files
        b'\x00\x00\x00': 'mp4',  # MP4/MOV files (many start with 'ftyp' after length)
        b'ftyp': 'mp4',  # MP4 files
        b'ID3': 'mp3',  # MP3 files with ID3 tag
        b'OggS': 'ogg'   # OGG files
    }
    
    # Check for each signature
    for sig, fmt in signatures.items():
        # Check at the beginning of the file
        if audio_data.startswith(sig):
            return fmt
        # For MP4, 'ftyp' might be after a length field
        if fmt == 'mp4' and sig == b'ftyp' and b'ftyp' in audio_data[:50]:
            return fmt
    
    return 'unknown'

def chunk_audio(audio_data, chunk_duration_seconds=30):
    """Split wave audio from BytesIO into chunks."""
    try:
        print(f"Starting audio chunking. Input data size: {len(audio_data)} bytes")
        
        # Check audio format
        audio_format = detect_audio_format(audio_data)
        print(f"Detected audio format: {audio_format}")
        
        # Check if it's a WAV file (starts with RIFF header)
        if not is_wav_format(audio_data):
            print(f"Input is not WAV format (detected as {audio_format}), attempting conversion...")
            try:
                audio_data = convert_mp4_to_wav(audio_data)
                print(f"Conversion completed. WAV data size: {len(audio_data)} bytes")
                
                # Verify the converted data is valid WAV
                if not is_wav_format(audio_data):
                    print("Warning: Converted data does not have RIFF header")
                    # Try to add RIFF header if missing
                    if not audio_data.startswith(b'RIFF'):
                        print("Adding RIFF header to converted data")
                        sample_rate = 44100
                        channels = 2
                        bits_per_sample = 16
                        
                        header = BytesIO()
                        header.write(b'RIFF')
                        header.write((36 + len(audio_data)).to_bytes(4, 'little'))
                        header.write(b'WAVE')
                        header.write(b'fmt ')
                        header.write((16).to_bytes(4, 'little'))
                        header.write((1).to_bytes(2, 'little'))
                        header.write((channels).to_bytes(2, 'little'))
                        header.write((sample_rate).to_bytes(4, 'little'))
                        header.write((sample_rate * channels * bits_per_sample // 8).to_bytes(4, 'little'))
                        header.write((channels * bits_per_sample // 8).to_bytes(2, 'little'))
                        header.write((bits_per_sample).to_bytes(2, 'little'))
                        header.write(b'data')
                        header.write((len(audio_data)).to_bytes(4, 'little'))
                        
                        audio_data = header.getvalue() + audio_data
                        print(f"Added RIFF header. New size: {len(audio_data)} bytes")
            except Exception as e:
                print(f"Error converting audio: {str(e)}")
                # This is a critical error - we can't proceed without conversion
                raise
        
        # Create a BytesIO object from the audio data
        wav_buffer = BytesIO(audio_data)
        print("WAV buffer created successfully")
        
        try:
            with wave.open(wav_buffer, 'rb') as wav_file:
                # Get file properties
                n_channels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                # Log wav file properties for debugging
                print(f"WAV properties: channels={n_channels}, sampwidth={sampwidth}, ")
                print(f"framerate={framerate}, frames={n_frames}")
                
                # Calculate frames per chunk
                frames_per_chunk = chunk_duration_seconds * framerate
                
                # For large audio files (especially MP4 conversions), create smaller chunks
                # to avoid SageMaker payload limits (typically around 5-6MB)
                max_payload_size = 2 * 1024 * 1024  # 2MB as a safe limit
                bytes_per_frame = n_channels * sampwidth
                estimated_chunk_size = frames_per_chunk * bytes_per_frame + 44  # WAV header size
                
                if estimated_chunk_size > max_payload_size:
                    size_ratio = max_payload_size / estimated_chunk_size
                    # Use 80% of the size limit as a safety margin
                    adjusted_chunk_duration = int(chunk_duration_seconds * size_ratio * 0.8)
                    frames_per_chunk = adjusted_chunk_duration * framerate
                    print(f"Adjusted chunk duration to {adjusted_chunk_duration} seconds to keep chunks under {max_payload_size/1024/1024:.1f}MB")
                
                n_chunks = math.ceil(n_frames / frames_per_chunk)
                print(f"Audio will be split into {n_chunks} chunks")
                
                chunks = []
                for i in range(n_chunks):
                    try:
                        # Read chunk of frames
                        start_frame = i * frames_per_chunk
                        wav_file.setpos(int(start_frame))
                        chunk_frames = wav_file.readframes(int(frames_per_chunk))
                        
                        # Create a new wave file in memory for this chunk
                        chunk_buffer = BytesIO()
                        with wave.open(chunk_buffer, 'wb') as chunk_wav:
                            chunk_wav.setnchannels(n_channels)
                            chunk_wav.setsampwidth(sampwidth)
                            chunk_wav.setframerate(framerate)
                            chunk_wav.writeframes(chunk_frames)
                        
                        chunk_data = chunk_buffer.getvalue()
                        print(f"Chunk {i+1}/{n_chunks} created, size: {len(chunk_data)} bytes")
                        chunks.append(chunk_data)
                    except Exception as chunk_error:
                        print(f"Error processing chunk {i+1}: {chunk_error}")
                        # Continue with the next chunk if one fails
                
                # Filter out any chunks that are too small (just headers)
                valid_chunks = []
                for i, chunk in enumerate(chunks):
                    # WAV headers are typically around 44 bytes
                    # If a chunk is only a header with no audio data, skip it
                    if len(chunk) <= 44:
                        print(f"Skipping chunk {i+1} as it contains only header (size: {len(chunk)} bytes)")
                    else:
                        valid_chunks.append(chunk)
                
                print(f"Successfully created {len(valid_chunks)} valid chunks out of {len(chunks)} total chunks")
                return valid_chunks
        except Exception as wave_error:
            print(f"Error opening WAV file: {wave_error}")
            raise
    except Exception as e:
        print(f"Error in chunk_audio: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return empty list as fallback
        return []

def transcribe_chunk(sagemaker_client, chunk_data, endpoint_name):
    """Transcribe a single audio chunk using SageMaker runtime with Whisper endpoint."""
    try:
        import io
        import base64
        import wave

        print(f"Using SageMaker endpoint: {endpoint_name}")
        print(f"Sending request to SageMaker runtime with audio size: {len(chunk_data)} bytes")
        
        # Convert audio to hex string (not base64)
        hex_audio = chunk_data.hex()
        
        # Create payload in the format expected by Whisper endpoints
        payload = {
            "audio_input": hex_audio,
            "language": "english",
            "task": "transcribe",
            "top_p": 0.9
        }
        
        # Invoke the SageMaker endpoint with JSON payload
        response = sagemaker_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        # Parse the response
        print("Response received from SageMaker endpoint")
        response_body = json.loads(response['Body'].read().decode('utf-8'))
        print(f"Response type: {type(response_body)}")
        
        # For debugging - print the response structure
        if isinstance(response_body, dict):
            print(f"Response keys: {list(response_body.keys())}")
            if 'text' in response_body:
                print(f"First part of text: {response_body['text'][:100]}...")
        
        # Return the response object - we'll handle formatting in the calling function
        return response_body
    except Exception as e:
        print(f"Error invoking SageMaker endpoint: {str(e)}")
        # Print detailed exception for debugging
        import traceback
        print(traceback.format_exc())
        raise

def create_speaker_timestamps(text, start_time, end_time):
    """
    Create simulated speaker timestamps for a text segment.
    Since Whisper doesn't provide speaker diarization, we'll assign a default speaker
    and distribute words evenly across the time range.
    """
    words = text.split()
    if not words:
        return []
    
    duration = end_time - start_time
    word_duration = duration / len(words)
    
    items = []
    for i, word in enumerate(words):
        word_start = start_time + (i * word_duration)
        word_end = word_start + word_duration
        
        items.append({
            "start_time": str(round(word_start, 3)),
            "end_time": str(round(word_end, 3)),
            "alternatives": [{"content": word}],
            "type": "pronunciation"
        })
        
        # Add punctuation as a separate item if the word ends with punctuation
        if word[-1] in ",.?!;:":
            items.append({
                "alternatives": [{"content": word[-1]}],
                "type": "punctuation"
            })
    
    return items

def lambda_handler(event, context):
    try:
        print("Event received:", json.dumps(event))
        
        # Extract bucket and key from the event
        bucket = event['detail']['bucket']['name']
        input_key = event['detail']['object']['key']
        
        # Generate job name (similar to AWS Transcribe format)
        file_name = input_key.split('/')[-1]
        job_name = f"Transcription-Job-{file_name}"
        
        # Generate output key for full transcription
        output_key = f"Transcription-Output-for-{input_key}.txt"
        
        print(f"Processing s3://{bucket}/{input_key}")
        
        # Initialize clients
        s3 = boto3.client('s3')
        
        # Initialize clients
        s3 = boto3.client('s3')
        # Use SageMaker runtime for SageMaker endpoints
        sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
        # Use SageMaker Whisper endpoint name from environment variable (required)
        endpoint_name = os.environ['WHISPER_ENDPOINT']
        if not endpoint_name:
            raise ValueError("WHISPER_ENDPOINT environment variable must be set")
        
        print(f"Using SageMaker endpoint: {endpoint_name}")
        
        # Set up ffmpeg path (if using Lambda layers)
        ffmpeg_paths = [
            '/opt/bin',            # Common Lambda layer path
            '/opt/ffmpeg/bin',     # Another possible location
            '/var/task/bin',       # If you added ffmpeg in the deployment package
            '/tmp/bin',            # If you downloaded ffmpeg at runtime
            '/opt/ffmpeg',         # FFmpeg directory itself
            '/opt'                 # Root opt directory
        ]
        
        # Add all possible FFmpeg paths to PATH
        for path in ffmpeg_paths:
            if path not in os.environ.get('PATH', ''):
                os.environ['PATH'] = f"{path}:{os.environ.get('PATH', '')}"
        
        print(f"Updated PATH: {os.environ.get('PATH', 'Not set')}")
        
        # Check if FFmpeg is available after PATH updates
        ffmpeg_available = check_ffmpeg()
        print(f"FFmpeg available after PATH setup: {ffmpeg_available}")
        
        # List files in potential FFmpeg directories for debugging
        for path in ffmpeg_paths:
            if os.path.exists(path):
                try:
                    files = os.listdir(path)
                    print(f"Files in {path}: {files if files else 'Empty directory'}")
                except Exception as e:
                    print(f"Error listing files in {path}: {str(e)}")
        
        # Download audio file from S3
        response = s3.get_object(Bucket=bucket, Key=input_key)
        audio_data = response['Body'].read()
        
        # Check audio format and reject non-WAV files
        print("Splitting audio into chunks...")
        print(f"Starting audio chunking. Input data size: {len(audio_data)} bytes")
        
        # Detect the file format
        audio_format = detect_audio_format(audio_data)
        print(f"Detected audio format: {audio_format}")
        
        # Only accept WAV files
        if audio_format != 'wav':
            error_message = f"Error: {audio_format.upper()} files are not supported. Please convert to WAV format before uploading."
            print(error_message)
            raise ValueError(error_message)
        
        # Split audio into chunks
        chunks = chunk_audio(audio_data)
        
        # Process each chunk
        all_transcriptions = []
        chunk_timings = []
        cumulative_duration = 0
        
        for i, chunk_data in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)}")
            try:
                # Get duration of this chunk (30 seconds per chunk, or less for the last chunk)
                chunk_start = cumulative_duration
                chunk_duration = 30  # Default chunk duration in seconds
                chunk_end = chunk_start + chunk_duration
                cumulative_duration = chunk_end
                
                # Use SageMaker runtime client with the endpoint name
                # SageMaker endpoints use a different API than Bedrock
                result = transcribe_chunk(sagemaker_runtime, chunk_data, endpoint_name)
                
                # For debugging
                print(f"Transcription result type: {type(result)}")
                if isinstance(result, dict):
                    print(f"Result keys: {result.keys()}")
                
                all_transcriptions.append(result)
                chunk_timings.append((chunk_start, chunk_end))
            except Exception as e:
                print(f"Error processing chunk {i}: {str(e)}")
                raise
        
        # Combine transcriptions into a format similar to AWS Transcribe output
        full_transcription = []
        all_items = []
        speaker_segments = []
        
        for i, (result, (start_time, end_time)) in enumerate(zip(all_transcriptions, chunk_timings)):
            # Handle different response formats from the Whisper model
            if isinstance(result, dict) and 'text' in result:
                # Standard format with text field
                text = result['text'] if isinstance(result['text'], str) else ' '.join(result['text'])
            elif isinstance(result, str):
                # Directly returned text string
                text = result
            else:
                # Fallback for unexpected formats
                print(f"Unexpected result format for chunk {i}: {type(result)}")
                try:
                    # Try to convert to string representation
                    text = str(result)
                except:
                    text = f"[Unable to transcribe chunk {i}]"
            
            print(f"Processed text for chunk {i}: {text[:50]}...")
            full_transcription.append(text)
            
            # Create simulated timestamps for words
            chunk_items = create_speaker_timestamps(text, start_time, end_time)
            all_items.extend(chunk_items)
            
            # Create a speaker segment
            speaker_segment = {
                "start_time": str(start_time),
                "end_time": str(end_time),
                "speaker_label": "spk_0",  # Default speaker label
                "items": [
                    {
                        "start_time": item.get("start_time", "0"),
                        "end_time": item.get("end_time", "0"),
                        "speaker_label": "spk_0"
                    }
                    for item in chunk_items if item.get("type") == "pronunciation"
                ]
            }
            speaker_segments.append(speaker_segment)
        
        # Join all elements with spaces
        final_text = ' '.join(full_transcription)
        
        # Create AWS Transcribe-like output structure
        transcribe_output = {
            "jobName": job_name,
            "accountId": "123456789012",  # Placeholder
            "results": {
                "transcripts": [
                    {"transcript": final_text}
                ],
                "items": all_items,
                "speaker_labels": {
                    "speakers": 1,
                    "segments": speaker_segments
                }
            },
            "status": "COMPLETED"
        }
        
        # Get the summaries bucket name from environment variables
        summaries_bucket = os.environ.get('SUMMARIES_BUCKET', bucket)
        
        # Upload result to S3
        s3.put_object(
            Bucket=summaries_bucket,
            Key=output_key,
            Body=json.dumps(transcribe_output, indent=2),
            ContentType='application/json'
        )
        
        print(f"Transcription saved to s3://{summaries_bucket}/{output_key}")
        
        # Return a response compatible with the state machine
        # The Lambda Invoke task will automatically place our response in $.TranscriptionJob.Payload
        return {
            "TranscriptionJob": {
                "TranscriptionJobStatus": "COMPLETED",
                "TranscriptionJobName": job_name,
                "Transcript": {
                    "TranscriptFileUri": f"https://s3.amazonaws.com/{summaries_bucket}/{output_key}"
                }
            }
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "TranscriptionJob": {
                "TranscriptionJobStatus": "FAILED",
                "TranscriptionJobName": f"Transcription-Job-{event['detail']['object']['key'].split('/')[-1] if 'detail' in event and 'object' in event['detail'] else 'unknown'}",
                "FailureReason": str(e)
            }
        }
