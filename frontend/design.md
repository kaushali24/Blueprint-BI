# ChatInsights MVP Frontend Implementation Design

> **Status**: Implementation contract. Frozen for Phase 1 build.
> **Reference**: `frontend/stitch_chatinsights_mvp_wireframes/` (visual reference only — do not copy HTML wholesale)
> **Backend**: `backend/app/main.py` and related service modules

---

## 1. Context

ChatInsights is a WhatsApp-to-business-intelligence tool for small business owners in Sri Lanka. Owners export their WhatsApp chat history as a ZIP file, upload it, and the system extracts orders, inquiries, and revenue metrics. This document defines the technical contract for building the frontend MVP across 6 approved screens: Overview, Imports, Orders, Order Details + Evidence, Inquiries, and Ask ChatInsights (Assistant).

The approved high-fidelity Stitch designs are the sole visual/UX reference. All implementation must be in the existing Next.js application — **not** in the exported Stitch HTML.

---

## 2. Goals

- Build 6 screens that exactly reproduce the Stitch visual design inside the existing Next.js app.
- Integrate with the 2 verified FastAPI endpoints.
- Identify and specify the 5 minimal GET endpoints required before backend data can be rendered.
- Define a typed API client layer, a clean route structure, and a reusable component plan.
- Ground all design token decisions in the actual Stitch `tailwind.config` extracted from the exported `code.html` files.

---

## 3. Non-Goals

- Authentication or authorization.
- Search, filtering, or date ranges.
- Forecasting, trends, or growth indicators.
- Editing extracted orders or inquiries.
- A full-conversation viewer.
- Modifying backend extraction or analytics logic.
- Replacing the existing Next.js App Router architecture.

---

## 4. Existing Frontend Reality

**Verified by inspecting the repository directly.**

| Attribute | Actual Value |
|---|---|
| Framework | Next.js `^15.5.21` (App Router) |
| React | `^19.2.5` |
| Language | TypeScript `~5.8.3` |
| Package Manager | pnpm `10.5.1` |
| Styling | Tailwind CSS `^4.2.4` (via `@tailwindcss/postcss`) |
| Component Library | Radix UI (`@radix-ui/react-*`) + custom shadcn-style components in `src/components/ui/` |
| Animation | `framer-motion ^12.38.0`, `tailwindcss-animate ^1.0.7` |
| Icons | `lucide-react ^0.476.0` (vector icons). Stitch uses Google Material Symbols — **see Icon Strategy below.** |
| Chat / Streaming | `@langchain/langgraph-sdk ^1.8.10`, `@langchain/langgraph-sdk/react` |
| API Proxy | `langgraph-nextjs-api-passthrough ^0.1.4` at `src/app/api/[..._path]/route.ts` |
| File Upload Hook | `src/hooks/use-file-upload.tsx` — handles images/PDFs via drag-drop. Supports duplicate detection. |
| Responsive Hook | `src/hooks/useMediaQuery.tsx` |
| Toast | `sonner ^2.0.7` |
| Routing | Currently single-page (`src/app/page.tsx` renders `<Thread />`) |
| Theme System | CSS custom properties in `src/app/globals.css` (`--primary`, `--background`, etc.) mapped via `@theme inline` |
| Current CSS Variables | Black/white neutral (shadcn defaults) — must be replaced with Stitch brand tokens |

### Current Chat Infrastructure

`src/providers/Stream.tsx` — establishes the LangGraph streaming connection using `useStream` from `@langchain/langgraph-sdk/react`. Reads `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_ASSISTANT_ID` from env. Renders a connection setup form if vars are missing.

`src/providers/Thread.tsx` — manages thread list via LangGraph `client.threads.search`.

`src/components/thread/index.tsx` — full chat thread UI (566 lines): composer, message list, history sidebar, sticky-to-bottom scroll, artifact viewer.

`src/providers/client.ts` — wraps `@langchain/langgraph-sdk` `Client`.

**The existing LangGraph streaming infrastructure will NOT be used for the FastAPI assistant.** The assistant will use a simple `fetch()` POST via the typed API client. The existing `Thread` component will be replaced by a simpler `AssistantThread` component on the `/assistant` route.

### Existing UI Components Available for Reuse

From `src/components/ui/`: `button`, `card`, `input`, `label`, `textarea`, `separator`, `skeleton`, `sonner`, `avatar`, `sheet`, `tooltip`, `switch`.

### Icon Strategy

The Stitch HTML uses **Google Material Symbols Outlined** (variable font). The existing codebase uses **Lucide React**.

**Decision**: Use Lucide React as the primary icon library (already installed, tree-shakeable, React-native). Map Stitch Material Symbol names to their Lucide equivalents in a single `src/lib/icons.ts` mapping file. Do **not** add a new icon CDN dependency.

| Stitch Material Symbol | Lucide Equivalent |
|---|---|
| `analytics` | `BarChart2` |
| `dashboard` | `LayoutDashboard` |
| `upload_file` | `FileUp` |
| `shopping_bag` | `ShoppingBag` |
| `forum` | `MessageSquare` |
| `smart_toy` | `Bot` |
| `check_circle` | `CheckCircle2` |
| `pending_actions` | `Clock` |
| `group` | `Users` |
| `info` | `Info` |
| `arrow_back` | `ArrowLeft` |
| `chat_bubble` | `MessageCircle` |

---

## 5. Existing Backend/API Reality

**Verified by inspecting `backend/app/main.py` and `backend/app/analytics/service.py`.**

### Confirmed HTTP Endpoints (currently live)

#### `POST /api/v1/whatsapp/imports`

