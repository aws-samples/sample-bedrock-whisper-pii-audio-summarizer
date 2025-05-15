#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AudioSummarizerStack } from '../lib/audio-summarizer-stack';

const app = new cdk.App();
new AudioSummarizerStack(app, 'SampleBedrockWhisperPiiAudioSummarizerStack', {
  env: { region: 'us-west-1' },
});
