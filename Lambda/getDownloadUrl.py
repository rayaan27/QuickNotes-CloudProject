import json
import boto3
import os

s3       = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table('Notes')

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'quicknotes-files')
URL_EXPIRY  = 300  # 5 minutes

def lambda_handler(event, context):
    try:
        note_id = event.get('pathParameters', {}).get('id')

        if not note_id:
            return response(400, {'error': 'noteId is required in the path'})

        # Get the note from DynamoDB
        result = table.get_item(Key={'noteId': note_id})
        note   = result.get('Item')

        if not note:
            return response(404, {'error': 'Note not found'})

        file_key = note.get('fileKey')

        if not file_key:
            return response(404, {'error': 'No file attached to this note'})

        # Generate a pre-signed GET URL
        download_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key':    file_key
            },
            ExpiresIn=URL_EXPIRY
        )

        return response(200, {
            'downloadUrl': download_url,
            'fileKey':     file_key,
            'expiresIn':   f'{URL_EXPIRY} seconds',
            'noteTitle':   note.get('title'),
            'instructions': 'Open downloadUrl in a browser or send a GET request to download the file'
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
