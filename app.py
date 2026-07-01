import csv
import html
import io
import mimetypes
import sqlite3
import sys
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from seed import DB_PATH, initialize

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
PROJECT_CODE = 'A.14002'

MODULES = {
    'companies': ('Firmen', 'companies', 'SELECT id, name AS Firma, type AS Typ, discipline_hint AS Gewerk, contact_person AS Kontakt, status AS Status FROM companies ORDER BY name'),
    'contracts': ('Vertraege', 'contracts', 'SELECT c.id, c.contract_no AS Vertrag, c.title AS Titel, co.name AS Firma, c.commercial_status AS Status, c.risk_level AS Risiko, c.owner AS Owner FROM contracts c LEFT JOIN companies co ON co.id=c.company_id WHERE c.project_id=? ORDER BY c.risk_level DESC, c.contract_no'),
    'documents': ('Dokumente', 'documents', 'SELECT d.id, d.document_no AS Dokument, d.title AS Titel, d.document_type AS Typ, d.revision AS Rev, d.status AS Status, co.name AS Firma, d.owner AS Owner FROM documents d LEFT JOIN companies co ON co.id=d.company_id WHERE d.project_id=? ORDER BY d.document_no'),
    'drawings': ('Zeichnungen', 'drawings', 'SELECT dr.id, dr.drawing_no AS Zeichnung, dr.title AS Titel, dr.revision AS Rev, dr.status AS Status, co.name AS Firma, a.code AS Area, s.code AS System, dr.redline_status AS Redline FROM drawings dr LEFT JOIN companies co ON co.id=dr.company_id LEFT JOIN areas a ON a.id=dr.area_id LEFT JOIN systems s ON s.id=dr.system_id WHERE dr.project_id=? ORDER BY dr.drawing_no'),
    'meetings': ('Meetings', 'meetings', 'SELECT id, meeting_date AS Datum, meeting_type AS Typ, title AS Titel, status AS Status, owner AS Owner, participants AS Teilnehmer FROM meetings WHERE project_id=? ORDER BY meeting_date DESC'),
    'actions': ('Actions', 'meeting_actions', 'SELECT ma.id, ma.action_no AS Nr, ma.description AS Beschreibung, co.name AS Firma, ma.due_date AS Faellig, ma.priority AS Prioritaet, ma.status AS Status FROM meeting_actions ma LEFT JOIN companies co ON co.id=ma.responsible_company_id WHERE ma.project_id=? ORDER BY ma.due_date'),
    'progress': ('Progress', 'progress_items', 'SELECT pi.id, pi.item_code AS Code, pi.description AS Beschreibung, co.name AS Firma, di.name AS Gewerk, a.code AS Area, pi.unit AS Einheit, pi.baseline_qty AS Baseline, COALESCE(SUM(dp.actual_qty),0) AS Ist, ROUND(MIN(COALESCE(SUM(dp.actual_qty),0)/NULLIF(pi.baseline_qty,0),1)*100,1) AS Ist_Prozent, pi.planned_percent AS Plan_Prozent, pi.status AS Status FROM progress_items pi LEFT JOIN daily_progress dp ON dp.progress_item_id=pi.id LEFT JOIN companies co ON co.id=pi.company_id LEFT JOIN disciplines di ON di.id=pi.discipline_id LEFT JOIN areas a ON a.id=pi.area_id WHERE pi.project_id=? GROUP BY pi.id ORDER BY co.name'),
    'daily_progress': ('Daily Input', 'daily_progress', 'SELECT dp.id, dp.report_date AS Datum, pi.item_code AS Progress_Item, co.name AS Firma, dp.actual_qty AS Menge, pi.unit AS Einheit, dp.manpower AS Mannstunden, dp.status AS Status, dp.blocker AS Blocker, dp.validated AS Validiert FROM daily_progress dp JOIN progress_items pi ON pi.id=dp.progress_item_id LEFT JOIN companies co ON co.id=pi.company_id WHERE dp.project_id=? ORDER BY dp.report_date DESC'),
    'sewo': ('SEWO', 'sewo_items', 'SELECT se.id, se.sewo_no AS SEWO, se.title AS Titel, co.name AS Firma, se.status AS Status, se.commercial_status AS Commercial, se.execution_status AS Ausfuehrung FROM sewo_items se LEFT JOIN companies co ON co.id=se.company_id WHERE se.project_id=? ORDER BY se.sewo_no'),
    'permits': ('Permits', 'hse_permits', 'SELECT p.id, p.permit_no AS Permit, p.permit_type AS Typ, co.name AS Firma, a.code AS Area, p.valid_from AS Von, p.valid_to AS Bis, p.status AS Status, p.responsible AS Verantwortlich FROM hse_permits p LEFT JOIN companies co ON co.id=p.company_id LEFT JOIN areas a ON a.id=p.area_id WHERE p.project_id=? ORDER BY p.valid_from DESC'),
    'manpower': ('Mannstunden', 'manpower_entries', 'SELECT mp.id, mp.entry_date AS Datum, co.name AS Firma, di.name AS Gewerk, a.code AS Area, mp.workers AS Mitarbeiter, mp.hours AS Stunden, mp.shift AS Schicht FROM manpower_entries mp LEFT JOIN companies co ON co.id=mp.company_id LEFT JOIN disciplines di ON di.id=mp.discipline_id LEFT JOIN areas a ON a.id=mp.area_id WHERE mp.project_id=? ORDER BY mp.entry_date DESC'),
    'hse': ('HSE Beobachtungen', 'hse_observations', 'SELECT h.id, h.observation_date AS Datum, co.name AS Firma, a.code AS Area, h.category AS Kategorie, h.description AS Beschreibung, h.responsible AS Verantwortlich, h.status AS Status FROM hse_observations h LEFT JOIN companies co ON co.id=h.company_id LEFT JOIN areas a ON a.id=h.area_id WHERE h.project_id=? ORDER BY h.observation_date DESC'),
    'incidents': ('Unfallberichte', 'incidents', 'SELECT i.id, i.incident_date AS Datum, co.name AS Firma, a.code AS Area, i.incident_type AS Typ, i.severity AS Schwere, i.status AS Status, i.description AS Beschreibung FROM incidents i LEFT JOIN companies co ON co.id=i.company_id LEFT JOIN areas a ON a.id=i.area_id WHERE i.project_id=? ORDER BY i.incident_date DESC'),
    'itp': ('ITP / Quality', 'itps', 'SELECT it.id, it.itp_no AS ITP, it.title AS Titel, di.name AS Gewerk, co.name AS Firma, it.revision AS Rev, it.status AS Status, it.hold_points AS Hold, it.witness_points AS Witness FROM itps it LEFT JOIN disciplines di ON di.id=it.discipline_id LEFT JOIN companies co ON co.id=it.company_id WHERE it.project_id=? ORDER BY it.itp_no'),
    'mc': ('Mechanical Completion', 'mc_packages', 'SELECT mc.id, mc.package_no AS Paket, mc.title AS Titel, s.code AS System, co.name AS Firma, mc.completion_percent AS Prozent, mc.status AS Status FROM mc_packages mc LEFT JOIN systems s ON s.id=mc.system_id LEFT JOIN companies co ON co.id=mc.company_id WHERE mc.project_id=? ORDER BY mc.package_no'),
    'punch': ('Punch Items', 'punch_items', 'SELECT p.id, p.punch_no AS Punch, p.title AS Titel, p.category AS Kategorie, p.status AS Status, co.name AS Firma, a.code AS Area, s.code AS System, p.responsible AS Verantwortlich, p.due_date AS Faellig FROM punch_items p LEFT JOIN companies co ON co.id=p.company_id LEFT JOIN areas a ON a.id=p.area_id LEFT JOIN systems s ON s.id=p.system_id WHERE p.project_id=? ORDER BY p.category, p.due_date'),
    'photos': ('Fotos', 'photos', 'SELECT ph.id, ph.photo_date AS Datum, ph.title AS Titel, co.name AS Firma, a.code AS Area, ph.drawing_ref AS Zeichnung, ph.file_ref AS Datei FROM photos ph LEFT JOIN companies co ON co.id=ph.company_id LEFT JOIN areas a ON a.id=ph.area_id WHERE ph.project_id=? ORDER BY ph.photo_date DESC'),
}

