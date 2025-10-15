"""Appointment types and enums for Open Dental SDK."""

from enum import Enum


class AppointmentStatus(str, Enum):
    """Appointment status enum."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentPriority(str, Enum):
    """Appointment priority enum."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BlockType(str, Enum):
    """Schedule block type enum."""
    SCHEDULE = "schedule"
    LUNCH = "lunch"
    MEETING = "meeting"
    BREAK = "break"
    EMERGENCY = "emergency"
    BLOCKED = "blocked"


class ReminderType(str, Enum):
    """Reminder type enum."""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    POSTCARD = "postcard"