"""
FastAPI entrypoint.

No auth, no DB, no background jobs—just a minimal /chat endpoint.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from config import load_settings
from npc_agent import NPCAgent


app = FastAPI(title="AI Co-Worker Engine (Prototype)", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    """Serve the chat UI."""
    return _get_chat_html()


def _get_chat_html() -> str:
    """Return the chat interface HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Co-Worker Engine - Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chat-header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .chat-header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 16px;
            display: flex;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 12px;
            word-wrap: break-word;
            line-height: 1.5;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        .message-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 4px;
            opacity: 0.7;
        }
        
        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .chat-input-wrapper {
            display: flex;
            gap: 12px;
        }
        
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        
        #messageInput:focus {
            border-color: #667eea;
        }
        
        #sendButton {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 24px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        #sendButton:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        #sendButton:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .loading {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .state-indicator {
            font-size: 11px;
            color: #666;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #e0e0e0;
        }
        
        .state-indicator span {
            margin-right: 12px;
        }
        
        .error-message {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            border-left: 4px solid #c33;
        }
        
        .error-message.quota-error {
            background: #fff3cd;
            color: #856404;
            border-left-color: #ffc107;
        }
        
        .error-message.quota-error a {
            color: #856404;
            text-decoration: underline;
        }
        
        .error-message.quota-error strong {
            display: block;
            margin-bottom: 8px;
            font-size: 16px;
        }
        
        .error-message.quota-error small {
            display: block;
            margin-top: 8px;
            opacity: 0.8;
        }
        
        .empty-state {
            text-align: center;
            color: #999;
            padding: 40px 20px;
        }
        
        .empty-state svg {
            width: 64px;
            height: 64px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 AI Co-Worker Engine</h1>
            <p>Chat with Gucci Group CEO</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <p>Start a conversation with the CEO...</p>
            </div>
        </div>
        
        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <input 
                    type="text" 
                    id="messageInput" 
                    placeholder="Type your message..." 
                    autocomplete="off"
                >
                <button id="sendButton">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        let conversationHistory = [];
        
        function addMessage(role, content, state = null) {
            // Remove empty state if exists
            const emptyState = chatMessages.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            const labelDiv = document.createElement('div');
            labelDiv.className = 'message-label';
            labelDiv.textContent = role === 'user' ? 'You' : 'CEO';
            
            const textDiv = document.createElement('div');
            textDiv.textContent = content;
            
            contentDiv.appendChild(labelDiv);
            contentDiv.appendChild(textDiv);
            
            if (state && role === 'assistant') {
                const stateDiv = document.createElement('div');
                stateDiv.className = 'state-indicator';
                stateDiv.innerHTML = `
                    <span>Trust: ${(state.trust_score * 100).toFixed(0)}%</span>
                    <span>Frustration: ${(state.frustration_score * 100).toFixed(0)}%</span>
                    <span>Alignment: ${(state.alignment_score * 100).toFixed(0)}%</span>
                `;
                contentDiv.appendChild(stateDiv);
            }
            
            messageDiv.appendChild(contentDiv);
            chatMessages.appendChild(messageDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showError(message, isQuotaError = false) {
            const errorDiv = document.createElement('div');
            errorDiv.className = isQuotaError ? 'error-message quota-error' : 'error-message';
            
            if (isQuotaError) {
                errorDiv.innerHTML = `
                    <strong>⚠️ API Quota Exceeded</strong><br>
                    ${message}<br>
                    <small>💡 Tip: Check your quota at <a href="https://ai.dev/rate-limit" target="_blank">ai.dev/rate-limit</a> or try again later.</small>
                `;
            } else {
                errorDiv.textContent = `Error: ${message}`;
            }
            
            chatMessages.appendChild(errorDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message to UI
            addMessage('user', message);
            messageInput.value = '';
            
            // Disable input
            messageInput.disabled = true;
            sendButton.disabled = true;
            sendButton.innerHTML = '<span class="loading"></span> Sending...';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        persona_id: 'gucci_ceo',
                        message: message
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    const isQuotaError = response.status === 429;
                    throw { message: error.detail || 'Failed to get response', isQuotaError };
                }
                
                const data = await response.json();
                
                // Add assistant response to UI
                addMessage('assistant', data.assistant_message, data.state);
                
            } catch (error) {
                if (error.isQuotaError !== undefined) {
                    showError(error.message, error.isQuotaError);
                } else {
                    showError(error.message || String(error));
                }
            } finally {
                // Re-enable input
                messageInput.disabled = false;
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                messageInput.focus();
            }
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
    """


class ChatRequest(BaseModel):
    persona_id: str = Field(default="gucci_ceo", description="Persona identifier")
    message: str = Field(..., min_length=1, description="User message")


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    try:
        settings = load_settings()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        agent = NPCAgent(persona_id=req.persona_id, settings=settings)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        return agent.respond(req.message)
    except RuntimeError as e:
        # Handle API errors (quota, network, etc.)
        error_msg = str(e)
        if "quota" in error_msg.lower():
            raise HTTPException(status_code=429, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

