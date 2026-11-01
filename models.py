"""
PlanGenius AI - Data Models & Validation Layer
Leverages Pydantic v2 for robust schema definition, strict type checking,
and automatic request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class BudgetItemModel(BaseModel):
    """Schema for itemized event expenses."""
    id: Optional[str] = Field(default=None, description="Unique budget item identifier")
    category: str = Field(..., description="Expense category e.g., Venue & Rentals, Catering & Bar")
    name: str = Field(..., description="Item or service description")
    estimated: float = Field(default=0.0, ge=0, description="Estimated budget cost")
    actual: float = Field(default=0.0, ge=0, description="Actual amount paid to date")
    status: str = Field(default="pending", description="Payment status: pending, deposit_paid, paid")
    notes: Optional[str] = Field(default="", description="Additional billing or contract notes")


class TimelineMilestoneModel(BaseModel):
    """Schema for phased milestone roadmap deadlines."""
    id: Optional[str] = Field(default=None, description="Milestone identifier")
    phase: str = Field(..., description="Planning phase e.g., 9-12 Months Out, Day Of")
    task: str = Field(..., description="Milestone task description")
    dueDate: Optional[str] = Field(default="", description="Target due date (YYYY-MM-DD)")
    completed: bool = Field(default=False, description="Whether the milestone is completed")


class RunOfShowModel(BaseModel):
    """Schema for hour-by-hour day-of event schedule."""
    id: Optional[str] = Field(default=None, description="Schedule item identifier")
    time: str = Field(..., description="Time string e.g., 05:30 PM")
    activity: str = Field(..., description="Activity name e.g., Ceremony Processional")
    responsible: Optional[str] = Field(default="Lead Coordinator", description="Lead point of contact")
    location: Optional[str] = Field(default="Main Venue", description="Specific venue zone")


class VendorModel(BaseModel):
    """Schema for event vendors and suppliers."""
    id: Optional[str] = Field(default=None, description="Vendor identifier")
    category: str = Field(..., description="Vendor category e.g., Catering, Photography")
    name: str = Field(..., description="Business or vendor name")
    contact: Optional[str] = Field(default="", description="Contact email address")
    phone: Optional[str] = Field(default="", description="Contact telephone number")
    status: str = Field(default="to_research", description="Booking status")
    quoted: float = Field(default=0.0, ge=0, description="Quoted or estimated price")
    notes: Optional[str] = Field(default="", description="Contract notes")


class EventPlanModel(BaseModel):
    """Master schema for an end-to-end event plan."""
    id: Optional[str] = Field(default=None, description="Unique event identifier")
    title: str = Field(..., min_length=1, description="Event title")
    eventType: str = Field(default="wedding", description="Event type: wedding, birthday, community")
    subType: Optional[str] = Field(default="", description="Style preset or theme sub-type")
    date: str = Field(..., description="Event date (YYYY-MM-DD)")
    location: str = Field(default="TBD", description="Event location or venue")
    guestCount: int = Field(default=50, ge=1, description="Estimated guest count")
    totalBudget: float = Field(default=10000.0, ge=0, description="Total budget amount")
    currency: str = Field(default="$", description="Currency symbol: $, €, £, ₹, C$, A$")
    theme: Optional[str] = Field(default="", description="Aesthetic theme or vibe")
    priorities: Optional[str] = Field(default="", description="Key priorities for the event")
    dietaryNotes: Optional[str] = Field(default="", description="Dietary restrictions or notes")
    budgetItems: List[BudgetItemModel] = Field(default_factory=list, description="Itemized budget items")
    timelineMilestones: List[TimelineMilestoneModel] = Field(default_factory=list, description="Milestone roadmap")
    runOfShow: List[RunOfShowModel] = Field(default_factory=list, description="Day-of run-of-show schedule")
    vendors: List[VendorModel] = Field(default_factory=list, description="Vendor list")
    creativeIdeas: List[str] = Field(default_factory=list, description="Curated creative concepts")
    colorPalette: List[str] = Field(default_factory=list, description="Hex color codes palette")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Event title cannot be empty or whitespace")
        return stripped


# API Request Payload Schemas
class GeneratePlanRequest(BaseModel):
    """Request payload for /api/generate endpoint."""
    provider: str = Field(default="groq", description="AI provider: groq, gemini, or local")
    apiKey: Optional[str] = Field(default="", description="Provider API key")
    model: Optional[str] = Field(default="", description="Target LLM model ID")
    params: Dict[str, Any] = Field(..., description="Event parameters for generation")
    autoSave: bool = Field(default=True, description="Whether to auto-save to storage")


class ChatMessage(BaseModel):
    """Single chat message in conversation history."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    """Request payload for /api/chat Co-pilot endpoint."""
    messages: List[ChatMessage] = Field(default_factory=list, description="Message history")
    currentEvent: Optional[Dict[str, Any]] = Field(default=None, description="Active event context")
    provider: str = Field(default="groq", description="AI provider: groq, gemini, or local")
    apiKey: Optional[str] = Field(default="", description="Provider API key")
    model: Optional[str] = Field(default="", description="Target LLM model ID")


class VendorEmailRequest(BaseModel):
    """Request payload for /api/vendor-email endpoint."""
    vendor: Dict[str, Any] = Field(..., description="Vendor object")
    event: Dict[str, Any] = Field(..., description="Event plan object")
    provider: str = Field(default="groq", description="AI provider")
    apiKey: Optional[str] = Field(default="", description="Provider API key")
    model: Optional[str] = Field(default="", description="Target LLM model ID")


class ExtraIdeasRequest(BaseModel):
    """Request payload for /api/extra-ideas endpoint."""
    category: str = Field(default="general", description="Idea category")
    event: Dict[str, Any] = Field(..., description="Event plan object")
    provider: str = Field(default="groq", description="AI provider")
    apiKey: Optional[str] = Field(default="", description="Provider API key")
    model: Optional[str] = Field(default="", description="Target LLM model ID")
