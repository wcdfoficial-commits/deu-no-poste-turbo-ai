import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

from database import (
    get_connection,
    get_latest_draw,
    registrar_sugestoes_ia,
    auditar_sugestoes_pendentes,
    obter_metricas_assertividade_longo_prazo
)
from sync_engine import sync_latest_results
from ai_engine import generate_ai_predictions

class AutoPilotService:
    def __init__(self, interval_seconds: int = 120):
        self.interval = interval_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.total_runs = 0
        self.last_check_time: Optional[str] = None
        self.last_event: str = "Iniciando serviço do Piloto Automático..."
        self.proxima_extracao: str = self._calcular_proxima_extracao()
        
    def _calcular_proxima_extracao(self) -> str:
        now = datetime.now()
        h = now.hour
        m = now.minute
        t_val = h * 60 + m
        
        # Horários RJ: PPT (09:20), PTM (11:20), PT (14:20), PTV (16:00), PTN (18:20), CORUJA (21:20)
        if t_val < 9 * 60 + 20:
            return "PPT (09:20)"
        elif t_val < 11 * 60 + 20:
            return "PTM (11:20)"
        elif t_val < 14 * 60 + 20:
            return "PT (14:20)"
        elif t_val < 16 * 60:
            return "PTV (16:00)"
        elif t_val < 18 * 60 + 20:
            return "PTN (18:20)"
        elif t_val < 21 * 60 + 20:
            return "CORUJA (21:20)"
        else:
            return "PPT (09:20 - Amanhã)"

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True, name="AutoPilotThread")
        self.thread.start()
        print("[AutoPilot] 🚀 Piloto Automático ativado com sucesso em segundo plano!")

    def stop(self):
        self.running = False

    def _loop(self):
        # Execução inicial imediata
        time.sleep(2)
        self.executar_ciclo()
        
        while self.running:
            time.sleep(self.interval)
            if self.running:
                try:
                    self.executar_ciclo()
                except Exception as e:
                    print(f"[AutoPilot] ❌ Erro no ciclo de varredura: {e}")

    def executar_ciclo(self) -> Dict[str, Any]:
        self.total_runs += 1
        self.last_check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.proxima_extracao = self._calcular_proxima_extracao()
        
        # 1. Sincronizar resultados com a web
        res_sync = sync_latest_results()
        novos = res_sync.get("novos_registros", 0)
        
        # 2. Auditar sugestões pendentes
        auditados = auditar_sugestoes_pendentes()
        
        # 3. Se houve novo sorteio ou se não há sugestão registrada para o último sorteio
        lat = get_latest_draw()
        if lat:
            cabeca = lat[0]
            # Gerar novas previsões da IA
            predicoes = generate_ai_predictions()
            if predicoes.get("status") == "success":
                registrar_sugestoes_ia(cabeca, predicoes)
                
        # 4. Registrar log
        msg = f"Varredura #{self.total_runs}: {novos} novos registros. {len(auditados)} auditorias processadas."
        self.last_event = msg
        
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO log_automacao_scheduler (
                data_hora, tipo_evento, sorteio_detectado, novos_registros, assertividade_auditada, status, mensagem
            ) VALUES (?, 'VARREDURA_AUTO', ?, ?, ?, 'OK', ?)
        """, (
            self.last_check_time,
            f"{lat[0]['data']} {lat[0]['extracao']}" if lat else "",
            novos,
            f"{len(auditados)} auditados",
            msg
        ))
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "total_runs": self.total_runs,
            "novos_registros": novos,
            "auditorias_processadas": len(auditados),
            "proxima_extracao": self.proxima_extracao,
            "ultimo_sorteio": f"{lat[0]['extracao']} {lat[0]['horario']} ({lat[0]['bicho']})" if lat else "",
            "timestamp": self.last_check_time
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "ativo": self.running,
            "intervalo_segundos": self.interval,
            "total_varreduras": self.total_runs,
            "ultima_checagem": self.last_check_time or "Aguardando primeiro ciclo...",
            "ultimo_evento": self.last_event,
            "proxima_extracao": self._calcular_proxima_extracao(),
            "status_operacional": "🟢 OPERACIONAL - MONITORAMENTO CONTÍNUO ATIVO" if self.running else "🔴 PAUSADO"
        }

# Instância Singleton
auto_pilot = AutoPilotService(interval_seconds=180)
