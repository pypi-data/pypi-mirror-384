from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, root_validator

# Define a generic type variable
T = TypeVar("T")

# Create a generic response model with a custom constructor
class ResponseModel(BaseModel, Generic[T]):
    screen_id: Optional[str] = None
    status: str = "200"
    message: str = "success"
    data: Optional[T] = None


    def set_response(self, screen_id: Optional[str] = None, status: Optional[str] = None, 
                     message: Optional[str] = None, data: Optional[T] = None):
        """Setter method to update response attributes"""
        if screen_id is not None:
            self.screen_id = screen_id
        if status is not None:
            self.status = status
        if message is not None:
            self.message = message
        if data is not None:
            self.data = data
        super().__init__(screen_id=screen_id, status=status, message=message, data=data)

# Example usage
response = ResponseModel(screen_id="home", status="success", message="Operation completed", data={"id": 1, "name": "Arjun"})
print(response)

# Updating response using setter method
response.set_response(message="Updated successfully", status="updated")
print(response)