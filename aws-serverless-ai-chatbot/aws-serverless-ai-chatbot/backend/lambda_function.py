import json
import os
import time

import boto3
from boto3.dynamodb.conditions import Key

bedrock = boto3.client("bedrock-runtime")
table = boto3.resource("dynamodb").Table("ChatHistory")
MODEL_ID = os.environ["MODEL_ID"]

SYSTEM_PROMPT = "You are a helpful AWS learning assistant. Keep answers clear and simple."
MAX_MESSAGE_LENGTH = 2000


def response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        session_id = body["sessionId"]
        user_msg = body["message"].strip()

        if not user_msg or len(user_msg) > MAX_MESSAGE_LENGTH:
            return response(400, {"error": "Message must be 1-2000 characters"})

        # 1. Load the last 20 messages of this chat from DynamoDB
        result = table.query(
            KeyConditionExpression=Key("sessionId").eq(session_id),
            ScanIndexForward=False,
            Limit=20,
        )
        history = list(reversed(result["Items"]))
        while history and history[0]["role"] != "user":
            history.pop(0)  # a conversation must start with a user message

        messages = [
            {"role": h["role"], "content": [{"text": h["text"]}]} for h in history
        ]
        messages.append({"role": "user", "content": [{"text": user_msg}]})

        # 2. Ask the AI model through the Bedrock Converse API
        ai = bedrock.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            inferenceConfig={"maxTokens": 800, "temperature": 0.5},
        )
        reply = ai["output"]["message"]["content"][0]["text"]

        # 3. Save both messages (sort key "ts" is a Number)
        now = int(time.time() * 1000)
        table.put_item(Item={"sessionId": session_id, "ts": now, "role": "user", "text": user_msg})
        table.put_item(Item={"sessionId": session_id, "ts": now + 1, "role": "assistant", "text": reply})

        return response(200, {"reply": reply})

    except Exception as e:
        print("ERROR:", str(e))  # full error goes to CloudWatch Logs only
        return response(500, {"error": "Something went wrong"})
