import React, { useState } from 'react';
import { Source } from '../util/types';

interface SourceSelectorProps {
    sources: Source[];
    onSourceChange: (sourceId: string) => void;
}

const SourceSelector = ({ sources, onSourceChange }: SourceSelectorProps) => {
    const [selectedSourceId, setSelectedSourceId] = useState<string>('');

    const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const sourceId = event.target.value;
        setSelectedSourceId(sourceId);
        onSourceChange(sourceId);
    };

    return (
        <div className="source-selector">
            <select value={selectedSourceId} onChange={handleChange}>
                <option value="">Choose a source...</option>
                {sources.map((source) => (
                    <option key={source.source_id} value={source.source_id}>
                        {source.title} - {source.author} - {source.source_type} - {source.concept} - {source.date_info}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default SourceSelector;