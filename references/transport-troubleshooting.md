# Diagnose direct API access

A no-plugin prompt removes a repository dependency; it does not add network tools. Compare tool capabilities, not accounts' dataset search results.

1. Probe a small official JSON response: `https://data.cityofnewyork.us/resource/a9md-ynri.json?%24select=count%28%2A%29%20as%20total`. An array with a total tests the transport, not identity or monitoring completeness.
2. Fetch the official metadata for each dataset, then an exact filtered count using its actual fields. Candidate discovery by name/exam does not establish identity until title and exact List No are resolved. Preserve leading-zero variants. Do not copy another exam's title/List No from memory.
3. Use a supported direct GET tool if research-page retrieval cannot expose JSON. If none is supplied, stop with a tool-level access failure. No HTTP status means no claim about 403, DNS or the DCAS server being down. Do not try to bypass restrictions or fabricate a successful preflight.
4. After transport succeeds, perform every identity, pagination, count, timestamp and history check in the runtime contract. A successful single request is not a full scheduled end-to-end test.

On a private terminal, shell quoting must preserve the literal dollar signs in `$where`, `$select`, `$limit` and `$offset`. Use single-quoted parameter strings or a subprocess argument list; do not let a shell expand parameter names. Construct SoQL literals and URL encoding correctly. A malformed query returning400 is a query error, not proof of blocked network.

When acquisition fails, report: “Verification incomplete — personal records not retrieved,” component, actual attempted URL, tool/status or observed error, executed/incomplete/not-executed scope, comparison unknown and checkpoint preservation. Never say “no confirmed change” or “no match” as the result of a failed query. Do not require GitHub or repository deployment. A dataset update time read from a source page is not evidence that candidate rows were queried.

The same official URL may succeed through curl and fail through a research fetch tool. Success here does not prove another user's account can reach it. A prompt-only workflow is supported only where the executor actually exposes direct official API retrieval and the required private state. An alternative privately run script is optional, not a hidden deployment prerequisite.
