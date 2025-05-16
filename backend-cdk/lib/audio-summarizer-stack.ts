import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';

export class AudioSummarizerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create S3 buckets with secure configuration
    const uploadsBucket = new s3.Bucket(this, 'UploadsBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: true,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(7), // Short retention for uploads
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(1)
        }
      ],
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
          exposedHeaders: ['ETag'],
          maxAge: 3000
        }
      ]
    });

    const summariesBucket = new s3.Bucket(this, 'SummariesBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: true,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
          maxAge: 3000
        }
      ]
    });

    const uiBucket = new s3.Bucket(this, 'UIBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
    });

    // Create Whisper Transcription Lambda
    const whisperTranscriptionFunction = new lambda.Function(this, 'WhisperTranscriptionFunction', {
      runtime: lambda.Runtime.PYTHON_3_12, // Updated to latest Python runtime
      handler: 'whisper-transcription.lambda_handler',
      code: lambda.Code.fromAsset('lambda'),
      memorySize: 2048,
      timeout: cdk.Duration.seconds(600),  // 10-minute timeout for larger files
      environment: {
        UPLOADS_BUCKET: uploadsBucket.bucketName,
        SUMMARIES_BUCKET: summariesBucket.bucketName,
        REGION: cdk.Stack.of(this).region,
        WHISPER_ENDPOINT: 'endpoint-quick-start-irrc7' // Must be configured before deployment
      },
      logRetention: logs.RetentionDays.ONE_WEEK
    });

    // Add Bedrock permissions to the Whisper transcription Lambda with specific model ARNs
    whisperTranscriptionFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW, 
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream'
      ],
      resources: [
        // Specify the exact model ARNs that will be used
        `arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:model/anthropic.claude-3-sonnet-20240229-v1:0`,
        `arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:model/anthropic.claude-3-haiku-20240307-v1:0`
      ] // Restricted to specific models
    }));

    // Create Speaker Identification Lambda
    const speakerIdentificationFunction = new lambda.Function(this, 'SpeakerIdentificationFunction', {
      runtime: lambda.Runtime.PYTHON_3_12, // Updated to latest Python runtime
      handler: 'speaker-identification.lambda_handler',
      code: lambda.Code.fromAsset('lambda'),
      memorySize: 2048,
      timeout: cdk.Duration.seconds(300),
      environment: {
        SUMMARIES_BUCKET: summariesBucket.bucketName
      },
      logRetention: logs.RetentionDays.ONE_WEEK
    });

    // Create PII Redaction Lambda
    const piiRedactionFunction = new lambda.Function(this, 'PIIRedactionFunction', {
      runtime: lambda.Runtime.PYTHON_3_12, // Updated to latest Python runtime
      handler: 'pii-redaction.lambda_handler',
      code: lambda.Code.fromAsset('lambda'),
      memorySize: 2048,
      timeout: cdk.Duration.seconds(300),
      environment: {
        SUMMARIES_BUCKET: summariesBucket.bucketName
      },
      logRetention: logs.RetentionDays.ONE_WEEK
    });

    // Add Comprehend permissions for PII redaction with specific region restriction
    piiRedactionFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'comprehend:DetectPiiEntities'
      ],
      // While Comprehend doesn't support resource-level permissions for DetectPiiEntities,
      // we add a condition to restrict the region
      resources: ['*'],
      conditions: {
        'StringEquals': {
          'aws:RequestedRegion': cdk.Stack.of(this).region
        }
      }
    }));

    // Create Bedrock Summary Lambda
    const bedrockSummaryFunction = new lambda.Function(this, 'BedrockSummaryFunction', {
      runtime: lambda.Runtime.PYTHON_3_12, // Updated to latest Python runtime
      handler: 'bedrock-summary.lambda_handler',
      code: lambda.Code.fromAsset('lambda'),
      memorySize: 2048,
      timeout: cdk.Duration.seconds(300),
      environment: {
        SUMMARIES_BUCKET: summariesBucket.bucketName,
        REGION: cdk.Stack.of(this).region,
        GUARDRAIL_ID: 'arn:aws:bedrock:us-east-1:064080936720:guardrail-profile/us.guardrail.v1:0' // Must be configured before deployment
      },
      logRetention: logs.RetentionDays.ONE_WEEK
    });

    // Add Bedrock permissions to the summary Lambda with specific model ARNs
    bedrockSummaryFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream'
      ],
      resources: [
        // Specify the exact model ARNs that will be used
        `arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:model/anthropic.claude-3-sonnet-20240229-v1:0`,
        `arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:model/anthropic.claude-3-haiku-20240307-v1:0`
      ] // Restricted to specific models
    }));
    
    // Add Bedrock Guardrail permissions
    bedrockSummaryFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:ApplyGuardrail'
      ],
      resources: [
        // Use a template literal with a variable to allow customization
        '*' // Using wildcard for flexibility, but could be restricted to specific guardrail ARN
      ]
    }));

    // Grant Lambda access to S3 with specific permissions instead of wildcard
    uploadsBucket.grantRead(whisperTranscriptionFunction); // More specific permission
    summariesBucket.grantReadWrite(whisperTranscriptionFunction);
    summariesBucket.grantReadWrite(speakerIdentificationFunction);
    summariesBucket.grantReadWrite(piiRedactionFunction);
    summariesBucket.grantReadWrite(bedrockSummaryFunction);

    // Create Step Function for orchestration
    // Define the state machine
    const transcribeTask = new tasks.LambdaInvoke(this, 'TranscribeAudio', {
      lambdaFunction: whisperTranscriptionFunction,
      outputPath: '$.Payload',
    });

    const identifySpeakersTask = new tasks.LambdaInvoke(this, 'IdentifySpeakers', {
      lambdaFunction: speakerIdentificationFunction,
      outputPath: '$.Payload',
    });

    const redactPIITask = new tasks.LambdaInvoke(this, 'RedactPII', {
      lambdaFunction: piiRedactionFunction,
      outputPath: '$.Payload',
    });

    const generateSummaryTask = new tasks.LambdaInvoke(this, 'GenerateSummary', {
      lambdaFunction: bedrockSummaryFunction,
      outputPath: '$.Payload',
    });

    // Define a workflow that combines all these steps
    const definition = transcribeTask
      .next(identifySpeakersTask)
      .next(redactPIITask)
      .next(generateSummaryTask);

    // Create the state machine with the defined workflow
    const stateMachine = new sfn.StateMachine(this, 'AudioSummarizerWorkflow', {
      definition,
      timeout: cdk.Duration.minutes(30),
      tracingEnabled: true, // Enable X-Ray tracing
      logs: {
        destination: new logs.LogGroup(this, 'StateMachineLogs', {
          retention: logs.RetentionDays.ONE_WEEK
        }),
        level: sfn.LogLevel.ERROR
      }
    });

    // Grant Step Function permissions to invoke Lambda functions and access S3
    // No transcribe permissions needed as we're using Whisper directly

    // Grant more specific S3 permissions to the state machine
    // For bucket level operations (ListBucket)
    stateMachine.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['s3:ListBucket'],
      resources: [
        uploadsBucket.bucketArn,
        summariesBucket.bucketArn
      ]
    }));
    
    // For object level operations
    stateMachine.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        's3:GetObject',
        's3:PutObject'
      ],
      resources: [
        `${uploadsBucket.bucketArn}/*`,
        `${summariesBucket.bucketArn}/*`
      ]
    }));

    whisperTranscriptionFunction.grantInvoke(stateMachine);
    speakerIdentificationFunction.grantInvoke(stateMachine);
    bedrockSummaryFunction.grantInvoke(stateMachine);

    // Create API access logs group with appropriate retention
    const apiAccessLogs = new logs.LogGroup(this, 'ApiAccessLogs', {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // Create API Gateway with CORS support and enhanced security
    const api = new apigateway.RestApi(this, 'AudioSummarizerApi', {
      restApiName: 'Audio Summarizer API',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key', 'X-Amz-Security-Token', 'X-Requested-With'],
        allowCredentials: true,
      },
      defaultMethodOptions: {
        authorizationType: apigateway.AuthorizationType.NONE, // For demo purposes - production would use proper auth
      },
      // Disable CloudWatch logging to avoid CloudWatch Logs role ARN issue
      deployOptions: {
        stageName: 'prod',
        // Removed accessLogDestination and accessLogFormat to disable access logs
        loggingLevel: apigateway.MethodLoggingLevel.OFF, // Disable CloudWatch logging
        metricsEnabled: true,
        tracingEnabled: false, // Disable X-Ray tracing
        methodOptions: {
          '/*/*': {
            throttlingRateLimit: 20,
            throttlingBurstLimit: 10
          }
        }
      }
    });

    // Add request validator
    const requestValidator = new apigateway.RequestValidator(this, 'DefaultValidator', {
      restApi: api,
      validateRequestBody: true,
      validateRequestParameters: true
    });

    // Create API Lambda function with enhanced configuration
    const apiFunction = new lambda.Function(this, 'ApiFunction', {
      runtime: lambda.Runtime.NODEJS_20_X, // Updated to latest Node.js runtime
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda'),
      timeout: cdk.Duration.seconds(25),
      memorySize: 2048,
      environment: {
        UPLOADS_BUCKET: uploadsBucket.bucketName,
        SUMMARIES_BUCKET: summariesBucket.bucketName,
        NODE_ENV: 'production'
      },
      logRetention: logs.RetentionDays.ONE_WEEK
    });

    // Add basic request validation model
    const uploadUrlModel = new apigateway.Model(this, 'UploadUrlModel', {
      restApi: api,
      contentType: 'application/json',
      modelName: 'UploadUrlModel',
      schema: {
        schema: apigateway.JsonSchemaVersion.DRAFT4,
        title: 'uploadUrlSchema',
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['filename'],
        properties: {
          filename: { type: apigateway.JsonSchemaType.STRING }
        }
      }
    });

    // Add explicit permission for API Gateway to invoke Lambda
    apiFunction.addPermission('ApiGatewayInvokePermission', {
      principal: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      sourceArn: `arn:aws:execute-api:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:${api.restApiId}/*/*/*`
    });

    // Grant Lambda permissions to access S3 buckets with more specific permissions
    // For uploads bucket, allow read and specific write operations
    uploadsBucket.grantRead(apiFunction);
    apiFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        's3:PutObject',
        's3:DeleteObject'
      ],
      resources: [`${uploadsBucket.bucketArn}/*`]
    }));
    
    // For summaries bucket, allow read and specific write operations
    summariesBucket.grantRead(apiFunction);
    apiFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        's3:PutObject',
        's3:DeleteObject'
      ],
      resources: [`${summariesBucket.bucketArn}/*`]
    }));

    // Create S3 event processor to trigger Step Function
    const s3EventProcessor = new lambda.Function(this, 'S3EventProcessor', {
      runtime: lambda.Runtime.NODEJS_20_X, // Updated to latest Node.js runtime
      handler: 'index.handler',
      environment: {
        USE_WHISPER: 'true',  // Set to true to use Whisper by default
      },
      code: lambda.Code.fromInline(`
        const { SFNClient, StartExecutionCommand } = require('@aws-sdk/client-sfn');
        const sfnClient = new SFNClient();
        
        exports.handler = async (event) => {
          console.log('Received S3 event:', JSON.stringify(event, null, 2));
          
          try {
            for (const record of event.Records) {
              console.log('Processing record:', JSON.stringify(record, null, 2));
              
              // Default to using Whisper instead of AWS Transcribe
              const useWhisper = process.env.USE_WHISPER === 'true';
              console.log('Using Whisper for transcription:', useWhisper);
              
              const params = {
                stateMachineArn: '${stateMachine.stateMachineArn}',
                input: JSON.stringify({
                  detail: {
                    bucket: { name: record.s3.bucket.name },
                    object: { key: record.s3.object.key }
                  },
                  useWhisper: useWhisper
                })
              };
              
              console.log('Starting Step Function execution with params:', JSON.stringify(params, null, 2));
              
              const command = new StartExecutionCommand(params);
              const result = await sfnClient.send(command);
              console.log('Step Function execution started:', result);
            }
          } catch (error) {
            console.error('Error processing S3 event:', error);
            throw error;
          }
        };
      `)
    });

    // Grant permissions
    stateMachine.grantStartExecution(s3EventProcessor);
    uploadsBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED_PUT,
      new s3n.LambdaDestination(s3EventProcessor)
    );

    // Create API endpoints with proxy integration
    const apiIntegration = new apigateway.LambdaIntegration(apiFunction, {
      proxy: true
    });

    // Create and configure resources with explicit CORS
    const corsOptions = {
      allowOrigins: ['*'],
      allowMethods: ['*'],
      allowHeaders: ['*'],
      allowCredentials: true,
      exposeHeaders: ['*'],
      maxAge: cdk.Duration.seconds(86400),
    };

    const getUploadUrl = api.root.addResource('get-upload-url');
    // Add POST method with validation
    getUploadUrl.addMethod('POST', apiIntegration, {
      requestValidator: requestValidator,
      requestModels: {
        'application/json': uploadUrlModel
      }
    });

    const checkSummaryRoot = api.root.addResource('check-summary');
    const checkSummary = checkSummaryRoot.addResource('{uuid}');

    // Add GET method with enhanced validation
    checkSummary.addMethod('GET', apiIntegration, {
      requestValidator: requestValidator,
      requestParameters: {
        'method.request.path.uuid': true  // Require the uuid parameter
      },
      methodResponses: [{
        statusCode: '200',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
          'method.response.header.Access-Control-Allow-Methods': true,
          'method.response.header.Access-Control-Allow-Headers': true,
          'method.response.header.Access-Control-Allow-Credentials': true,
        },
      },
      {
        statusCode: '400',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
          'method.response.header.Access-Control-Allow-Methods': true,
          'method.response.header.Access-Control-Allow-Headers': true,
        },
      }]
    });

    const fetchSummaryRoot = api.root.addResource('fetch-summary');
    const fetchSummary = fetchSummaryRoot.addResource('{filename}');

    // Add GET method with enhanced validation
    fetchSummary.addMethod('GET', apiIntegration, {
      requestValidator: requestValidator,
      requestParameters: {
        'method.request.path.filename': true  // Require the filename parameter
      },
      methodResponses: [{
        statusCode: '200',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
          'method.response.header.Access-Control-Allow-Methods': true,
          'method.response.header.Access-Control-Allow-Headers': true,
        },
      },
      {
        statusCode: '400',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
          'method.response.header.Access-Control-Allow-Methods': true,
          'method.response.header.Access-Control-Allow-Headers': true,
        },
      },
      {
        statusCode: '404',
        responseParameters: {
          'method.response.header.Access-Control-Allow-Origin': true,
          'method.response.header.Access-Control-Allow-Methods': true,
          'method.response.header.Access-Control-Allow-Headers': true,
        },
      }]
    });

    // Output the API endpoint URL
    new cdk.CfnOutput(this, 'ApiEndpoint', {
      description: 'API Gateway endpoint URL',
      value: api.url,
    });

    new cdk.CfnOutput(this, 'ApiId', {
      description: 'API Gateway ID',
      value: api.restApiId,
    });

    // Define common CloudFront behavior patterns
    const baseApiPattern = {
      origin: new origins.RestApiOrigin(api, {
        originPath: '/prod'  // Keep /prod in the origin path
      }),
      viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
      cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
      cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
      originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,  // Forward all headers except Host
      responseHeadersPolicy: cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT
    };

    // Create CloudFront distribution with default viewer certificate
    // Create access logs destination bucket for the CloudFront logs bucket itself
    const accessLogsDestinationBucket = new s3.Bucket(this, 'AccessLogsDestinationBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(90),
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30)
            }
          ]
        }
      ]
    });

    // Set up CloudFront access logs bucket with encryption, lifecycle rules, and server access logging
    const accessLogsBucket = new s3.Bucket(this, 'AccessLogsBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      serverAccessLogsBucket: accessLogsDestinationBucket,
      serverAccessLogsPrefix: 'access-logs-bucket-logs/',
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(90),  // Retain logs for 90 days
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30)
            }
          ]
        }
      ]
    });

    // Create origin access identity for CloudFront
    const uiOriginAccessIdentity = new cloudfront.OriginAccessIdentity(this, 'UIOriginAccessIdentity', {
      comment: 'Access to UI bucket'
    });
    
    const uploadsOriginAccessIdentity = new cloudfront.OriginAccessIdentity(this, 'UploadsOriginAccessIdentity', {
      comment: 'Access to uploads bucket'
    });
    
    // Grant the OAI access to the buckets
    uiBucket.grantRead(uiOriginAccessIdentity);
    uploadsBucket.grantRead(uploadsOriginAccessIdentity);
    
    // Create CloudFront distribution with enhanced security settings
    const distribution = new cloudfront.Distribution(this, 'UIDistribution', {
      defaultBehavior: {
        origin: new origins.S3Origin(uiBucket, {
          originAccessIdentity: uiOriginAccessIdentity
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
      additionalBehaviors: {
        'check-summary/*': baseApiPattern,
        'fetch-summary/*': baseApiPattern,
        'uploads/*': {
          origin: new origins.S3Origin(uploadsBucket, {
            originAccessIdentity: uploadsOriginAccessIdentity
          }),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        },
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
        },
      ],
      // The default CloudFront certificate (.cloudfront.net) will be used automatically
      // by not specifying any certificate property
      // CloudFront logging disabled to avoid S3 bucket ACL issues
      // Set minimum TLS protocol version - this specifically addresses the CFR4 issue
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      // Enable geo restriction if needed (uncomment and configure as required)
      // geoRestriction: {
      //   restrictionType: cloudfront.GeoRestrictionType.WHITELIST,
      //   locations: ['US', 'CA'],  // Allow access only from US and Canada
      // },
    });
    
    // Add CDK-nag suppression for CloudFront logging

    new cdk.CfnOutput(this, 'CloudFrontURL', {
      description: 'CloudFront URL',
      value: distribution.distributionDomainName,
    });

    new cdk.CfnOutput(this, 'UIBucketName', {
      description: 'Frontend UI S3 Bucket Name',
      value: uiBucket.bucketName,
    });  }
}
