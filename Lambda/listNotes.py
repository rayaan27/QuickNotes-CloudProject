import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Notes')

def lambda_handler(event, context):
    try:
        result = table.scan()
        notes  = result.get('Items', [])

        # Sort newest first
        notes.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

        return response(200, {'count': len(notes), 'notes': notes})

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
