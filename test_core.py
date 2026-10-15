import json
import threading
import pytest
from fastapi.testclient import TestClient
from core import Settings, run_pipeline, rule_checks, endpoint_url, LLMClient

TEXT = 'Original ' + 'A park offers shade and gives people room to walk. ' * 12
A = TEXT.replace('Original', 'Improved')
B = TEXT.replace('Original', 'Worse')

class FakeModels:
    def __init__(self): self.calls=[]
    def detect(self, text, kind='guide'):
        self.calls.append((kind,text))
        score = .2 if text.startswith('Improved') else .8 if text.startswith('Original') else .9
        return {'score':score, 'windows':[], 'tokens':100}
    def meaning(self, original, candidate): return {'passed':True, 'reasons':[]}

class FakeLLM:
    def __init__(self, texts): self.texts=iter(texts);self.calls=0
    def rewrite(self,*args): self.calls+=1;return next(self.texts)

def test_backtrack_and_holdout_separation():
    models=FakeModels(); llm=FakeLLM([A,B,B,B])
    r=run_pipeline(TEXT,llm,models,Settings(2,2))
    assert r['text']==A
    assert [h['accepted'] for h in r['history']]==[True,False,False,False]
    assert all(c[0]=='guide' for c in models.calls[:-2])
    assert [c[0] for c in models.calls[-2:]]==['holdout','holdout']

def test_no_improvement_keeps_original_and_stops_early():
    llm=FakeLLM([B,B]);r=run_pipeline(TEXT,llm,FakeModels(),Settings(3,2))
    assert r['text']==TEXT and llm.calls==2

def test_quality_failure_never_falls_back_to_invalid_candidate():
    r=run_pipeline(TEXT,FakeLLM(['Improved but now only 5 words.']),FakeModels(),Settings(1,1))
    assert r['text']==TEXT and not r['history'][0]['accepted']

def test_contradiction_rejects_candidate_even_with_lower_score():
    m=FakeModels();m.meaning=lambda a,b:{'passed':False,'reasons':['contradiction']}
    r=run_pipeline(TEXT,FakeLLM([A]),m,Settings(1,1))
    assert r['text']==TEXT

def test_protected_numbers_quotes_and_citations():
    original='In 2024, Smith wrote "Parks help" [1]. ' + TEXT
    assert not rule_checks(original,original.replace('2024','2025'))['passed']
    assert not rule_checks(original,original.replace('[1]','[2]'))['passed']
    assert not rule_checks(original,original.replace('Parks help','Parks hurt'))['passed']
    assert rule_checks(original,original)['passed']
    assert not rule_checks(TEXT,A,('Original',))['passed']

def test_cancellation_makes_no_api_requests():
    stop=threading.Event();stop.set();llm=FakeLLM([])
    r=run_pipeline(TEXT,llm,FakeModels(),Settings(),stop=stop)
    assert llm.calls==0 and r['text']==TEXT and r['stopped']

def test_api_failure_preserves_best():
    class Broken:
        def rewrite(self,*args): raise RuntimeError('HTTP 401')
    r=run_pipeline(TEXT,Broken(),FakeModels(),Settings())
    assert r['api_failed'] and r['text']==TEXT

def test_endpoint_policy_and_suffix():
    assert endpoint_url('https://example.com/v1')=='https://example.com/v1/chat/completions'
    assert endpoint_url('https://example.com/v1/chat/completions').count('chat/completions')==1
    for u in ['http://example.com','https://user:password@example.com','https://example.com?key=abc']:
        with pytest.raises(ValueError): endpoint_url(u)

def test_http_boundaries_and_no_key_echo():
    import app
    client=TestClient(app.app)
    assert client.get('/api/health').status_code==403
    headers={'X-Local-Token':app.TOKEN}
    assert client.get('/api/health',headers=headers).status_code==200
    assert client.post('/api/run',headers={**headers,'Origin':'https://evil.example'},json={}).status_code==403
    secret='TEST-SECRET-MUST-NOT-BE-ECHOED'
    r=client.post('/api/run',headers=headers,json={'text':TEXT,'api_key':secret,'rounds':0})
    assert r.status_code==422 and secret not in r.text

def test_provider_error_body_is_not_exposed(monkeypatch):
    class Response:
        status_code=401
        text='API-KEY-OR-OTHER-SENSITIVE-PROVIDER-DATA'
    monkeypatch.setattr('core.requests.post',lambda *a,**k:Response())
    with pytest.raises(RuntimeError) as exc:
        LLMClient('https://example.com/v1','secret','model').rewrite(TEXT,TEXT,[],[],0)
    assert 'SENSITIVE' not in str(exc.value) and '401' in str(exc.value)

def test_codex_parses_text_and_usage_without_key():
    from codex_provider import CodexClient
    events=[{'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'text':'Edited article.'})}},
            {'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':4}}]
    text,usage=CodexClient._parse('\n'.join(json.dumps(x) for x in events),0)
    assert text=='Edited article.' and usage['output_tokens']==4

def test_codex_rejects_tool_events():
    from codex_provider import CodexClient
    with pytest.raises(RuntimeError):
        CodexClient._parse(json.dumps({'type':'item.started','item':{'type':'command_execution'}}),0)

def test_codex_strips_api_keys_from_child_environment(monkeypatch):
    from codex_provider import child_env
    monkeypatch.setenv('OPENAI_API_KEY','do-not-inherit')
    monkeypatch.setenv('CODEX_API_KEY','do-not-inherit')
    assert 'OPENAI_API_KEY' not in child_env() and 'CODEX_API_KEY' not in child_env()

def test_codex_request_requires_login_but_not_api_key(monkeypatch):
    import app
    monkeypatch.setattr(app,'codex_status',lambda:{'chatgpt_login':False})
    client=TestClient(app.app)
    response=client.post('/api/run',headers={'X-Local-Token':app.TOKEN},json={'text':TEXT,'provider':'codex'})
    assert response.status_code==400 and '登入' in response.json()['detail']

def test_micro_variants_and_codex_alternatives():
    from core import sentence_micro_variants
    from codex_provider import CodexClient
    v = sentence_micro_variants('In recent years, parks provide residents with places to walk.')
    assert any('Lately,' in s for s in v)
    msg = '\n'.join([json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'text':'Draft 1.','alternatives':['Draft 2.','Draft 3.']})}})])
    assert CodexClient._extract_alternatives(msg) == ['Draft 2.', 'Draft 3.']


