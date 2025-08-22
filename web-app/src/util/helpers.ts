import { Sentence, RelatedText, ChatResponse, Source } from "./types";

/** Global registry: related_text_id -> stable global number (persists across calls) */
const GLOBAL_ID_MAP = new Map<string, number>();
/** Global counter for new related texts across calls */
let GLOBAL_REF_SEQ = 0;
/** Optional: reset global state when you need to (tests, dev, etc.) */
export function resetGlobalRefs(to = 0) {
	GLOBAL_REF_SEQ = to;
	GLOBAL_ID_MAP.clear();
}

type WithGlobal = RelatedText & { g: number };

export function sentencesAndRelatedTextsToChatResponse(
	sentences: Sentence[], // sorted
	relatedTexts: RelatedText[], // sorted by appearance (may span many sources)
	sources: Source[] // metadata
): ChatResponse {
	const cid = "c" + Math.random().toString(36).slice(2, 8); // per-render scope

	// 1) Group related texts by source & assign GLOBAL numbers (persist across calls)
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
	const sourceOrder = Array.from(relatedBySource.keys());

	// 2) Build LOCAL display numbering (resets to 1 each call)
	const localByGlobal = new Map<number, number>();
	let localCounter = 0;
	for (const sid of sourceOrder) {
		for (const rt of relatedBySource.get(sid)!) {
			if (!localByGlobal.has(rt.g)) localByGlobal.set(rt.g, ++localCounter);
		}
	}

	// 3) Source lookup
	const sourceById = new Map<string, Source>();
	for (const s of sources) sourceById.set(s.source_id, s);

	// 4) Group sentences by section (safeguard sort)
	const bySection = new Map<number, Sentence[]>();
	for (const s of sentences) {
		if (!bySection.has(s.section_id)) bySection.set(s.section_id, []);
		bySection.get(s.section_id)!.push(s);
	}
	const sectionIds = Array.from(bySection.keys()).sort((a, b) => a - b);
	for (const id of sectionIds) {
		bySection.get(id)!.sort((a, b) => a.sentence_id - b.sentence_id);
	}

	// 5) Render
	const parts: string[] = [];
	parts.push(`<div class="chat-answer" dir="rtl" lang="ar" data-cid="${cid}">`);

	// ===== الآيات =====
	parts.push(`<h3 class="section-title">الآيات</h3>`);
	parts.push(`<ul class="verses">`);

	// Track any global refs used in verses that did not appear in relatedTexts for this render,
	// so we can append invisible placeholders at the end (ensures anchors always have a target).
	const missingGlobals = new Set<number>();

	for (const secId of sectionIds) {
		for (const s of bySection.get(secId)!) {
			// Map sentence refs -> GLOBAL numbers (assign new globals if unseen)
			const gRefs = Array.from(
				new Set(
					(s.related_text_ids || []).map((id) => {
						let g = GLOBAL_ID_MAP.get(id);
						if (g == null) {
							g = ++GLOBAL_REF_SEQ;
							GLOBAL_ID_MAP.set(id, g);
							missingGlobals.add(g); // will not have a real tafsir in this render
						}
						return g;
					})
				)
			).sort((a, b) => a - b);

			// Compute LOCAL display numbers for those globals
			const localRefs = gRefs.map((g) => {
				let d = localByGlobal.get(g);
				if (d == null) {
					d = ++localCounter; // show it locally even if the tafsir isn't in this render
					localByGlobal.set(g, d);
				}
				return { g, d };
			});

			// Verse line: {TEXT} [section:sentence] then superscript anchors
			parts.push(
				`<li class="verse" id="${cid}-s-${s.section_id}-${s.sentence_id}">` +
					`<span class="aya-braced">{</span>` +
					`<span class="verse-text">${renderImportant(s.text)}</span>` +
					`<span class="aya-braced">}</span>` +
					` <span class="verse-label" dir="ltr">[${escapeHtml(
						String(s.section_id)
					)}:${escapeHtml(String(s.sentence_id))}]</span>` +
					(localRefs.length
						? ` <span class="refs">` +
						  localRefs
								.map(
									({ g, d }) =>
										`<a class="ref" href="#${cid}-taf-${g}" data-cid="${cid}" data-ref-global="${g}" data-ref-display="${d}"><sup>${d}</sup></a>`
								)
								.join(" ") +
						  `</span>`
						: ``) +
					`</li>`
			);
		}
	}

	parts.push(`</ul>`);

	// ===== التفاسير =====
	parts.push(`<h3 class="section-title">التفاسير</h3>`);

	for (const sid of sourceOrder) {
		const src = sourceById.get(sid);
		const list = relatedBySource.get(sid)!; // WithGlobal[]

		// Heading: title (concept) - author - date_info - [source_type]
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

		// Each tafsir as <p id="${cid}-taf-${g}">
		for (const rt of list) {
			const g = rt.g;
			const d = localByGlobal.get(g)!; // local display number for this render
			parts.push(
				`<p class="tafsir" id="${cid}-taf-${g}" data-ref-global="${g}" data-ref-display="${d}">` +
					`${renderImportant(rt.details)}` +
					`</p>`
			);
			// If this global was in the "missing" set (referenced in verses but not in list),
			// showing it now means it's no longer missing.
			missingGlobals.delete(g);
		}
	}

	// Placeholders for any verse refs whose tafsir wasn’t included this render
	if (missingGlobals.size) {
		missingGlobals.forEach((g) => {
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
		.replace(/'/g, "&#39;");
}

/** Replace $$...$$ with <span class="important">...</span>, safely escaped */
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
