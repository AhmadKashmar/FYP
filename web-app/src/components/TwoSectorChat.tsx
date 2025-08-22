import { useState } from 'react';
import ChatInterface from './ChatInterface';
import { sendMessageWithInference, sendMessageWithoutInference } from '../services/api';
import { ChatResponse } from '../util/types';

interface TwoSectorChatProps {
    selectedSourceId: string;
}

const TwoSectorChat = ({ selectedSourceId }: TwoSectorChatProps) => {
    const [mode, setMode] = useState<'with' | 'without'>('with');

    const sendMessageFn =
        mode === 'with' ? sendMessageWithInference : sendMessageWithoutInference;

    return (
        <div className="flex flex-col m-4 p-4 gap-4">
            <div className="mode-toggle">
                <button
                    className={mode === 'with' ? 'selected' : ''}
                    onClick={() => setMode('with')}
                >
                    مع الاستدلال
                </button>
                <button
                    className={mode === 'without' ? 'selected' : ''}
                    onClick={() => setMode('without')}
                >
                    بدون استدلال
                </button>
            </div>

            <ChatInterface
                selectedSourceId={selectedSourceId}
                sendMessageFunction={sendMessageFn}
            />
        </div>
    );
};

export default TwoSectorChat;