- **Transport**: `multipart/form-data`
- **Request fields**:
  - `business_id: int` (Form field)
  - `file: UploadFile` (ZIP file only; `.zip` extension required)
- **Success response** (`200 OK`):
  ```json
  {
    "import_batch_id": 42,
    "status": "completed",
    "is_successful": true,
    "errors": [],
    "warnings": []
  }
  ```
- **Partial success** (`200 OK`): `"status": "completed_with_warnings"`, `is_successful: true`, `warnings` non-empty.
- **Failure** (`400 Bad Request`): body contains `{ "errors": [...], "warnings": [...], "status": "failed", "is_successful": false }`.
- **DB lock error** (`503`): `{ "errors": ["The database is locked..."] }`.
- **Not found** (`404`): `{ "errors": ["Business 1 was not found."] }`.
- **business_id handling**: Received as a form field. Backend looks up `Business` by PK before processing.

#### `POST /api/v1/assistant/chat`

- **Transport**: `application/json`
- **Request body**:
  ```json
  { "business_id": 1, "message": "What is my known revenue?" }
  ```
- **Success response** (`200 OK`):
  ```json
  { "response": "Your known revenue is Rs. 45,000." }
  ```
- **Error** (`500`): `{ "detail": "<exception string>" }` — do not expose this to the user.
- **Not found** (`404`): `{ "errors": ["Business 1 was not found."] }`.
- **business_id handling**: Received in JSON body. Passed as LangGraph `configurable.business_id`.

### Confirmed Service Methods (exist as Python, NOT as HTTP endpoints)

| Service | Method | Status |
|---|---|---|
| `AnalyticsService` | `get_business_analytics_report(session, business_id)` | **SERVICE ONLY** |
| `AnalyticsService` | `get_order_metrics(session, business_id)` | **SERVICE ONLY** |
| `AnalyticsService` | `get_product_metrics(session, business_id)` | **SERVICE ONLY** |
| `AnalyticsService` | `get_inquiry_metrics(session, business_id)` | **SERVICE ONLY** |
| `AnalyticsService` | `get_customer_metrics(session, business_id)` | **SERVICE ONLY** |
| `AnalyticsService` | `get_feedback_metrics(session, business_id)` | **SERVICE ONLY** |
| DB Models | `Order`, `OrderItem`, `Customer` | **DB ONLY** |
| DB Models | `Inquiry` | **DB ONLY** |
| DB Models | `ExtractionEvidence` (linked to `Order`, `Message`) | **DB ONLY** |
| DB Models | `ImportBatch` | **DB ONLY** |

---

## 6. API Gap Analysis

| Screen | UI Data Required | Backend Service | HTTP Endpoint | Gap |
|---|---|---|---|---|
| **Overview** | `known_total_revenue`, `orders_with_unknown_revenue_count`, confirmed/pending counts, customer count, open inquiry count, top products, recent orders | `AnalyticsService.get_business_analytics_report()` | ❌ None | **MISSING** |
| **Imports** | Upload form, progress state, result (`status`, `is_successful`, `errors`, `warnings`) | `ImportCoordinator` | ✅ `POST /api/v1/whatsapp/imports` | None |
| **Imports (history)** | List of past `ImportBatch` records | `ImportBatch` model | ❌ None | **MISSING** |
| **Orders** | List: customer name, product name, status, `total_amount`, `created_at` | `Order`, `Customer`, `OrderItem` models | ❌ None | **MISSING** |
| **Order Details** | Full `Order` + `OrderItem`s + linked `Customer.name` | ORM relationships | ❌ None | **MISSING** |
| **Order Evidence** | `ExtractionEvidence.evidence_text`, `Message.content`, `Message.sent_at`, `Participant.display_name` | ORM relationships | ❌ None | **MISSING** |
| **Inquiries** | List: customer name, `inquiry_type`, `summary`, `status`, `created_at` | `Inquiry`, `Customer` models | ❌ None | **MISSING** |
| **Assistant** | Chat request/response | LangGraph via FastAPI | ✅ `POST /api/v1/assistant/chat` | None |

**Summary**: 2 endpoints exist. 5 additional read-only GET endpoints must be added to the backend before full frontend data integration is possible.

---

## 7. Proposed Minimal API Additions

These 5 endpoints expose only existing, deterministic data. No new business logic.

### `GET /api/v1/businesses/{business_id}/analytics`
Returns `BusinessAnalyticsReportDTO` (already defined in `backend/app/analytics/schemas.py`).

**Response shape** (already defined as Pydantic):
```json
{
  "business_id": 1,
  "order_metrics": {
    "total_count": 16,
    "status_counts": { "confirmed": 12, "pending": 4 },
    "known_total_revenue": "45000.00",
    "orders_with_unknown_revenue_count": 2,
    "recent_orders": [
      { "id": 1, "order_number": null, "status": "confirmed", "total_amount": "4500.00", "created_at": "..." }
    ]
  },
  "product_metrics": { "top_products": [{ "product_name": "Chocolate Cake", "total_quantity": "12", "line_count": 4 }] },
  "inquiry_metrics": { "total_count": 8, "status_counts": { "open": 8 }, "recent_inquiries": [...] },
  "customer_metrics": { "total_known_customers": 45, "repeat_customer_count": 3 },
  "feedback_metrics": { "total_count": 5, "sentiment_counts": { "positive": 3 } }
}
```

### `GET /api/v1/businesses/{business_id}/orders`
Returns a flat list of orders with joined customer name.

**Proposed response**:
```json
[
  {
    "id": 1,
    "order_number": null,
    "status": "confirmed",
    "total_amount": "4500.00",
    "created_at": "2023-10-24T10:00:00Z",
    "customer_name": "Nimali",
    "first_product_name": "1kg Chocolate Cake"
  }
]
```

