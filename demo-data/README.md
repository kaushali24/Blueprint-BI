# ChatInsights Demo Data

## Purpose

These curated WhatsApp exports are supplied for reproducible MVP evaluation. They demonstrate the ChatInsights platform's ability to ingest, parse, extract, and analyze unstructured customer conversations into structured business data (orders, inquiries, feedback).

## Before You Start

- Ensure you have followed the setup instructions in the root `README.md`.
- **CRITICAL:** You must run `python scripts/init_db.py` to initialize the database and seed the required `Nadeeka Cakes` business record before attempting any imports.
- Make sure both the backend (FastAPI) and frontend (Next.js) servers are running.
- You must have configured a valid `GOOGLE_API_KEY` in `backend/.env` for Gemini extraction to work.

## Demo Data Structure

The provided data contains curated exports for 5 distinct customers:

- `initial/`: The first export of a conversation.
- `increment-01/`: A later export of the same conversation, containing the previous messages plus new messages.

## Scenario 1 — Initial Imports

To reproduce the exact MVP baseline state, perform the following initial imports through the web UI. 

**Steps:**
1. Navigate to the **Imports** tab in the ChatInsights web UI.
2. Upload the ZIP files directly (do not manually extract the text files).
3. Wait for each file's processing to finish before uploading the next.

**Import Sequence:**
For the most consistent timeline, import them in this verified order:
1. `initial/WhatsApp Chat with Dilhani.zip`
2. `initial/WhatsApp Chat with Fathima.zip`
3. `initial/WhatsApp Chat with Ruwan.zip`
4. `initial/WhatsApp Chat with Shenali.zip`
5. `initial/WhatsApp Chat with Kavindu.zip`

### Expected Results After Initial Imports

The AI model (Gemini 3.6 Flash) will analyze the episodes. Note that while LLMs can have slight non-deterministic variations in exact wording, the core structured classifications should match these verified baseline results:

| Metric | Expected Value | Notes |
|---|---|---|
| **Customers** | 5 | All 5 distinct identities recognized. |
| **Confirmed Orders** | 3 | Dilhani, Fathima, Shenali. |
| **Pending Orders** | 1 | Kavindu (Quote provided, but intent to purchase unconfirmed). |
| **Open Inquiries** | 1 | Ruwan (Question asked, waiting for business reply). |
| **Known Revenue** | LKR 31,100.00 | Sum of *Confirmed* orders only (Kavindu's 4,500 pending quote is explicitly excluded). |
| **Shenali Order** | Multi-item | Successfully extracts multiple items (Ribbon cake + cupcakes) in one order. |

## Scenario 2 — Incremental Imports

ChatInsights supports importing later exports of the same conversation. The system will deduplicate raw messages and intelligently skip extraction for historical episodes that have not changed, reducing LLM costs.

**Steps:**
1. Upload `increment-01/WhatsApp Chat with Fathima (2).zip`
2. Upload `increment-01/WhatsApp Chat with Shenali (2).zip`

*(Note: You can also upload Dilhani, Ruwan, or Kavindu's incremental files to test further interactions).*

### Expected Results After Incremental Imports

- **Fathima Increment:** The AI should detect new post-purchase interactions and extract a **Positive Feedback** record, tying it to her existing customer profile.
- **Deduplication:** The backend logs should indicate that historical messages were identified as duplicates and unchanged extraction targets were skipped.

## What to Verify in the UI

After importing, explore the following areas in the UI to verify the MVP:

- **Overview:** Check the aggregate metrics (Revenue, Counts, Top Products).
- **Orders:** Verify the distinction between Pending and Confirmed statuses. Click to view line items.
- **Inquiries:** Check Ruwan's unresolved question.
- **Customers:** View the consolidated customer list.
- **Recent Imports:** View the batch success status and deduplication counts.
- **Assistant:** Use the chat interface to ask natural language questions (e.g., *"What is my known revenue?"*, *"How many pending orders do I have?"*).

## Notes / MVP Boundaries

- **Demo Data Only:** These are curated demonstration conversations designed to highlight specific business interaction types. They are not production customer data.
- **Non-Determinism:** While the extraction schema is strictly enforced, LLMs may sometimes vary their exact wording or summarization of a customer inquiry. 
- **Business Identity:** The MVP is currently scoped to a single hardcoded business ID (`Nadeeka Cakes`). Do not modify the business identity or database structure without reviewing the architecture first.
