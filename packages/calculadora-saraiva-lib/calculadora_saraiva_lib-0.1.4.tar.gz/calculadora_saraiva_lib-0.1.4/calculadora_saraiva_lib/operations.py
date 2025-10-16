def add(a: float, b: float) -> float:
    """
    Retorna a soma de dois números.

    Args:
        a (float): Primeiro número.
        b (float): Segundo número.

    Returns:
        float: Resultado da soma (a + b).
    """
    return a + b

def subtract(a: float, b: float) -> float:
    """
    Retorna a subtração de dois números.

    Args:
        a (float): Primeiro número.
        b (float): Segundo número.

    Returns:
        float: Resultado da subtração (a - b).
    """
    return a - b

def multiply(a: float, b: float) -> float:
    """
    Retorna a multiplicação de dois números.

    Args:
        a (float): Primeiro número.
        b (float): Segundo número.

    Returns:
        float: Resultado da multiplicação (a * b).
    """
    return a * b

def divide(a: float, b: float) -> float:
    """
    Retorna a divisão de dois números.

    Args:
        a (float): Numerador.
        b (float): Denominador.

    Raises:
        ValueError: Se o denominador `b` for zero.

    Returns:
        float: Resultado da divisão (a / b).
    """
    if b == 0:
        raise ValueError("Divisão por zero não é permitida.")
    return a / b