# aws-serverless-ai-chatbot
Serverless generative AI chatbot on AWS using Amazon Bedrock (Nova), Lambda, API Gateway, DynamoDB and S3, with persistent conversation memory.
# Serverless AI Chatbot on AWS

A ChatGPT-style chat application built entirely with AWS serverless services. Users type a question in a web page, and an AI model on **Amazon Bedrock** answers. Each conversation is stored in **DynamoDB**, so the chatbot remembers earlier messages.

> Screenshots: see the `screenshots/` folder.

## Architecture

```
User's browser
     |
     v
S3 static website  (index.html)
     |  POST /chat  { sessionId, message }
     v
API Gateway (HTTP API)
     |
     v
Lambda (Python 3.x) ----> DynamoDB  (load and save chat history)
     |
     v
Amazon Bedrock (Amazon Nova, Converse API)
     |
     v
Reply returned to the browser
```

## AWS services used

| Service | Role in the project |
|---|---|
| Amazon S3 | Hosts the static chat web page |
| Amazon API Gateway (HTTP API) | Public `POST /chat` endpoint |
| AWS Lambda (Python) | Backend logic: history, AI call, saving messages |
| Amazon Bedrock (Amazon Nova) | Generates the AI replies through the Converse API |
| Amazon DynamoDB (on-demand) | Stores conversation history per session |
| AWS IAM | Least-privilege role for Lambda |
| Amazon CloudWatch Logs | Logging and debugging |

## How it works

1. The page creates a random `sessionId` when it loads. One page load is one conversation.
2. On Send, the page POSTs `{ sessionId, message }` to API Gateway.
3. API Gateway invokes the Lambda function.
4. Lambda loads the last 20 messages for that `sessionId` from DynamoDB.
5. Lambda sends the history and the new message to Bedrock using the Converse API.
6. Lambda saves the user message and the AI reply to DynamoDB.
7. The reply goes back to the page.

## Project structure

```
aws-serverless-ai-chatbot/
├── README.md
├── frontend/index.html          # chat page (hosted on S3)
├── backend/lambda_function.py   # Lambda function
├── iam/lambda-policy.json       # inline policy for the Lambda role
├── iam/s3-bucket-policy.json    # public-read policy for the website bucket
└── screenshots/
```

## Setup

Use one region for everything (for example `us-east-1`).

1. **Bedrock:** open the Model catalog, choose an Amazon Nova model (for example Nova Lite), and copy its model ID or inference profile ID (for example `us.amazon.nova-lite-v1:0`). Test it once in the Playground.
2. **DynamoDB:** create table `ChatHistory` with partition key `sessionId` (String) and sort key `ts` (**Number**). Use on-demand capacity.
3. **IAM:** create a Lambda role named `chatbotLambdaRole`. Attach `AWSLambdaBasicExecutionRole`, and add the inline policy from `iam/lambda-policy.json` (replace `REGION` and `ACCOUNT_ID`).
4. **Lambda:** create a Python function, use the role above, paste `backend/lambda_function.py`, and click Deploy. Set the timeout to 30 seconds and add the environment variable `MODEL_ID` with your model ID.
5. **API Gateway:** create an HTTP API with route `POST /chat` integrated with the Lambda function, stage `$default` with auto-deploy. Copy the invoke URL and add `/chat` at the end.
6. **Front end:** put your API URL in `API_URL` inside `frontend/index.html`.
7. **S3:** create a bucket, upload `index.html`, enable static website hosting, turn off Block Public Access, and apply `iam/s3-bucket-policy.json` (replace the bucket name). Open the bucket website endpoint.

## Challenges and fixes

- **Invalid model identifier:** Nova models in `us-east-1` need the inference profile ID (with the `us.` prefix), not the bare model ID.
- **DynamoDB type mismatch on `ts`:** the sort key was created as a String while the code wrote a Number. Key types cannot be changed after creation, so the table was recreated with a Number sort key.
- **Browser "Failed to fetch":** the API worked from the command line but the browser blocked the response because of CORS. Fixed by configuring CORS on the API, returning `Access-Control-Allow-Origin` from Lambda, and sending the request as `text/plain` so no preflight is required.
- **Debugging:** temporarily returning the raw error in the response made the real cause visible. It was changed back to a generic message afterwards, and full errors stay in CloudWatch Logs.

## Security notes

- The Lambda role follows least privilege for DynamoDB (two actions on one table). Bedrock access uses `*` for simplicity and can be limited to a specific model ARN.
- The API has no authentication, so anyone with the URL can call it. For a public deployment, add Amazon Cognito and API throttling.
- Do not commit AWS account IDs, access keys, or personal details.

## Cost

Everything is pay-per-use, so an idle deployment costs almost nothing. Bedrock charges per message. Set an AWS Budget alert before sharing the project.

## Future improvements

- Amazon Cognito login so each user sees only their own chats
- CloudFront with an ACM certificate for HTTPS
- Streaming replies
- Restrict the Bedrock permission to a specific model ARN
- Input validation and API throttling

## Clean up

Delete the S3 bucket, API, Lambda function, its CloudWatch log group, the DynamoDB table, and the IAM role to stop all resources.

## Resume summary

Built a serverless generative AI chat application on AWS using Amazon Bedrock (Nova), Lambda, API Gateway, DynamoDB, and S3, with persistent conversation memory and least-privilege IAM.
