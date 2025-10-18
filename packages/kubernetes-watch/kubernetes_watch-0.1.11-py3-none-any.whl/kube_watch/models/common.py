from pydantic import BaseModel, ConfigDict
from humps.camel import case

def to_camel(string):
    if string == "id":
        return "_id"
    if string.startswith("_"):  # "_id"
        return string
    return case(string)

class CamelModel(BaseModel):
    """
    Replacement for pydanitc BaseModel which simply adds a camel case alias to every field
    NOTE: This has been updated for Pydantic 2 to remove some common encoding helpers
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)