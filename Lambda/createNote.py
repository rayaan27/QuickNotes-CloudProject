import json
import boto3
import uuid
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table('Notes')
sns      = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    try:
        raw_body = event.get('body') or '{}'
        body     = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        title   = body.get('title', '').strip()
        content = body.get('content', '').strip()

        if not title or not content:
            return response(400, {'error': 'title and content are required'})

        note = {
            'noteId':    str(uuid.uuid4()),
            'title':     title,
            'content':   content,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'fileKey':   None
        }

        table.put_item(Item=note)

        if SNS_TOPIC_ARN:
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject='QuickNotes - New note created',
                    Message=(
                        f'A new note has been created on QuickNotes.\n\n'
                        f'Title:   {title}\n'
                        f'NoteID:  {note["noteId"]}\n'
                        f'Created: {note["createdAt"]}\n'
                    )
                )
            except Exception as sns_error:
                print("SNS ERROR:", str(sns_error))

        return response(201, {'message': 'Note created', 'note': note})

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
