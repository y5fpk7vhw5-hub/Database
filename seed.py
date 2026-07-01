import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'data' / 'construction.db'
SCHEMA_PATH = BASE_DIR / 'schema.sql'


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def first_id(conn, table, column, value):
    row = conn.execute(f'SELECT id FROM {table} WHERE {column} = ?', (value,)).fetchone()
    return row['id'] if row else None


def insert_ignore(conn, table, columns, values):
    cols = ', '.join(columns)
    placeholders = ', '.join('?' for _ in columns)
    conn.execute(f'INSERT OR IGNORE INTO {table} ({cols}) VALUES ({placeholders})', values)


def initialize(reset=False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect()
    conn.executescript(SCHEMA_PATH.read_text(encoding='utf-8'))

    insert_ignore(conn, 'projects', ['code', 'name', 'client', 'location', 'pac_target', 'status'],
                  ['A.14002', 'SSI Flanders Construction', 'Client / Owner', 'Gent, Belgium', '2027-03-10', 'active'])
    pid = first_id(conn, 'projects', 'code', 'A.14002')

    companies = [
        ('Doosan Lentjes', 'epc', 'Construction Management'),
        ('BESIX', 'partner', 'Civil / Building'),
        ('Bilfinger Insulation', 'subcontractor', 'Insulation'),
        ('MKL Stahlbau', 'subcontractor', 'Structural Steel'),
        ('ERS Refractory', 'subcontractor', 'Refractory'),
        ('JWW Mechanical Erection', 'subcontractor', 'Mechanical / Boiler'),
        ('Goodmont Auxiliary Piping', 'subcontractor', 'Auxiliary Piping'),
        ('SpecTech FRP Piping', 'subcontractor', 'FRP Piping'),
        ('Powerspex Electrical & Instrumentation', 'subcontractor', 'E&I'),
        ('Client / Owner', 'client', 'Owner'),
    ]
    for name, ctype, hint in companies:
        insert_ignore(conn, 'companies', ['name', 'type', 'discipline_hint', 'contact_person', 'email', 'status'],
                      [name, ctype, hint, 'Site Manager', f"{name.lower().replace(' ', '.').replace('&', 'and')}@example.com", 'active'])

    disciplines = [
        ('Stahlbau', 't, pcs, bolting %, m2 grating', 'Steel, platforms, gratings, handrails and supports'),
        ('Kessel', 't, equipment, welds, test packages', 'Boiler, furnace, drum, headers, ECO and superheater'),
        ('Static Equipment', 'pcs, t, alignment points', 'Vessels, tanks, filters and ducts'),
        ('Rotating Equipment', 'pcs, alignment, loop checks', 'Pumps, fans, compressors and motors'),
        ('Piping', 'DI, m, spools, welds, supports', 'Steel piping, spools, valves, supports and pressure tests'),
        ('Refractory', 'm2, t, zones, layers', 'Refractory, anchors, curing and dry-out'),
        ('Instrumentierung', 'instruments, loops, hook-ups', 'Instruments, hook-ups, calibration and loop checks'),
        ('Electrical', 'm trays, m cables, terminations', 'Cable trays, pulling, terminations, LV/MV and energization'),
        ('Package Units', 'package %, vendor milestones', 'Vendor packages including FAT/SAT and interface points'),
        ('Insulation', 'm, m2, equipment, systems', 'Insulation, cladding and reinstatement'),
    ]
    for row in disciplines:
        insert_ignore(conn, 'disciplines', ['name', 'unit_examples', 'description'], row)

    for code, name in [('BA4', 'Building Area 4'), ('BA5', 'Building Area 5'), ('ADM', 'Administration Building'), ('EXT', 'External Area')]:
        insert_ignore(conn, 'areas', ['project_id', 'code', 'name'], [pid, code, name])

    systems = [
        ('BOI-100', 'Boiler and Furnace', 'Kessel', 'in progress'),
        ('PIP-210', 'Auxiliary Piping', 'Piping', 'in progress'),
        ('FRP-330', 'FRP Piping', 'Piping', 'blocked'),
        ('ELE-410', 'Electrical LV', 'Electrical', 'open'),
        ('INS-520', 'Insulation and Cladding', 'Insulation', 'open'),
        ('REF-610', 'Refractory Works', 'Refractory', 'open'),
    ]
    for code, name, discipline, status in systems:
        insert_ignore(conn, 'systems', ['project_id', 'code', 'name', 'discipline_id', 'status'],
                      [pid, code, name, first_id(conn, 'disciplines', 'name', discipline), status])

    packages = [
        ('WP-STE-001', 'Structural steel erection BA4', 'Stahlbau', 'MKL Stahlbau', 'BA4', 'BOI-100', 'in progress'),
        ('WP-BOI-001', 'Boiler mechanical erection', 'Kessel', 'JWW Mechanical Erection', 'BA4', 'BOI-100', 'in progress'),
        ('WP-PIP-001', 'Auxiliary piping erection', 'Piping', 'Goodmont Auxiliary Piping', 'BA5', 'PIP-210', 'in progress'),
        ('WP-FRP-001', 'FRP piping erection', 'Piping', 'SpecTech FRP Piping', 'BA5', 'FRP-330', 'blocked'),
        ('WP-EI-001', 'Electrical and instrumentation', 'Electrical', 'Powerspex Electrical & Instrumentation', 'BA4', 'ELE-410', 'open'),
        ('WP-REF-001', 'Refractory installation', 'Refractory', 'ERS Refractory', 'BA4', 'REF-610', 'open'),
        ('WP-INS-001', 'Insulation and cladding', 'Insulation', 'Bilfinger Insulation', 'BA4', 'INS-520', 'open'),
    ]
    for code, name, discipline, company, area, system, status in packages:
        insert_ignore(conn, 'work_packages', ['project_id', 'code', 'name', 'discipline_id', 'company_id', 'area_id', 'system_id', 'status'],
                      [pid, code, name, first_id(conn, 'disciplines', 'name', discipline), first_id(conn, 'companies', 'name', company), first_id(conn, 'areas', 'code', area), first_id(conn, 'systems', 'code', system), status])

    contracts = [
        ('PO-BIL-001', 'Insulation subcontract', 'Bilfinger Insulation', 'Insulation, cladding and reinstatement', 'green'),
        ('PO-MKL-001', 'Structural steel subcontract', 'MKL Stahlbau', 'Steel erection, platforms, gratings and bolting', 'yellow'),
        ('PO-JWW-001', 'Mechanical erection subcontract', 'JWW Mechanical Erection', 'Boiler and mechanical erection', 'yellow'),
        ('PO-PWR-001', 'Electrical and instrumentation subcontract', 'Powerspex Electrical & Instrumentation', 'Cable trays, cabling, terminations and loop checks', 'red'),
    ]
    for no, title, company, scope, risk in contracts:
        insert_ignore(conn, 'contracts', ['project_id', 'company_id', 'contract_no', 'title', 'contract_type', 'scope_summary', 'commercial_status', 'risk_level', 'owner'],
                      [pid, first_id(conn, 'companies', 'name', company), no, title, 'subcontract', scope, 'valid', risk, 'Commercial'])

    drawings = [
        ('ISO-PIP-210-001', 'Auxiliary piping isometrics package 1', 'Piping', 'Goodmont Auxiliary Piping', 'BA5', 'PIP-210', 'B', 'for construction'),
        ('GA-STE-BA4-001', 'Structural steel GA BA4', 'Stahlbau', 'MKL Stahlbau', 'BA4', 'BOI-100', 'C', 'approved'),
        ('EWD-ELE-410-001', 'LV cable tray routing', 'Electrical', 'Powerspex Electrical & Instrumentation', 'BA4', 'ELE-410', 'A', 'for review'),
    ]
    for no, title, discipline, company, area, system, rev, status in drawings:
        insert_ignore(conn, 'drawings', ['project_id', 'drawing_no', 'title', 'discipline_id', 'company_id', 'area_id', 'system_id', 'revision', 'status'],
                      [pid, no, title, first_id(conn, 'disciplines', 'name', discipline), first_id(conn, 'companies', 'name', company), first_id(conn, 'areas', 'code', area), first_id(conn, 'systems', 'code', system), rev, status])

    progress = [
        ('PR-MKL-STEEL', 'WP-STE-001', 'MKL Stahlbau', 'Stahlbau', 'BA4', 'BOI-100', 'Steel tonnage erected', 't', 220, 12, 45, 96, 'in progress'),
        ('PR-JWW-BOILER', 'WP-BOI-001', 'JWW Mechanical Erection', 'Kessel', 'BA4', 'BOI-100', 'Boiler components erected', 't', 480, 25, 30, 118, 'in progress'),
        ('PR-GDM-PIPING', 'WP-PIP-001', 'Goodmont Auxiliary Piping', 'Piping', 'BA5', 'PIP-210', 'Auxiliary piping installed', 'DI', 1500, 18, 20, 220, 'in progress'),
        ('PR-SPT-FRP', 'WP-FRP-001', 'SpecTech FRP Piping', 'Piping', 'BA5', 'FRP-330', 'FRP joints completed', 'joint', 320, 10, 15, 24, 'blocked'),
        ('PR-PWR-TRAY', 'WP-EI-001', 'Powerspex Electrical & Instrumentation', 'Electrical', 'BA4', 'ELE-410', 'Cable tray installed', 'm', 2600, 14, 10, 0, 'open'),
        ('PR-ERS-REF', 'WP-REF-001', 'ERS Refractory', 'Refractory', 'BA4', 'REF-610', 'Refractory installed', 'm2', 900, 11, 0, 0, 'not started'),
        ('PR-BIL-INS', 'WP-INS-001', 'Bilfinger Insulation', 'Insulation', 'BA4', 'INS-520', 'Insulation completed', 'm2', 1800, 10, 0, 0, 'not started'),
    ]
    for code, wp, company, discipline, area, system, desc, unit, baseline, weight, planned, actual, status in progress:
        insert_ignore(conn, 'progress_items', ['project_id', 'work_package_id', 'company_id', 'discipline_id', 'area_id', 'system_id', 'item_code', 'description', 'unit', 'baseline_qty', 'weight', 'planned_percent', 'qa_gate', 'status'],
                      [pid, first_id(conn, 'work_packages', 'code', wp), first_id(conn, 'companies', 'name', company), first_id(conn, 'disciplines', 'name', discipline), first_id(conn, 'areas', 'code', area), first_id(conn, 'systems', 'code', system), code, desc, unit, baseline, weight, planned, 'QC accepted / handover gate required for 100%', status])
        pi = first_id(conn, 'progress_items', 'item_code', code)
        conn.execute("INSERT INTO daily_progress(project_id, progress_item_id, report_date, actual_qty, manpower, status, evidence, supervisor, validated) SELECT ?, ?, '2026-07-01', ?, 12, ?, 'Supervisor validation', 'Site Supervisor', 1 WHERE NOT EXISTS (SELECT 1 FROM daily_progress WHERE progress_item_id=? AND report_date='2026-07-01')", (pid, pi, actual, status, pi))

    insert_ignore(conn, 'meetings', ['project_id', 'meeting_date', 'meeting_type', 'title', 'participants', 'decisions', 'status', 'owner'],
                  [pid, '2026-07-01', 'daily coordination', 'Daily Construction Coordination', 'Doosan, JWW, MKL, Goodmont, SpecTech, Powerspex, HSE, QA/QC', 'Priorities confirmed. FRP workfront to be escalated.', 'approved', 'Site Administration'])
    meeting_id = conn.execute('SELECT id FROM meetings WHERE project_id=? ORDER BY id LIMIT 1', (pid,)).fetchone()['id']
    actions = [
        ('A-001', 'Powerspex to nominate permanent site representative and attend daily meetings.', 'Powerspex Electrical & Instrumentation', '2026-07-03', 'high'),
        ('A-002', 'BESIX to confirm workfront release for FRP penetrations.', 'BESIX', '2026-07-04', 'high'),
        ('A-003', 'JWW to submit mobilisation curve and weekly manpower forecast.', 'JWW Mechanical Erection', '2026-07-05', 'medium'),
    ]
    for no, desc, company, due, prio in actions:
        insert_ignore(conn, 'meeting_actions', ['meeting_id', 'project_id', 'action_no', 'description', 'responsible_company_id', 'due_date', 'priority', 'status'],
                      [meeting_id, pid, no, desc, first_id(conn, 'companies', 'name', company), due, prio, 'open'])

    sewo = [('SEWO-001', 'Additional temporary sealing for facade openings', 'BESIX'), ('SEWO-002', 'Additional scaffold modification for heavy boiler component', 'JWW Mechanical Erection')]
    for no, title, company in sewo:
        insert_ignore(conn, 'sewo_items', ['project_id', 'company_id', 'sewo_no', 'title', 'status', 'commercial_status', 'execution_status'],
                      [pid, first_id(conn, 'companies', 'name', company), no, title, 'submitted', 'under review', 'not started'])

    permits = [('PTW-2026-001', 'Hot Work', 'JWW Mechanical Erection', 'BA4', 'Welding at boiler support steel', 'approved'), ('PTW-2026-002', 'Confined Space', 'Goodmont Auxiliary Piping', 'BA5', 'Inspection inside tank connection area', 'requested')]
    for no, ptype, company, area, desc, status in permits:
        insert_ignore(conn, 'hse_permits', ['project_id', 'permit_no', 'permit_type', 'company_id', 'area_id', 'work_description', 'valid_from', 'valid_to', 'status', 'issuer', 'responsible', 'controls'],
                      [pid, no, ptype, first_id(conn, 'companies', 'name', company), first_id(conn, 'areas', 'code', area), desc, '2026-07-01', '2026-07-01', status, 'HSE Manager', 'Site Supervisor', 'Fire watch / gas check / rescue plan as applicable'])

    manpower = [('JWW Mechanical Erection', 'Kessel', 'BA4', 25, 250), ('MKL Stahlbau', 'Stahlbau', 'BA4', 18, 180), ('Goodmont Auxiliary Piping', 'Piping', 'BA5', 16, 160), ('SpecTech FRP Piping', 'Piping', 'BA5', 8, 80), ('Powerspex Electrical & Instrumentation', 'Electrical', 'BA4', 6, 60)]
    for company, discipline, area, workers, hours in manpower:
        conn.execute("INSERT INTO manpower_entries(project_id, company_id, discipline_id, area_id, entry_date, workers, hours, remarks) SELECT ?, ?, ?, ?, '2026-07-01', ?, ?, 'Daily contractor input' WHERE NOT EXISTS (SELECT 1 FROM manpower_entries WHERE project_id=? AND company_id=? AND entry_date='2026-07-01')", (pid, first_id(conn, 'companies', 'name', company), first_id(conn, 'disciplines', 'name', discipline), first_id(conn, 'areas', 'code', area), workers, hours, pid, first_id(conn, 'companies', 'name', company)))

    itps = [('ITP-PIP-001', 'Auxiliary piping erection and test pack ITP', 'Piping', 'Goodmont Auxiliary Piping', 'approved'), ('ITP-BOI-001', 'Boiler erection ITP', 'Kessel', 'JWW Mechanical Erection', 'for review'), ('ITP-ELE-001', 'Cable installation and termination ITP', 'Electrical', 'Powerspex Electrical & Instrumentation', 'draft')]
    for no, title, discipline, company, status in itps:
        insert_ignore(conn, 'itps', ['project_id', 'discipline_id', 'company_id', 'itp_no', 'title', 'revision', 'status', 'hold_points', 'witness_points', 'owner'],
                      [pid, first_id(conn, 'disciplines', 'name', discipline), first_id(conn, 'companies', 'name', company), no, title, 'A', status, 2, 4, 'QA/QC Manager'])

    mcs = [('MC-BOI-100', 'Boiler and Furnace MC Package', 'BOI-100', 'Kessel', 'JWW Mechanical Erection', 22), ('MC-PIP-210', 'Auxiliary Piping MC Package', 'PIP-210', 'Piping', 'Goodmont Auxiliary Piping', 15), ('MC-ELE-410', 'LV Electrical MC Package', 'ELE-410', 'Electrical', 'Powerspex Electrical & Instrumentation', 4)]
    for no, title, system, discipline, company, pct in mcs:
        insert_ignore(conn, 'mc_packages', ['project_id', 'system_id', 'package_no', 'title', 'discipline_id', 'company_id', 'status', 'completion_percent'],
                      [pid, first_id(conn, 'systems', 'code', system), no, title, first_id(conn, 'disciplines', 'name', discipline), first_id(conn, 'companies', 'name', company), 'open', pct])

    punches = [('P-0001', 'Missing torque record at platform BA4', 'B', 'Stahlbau', 'MKL Stahlbau', 'BA4', 'BOI-100'), ('P-0002', 'FRP penetration solution pending', 'A', 'Piping', 'SpecTech FRP Piping', 'BA5', 'FRP-330'), ('P-0003', 'Cable tray route clash with pipe support', 'B', 'Electrical', 'Powerspex Electrical & Instrumentation', 'BA4', 'ELE-410')]
    for no, title, cat, discipline, company, area, system in punches:
        insert_ignore(conn, 'punch_items', ['project_id', 'punch_no', 'title', 'category', 'status', 'discipline_id', 'company_id', 'area_id', 'system_id', 'responsible', 'due_date'],
                      [pid, no, title, cat, 'open', first_id(conn, 'disciplines', 'name', discipline), first_id(conn, 'companies', 'name', company), first_id(conn, 'areas', 'code', area), first_id(conn, 'systems', 'code', system), 'Site Supervisor', '2026-07-08'])

    conn.commit()
    conn.close()
    return DB_PATH


if __name__ == '__main__':
    print(initialize(reset=True))
