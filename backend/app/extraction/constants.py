from decimal import Decimal

EXTRACTION_ELIGIBLE_STATES = ('relevant',)
CONTEXT_ALLOWED_STATES = ('relevant', 'needs_review')
MAX_EPISODE_GAP_DAYS = 7
MAX_EPISODE_MESSAGES = 200
ORDER_VALID_STATUSES = ('inquiry', 'pending', 'confirmed', 'cancelled')
CONFIDENCE_REVIEW_THRESHOLD = Decimal('0.70')
