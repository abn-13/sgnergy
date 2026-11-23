"""Adapted from original proposal module; estimates, not verified savings."""
from common import sgd
ENGINEER_FLAG = "Needs review by a PE (Mechanical) or BCA-registered Energy Auditor"

def run(df, anomaly, cfg, raw_df=None):
    tariff = cfg['tariff']['sgd_per_kwh_before_gst']
    days = (df.Timestamp.max()-df.Timestamp.min()).total_seconds()/86400+1/24
    yr = 365/days
    by_id = {f['id']:f for f in anomaly['findings']}
    fixes, top3 = [], []
    night = by_id.get('night_waste')
    nightly_cost = None
    if night and raw_df is not None:
        ts = raw_df.Timestamp
        mask = ((ts.dt.dayofweek < 5) & ~ts.dt.hour.between(8,18) & (ts.dt.strftime('%Y-%m-%d') >= night['start_date']))
        dates = sorted(ts[mask].dt.strftime('%Y-%m-%d').unique().tolist())
        count = len(dates)
        cost = night['excess_kwh']['value'] * tariff
        nightly_cost = {'value':sgd(cost/count) if count else None,'label':'ESTIMATED','units':'SGD/affected weekday night before GST',
            'basis':'Existing full-period night_waste.excess_kwh x project tariff / raw-CSV affected weekday calendar dates from finding onset. Numerator includes pre-onset baseline excess; not isolated fault attribution or measured savings. Each date combines early and late after-hours blocks, not an overnight interval; weekends excluded.',
            'excess_kwh':night['excess_kwh']['value'],'tariff_sgd_per_kwh_before_gst':tariff,'period_cost_sgd_before_gst':sgd(cost),
            'denominator':{'count':count,'units':'affected weekday calendar dates','start_date':night['start_date'],'end_date':str(ts.max().date()),'dates':dates,
                'mask':'weekday < 5 AND hour NOT BETWEEN 8 AND 18 inclusive AND local date >= finding start_date','raw_after_hours_rows':int(mask.sum()),
                'occupancy_basis':'generate_data.py: weekday occupancy 08:00-19:00; no measured occupancy column in meter CSV'},
            'source_references':['data_file: Timestamp, Total_Building_kWh (hourly)','anomaly.findings[id=night_waste].excess_kwh',
                'anomaly.findings[id=night_waste].start_date','config.json: tariff.sgd_per_kwh_before_gst','pipeline/anomaly.py: weekday after_hours mask','generate_data.py: occupied definition'],
            'code_edition_qualifier':'Uses existing project config (BCA PEA Code 3.0 reference); no code-edition applicability or MEI compliance conclusion is established by this cost estimate.'}
    weekend = by_id.get('weekend_waste')
    sched_kwh = sum(f['excess_kwh']['value'] for f in (night,weekend) if f)
    if sched_kwh > 0:
        annual_sav = sched_kwh * yr * tariff
        cost = cfg['fix_costs_sgd']['F1_bms_schedule_correction']
        fixes.append({'id':'F1','name':'BMS schedule correction (night + Saturday)','basis_kwh_month':round(sched_kwh,0),
            'savings_sgd_year':{'value':sgd(annual_sav),'label':'ESTIMATED','basis':f'{sched_kwh:.0f} kWh/mo x S${tariff}/kWh, annualised'},
            'cost_sgd':{'value':cost,'label':'ASSUMPTION'},'payback_years':{'value':round(cost/annual_sav,2),'label':'ESTIMATED'},'engineer_flag':False})
        if night:
            top3.append({'issue':'Night waste (empty hours running)','sgd_year':sgd(night['excess_kwh']['value']*yr*tariff)})
        if weekend:
            top3.append({'issue':'Saturday waste (weekday schedule)','sgd_year':sgd(weekend['excess_kwh']['value']*yr*tariff)})
    chiller = by_id.get('chiller_drift')
    if chiller:
        delta = chiller['kwrt_end']-chiller['kwrt_start']
        rt_hours = chiller['rt_hours_above_low_load_filter']
        monthly_sav = max(delta,0)*rt_hours*tariff
        annual_sav = monthly_sav*yr
        cost = cfg['fix_costs_sgd']['F2_chiller_plant_service']
        fixes.append({'id':'F2','name':'Chiller plant inspection and service',
            'basis':f"efficiency drift {chiller['kwrt_start']} -> {chiller['kwrt_end']} kW/RT",
            'savings_sgd_year':{'value':sgd(annual_sav),'label':'ESTIMATED','basis':'drift x occupied RT-hours x tariff, annualised; recoverable portion unconfirmed'},
            'cost_sgd':{'value':cost,'label':'ASSUMPTION'},'payback_years':{'value':round(cost/annual_sav,2) if annual_sav > 0 else None,'label':'ESTIMATED'},
            'engineer_flag':True,'engineer_flag_text':ENGINEER_FLAG})
        top3.append({'issue':'Chiller efficiency drift (getting worse daily)','sgd_year':sgd(annual_sav)})
    top3.sort(key=lambda x:-x['sgd_year'])
    result = {'fixes':fixes,'top3_issues_sgd_year':top3[:3],
        'total_potential_savings_sgd_year':sgd(sum(f['savings_sgd_year']['value'] for f in fixes)),
        'tariff_sgd_kwh':{'value':tariff,'label':'ASSUMPTION','range':cfg['tariff']['range']},
        'assumptions':[f"Tariff S${tariff}/kWh before GST (range {cfg['tariff']['range']})",'Fix costs are placeholders pending quotes',
                       'Office hours 08:00-19:00, night window 22:00-06:00','Annual figures extrapolated from one month of data'],
        'engineer_items':[f['name'] for f in fixes if f['engineer_flag']],
        'disclaimer':'Synthetic demo data. Findings are indicators, not diagnoses. No compliance claim is made. Plant-related items require a PE (Mechanical) or BCA-registered Energy Auditor.'}
    if nightly_cost is not None:
        result['night_waste_sgd_per_affected_night'] = nightly_cost
    return result
