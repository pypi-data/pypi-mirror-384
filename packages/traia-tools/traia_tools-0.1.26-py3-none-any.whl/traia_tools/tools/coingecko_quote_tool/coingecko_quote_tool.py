import requests
from typing import Type
from pydantic import BaseModel, PrivateAttr
from crewai.tools import BaseTool


class CoingeckoUniversalQuoteToolSchema(BaseModel):
    token_id: str | None = None
    amount: float = 1.0


class CoingeckoUniversalQuoteTool(BaseTool):
    name: str = "coingecko_universal_quote_tool"
    description: str = "A tool for fetching token prices from Coingecko API."
    args_schema: Type[BaseModel] = CoingeckoUniversalQuoteToolSchema
    _base_url: str = PrivateAttr(default="https://api.coingecko.com/api/v3")
    
    def __init__(self, **data):
        super().__init__(**data)

    def _run(self, token_id: str = None, amount: float = 1.0):
        """
        Fetches the price for a token.

        Args:
            token_id (str, optional): The token ID (e.g., "bitcoin").
            amount (float, optional): The quantity of the token.

        Returns:
            dict: A dictionary containing the token price.
        """
        try:
            if not token_id:
                return {"error": "Invalid input. Provide either a token_id."}

            endpoint = f"{self._base_url}/simple/price?ids={token_id}&vs_currencies=usd"
            response = requests.get(endpoint)
            response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            data = response.json()

            price = data.get(token_id, {}).get("usd")

            if price is not None:
                return {"token": token_id, "price": price}
            else:
                return {"error": "Price data unavailable."}

        except requests.RequestException as e:
            return {"error": f"Error fetching data: {str(e)}"}


if __name__ == "__main__":

    """
    Simple test function for CoingeckoUniversalQuoteTool.
    """
    tool_instance = CoingeckoUniversalQuoteTool()

    # Test with a known token_id
    result = tool_instance.run(token_id="bitcoin", amount=2.5)
    print("Result for bitcoin price query:", result)
