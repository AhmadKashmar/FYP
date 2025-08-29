import { Sentence, RelatedText, ChatResponse, Source } from "./types";

/** Global registry: related_text_id -> stable global number (persists across calls) */
const GLOBAL_ID_MAP = new Map<string, number>();
/** Global counter for new related texts across calls */
let GLOBAL_REF_SEQ = 0;
export function resetGlobalRefs(to = 0) {
	GLOBAL_REF_SEQ = to;
	GLOBAL_ID_MAP.clear();
}

type WithGlobal = RelatedText & { g: number };

export function sentencesAndRelatedTextsToChatResponse(
	sentences: Sentence[],
	relatedTexts: RelatedText[],
	sources: Source[]
): ChatResponse {
	if (
		(!sentences || sentences.length === 0) &&
		(!relatedTexts || relatedTexts.length === 0)
	) {
		return {
			answer:
				`<div class="chat-answer" dir="rtl" lang="ar">` +
				`<p class="no-data">لم أجد معلومات مفيدة.</p>` +
				`</div>`,
		};
	}

	const cid = "c" + Math.random().toString(36).slice(2, 8);

	/* 1) Assign GLOBAL numbers & group tafāsīr by source (preserve insertion order) */
	const relatedBySource = new Map<string, WithGlobal[]>();
	for (const rt of relatedTexts) {
		let g = GLOBAL_ID_MAP.get(rt.related_text_id);
		if (g == null) {
			g = ++GLOBAL_REF_SEQ;
			GLOBAL_ID_MAP.set(rt.related_text_id, g);
		}
		if (!relatedBySource.has(rt.source_id)) relatedBySource.set(rt.source_id, []);
		relatedBySource.get(rt.source_id)!.push({ ...rt, g });
	}

	/* 2) Source lookup */
	const sourceById = new Map<string, Source>();
	for (const s of sources) sourceById.set(s.source_id, s);

	/* 3) Group sentences by section (safe sort) */
	const bySection = new Map<number, Sentence[]>();
	for (const s of sentences) {
		if (!bySection.has(s.section_id)) bySection.set(s.section_id, []);
		bySection.get(s.section_id)!.push(s);
	}
	const sectionIds = Array.from(bySection.keys()).sort((a, b) => a - b);
	for (const id of sectionIds) {
		bySection.get(id)!.sort((a, b) => a.sentence_id - b.sentence_id);
	}

	/* 4) LOCAL numbering by first appearance in verses */
	const localByGlobal = new Map<number, number>();
	let localCounter = 0;
	const missingGlobals = new Set<number>();

	for (const secId of sectionIds) {
		for (const s of bySection.get(secId)!) {
			const seenInVerse = new Set<string>();
			for (const relId of s.related_text_ids || []) {
				if (seenInVerse.has(relId)) continue;
				seenInVerse.add(relId);

				let g = GLOBAL_ID_MAP.get(relId);
				if (g == null) {
					g = ++GLOBAL_REF_SEQ;
					GLOBAL_ID_MAP.set(relId, g);
					missingGlobals.add(g);
				}
				if (!localByGlobal.has(g)) {
					localByGlobal.set(g, ++localCounter);
				}
			}
		}
	}

	/* 5) Build sorted source order & per-source lists based on LOCAL numbers */
	type Enriched = WithGlobal & { d: number | null };
	const enrichedBySource = new Map<string, Enriched[]>();

	// ⬇️ Replace `for...of (relatedBySource)` with typed forEach to avoid downlevelIteration need
	relatedBySource.forEach((list: WithGlobal[], sid: string) => {
		const enriched: Enriched[] = list.map((rt: WithGlobal) => ({
			...rt,
			d: localByGlobal.has(rt.g) ? (localByGlobal.get(rt.g) as number) : null,
		}));
		// sort tafāsīr within the source by local number (nulls last)
		enriched.sort((a: Enriched, b: Enriched) => {
			const da = a.d ?? Number.POSITIVE_INFINITY;
			const db = b.d ?? Number.POSITIVE_INFINITY;
			if (da !== db) return da - db;
			return 0; // keep original order on tie
		});
		enrichedBySource.set(sid, enriched);
	});

	// Sort sources by the minimum local number they contain (nulls last)
	const sourceOrder = Array.from(enrichedBySource.keys()).sort((sa, sb) => {
		const la = enrichedBySource.get(sa)!;
		const lb = enrichedBySource.get(sb)!;
		const mina = la.reduce(
			(m, x) => (x.d != null && x.d < m ? x.d : m),
			Number.POSITIVE_INFINITY
		);
		const minb = lb.reduce(
			(m, x) => (x.d != null && x.d < m ? x.d : m),
			Number.POSITIVE_INFINITY
		);
		return mina - minb;
	});

	/* 6) Render */
	const parts: string[] = [];
	parts.push(`<div class="chat-answer" dir="rtl" lang="ar" data-cid="${cid}">`);

	// === الآيات ===
	parts.push(`<h3 class="section-title">الآيات</h3>`);
	parts.push(`<ul class="verses">`);

	for (const secId of sectionIds) {
		for (const s of bySection.get(secId)!) {
			// verse order, dedup
			const verseGlobals: number[] = [];
			const seen = new Set<number>();
			for (const relId of s.related_text_ids || []) {
				let g = GLOBAL_ID_MAP.get(relId);
				if (g == null) {
					g = ++GLOBAL_REF_SEQ;
					GLOBAL_ID_MAP.set(relId, g);
					missingGlobals.add(g);
					if (!localByGlobal.has(g)) localByGlobal.set(g, ++localCounter);
				}
				if (!seen.has(g)) {
					seen.add(g);
					verseGlobals.push(g);
				}
			}

			parts.push(
				`<li class="verse" id="${cid}-s-${s.section_id}-${s.sentence_id}">` +
					`<span class="aya-braced">{</span>` +
					`<span class="verse-text">${renderImportant(s.text)}</span>` +
					`<span class="aya-braced">}</span>` +
					` <span class="verse-label" dir="ltr">[${escapeHtml(
						String(s.section_id)
					)}:${escapeHtml(String(s.sentence_id))}]</span>` +
					(verseGlobals.length
						? ` <span class="refs">` +
						  verseGlobals
								.map((g) => {
									const d = localByGlobal.get(g)!; // already assigned
									return `<a class="ref" href="#${cid}-taf-${g}" data-cid="${cid}" data-ref-global="${g}" data-ref-display="${d}"><sup>${d}</sup></a>`;
								})
								.join(" ") +
						  `</span>`
						: ``) +
					`</li>`
			);
		}
	}
	parts.push(`</ul>`);

	// === التفاسير ===
	parts.push(`<h3 class="section-title">التفاسير</h3>`);

	// use forEach to avoid `for...of` over Map/iterables
	sourceOrder.forEach((sid: string) => {
		const src = sourceById.get(sid);
		const list = enrichedBySource.get(sid)!; // Enriched[]

		const title = src?.title || sid || "مصدر غير معروف";
		const concept = src?.concept ? ` (${escapeHtml(src.concept)})` : "";
		const author = src?.author ? ` - ${escapeHtml(src.author)}` : "";
		const dateInfo = src?.date_info ? ` - ${escapeHtml(src.date_info)}` : "";
		const stype = src?.source_type ? ` - [${escapeHtml(src.source_type)}]` : "";

		parts.push(
			`<h2 class="source-heading">${escapeHtml(
				title
			)}${concept}${author}${dateInfo}${stype}</h2>`
		);

		list.forEach((rt: Enriched) => {
			parts.push(
				`<p class="tafsir" id="${cid}-taf-${rt.g}" data-ref-global="${rt.g}"` +
					(rt.d != null ? ` data-ref-display="${rt.d}"` : ``) +
					`>${renderImportant(rt.details)}</p>`
			);
			missingGlobals.delete(rt.g);
		});
	});

	// Invisible placeholders for any verse refs that didn't have tafsir in this render
	if (missingGlobals.size) {
		missingGlobals.forEach((g: number) => {
			parts.push(
				`<p id="${cid}-taf-${g}" class="tafsir placeholder" style="height:0;margin:0;padding:0;overflow:hidden;"></p>`
			);
		});
	}

	parts.push(`</div>`);
	return { answer: parts.join("") };
}

/* ===== Utilities ===== */

function escapeHtml(s: string): string {
	return s
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;")
		.replace(/\r?\n/g, "<br>");
}

function renderImportant(text: string): string {
	if (!text) return "";
	const re = /\$\$([\s\S]*?)\$\$/g;
	let out = "";
	let last = 0;
	let m: RegExpExecArray | null;
	while ((m = re.exec(text))) {
		out += escapeHtml(text.slice(last, m.index));
		out += `<span class="important">${escapeHtml(m[1])}</span>`;
		last = m.index + m[0].length;
	}
	out += escapeHtml(text.slice(last));
	return out;
}
