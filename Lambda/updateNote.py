import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table('Notes')

def lambda_handler(event, context):
    try:
        note_id = event.get('pathParameters', {}).get('id')
        body    = json.loads(event.get('body') or '{}')

        if not note_id:
            return response(400, {'error': 'noteId is required in the path'})

        existing = table.get_item(Key={'noteId': note_id}).get('Item')
        if not existing:
            return response(404, {'error': 'Note not found'})

        updates = {}
        if 'title'   in body: updates['title']   = body['title'].strip()
        if 'content' in body: updates['content'] = body['content'].strip()

        if not updates:
            return response(400, {'error': 'Provide at least title or content to update'})

        updates['updatedAt'] = datetime.utcnow().isoformat()

        expr       = 'SET ' + ', '.join(f'#{k} = :{k}' for k in updates)
        expr_names = {f'#{k}': k for k in updates}
        expr_vals  = {f':{k}': v for k, v in updates.items()}

        result = table.update_item(
            Key={'noteId': note_id},
            UpdateExpression=expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_vals,
            ReturnValues='ALL_NEW'
        )

        return response(200, {'message': 'Note updated', 'note': result['Attributes']})

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
