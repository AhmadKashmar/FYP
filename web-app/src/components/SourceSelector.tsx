import React, { useState } from "react";
import { Source } from "../util/types";

interface SourceSelectorProps {
	sources: Source[];
	onSourceChange: (sourceId: string) => void;
}

const SourceSelector = ({ sources, onSourceChange }: SourceSelectorProps) => {
	const [selectedSourceId, setSelectedSourceId] = useState<string>("");

	const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
		const sourceId = event.target.value;
		setSelectedSourceId(sourceId);
		onSourceChange(sourceId);
	};

	return (
		<div className="source-selector">
			<select value={selectedSourceId} onChange={handleChange}>
				<option key="Choose a source" value="">
					جميع المصادر
				</option>
				{sources.map((source) => (
					<option key={source.source_id} value={source.source_id}>
						{source.title} ({source.concept}) -{source.author} -{" "}
						{source.date_info} - [{source.source_type}]
					</option>
				))}
			</select>
		</div>
	);
};

export default SourceSelector;
