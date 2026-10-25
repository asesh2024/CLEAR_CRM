from pathlib import Path
import json
import pandas as pd
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
o=root/'outputs/main'
s=json.loads((o/'metadata.json').read_text());d=pd.read_csv(o/'decisions.csv');l=pd.read_csv(o/'passport_lineage.csv');p=pd.read_csv(o/'proof_negative_tests.csv')
assert len(d)==s['total_products']*8
assert len(l)==s['total_products']
assert d.groupby(['seed','item']).policy.nunique().eq(8).all()
assert (l.mass_residual_kg.abs()<1e-10).all()
assert p[['valid','replay_rejected','tamper_rejected','false_statement_rejected','unauthorized_rejected','stale_rejected']].eq(1).all().all()
assert len(list((root/'figures').glob('fig*.png')))==10
assert (root/'manuscript.pdf').exists()
print('VERIFIED:',len(d),'product-policy observations;',len(l),'passports;',len(p),'proof cases;',len(PdfReader(root/'manuscript.pdf').pages),'PDF pages')
