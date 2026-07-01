PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  client TEXT DEFAULT '',
  location TEXT DEFAULT '',
  pac_target TEXT DEFAULT '',
  status TEXT DEFAULT 'active',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  type TEXT DEFAULT 'subcontractor',
  discipline_hint TEXT DEFAULT '',
  contact_person TEXT DEFAULT '',
  email TEXT DEFAULT '',
  status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS disciplines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  unit_examples TEXT DEFAULT '',
  description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS areas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  UNIQUE(project_id, code)
);

CREATE TABLE IF NOT EXISTS systems (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  discipline_id INTEGER REFERENCES disciplines(id),
  status TEXT DEFAULT 'open',
  UNIQUE(project_id, code)
);

CREATE TABLE IF NOT EXISTS contracts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  company_id INTEGER REFERENCES companies(id),
  contract_no TEXT NOT NULL,
  title TEXT NOT NULL,
  contract_type TEXT DEFAULT 'subcontract',
  scope_summary TEXT DEFAULT '',
  commercial_status TEXT DEFAULT 'valid',
  risk_level TEXT DEFAULT 'green',
  owner TEXT DEFAULT '',
  UNIQUE(project_id, contract_no)
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  document_no TEXT NOT NULL,
  title TEXT NOT NULL,
  document_type TEXT DEFAULT 'general',
  revision TEXT DEFAULT '0',
  status TEXT DEFAULT 'draft',
  discipline_id INTEGER REFERENCES disciplines(id),
  company_id INTEGER REFERENCES companies(id),
  file_ref TEXT DEFAULT '',
  owner TEXT DEFAULT '',
  UNIQUE(project_id, document_no, revision)
);

CREATE TABLE IF NOT EXISTS drawings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  drawing_no TEXT NOT NULL,
  title TEXT NOT NULL,
  revision TEXT DEFAULT '0',
  status TEXT DEFAULT 'for construction',
  discipline_id INTEGER REFERENCES disciplines(id),
  company_id INTEGER REFERENCES companies(id),
  area_id INTEGER REFERENCES areas(id),
  system_id INTEGER REFERENCES systems(id),
  redline_status TEXT DEFAULT 'open',
  as_built_status TEXT DEFAULT 'open',
  UNIQUE(project_id, drawing_no, revision)
);

CREATE TABLE IF NOT EXISTS meetings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  meeting_date TEXT NOT NULL,
  meeting_type TEXT DEFAULT 'daily coordination',
  title TEXT NOT NULL,
  participants TEXT DEFAULT '',
  decisions TEXT DEFAULT '',
  status TEXT DEFAULT 'draft',
  owner TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS meeting_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  meeting_id INTEGER REFERENCES meetings(id),
  action_no TEXT NOT NULL,
  description TEXT NOT NULL,
  responsible_company_id INTEGER REFERENCES companies(id),
  responsible_user TEXT DEFAULT '',
  due_date TEXT DEFAULT '',
  priority TEXT DEFAULT 'medium',
  status TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS work_packages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  discipline_id INTEGER REFERENCES disciplines(id),
  company_id INTEGER REFERENCES companies(id),
  area_id INTEGER REFERENCES areas(id),
  system_id INTEGER REFERENCES systems(id),
  status TEXT DEFAULT 'open',
  UNIQUE(project_id, code)
);

CREATE TABLE IF NOT EXISTS progress_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  work_package_id INTEGER REFERENCES work_packages(id),
  company_id INTEGER REFERENCES companies(id),
  discipline_id INTEGER REFERENCES disciplines(id),
  area_id INTEGER REFERENCES areas(id),
  system_id INTEGER REFERENCES systems(id),
  item_code TEXT NOT NULL,
  description TEXT NOT NULL,
  unit TEXT NOT NULL,
  baseline_qty REAL DEFAULT 0,
  weight REAL DEFAULT 1,
  planned_percent REAL DEFAULT 0,
  qa_gate TEXT DEFAULT '',
  status TEXT DEFAULT 'not started',
  UNIQUE(project_id, item_code)
);

CREATE TABLE IF NOT EXISTS daily_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  progress_item_id INTEGER NOT NULL REFERENCES progress_items(id),
  report_date TEXT NOT NULL,
  actual_qty REAL DEFAULT 0,
  manpower REAL DEFAULT 0,
  status TEXT DEFAULT 'in progress',
  blocker TEXT DEFAULT '',
  evidence TEXT DEFAULT '',
  supervisor TEXT DEFAULT '',
  validated INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sewo_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  company_id INTEGER REFERENCES companies(id),
  sewo_no TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  status TEXT DEFAULT 'draft',
  commercial_status TEXT DEFAULT 'not submitted',
  execution_status TEXT DEFAULT 'not started',
  due_date TEXT DEFAULT '',
  UNIQUE(project_id, sewo_no)
);

