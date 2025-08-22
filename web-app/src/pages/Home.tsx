import { useState, useEffect } from "react";
import { Source } from "../util/types";
import SourceSelector from "../components/SourceSelector";
import TwoSectorChat from "../components/TwoSectorChat"; // Import the new component
import { getSourcesMock } from "../services/api";
import "../styles.css";

async function getSources() {
    const response = await getSourcesMock();
    if (!response) {
        throw new Error("Failed to fetch sources");
    }
    const sources: Source[] = response;
    return sources;
}

export const Home = () => {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [sources, setSources] = useState<Source[]>([]);
    const [selectedSourceId, setSelectedSourceId] = useState<string>('');

    // Fetch sources on component mount
    useEffect(() => {
        const fetchSources = async () => {
            try {
                const fetchedSources = await getSources();
                setSources(fetchedSources);
            } catch (err: any) {
                console.error("Error fetching sources:", err);
                setError("Failed to load sources.");
            }
        };
        fetchSources();
    }, []);

    const handleSourceChange = (sourceId: string) => {
        setSelectedSourceId(sourceId);
    };

    return (
        <div className="App">
            <header className="App-header">
                <img src={"/assets/logo.png"} alt="logo" />
                <h1>GPT كتاب </h1>
            </header>
            <main className="App-main">
                <div className="sidebar">
                    <h2>المصادر</h2>
                    {error && <p className="error-message">{error}</p>}
                    <SourceSelector
                        sources={sources}
                        onSourceChange={handleSourceChange}
                    />
                </div>
                <div className="chat-section">
                    <h2>تحدث مع المساعد</h2>
                    <TwoSectorChat selectedSourceId={selectedSourceId} />
                </div>
            </main>
        </div>
    );
}