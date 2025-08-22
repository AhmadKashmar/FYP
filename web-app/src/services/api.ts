import type {
	QueryRequest,
	Sentence,
	RelatedText,
	Source,
	ChatResponse,
} from "../util/types";
import { sentencesAndRelatedTextsToChatResponse } from "../util/helpers";

const BASE_URL =
	(typeof process !== "undefined" &&
		(process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL)) ||
	"http://localhost:5000";

let SOURCES: Array<Source> = [];

export async function QueryWithoutInference(body: QueryRequest): Promise<ChatResponse> {
	const url = `${BASE_URL}/query-without-inference`;
	const res = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json",
		},
		body: JSON.stringify(body),
	});
	if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
	const { sentences, related_texts } = await res.json();
	const sentencesTyped = sentences as Array<Sentence>;
	const relatedTextsTyped = related_texts as Array<RelatedText>;

	return sentencesAndRelatedTextsToChatResponse(
		sentencesTyped,
		relatedTextsTyped,
		SOURCES
	);
}

export async function QueryWithInference(body: QueryRequest): Promise<ChatResponse> {
	const url = `${BASE_URL}/query-with-inference`;
	const res = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json",
		},
		body: JSON.stringify(body),
	});
	if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

	const data = await res.json();

	return { answer: data.response } as ChatResponse;
}

export async function getSourcesAPI(): Promise<Source[]> {
	const url = `${BASE_URL}/sources`;
	const res = await fetch(url, {
		method: "GET",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json",
		},
	});
	if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

	const { sources: json_sources } = await res.json();
	const sources = json_sources.map(
		(s: Source) =>
			({
				source_id: s.source_id || "",
				author: s.author || "",
				concept: s.concept || "",
				date_info: s.date_info || "",
				source_type: s.source_type || "",
				title: s.title || "",
			} as Source)
	);
	SOURCES = sources;
	return sources;
}