### `GET /api/v1/businesses/{business_id}/orders/{order_id}`
Returns full order detail with items.

**Proposed response**:
```json
{
  "id": 1,
  "order_number": null,
  "status": "confirmed",
  "total_amount": "4500.00",
  "created_at": "2023-10-24T10:00:00Z",
  "customer_name": "Nimali",
  "items": [
    { "product_name": "1kg Chocolate Cake", "quantity": "1", "unit_price": "4500.00", "line_total": "4500.00" }
  ]
}
```

### `GET /api/v1/businesses/{business_id}/orders/{order_id}/evidence`
Returns the WhatsApp message snippets that support this order. Sourced from `ExtractionEvidence` → `Message` → `Participant`.

**Proposed response**:
```json
[
  {
    "sender_name": "Nimali",
    "sender_type": "customer",
    "content": "Hi, I'd like to order a 1kg chocolate cake for Saturday please.",
    "sent_at": "2023-10-24T09:55:00Z"
  },
  {
    "sender_name": "Business",
    "sender_type": "business",
    "content": "Sure! That will be Rs. 4,500. Shall I confirm the order?",
    "sent_at": "2023-10-24T09:56:00Z"
  }
]
```

### `GET /api/v1/businesses/{business_id}/inquiries`
Returns list of inquiries with customer name.

**Proposed response**:
```json
[
  {
    "id": 1,
    "inquiry_type": "product_availability",
    "summary": "\"1kg chocolate cake ekak keeyada?\"",
    "status": "open",
    "created_at": "2023-10-24T10:00:00Z",
    "customer_name": "Amaya"
  }
]
```

> **Important**: Import history (`GET .../imports`) is deferred to Phase 3 implementation — the POST flow alone provides the required UI states. Add if time permits.

---

## 8. Information Architecture

5 primary destinations. Mobile-first navigation. No nested sub-navigation.

```
ChatInsights
├── Overview        (dashboard / home)
├── Imports         (WhatsApp ZIP upload)
├── Orders          (order list → order detail)
├── Inquiries       (inquiry list, read-only)
└── Assistant       (ChatInsights AI chat)
```

---

## 9. Route Design

Using Next.js App Router. The current `src/app/page.tsx` (single thread view) will be replaced.

```
src/app/
├── layout.tsx                    ← Root layout with AppShell, font, providers
├── page.tsx                      ← redirect to /overview
├── overview/
│   └── page.tsx
├── imports/
│   └── page.tsx
├── orders/
│   ├── page.tsx
│   └── [id]/
│       └── page.tsx
├── inquiries/
│   └── page.tsx
└── assistant/
    └── page.tsx
```

The existing `src/app/api/[..._path]/route.ts` LangGraph proxy is **kept unchanged** — it is not called by the ChatInsights UI but costs nothing to preserve.

---

## 10. Screen Specifications

### Overview (`/overview`)

**Layout**: Full-width page, `max-w-5xl mx-auto`, `px-4` padding.

**Sections** (top to bottom):

1. **Known Revenue Hero** — centered, `text-center`
   - Eyebrow label: `KNOWN REVENUE` (`label-caps`, `text-secondary`, uppercase)
   - Amount: `Rs. 45,000` (`metric-lg-mobile` on mobile, `metric-lg` on desktop, `text-primary`)
   - Caveat: `ⓘ 2 confirmed orders have Amount unavailable.` (`metadata`, `text-secondary`)
   - Must use `known_total_revenue` and `orders_with_unknown_revenue_count` directly.
   - If `orders_with_unknown_revenue_count === 0`, hide the caveat row.
   - **Never** show `Rs. 0` when revenue is zero — show `Rs. 0` only if `known_total_revenue` is literally 0 AND `orders_with_unknown_revenue_count` is 0.

2. **Metrics Grid** — `grid grid-cols-2 md:grid-cols-4 gap-4`
   - Confirmed Orders (`status_counts.confirmed ?? 0`)
   - Pending Orders (`status_counts.pending ?? 0`)
   - Customers (`customer_metrics.total_known_customers`)
   - Open Inquiries (`inquiry_metrics.status_counts.open ?? 0`)

3. **Two-column section** — `grid grid-cols-1 md:grid-cols-2 gap-6`
   - Left: **Top Products** list — ranked by `total_quantity` (already sorted by service)
   - Right: **Ask ChatInsights** CTA card — navigates to `/assistant`

4. **Recent Orders** — full width list of `recent_orders` (max 5, already limited by service)

### Imports (`/imports`)

**States (state machine)**:

| State | UI |
|---|---|
| `idle` | Instructions card (Quick Steps 1–4) + drag-drop dropzone |
| `file_selected` | Dropzone shows filename, enabled "Upload" button |
| `uploading` | Spinner overlay on dropzone, disabled button |
| `success` | Green result card: "Import completed successfully" + summary |
| `warning` | Amber result card: "Import completed with warnings" + warning list |
| `error` | Red result card: "Import failed" + user-friendly error messages |

**Mapping backend `status` → UI state**:
- `"completed"` + `is_successful: true` + no warnings → `success`
- `"completed_with_warnings"` + warnings present → `warning`
- `"failed"` → `error`

**Backend error translation** (do not expose raw strings):
- DB lock error → "The database is busy. Please wait a moment and try again."
- Generic error → "Import failed. Please check your file and try again."

**Recent Imports**: Display `ImportBatch` history if the endpoint exists (deferred). If unavailable at Phase 3, the section is omitted silently.