FORM_FIELDS = {
    'contracts': [('company_id','Firma','companies'),('contract_no','Vertragsnummer','text'),('title','Titel','text'),('contract_type','Typ','text'),('scope_summary','Scope','textarea'),('commercial_status','Status','text'),('risk_level','Risiko','text'),('owner','Owner','text')],
    'documents': [('document_no','Dokumentnummer','text'),('title','Titel','text'),('document_type','Typ','text'),('revision','Revision','text'),('status','Status','text'),('company_id','Firma','companies'),('owner','Owner','text'),('file_ref','Datei/DMS','text')],
    'actions': [('action_no','Action Nr.','text'),('description','Beschreibung','textarea'),('responsible_company_id','Firma','companies'),('responsible_user','Verantwortlich','text'),('due_date','Faelligkeit','date'),('priority','Prioritaet','text'),('status','Status','text')],
    'daily_progress': [('progress_item_id','Progress Item','progress_items'),('report_date','Datum','date'),('actual_qty','Ist-Menge','number'),('manpower','Mannstunden','number'),('status','Status','text'),('blocker','Blocker','textarea'),('evidence','Nachweis','textarea'),('supervisor','Supervisor','text'),('validated','Validiert 0/1','number')],
    'permits': [('permit_no','Permit Nr.','text'),('permit_type','Typ','text'),('company_id','Firma','companies'),('area_id','Area','areas'),('work_description','Arbeitsbeschreibung','textarea'),('valid_from','Von','date'),('valid_to','Bis','date'),('status','Status','text'),('issuer','Aussteller','text'),('responsible','Verantwortlich','text'),('controls','Massnahmen','textarea')],
    'punch': [('punch_no','Punch Nr.','text'),('title','Titel','text'),('description','Beschreibung','textarea'),('category','Kategorie','text'),('status','Status','text'),('company_id','Firma','companies'),('area_id','Area','areas'),('system_id','System','systems'),('responsible','Verantwortlich','text'),('due_date','Faelligkeit','date')],
    'sewo': [('company_id','Firma','companies'),('sewo_no','SEWO Nr.','text'),('title','Titel','text'),('description','Beschreibung','textarea'),('status','Status','text'),('commercial_status','Commercial','text'),('execution_status','Ausfuehrung','text'),('due_date','Faelligkeit','date')],
    'manpower': [('company_id','Firma','companies'),('discipline_id','Gewerk','disciplines'),('area_id','Area','areas'),('entry_date','Datum','date'),('workers','Mitarbeiter','number'),('hours','Stunden','number'),('shift','Schicht','text'),('remarks','Bemerkung','textarea')],
}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def project_id(conn):
    row = conn.execute('SELECT id FROM projects WHERE code=?', (PROJECT_CODE,)).fetchone()
    return row['id'] if row else 1


