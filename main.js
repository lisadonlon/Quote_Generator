// Wait for the entire HTML document to load before running the script.
document.addEventListener('DOMContentLoaded', () => {
    // Get references to the HTML elements we'll be interacting with.
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Function to handle sending a message.
    const sendMessage = async () => {
        // Get the user's message and trim any whitespace.
        const messageText = userInput.value.trim();

        // If there's no message, do nothing.
        if (!messageText) return;

        // Display the user's message on the screen.
        addMessage(messageText, 'user-message');
        // Clear the input box.
        userInput.value = '';

        try {
            // Send the user's message to the chat endpoint.
            const chatResponse = await fetch('http://127.0.0.1:5000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            const chatData = await chatResponse.json();
            const botResponse = chatData.response;

            // ** NEW LOGIC STARTS HERE **
            // Check if the AI has signaled that the draft is ready.
            if (botResponse.startsWith('[DRAFT_READY]')) {
                // Extract the actual email content, removing the marker.
                const emailContent = botResponse.replace('[DRAFT_READY]', '').trim();
                
                addMessage('OK, creating that draft in Gmail for you now...', 'bot-message');
                
                // Send the final content to the new /create_draft endpoint.
                const draftResponse = await fetch('http://127.0.0.1:5000/create_draft', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: emailContent }),
                });

                const draftData = await draftResponse.json();
                // Display the final success or error message from the draft creation.
                addMessage(draftData.message, 'bot-message');

            } else {
                // If it's a normal conversational message, just display it.
                addMessage(botResponse, 'bot-message');
            }
            // ** NEW LOGIC ENDS HERE **

        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, something went wrong. Please check the server.', 'bot-message');
        }
    };

    // Function to add a new message bubble to the chat window.
    const addMessage = (text, className) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        
        const bubbleDiv = document.createElement('div');
        // Replace newline characters with <br> tags for proper display.
        bubbleDiv.innerHTML = text.replace(/\n/g, '<br>');

        messageDiv.appendChild(bubbleDiv);
        chatWindow.appendChild(messageDiv);

        // Automatically scroll to the latest message.
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };

    // Add event listeners for sending the message.
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (event) => {
        // Allow sending by pressing the "Enter" key.
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
});