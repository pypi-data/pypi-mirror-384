

from pydantic import BaseModel


class A (BaseModel):
    b : int 

class C (BaseModel):
    d : int


g = A | B

