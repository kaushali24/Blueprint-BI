# Demo Baseline Notes

This describes the exact authoritative database state to be used as the starting point for live demos or rehearsal.

## Files Included in Baseline
The following files were imported in this exact order:
1. `initial/WhatsApp Chat with Dilhani.zip`
2. `initial/WhatsApp Chat with Fathima.zip`
3. `increment-01/WhatsApp Chat with Fathima (2).zip` (provides feedback extraction)
4. `initial/WhatsApp Chat with Ruwan.zip`
5. `initial/WhatsApp Chat with Shenali.zip`
6. `increment-01/WhatsApp Chat with Shenali (2).zip`
7. `initial/WhatsApp Chat with Kavindu.zip`

## Files Intentionally Excluded
- `increment-01/WhatsApp Chat with Dilhani (2).zip` — **RESERVED FOR LIVE DEMO IMPORT**
- `increment-01/WhatsApp Chat with Ruwan (2).zip` — Excluded to preserve Ruwan as an Open Inquiry.
- `increment-01/WhatsApp Chat with Kavindu (2).zip` — Excluded to preserve Kavindu as a Pending Order with excluded quoted revenue.

## Expected Baseline UI State
- **Customers**: 5
- **Confirmed Orders**: 3 (Dilhani, Fathima, Shenali)
- **Pending Orders**: 1 (Kavindu - LKR 4500 quoted)
- **Open Inquiries**: 1 (Ruwan)
- **Known Revenue**: LKR 31,100.00 (excludes Kavindu's 4500)
- **Top Products**: 4 (Vanilla cupcakes leading with 18 qty, Butter cake missing since it is pending)
- **Existing Feedback**: 1 Positive (Fathima)
- **Shenali Order**: Multi-item (1kg ribbon cake + 18 cupcakes)

## Live Demo Expectation
During the live demo, importing `WhatsApp Chat with Dilhani (2).zip` will:
- Add a new feedback item for Dilhani to the dashboard.
- Provide live extraction validation.
