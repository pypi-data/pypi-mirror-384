from pydantic import BaseModel, Field
from typing import List, Optional, Any


class RiskCategory(BaseModel):
    """Describes a Risk Category referenced in a risk Scorecard

    Parameters
    ----------
    name : str
        Name of the category
    score: float
        Numeric score of the category
    max_score : float
        The maximum score achievable in this category
    risks: List[str]
        The list of risk factors identified in this category

    """
    name: str = Field(description="Name of the risk category")
    score: float = Field(description="Score of the risk category")
    max_score: float = Field(description="Max possible score for the risk category", default=5.0)
    risks: List[str] = Field(description="List of identified risk factors")


class Scorecard(BaseModel):
    """The risk assessment scorecard for a Session

    Our risk scorecard is based on the Responsible Forecast framework (Rostami-Tabar et al., 2024).

    Citations
    ---------
    Rostami-Tabar, B., Greene, T., Shmueli, G., & Hyndman, R. J.
    (2024). Responsible forecasting: identifying and typifying forecasting harms.
    arXiv preprint arXiv:2411.16531.

    Parameters
    ----------
    categories : List[RiskCategory]
        A list of categories
    assessment: str
        Overall assessment of the risk for the session
    recommendation : str
        Recommendations and risk mitigation strategies for risks highlighted in the assessment


    Attributes
    ----------
    categories : List[RiskCategory]
        A list of categories
    assessment: str
        Overall assessment of the risk for the session
    recommendation : str
        Recommendations and risk mitigation strategies for risks highlighted in the assessment

    """
    categories: List[RiskCategory] = Field(description="Risk categories")
    assessment: str = Field(description="Overall Assessment")
    recommendation: str = Field(description="Mitigation Recommendations")


