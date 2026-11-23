"""Repository adaptation of original deterministic claim-register builder.
Compact sections preserve numeric sources and labels; not an exact copy.
"""
def build_content(results,cfg,client,month):
    b,a,p = results['benchmark'],results['anomaly'],results['proposal']
    claims, sections = [], []
    def claim(cid,value,label,source,precision=2):
        if label == 'ESTIMATED' and (cid == 'annual_kwh' or cid.endswith('.excess_kwh') or cid.startswith('top3.') or cid.endswith('savings_sgd_year')):
            precision = -2
            value = round(value,precision)
        claims.append({'id':cid,'value':value,'label':label,'source':source,'precision':precision})
        return value
    eui = claim('eui',b['eui_kwh_m2_yr']['value'],'ESTIMATED','benchmark.eui_kwh_m2_yr',1)
    annual = claim('annual_kwh',b['annual_kwh']['value'],'ESTIMATED','benchmark.annual_kwh',0)
    total = claim('month_kwh',b['month_kwh'],'MEASURED','benchmark.month_kwh',1)
    claim('tariff',p['tariff_sgd_kwh']['value'],'ASSUMPTION','config.tariff')
    sections.append({'heading':'Executive summary','paragraphs':[
        f'Monthly consumption {total:,.1f} kWh [MEASURED in synthetic fixture]. Annualized energy {annual:,.0f} kWh [ESTIMATED from one month].',
        f'EUI {eui} kWh/m2/year [ESTIMATED]. Benchmark constants are inherited demo references; regulatory applicability requires professional review.']})
    dq = results.get('intake',{}).get('data_quality') or {}
    if dq.get('hours_interpolated') or dq.get('hours_excluded') or dq.get('checks_skipped'):
        cov = claim('data_coverage_pct',dq['coverage_pct'],'MEASURED','intake.data_quality.coverage_pct',1)
        pars = [f'Data coverage {cov}% [MEASURED].']
        for field in ('hours_interpolated','hours_excluded'):
            val = claim(field,dq[field],'MEASURED',f'intake.data_quality.{field}',0)
            pars.append(f'{field}: {val} hours. Repaired readings are estimates, not measurements.')
        pars.extend(f'Check skipped: {s}.' for s in dq['checks_skipped'])
        sections.append({'heading':'Data quality','paragraphs':pars})
    pars = []
    for x in a['findings']:
        fid = x['id']
        ex = claim(f'{fid}.excess_kwh',x['excess_kwh']['value'],'ESTIMATED',f'anomaly.{fid}.excess_kwh',0)
        pars.append(f"{x['title']}: from day {x['start_day']}; estimated excess {ex:,.0f} kWh [ESTIMATED]. {x['possible_cause']}.")
        if fid == 'night_waste':
            for field,key in [('ratio_before','night_day_ratio_before'),('ratio_after','night_day_ratio_after')]:
                if x[key] is not None:
                    value = claim(f'{fid}.{field}',x[key],'HEURISTIC',f'anomaly.{fid}.{field}')
                    pars.append(f'{field}: {value} [HEURISTIC].')
        elif fid == 'weekend_waste':
            for d,val in x['saturday_vs_weekday_pct'].items():
                value = claim(f'{fid}.sat_pct.{d}',val,'HEURISTIC',f'anomaly.{fid}.saturday_vs_weekday_pct.{d}',0)
                pars.append(f'Saturday day {d}: {value}% of weekday mean [HEURISTIC].')
        else:
            for field in ('kwrt_start','kwrt_end'):
                value = claim(f'{fid}.{field}',x[field],'MEASURED',f'anomaly.{fid}.{field}',3)
                pars.append(f'{field}: {value} kW/RT [MEASURED in synthetic fixture].')
            pars.append(x['engineer_flag_text'])
    sections.append({'heading':'Findings','paragraphs':pars or ['No abnormal patterns detected by these heuristics.']})
    pars = []
    for fx in p['fixes']:
        sav = claim(f"{fx['id']}.savings_sgd_year",fx['savings_sgd_year']['value'],'ESTIMATED',f"proposal.{fx['id']}.savings_sgd_year")
        cost = claim(f"{fx['id']}.cost_sgd",fx['cost_sgd']['value'],'ASSUMPTION',f"config.fix_costs.{fx['id']}",0)
        pars.append(f"{fx['name']}: potential S${sav:,.0f}/year [ESTIMATED]; cost S${cost:,.0f} [ASSUMPTION]. Recoverability unconfirmed; not a promise.")
        if fx['payback_years']['value'] is not None:
            claim(f"{fx['id']}.payback_years",fx['payback_years']['value'],'ESTIMATED',f"proposal.{fx['id']}.payback_years")
    for i,t in enumerate(p['top3_issues_sgd_year']):
        claim(f'top3.{i}',t['sgd_year'],'ESTIMATED',f'proposal.top3_issues_sgd_year[{i}]')
    claim('total_savings_sgd_year',p['total_potential_savings_sgd_year'],'ESTIMATED','proposal.total_potential_savings_sgd_year')
    sections.append({'heading':'Proposed fixes','paragraphs':pars or ['No fixes proposed.']})
    sections.append({'heading':'Assumptions','paragraphs':p['assumptions']+[p['disclaimer']]})
    engineers = [{'item':fx['name'],'flag':fx['engineer_flag_text']} for fx in p['fixes'] if fx['engineer_flag']]
    engineers += [{'item':x['title'],'flag':x['engineer_flag_text']} for x in a['findings'] if x['engineer_flag']]
    return {'client':client['client_name'],'month':month,'disclosure':client['disclosure'],'generated_from':'results.json',
            'sections':sections,'claims':claims,'engineer_items':engineers,
            'label_legend':{'MEASURED':'fixture meter values','ESTIMATED':'calculation with assumptions','BENCHMARK':'demo comparison reference',
                            'REGULATORY':'inherited reference; applicability unverified','HEURISTIC':'indicator, not diagnosis','ASSUMPTION':'placeholder'}}
