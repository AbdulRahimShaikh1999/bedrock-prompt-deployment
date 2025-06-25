import os
import json
from jinja2 import Template
import boto3

# === Step 1: Load template and variables ===
TEMPLATE_PATH = "prompt_templates/welcome_email.txt"
CONFIG_PATH = "prompts/welcome_prompt.json"

with open(TEMPLATE_PATH, "r") as f:
    template_str = f.read()

with open(CONFIG_PATH, "r") as f:
    variables = json.load(f)

template = Template(template_str)
final_prompt = template.render(variables)

print("Rendered Prompt:")
print(final_prompt)

# === Step 2: Call Claude via Bedrock ===
json_body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": f"Human: {final_prompt}"
        }
    ]
})

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

response = bedrock.invoke_model(
    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
    body=json_body,
    contentType="application/json",
    accept="application/json"
)


response_body = json.loads(response["body"].read())
bedrock_output = response_body["content"][0]["text"]

print("\n🧠 Bedrock Response:")
print(bedrock_output)

# === Step 3: Save response and upload to S3 ===
env = os.getenv("DEPLOY_ENV", "beta")

bucket_name = os.getenv("S3_BUCKET_BETA") if env == "beta" else os.getenv("S3_BUCKET_PROD")

filename = f"{env}_welcome_{variables['name'].lower()}.html"
output_path = f"outputs/{filename}"
s3_key = f"{env}/outputs/{filename}"

os.makedirs("outputs", exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(bedrock_output)

print(f"✅ Saved to {output_path}")
print(f"🔍 Environment: {env}")
print(f"📁 Filename: {filename}")
print(f"🪣 S3 Bucket: {bucket_name}")
print(f"🗂️ S3 Key: {s3_key}")

s3 = boto3.client("s3")
s3.upload_file(Filename=output_path, Bucket=bucket_name, Key=s3_key)

print(f"📤 Uploaded to s3://{bucket_name}/{s3_key}")