**File constraint**: Only `.zip` files accepted. State `file_selected` triggers only for valid `.zip`.

### Orders (`/orders`)

**Layout**: Single-column list of `OrderCard`s. No search/filter.

**OrderCard fields** (from list endpoint):
- Customer name (bold, `body-md`)
- Status badge (`StatusBadge`)
- First product name (`metadata`, `text-secondary`)
- Amount (`AmountDisplay` — handles null)
- Date (`metadata`, `text-secondary`, relative: Today / Yesterday / Oct 24)

**`AmountDisplay` contract**:
- `total_amount !== null` → `Rs. {amount}` (`body-md`, `text-primary`, bold)
- `total_amount === null` → `Amount unavailable` (`metadata`, `text-secondary`, italic)
- **Never** show `Rs. 0.00` for `null` amounts.

**`StatusBadge` contract** (pill shape, `rounded-full`):
- `confirmed` → `bg-primary-fixed text-on-primary-fixed-variant` (teal tint)
- `pending` → `bg-tertiary-fixed text-on-tertiary-fixed-variant` (amber tint)
- `cancelled` → `bg-error-container text-on-error-container` (red tint)

Tapping an order → navigates to `/orders/[id]`.

### Order Details (`/orders/[id]`)

**Two-section layout**:

**Section 1 — CHATINSIGHTS IDENTIFIED** (`label-caps` eyebrow)
Card with: Status badge, Date, Customer label+value, Product label+value, Total Amount.

**Section 2 — SUPPORTING WHATSAPP MESSAGES** (`label-caps` eyebrow)
Chat bubble container. Evidence messages rendered as:
- Customer messages: left-aligned, white card, `border-l-2 border-primary`, `rounded-2xl rounded-tl-sm`
- Business messages: right-aligned, `bg-primary text-on-primary`, `rounded-2xl rounded-tr-sm`
- Sender name above bubble in `metadata text-secondary`

Footer note (italic): *"These messages support the information ChatInsights identified above."*

**Do NOT expose**: confidence, model name, extraction IDs, JSON data, full conversation history.

**Desktop layout**: `grid grid-cols-1 lg:grid-cols-12` — Identified takes `lg:col-span-5`, Evidence takes `lg:col-span-7`.

### Inquiries (`/inquiries`)

**Page subtitle**: "View customer questions and requests." (fixed copy)

Single-column list of `InquiryCard`s. No editing.

**InquiryCard fields**:
- Avatar: initials circle (`secondary-container` background)
- Customer name (bold)
- Date (right-aligned, `metadata`, `text-secondary`)
- Summary text (quoted, `body-md`)
- Status badge: `open` → amber, `resolved` → teal

Active/selected inquiry card: left border highlight `border-l-2 border-primary`.

### Assistant (`/assistant`)

**Layout**: Full-height flex column. Header, message thread, suggested queries, composer at bottom.

**Welcome state** (empty thread):
- Bot icon card: "What can I help you with today?"
- Body: "I can answer questions using your available business data. Try asking about: Known revenue, Orders and their status, Top products, Customers and inquiries"

**Starter questions** (rendered as pill buttons when thread is empty):
```
How many confirmed orders do I have?
What is my known revenue?
What are my top products?
How many inquiries do I have?
mage confirmed orders keeyak thiyenawada?
```

Tapping a starter question sends it immediately.

**Message display**:
- User messages: right-aligned, `bg-primary text-on-primary` bubble
- AI responses: left-aligned, white card with teal left border (`ai-bubble-shadow`)
- If response contains a key metric (e.g. revenue number), render in a highlighted `AssistantMetricCard` sub-component

**Composer**:
- Placeholder: `Ask in English, සිංහල or Singlish...`
- Send icon button
- Disabled while waiting for response

**Error handling**: On 500 from FastAPI → show "ChatInsights is temporarily unavailable. Please try again." Do NOT show the raw exception string.

**Do NOT advertise**: date filters, forecasting, growth, trends, predictions.

---

## 11. Component Architecture

### File structure

```
src/
├── app/                        ← Next.js App Router pages
├── components/
│   ├── ui/                     ← Existing shadcn primitives (reuse as-is)
│   ├── layout/
│   │   ├── AppShell.tsx        ← Root layout wrapper with nav
│   │   ├── BottomNavigation.tsx ← Fixed bottom nav (mobile only, md:hidden)
│   │   ├── SideNavigation.tsx  ← Left sidebar (hidden on mobile, md:flex)
│   │   └── PageHeader.tsx      ← Page title + optional back button
│   ├── overview/
│   │   ├── KnownRevenueCard.tsx
│   │   ├── MetricCard.tsx
│   │   ├── TopProductsList.tsx
│   │   ├── RecentOrdersList.tsx
│   │   └── AssistantCTACard.tsx
│   ├── imports/
│   │   ├── FileUploadCard.tsx
│   │   ├── ImportProgress.tsx
│   │   └── ImportResultCard.tsx
│   ├── orders/
│   │   ├── OrderCard.tsx
│   │   ├── OrderDetailsCard.tsx
│   │   └── EvidenceMessageList.tsx
│   ├── inquiries/
│   │   └── InquiryCard.tsx
│   ├── assistant/
│   │   ├── AssistantThread.tsx
│   │   ├── AssistantMessage.tsx
│   │   ├── StarterQuestions.tsx
│   │   └── AssistantComposer.tsx
│   └── shared/
│       ├── StatusBadge.tsx
│       ├── AmountDisplay.tsx
│       ├── LoadingState.tsx
│       ├── EmptyState.tsx
│       └── ErrorState.tsx
├── hooks/
│   ├── use-file-upload.tsx     ← Existing (reuse)
│   ├── useMediaQuery.tsx       ← Existing (reuse)
│   └── useZipUpload.ts         ← NEW: wraps fetch POST to /api/v1/whatsapp/imports
├── lib/
│   ├── api/
│   │   ├── client.ts           ← NEW: typed FastAPI client
│   │   └── types.ts            ← NEW: TS interfaces from FastAPI schemas
│   ├── icons.ts                ← NEW: Lucide icon mapping
│   └── utils.ts                ← Existing (reuse)
└── providers/
    ├── BusinessProvider.tsx    ← NEW: business_id context
    ├── Stream.tsx              ← Existing (keep, unused by ChatInsights UI)
    └── Thread.tsx              ← Existing (keep, unused by ChatInsights UI)
```

