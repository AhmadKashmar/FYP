import { Source, ChatResponse } from '../util/types';

// Mock sources data 
const mockSources: Source[] = [
    { author: 'المحلي و السيوطي', concept: 'ميسر', date_info: 'ت 864 هـ', source_id: '1_8', source_type: 'أمهات التفاسير', title: 'تفسير الجلالين' },
    { author: 'الطبري', concept: 'بالمأثور', date_info: 'ت 310 هـ', source_id: '1_1', source_type: 'أمهات التفاسير', title: 'جامع البيان في تفسير القرآن' },
    { author: 'الزمخشري', concept: 'بياني', date_info: 'ت 538 هـ', source_id: '1_2', source_type: 'أمهات التفاسير', title: 'الكشاف' },
];

const mockChatResponse: ChatResponse = {
    answer: "هذا هو الجواب على سؤالك. يمكن أن يحتوي على تنسيق **Markdown**.",
    context_used: [], // temporarily
};

// Get sources endpoint Mock
export const getSourcesMock = (): Promise<Source[]> => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(mockSources);
        }, 500); // Simulate network delay
    });
};


// Mocks the API call to send a user message to the "with inference" API.
export const sendMessageWithInference = (query: string, sources: string[]): Promise<ChatResponse> => {
    console.log(`Mock "with inference" API call received: query="${query}", sources=${sources}`);
    return new Promise((resolve) => {
        setTimeout(() => {
            const mockChatResponse: ChatResponse = {
                answer: "This is a response generated with **inference**. The context has been used to provide a more detailed and nuanced answer.",
                context_used: [],
            };
            resolve(mockChatResponse);
        }, 1000); // Simulate network delay
    });
};

// Mocks the API call to send a user message to the "without inference" API.
export const sendMessageWithoutInference = (query: string, sources: string[]): Promise<ChatResponse> => {
    console.log(`Mock "without inference" API call received: query="${query}", sources=${sources}`);
    return new Promise((resolve) => {
        setTimeout(() => {
            const mockChatResponse: ChatResponse = {
                answer: "This is a response generated **without inference**. It is a general response that does not use any specific context from the sources.",
                context_used: [],
            };
            resolve(mockChatResponse);
        }, 1000); // Simulate network delay
    });
};
