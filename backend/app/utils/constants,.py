"""
Constants used throughout ROSHNI.
"""

# Prosumer types
PROSUMER_TYPE_GENERATOR = "generator"
PROSUMER_TYPE_CONSUMER = "consumer"
PROSUMER_TYPE_PROSUMER = "prosumer"

# Allocation status
ALLOCATION_PENDING = "pending"
ALLOCATION_MATCHED = "matched"
ALLOCATION_COMPLETED = "completed"
ALLOCATION_FAILED = "failed"

# Bill status
BILL_DRAFT = "draft"
BILL_FINALIZED = "finalized"
BILL_PAID = "paid"

# IoT LED states
LED_IDLE = "blue"
LED_NEGOTIATING = "yellow"
LED_ALLOCATED = "green"
LED_INSUFFICIENT = "red"

# Day/Night modes
DAY_MODE = 1.0  # Normal generation
NIGHT_MODE = 0.0  # No generation