### Component Contracts

**`MetricCard`**
```tsx
interface MetricCardProps {
  label: string;       // "CONFIRMED ORDERS"
  value: number;
  icon: LucideIcon;
  isLoading?: boolean;
}
```

**`KnownRevenueCard`**
```tsx
interface KnownRevenueCardProps {
  knownTotalRevenue: Decimal | string;
  ordersWithUnknownRevenueCount: number;
  isLoading?: boolean;
}
```

**`StatusBadge`**
```tsx
type OrderStatus = "confirmed" | "pending" | "cancelled";
type InquiryStatus = "open" | "resolved";
interface StatusBadgeProps { status: OrderStatus | InquiryStatus; }
```

**`AmountDisplay`**
```tsx
interface AmountDisplayProps {
  amount: string | null;  // Decimal serialized as string from FastAPI
  variant?: "hero" | "inline";
}
```

---

## 12. Design System / Tokens

**Source**: Extracted directly from `stitch_chatinsights_mvp_wireframes/*/code.html` Tailwind config. These are the authoritative values — do not deviate.

### Implementation approach

The existing `src/app/globals.css` uses shadcn CSS variables. These will be **extended** (not replaced) by adding ChatInsights-specific tokens in a new `@layer base` block. The shadcn primitives (`button`, `card`, etc.) continue to use their own `--primary`, `--border` vars. New ChatInsights components will use the `ci-*` prefixed custom properties.

### Color Tokens (exact hex from Stitch)

```css
/* In globals.css — add to :root */
--ci-primary: #00685f;
--ci-primary-container: #008378;
--ci-on-primary: #ffffff;
--ci-on-primary-container: #f4fffc;
--ci-primary-fixed: #89f5e7;
--ci-primary-fixed-dim: #6bd8cb;
--ci-on-primary-fixed: #00201d;
--ci-on-primary-fixed-variant: #005049;

--ci-secondary: #5a5f62;
--ci-secondary-container: #dce0e4;
--ci-on-secondary: #ffffff;
--ci-on-secondary-container: #5e6367;

--ci-tertiary: #8d4b00;
--ci-tertiary-fixed: #ffdcc3;
--ci-tertiary-fixed-dim: #ffb77d;
--ci-on-tertiary-fixed: #2f1500;
--ci-on-tertiary-fixed-variant: #6e3900;

--ci-background: #f9f9ff;
--ci-surface: #f9f9ff;
--ci-surface-container-lowest: #ffffff;
--ci-surface-container-low: #f0f3ff;
--ci-surface-container: #e7eeff;
--ci-surface-container-high: #dee8ff;
--ci-surface-container-highest: #d8e3fb;
--ci-surface-variant: #d8e3fb;

--ci-on-background: #111c2d;
--ci-on-surface: #111c2d;
--ci-on-surface-variant: #3d4947;

--ci-outline: #6d7a77;
--ci-outline-variant: #bcc9c6;

--ci-error: #ba1a1a;
--ci-error-container: #ffdad6;
--ci-on-error: #ffffff;
--ci-on-error-container: #93000a;

--ci-inverse-surface: #263143;
--ci-inverse-on-surface: #ecf1ff;
--ci-inverse-primary: #6bd8cb;
```

### Tailwind Extension (in `tailwind.config.js`)

```js
// Add to theme.extend.colors
colors: {
  "ci-primary": "var(--ci-primary)",
  "ci-primary-container": "var(--ci-primary-container)",
  "ci-on-primary": "var(--ci-on-primary)",
  "ci-primary-fixed": "var(--ci-primary-fixed)",
  "ci-on-primary-fixed-variant": "var(--ci-on-primary-fixed-variant)",
  "ci-secondary": "var(--ci-secondary)",
  "ci-secondary-container": "var(--ci-secondary-container)",
  "ci-tertiary-fixed": "var(--ci-tertiary-fixed)",
  "ci-on-tertiary-fixed-variant": "var(--ci-on-tertiary-fixed-variant)",
  "ci-background": "var(--ci-background)",
  "ci-surface": "var(--ci-surface)",
  "ci-surface-container-lowest": "var(--ci-surface-container-lowest)",
  "ci-surface-container-low": "var(--ci-surface-container-low)",
  "ci-surface-container": "var(--ci-surface-container)",
  "ci-on-surface": "var(--ci-on-surface)",
  "ci-on-surface-variant": "var(--ci-on-surface-variant)",
  "ci-outline": "var(--ci-outline)",
  "ci-outline-variant": "var(--ci-outline-variant)",
  "ci-error": "var(--ci-error)",
  "ci-error-container": "var(--ci-error-container)",
  "ci-on-error-container": "var(--ci-on-error-container)",
}
```

### Typography (exact from Stitch)

All use **Inter** — already loaded in `src/app/layout.tsx` via `next/font/google`.

