from pydantic import BaseModel, model_validator


class WeaknessBase(BaseModel):
    """Base model with common fields for all models"""

    @model_validator(mode='before')
    @classmethod
    def handle_inconsistent_structure(cls, data):
        """Handle inconsistent XML structure by normalizing data"""
        if isinstance(data, list):
            # If we get a list but expect a dict, use the first item
            if data:
                return data[0]
            return {}
        return data
