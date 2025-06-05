from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
import os
import json
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_BOT_USER_ID = os.getenv('SLACK_BOT_USER_ID')
PSQL_URL = os.getenv('DATABASE_URL')

flask_app = Flask(__name__)
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


handler = SlackRequestHandler(app)

result = urlparse(psql_url)

conn = psycopg2.connect(
    dbname=result.path[1:],  # Skip the leading '/'
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port
)

cur = conn.cursor()
cur.execute("SELECT version();")
result = cur.fetchone()
print(result)

cur.close()
conn.close()

# listen fur user mentoining the slack app
@app.event("app_mention")
def event_test(body, say, logger):
    logger.info(body)
    say("What's up?")

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)



@app.command("/command_example")
def pricing_command(ack, say, body,  command, logger, client):
    ack()
    trigger_id = body['trigger_id']
    logger.info("Hola")
    logger.info("db" + result)
    try:
        with open('command_example.json') as file:      
            json_data = json.load(file)
            say(json_data)
    except Exception as e:
        logger.error(f"Error Handling in /command_example {e}")


@app.command("/modal_example")
def pricing_command(ack, say, body,  command, logger, client):
    ack()
    trigger_id = body['trigger_id']
    try:
        with open('modal_example.json') as file:
            json_data = json.load(file)
            client.views_open(trigger_id=trigger_id, view=json_data)
    except Exception as e:
                logger.error(f"Error Handling in /modal_example {e}")

@app.view("modal_example")
def handle_pricing_submission(ack, body, logger):
    ack()
    try:
        print('pricing modals works')
    except Exception as e:
        logger.error(f"Error Handling modal_example{e}")

@app.command("/button_example")
def pricing_command(ack, say, body,  command, logger, client):
    ack()
    trigger_id = body['trigger_id']
    try:
        with open('button_example.json') as file:      
            json_data = json.load(file)
            say(json_data)
    except Exception as e:
        logger.error(f"Error Handling /button_example {e}")

@app.action("actionId-0")
def pricing_command(ack, say, body, logger, client):
    ack()
    trigger_id = body['trigger_id']
    try:
        with open('example.json') as file:      
            json_data = json.load(file)
            say(trigger_id=trigger_id, blocks=json_data['blocks'])

    except Exception as e:
        logger.error(f"Error Handling hactionId-0 {e}")


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
