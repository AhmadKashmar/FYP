import { useState } from "react";
import ChatInterface from "../ChatInterface/ChatInterface";
import { QueryWithInference, QueryWithoutInference } from "../../services/api";
import { ChatResponse } from "../../util/types";
import "./toggle-chat.css";

interface TwoSectorChatProps {
	selectedSourceId: string;
}

const TwoSectorChat = ({ selectedSourceId }: TwoSectorChatProps) => {
	const [mode, setMode] = useState<"with" | "without">("with");

	const sendMessageFn = mode === "with" ? QueryWithInference : QueryWithoutInference;

	return (
		<>
			<div className="mode-toggle">
				<button
					className={mode === "with" ? "selected" : ""}
					onClick={() => setMode("with")}
				>
					الرد الذكي
					<img src={"../../assets/llm-powered.png"}/>
				</button>
				<button
					className={mode === "without" ? "selected" : ""}
					onClick={() => setMode("without")}
				>
					البيانات الأصلية
					<img src={"../../assets/doc.png"}/>
				</button>
			</div>

			<ChatInterface
				selectedSourceId={selectedSourceId}
				sendMessageFunction={sendMessageFn}
			/>
		</>
	);
};

export default TwoSectorChat;
