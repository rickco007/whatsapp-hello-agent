from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# These come from Railway environment variables (we'll set them soon)
VERIFY_TOKEN    = os.environ.get("VERIFY_TOKEN", "hello-agent-token")
WA_TOKEN        = os.environ.get("WA_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")


# ── Step 1: Meta calls this to verify your webhook is real ──────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return challenge, 200

    return "Forbidden", 403


# ── Step 2: Meta calls this every time someone messages you ─────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        # Ignore non-message events (delivery receipts, etc.)
        if "messages" not in value:
            return jsonify({"status": "ok"}), 200

        message     = value["messages"][0]
        from_number = message["from"]            # sender's WhatsApp number
        user_text   = message["text"]["body"]    # what they typed

        print(f"📩 Message from {from_number}: {user_text}")

        # Reply — for now just say hello back
        reply = "Hello! 👋 I'm your AI agent. I'm alive and listening!"
        send_whatsapp_message(from_number, reply)

    except Exception as e:
        print(f"Error: {e}")

    # Always return 200 so Meta doesn't retry
    return jsonify({"status": "ok"}), 200


# ── Helper: send a WhatsApp message ─────────────────────────────────────────
def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"📤 Sent reply: {response.status_code}")


# ── Start the server ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
