#!/usr/bin/env python3
"""NEW in-memory adaptation of original R1-R6 tamper suite; no deletion/PDF writes."""
import copy
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT / 'pipeline'))
import common
import intake
import benchmark
import anomaly
import proposal
import report_content
import validate_report
path = ROOT / 'clients/demo-office/2026-09/meter_data.csv'
raw = common.load_csv(path)
cfg = common.load_config()
client = common.load_client(path.parent.parent)
ir = intake.run(raw,client['gfa_m2'])
clean = ir.pop('df_clean')
a = anomaly.run(clean,cfg)
results = {'intake':ir,'benchmark':benchmark.run(clean,client['gfa_m2'],cfg),'anomaly':a,'proposal':proposal.run(clean,a,cfg,raw_df=raw)}
content = report_content.build_content(results,cfg,client,'2026-09')
def validate(c):
    return validate_report.validate(c,raw,client['gfa_m2'],cfg,path)
assert not validate(content)
mutations = {
 'R1':lambda c:c['claims'][0].update(label=''),
 'R2':lambda c:c['sections'][0]['paragraphs'].append('Chiller fault confirmed, savings guaranteed.'),
 'R3':lambda c:c['claims'][0].update(value=1185),
 'R4':lambda c:c.update(engineer_items=[]),
 'R5':lambda c:c['claims'].append({'id':'made_up','value':62000,'label':'ESTIMATED','precision':2}),
 'R6':lambda c:c['sections'][0]['paragraphs'].append('You will save S$62,000 per year.')}
for rule,mutate in mutations.items():
    bad = copy.deepcopy(content)
    mutate(bad)
    assert any(rule in v for v in validate(bad)), rule
    print('PASS:',rule)
print('PASS: clean content and six in-memory tamper gates. Not PDF preservation evidence.')
