import boto3
import os
import json
from PIL import Image
import io

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # 1. Get bucket and key from S3 event
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"Processing: {key} from {source_bucket}")
        
        # 2. Download image
        response = s3.get_object(Bucket=source_bucket, Key=key)
        image_data = response['Body'].read()
        
        # 3. Create thumbnail
        image = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if needed for JPEG compatibility
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create a white background and paste the image
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.thumbnail((200, 200))
        
        # Save thumbnail to buffer
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # 4. Upload to processed bucket
        processed_bucket = os.environ['PROCESSED_BUCKET']
        # Create new key: keep folder structure, append '_thumbnail' before extension
        name, ext = os.path.splitext(key)
        thumb_key = f"{name}_thumbnail.jpg"
        
        s3.put_object(
            Bucket=processed_bucket,
            Key=thumb_key,
            Body=buffer,
            ContentType='image/jpeg'
        )
        
        print(f"Uploaded thumbnail to: {processed_bucket}/{thumb_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {key} successfully')
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
