#!/bin/bash
# Script to remove CDK nag references from the stack file

# 1. Remove the import statement
sed -i '' '/import.*cdk-nag/d' backend-cdk/lib/audio-summarizer-stack.ts

# 2. Replace the comment about CDK nag with a simpler one
sed -i '' 's/origin access identity for CloudFront (needed for specific cdk-nag rules)/origin access identity for CloudFront/g' backend-cdk/lib/audio-summarizer-stack.ts

# 3. Find the NagSuppressions block and remove it (including any lines until we find a closing brace)
# First, find the line number where NagSuppressions.addResourceSuppressions begins
START_LINE=$(grep -n "NagSuppressions.addResourceSuppressions" backend-cdk/lib/audio-summarizer-stack.ts | cut -d':' -f1)

if [ ! -z "$START_LINE" ]; then
  # Find the next closing brace (]);
  END_LINE=$(tail -n +$START_LINE backend-cdk/lib/audio-summarizer-stack.ts | grep -n "\]);" | head -1 | cut -d':' -f1)
  END_LINE=$((START_LINE + END_LINE - 1))
  
  # Delete all lines from START_LINE to END_LINE
  sed -i '' "${START_LINE},${END_LINE}d" backend-cdk/lib/audio-summarizer-stack.ts
fi

echo "Removed CDK nag references from the stack file."
