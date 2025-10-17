# Apgard SDK - Client Usage Guide

## Installation

`pip install apgard`

## Quick Start

`from apgard import ApgardClient`

# Initialize client
`client = ApgardClient(api_key="your-api-key")`

# Track user activity
```
status = client.take_a_break.activity(
    user_id="user_123",
    thread_id="conversation_456"
)
```

# Check if break is due
```
if status.break_due:
    print(status.message)  # Show break reminder to user
```

## Basic Usage

### 1. Initialize the Client

```
from apgard import ApgardClient

client = ApgardClient(
    api_key="your-api-key",
    base_url="https://api.apgardai.com"  # Optional, defaults to localhost
)
```

**Parameters:**
- `api_key` (required): Your API key from Apgard
- `base_url` (optional): API endpoint (default: `http://localhost:8000`)

### 2. Track User Activity

Call `activity()` whenever the user interacts with your chatbot:

```
status = client.take_a_break.activity(
    user_id="user_123",
    thread_id="conversation_456",  # Optional: tracks per-conversation
    metadata={"model": "gpt-4", "temperature": 0.7}  # Optional
)
```

# Response
# status.break_due: bool - whether break is due
# status.message: str - break reminder message
# status.thread_id: str - the thread ID


### 3. Handle Break Status

```
status = client.take_a_break.activity(user_id="user_123")

if status.break_due:
    # Display break reminder to user
    print(status.message)
    # Output: "Time to take a break! Reminder: this chatbot is AI-generated, not human."
    
    # Stop or limit chatbot interactions
    # You can implement your own logic here
else:
    # Continue normal chatbot operation
    print(f"User can continue for {status.minutes_until_break} more minutes")
```

## Advanced Usage

### Custom Break Duration

Set a custom break threshold (default: 180 minutes / 3 hours):


# 2-hour break threshold
```
client.take_a_break = TakeABreak(client, break_time_minutes=120)

status = client.take_a_break.activity(user_id="user_123")
```

### Per-User Custom Thresholds

Different users can have different break thresholds:

```
# User prefers breaks every 1.5 hours
break_tracker_1 = TakeABreak(client, break_time_minutes=90)
status1 = break_tracker_1.activity(user_id="user_1")

# Another user prefers breaks every 2 hours
break_tracker_2 = TakeABreak(client, break_time_minutes=120)
status2 = break_tracker_2.activity(user_id="user_2")
```

### Track by Conversation Thread

Track activity per conversation for granular insights:

```
# Same user, different conversations
status1 = client.take_a_break.activity(
    user_id="user_123",
    thread_id="conversation_abc"
)

status2 = client.take_a_break.activity(
    user_id="user_123",
    thread_id="conversation_xyz"
)
```

### Include Metadata

Attach custom metadata for analytics:

```
status = client.take_a_break.activity(
    user_id="user_123",
    thread_id="conversation_456",
    metadata={
        "user_age_group": "18-25",
        "device": "mobile",
        "language": "en",
        "session_type": "learning"
    }
)
```

## Best Practices

### 1. Call activity() at the Start of Each Interaction

```
# ✅ Good - check before processing
status = client.take_a_break.activity(user_id=user_id)
if status.break_due:
    return break_message

response = process_chat(message)
return response

# ❌ Bad - check after processing
response = process_chat(message)
client.take_a_break.activity(user_id=user_id)
```

## Response Structure

```
BreakStatus:
    break_due: bool              # Whether user should take a break
    message: Optional[str]       # Break reminder message to display
    thread_id: Optional[str]     # The conversation thread ID
```

## Troubleshooting

### "Invalid API key" Error

```
# Verify your API key is correct
client = ApgardClient(api_key="your-actual-api-key")
```

### Break Status Always False

- Verify `break_time_minutes` is set appropriately
- Check that `activity()` is being called regularly
- Ensure user IDs are consistent across calls

## Support

- Documentation: https://docs.apgardai.com
- Email: ariel@apgardai.com