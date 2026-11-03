from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os

from database import get_stats, get_latest_draw, query_results, BICHO_INFO
from sync_engine import sync_latest_results
from ai_engine import generate_ai_predictions, get_puxadas_for_bicho

app = FastAPI(title="DEU NO POSTE TURBO AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConferirRequest(BaseModel):
    tipo: str # "milhar", "centena", "dezena", "grupo"
    apostas: List[str]
    id_sorteio: Optional[int] = None

class LoginRequest(BaseModel):
    username: Optional[str] = "admin"
    password: str

ADMIN_PASSWORD = "@As975109"

@app.post("/api/auth/login")
def api_auth_login(req: LoginRequest):
    if req.password.strip() == ADMIN_PASSWORD:
        return {
            "status": "success",
            "message": "Autenticado com sucesso",
            "token": "tok_admin_deu_no_poste_pro_2026",
            "user": req.username or "Admin",
            "role": "admin"
        }
    raise HTTPException(status_code=401, detail="Senha incorreta! Acesso não autorizado.")

@app.get("/api/status")
def api_status():
    return get_stats()

@app.get("/api/bichos")
def api_bichos():
    return [
        {"grupo": f"{g:02d}", "nome": v["nome"], "icone": v["icone"], "dezenas": v["dezenas"]}
        for g, v in BICHO_INFO.items()
    ]

@app.get("/api/ultimo-sorteio")
def api_ultimo_sorteio():
    return get_latest_draw()

@app.get("/api/resultados")
def api_resultados(
    data_ini: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    extracao: Optional[str] = Query(None),
    bicho: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
    dezena: Optional[str] = Query(None),
    centena: Optional[str] = Query(None),
    milhar: Optional[str] = Query(None),
    premio_num: Optional[int] = Query(None),
    so_cabeca: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    return query_results(
        data_ini=data_ini,
        data_fim=data_fim,
        extracao=extracao,
        bicho=bicho,
        grupo=grupo,
        dezena=dezena,
        centena=centena,
        milhar=milhar,
        premio_num=premio_num,
        so_cabeca=so_cabeca,
        page=page,
        page_size=page_size
    )

@app.get("/api/predicoes")
def api_predicoes():
    return generate_ai_predictions()

@app.get("/api/puxadas")
def api_puxadas(bicho: str = Query(..., description="Nome do animal para consulta")):
    return get_puxadas_for_bicho(bicho)

@app.post("/api/sync")
def api_sync():
    return sync_latest_results()

@app.post("/api/conferir")
def api_conferir(req: ConferirRequest):
    latest_draw = get_latest_draw()
    if not latest_draw:
        raise HTTPException(status_code=400, detail="Nenhum sorteio registrado para conferência.")
        
    cabeca = latest_draw[0]
    hits = []
    
    apostas_clean = [a.strip() for a in req.apostas if a.strip()]
    
    for aposta in apostas_clean:
        hit = False
        premio_atingido = ""
        retorno = 0
        
        if req.tipo == "milhar":
            if aposta == cabeca["milhar"]:
                hit = True
                premio_atingido = "1º Prêmio (Cabeça) - MILHAR SECA!"
                retorno = 4578.00
            else:
                for r in latest_draw[1:5]:
                    if aposta == r["milhar"]:
                        hit = True
                        premio_atingido = f"{r['premio']} Prêmio (Cercado) - Milhar"
                        retorno = 800.00
                        break
        elif req.tipo == "centena":
            if aposta == cabeca["centena"]:
                hit = True
                premio_atingido = "1º Prêmio (Cabeça) - CENTENA SECA!"
                retorno = 578.00
            else:
                for r in latest_draw[1:5]:
                    if aposta == r["centena"]:
                        hit = True
                        premio_atingido = f"{r['premio']} Prêmio (Cercado) - Centena"
                        retorno = 100.00
                        break
        elif req.tipo == "dezena":
            if aposta == cabeca["dezena"]:
                hit = True
                premio_atingido = "1º Prêmio (Cabeça) - DEZENA SECA!"
                retorno = 60.00
        elif req.tipo == "grupo":
            g_str = f"{int(aposta):02d}" if aposta.isdigit() else aposta
            if g_str == cabeca["grupo"] or aposta.lower() == cabeca["bicho"].lower():
                hit = True
                premio_atingido = "1º Prêmio (Cabeça) - GRUPO SECO!"
                retorno = 18.00
                
        if hit:
            hits.append({
                "aposta": aposta,
                "premio": premio_atingido,
                "retorno_estimado": retorno
            })
            
    total_premio = sum(h["retorno_estimado"] for h in hits)
    return {
        "sorteio_conferido": f"{cabeca['data']} ({cabeca['extracao']})",
        "milhar_sorteada": cabeca["milhar"],
        "bicho_sorteado": f"{cabeca['icone']} {cabeca['bicho']}",
        "total_apostas": len(apostas_clean),
        "total_acertos": len(hits),
        "acertos": hits,
        "premio_total": total_premio
    }

# Montar arquivos estáticos do frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
