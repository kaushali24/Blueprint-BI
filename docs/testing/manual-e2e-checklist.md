# Manual E2E Checklist

The following capabilities form the actual MVP user journey and are validated against the current UI and backend implementation.

| ID | Scenario | Status | Notes |
|---|---|---|---|
| 1 | Import valid WhatsApp ZIP | PASS | Processes text file, extracts participants and messages. |
| 2 | Media-containing ZIP succeeds with informational limitation | PASS | Media filenames/types extracted; image analysis deferred. |
| 3 | Recent Import appears | PASS | UI displays import history and deduplicated message count. |
| 4 | Re-import updated conversation | PASS | Successfully imports updated ZIP without errors. |
| 5 | Existing messages deduplicate | PASS | Original provenance maintained. |
| 6 | Incremental messages are processed | PASS | New messages appended and analyzed. |
| 7 | Overview metrics update | PASS | Total customers, orders, inquiries refresh on load. |
| 8 | Confirmed orders count | PASS | Only 'confirmed' or 'completed' states counted. |
| 9 | Pending orders count | PASS | Pending state counted correctly. |
| 10 | Open inquiries count | PASS | Distinct from orders; inquiries display properly. |
| 11 | Revenue excludes pending quoted amount | PASS | Semantic test passes; quotes do not inflate confirmed revenue. |
| 12 | Top products use intended confirmed-order semantics | PASS | Products ranked by confirmed volume. |
| 13 | Overview cards navigate to filtered screens | PASS | Clicks route to pre-filtered lists (Orders/Inquiries). |
| 14 | Recent Order opens Order Details | PASS | Full order breakdown and message evidence loads. |
| 15 | Multi-item order shows all items | PASS | Correct quantities and prices displayed for multiple items. |
| 16 | Evidence matches source messages | PASS | Original WhatsApp text shown for extracted fields. |
| 17 | Feedback survives incremental import | PASS | Feedback records persist. |
| 18 | Feedback raw evidence is grounded | PASS | Direct ties to message timestamps and content. |
| 19 | Assistant English query | PASS | Routes to Analytics tool, responds correctly. |
| 20 | Assistant Sinhala query | PASS | Gemini interprets intent, calls correct tool, responds in Sinhala/English. |
| 21 | Assistant Singlish query | PASS | Same cross-lingual support. |
| 22 | Markdown renders correctly | PASS | Bold, lists, tables format properly in chat UI. |
| 23 | Assistant local chat history switch/new chat | PASS | UI handles session state (backend is stateless between prompts). |
| 24 | Mobile navigation | PASS | Responsive layout scales. |
| 25 | Tablet layout | PASS | Responsive layout scales. |
| 26 | Desktop layout | PASS | Sidebar and multi-column grid render cleanly. |
| 27 | Business isolation where manually verifiable | PASS | Business 1 cannot query Business 2 metrics. |
