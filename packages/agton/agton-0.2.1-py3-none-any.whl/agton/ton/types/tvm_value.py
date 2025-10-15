from agton.ton import Cell, Slice, Builder
from agton.ton.types.continuation import Continuation

TvmValue = (
    None 
    | int 
    | Cell 
    | Slice 
    | Builder
    | Continuation
    | tuple["TvmValue", ...]
)
