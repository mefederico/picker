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
import hmac
import hashlib

load_dotenv(find_dotenv())

db = DatabaseManager()

SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_BOT_USER_ID = os.getenv('SLACK_BOT_USER_ID')
PSQL_URL = os.getenv('DATABASE_URL')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
GITHUB_NOTIFICATIONS_CHANNEL = os.getenv('GITHUB_NOTIFICATIONS_CHANNEL', 'C04D5B9EXLZ')  # Default channel

flask_app = Flask(__name__)
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

handler = SlackRequestHandler(app)

def verify_github_signature(payload_body, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256."""
    if not signature_header:
        return False
    
    if not GITHUB_WEBHOOK_SECRET:
        return False
    
    try:
        hash_object = hmac.new(GITHUB_WEBHOOK_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = "sha256=" + hash_object.hexdigest()
        return hmac.compare_digest(expected_signature, signature_header)
    except Exception as e:
        print(f"Error during signature verification: {e}")
        return False

def format_slack_message_for_release(event_data):
    """Format a Slack message for GitHub release events."""
    action = event_data.get('action')
    release = event_data.get('release', {})
    repository = event_data.get('repository', {})
    
    repo_name = repository.get('full_name', 'Unknown Repository')
    release_name = release.get('name') or release.get('tag_name', 'Unknown Release')
    release_url = release.get('html_url', '')
    release_body = release.get('body', '')
    is_prerelease = release.get('prerelease', False)
    is_draft = release.get('draft', False)
    
    # Determine emoji and message based on release type
    if is_draft:
        emoji = "📝"
        status = "Draft Release"
    elif is_prerelease:
        emoji = "🚧"
        status = "Pre-release"
    else:
        emoji = "🚀"
        status = "Release"
    
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {status} {action.title()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n{repo_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release:*\n<{release_url}|{release_name}>"
                    }
                ]
            }
        ]
    }
    
    # Add release notes if available
    if release_body:
        # Truncate if too long
        truncated_body = release_body[:500] + "..." if len(release_body) > 500 else release_body
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Release Notes:*\n```{truncated_body}```"
            }
        })
    
    return message

def format_slack_message_for_pr(event_data):
    """Format a Slack message for GitHub PR events."""
    action = event_data.get('action')
    pull_request = event_data.get('pull_request', {})
    repository = event_data.get('repository', {})
    
    repo_name = repository.get('full_name', 'Unknown Repository')
    pr_title = pull_request.get('title', 'Unknown PR')
    pr_url = pull_request.get('html_url', '')
    pr_number = pull_request.get('number', 0)
    pr_user = pull_request.get('user', {}).get('login', 'Unknown User')
    pr_body = pull_request.get('body', '')
    base_branch = pull_request.get('base', {}).get('ref', 'main')
    head_branch = pull_request.get('head', {}).get('ref', 'unknown')
    
    # Check if this is a release branch
    is_release_branch = 'release' in head_branch.lower() or 'release' in base_branch.lower()
    
    emoji = "🔀" if not is_release_branch else "🚀"
    branch_info = f"from `{head_branch}` to `{base_branch}`"
    
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Pull Request {action.title()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n{repo_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*PR:*\n<{pr_url}|#{pr_number}: {pr_title}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Author:*\n{pr_user}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Branches:*\n{branch_info}"
                    }
                ]
            }
        ]
    }
    
    # Add special notification for release branches
    if is_release_branch:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚨 *This is a release branch PR!*"
            }
        })
    
    # Add PR description if available
    if pr_body:
        # Truncate if too long
        truncated_body = pr_body[:300] + "..." if len(pr_body) > 300 else pr_body
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n```{truncated_body}```"
            }
        })
    
    return message

@flask_app.route("/github/webhook", methods=["POST"])
def github_webhook():
    """Handle GitHub webhook events."""
    try:
        # Get the signature from headers
        signature = request.headers.get('X-Hub-Signature-256')
        
        # Get the event type
        event_type = request.headers.get('X-GitHub-Event')
        
        # Get raw payload data for signature verification
        raw_payload = request.get_data()
        
        # Verify the payload came from GitHub
        if GITHUB_WEBHOOK_SECRET and not verify_github_signature(raw_payload, signature):
            return jsonify({"error": "Invalid signature"}), 401
        
        # Handle different content types
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            payload = request.get_json()
        elif 'application/x-www-form-urlencoded' in content_type:
            # GitHub sends form data with 'payload' field containing JSON
            form_data = request.get_data(as_text=True)
            
            # Parse form data
            from urllib.parse import parse_qs, unquote_plus
            parsed_form = parse_qs(form_data)
            
            if 'payload' in parsed_form:
                payload_json = parsed_form['payload'][0]
                payload = json.loads(unquote_plus(payload_json))
            else:
                return jsonify({"error": "Invalid form payload"}), 400
        else:
            return jsonify({"error": "Unsupported content type"}), 400
        
        if not payload:
            return jsonify({"error": "No payload received"}), 400
        
        # Handle release events
        if event_type == 'release':
            action = payload.get('action')
            if action in ['released']:
                message = format_slack_message_for_release(payload)
                
                # Send to Slack
                try:
                    app.client.chat_postMessage(
                        channel=GITHUB_NOTIFICATIONS_CHANNEL,
                        blocks=message['blocks']
                    )
                except SlackApiError as e:
                    print(f"Error sending release notification to Slack: {e.response['error']}")
                    return jsonify({"error": "Failed to send Slack notification"}), 500
        
        # Handle pull request events
        elif event_type == 'pull_request':
            action = payload.get('action')
            if action in ['opened', 'closed', 'merged']:
                message = format_slack_message_for_pr(payload)
                
                # Send to Slack
                try:
                    app.client.chat_postMessage(
                        channel=GITHUB_NOTIFICATIONS_CHANNEL,
                        blocks=message['blocks']
                    )
                except SlackApiError as e:
                    print(f"Error sending PR notification to Slack: {e.response['error']}")
                    return jsonify({"error": "Failed to send Slack notification"}), 500
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Error handling GitHub webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

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

@flask_app.route("/github/webhook/test", methods=["GET"])
def github_webhook_test():
    """Test endpoint to verify GitHub webhook setup."""
    # Test Slack connection
    slack_connection_ok = False
    slack_error = None
    try:
        test_response = app.client.auth_test()
        slack_connection_ok = test_response.get("ok", False)
    except Exception as e:
        slack_error = str(e)
    
    return jsonify({
        "status": "GitHub webhook endpoint is active",
        "timestamp": datetime.datetime.now().isoformat(),
        "webhook_url": "/github/webhook",
        "supported_events": ["release", "pull_request"],
        "configuration": {
            "webhook_secret_configured": bool(GITHUB_WEBHOOK_SECRET),
            "webhook_secret_length": len(GITHUB_WEBHOOK_SECRET) if GITHUB_WEBHOOK_SECRET else 0,
            "notifications_channel": GITHUB_NOTIFICATIONS_CHANNEL,
            "slack_bot_token_configured": bool(SLACK_BOT_TOKEN),
            "slack_connection_ok": slack_connection_ok,
            "slack_error": slack_error
        },
        "instructions": {
            "setup_webhook": "Add webhook in GitHub: Settings → Webhooks → Add webhook",
            "payload_url": f"{request.url_root}github/webhook",
            "content_type": "application/json",
            "events": ["Pull requests", "Releases"],
            "test_delivery": "After setup, use 'Recent Deliveries' to test and view logs"
        }
    }), 200



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
