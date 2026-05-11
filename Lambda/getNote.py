import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Notes')

def lambda_handler(event, context):
    try:
        note_id = event.get('pathParameters', {}).get('id')

        if not note_id:
            return response(400, {'error': 'noteId is required in the path'})

        result = table.get_item(Key={'noteId': note_id})
        note   = result.get('Item')

        if not note:
            return response(404, {'error': 'Note not found'})

        return response(200, {'note': note})

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
