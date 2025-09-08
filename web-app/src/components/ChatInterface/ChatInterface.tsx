import React, { useState, useEffect, useRef } from "react";
import { Message, ChatResponse, QueryRequest } from "../../util/types";
import { v4 as uuidv4 } from "uuid";
import "./chat.css";

interface ChatInterfaceProps {
    selectedSourceId: string;
    sendMessageFunction: (queryRequest: QueryRequest) => Promise<ChatResponse>;
}

const ChatInterface = ({ selectedSourceId, sendMessageFunction }: ChatInterfaceProps) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputMessage, setInputMessage] = useState<string>("");
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Autoscroll to newest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Autogrow textarea height
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [inputMessage]);

    const formatText = (text: string) => {
        return text.replace(/\n/g, "<br />");
    };

    const handleDownload = () => {
    if (messages.length === 0) return;

    const textContent = messages
        .map(
        (msg) =>
            `${msg.sender === "user" ? "انت" : "المساعد"} [${new Date(
            msg.timestamp
            ).toLocaleString()}]:\n${msg.text}\n`
        )
        .join("\n--------------------\n\n");

    const blob = new Blob([textContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `conversation_${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
};


    const handleSendMessage = async () => {
        if (!inputMessage.trim()) return;

        const userMessage: Message = {
            id: uuidv4(),
            sender: "user",
            text: inputMessage,
            timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setInputMessage("");
        setLoading(true);
        setError(null);

        try {
            const response = await sendMessageFunction({
                query: inputMessage,
                sources: selectedSourceId ? [selectedSourceId] : [],
            } as QueryRequest);
            const botMessage: Message = {
                id: uuidv4(),
                sender: "bot",
                text: response.answer,
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (err: any) {
            console.error("Error sending message:", err);
            const errorMessage: Message = {
                id: uuidv4(),
                sender: "bot",
                text: `Error: ${err.message || "Failed to get a response."}`,
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
            setError(err.message || "Failed to get a response.");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <button
                    onClick={handleDownload}
                    disabled={messages.length === 0}
                    className="download-btn"
                >
                    <img src="/assets/download.png" alt="تحميل" className="download-icon" />
                </button>
            </div>

            <div className="messages-display">
                {messages.length === 0 ? (
                    <p className="no-messages">
                        ... ابدأ بالتحدث مع المساعد الذكي، اسأل عن موضوع في كتابك /
                        بياناتك
                    </p>
                ) : (
                    messages.map((msg) => (
                        <div key={msg.id} className={`message ${msg.sender}`}>
                            <div className="message-sender">
                                {msg.sender === "user" ? "انت" : "المساعد"}
                            </div>

                            {msg.sender === "bot" ? (
                                <div
                                    className="message-text"
                                    dangerouslySetInnerHTML={{ __html: formatText(msg.text) }}
                                />
                            ) : (
                                <div className="message-text">{msg.text}</div>
                            )}

                            <div className="message-timestamp">
                                {new Date(msg.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {loading && <p className="loading-message">جار التفكير...</p>}
            {error && <p className="error-message">{error}</p>}

            <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="chat-input-form">
                <textarea
                    ref={textareaRef}
                    rows={1}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={"... اطرح سؤال"}
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