| Token | Size | Weight | Line Height | Letter Spacing |
|---|---|---|---|---|
| `metric-lg` | 32px | 700 | 40px | -0.02em |
| `metric-lg-mobile` | 28px | 700 | 34px | -0.01em |
| `headline-md` | 20px | 600 | 28px | — |
| `body-md` | 16px | 400 | 24px | — |
| `label-caps` | 12px | 600 | 16px | 0.05em |
| `metadata` | 13px | 400 | 18px | — |

### Border Radius (from Stitch)

| Token | Value |
|---|---|
| `DEFAULT` | 0.25rem (4px) |
| `lg` | 0.5rem (8px) |
| `xl` | 0.75rem (12px) |
| `full` | 9999px |

### Spacing (from Stitch)

| Token | Value |
|---|---|
| `container-padding` | 1rem (16px) |
| `card-padding` | 1.25rem (20px) |
| `stack-gap-sm` | 0.5rem (8px) |
| `stack-gap-md` | 1rem (16px) |
| `stack-gap-lg` | 1.5rem (24px) |

### Shadow / Elevation

- Cards: `border border-ci-outline-variant` (1px solid) — no box-shadow
- Evidence bubbles: `box-shadow: 0px 2px 4px rgba(30, 41, 59, 0.05)` → custom class `.ai-bubble-shadow` in `globals.css`
- Primary buttons: `shadow-sm`

---

## 13. API Client Architecture

All FastAPI calls go through `src/lib/api/client.ts`. Components call typed async functions — no bare `fetch()` in component files.

### `src/lib/api/types.ts`

```ts
// Maps 1:1 to FastAPI Pydantic models

export interface RecentOrderDTO {
  id: number;
  order_number: string | null;
  status: string;
  total_amount: string | null;  // Decimal serialized as string
  created_at: string;           // ISO 8601
}

export interface ProductMetricItemDTO {
  product_name: string;
  total_quantity: string;
  line_count: number;
}

export interface OrderMetricsDTO {
  total_count: number;
  status_counts: Record<string, number>;
  known_total_revenue: string;
  orders_with_unknown_revenue_count: number;
  recent_orders: RecentOrderDTO[];
}

export interface CustomerMetricsDTO {
  total_known_customers: number;
  repeat_customer_count: number;
}

export interface InquiryMetricsDTO {
  total_count: number;
  status_counts: Record<string, number>;
  recent_inquiries: RecentInquiryDTO[];
}

export interface BusinessAnalyticsReportDTO {
  business_id: number;
  order_metrics: OrderMetricsDTO;
  product_metrics: { top_products: ProductMetricItemDTO[] };
  inquiry_metrics: InquiryMetricsDTO;
  customer_metrics: CustomerMetricsDTO;
  feedback_metrics: { total_count: number; sentiment_counts: Record<string, number> };
}

export interface OrderSummaryDTO {
  id: number;
  order_number: string | null;
  status: string;
  total_amount: string | null;
  created_at: string;
  customer_name: string | null;
  first_product_name: string | null;
}

export interface OrderItemDTO {
  product_name: string;
  quantity: string;
  unit_price: string | null;
  line_total: string | null;
}

export interface OrderDetailDTO {
  id: number;
  order_number: string | null;
  status: string;
  total_amount: string | null;
  created_at: string;
  customer_name: string | null;
  items: OrderItemDTO[];
}

export interface EvidenceMessageDTO {
  sender_name: string;
  sender_type: "customer" | "business";
  content: string;
  sent_at: string | null;
}

export interface InquirySummaryDTO {
  id: number;
  inquiry_type: string;
  summary: string;
  status: string;
  created_at: string;
  customer_name: string | null;
}

export interface ImportResultDTO {
  import_batch_id: number;
  status: string;
  is_successful: boolean;
  errors: string[];
  warnings: string[];
}

export interface ChatResponseDTO {
  response: string;
}
```

### `src/lib/api/client.ts`

```ts
const API_BASE = process.env.NEXT_PUBLIC_FASTAPI_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err);
  }
  return res.json();
}

export const api = {
  getAnalytics: (businessId: number) =>
    apiFetch<BusinessAnalyticsReportDTO>(`/api/v1/businesses/${businessId}/analytics`),

  getOrders: (businessId: number) =>
    apiFetch<OrderSummaryDTO[]>(`/api/v1/businesses/${businessId}/orders`),

  getOrder: (businessId: number, orderId: number) =>
    apiFetch<OrderDetailDTO>(`/api/v1/businesses/${businessId}/orders/${orderId}`),

  getOrderEvidence: (businessId: number, orderId: number) =>
    apiFetch<EvidenceMessageDTO[]>(`/api/v1/businesses/${businessId}/orders/${orderId}/evidence`),

  getInquiries: (businessId: number) =>
    apiFetch<InquirySummaryDTO[]>(`/api/v1/businesses/${businessId}/inquiries`),

  uploadImport: (businessId: number, file: File) => {
    const form = new FormData();
    form.append("business_id", String(businessId));
    form.append("file", file);
    return apiFetch<ImportResultDTO>("/api/v1/whatsapp/imports", {
      method: "POST",
      headers: {},  // Let browser set Content-Type with boundary
      body: form,
    });
  },

  chat: (businessId: number, message: string) =>
    apiFetch<ChatResponseDTO>("/api/v1/assistant/chat", {
      method: "POST",
      body: JSON.stringify({ business_id: businessId, message }),
    }),
};
```

### Environment Variable

Add to `frontend/agent-chat-ui/.env`:
```
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
```

---

## 14. Business Context Handling

**MVP Boundary**: No authentication. `business_id` is scoped client-side for demo purposes only.

