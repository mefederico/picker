from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv, find_dotenv
from db_manager import DatabaseManager
import random
import datetime

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
        if text.startswith('cr '):
            link = text[3:].strip()
            channel_id = body['channel_id']
            members_resp = client.conversations_members(channel='C03GLBY2B41')
            members = members_resp.get('members', [])
            bot_user_id = os.getenv('SLACK_BOT_USER_ID')
            members = [m for m in members if m != bot_user_id]
            if len(members) < 2:
                say('Not enough users in the channel to assign reviewers.')
                return
            reviewers = random.sample(members, 2)
            reviewer_names = []
            for user_id in reviewers:
                user_info = client.users_info(user=user_id)
                reviewer_names.append(f"<{user_id}>")
            say(f"Pull request: {link}\nReviewers: {', '.join(reviewer_names)}")
        elif text.startswith('exclude '):
            parts = text.split()
            if len(parts) < 2:
                say('Usage: /medi-pr-test exclude <@U1234|user> [-For <days>]')
                return
            user_mention = parts[1]
            # Extract user_id from <@U1234|user>
            if user_mention.startswith('<@') and user_mention.endswith('>'):
                user_id = user_mention[2:-1].split('|')[0]
            else:
                say('Invalid user mention format.')
                return
            days = None
            if '-For' in parts:
                idx = parts.index('-For')
                if idx+1 < len(parts):
                    try:
                        days = int(parts[idx+1])
                    except ValueError:
                        say('Invalid number of days.')
                        return
            channel_id = body['channel_id']
            until = None
            if days:
                until = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            db.create_user(slack_id=user_id, until=until, available=False, channel=channel_id)
            if days:
                say(f"User <@{user_id}> excluded from this channel for {days} days.")
            else:
                say(f"User <@{user_id}> excluded from this channel permanently.")
        else:
            say('Usage: /medi-pr-test cr <link> or /medi-pr-test exclude <@U1234|user> [-For <days>]')
    except Exception as e:
        logger.error(f"Error in /medi-pr-test: {e}")
        say('An error occurred while processing the command.')

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
