# Sources and reporting

## Official datasets

- Certifications: https://data.cityofnewyork.us/City-Government/Civil-Service-List-Certification/a9md-ynri
- Active lists: https://data.cityofnewyork.us/City-Government/Civil-Service-List-Active-/vx8i-nprf
- API: https://data.cityofnewyork.us/resource/{dataset}.json
- Metadata: https://data.cityofnewyork.us/api/views/{dataset}.json

For reliable fetching, follow [direct SODA2 retrieval](api-retrieval.md), count-verification, total ordering, and bounded retries. `rowsUpdatedAt` is dataset-wide, not an event date. Inspect schema on field changes. Paginate and check counts; never rely on API default limits. Escape SoQL literals and parse numbers as Decimal.

| Field | Use |
|---|---|
| exam_no / list_title_code | Scope exam/title and exclude reused exam numbers |
| first_name / mi / last_name / list_no | Candidate identity |
| list_agency_code / list_agency_desc | Promotion-list agency attributes, **not verified requesting agency** |
| cert_issue_no | Certificate identifier; candidate rows are not certificate counts |
| cert_seq_no | Sequence inside the certificate, not hiring rank |
| request_date / cert_date | Request date and certification issue date |
| reissue_date / cert_expiration_date | Reissue and certificate expiry |
| no_certified / no_requested | Published counts, not hires |
| no_vacancies / provisional_replacement | Auxiliary fields, not appointment proof |
| sel_cert_description | Selection conditions; retain separately |
| established_date | Exam list establishment date |
| anniversary_date / extension_date | Published list anniversary/extension; verify official termination separately |
| adj_fa / group_no | Score and published group; do not equate group_no with a tie group |

Use “认证签发日期” for cert_date. If user asks for “cert 建立时间,” provide this date and keep request_date and exam-list established_date distinct. Resolve agency names to official codes; preserve the published legacy name and explain aliases only with official evidence. Do not silently treat similar agency names as equivalent.

Distinguish published no_certified from distinct candidate rows actually fetched, especially when multiple exams/lists share a certificate. Do not invent percentiles from a scope count. Preserve conflicting counts as a limitation.

## Windows and tables

Use New York's date. Subtract a calendar month/year with day clamping, including leap-day handling. Include both endpoints. Exclude future issue dates. Flag reissues of older certificates separately.

Current minima: Requesting agency (independently verified or unknown) | Cert Issue No | Cert Seq No | List No | Cert Date | Reissue Date | Expiry | Published No Certified | Selection conditions. Include all ties and unknown-expiry rows separately.

Agency tracking: Cert Issue No | Request Date | Cert Date | Reissue Date | Personal Seq No | Published count | Expiry | Change since previous observation.

Recent month: Agency | Cert Issue No | Cert Date | Personal Seq No | Expiry. Include every batch, not just each agency's latest.

Annual history: Agency | Cert Date | Cert Issue No | Reissue Date | Personal Seq No | Published count | Sequence difference from preceding observed batch | Expiry. Follow with first/latest/best/worst observed positions and qualified analysis. Never call a between-batch difference movement inside one certificate. Within-certificate change requires two dated observations.

A zero result means no matching records in this source/window, not never certified. Give official links, data timestamps and coverage limits. Do not speculate about HR actions or tie-breaker rules.

## Appointing agency verification

`list_agency_code` and `list_agency_desc` on this dataset are promotion-list agency fields. For open-competitive certifications, they cannot be used alone to name an agency that requested the certificate. Retain the certification issue number and person-specific values, but mark the appointing agency **unknown** without an independently verified official link. Do not mistake a citywide `000` promotion-list code for an appointing agency.

## Acquisition evidence and comparison compatibility

Preserve exam numbers as strings, including the official leading-zero form; record verified equivalent variants. Preserve List No as exact decimal text and compare with Decimal. Store API count scope separately if the candidate helper filters List No locally. Before accepting a complete observation, verify same-predicate counts, every page, and stable official `rowsUpdatedAt` before/after retrieval.

Record independently verified requesting-agency associations separately from raw `list_agency_code/desc`, with official evidence URLs and dates. Do not turn a promotion-list code or an unverified legacy name into an agency conclusion. Group batch identities by exam/title/cert number; retain selection variants and raw agency fields within the batch.

A newly fetched optional field (for example salary) has no old observed value: establish its baseline rather than report it as an update. Preserve existing event deduplication across transport or field changes. Separate event date, source update timestamp and check timestamp.