CREATE TABLE IF NOT EXISTS hse_permits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  permit_no TEXT NOT NULL,
  permit_type TEXT NOT NULL,
  company_id INTEGER REFERENCES companies(id),
  area_id INTEGER REFERENCES areas(id),
  work_description TEXT NOT NULL,
  valid_from TEXT DEFAULT '',
  valid_to TEXT DEFAULT '',
  status TEXT DEFAULT 'requested',
  issuer TEXT DEFAULT '',
  responsible TEXT DEFAULT '',
  controls TEXT DEFAULT '',
  UNIQUE(project_id, permit_no)
);

CREATE TABLE IF NOT EXISTS manpower_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  company_id INTEGER REFERENCES companies(id),
  discipline_id INTEGER REFERENCES disciplines(id),
  area_id INTEGER REFERENCES areas(id),
  entry_date TEXT NOT NULL,
  workers INTEGER DEFAULT 0,
  hours REAL DEFAULT 0,
  shift TEXT DEFAULT 'day',
  remarks TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS hse_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  observation_date TEXT NOT NULL,
  company_id INTEGER REFERENCES companies(id),
  area_id INTEGER REFERENCES areas(id),
  category TEXT DEFAULT 'observation',
  description TEXT NOT NULL,
  action_required TEXT DEFAULT '',
  responsible TEXT DEFAULT '',
  due_date TEXT DEFAULT '',
  status TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  incident_date TEXT NOT NULL,
  company_id INTEGER REFERENCES companies(id),
  area_id INTEGER REFERENCES areas(id),
  incident_type TEXT NOT NULL,
  severity TEXT DEFAULT 'low',
  description TEXT NOT NULL,
  immediate_action TEXT DEFAULT '',
  root_cause TEXT DEFAULT '',
  status TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS itps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  discipline_id INTEGER REFERENCES disciplines(id),
  company_id INTEGER REFERENCES companies(id),
  itp_no TEXT NOT NULL,
  title TEXT NOT NULL,
  revision TEXT DEFAULT '0',
  status TEXT DEFAULT 'draft',
  hold_points INTEGER DEFAULT 0,
  witness_points INTEGER DEFAULT 0,
  owner TEXT DEFAULT '',
  UNIQUE(project_id, itp_no, revision)
);

CREATE TABLE IF NOT EXISTS mc_packages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  system_id INTEGER REFERENCES systems(id),
  package_no TEXT NOT NULL,
  title TEXT NOT NULL,
  discipline_id INTEGER REFERENCES disciplines(id),
  company_id INTEGER REFERENCES companies(id),
  status TEXT DEFAULT 'open',
  completion_percent REAL DEFAULT 0,
  handover_date TEXT DEFAULT '',
  dossier_ref TEXT DEFAULT '',
  UNIQUE(project_id, package_no)
);

CREATE TABLE IF NOT EXISTS punch_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  punch_no TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  category TEXT DEFAULT 'B',
  status TEXT DEFAULT 'open',
  discipline_id INTEGER REFERENCES disciplines(id),
  company_id INTEGER REFERENCES companies(id),
  area_id INTEGER REFERENCES areas(id),
  system_id INTEGER REFERENCES systems(id),
  mc_package_id INTEGER REFERENCES mc_packages(id),
  responsible TEXT DEFAULT '',
  due_date TEXT DEFAULT '',
  evidence TEXT DEFAULT '',
  UNIQUE(project_id, punch_no)
);

CREATE TABLE IF NOT EXISTS photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  photo_date TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  company_id INTEGER REFERENCES companies(id),
  discipline_id INTEGER REFERENCES disciplines(id),
  area_id INTEGER REFERENCES areas(id),
  system_id INTEGER REFERENCES systems(id),
  drawing_ref TEXT DEFAULT '',
  file_ref TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  entity TEXT NOT NULL,
  entity_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  summary TEXT DEFAULT '',
  actor TEXT DEFAULT 'system',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_progress_project ON progress_items(project_id, company_id, discipline_id);
CREATE INDEX IF NOT EXISTS idx_daily_item ON daily_progress(progress_item_id, report_date);
CREATE INDEX IF NOT EXISTS idx_punch_status ON punch_items(project_id, status, category);
CREATE INDEX IF NOT EXISTS idx_permit_status ON hse_permits(project_id, status);
