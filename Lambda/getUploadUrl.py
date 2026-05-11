import json
import boto3
import os
from datetime import datetime

s3       = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table('Notes')

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'quicknotes-files')   # set this in Lambda env vars
URL_EXPIRY  = 300  # pre-signed URL valid for 5 minutes

def lambda_handler(event, context):
    try:
        note_id  = event.get('pathParameters', {}).get('id')
        params   = event.get('queryStringParameters') or {}
        filename = params.get('filename', 'attachment')

        if not note_id:
            return response(400, {'error': 'noteId is required in the path'})

        # Check note exists
        existing = table.get_item(Key={'noteId': note_id}).get('Item')
        if not existing:
            return response(404, {'error': 'Note not found'})

        # Build a unique S3 key so files never overwrite each other
        s3_key = f'notes/{note_id}/{filename}'

        # Generate a pre-signed PUT URL — the client uploads directly to S3
        upload_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket':      BUCKET_NAME,
                'Key':         s3_key,
                'ContentType': 'application/octet-stream'
            },
            ExpiresIn=URL_EXPIRY
        )

        # Store the S3 key on the note record so we can retrieve the file later
        table.update_item(
            Key={'noteId': note_id},
            UpdateExpression='SET fileKey = :fk, updatedAt = :ua',
            ExpressionAttributeValues={
                ':fk': s3_key,
                ':ua': datetime.utcnow().isoformat()
            }
        )

        return response(200, {
            'uploadUrl': upload_url,
            'fileKey':   s3_key,
            'expiresIn': f'{URL_EXPIRY} seconds',
            'instructions': 'Send a PUT request to uploadUrl with your file as the raw body'
        })

    except Exception as e:
        return response(500, {'error': str(e)})


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type':                'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
