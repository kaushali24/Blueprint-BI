from decimal import Decimal

EXTRACTION_ELIGIBLE_STATES = ('relevant',)
CONTEXT_ALLOWED_STATES = ('relevant', 'needs_review')
CONTEXT_WINDOW_BEFORE = 5
CONTEXT_WINDOW_AFTER = 2
ORDER_VALID_STATUSES = ('inquiry', 'pending', 'confirmed', 'cancelled')
CONFIDENCE_REVIEW_THRESHOLD = Decimal('0.70')
