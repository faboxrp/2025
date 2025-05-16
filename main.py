from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import math  # Necesario para verificar si Aci es > 0 para evitar división por cero

# Inicializa FastAPI
app = FastAPI(
    title="Calculadora Resistencia Mampostería Confinada",
    description="Una aplicación web para calcular la resistencia a compresión de mampostería confinada.",
    version="1.0.0"
)

# Configura Jinja2 para cargar plantillas HTML desde el directorio 'templates'
templates = Jinja2Templates(directory="templates")


def perform_calculations(H: float, L: float, t: float, b_conf: float, h_conf: float, Ast: float, Re: float):
    """
    Realiza los cálculos de resistencia de la mampostería confinada.
    """
    results = {}

    # Cálculos
    # Aci: Área de la sección transversal de una columna de confinamiento
    # área de confinamiento en cm² (1 m² = 1e4 cm²)
    Aci = b_conf * h_conf * 1e4

    # Amd: Área efectiva de mampostería en el muro
    # área efectiva de mampostería en cm² (1 m² = 10,000 cm²)
    Amd = L * t * 1e4

    Pnc = Re * Aci / 1000        # carga de una columna en toneladas
    Pnct = 2 * Pnc               # carga de dos columnas
    Pnd = Re * Amd / 1000        # carga de mampostería
    Pr = Pnct + Pnd              # carga total

    results["Aci"] = f"{Aci:.2f}"
    results["Amd"] = f"{Amd:.2f}"
    results["Pnc"] = f"{Pnc:.3f}"
    results["Pnct"] = f"{Pnct:.3f}"
    results["Pnd"] = f"{Pnd:.3f}"
    results["Pr"] = f"{Pr:.3f}"

    # Verificaciones
    h_t = H / t if t > 0 else 0.0  # Evitar división por cero si t es 0
    limite_esbeltez = 30  # Límite de ejemplo, puede variar según normativa
    cumple_esbeltez_bool = h_t <= limite_esbeltez if t > 0 else False

    results["h_t"] = f"{h_t:.2f}"
    results["cumple_esbeltez"] = f"Cumple (≤ {limite_esbeltez})" if cumple_esbeltez_bool else f"No cumple (> {limite_esbeltez} o t=0) - revisar límite normativo"
    if t == 0:
        results["cumple_esbeltez"] = "Espesor del muro (t) no puede ser cero."

    if Aci > 0:
        cuantia = Ast / Aci
        limite_cuantia = 0.0025  # Valor típico mínimo de cuantía de refuerzo
        cumple_cuantia_bool = cuantia >= limite_cuantia
        results["cuantia"] = f"{cuantia:.5f} ({cuantia*100:.3f}%)"
        results["cumple_cuantia"] = f"Cumple (≥ {limite_cuantia*100:.2f}%)" if cumple_cuantia_bool else f"No cumple (< {limite_cuantia*100:.2f}%) - revisar mínimo normativo"
    else:
        results["cuantia"] = "N/A (Área de confinamiento Aci es 0)"
        results["cumple_cuantia"] = "No se puede calcular (Aci es 0)"
        # Si Aci es 0, Pnc y Pnct serán 0, lo que es consistente.

    return results


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    """
    Muestra el formulario de ingreso de datos.
    """
    return templates.TemplateResponse("index.html", {"request": request, "results": None, "inputs": None})


@app.post("/", response_class=HTMLResponse)
async def calculate_resistance_from_form(
    request: Request,
    H: float = Form(...),
    L: float = Form(...),
    t: float = Form(...),
    b_conf: float = Form(...),
    h_conf: float = Form(...),
    Ast: float = Form(...),
    Re: float = Form(...)
):
    """
    Recibe los datos del formulario, realiza los cálculos y muestra los resultados.
    """
    # Validar que los valores no sean negativos donde no tiene sentido
    if H <= 0 or L <= 0 or t <= 0 or b_conf <= 0 or h_conf <= 0 or Ast < 0 or Re <= 0:
        error_message = "Todos los valores dimensionales y de resistencia deben ser positivos. El área de acero (Ast) puede ser cero."
        if Ast < 0:
            error_message = "El área de acero (Ast) no puede ser negativa."

        input_data_for_template = {
            "H": H, "L": L, "t": t,
            "b_conf": b_conf, "h_conf": h_conf,
            "Ast": Ast, "Re": Re
        }
        return templates.TemplateResponse("index.html", {
            "request": request,
            "results": None,
            "inputs": input_data_for_template,
            "error": error_message
        })

    calculation_results = perform_calculations(
        H, L, t, b_conf, h_conf, Ast, Re)

    input_data_for_template = {
        "H": H, "L": L, "t": t,
        "b_conf": b_conf, "h_conf": h_conf,
        "Ast": Ast, "Re": Re
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "results": calculation_results,
        # Para rellenar el formulario con los valores ingresados
        "inputs": input_data_for_template
    })

# Si quieres ejecutar esto directamente con `python main.py` para desarrollo local (aunque uvicorn es preferido)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
