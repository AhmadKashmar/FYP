import { useState } from "react";
import { Document } from "../util/types";
import ChatInterface from "../components/ChatInterface";
import "../styles.css";


export const Home = () => {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    return (
        <div className="App">
            <header className="App-header">
                <img src={"/assets/logo.png"} alt="logo" />
                <h1>GPT كتاب </h1>
            </header>
            <main className="App-main">
                <div className="sidebar">
                    <h2>Placeholder</h2>
                </div>
                <div className="chat-section">
                    <h2>تحدث مع المساعد</h2>
                    <ChatInterface/>
                </div>
            </main>
        </div>
    );
}