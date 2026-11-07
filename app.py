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
    init_usuarios_table, cadastrar_usuario, autenticar_usuario,
    REGRAS_ZAZA, SORTEIO_EXEMPLO_AULA, EXEMPLOS_AULA_ZAZA,
    conferir_apostas_zaza, resolver_grupo_bicho
)
from sync_engine import sync_latest_results
from ai_engine import generate_ai_predictions, get_puxadas_for_bicho
from auto_pilot import auto_pilot
from grade3x3_engine import gerar_top_k_grade3x3, obter_dados_contexto, build_grade_3x3

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
    tipo: str # "grupo", "dezena", "centena", "milhar", "duque_grupo", "duque_dezena", "terno_grupo", "terno_dezena"
    posicao: Optional[str] = "cabeca" # "cabeca" (1º prêmio) ou "cercado" (1º ao 5º prêmio)
    valor_aposta: Optional[float] = 1.0 # Valor em R$ por bilhete
    apostas: List[str]
    origem_sorteio: Optional[str] = "ultimo" # "ultimo", "aula_zaza", ou "id"
    id_sorteio: Optional[int] = None

class SimularAulaRequest(BaseModel):
    exemplo_id: Optional[str] = None
    tipo: Optional[str] = None
    posicao: Optional[str] = "cabeca"
    valor_aposta: Optional[float] = 10.0
    apostas: Optional[List[str]] = None

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

@app.get("/api/regras-apostas")
def api_regras_apostas():
    return {
        "status": "success",
        "regras": REGRAS_ZAZA,
        "bichos": [
            {
                "grupo": f"{g:02d}",
                "nome": v["nome"],
                "icone": v["icone"],
                "dezenas": v["dezenas"]
            }
            for g, v in sorted(BICHO_INFO.items())
        ],
        "sorteio_aula": SORTEIO_EXEMPLO_AULA,
        "exemplos_aula": EXEMPLOS_AULA_ZAZA
    }

@app.post("/api/simular-aula-zaza")
def api_simular_aula_zaza(req: SimularAulaRequest):
    if req.exemplo_id:
        ex = next((e for e in EXEMPLOS_AULA_ZAZA if e["id"] == req.exemplo_id), None)
        if not ex:
            raise HTTPException(status_code=404, detail="Exemplo da aula não encontrado.")
        res = conferir_apostas_zaza(
            tipo=ex["tipo"],
            posicao=ex["posicao"],
            valor_aposta=float(ex["valor"]),
            apostas=[ex["aposta"]],
            sorteio_alvo=SORTEIO_EXEMPLO_AULA
        )
        res["exemplo_info"] = ex
        return res

    tipo = req.tipo or "grupo"
    pos = req.posicao or "cabeca"
    val = float(req.valor_aposta or 10.0)
    apostas = req.apostas or ["Tigre"]
    return conferir_apostas_zaza(
        tipo=tipo,
        posicao=pos,
        valor_aposta=val,
        apostas=apostas,
        sorteio_alvo=SORTEIO_EXEMPLO_AULA
    )

@app.post("/api/conferir")
def api_conferir(req: ConferirRequest):
    sorteio_alvo = None
    origem_label = ""
    
    if req.origem_sorteio == "aula_zaza":
        sorteio_alvo = SORTEIO_EXEMPLO_AULA
        origem_label = "Exemplo Didático da Aula do Professor Zazá"
    elif req.id_sorteio:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resultados WHERE id_sorteio = ? ORDER BY premio_num ASC", (req.id_sorteio,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if not rows:
            raise HTTPException(status_code=404, detail="Sorteio especificado não encontrado.")
        sorteio_alvo = rows
        origem_label = f"{rows[0]['data']} ({rows[0]['extracao']})"
    else:
        latest = get_latest_draw()
        if not latest:
            sorteio_alvo = SORTEIO_EXEMPLO_AULA
            origem_label = "Exemplo da Aula do Zazá (Base sem sorteios)"
        else:
            sorteio_alvo = latest
            origem_label = f"{latest[0]['data']} ({latest[0]['extracao']})"
            
    try:
        resultado = conferir_apostas_zaza(
            tipo=req.tipo,
            posicao=req.posicao or "cabeca",
            valor_aposta=float(req.valor_aposta or 1.0),
            apostas=req.apostas,
            sorteio_alvo=sorteio_alvo
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    cabeca = resultado["sorteio"][0]
    hits_legado = []
    for d in resultado["detalhes"]:
        if d.get("acertou"):
            hits_legado.append({
                "aposta": d["aposta"],
                "premio": ", ".join(d["premios_atingidos"]),
                "retorno_estimado": d["retorno"]
            })
            
    resultado.update({
        "sorteio_conferido": origem_label,
        "milhar_sorteada": cabeca["milhar"],
        "bicho_sorteado": f"{cabeca['icone']} {cabeca['bicho']}",
        "acertos": hits_legado
    })
    return resultado

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



# ==============================================================================
# MÓDULO GRADE 3X3 TURBO (TOP-K) + PUXADAS & HISTÓRICO 24H
# ==============================================================================
class Grade3x3GerarRequest(BaseModel):
    qtd_cartoes: Optional[int] = 3
    modalidade: Optional[str] = "centena"
    posicao: Optional[str] = "cabeca"
    valor_aposta: Optional[float] = 1.0
    bicho_preferido: Optional[str] = None
    data_alvo: Optional[str] = None

class Grade3x3FilaRequest(BaseModel):
    apostas: List[str]
    tipo: str
    custo_por_rodada: float
    id_sorteio_gatilho: Optional[int] = None
    nome_estrategia: Optional[str] = "Grade 3x3 Turbo (Top-K)"

@app.get("/api/grade-3x3/info")
def api_grade3x3_info(data_alvo: Optional[str] = None):
    ctx = obter_dados_contexto(data_alvo)
    grid = build_grade_3x3(ctx["g1"], ctx["g2"])
    return {
        "status": "success",
        "contexto": ctx,
        "grade_3x3": grid
    }

@app.post("/api/grade-3x3/gerar")
def api_grade3x3_gerar(req: Grade3x3GerarRequest):
    return gerar_top_k_grade3x3(
        qtd_cartoes=req.qtd_cartoes or 3,
        modalidade=req.modalidade or "centena",
        posicao=req.posicao or "cabeca",
        valor_aposta=req.valor_aposta or 1.0,
        bicho_preferido=req.bicho_preferido,
        data_alvo=req.data_alvo
    )

@app.post("/api/grade-3x3/enviar-fila")
def api_grade3x3_enviar_fila(req: Grade3x3FilaRequest):
    return adicionar_aposta_fila(
        nome_estrategia=req.nome_estrategia or "Grade 3x3 Turbo (Top-K)",
        tipo=req.tipo,
        apostas=req.apostas,
        custo_por_rodada=req.custo_por_rodada,
        id_sorteio_gatilho=req.id_sorteio_gatilho
    )

# Montar arquivos estáticos do frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
