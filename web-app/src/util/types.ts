export type QueryRequest = {
	query: string;
	sources: string[];
	previousMessages?: Message[];
};

export type Sentence = {
	sentence_id: number;
	section_id: number;
	text: string;
	similarity: number;
	related_text_ids: string[];
};

export type RelatedText = {
	related_text_id: string;
	details: string;
	similarity: number;
	source_id: string;
};

export interface ChatResponse {
	answer: string;
}

export type Source = {
	source_id: string;
	author: string;
	concept: string;
	date_info: string;
	source_type: string;
	title: string;
};

export interface Message {
	id: string;
	sender: "user" | "bot";
	text: string;
	timestamp: string;
}
