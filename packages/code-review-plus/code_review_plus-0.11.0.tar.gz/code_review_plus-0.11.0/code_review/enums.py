from enum import Enum


class ReviewRuleLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ReviewRuleLevelIcon(Enum):
    INFO = "✅"
    WARNING = "⚠"
    ERROR = "❌"
    CRITICAL = "🔥"
