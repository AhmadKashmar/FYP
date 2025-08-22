import React, { useState, useEffect, useRef } from "react";
import { Message, ChatResponse, QueryRequest } from "../util/types";
import { v4 as uuidv4 } from "uuid";
import "../styles.css";

interface ChatInterfaceProps {
	selectedSourceId: string;
	sendMessageFunction: (queryRequest: QueryRequest) => Promise<ChatResponse>;
}

const ChatInterface = ({ selectedSourceId, sendMessageFunction }: ChatInterfaceProps) => {
	const [messages, setMessages] = useState<Message[]>([]);
	const [inputMessage, setInputMessage] = useState<string>("");
	const [loading, setLoading] = useState<boolean>(false);
	const [error, setError] = useState<string | null>(null);

	// autoscroll to newest message
	const messagesEndRef = useRef<HTMLDivElement>(null);
	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages]);

	const handleSendMessage = async (event: React.FormEvent) => {
		event.preventDefault();
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

	return (
		<div className="chat-interface">
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
									dangerouslySetInnerHTML={{ __html: msg.text }}
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
