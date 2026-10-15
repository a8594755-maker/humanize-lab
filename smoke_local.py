"""Real local model smoke + simulated HTTP LLM. Does NOT test a paid provider."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from core import LocalModels, LLMClient, Settings, run_pipeline, rule_checks

SOURCE = '''In today's rapidly evolving urban landscape, public parks play a crucial role in enhancing the well-being of local communities. These green spaces offer a wide range of benefits, from providing opportunities for physical activity to fostering social connections among residents. Furthermore, parks can offer shade during warm weather and provide habitats for birds and insects. It is important to note that the value of a park depends on more than its size. Accessibility, maintenance, and the needs of nearby residents all play a significant role in determining how often the space is used. A large park that is difficult to reach may be less useful than a smaller one within walking distance. In conclusion, city planners should consider both the amount of green space and the practical experience of residents, while providing ongoing maintenance and opportunities for community feedback.'''
DRAFT = '''Parks give city residents somewhere to exercise, relax, and spend time with other people. They also provide shade in warm weather and places for birds and insects to live. Those benefits matter, but the size of a park tells us little about how useful it is to the people nearby. Getting there matters too. A small park within walking distance may serve residents better than a large one that is hard to reach. Maintenance and the needs of the surrounding community also affect how often people use it. When planning green spaces, cities should look at both the amount of land available and what using those spaces is actually like. They should plan for regular upkeep and give residents a way to share feedback.'''

def main():
    models = LocalModels()
    events = []
    class MockLLM(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert payload['model'] == 'simulated-llm'
            response = json.dumps({'choices':[{'finish_reason':'stop','message':{'content':DRAFT}}]}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.end_headers();self.wfile.write(response)
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),MockLLM)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        client=LLMClient(f'http://127.0.0.1:{server.server_port}/v1','SIMULATED-KEY','simulated-llm')
        result=run_pipeline(SOURCE,client,models,Settings(1,1),lambda e: print(e['stage'],flush=True))
        long_result=models.detect(SOURCE+'\n\n'+SOURCE+'\n\n'+SOURCE+'\n\n'+SOURCE)
        assert len(long_result['windows'])>1
        assert sum(w['tokens'] for w in long_result['windows'])==long_result['tokens']
        assert long_result['windows'][-1]['end_token']==long_result['tokens']
        contradiction=models.meaning('The committee approved the project. Construction will begin next month.',
                                     'The committee rejected the project. Construction will not begin next month.')
        assert not contradiction['passed'], contradiction
        assert 'SIMULATED-KEY' not in json.dumps(result)
        evidence={'test_type':'real local detectors and semantic models; simulated HTTP LLM response',
                  'external_llm_tested':False,'device':models.device,
                  'long_text_coverage_test':long_result,'contradiction_test':contradiction,'pipeline':result}
        out=Path(__file__).resolve().parent/'verification.json'
        out.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'guide_before':result['guide_before']['score'],
                          'guide_after':result['guide_after']['score'],'changed':result['changed'],
                          'holdout_before':result['holdout_before']['score'],
                          'holdout_after':result['holdout_after']['score'],
                          'contradiction_rejected':not contradiction['passed'],
                          'coverage_windows':len(long_result['windows'])},indent=2),flush=True)
    finally:
        server.shutdown();server.server_close()

if __name__=='__main__': main()
