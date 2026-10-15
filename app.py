from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import secrets
import threading
import time
import webbrowser
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, SecretStr
from starlette.middleware.trustedhost import TrustedHostMiddleware
from core import LocalModels, LLMClient, Settings, run_pipeline, words, endpoint_url, diagnostics_report
from codex_provider import CodexClient, status as codex_status, ALLOWED_MODELS, ALLOWED_EFFORTS

ROOT = Path(__file__).resolve().parent
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', '[::1]', 'testserver'])
TOKEN = secrets.token_urlsafe(32)
MODELS = LocalModels()
POOL = ThreadPoolExecutor(max_workers=1)
JOBS = {}
LOCK = threading.RLock()

@app.exception_handler(RequestValidationError)
async def invalid_input(request, exc):
    # Pydantic's default detail may include submitted values. Never echo keys.
    return JSONResponse(status_code=422, content={'detail': '輸入格式或參數範圍不正確。請檢查文章、輪數與候選數。'})

class RunRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    action: str = 'rewrite'
    provider: str = 'codex'
    codex_model: str = 'gpt-6-luna'
    codex_effort: str = 'xhigh'
    base_url: str = Field(default='', max_length=500)
    api_key: SecretStr = SecretStr('')
    model: str = Field(default='', max_length=200)
    rounds: int = Field(default=1, ge=1, le=3)
    candidates: int = Field(default=1, ge=1, le=4)
    protected: list[str] = Field(default_factory=list, max_length=40)
    holdout: bool = True

@app.middleware('http')
async def local_auth(request, call_next):
    if request.url.path.startswith('/api/'):
        if request.headers.get('x-local-token') != TOKEN:
            return HTMLResponse('Forbidden', status_code=403)
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return HTMLResponse('Origin rejected', status_code=403)
        if int(request.headers.get('content-length', '0')) > 150000:
            return HTMLResponse('Request too large', status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response

@app.get('/', response_class=HTMLResponse)
def index():
    return (ROOT/'index.html').read_text(encoding='utf-8').replace('__LOCAL_TOKEN__', TOKEN)

@app.get('/api/health')
def health():
    return {'ready': all((ROOT/'models'/n/'model.safetensors').exists() for n in ('guide','holdout','similarity','nli')),
            'loaded': list(MODELS.loaded), 'device': MODELS.device or '尚未載入',
            'training': False, 'keys_persisted': False, 'codex': codex_status()}

def work(job_id, req):
    stop = JOBS[job_id]['stop']
    def update(event):
        with LOCK:
            JOBS[job_id].update(event)
    update({'state': 'running', 'stage': '載入本機模型'})
    llm = None
    try:
        if req.action == 'detect':
            guide = MODELS.detect(req.text)
            diag = diagnostics_report(MODELS, req.text)
            result = {'original': req.text, 'text': req.text, 'changed': False,
                      'guide_before': guide, 'guide_after': guide,
                      'diagnostics_before': diag, 'diagnostics_after': diag,
                      'history': [], 'mode': 'detect',
                      'interpretation': '本機模型與滑動視窗分數，非真實作者來源機率。'}
            if req.holdout and not stop.is_set():
                update({'stage': '第二偵測器：Desklib'})
                h = MODELS.detect(req.text, 'holdout')
                result.update({'holdout_before': h, 'holdout_after': h})
        else:
            llm = CodexClient(req.codex_model, stop, req.codex_effort) if req.provider == 'codex' else LLMClient(req.base_url, req.api_key.get_secret_value(), req.model)
            result = run_pipeline(req.text, llm, MODELS,
                        Settings(req.rounds, req.candidates, tuple(req.protected), req.holdout), update, stop)
            result['rewriter'] = getattr(llm, 'metadata', {'provider': 'api', 'model': req.model})
        update({'state': 'done', 'result': result, 'stage': '已停止並保留最佳版本' if stop.is_set() else '完成'})
    except Exception:
        # Never relay arbitrary provider bodies, requests or exception strings containing credentials.
        update({'state': 'error', 'stage': '執行失敗', 'error': '本機模型或運算發生錯誤。請確認已執行 Setup.ps1，並嘗試較短文章。'})
    finally:
        req.api_key = SecretStr('')
        if llm is not None and hasattr(llm, 'key'):
            llm.key = ''

@app.post('/api/run')
def run(req: RunRequest):
    n = len(words(req.text))
    if not 80 <= n <= 2000:
        raise HTTPException(400, '第一版支援 80–2,000 個英文單字；短文分數較不穩定。')
    if req.action not in ('detect', 'rewrite'):
        raise HTTPException(400, 'Unknown action')
    if req.provider not in ('codex', 'api'):
        raise HTTPException(400, 'Unknown provider')
    if req.provider == 'codex' and (req.codex_model not in ALLOWED_MODELS or req.codex_effort not in ALLOWED_EFFORTS):
        raise HTTPException(400, '不支援的 Codex 模型或思考強度。')
    if req.action == 'rewrite' and req.provider == 'codex':
        if not codex_status()['chatgpt_login']:
            raise HTTPException(400, '請先在 Codex 登入 ChatGPT 帳號；不會自動改用 API。')
    if req.action == 'rewrite' and req.provider == 'api':
        try:
            ep = endpoint_url(req.base_url)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        is_local_ep = any(h in ep for h in ('//127.0.0.1', '//localhost', '//[::1]'))
        if not req.model.strip() or (not is_local_ep and not req.api_key.get_secret_value().strip()):
            raise HTTPException(400, '請填入 API 金鑰及模型名稱（本機 Ollama 僅需填模型名稱）。')
    if any(len(s) > 500 or s not in req.text for s in req.protected):
        raise HTTPException(400, '指定保留文字必須出現在原文，且每項不超過 500 字元。')
    with LOCK:
        if any(j['state'] in ('queued','running') for j in JOBS.values()):
            raise HTTPException(409, '已有一個工作正在執行。請等待或先停止。')
        while len(JOBS) >= 12:
            JOBS.pop(next(iter(JOBS)))
        job_id = secrets.token_urlsafe(24)
        JOBS[job_id] = {'state': 'queued', 'stage': '排隊中', 'stop': threading.Event(), 'created': time.time()}
        POOL.submit(work, job_id, req)
    return {'job_id': job_id}

@app.get('/api/jobs/{job_id}')
def job(job_id: str):
    with LOCK:
        if job_id not in JOBS:
            raise HTTPException(404, '工作不存在或已清除。')
        return {k:v for k,v in JOBS[job_id].items() if k != 'stop'}

@app.post('/api/jobs/{job_id}/stop')
def stop(job_id: str):
    with LOCK:
        if job_id not in JOBS:
            raise HTTPException(404, '工作不存在。')
        JOBS[job_id]['stop'].set()
    return {'message': '停止新增請求；目前 API 請求或本機計算結束後停止。'}

@app.delete('/api/jobs/{job_id}')
def clear(job_id: str):
    with LOCK:
        if job_id in JOBS and JOBS[job_id]['state'] in ('queued','running'):
            raise HTTPException(409, '請先停止或等待工作結束。')
        JOBS.pop(job_id, None)
    return {'cleared': True}

if __name__ == '__main__':
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8391)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    def _warm():
        for k in ('guide', 'similarity', 'nli', 'holdout'):
            try:
                MODELS.load(k)
            except Exception:
                pass
    threading.Thread(target=_warm, daemon=True).start()
    if args.open:
        threading.Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{args.port}')).start()
    uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False)