def esc(value):
    return html.escape('' if value is None else str(value), quote=True)


def table(rows):
    if not rows:
        return '<div class="empty">Keine Eintraege vorhanden.</div>'
    heads = [h for h in rows[0].keys() if h != 'id']
    html_rows = []
    for r in rows:
        cells = ''.join(f'<td class="{status_class(r[h])}">{esc(r[h])}</td>' for h in heads)
        html_rows.append(f'<tr>{cells}</tr>')
    return '<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th>{esc(h)}</th>' for h in heads) + '</tr></thead><tbody>' + ''.join(html_rows) + '</tbody></table></div>'


def status_class(value):
    text = str(value or '').lower()
    if text in {'red','blocked','rejected','critical','a'}:
        return 'bad'
    if text in {'yellow','open','requested','for review','draft','in progress','submitted','under review'}:
        return 'warn'
    if text in {'green','approved','accepted','closed','active','valid'}:
        return 'good'
    return ''


def rows_for(conn, key):
    title, source, sql = MODULES[key]
    if 'WHERE' in sql and 'project_id=?' in sql:
        return conn.execute(sql, (project_id(conn),)).fetchall()
    return conn.execute(sql).fetchall()


def options(conn, table_name):
    label = {'companies':'name','areas':'code','systems':'code','disciplines':'name','progress_items':'item_code'}.get(table_name, 'name')
    if table_name in {'areas','systems','progress_items'}:
        return conn.execute(f'SELECT id, {label} AS label FROM {table_name} WHERE project_id=? ORDER BY {label}', (project_id(conn),)).fetchall()
    return conn.execute(f'SELECT id, {label} AS label FROM {table_name} ORDER BY {label}').fetchall()


