from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv, find_dotenv
from db_manager import DatabaseManager
import random

load_dotenv(find_dotenv())

db = DatabaseManager()

SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_BOT_USER_ID = os.getenv('SLACK_BOT_USER_ID')
PSQL_URL = os.getenv('DATABASE_URL')

flask_app = Flask(__name__)
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


handler = SlackRequestHandler(app)

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

@app.command("/medi-pr-test")
def medi_pr_test_command(ack, say, body, command, logger, client):
    ack()
    try:
        text = command.get('text', '').strip()
        if not text.startswith('cr '):
            say('Usage: /medi-pr-test cr <link>')
            return
        link = text[3:].strip()
        channel_id = body['channel_id']
        # Fetch users in the channel
        members_resp = client.conversations_members(channel='C03GLBY2B41')
        members = members_resp.get('members', [])
        # Remove the bot itself from the list
        bot_user_id = os.getenv('SLACK_BOT_USER_ID')
        members = [m for m in members if m != bot_user_id]
        if len(members) < 2:
            say('Not enough users in the channel to assign reviewers.')
            return
        reviewers = random.sample(members, 2)
        # Optionally, fetch user info for display names
        reviewer_names = []
        for user_id in reviewers:
            user_info = client.users_info(user=user_id)
            reviewer_names.append(f"<{user_id}>")
        say(f"Pull request: {link}\nReviewers: {', '.join(reviewer_names)}")
    except Exception as e:
        logger.error(f"Error in /medi-pr-test: {e}")
        say('An error occurred while processing the command.')

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
