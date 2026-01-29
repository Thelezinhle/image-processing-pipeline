import boto3
import os
import json
from PIL import Image
import io

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        print("START: Lambda triggered by S3 event")
        
        # 1. Extract bucket and key from event
        record = event['Records'][0]
        source_bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        print(f"Source: s3://{source_bucket}/{key}")
        
        # 2. Download image from S3
        print("Downloading image...")
        response = s3.get_object(Bucket=source_bucket, Key=key)
        image_bytes = response['Body'].read()
        
        # 3. Create thumbnail (200x200)
        print("Resizing to 200x200 thumbnail...")
        image = Image.open(io.BytesIO(image_bytes))
        
        # Ensure RGB mode for JPEG
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.thumbnail((200, 200))
        
        # Save thumbnail to buffer
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # 4. Upload to processed bucket
        processed_bucket = os.environ['PROCESSED_BUCKET']
        thumbnail_key = f"thumb_{key}"
        
        print(f"Uploading to: s3://{processed_bucket}/{thumbnail_key}")
        s3.put_object(
            Bucket=processed_bucket,
            Key=thumbnail_key,
            Body=buffer,
            ContentType='image/jpeg'
        )
        
        print("SUCCESS: Thumbnail created and uploaded!")
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {key} successfully')
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