def layout(title, body, active='dashboard'):
    nav = '<a class="%s" href="/">OV Dashboard</a>' % ('active' if active == 'dashboard' else '')
    nav += '<a class="%s" href="/weekly-report">WR Wochenreport</a>' % ('active' if active == 'report' else '')
    for key, (label, _, _) in MODULES.items():
        nav += f'<a class="{"active" if key == active else ""}" href="/module/{key}">{esc(label)}</a>'
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title><link rel="stylesheet" href="/static/styles.css"></head><body><aside><h1>Construction DB</h1><small>A.14002 SSI Flanders</small><nav>{nav}</nav></aside><main><header><form action="/search"><input name="q" placeholder="Globale Suche"><button>Suchen</button></form><button onclick="window.print()">Drucken / PDF</button></header>{body}</main><script src="/static/app.js"></script></body></html>'''


def dashboard(conn):
    pid = project_id(conn)
    progress = conn.execute('SELECT pi.baseline_qty, pi.weight, pi.planned_percent, COALESCE(SUM(dp.actual_qty),0) actual FROM progress_items pi LEFT JOIN daily_progress dp ON dp.progress_item_id=pi.id WHERE pi.project_id=? GROUP BY pi.id', (pid,)).fetchall()
    total = sum(float(r['weight'] or 0) for r in progress) or 1
    actual = sum(min((float(r['actual'] or 0) / float(r['baseline_qty'] or 1)), 1) * float(r['weight'] or 0) for r in progress) / total * 100
    planned = sum(float(r['planned_percent'] or 0) / 100 * float(r['weight'] or 0) for r in progress) / total * 100
    cards = [
        ('Ist-Progress', f'{actual:.1f}%'), ('Plan', f'{planned:.1f}%'), ('Delta', f'{actual-planned:.1f}%'),
        ('Offene Actions', conn.execute("SELECT COUNT(*) FROM meeting_actions WHERE project_id=? AND status NOT IN ('closed','accepted')", (pid,)).fetchone()[0]),
        ('Offene Punches', conn.execute("SELECT COUNT(*) FROM punch_items WHERE project_id=? AND status NOT IN ('closed','accepted')", (pid,)).fetchone()[0]),
        ('Aktive Permits', conn.execute("SELECT COUNT(*) FROM hse_permits WHERE project_id=? AND status IN ('approved','requested')", (pid,)).fetchone()[0]),
        ('SEWO offen', conn.execute("SELECT COUNT(*) FROM sewo_items WHERE project_id=? AND status NOT IN ('closed','accepted','rejected')", (pid,)).fetchone()[0]),
        ('Mannstunden', conn.execute('SELECT COALESCE(SUM(hours),0) FROM manpower_entries WHERE project_id=?', (pid,)).fetchone()[0]),
    ]
    card_html = ''.join(f'<section class="metric"><span>{esc(k)}</span><strong>{esc(v)}</strong></section>' for k, v in cards)
    contractor = conn.execute("SELECT co.name Firma, ROUND(SUM(MIN(COALESCE(x.actual,0)/NULLIF(pi.baseline_qty,0),1)*pi.weight)/NULLIF(SUM(pi.weight),0)*100,1) Progress FROM progress_items pi LEFT JOIN companies co ON co.id=pi.company_id LEFT JOIN (SELECT progress_item_id, SUM(actual_qty) actual FROM daily_progress GROUP BY progress_item_id) x ON x.progress_item_id=pi.id WHERE pi.project_id=? GROUP BY co.name ORDER BY co.name", (pid,)).fetchall()
    actions = conn.execute('SELECT action_no Nr, description Beschreibung, due_date Faellig, priority Prioritaet, status Status FROM meeting_actions WHERE project_id=? ORDER BY due_date LIMIT 8', (pid,)).fetchall()
    body = f'<section class="hero"><h2>Zentrale Baustellensteuerung fuer Construction, HSE, Quality, Commercial und Commissioning</h2><p>Vertraege, Dokumente, Meetings, Progress, SEWO, Permits, ITP, MC und Punch in einer Plattform.</p></section><section class="metrics">{card_html}</section><section class="grid"><article><h2>Progress je Nachunternehmer</h2>{table(contractor)}</article><article><h2>Naechste Actions</h2>{table(actions)}</article></section>'
    return layout('Dashboard', body)


def module_page(conn, key):
    if key not in MODULES:
        return layout('Fehler', '<h2>Modul nicht gefunden</h2>')
    title = MODULES[key][0]
    new_button = f'<a class="button primary" href="/new/{key}">Neu</a>' if key in FORM_FIELDS else ''
    body = f'<section class="page-head"><h2>{esc(title)}</h2><div>{new_button}<a class="button" href="/export/{key}.csv">CSV</a></div></section><article>{table(rows_for(conn, key))}</article>'
    return layout(title, body, key)


def form_page(conn, key):
    fields = []
    for name, label, kind in FORM_FIELDS[key]:
        if kind == 'textarea':
            control = f'<textarea name="{name}"></textarea>'
        elif kind in {'companies','areas','systems','disciplines','progress_items'}:
            opts = '<option value="">-- waehlen --</option>' + ''.join(f'<option value="{r["id"]}">{esc(r["label"])}</option>' for r in options(conn, kind))
            control = f'<select name="{name}">{opts}</select>'
        elif kind == 'date':
            control = f'<input type="date" name="{name}" value="{date.today().isoformat()}">'
        elif kind == 'number':
            control = f'<input type="number" step="0.01" name="{name}" value="0">'
        else:
            control = f'<input name="{name}">' 
        fields.append(f'<label><span>{esc(label)}</span>{control}</label>')
    return layout('Neu', f'<section class="page-head"><h2>Neu: {esc(MODULES[key][0])}</h2></section><form class="record-form" method="post" action="/create/{key}">{"".join(fields)}<button class="primary">Speichern</button></form>', key)


def create_record(conn, key, form):
    table_name = MODULES[key][1]
    cols = ['project_id']
    vals = [project_id(conn)]
    for name, _, _ in FORM_FIELDS[key]:
        cols.append(name)
        vals.append(form.get(name, [''])[0])
    conn.execute(f'INSERT INTO {table_name} ({", ".join(cols)}) VALUES ({", ".join("?" for _ in cols)})', vals)
    entity_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.execute('INSERT INTO audit_log(project_id, entity, entity_id, action, summary, actor) VALUES (?, ?, ?, ?, ?, ?)', (project_id(conn), table_name, entity_id, 'created', key, 'local user'))
    conn.commit()


def search_page(conn, query):
    pid = project_id(conn)
    q = '%' + query + '%'
    searches = [
        ('Vertraege', 'SELECT contract_no Nr, title Titel, commercial_status Status FROM contracts WHERE project_id=? AND (contract_no LIKE ? OR title LIKE ? OR scope_summary LIKE ?)', (pid,q,q,q)),
        ('Dokumente', 'SELECT document_no Nr, title Titel, status Status FROM documents WHERE project_id=? AND (document_no LIKE ? OR title LIKE ?)', (pid,q,q)),
        ('Zeichnungen', 'SELECT drawing_no Nr, title Titel, status Status FROM drawings WHERE project_id=? AND (drawing_no LIKE ? OR title LIKE ?)', (pid,q,q)),
        ('Progress', 'SELECT item_code Nr, description Titel, status Status FROM progress_items WHERE project_id=? AND (item_code LIKE ? OR description LIKE ?)', (pid,q,q)),
        ('SEWO', 'SELECT sewo_no Nr, title Titel, status Status FROM sewo_items WHERE project_id=? AND (sewo_no LIKE ? OR title LIKE ?)', (pid,q,q)),
        ('Punch', 'SELECT punch_no Nr, title Titel, status Status FROM punch_items WHERE project_id=? AND (punch_no LIKE ? OR title LIKE ?)', (pid,q,q)),
    ]
    body = '<section class="page-head"><h2>Suche: %s</h2></section>' % esc(query)
    body += '<section class="grid">' + ''.join(f'<article><h2>{esc(t)}</h2>{table(conn.execute(sql,args).fetchall())}</article>' for t, sql, args in searches) + '</section>'
    return layout('Suche', body)


def weekly_report(conn):
    pid = project_id(conn)
    body = '<section class="page-head"><h2>Wochenreport Construction</h2><p>Automatisch generiert am %s</p></section>' % esc(datetime.now().strftime('%d.%m.%Y %H:%M'))
    for key in ['progress', 'actions', 'permits', 'punch', 'sewo', 'manpower']:
        body += f'<article><h2>{esc(MODULES[key][0])}</h2>{table(rows_for(conn, key))}</article>'
    return layout('Wochenreport', body, 'report')


def export_csv(conn, key):
    rows = rows_for(conn, key)
    headers = [h for h in rows[0].keys() if h != 'id'] if rows else []
    out = io.StringIO()
    writer = csv.writer(out, delimiter=';')
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row[h] for h in headers])
    return out.getvalue().encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path.startswith('/static/'):
                return self.static(path)
            with db() as conn:
                if path == '/':
                    return self.html(dashboard(conn))
                if path == '/weekly-report':
                    return self.html(weekly_report(conn))
                if path == '/search':
                    return self.html(search_page(conn, parse_qs(parsed.query).get('q', [''])[0]))
                if path.startswith('/module/'):
                    return self.html(module_page(conn, path.split('/')[-1]))
                if path.startswith('/new/'):
                    return self.html(form_page(conn, path.split('/')[-1]))
                if path.startswith('/export/') and path.endswith('.csv'):
                    key = Path(path).stem
                    return self.bytes(export_csv(conn, key), 'text/csv; charset=utf-8', f'{key}.csv')
            return self.html(layout('404', '<h2>Nicht gefunden</h2>'), 404)
        except Exception as exc:
            return self.html(layout('Fehler', f'<h2>Fehler</h2><pre>{esc(exc)}</pre>'), 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            form = parse_qs(self.rfile.read(length).decode('utf-8'))
            if path.startswith('/create/'):
                key = path.split('/')[-1]
                with db() as conn:
                    create_record(conn, key, form)
                self.send_response(303)
                self.send_header('Location', f'/module/{quote(key)}')
                self.end_headers()
                return
            self.html(layout('404', '<h2>Nicht gefunden</h2>'), 404)
        except Exception as exc:
            self.html(layout('Fehler', f'<h2>Fehler</h2><pre>{esc(exc)}</pre>'), 500)

    def static(self, path):
        rel = path.removeprefix('/static/').strip('/')
        target = (STATIC_DIR / rel).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists():
            self.send_error(404)
            return
        self.bytes(target.read_bytes(), mimetypes.guess_type(target.name)[0] or 'application/octet-stream')

    def html(self, text, status=200):
        self.bytes(text.encode('utf-8'), 'text/html; charset=utf-8', None, status)

    def bytes(self, payload, content_type, filename=None, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(payload)


def main():
    initialize(reset=not DB_PATH.exists())
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'Construction Site DB running on http://127.0.0.1:{port}')
    server.serve_forever()


if __name__ == '__main__':
    main()
