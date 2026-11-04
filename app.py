from fastapi import FastAPI, Query, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import secrets

from database import (
    get_stats, get_latest_draw, query_results, BICHO_INFO, get_connection,
    adicionar_aposta_fila, listar_fila_apostas, remover_aposta_fila,
    obter_sorteios_posteriores, conferir_aposta_ciclo, obter_estatisticas_ciclos,
    obter_metricas_assertividade_longo_prazo,
    init_usuarios_table, cadastrar_usuario, autenticar_usuario
)
from sync_engine import sync_latest_results
from ai_engine import generate_ai_predictions, get_puxadas_for_bicho
from auto_pilot import auto_pilot

app = FastAPI(title="DEU NO POSTE TURBO AI", version="2.0")

@app.on_event("startup")
def startup_event():
    init_usuarios_table()
    auto_pilot.start()

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

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
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

@app.post("/api/auth/login")
def api_auth_login(req: LoginRequest):
    user = autenticar_usuario(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário/e-mail ou senha incorretos.")
    
    token = f"tok_{user['role']}_{user['username']}_{secrets.token_hex(8)}"
    return {
        "status": "success",
        "message": f"Bem-vindo(a), {user['username']}!",
        "token": token,
        "user": user["username"],
        "role": user["role"],
        "plan": user.get("plan", "vip")
    }

@app.post("/api/auth/register")
def api_auth_register(req: RegisterRequest):
    try:
        user = cadastrar_usuario(req.username, req.email, req.password)
        token = f"tok_user_{user['username']}_{secrets.token_hex(8)}"
        return {
            "status": "success",
            "message": "Conta criada com sucesso! Acesso liberado ao Terminal.",
            "token": token,
            "user": user["username"],
            "role": user["role"],
            "plan": user["plan"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

class FilaAddRequest(BaseModel):
    nome_estrategia: str
    tipo: str
    apostas: List[str]
    custo_por_rodada: float
    id_sorteio_gatilho: Optional[int] = None

class FilaConferirRequest(BaseModel):
    id_sorteio_alvo: Optional[int] = None

@app.get("/api/fila")
def api_listar_fila():
    return listar_fila_apostas()

@app.post("/api/fila/adicionar")
def api_adicionar_fila(req: FilaAddRequest):
    return adicionar_aposta_fila(
        nome_estrategia=req.nome_estrategia,
        tipo=req.tipo,
        apostas=req.apostas,
        custo_por_rodada=req.custo_por_rodada,
        id_sorteio_gatilho=req.id_sorteio_gatilho
    )

@app.delete("/api/fila/{id_aposta}")
def api_remover_fila(id_aposta: int):
    sucesso = remover_aposta_fila(id_aposta)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Aposta não encontrada na fila.")
    return {"status": "success", "mensagem": "Aposta removida da fila com sucesso."}

@app.get("/api/fila/{id_aposta}/sorteios-posteriores")
def api_sorteios_posteriores(id_aposta: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_sorteio_gatilho FROM fila_apostas WHERE id_aposta = ?", (id_aposta,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Aposta não encontrada.")
    return obter_sorteios_posteriores(row["id_sorteio_gatilho"])

@app.post("/api/fila/{id_aposta}/conferir")
def api_conferir_ciclo(id_aposta: int, req: Optional[FilaConferirRequest] = None):
    try:
        id_alvo = req.id_sorteio_alvo if req else None
        return conferir_aposta_ciclo(id_aposta, id_sorteio_alvo=id_alvo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/ciclos/estatisticas")
def api_estatisticas_ciclos():
    return obter_estatisticas_ciclos()

@app.get("/api/autopilot/status")
def api_autopilot_status():
    return auto_pilot.get_status()

@app.post("/api/autopilot/executar")
def api_autopilot_executar():
    return auto_pilot.executar_ciclo()

@app.get("/api/assertividade/monitoramento")
def api_assertividade_monitoramento():
    return obter_metricas_assertividade_longo_prazo(limite=30)

# Montar arquivos estáticos do frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
