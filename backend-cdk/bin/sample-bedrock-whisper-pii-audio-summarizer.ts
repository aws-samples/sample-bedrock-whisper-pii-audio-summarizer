#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { SampleBedrockWhisperPiiAudioSummarizerStack } from '../lib/sample-bedrock-whisper-pii-audio-summarizer-stack';

const app = new cdk.App();
new SampleBedrockWhisperPiiAudioSummarizerStack(app, 'SampleBedrockWhisperPiiAudioSummarizerStack', {
  env: { region: 'us-west-1' },
});
