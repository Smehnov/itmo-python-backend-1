from api import SimpleJsonApi, JSONResponse, Query, HTTPException   
from typing import Annotated
import math


app = SimpleJsonApi()


@app.get("/factorial")
async def get_factorial(n: Annotated[int, Query()]) -> JSONResponse:
    if n < 0:
        raise HTTPException(
                    status_code=400,
                    detail="Invalid value for n, must be non-negative",
                )

    result = math.factorial(n)

    return JSONResponse({"result": result})


@app.get("/fibonacci/{n}")
async def get_fibonacci(n: int) -> JSONResponse:
    if n < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid value for n, must be non-negative",
        )
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b

    return JSONResponse({"result": b})


@app.get("/mean")
async def get_mean(data: list[float]) -> JSONResponse:
    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid value for body, must be non-empty array of floats",
        )


    result = sum(data) / len(data)

    return JSONResponse({"result": result})

