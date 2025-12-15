from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import pandas as pd
import requests
import time
import re
import json
import io
from typing import Tuple

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class ApiConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    api_key_intelipost: str
    sobrepreco_padrao: float = 135.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ApiConfigCreate(BaseModel):
    api_key_intelipost: str
    sobrepreco_padrao: float = 135.0

class DeparaMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mappings: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProcessingHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: str
    arquivo_entrada: str
    arquivo_saida: Optional[str] = None
    status: str
    total_linhas: int = 0
    linhas_processadas: int = 0
    linhas_com_erro: int = 0
    logs: List[str] = Field(default_factory=list)
    erro_msg: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

# ============ HELPER FUNCTIONS ============

def to_float(x):
    if pd.isna(x):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(",", ".").replace("\u200b", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None

def normalize_cep(val):
    s = re.sub(r"\D", "", str(val) if val is not None else "")
    if len(s) < 8:
        s = s.zfill(8)
    return s if len(s) == 8 else None

def extract_messages(data_or_text):
    try:
        if isinstance(data_or_text, str):
            return data_or_text[:500]
        data = data_or_text or {}
        msgs = data.get("messages") or data.get("message") or []
        if isinstance(msgs, dict):
            msgs = [msgs]
        out = []
        for m in msgs:
            if isinstance(m, dict):
                picked = []
                for k in ("text", "message", "description", "detail", "error", "cause", "type", "id"):
                    if k in m and m[k]:
                        picked.append(str(m[k]))
                out.append(" - ".join(picked) if picked else json.dumps(m, ensure_ascii=False))
            else:
                out.append(str(m))
        return " | ".join([s for s in out if s])[:1000] if out else ""
    except Exception:
        try:
            return json.dumps(data_or_text, ensure_ascii=False)[:500]
        except Exception:
            return str(data_or_text)[:500]

def pick_column(cols, *candidates):
    low_map = {c.strip().lower(): c for c in cols}
    for cand in candidates:
        key = cand.strip().lower()
        if key in low_map:
            return low_map[key]
    for cand in candidates:
        key = cand.strip().lower()
        for low, original in low_map.items():
            if key in low:
                return original
    return None

# ============ INTELIPOST LOGIC ============

async def process_cotacao_intelipost(
    df: pd.DataFrame,
    api_key: str,
    sobrepreco: float,
    depara_map: Dict[str, Dict[str, str]]
) -> Tuple[pd.DataFrame, List[str]]:
    logs = []
    logs.append(f"[INFO] Iniciando processamento de {len(df)} linhas")
    
    depara_available = len(depara_map) > 0
    if depara_available:
        logs.append(f"[INFO] DE-PARA carregado com {len(depara_map)} mapeamentos")
    
    df.columns = [c.strip().lower() for c in df.columns]
    
    for nome in ["est", "estado", "uf"]:
        if nome in df.columns:
            df = df.drop(columns=[nome])
            break
    
    colunas_numericas = ["peso", "precoproduto", "comprimento", "altura", "largura"]
    obrigatorias = ["sku", "ceporigem", "cepdestino"] + colunas_numericas
    
    faltantes = [c for c in obrigatorias if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatórias faltando: {faltantes}")
    
    for col in colunas_numericas:
        df[col] = df[col].apply(to_float)
    
    df["cep_origem_payload"] = df["ceporigem"].apply(normalize_cep)
    df["cep_destino_payload"] = df["cepdestino"].apply(normalize_cep)
    
    endpoint = "https://api.intelipost.com.br/api/v1/quote_by_product"
    headers = {
        "api_key": api_key,
        "Content-Type": "application/json",
        "platform": "api"
    }
    
    session = requests.Session()
    session.headers.update(headers)
    resultados = []
    
    for idx, row in df.iterrows():
        try:
            cep_origem = row["cep_origem_payload"]
            cep_destino = row["cep_destino_payload"]
            
            if not cep_origem or not cep_destino:
                logs.append(f"[WARN] Linha {idx+1}: CEP inválido")
                resultados.append({
                    "sku": row["sku"],
                    "cep_origem_payload": cep_origem,
                    "cep_destino_payload": cep_destino,
                    "final_shipping_cost_api": None,
                    "final_shipping_cost_base": None,
                    "final_shipping_cost_com_sobrepreco": None,
                    "carrier": "CEP_INVALIDO",
                    "carrier_erp": "NÃO ENCONTRADO",
                    "codigo_erp": "NÃO ENCONTRADO",
                    "status_retorno": "ERRO",
                    "mensagem": "CEP origem ou destino inválido"
                })
                continue
            
            payload = {
                "origin_zip_code": cep_origem,
                "destination_zip_code": cep_destino,
                "quoting_mode": "DYNAMIC_BOX_ALL_ITEMS",
                "products": [{
                    "weight": to_float(row["peso"]),
                    "cost_of_goods": to_float(row["precoproduto"]),
                    "width": to_float(row["largura"]),
                    "height": to_float(row["altura"]),
                    "length": to_float(row["comprimento"]),
                    "quantity": 1,
                    "sku_id": str(row["sku"]),
                    "product_category": None
                }]
            }
            
            resp = session.post(endpoint, json=payload, timeout=60)
            
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5)
                resp = session.post(endpoint, json=payload, timeout=60)
            
            try:
                data = resp.json()
            except ValueError:
                logs.append(f"[ERROR] Linha {idx+1}: Resposta inválida da API")
                resultados.append({
                    "sku": row["sku"],
                    "cep_origem_payload": cep_origem,
                    "cep_destino_payload": cep_destino,
                    "final_shipping_cost_api": None,
                    "final_shipping_cost_base": None,
                    "final_shipping_cost_com_sobrepreco": None,
                    "carrier": "ERRO_JSON",
                    "carrier_erp": "NÃO ENCONTRADO",
                    "codigo_erp": "NÃO ENCONTRADO",
                    "status_retorno": resp.status_code,
                    "mensagem": extract_messages(resp.text)
                })
                continue
            
            delivery_options = (data.get("content") or {}).get("delivery_options", [])
            
            if not delivery_options:
                logs.append(f"[WARN] Linha {idx+1}: Sem opções de entrega")
                resultados.append({
                    "sku": row["sku"],
                    "cep_origem_payload": cep_origem,
                    "cep_destino_payload": cep_destino,
                    "final_shipping_cost_api": None,
                    "final_shipping_cost_base": None,
                    "final_shipping_cost_com_sobrepreco": None,
                    "carrier": "SEM_OPCAO",
                    "carrier_erp": "NÃO ENCONTRADO",
                    "codigo_erp": "NÃO ENCONTRADO",
                    "status_retorno": data.get("status", resp.status_code),
                    "mensagem": extract_messages(data)
                })
                continue
            
            menor_opcao = min(delivery_options, key=lambda x: x.get("final_shipping_cost", float("inf")))
            carrier_nome = menor_opcao.get("delivery_method_name") or menor_opcao.get("description") or "N/A"
            final_cost_api = menor_opcao.get("final_shipping_cost")
            
            # A API Intelipost JÁ retorna o valor com 135% de sobrepreço aplicado
            # Precisamos calcular o valor BASE (sem sobrepreço) primeiro
            final_cost_base = None
            final_cost_com_sobrepreco = None
            
            if final_cost_api is not None:
                # Remover o sobrepreço de 135% que já vem da API
                # Fórmula: valor_base = valor_com_sobrepreco / (1 + 1.35)
                final_cost_base = final_cost_api / 2.35
                
                # Aplicar o sobrepreço configurado pelo usuário
                final_cost_com_sobrepreco = final_cost_base * (1 + sobrepreco / 100)
            
            carrier_erp = "NÃO ENCONTRADO"
            codigo_erp = "NÃO ENCONTRADO"
            if depara_available:
                key = str(carrier_nome).strip().lower()
                mapa = depara_map.get(key, {})
                carrier_erp = mapa.get("erp", "NÃO ENCONTRADO") or "NÃO ENCONTRADO"
                codigo_erp = mapa.get("codigo_erp", "NÃO ENCONTRADO") or "NÃO ENCONTRADO"
            
            resultados.append({
                "sku": row["sku"],
                "cep_origem_payload": cep_origem,
                "cep_destino_payload": cep_destino,
                "final_shipping_cost_api": final_cost_api,
                "final_shipping_cost_base": final_cost_base,
                "final_shipping_cost_com_sobrepreco": final_cost_com_sobrepreco,
                "carrier": carrier_nome,
                "carrier_erp": carrier_erp,
                "codigo_erp": codigo_erp,
                "prazo_bd_uteis": menor_opcao.get("delivery_estimate_business_days"),
                "metodo": menor_opcao.get("delivery_method_type"),
                "contrato_id": menor_opcao.get("logistic_contract_id"),
                "status_retorno": data.get("status", resp.status_code),
                "mensagem": extract_messages(data)
            })
            
            logs.append(f"[SUCCESS] Linha {idx+1}: {carrier_nome} - Base: R$ {final_cost_base:.2f} | Com sobrepreço: R$ {final_cost_com_sobrepreco:.2f}")
            time.sleep(0.4)
            
        except Exception as e:
            logs.append(f"[ERROR] Linha {idx+1}: {str(e)}")
            resultados.append({
                "sku": row.get("sku"),
                "cep_origem_payload": row.get("cep_origem_payload"),
                "cep_destino_payload": row.get("cep_destino_payload"),
                "final_shipping_cost_api": None,
                "final_shipping_cost_base": None,
                "final_shipping_cost_com_sobrepreco": None,
                "carrier": "ERRO_EXCEPTION",
                "carrier_erp": "NÃO ENCONTRADO",
                "codigo_erp": "NÃO ENCONTRADO",
                "status_retorno": "EXCEPTION",
                "mensagem": str(e)
            })
    
    resultado_df = pd.DataFrame(resultados)
    logs.append(f"[INFO] Processamento concluído: {len(resultado_df)} linhas")
    
    return resultado_df, logs

# ============ VIACEP LOGIC ============

def limpar_cep(cep) -> Optional[str]:
    if pd.isna(cep):
        return None
    cep = "".join(ch for ch in str(cep) if ch.isdigit())
    if len(cep) == 0:
        return None
    if len(cep) < 8:
        cep = cep.zfill(8)
    return cep if len(cep) == 8 else None

def via_cep_lookup(session: requests.Session, cep: str, timeout: int = 5) -> Optional[Dict]:
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            if not data.get("erro"):
                return data
    except requests.RequestException:
        return None
    return None

def buscar_bairro_via_cep(
    session: requests.Session,
    cep: str,
    tentativas: int = 4,
    atraso_base: float = 0.4
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    for i in range(tentativas):
        data = via_cep_lookup(session, cep)
        if data:
            bairro = (data.get("bairro") or "").strip() or None
            cidade = (data.get("localidade") or "").strip() or None
            uf = (data.get("uf") or "").strip() or None
            return bairro, cidade, uf
        time.sleep(atraso_base * (2 ** i))
    return None, None, None

async def process_busca_cep(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    logs = []
    logs.append(f"[INFO] Iniciando busca de CEPs para {len(df)} linhas")
    
    if "CEP" not in df.columns:
        cep_col = None
        for col in df.columns:
            if "cep" in col.lower():
                cep_col = col
                break
        if not cep_col:
            raise ValueError("A planilha precisa ter a coluna 'CEP'")
        df = df.rename(columns={cep_col: "CEP"})
    
    cache: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]] = {}
    bairros = []
    cidades = []
    ufs = []
    falhas = []
    
    with requests.Session() as session:
        last_cep = None
        
        for idx, raw_cep in enumerate(df["CEP"]):
            cep = limpar_cep(raw_cep)
            
            if not cep:
                bairros.append(None)
                cidades.append(None)
                ufs.append(None)
                falhas.append(str(raw_cep))
                logs.append(f"[WARN] Linha {idx+1}: CEP inválido ({raw_cep})")
                continue
            
            if cep in cache:
                bairro, cidade, uf = cache[cep]
            else:
                if last_cep is None or cep != last_cep:
                    time.sleep(0.25)
                bairro, cidade, uf = buscar_bairro_via_cep(session, cep)
                cache[cep] = (bairro, cidade, uf)
            
            bairros.append(bairro)
            cidades.append(cidade)
            ufs.append(uf)
            
            if bairro is None:
                falhas.append(cep)
                logs.append(f"[WARN] Linha {idx+1}: Bairro não encontrado para CEP {cep}")
            else:
                logs.append(f"[SUCCESS] Linha {idx+1}: {bairro}, {cidade}/{uf}")
            
            last_cep = cep
    
    df["CEP Limpo"] = [limpar_cep(c) for c in df["CEP"]]
    df["Bairro"] = bairros
    df["Cidade"] = cidades
    df["UF"] = ufs
    
    logs.append(f"[INFO] Processamento concluído: {len(df)} linhas, {len(falhas)} falhas")
    
    return df, logs, falhas

# ============ API ENDPOINTS ============

@api_router.post("/config/intelipost")
async def save_intelipost_config(config: ApiConfigCreate):
    try:
        existing = await db.api_configs.find_one({}, {"_id": 0})
        
        if existing:
            doc = {
                "api_key_intelipost": config.api_key_intelipost,
                "sobrepreco_padrao": config.sobrepreco_padrao,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.api_configs.update_one({"id": existing["id"]}, {"$set": doc})
            return {"message": "Configuração atualizada com sucesso", "id": existing["id"]}
        else:
            config_obj = ApiConfig(**config.model_dump())
            doc = config_obj.model_dump()
            doc["created_at"] = doc["created_at"].isoformat()
            doc["updated_at"] = doc["updated_at"].isoformat()
            await db.api_configs.insert_one(doc)
            return {"message": "Configuração salva com sucesso", "id": config_obj.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/config/intelipost")
async def get_intelipost_config():
    try:
        config = await db.api_configs.find_one({}, {"_id": 0})
        if not config:
            return {"configured": False}
        
        api_key = config.get("api_key_intelipost", "")
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
        
        return {
            "configured": True,
            "api_key_masked": masked_key,
            "sobrepreco_padrao": config.get("sobrepreco_padrao", 135.0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/depara/upload")
async def upload_depara(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        depara_df = pd.read_excel(io.BytesIO(contents))
        depara_df.columns = [c.strip() for c in depara_df.columns]
        
        col_intelipost = pick_column(
            depara_df.columns,
            "intelipost", "nome_intelipost", "delivery_method_name", "transportadora", "carrier"
        )
        col_erp = pick_column(depara_df.columns, "erp", "transportadora_erp", "nome_erp", "erp_nome")
        col_cod_erp = pick_column(depara_df.columns, "codigo_erp", "cod_erp", "codigo", "código_erp")
        
        if not col_intelipost:
            raise HTTPException(status_code=400, detail="Coluna de transportadora Intelipost não encontrada")
        
        mappings = {}
        for _, r in depara_df.iterrows():
            key = str(r[col_intelipost]).strip().lower() if not pd.isna(r[col_intelipost]) else ""
            if not key:
                continue
            mappings[key] = {
                "erp": (None if col_erp is None else (None if pd.isna(r.get(col_erp, None)) else str(r.get(col_erp)))),
                "codigo_erp": (None if col_cod_erp is None else (None if pd.isna(r.get(col_cod_erp, None)) else str(r.get(col_cod_erp))))
            }
        
        existing = await db.depara_mappings.find_one({}, {"_id": 0})
        
        if existing:
            doc = {
                "mappings": mappings,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.depara_mappings.update_one({"id": existing["id"]}, {"$set": doc})
            return {"message": f"DE-PARA atualizado com {len(mappings)} mapeamentos", "count": len(mappings)}
        else:
            depara_obj = DeparaMapping(mappings=mappings)
            doc = depara_obj.model_dump()
            doc["created_at"] = doc["created_at"].isoformat()
            doc["updated_at"] = doc["updated_at"].isoformat()
            await db.depara_mappings.insert_one(doc)
            return {"message": f"DE-PARA salvo com {len(mappings)} mapeamentos", "count": len(mappings)}
            
    except Exception as e:
        logger.error(f"Erro ao fazer upload do DE-PARA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/depara/status")
async def get_depara_status():
    try:
        depara = await db.depara_mappings.find_one({}, {"_id": 0})
        if not depara:
            return {"configured": False, "count": 0}
        
        return {
            "configured": True,
            "count": len(depara.get("mappings", {})),
            "updated_at": depara.get("updated_at")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/cotacao/process")
async def process_cotacao(
    file: UploadFile = File(...),
    sobrepreco: Optional[float] = Form(None)
):
    try:
        config = await db.api_configs.find_one({}, {"_id": 0})
        if not config:
            raise HTTPException(status_code=400, detail="Configure a API key da Intelipost primeiro")
        
        api_key = config.get("api_key_intelipost")
        sobreprc = sobrepreco if sobrepreco is not None else config.get("sobrepreco_padrao", 135.0)
        
        depara_doc = await db.depara_mappings.find_one({}, {"_id": 0})
        depara_map = depara_doc.get("mappings", {}) if depara_doc else {}
        
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), dtype={"ceporigem": "string", "cepdestino": "string", "sku": "string"}, keep_default_na=False)
        
        history = ProcessingHistory(
            tipo="cotacao",
            arquivo_entrada=file.filename,
            status="processando",
            total_linhas=len(df)
        )
        history_doc = history.model_dump()
        history_doc["created_at"] = history_doc["created_at"].isoformat()
        await db.processing_history.insert_one(history_doc)
        
        resultado_df, logs = await process_cotacao_intelipost(df, api_key, sobreprc, depara_map)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            resultado_df.to_excel(writer, index=False, sheet_name="cotacoes")
        output.seek(0)
        
        linhas_erro = len(resultado_df[resultado_df["status_retorno"].astype(str).str.contains("ERRO|SEM_OPCAO|EXCEPTION", na=False)])
        await db.processing_history.update_one(
            {"id": history.id},
            {"$set": {
                "status": "concluido",
                "linhas_processadas": len(resultado_df),
                "linhas_com_erro": linhas_erro,
                "logs": logs,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "arquivo_saida": f"resultado-cotacao-{history.id}.xlsx"
            }}
        )
        
        filename = f"resultado-cotacao-{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar cotação: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/cep/process")
async def process_cep(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        history = ProcessingHistory(
            tipo="cep",
            arquivo_entrada=file.filename,
            status="processando",
            total_linhas=len(df)
        )
        history_doc = history.model_dump()
        history_doc["created_at"] = history_doc["created_at"].isoformat()
        await db.processing_history.insert_one(history_doc)
        
        resultado_df, logs, falhas = await process_busca_cep(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            resultado_df.to_excel(writer, index=False, sheet_name="resultados")
            if falhas:
                pd.DataFrame({"CEP": falhas}).to_excel(writer, index=False, sheet_name="falhas")
        output.seek(0)
        
        await db.processing_history.update_one(
            {"id": history.id},
            {"$set": {
                "status": "concluido",
                "linhas_processadas": len(resultado_df),
                "linhas_com_erro": len(falhas),
                "logs": logs,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "arquivo_saida": f"resultado-cep-{history.id}.xlsx"
            }}
        )
        
        filename = f"resultado-cep-{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar CEPs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history")
async def get_history():
    try:
        history = await db.processing_history.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()