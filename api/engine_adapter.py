"""
Adaptador entre la REST API y el motor congelado de Fase 3.
Este archivo permite exponer el motor sin modificar
scripts/decision_engine.py ni los demás componentes
congelados.
"""
import sys
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from decision_engine import evaluate_expense  # noqa: E402
def evaluate(
    expense: dict[str, Any],
) -> dict[str, Any]:
    """Ejecuta el motor determinístico sin alterar su lógica."""
    return evaluate_expense(expense)
