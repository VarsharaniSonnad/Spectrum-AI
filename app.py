from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import json  # Import the json module


app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# --- Environment Variables ---
# It's highly recommended to load these from actual environment variables in production
# The values provided here are defaults if environment variables are not set.

# IMPORTANT: Updated with the new Bland AI API key you provided.
# Replace this with your actual API key, or set the BLAND_AI_API_KEY env var.
BLAND_AI_API_KEY = os.getenv("BLAND_AI_API_KEY", "org_92a47865624f8abe7aa043df2e9969b94eb067d5fe76d26a2ad546d381c83bbdb7e81290970abb5267bb69")
BLAND_AI_BASE_URL = os.getenv("BLAND_AI_BASE_URL", "https://api.bland.ai/v1")

# IMPORTANT: Replace "AIzaSyDTSgDLB3zVg4mBjfKHvIPk4kh3CXoaYoI" with your actual Gemini API key, or set the GEMINI_API_KEY env var.
# The value you provided (AIzaSy...) is already set as the default here.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDTSgDLB3zVg4mBjfKHvIPk4kh3CXoaYoI")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# IMPORTANT: Using the specific Flow UUID you provided.
BLAND_AI_FLOW_UUID = os.getenv("BLAND_AI_FLOW_UUID", "0125bc9d-c304-4eb6-98c2-650ecd39ee77")

# IMPORTANT: Updated with the Zapier webhook URL you provided as the default.
# Replace this with your actual publicly accessible webhook URL or set the BLAND_AI_WEBHOOK_URL env var.
DEFAULT_WEBHOOK_URL = "https://hooks.zapier.com/hooks/catch/22924406/272kco7/"


# --- Helper Functions ---

