import { useState, useEffect, useRef } from "react";
import { Source } from "../util/types";
import SourceSelector from "../components/SourceSelector/SourceSelector";
import TwoSectorChat from "../components/TwoSectorChat/TwoSectorChat";
import { getSourcesAPI } from "../services/api";
import "../styles.css";

async function getSources() {
	const response = await getSourcesAPI();
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
	const [selectedSourceId, setSelectedSourceId] = useState<string>("");
	const hasFetched = useRef(false); // prevent double fetching
	// Fetch sources on component mount
	useEffect(() => {
		if (hasFetched.current) return;
		hasFetched.current = true;
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
			<div className="header-container">
				<h1>البحث المعنوي في تفاسير القرآن</h1>
				<div className="header-pattern"></div>
			</div>
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
					<TwoSectorChat selectedSourceId={selectedSourceId} />
				</div>
			</main>
		</div>
	);
};
