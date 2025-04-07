import os
import subprocess
import zipfile
import shutil

# Directory setup
layer_dir = 'lambda_layer'
python_dir = os.path.join(layer_dir, 'python')
os.makedirs(python_dir, exist_ok=True)

# Read requirements from file
requirements_file = 'lambda-layer-modules/requirements.txt'
with open(requirements_file, 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Add additional dependencies for Bedrock
requirements.append('boto3>=1.28.0')

# Print packages to be installed
print(f"Installing the following packages: {', '.join(requirements)}")

# Install packages to the python directory
for package in requirements:
    print(f"Installing {package}...")
    subprocess.check_call(['pip3', 'install', package, '--target', python_dir])

# Clean up unnecessary files to reduce size
print("Cleaning up unnecessary files...")
for root, dirs, files in os.walk(python_dir):
    for d in dirs:
        if d == '__pycache__' or d.endswith('.dist-info') or d.endswith('.egg-info'):
            shutil.rmtree(os.path.join(root, d))
    for f in files:
        if f.endswith('.pyc') or f.endswith('.pyo'):
            os.remove(os.path.join(root, f))

# Create zip file
zip_path = 'lambda_layer.zip'
print(f"Creating zip file: {zip_path}...")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files in os.walk(layer_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, layer_dir)
            zipf.write(file_path, arcname)

# Print zip file size
zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
print(f"Layer zip file created at: {os.path.abspath(zip_path)}")
print(f"Zip file size: {zip_size_mb:.2f} MB")

# Provide instructions for deployment
print("\nTo deploy this layer, run:")
print("cd capstonelambdabackend2-cdk")
print("aws lambda publish-layer-version --layer-name whisper-dependencies --zip-file fileb://lambda_layer.zip --compatible-runtimes python3.9")
print("Then update your CDK stack to use this layer ARN")
