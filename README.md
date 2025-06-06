## Slack Bot Template for Production Railway 🚃🤖

### 1) Create your app

Sign up or login and create your app. 
\
https://api.slack.com/apps

### 2) Select OAuth and Permission -> Bot Token Scopes. Then add the following Bot Token scopes shown below.

- app_mentions:read
- channels:history
- channels:read
- chat:write
- commands
- im:history
- mpim:history

  <img width="549" alt="Screenshot 2024-08-08 at 1 17 37 PM" src="https://github.com/user-attachments/assets/8775df9e-2c58-41ef-aa69-3d9f072f0dc8">
  
**Then Install the app to the Workspace.**

### 3) Go to Railway and deplay my template

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/iSYwFQ?referralCode=nHrUhe)

Add the following secret variables for deployment.
- **SLACK_BOT_TOKEN** (located in OAuth & Permission)
- **SLACK_SIGNING_SECRET** (located in Basic Information)
- **SLACK_BOT_USER_ID** (located in Basic Information)

#### GitHub Integration (Optional)
If you want to receive GitHub notifications, add these additional variables:
- **GITHUB_WEBHOOK_SECRET** (create a secret key for webhook verification)
- **GITHUB_NOTIFICATIONS_CHANNEL** (Slack channel ID where notifications will be sent)

Once your variable are added deply the template

### 4) Once your the slack template is deployed. Go to setting and generate your domain

Settings → Networking → Generate Domain  

### 5) Once your domain is set up then go back to slack API and go to your Event Subscription

turn on Enable Events. Then in your request url paste your domain in this specific format.     
<img width="565" alt="Screenshot 2024-08-08 at 1 04 59 PM" src="https://github.com/user-attachments/assets/9ba3bef6-6f7d-4108-8ec1-55763fd91392">

#### https://{your-domain}/slack/events

Add the following scope in the Event Subscriptions below. Then Save changes.
<img width="554" alt="Screenshot 2024-08-08 at 1 02 48 PM" src="https://github.com/user-attachments/assets/bcbf9a30-13a7-4dd1-b5aa-05e51de139e7">

### 6) Turn on Interactivity & Shortcuts and paste in your request url and save changes
<img width="559" alt="Screenshot 2024-08-08 at 1 04 21 PM" src="https://github.com/user-attachments/assets/77dbbf27-4447-4a85-9f35-b35297589dcc">

### 7) Go to Slash Commands → Create new Command

Here are the requiremnets for your slack comand

- Command Name (has to be the states the same in the code)
- Request Url ( [http://{your-domain}/slack/events )
- Short Description
<img width="516" alt="Screenshot 2024-08-08 at 1 06 55 PM" src="https://github.com/user-attachments/assets/bdc67fb7-5960-418d-b4bd-e9762fd96c30">

here are the Command Names in the template.
- /command_example
- /modal_example
- /button_example
- /medi-pr-test

### 8) GitHub Webhook Setup (Optional)

If you want to receive GitHub notifications for releases and pull requests:

1. Go to your GitHub repository → Settings → Webhooks
2. Click "Add webhook"
3. Configure the webhook:
   - **Payload URL**: `https://{your-domain}/github/webhook`
   - **Content type**: `application/json`
   - **Secret**: Use the same value as your `GITHUB_WEBHOOK_SECRET` environment variable
   - **Which events**: Select "Let me select individual events" and choose:
     - Pull requests
     - Releases
4. Click "Add webhook"

The bot will now send notifications to your specified Slack channel for:
- New releases (including pre-releases and drafts)
- Pull request creation, closure, and merging
- Special notifications for release branch pull requests

### Once your done invite your slack bot to a channel and try out the template Example

<img width="394" alt="Screenshot 2024-08-08 at 1 10 07 PM" src="https://github.com/user-attachments/assets/dc2cfaab-f75e-420d-a8a1-d25ba5c43f3a">

## Features

### Slack Commands
- `/command_example` - Example command response
- `/modal_example` - Opens a modal dialog
- `/button_example` - Shows interactive buttons
- `/medi-pr-test` - PR reviewer assignment tool

### GitHub Integration
- Automatic notifications for repository releases
- Pull request notifications with special handling for release branches
- Secure webhook verification
- Rich formatted messages with repository and PR details




  
