from typing import Dict, List, Optional
import pandas as pd

from ..metric.reformulation import create_reformulations
from ..metric.ter_computation import compute_scores

from ..config import get_api_key, require_api_key, MODELS_CONFIG

class Scorer:
    """
    A class to handle scoring and reformulation tasks for a dataset.

    Attributes:
        df (pd.DataFrame): The dataset to process.
        version (Dict[str, str]): Configuration version details.
        api_key (Optional[str]): API key for the reformulation models.
        model (Dict[str, str]): Model configuration details.
        results (Dict[str, float]): Results of the scoring process.
    """

    def __init__(self, df: pd.DataFrame, version: Dict[str, str], api_key: Optional[str] = None):
        """
        Initialize the Scorer with a dataset, version configuration, and optional API key.

        Args:
            df (pd.DataFrame): The dataset to process.
            version (Dict[str, str]): Configuration version details.
            api_key (Optional[str]): API key for accessing external services.

        Raises:
            ValueError: If the specified model in version is not available in MODELS_CONFIG.
        """
        self.version = version
        if self.version['REFORMULATION_MODEL'] not in MODELS_CONFIG:
            raise ValueError(f"Invalid model: {self.version['REFORMULATION_MODEL']}. Use get_available_models() to see valid options.")
        self.model = MODELS_CONFIG[self.version['REFORMULATION_MODEL']]
        self.api_key = api_key or get_api_key(self.model["api"])
        self.df = df
        self.results: Dict[str, float] = {}

    def reformulation(self) -> None:
        """
        Perform reformulation on the hypothesis using the specified model and method.

        Returns:
            None
        """
        api_key = self.api_key or require_api_key(self.model["api"])
        self.df = create_reformulations(self.df, self.version, api_key)

    def scoring(self) -> None:
        """
        Compute scores and store the results.

        Returns:
            None
        """
        self.df = compute_scores(self.df, self.version)
        results = {
            'average_score': self.df['score'].mean()
        }
        if self.version['CODE_VERSION'] in ["2", "3"]:
            results['average_cor_score'] = self.df['cor_score'].mean()
            results['average_ot_score'] = self.df['ot_score'].mean()
        self.results = results

    def save(self, path: str) -> None:
        """
        Save the processed dataset to a CSV file.

        Args:
            path (str): The file path to save the dataset.

        Returns:
            None
        """
        self.df.to_csv(path, index=False)

    def get_available_models(self) -> List[str]:
        """
        Get a list of the available models for reformulation.

        Returns:
            List[str]: A list of model names.
        """
        return list(MODELS_CONFIG.keys())