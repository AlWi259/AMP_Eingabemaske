from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class SentimentEnum(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class ClosedQuestions(BaseModel):
    """
    Represents a closed question and its answer, inferred from previous open questions.
    """
    question_id: str = Field(description="ID der geschlossenen Frage.")
    question: str = Field(description="Frage, die auf Basis vorheriger Antworten nicht mehr gestellt werden muss.")
    answer: str = Field(description="Antwort des Nutzers auf diese Frage, abgeleitet aus vorherigen Antworten.")

class QuestionResponse(BaseModel):
    """
    Represents the response for a question step in the interview, including closed questions and the next question to ask.
    """
    closed_questions: list[ClosedQuestions] = Field(description="Liste aller geschlossenen Fragen und deren Antworten.")
    next_question: str = Field(description="Nächste Frage, die dem Nutzer gestellt werden soll.")
    next_question_id: str = Field(description="ID der nächsten zu stellenden Frage.")

class AnswerEvaluation(BaseModel):
    """
    Evaluates the user's answer to determine if the topic is sufficiently covered, if anouther question is needed, or if probing is required.
    """
    topic_covered: bool = Field(description="Entscheidung, ob das Thema ausreichend abgedeckt ist oder nicht.")
    probing_needed: bool = Field(description="Entscheidung, ob eine weitere Vertiefungsfrage gestellt werden soll oder nicht.")
    probing_type: str = Field(description="Erklärung, was für eine Probing-Frage und warum gestellt werden sollte.")
    next_point: str = Field(description="Nächster Punkt, der im Interview behandelt werden soll, falls keine Probingfrage gestellt wird.")

class PsychologicalExpert(BaseModel):
    """
    Contains the psychological expert's analysis and recommendations for the interviewee.
    """
    psychological_analysis: str = Field(description="Einschätzung zur Bereitschaft des Interviewten, weitere Antworten zu geben.")
    psychological_recommendation: str = Field(description="Empfehlung, wie mögliche Folgefragen formuliert werden könnten.")

class ProbingExpert(BaseModel):
    """
    Contains the probing expert's analysis and recommendations for the interviewee.
    """
    probing_type: int = Field(description="Typ der Probingfrage.", examples=["clarification", "depth", "example", "emotional", "reformulation"])

class UseCase(BaseModel):
    """
    Represents a use case for a specific function, including its context and user satisfaction.
    """
    title: str = Field( description="Kurzbezeichnung des Use-Cases")
    description: str = Field(description="Freitext mit max. 250 Zeichen über Ablauf, Nutzen, Probleme")
    primary_benefit: Optional[str] = Field(description="Wichtigste Wirkung, z.B. 'Zeiteinsparung', 'Stressreduktion'")

class InterviewSummaryYgg(BaseModel):
    """
    Represents a summary YGG (knowledge piece) object for a specific function, including analysis and recommendations.
    """
    topic_label: str = Field(description="Menschenesschenlesbare Bezeichnung des Themas")
    usage_context: str = Field(description="Fließtext über Nutzungssituationen, Häufigkeit, Ziele.")
    use_cases: List[UseCase] = Field(description="Liste der Nutzungsszenarien für die Funktion.")
    experience_positive: List[str] = Field(description="Positiv bewertete Aspekte der Funktion")
    experience_negative: List[str] = Field(description="Negativ bewertete Aspekte der Funktion")
    overall_rating: SentimentEnum = Field(description="Gesamturteil")
    adaptions: List[str] = Field(description="Manuelle Anpassungen & Workarounds")
    insights: List[str] = Field(description="Verdichtete Kernerkenntnisse")
    created_at: datetime = Field(default_factory=datetime.now(), description="Zeitstempel der Objekterstellung (ISO-8601)")

class Ygg(BaseModel):
    """
    Represents a single Yggdrasil (Ygg) knowledge snippet extracted from the interview context.
    """
    title: str = Field(description="Titel des Gedankenbausteins – kurz, konkret und präzise.")
    content: str = Field(description="Inhalt des Gedankenbausteins – verständlich, vollständig und nützlich.")

class YggList(BaseModel):
    """
    Contains a list of all extracted Ygg knowledge snippets from the interview context.
    """
    ygg_list: list[Ygg] = Field("Liste aller extrahierten Gedankenbausteine.")