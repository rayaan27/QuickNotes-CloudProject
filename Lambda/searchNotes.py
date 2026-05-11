import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table('Notes')

def lambda_handler(event, context):
    try:
        params  = event.get('queryStringParameters') or {}
        keyword = params.get('search', '').strip().lower()

        if not keyword:
            return response(400, {'error': 'search query parameter is required — e.g. /notes/search?search=meeting'})

        # Scan DynamoDB and filter by keyword in title OR content
        result = table.scan(
            FilterExpression=(
                Attr('title').contains(keyword) |
                Attr('content').contains(keyword)
            )
        )

        notes = result.get('Items', [])

        # Sort newest first
        notes.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

        return response(200, {
            'keyword': keyword,
            'count':   len(notes),
            'notes':   notes
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
