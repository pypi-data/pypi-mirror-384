from typing import Dict, Optional
import sys
import os

# Add the parent directory to the path to import rubric
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .rubric import Rubric


class Question:
    """
    Represents a single question with its text and associated rubric.
    """
    def __init__(self, q_id: str, text: str, max_marks: float, rubric: Rubric = None, reference_answer: str = None):
        self.q_id = q_id
        self.text = text
        self.max_marks = max_marks
        self.rubric = rubric if rubric is not None else Rubric([])
        self.reference_answer = reference_answer

    def set_rubric(self, rubric: Rubric) -> None:
        """Set the rubric for this question."""
        if not isinstance(rubric, Rubric):
            raise TypeError("rubric must be an instance of Rubric")
        self.rubric = rubric

    def set_reference_answer(self, reference_answer: str) -> None:
        """Set the reference answer for this question."""
        if not isinstance(reference_answer, str):
            raise TypeError("reference_answer must be a string")
        self.reference_answer = reference_answer

    def __repr__(self):
        return f"Question(\nq_id={self.q_id!r}, \ntext={self.text!r}, \nrubric={self.rubric}, \nreference_answer={self.reference_answer!r})"


class QuestionPaper:
    """
    Represents a question paper containing multiple questions indexed by question ID.
    """
    def __init__(self, subject: str, language: str, class_level: Optional[str] = None):
        self.questions: Dict[str, Question] = {}
        self.subject: str = subject
        self.class_level: str = class_level
        self.language: str = language

    def add_question(self, question: Question) -> None:
        """Add a question to the question paper."""
        if not isinstance(question, Question):
            raise TypeError("question must be an instance of Question")
        self.questions[question.q_id] = question

    def add_rubric(self, question_id: str, rubric: Rubric) -> None:
        """Add a rubric to a specific question."""
        if question_id not in self.questions:
            raise ValueError(f"Question ID '{question_id}' not found in question paper")
        self.questions[question_id].set_rubric(rubric)

    def add_reference_answer(self, question_id: str, reference_answer: str) -> None:
        """Add a reference answer to a specific question."""
        if question_id not in self.questions:
            raise ValueError(f"Question ID '{question_id}' not found in question paper")
        self.questions[question_id].set_reference_answer(reference_answer)

    def get_question(self, question_id: str) -> Question:
        """Get a question by its ID."""
        if question_id not in self.questions.keys():
            raise ValueError(f"Question ID '{question_id}' not found in question paper")
        return self.questions[question_id]

    def get_all_questions(self) -> Dict[str, Question]:
        """Get all questions in the question paper."""
        return self.questions.copy()

    def get_question_ids(self) -> list:
        """Get all question IDs in the question paper."""
        return list(self.questions.keys())

    def get_total_marks(self) -> float:
        """Calculate total marks for all questions in the paper."""
        return sum(question.rubric.total_marks() for question in self.questions.values())

    def __repr__(self):
        return f"QuestionPaper(questions={len(self.questions)})"