def get_gemini_response(prompt):
    """
    Sends a text prompt to the Gemini API and returns the generated response.

    Args:
        prompt (str): The text prompt to send to Gemini.

    Returns:
        str: The generated text response from Gemini, or None on error.
    """
    # Check if GEMINI_API_KEY is the placeholder default
    if GEMINI_API_KEY == "AIzaSyDTSgDLB3zVg4mBjfKHvIPk4kh3CXoaYoI":
         print("ERROR: GEMINI_API_KEY is the default placeholder value. Replace it with your actual key.")
         # In a real app, you might want to return a more specific error or raise an exception
         # For now, we'll return an error message that Gemini couldn't be called.
         # Continue with the API call attempt anyway, it will likely fail if the key is invalid.

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [  # Add safety settings. From Gemini API documentation
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        gemini_response = response.json()
        # Safely access the nested structure
        ai_reply = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not ai_reply:
             print(f"Gemini returned empty response. Full response: {gemini_response}")
             return "Could not generate a response." # Return a default if empty or malformed

        return ai_reply
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding Gemini response: {e}.  Response text: {response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in get_gemini_response: {e}")
        return None


# UPDATED: Added required 'task' parameter and changed 'to' to 'phone_number'
def start_bland_call(phone_number, voice="June", record=True, language="en", task="AI Receptionist Inquiry"): # Added 'task' with a default value
    """Initiates a voice call using the Bland AI API."""
    # Check if BLAND_AI_API_KEY is the placeholder default (updated with the new key)
    # This check triggers if the value is *exactly* that placeholder string.
    # You MUST replace that string with your actual key from the Bland AI dashboard.
    if BLAND_AI_API_KEY == "org_92a47865624f8abe7aa043df2e9969b94eb067d5fe76d26a2ad546d381c83bbdb7e81290970abb5267bb69":
         print("WARNING: BLAND_AI_API_KEY is the default placeholder value. Replace it with your actual key.")
         # In a real app, you might want to raise an exception here instead of just printing a warning
         # raise Exception("Bland AI API key is the default placeholder value. Replace it with your actual key.")


    # Check if BLAND_AI_FLOW_UUID is still the *original* placeholder
    if BLAND_AI_FLOW_UUID == "YOUR_BLAND_AI_FLOW_UUID":
         print("WARNING: Bland AI Flow UUID is not set. Call might fail or use a default flow.")


    # Check for webhook URL placeholder default and validate HTTPS
    webhook_url = os.getenv("BLAND_AI_WEBHOOK_URL", DEFAULT_WEBHOOK_URL) # Use the new default

    # The check for the specific 'YOUR_WEBHOOK_URL' string is no longer strictly needed here
    # as we have a default that starts with https://, but we still enforce HTTPS.
    if not webhook_url.startswith("https://"):
         print(f"\n!!!!!!!!!! ERROR: Bland AI Webhook URL must start with https://. Current URL: {webhook_url} !!!!!!!!!\n")
         print("!!!!!!!!!! Configure BLAND_AI_WEBHOOK_URL environment variable or replace the default in app.py with an HTTPS URL. !!!!!!!!!\n")
         raise Exception(f"Bland AI Webhook URL must start with https://. Current URL: {webhook_url}")

    if webhook_url == DEFAULT_WEBHOOK_URL:
         print(f"\n!!!!!!!!!! WARNING: Bland AI Webhook URL is using the default value: {DEFAULT_WEBHOOK_URL}")
         print("Replace this with YOUR publicly accessible webhook URL if you aren't using this specific Zapier hook.")
         print("Bland AI webhooks (for transcription, call ended, etc.) will NOT work correctly unless this is replaced with YOUR endpoint.")
         print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")


    headers = {
        "Authorization": f"Bearer {BLAND_AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        # Changed "to" to "phone_number" to match Bland AI error and JS example
        "phone_number": phone_number,
        "flow_uuid": BLAND_AI_FLOW_UUID, # Use the constant here
        "from": os.getenv("BLAND_AI_FROM_NUMBER"), # Optional: Specify a 'from' number if needed
        "wait_for_greeting": True, # Recommended: Wait for the person to speak (JS example had false)
        "reduce_latency": True, # Recommended: Faster responses (not in JS example)
        "webhook": webhook_url, # Use the validated webhook URL

        # Added the required 'task' parameter
        "task": task,

        # Added parameters from the JS example
        "voice": voice,      # e.g., "June", "Sarah", etc.
        "record": record,    # True or False
        "language": language,# e.g., "en", "es", etc. This affects transcription and potentially TTS in Bland AI

        # Other parameters from the JS example you might add later if needed:
        # "answered_by_enabled": True,
        # "noise_cancellation": False,
        # "interruption_threshold": 100,
        # "block_interruptions": False,
        # "max_duration": 12, # Max duration in seconds
        # "model": "base", # Often handled by Flow UUID
        # "background_track": "none", # URL or 'none'
        # "voicemail_action": "hangup" # or "continue"
    }


    try:
        print(f"Attempting to start call to {phone_number} using Flow UUID: {BLAND_AI_FLOW_UUID}...")
        # Log relevant parameters being sent
        print(f"Call parameters: Task='{task}', Voice='{voice}', Record={record}, Language='{language}', Webhook='{payload['webhook']}'")
        response = requests.post(f"{BLAND_AI_BASE_URL}/calls", headers=headers, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        call_info = response.json()
        print(f"Call initiated successfully: {call_info}")
        return call_info
    except requests.exceptions.RequestException as e:
        # More detailed error logging
        if response is not None:
             print(f"Bland AI start_call error: Status {response.status_code}, Response: {response.text}")
             # Attempt to parse JSON error from Bland AI
             try:
                 error_data = response.json()
                 # Check if Bland AI returned a list of errors under the 'error' key (as per your traceback)
                 if 'error' in error_data and isinstance(error_data['error'], list):
                      error_list_str = json.dumps(error_data['error'])
                      raise Exception(f"Error starting Bland AI call: Status {response.status_code} - Invalid parameters. Error: {error_list_str}")
                 # Check for a single error message
                 elif 'message' in error_data:
                     raise Exception(f"Error starting Bland AI call: Status {response.status_code} - {error_data['message']}")
                 else:
                     # Fallback if the error structure is unexpected
                     raise Exception(f"Error starting Bland AI call: Status {response.status_code} - {response.text}")
             except json.JSONDecodeError:
                  # Handle cases where the response is not valid JSON
                  raise Exception(f"Error starting Bland AI call: Status {response.status_code} - Non-JSON response: {response.text[:100]}...")
        else:
             # Handle request failures that don't even get a response
             print(f"Bland AI start_call request failed: {e}")
             raise Exception(f"Error starting Bland AI call: {e}")
    except Exception as e:
         print(f"An unexpected error occurred in start_bland_call: {e}")
         raise Exception(f"An unexpected error occurred: {e}")


def send_text_to_bland(call_id, text):
    """Sends text to be spoken in an ongoing Bland AI call."""
    # Check if BLAND_AI_API_KEY is the placeholder default (updated with the new key)
    if BLAND_AI_API_KEY == "org_92a47865624f8abe7aa043df2e9969b94eb067d5fe76d26a2ad546d381c83bbdb7e81290970abb5267bb69":
         print("WARNING: BLAND_AI_API_KEY is the default placeholder value. Cannot send text to Bland AI.")
         return # Exit the function early

    headers = {
        "Authorization": f"Bearer {BLAND_AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        # Add TTS options if needed, e.g., voice_id, speed, reduce_latency
        "reduce_latency": True # Example for faster responses
    }
    try:
        response = requests.post(f"{BLAND_AI_BASE_URL}/calls/{call_id}/speak", headers=headers, json=payload)
        response.raise_for_status()
        print(f"Sent text to Bland AI for call {call_id}: {text[:50]}...") # Log first 50 chars
    except requests.exceptions.RequestException as e:
        # More detailed error logging
        if response is not None:
             print(f"Bland AI send_text_to_bland error for call {call_id}: Status {response.status_code}, Response: {response.text}")
        else:
             print(f"Bland AI send_text_to_bland request failed for call {call_id}: {e}")
        # Consider whether to raise the error or handle it more gracefully


# --- Flask Routes ---
@app.route('/')
def home():
    """Renders the homepage (home.html)."""
    return render_template("home.html")

@app.route('/index.html')
def index_html():
    """Renders the chat interface."""
    return render_template("index.html")



@app.route('/start_call', methods=['POST'])
def start_call_route():
    """
    Initiates a voice call using Bland AI.
    Expects a JSON payload with the 'phone_number'.
    The frontend does not currently send other parameters like voice or record,
    so defaults from start_bland_call will be used.
    """
    data = request.get_json()
    phone_number = data.get("phone_number")
    # Optional: You could pass voice, record, language from frontend if your UI allows
    # voice = data.get("voice", data.get("voice", "June")) # Example if frontend sends voice
    # record = data.get("record", data.get("record", True)) # Example if frontend sends record
    # language = data.get("language", data.get("language", "en")) # Example if frontend sends language
    # task = data.get("task", "AI Receptionist Inquiry") # Example if frontend sends task

    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400
    try:
        # Call start_bland_call with the phone number.
        # Optional: Pass other parameters if you got them from frontend.
        call_info = start_bland_call(phone_number)
        # Bland AI's /calls endpoint returns call_id on success
        if call_info and 'call_id' in call_info:
             return jsonify(call_info), 200
        else:
             # This case might occur if start_bland_call didn't raise an exception but returned unexpected data
             print(f"start_bland_call returned unexpected data: {call_info}")
             return jsonify({"error": "Failed to get call ID from Bland AI response"}), 500

    except Exception as e:
        print(f"Failed to start call: {e}") # Log the error server-side
        # Return the error message from the raised exception
        return jsonify({"error": str(e)}), 500


# ROUTE FOR ENDING CALLS
@app.route('/end_call', methods=['POST'])
def end_call_route():
    """
    Ends an ongoing voice call using Bland AI.
    Expects a JSON payload with the 'call_id'.
    """
    # Check if BLAND_AI_API_KEY is the placeholder default (updated with the new key)
    if BLAND_AI_API_KEY == "org_92a47865624f8abe7aa043df2e9969b94eb067d5fe76d26a2ad546d381c83bbdb7e81290970abb5267bb69":
         return jsonify({"error": "Bland AI API key is the default placeholder value. Cannot end call."}), 500 # Cannot end call without correct key

    data = request.get_json()
    call_id = data.get("call_id")
    if not call_id:
        return jsonify({"error": "Call ID is required"}), 400

    headers = {
        "Authorization": f"Bearer {BLAND_AI_API_KEY}",
    }

    try:
        print(f"Attempting to send end call request for call_id: {call_id}...")
        # Bland AI documentation specifies DELETE for ending a call
        response = requests.delete(f"{BLAND_AI_BASE_URL}/calls/{call_id}", headers=headers)

        # Bland AI's DELETE /calls/{call_id} usually returns 200 OK on success
        if response.status_code == 200:
             print(f"Successfully sent end call request for call_id: {call_id}")
             return jsonify({"status": "success", "message": f"Call {call_id} end signal sent."}), 200
        else:
             # Attempt to get error from response body if available
             error_message = f"Bland AI API error ending call {call_id}: Status {response.status_code}"
             try:
                 error_data = response.json()
                 if 'message' in error_data:
                     error_message += f" - {error_data['message']}"
                 elif 'error' in error_data:
                      # If there's a list of errors, join them
                      if isinstance(error_data['error'], list):
                           error_message += f" - Errors: {', '.join(str(e) for e in error_data['error'])}"
                      else:
                           error_message += f" - Error: {error_data['error']}"

             except json.JSONDecodeError:
                  error_message += f" - Response: {response.text[:100]}..." # Log part of response if not JSON

             print(error_message) # Log the detailed error on the server
             # Return the actual status code from Bland AI if it's an error status
             return jsonify({"error": error_message}), response.status_code if response.status_code >= 400 else 500

    except requests.exceptions.RequestException as e:
        print(f"Request error ending call {call_id}: {e}")
        return jsonify({"error": f"Request error ending call: {e}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred in end_call_route for call {call_id}: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@app.route('/bland_ai_webhook', methods=['POST'])
def bland_ai_webhook_route():
    """
    Handles webhooks from Bland AI, processing call events and transcriptions.
    """
    try:
        data = request.get_json()
        # Log the entire webhook payload nicely for debugging
        print("Bland AI Webhook Data:", json.dumps(data, indent=2))

        event_type = data.get("event")
        call_id = data.get("call_id") # Call ID is common to most events

        if event_type == "transcription":
            user_speech = data.get("transcription")
            if call_id and user_speech:
                print(f"Received transcription for call {call_id}: {user_speech}")
                # Optional: Add logic here to detect intent like ending the call
                # if "end the call" in user_speech.lower():
                #    print(f"Detected end call intent from user on call {call_id}")
                #    # You might trigger call ending logic here, perhaps by making a DELETE request to Bland AI
                #    # Note: This requires careful design of your Bland AI flow and state management
                #    # For now, we just process the transcription.
                #    # return jsonify({"status": "acknowledged and ending call"}) # Respond to webhook quickly if you handle ending here

                ai_response_text = get_gemini_response(user_speech)  # Get response from Gemini
                if ai_response_text is not None and ai_response_text.strip(): # Check for None and empty string
                    send_text_to_bland(call_id, ai_response_text)
                else:
                    print(f"Failed to get valid response from Gemini for call_id: {call_id}. Cannot send text back.")

            else:
                print("Missing call_id or transcription in Bland AI webhook data.")

        elif event_type == "call.ended":
            summary = data.get("summary") # Bland AI often includes a summary here
            direction = data.get("direction")
            duration = data.get("duration")
            cost = data.get("cost")
            error = data.get("error") # Includes errors like 'failed_to_connect'

            print(f"Call ended: {call_id}")
            print(f"  Direction: {direction}")
            print(f"  Duration: {duration} seconds")
            print(f"  Cost: {cost}")
            if error:
                 print(f"  Error during call: {error}")
            if summary:
                 print(f"  Summary: {summary}")

            # Add logic to update call status in your database, process summary, etc.

        elif event_type == "call.initiated":
            to_number = data.get("to")
            from_number = data.get("from") # If applicable
            print(f"Call initiated: {call_id} to {to_number}")

        elif event_type == "speak.started":
            text = data.get("text")
            print(f"Speak started on call {call_id} with text (first ~50 chars): {text[:50]}...")

        elif event_type == "speak.ended":
            text = data.get("text")
            print(f"Speak ended on call {call_id} with text (first ~50 chars): {text[:50]}...")

        elif event_type == "error":
            code = data.get("code")
            message = data.get("message")
            print(f"Bland AI Error Webhook for call {call_id}: Code {code}, Message: {message}")
            # Implement specific handling based on error codes (e.g., billing issue, invalid number)

        # Handle other Bland AI events as needed. The Bland AI documentation will list the events.
        # Example: "transfer_initiated", "digits_gathered" etc.

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"An unexpected error occurred in bland_ai_webhook_route: {e}")
        # It's important to return a 200 OK even on internal errors
        # so Bland AI doesn't keep retrying the webhook.
        # Log the error server-side and return success to Bland AI.
        return jsonify({"status": "error", "message": "Internal server error processing webhook"}), 200


@app.route('/chat', methods=['POST'])
def chat_api():
    """
    Handles text-based chat interactions. Receives a message from the frontend,
    says it to Gemini, and returns the response.
    """
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        target_language = data.get("language", "en")

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # UPDATED: Improve the prompt to encourage response in the target language
        # Explicitly state the desired output language requirement strongly.
        prompt = (
            f"User message: '{user_message}'. "
            f"As an AI receptionist, respond ONLY in {target_language}. "
            f"Ensure your entire response is in {target_language}."
        )

        print(f"Sending chat prompt to Gemini (target language: {target_language}): {prompt}") # Log prompt being sent

        ai_reply = get_gemini_response(prompt)  # Get response from Gemini

        if ai_reply is not None and ai_reply.strip(): # Check explicitly for None and empty string
            # Even though Gemini might sometimes fail the language instruction,
            # we still return the response it gave and the requested target language
            # so the frontend can attempt to speak it in that language.
            return jsonify({"response": ai_reply, "language": target_language}), 200
        else:
            # get_gemini_response already prints the error
            return jsonify({"error": "Failed to get response from AI"}), 500

    except Exception as e:
        print(f"An unexpected error occurred in chat route: {e}") # Log the error server-side
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # IMPORTANT: Check placeholders before running, especially for production
    print("\n--- Checking Configuration ---")
    # Check for the API key default placeholder values (updated to the new key)
    if BLAND_AI_API_KEY == "org_92a47865624f8abe7aa043df2e9969b94eb067d5fe76d26a2ad546d381c83bbdb7e81290970abb5267bb69":
         print("WARNING: BLAND_AI_API_KEY is the default placeholder value. Replace it with your actual key from Bland AI dashboard.")
    if GEMINI_API_KEY == "AIzaSyDTSgDLB3zVg4mBjfKHvIPk4kh3CXoaYoI":
         print("WARNING: GEMINI_API_KEY is the default placeholder value. Replace it with your actual key from Google Cloud Console/AI Studio.")
    # The Flow UUID is now set, so the check for the OLD placeholder is removed
    # if BLAND_AI_FLOW_UUID == "YOUR_BLAND_AI_FLOW_UUID":
    #      print("WARNING: BLAND_AI_FLOW_UUID is a placeholder.")

    # Check for the webhook URL default
    webhook_url_configured = os.getenv("BLAND_AI_WEBHOOK_URL", DEFAULT_WEBHOOK_URL)
    if webhook_url_configured == DEFAULT_WEBHOOK_URL: # Check against the new default
         print(f"WARNING: BLAND_AI_WEBHOOK_URL is using the default value: {DEFAULT_WEBHOOK_URL}")
         print("Replace this with YOUR publicly accessible webhook URL if you aren't using this specific Zapier hook.")
    # The check for https:// is done within start_bland_call and raises an exception there.
    # This check here is just a warning about the default value itself.


    print("------------------------------\n")


    # Make sure your static and templates folders are correctly located relative to this script,
    # or update the Flask app definition if needed.
    app.run(host='0.0.0.0', port=5001, debug=True)