import React, { useState, useEffect, useRef } from 'react';
// import { sendMessageToChat } from '../services/api';
import { Message, ChatResponse, Source } from '../util/types';
import { v4 as uuidv4 } from 'uuid';
import '../styles.css';

interface ChatInterfaceProps {
    selectedSourceId: string;
    sendMessageFunction: (query: string, sources: string[]) => Promise<ChatResponse>;
}

const ChatInterface = ({ selectedSourceId, sendMessageFunction }: ChatInterfaceProps) => {
    const [messages, setMessages] = useState<Message[]>([]);    // chat history
    const [inputMessage, setInputMessage] = useState<string>('');    // user input
    const [loading, setLoading] = useState<boolean>(false);    // loading indicator
    const [error, setError] = useState<string | null>(null);    // error message

    // For auto-scrolling
    const messagesEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!inputMessage.trim()) return;

        const userMessage: Message = {
            id: uuidv4(),
            sender: 'user',
            text: inputMessage,
            timestamp: new Date().toISOString(),
        };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setInputMessage('');
        setLoading(true);
        setError(null);

        try {
            const response = await sendMessageFunction(
                inputMessage,
                selectedSourceId ? [selectedSourceId] : []
            );

            const botMessage: Message = {
                id: uuidv4(),
                sender: 'bot',
                text: response.answer,
                timestamp: new Date().toISOString(),
            };
            setMessages((prevMessages) => [...prevMessages, botMessage]);
        } catch (err: any) {
            console.error('Error sending message:', err);
            const errorMessage: Message = {
                id: uuidv4(),
                sender: 'bot',
                text: `Error: ${err.message || 'Failed to get a response.'}`,
                timestamp: new Date().toISOString(),
            };
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
            setError(err.message || 'Failed to get a response.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-interface">
            <div className="messages-display">
                {messages.length === 0 ? (
                    <p className="no-messages">
                        ... ابدأ بالتحدث مع المساعد الذكي، اسأل عن موضوع في كتابك / بياناتك 
                    </p>
                ) : (
                    messages.map((msg) => (
                        <div key={msg.id} className={`message ${msg.sender}`}>
                            <div className="message-sender">{msg.sender === 'user' ? 'You' : 'Bot'}</div>
                            <div className="message-text">{msg.text}</div>
                            <div className="message-timestamp">
                                {new Date(msg.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {loading && <p className="loading-message">Thinking...</p>}
            {error && <p className="error-message">{error}</p>}

            <form onSubmit={handleSendMessage} className="chat-input-form">
                <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder={"... اطرح سؤال"}
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !inputMessage.trim()}>
                    أرسل
                </button>
            </form>
        </div>
    );
};

export default ChatInterface;