export interface Document {
    id: string;
    filename: string;
    // Add other fields if your backend returns them (e.g., upload_date)
}

export interface Message {
    id: string; // Unique ID for each message
    sender: 'user' | 'bot';
    text: string;
    timestamp: string; // ISO string or similar
}

export interface ChatResponse {
    answer: string;
    context_used: string[];
}