**Implementation**: `src/providers/BusinessProvider.tsx` — a React Context with a single constant.

```tsx
const DEMO_BUSINESS_ID = 1;  // MVP constant — not auth-protected

const BusinessContext = createContext<{ businessId: number }>({ businessId: DEMO_BUSINESS_ID });

export function BusinessProvider({ children }: { children: ReactNode }) {
  return (
    <BusinessContext.Provider value={{ businessId: DEMO_BUSINESS_ID }}>
      {children}
    </BusinessContext.Provider>
  );
}

export const useBusinessId = () => useContext(BusinessContext).businessId;
```

`BusinessProvider` wraps the app in `src/app/layout.tsx`. All API client calls read `businessId` via `useBusinessId()`. The constant is defined once and never derived from user input.

**This is a demo scoping mechanism, not authorization.**

---

## 15. Assistant Integration

The existing LangGraph `StreamProvider` / `ThreadProvider` / `Thread` component are **not used** on the `/assistant` route. They remain in the codebase for potential future use.

The `/assistant` page uses a new `AssistantThread` component that:
1. Maintains local `messages: Array<{role: 'user'|'assistant', content: string}>` state.
2. On submit, calls `api.chat(businessId, message)`.
3. Renders messages as styled bubbles.
4. Shows `StarterQuestions` when `messages.length === 0`.
5. Scrolls to bottom after each new message (use `useEffect` on messages array).

**No streaming**: The FastAPI endpoint returns a complete response synchronously. Show a loading spinner while awaiting.

---

## 16. Import Workflow

`useZipUpload` hook encapsulates the state machine:

```ts
type ImportState =
  | { stage: "idle" }
  | { stage: "file_selected"; file: File }
  | { stage: "uploading" }
  | { stage: "success"; result: ImportResultDTO }
  | { stage: "warning"; result: ImportResultDTO }
  | { stage: "error"; messages: string[] };
```

The `FileUploadCard` component accepts only `.zip` files via input `accept=".zip"` and drag-drop. On file drop, transitions to `file_selected`. User confirms → transitions to `uploading` → calls `api.uploadImport()` → transitions to result state.

**Error translation** (in `useZipUpload`):
- Backend `errors` array items are displayed verbatim only if they are user-safe.
- DB lock message → "The database is busy. Please try again in a moment."
- Generic 500 → "Import failed. Please try again."
- 404 → "Business not found. Contact support."

---

## 17. Orders / Evidence Integration

Two separate fetches for the `/orders/[id]` page:
1. `api.getOrder(businessId, id)` → Order detail
2. `api.getOrderEvidence(businessId, id)` → Evidence messages

Both run in parallel with `Promise.all`. If evidence returns an empty array, show: *"No supporting messages available for this order."*

`EvidenceMessageList` maps `sender_type`:
- `"customer"` → left bubble (`bg-ci-surface-container-lowest border-l-2 border-ci-primary`)
- `"business"` → right bubble (`bg-ci-primary text-ci-on-primary`)

---

## 18. Loading / Empty / Error States

### Per-screen state table

| Screen | Loading | Empty | Error |
|---|---|---|---|
| Overview | Skeleton cards (2×2 grid + revenue row) | "No business insights yet. Upload a WhatsApp export to get started." + Import CTA button | "Could not load overview. Please try again." |
| Imports | N/A (upload is synchronous) | Idle state = default | Inline error card |
| Orders | Skeleton list (3 cards) | "No orders identified yet." | "Could not load orders. Please try again." |
| Order Details | Skeleton detail card + evidence skeleton | "No supporting messages available." (evidence only) | "Could not load order details." |
| Inquiries | Skeleton list (3 cards) | "No inquiries identified yet." | "Could not load inquiries." |
| Assistant | Loading spinner on composer while awaiting | Welcome card + starter questions | Inline error message (not raw exception) |

### `LoadingState` — Skeleton

Use the existing `src/components/ui/skeleton.tsx`. Each page wraps its main content with `<Suspense>` and a skeleton fallback.

### `EmptyState`

```tsx
interface EmptyStateProps {
  message: string;
  action?: { label: string; href: string };
}
```

### `ErrorState`

```tsx
interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}
```

---

## 19. Responsive Design

### Breakpoints (Tailwind defaults, aligned with Stitch)

| Breakpoint | Prefix | Notes |
|---|---|---|
| < 768px | (default) | Mobile: bottom nav, single column |
| ≥ 768px | `md:` | Tablet/Desktop: side nav appears, grid expands |
| ≥ 1024px | `lg:` | Desktop: 2-column layout on Order Details |

### Navigation

- **Mobile** (`< md`): Fixed bottom nav bar (16px height), 5 items. `md:hidden`.
- **Desktop** (`md+`): Fixed left sidebar (w-64), `hidden md:flex`. Bottom nav hidden.
- `AppShell` renders both; CSS controls visibility.

### Content area

```html
<main class="md:ml-64 max-w-5xl mx-auto px-4 pt-20 pb-24 md:pt-8 md:pb-8">
```

- `pt-20` accounts for fixed top bar on mobile.
- `pb-24` accounts for fixed bottom nav on mobile.
- `md:ml-64` accounts for sidebar on desktop.

### Specific responsive behaviors

| Screen | Mobile | Desktop |
|---|---|---|
| Overview metrics | `grid-cols-2` | `md:grid-cols-4` |
| Overview Top Products + CTA | Stacked (`grid-cols-1`) | Side by side (`md:grid-cols-2`) |
| Order Details sections | Stacked | `lg:grid-cols-12` (5+7 split) |
| Known Revenue text | `text-metric-lg-mobile` (28px) | `md:text-metric-lg` (32px) |

