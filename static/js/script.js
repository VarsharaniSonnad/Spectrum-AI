// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // Define the base URL for your Flask backend
    const FLASK_BACKEND_URL = 'http://127.0.0.1:5001'; // **IMPORTANT: CHANGE THIS if your Flask app runs elsewhere**

    // --- Get References to HTML Elements ---
    const phoneNumberInput = document.getElementById('phoneNumber');
    const startCallBtn = document.getElementById('startCallBtn');
    const endCallBtn = document.getElementById('endCallBtn'); // Get the new button
    const callStatusDiv = document.getElementById('callStatus');

    const chatConversationDiv = document.getElementById('chatConversation');
    const chatInput = document.getElementById('chatInput');
    const languageSelect = document.getElementById('languageSelect');
    const sendChatBtn = document.getElementById('sendChatBtn');

    // Voice elements
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    const listeningStatusDiv = document.getElementById('listeningStatus');
    const bodyElement = document.body; // To add/remove 'listening' class for CSS

    // --- State Variables ---
    let currentCallId = null; // Variable to store the active call ID

    // --- Web Speech API Setup ---
    // Get the browser's Speech Recognition and Synthesis interfaces
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const SpeechSynthesis = window.speechSynthesis;

    let recognition = null; // Holds the SpeechRecognition instance
    let isListening = false; // Tracks if the microphone is actively listening
    let isSpeaking = false; // Tracks if the browser is currently speaking

    // Check for SpeechRecognition compatibility
    if (!SpeechRecognition) {
        // If not supported, disable the voice input button and show a message
        if (voiceInputBtn) { // Check if the button exists in the HTML
            voiceInputBtn.disabled = true;
        }
        if (listeningStatusDiv) { // Check if the status div exists
            listeningStatusDiv.textContent = 'Speech input not supported in this browser.';
        }
        console.warn('Web Speech Recognition API not supported.');
    } else {
        // Create a new SpeechRecognition instance
        recognition = new SpeechRecognition();
        recognition.continuous = false; // Stop listening after a pause
        recognition.interimResults = false; // Only return final results

        // --- Speech Recognition Event Handlers ---
        recognition.onstart = function() {
            isListening = true;
            if (listeningStatusDiv) listeningStatusDiv.textContent = 'Listening... Speak now.';
            bodyElement.classList.add('listening'); // Add class for CSS styling
            if (voiceInputBtn) {
                voiceInputBtn.classList.add('btn-danger'); // Optional: Change button color to red
                voiceInputBtn.classList.remove('btn-outline-secondary');
            }
        };

        recognition.onresult = function(event) {
            // Get the transcribed text from the event
            const transcript = event.results[0][0].transcript;
            console.log('Speech recognized:', transcript);
            if (chatInput) chatInput.value = transcript; // Put transcript in the input field

            // Automatically send the message after speech is recognized
            // Timeout gives the user a moment to see the transcription if needed
            setTimeout(() => {
                 sendChatMessage();
            }, 100); // Small delay before sending
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            let errorMessage = `Error: ${event.error}`;
             // Provide more user-friendly messages for common errors
            if (event.error === 'not-allowed') {
                 errorMessage = 'Microphone permission denied. Please allow access.';
            } else if (event.error === 'no-speech') {
                 errorMessage = 'No speech detected. Please try speaking louder or clearer.';
            } else if (event.error === 'audio-capture') {
                 errorMessage = 'Error capturing audio. Check your microphone.';
            } else if (event.error === 'network') {
                 errorMessage = 'Network error during recognition.';
            }
            if (listeningStatusDiv) listeningStatusDiv.textContent = errorMessage;
        };

        recognition.onend = function() {
            isListening = false;
             // Clear status message unless it's displaying a persistent error
            if (listeningStatusDiv && !listeningStatusDiv.textContent.startsWith('Error:')) {
                 listeningStatusDiv.textContent = '';
            }
            bodyElement.classList.remove('listening'); // Remove CSS class
            if (voiceInputBtn) {
                voiceInputBtn.classList.remove('btn-danger'); // Revert button color
                voiceInputBtn.classList.add('btn-outline-secondary');
            }
        };

        // --- Voice Input Button Click Listener ---
        if (voiceInputBtn) { // Add listener only if button exists and API is supported
            voiceInputBtn.addEventListener('click', function() {
                if (isListening) {
                    recognition.stop(); // If listening, stop it
                } else {
                     // If not listening, start it.
                     // Before starting, cancel any ongoing speech synthesis.
                     if(SpeechSynthesis && SpeechSynthesis.speaking){
                        SpeechSynthesis.cancel();
                        isSpeaking = false; // Ensure flag is reset
                     }
                     // Set language for recognition (attempt to match selected chat language)
                     // Note: Recognition language support varies by browser/OS and may not match synthesis
                     if (languageSelect) recognition.lang = languageSelect.value; // Attempt to use selected language
                     else recognition.lang = 'en-US'; // Default to English if no language select

                     try {
                         recognition.start(); // Start listening
                     } catch (error) {
                         console.error("Recognition start error:", error);
                         if (listeningStatusDiv) listeningStatusDiv.textContent = 'Error starting microphone. Please try again.';
                         isListening = false; // Reset state
                         bodyElement.classList.remove('listening');
                         if (voiceInputBtn) {
                              voiceInputBtn.classList.remove('btn-danger');
                              voiceInputBtn.classList.add('btn-outline-secondary');
                         }
                     }
                }
            });
        }
    }

     // Check for SpeechSynthesis compatibility
    if (!SpeechSynthesis) {
        console.warn('Web Speech Synthesis API not supported.');
        // You might want to hide or disable elements related to voice output if not supported
    } else {
         // Optional: Preload voices - necessary for some browsers
         // Calling this once can help populate the voices list needed for setting specific voices later.
         SpeechSynthesis.getVoices();
         SpeechSynthesis.onvoiceschanged = function() {
             console.log("Browser voices updated.");
             // You could populate a voice selection dropdown here if needed
         };
    }


    // --- Helper function to speak text using browser's TTS ---
    function speakText(text, lang = 'en') {
        if (!SpeechSynthesis || isSpeaking) {
            // console.log("Speech synthesis not available or already speaking.");
            return;
        }

        // Stop any current speech before starting new one (optional, browser often queues)
        // SpeechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        // Set language - crucial for correct pronunciation
        utterance.lang = lang;

        // Optional: Set rate and pitch
        // utterance.rate = 1.0; // 0.1 to 10
        // utterance.pitch = 1.0; // 0 to 2

        // Optional: Select a specific voice
        // const voices = SpeechSynthesis.getVoices();
        // Find a voice that matches the language and is potentially a default or preferred voice.
        // Finding specific voices is inconsistent across browsers. Setting lang is often enough.
        // utterance.voice = voices.find(voice => voice.lang === lang && voice.name.includes('Google') || voice.default);

        utterance.onstart = function() {
            isSpeaking = true;
            console.log('AI speaking started...');
             // Optionally visually indicate speaking status (e.g., highlight AI message)
        };

        utterance.onend = function() {
            isSpeaking = false;
            console.log('AI speaking finished.');
             // Optionally remove speaking status indicator
        };

        utterance.onerror = function(event) {
            isSpeaking = false;
            console.error('Speech synthesis error:', event.error);
             // Handle errors, e.g., language not supported for speaking
        };

        try {
            SpeechSynthesis.speak(utterance);
        } catch (error) {
            console.error("SpeechSynthesis.speak error:", error);
            isSpeaking = false; // Ensure state is reset on error
        }
    }


    // --- Voice Call Functionality ---
    if (startCallBtn) { // Add listener only if button exists
        startCallBtn.addEventListener('click', async function() {
            const phoneNumber = phoneNumberInput ? phoneNumberInput.value.trim() : ''; // Check if input exists

            if (!phoneNumber) {
                displayCallStatus('Please enter a phone number.', 'danger');
                return;
            }

            displayCallStatus('Starting call...', 'info');
            startCallBtn.disabled = true;
            if (endCallBtn) endCallBtn.disabled = true; // Ensure End Call is disabled while starting

            try {
                // Fetch call targets the Flask backend's /start_call route
                const response = await fetch(`${FLASK_BACKEND_URL}/start_call`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ phone_number: phoneNumber }),
                });

                const result = await response.json();

                if (response.ok) {
                    currentCallId = result.call_id; // Store the call ID received from backend
                    displayCallStatus(`Call initiated! Call ID: ${currentCallId || 'N/A'}. Bland AI webhook will handle conversation.`, 'success');
                    if (endCallBtn) endCallBtn.disabled = false; // Enable the End Call button

                    // Clear phone number input after successful start?
                    // if (phoneNumberInput) phoneNumberInput.value = '';

                } else {
                    displayCallStatus(`Error starting call: ${result.error || 'Unknown error'}`, 'danger');
                    currentCallId = null; // Clear call ID on error or non-ok response
                }

            } catch (error) {
                console.error('Error starting call:', error);
                displayCallStatus('An unexpected error occurred while trying to start the call. Check console for details.', 'danger');
                currentCallId = null; // Clear call ID on error
            } finally {
                startCallBtn.disabled = false; // Re-enable Start Call button
            }
        });
    }


    // --- End Call Functionality ---
    if (endCallBtn) { // Add listener only if button exists
        endCallBtn.addEventListener('click', async function() {
            if (!currentCallId) {
                displayCallStatus('No active call to end.', 'warning');
                endCallBtn.disabled = true; // Should already be disabled, but good check
                return;
            }

            displayCallStatus(`Sending end call signal for call ${currentCallId}...`, 'info');
            endCallBtn.disabled = true; // Disable button while ending
            if (startCallBtn) startCallBtn.disabled = true; // Also disable start while ending

            try {
                // Fetch call targets the Flask backend's /end_call route
                const response = await fetch(`${FLASK_BACKEND_URL}/end_call`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ call_id: currentCallId }), // Send the stored call ID
                });

                const result = await response.json();

                if (response.ok) {
                    displayCallStatus(`Call ${currentCallId} end signal sent. Status: ${result.status}. Bland AI will confirm end via webhook.`, 'success');
                } else {
                    displayCallStatus(`Error ending call ${currentCallId}: ${result.error || 'Unknown error'}`, 'danger');
                }

            } catch (error) {
                console.error('Error ending call:', error);
                displayCallStatus(`An unexpected error occurred while trying to end call ${currentCallId}. Check console for details.`, 'danger');
            } finally {
                // Regardless of success/failure of the END API call,
                // the UI assumes the call is no longer manageable via this button
                currentCallId = null;
                endCallBtn.disabled = true;
                if (startCallBtn) startCallBtn.disabled = false; // Re-enable start call
            }
        });
    }


    // Helper function to display call status messages
    function displayCallStatus(message, type) {
        if (callStatusDiv) { // Check if the status div exists
            // Use Bootstrap alert styles
            callStatusDiv.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
        }
    }


    // --- Text/Voice Chat Functionality ---
    if (sendChatBtn) { // Add listener only if button exists
        sendChatBtn.addEventListener('click', async function() {
            await sendChatMessage();
        });
    }

    // Allow sending message with Enter key in chat input
    if (chatInput) { // Add listener only if input exists
        chatInput.addEventListener('keypress', async function(event) {
            if (event.key === 'Enter' && !event.shiftKey) { // Check for Enter key, allow Shift+Enter for new line
                event.preventDefault(); // Prevent default form submission/newline
                await sendChatMessage();
            }
        });
    }


    async function sendChatMessage() {
        const userMessage = chatInput ? chatInput.value.trim() : ''; // Check if input exists
        const targetLanguage = languageSelect ? languageSelect.value : 'en'; // Check if select exists

        if (!userMessage) {
            // Optionally add a visual cue that input is needed
            console.log("Chat input is empty.");
            return;
        }

        // Display user message immediately
        addMessageToChat('user', userMessage);
        if (chatInput) chatInput.value = ''; // Clear the input field

        // Disable input and buttons while waiting for AI response
        if (sendChatBtn) sendChatBtn.disabled = true;
        if (chatInput) chatInput.disabled = true;
        // Disable voice input button if it exists and API is supported
        if (voiceInputBtn && SpeechRecognition) voiceInputBtn.disabled = true;


        // Cancel any ongoing speech synthesis when user sends a new message
        if(SpeechSynthesis && SpeechSynthesis.speaking){
           SpeechSynthesis.cancel();
           isSpeaking = false; // Ensure flag is reset
        }


        try {
            // Fetch call targets the Flask backend's /chat route
            const response = await fetch(`${FLASK_BACKEND_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage, language: targetLanguage }),
            });

            const result = await response.json();

            if (response.ok) {
                addMessageToChat('ai', result.response); // Display AI response
                 // --- Speak the AI Response ---
                 if (SpeechSynthesis && result.response) { // Check if speech synth is available and response is not empty
                     speakText(result.response, result.language); // Use language returned by backend (or sent)
                 }
                 // -----------------------------
            } else {
                 addMessageToChat('ai', `Error: ${result.error || 'Could not get response'}`); // Display error message from backend
            }

        } catch (error) {
            console.error('Error sending chat message:', error);
            addMessageToChat('ai', 'An unexpected error occurred while fetching AI response. Check console for details.'); // Display generic error
        } finally {
             // Re-enable input and buttons
             if (sendChatBtn) sendChatBtn.disabled = false;
             if (chatInput) chatInput.disabled = false;
             // Re-enable voice input button if it's supported and exists
             if (voiceInputBtn && SpeechRecognition) voiceInputBtn.disabled = false;

             scrollToBottomOfChat(); // Scroll to show latest message
        }
    }

    // Helper function to add messages to the chat display
    function addMessageToChat(sender, text) {
        if (chatConversationDiv) { // Check if chat display area exists
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', sender + '-message');
            // Use textContent or createTextNode to prevent XSS
            messageElement.appendChild(document.createTextNode(text));
            chatConversationDiv.appendChild(messageElement);
            scrollToBottomOfChat();
        }
    }

    // Helper function to scroll chat to the bottom
    function scrollToBottomOfChat() {
         if (chatConversationDiv) { // Check if chat display area exists
             chatConversationDiv.scrollTop = chatConversationDiv.scrollHeight;
         }
    }

    // --- Initial Setup ---
    // Ensure voice input button is disabled if API is not supported on page load
    if (!SpeechRecognition && voiceInputBtn) {
        voiceInputBtn.disabled = true;
        if (listeningStatusDiv) listeningStatusDiv.textContent = 'Speech input not supported.';
    }
     // Ensure end call button is disabled initially
     if(endCallBtn) {
          endCallBtn.disabled = true;
     }
});