---

## 20. Accessibility

- Semantic HTML: `<nav>`, `<main>`, `<header>`, `<section>`, `<h1>`–`<h3>`.
- Active nav item has `aria-current="page"`.
- `AmountDisplay` uses `aria-label="Amount unavailable"` when null (not an empty span).
- `StatusBadge` uses `role="status"` for screen readers.
- All icon-only buttons have `aria-label`.
- Focus management on route change (Next.js handles this with App Router).
- Color contrast: `ci-primary (#00685f)` on `ci-surface-container-lowest (#ffffff)` — verified contrast ratio > 4.5:1.

---

## 21. Implementation Sequence

### Phase 1 — Foundation (prerequisite for all other phases)
- Update `globals.css` with ChatInsights CSS custom properties.
- Extend `tailwind.config.js` with `ci-*` color tokens and Stitch spacing/typography.
- Add `NEXT_PUBLIC_FASTAPI_URL` to `.env`.
- Create `src/lib/api/types.ts` and `src/lib/api/client.ts`.
- Create `src/providers/BusinessProvider.tsx`.
- Scaffold App Router route structure (`/overview`, `/imports`, `/orders`, `/orders/[id]`, `/inquiries`, `/assistant`).
- Build `AppShell`, `BottomNavigation`, `SideNavigation`, `PageHeader`.
- Build shared: `StatusBadge`, `AmountDisplay`, `LoadingState`, `EmptyState`, `ErrorState`.
- Update `src/app/layout.tsx`: add `BusinessProvider`, `AppShell`.

### Phase 2 — Overview
- Build `KnownRevenueCard`, `MetricCard`, `TopProductsList`, `RecentOrdersList`, `AssistantCTACard`.
- Wire to `api.getAnalytics()`.
- Implement loading skeleton + empty + error states.

> **Note**: Requires `GET /api/v1/businesses/{business_id}/analytics` on backend. Build with mock data first.

### Phase 3 — Imports
- Build `FileUploadCard`, `ImportProgress`, `ImportResultCard`.
- Implement `useZipUpload` hook.
- Wire to `api.uploadImport()`.
- Implement all 5 UI states.

### Phase 4 — Orders + Order Details + Evidence
- Build `OrderCard`, `OrderDetailsCard`, `EvidenceMessageList`.
- Wire `/orders` to `api.getOrders()`.
- Wire `/orders/[id]` to `api.getOrder()` + `api.getOrderEvidence()` in parallel.
- Implement empty + loading + error states.

> **Note**: Requires `GET .../orders`, `GET .../orders/{id}`, `GET .../orders/{id}/evidence`.

### Phase 5 — Inquiries
- Build `InquiryCard`.
- Wire to `api.getInquiries()`.

> **Note**: Requires `GET .../inquiries`.

### Phase 6 — Assistant
- Build `AssistantThread`, `AssistantMessage`, `StarterQuestions`, `AssistantComposer`.
- Wire to `api.chat()`.
- Implement welcome state, loading state, error state.

### Phase 7 — Polish
- Responsive testing on mobile (375px), tablet (768px), desktop (1280px).
- Verify all empty/loading/error states render correctly.
- Verify `AmountDisplay` never shows `Rs. 0` for null amounts.
- Verify `KnownRevenueCard` caveat text logic.
- Verify assistant does not expose raw backend exceptions.
- Fix any layout overflow issues on small screens.

### Phase 8 — E2E Integration
- Full integration test with live FastAPI backend.
- Upload a real WhatsApp ZIP → verify Overview updates.
- Click through to Order Details → verify evidence renders.
- Ask a question in assistant → verify response renders.

---

## 22. Testing Strategy

- **Unit**: `AmountDisplay` (null handling), `StatusBadge` (all status variants), `useZipUpload` (state transitions).
- **API client**: Mock `fetch` in tests; verify correct URL construction for each `api.*` function.
- **Integration**: Run Next.js dev server against local FastAPI. Verify each screen loads without console errors.
- **Responsive**: Use Chrome DevTools device emulation at 375px, 768px, 1280px.

---

## 23. Manual E2E Acceptance Criteria

1. **Imports**: Upload a valid WhatsApp `.zip` → see "Import completed successfully" result card.
2. **Overview**: After import, navigate to Overview → see non-zero `Known Revenue` and metric counts.
3. **Orders**: Navigate to Orders → see list of orders with correct `AmountDisplay` (no `Rs. 0` for unknowns).
4. **Order Details**: Tap an order → see "CHATINSIGHTS IDENTIFIED" section and "SUPPORTING WHATSAPP MESSAGES" chat bubbles.
5. **Inquiries**: Navigate to Inquiries → see list with correct status badges.
6. **Assistant**: Ask "What is my known revenue?" → receive a business-relevant answer. No raw exception strings visible.
7. **Singlish**: Ask "mage confirmed orders keeyak thiyenawada?" → receive a meaningful response.
8. **Mobile nav**: On 375px viewport, bottom nav is visible and all 5 tabs navigate correctly.
9. **Empty state**: On a fresh business with no data, all screens show the appropriate empty state message.

---

## 24. Deferred Features

The following are explicitly out of scope for MVP and must NOT be built:

- Authentication / authorization / session management
- Date range filtering on any screen
- Search within orders or inquiries
- Editing extracted order or inquiry data
- Full-conversation viewer (beyond the evidence messages tied to a specific order)
- Forecasting, growth trends, or predictions in the assistant
- Import history list (the `GET .../imports` endpoint)
- Dark mode (Stitch design is light-mode only)
- Push notifications or real-time updates
- Pagination (assume data volume is small for MVP)
