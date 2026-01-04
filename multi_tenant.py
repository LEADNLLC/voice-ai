"""
VOICE CRM - Multi-Tenant Client Management System
==================================================
Add this to voice_app.py to enable per-client tracking
"""

# ============================================
# DATABASE SCHEMA ADDITIONS
# ============================================

MULTI_TENANT_SCHEMA = """
-- Clients table (each business using your platform)
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    industry TEXT,
    plan TEXT DEFAULT 'starter',
    status TEXT DEFAULT 'active',
    monthly_budget REAL DEFAULT 500.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Client API integrations (each client's own credentials)
CREATE TABLE IF NOT EXISTS client_integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    integration_type TEXT NOT NULL,  -- 'retell', 'twilio', 'ghl', 'zapier', etc.
    api_key TEXT,
    api_secret TEXT,
    webhook_url TEXT,
    phone_number TEXT,
    agent_id TEXT,
    settings TEXT,  -- JSON for additional settings
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Client costs tracking (real-time cost per client)
CREATE TABLE IF NOT EXISTS client_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    cost_type TEXT NOT NULL,  -- 'retell_minutes', 'twilio_sms', 'ai_tokens', etc.
    quantity REAL DEFAULT 0,
    unit_cost REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    description TEXT,
    call_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Client monthly summaries
CREATE TABLE IF NOT EXISTS client_monthly_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    month TEXT NOT NULL,  -- '2026-01'
    total_calls INTEGER DEFAULT 0,
    total_minutes REAL DEFAULT 0,
    total_appointments INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0,
    total_revenue REAL DEFAULT 0,
    conversion_rate REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    UNIQUE(client_id, month)
);

-- Update leads table to include client_id
ALTER TABLE leads ADD COLUMN client_id INTEGER DEFAULT 1;

-- Update call_log table to include client_id  
ALTER TABLE call_log ADD COLUMN client_id INTEGER DEFAULT 1;

-- Client users (for client login)
CREATE TABLE IF NOT EXISTS client_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'user',  -- 'admin', 'manager', 'user'
    is_active INTEGER DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Admin users (your team)
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'admin',  -- 'superadmin', 'admin', 'support'
    is_active INTEGER DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Client pipelines (custom stages per client)
CREATE TABLE IF NOT EXISTS client_pipelines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    stages TEXT NOT NULL,  -- JSON array of stages
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_client ON leads(client_id);
CREATE INDEX IF NOT EXISTS idx_calls_client ON call_log(client_id);
CREATE INDEX IF NOT EXISTS idx_costs_client_date ON client_costs(client_id, date);
"""

# ============================================
# PYTHON FUNCTIONS
# ============================================

import uuid
import hashlib
import json
from datetime import datetime, timedelta

def generate_client_uuid():
    """Generate unique client identifier"""
    return str(uuid.uuid4())[:8]

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_multi_tenant_db():
    """Initialize multi-tenant database tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Execute schema (handle ALTER TABLE errors gracefully)
    for statement in MULTI_TENANT_SCHEMA.split(';'):
        statement = statement.strip()
        if statement:
            try:
                c.execute(statement)
            except sqlite3.OperationalError as e:
                if 'duplicate column' not in str(e).lower() and 'already exists' not in str(e).lower():
                    print(f"DB Warning: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Multi-tenant database initialized")

# ============================================
# CLIENT MANAGEMENT FUNCTIONS
# ============================================

def create_client(company_name, contact_name, email, phone, industry, plan='starter'):
    """Create a new client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    client_uuid = generate_client_uuid()
    
    c.execute('''INSERT INTO clients 
                 (uuid, company_name, contact_name, email, phone, industry, plan)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (client_uuid, company_name, contact_name, email, phone, industry, plan))
    
    client_id = c.lastrowid
    
    # Create default pipeline for client
    default_stages = json.dumps(['New', 'Contacted', 'Qualified', 'Appointment Set', 'Closed Won', 'Closed Lost'])
    c.execute('''INSERT INTO client_pipelines (client_id, name, stages, is_default)
                 VALUES (?, ?, ?, 1)''', (client_id, 'Default Pipeline', default_stages))
    
    conn.commit()
    conn.close()
    
    return {'id': client_id, 'uuid': client_uuid, 'company_name': company_name}

def get_all_clients():
    """Get all clients for admin view"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT c.*, 
                 (SELECT COUNT(*) FROM leads WHERE client_id = c.id) as lead_count,
                 (SELECT COUNT(*) FROM call_log WHERE client_id = c.id) as call_count,
                 (SELECT COALESCE(SUM(total_cost), 0) FROM client_costs WHERE client_id = c.id AND date >= date('now', '-30 days')) as monthly_cost
                 FROM clients c ORDER BY c.created_at DESC''')
    
    columns = [desc[0] for desc in c.description]
    clients = [dict(zip(columns, row)) for row in c.fetchall()]
    
    conn.close()
    return clients

def get_client(client_id):
    """Get single client with full details"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
    columns = [desc[0] for desc in c.description]
    row = c.fetchone()
    
    if not row:
        conn.close()
        return None
    
    client = dict(zip(columns, row))
    
    # Get integrations
    c.execute('SELECT * FROM client_integrations WHERE client_id = ?', (client_id,))
    columns = [desc[0] for desc in c.description]
    client['integrations'] = [dict(zip(columns, row)) for row in c.fetchall()]
    
    # Get stats
    c.execute('''SELECT 
                 COUNT(*) as total_leads,
                 SUM(CASE WHEN status = 'sold' THEN 1 ELSE 0 END) as sold,
                 SUM(CASE WHEN status = 'appointment_set' THEN 1 ELSE 0 END) as appointments
                 FROM leads WHERE client_id = ?''', (client_id,))
    stats = c.fetchone()
    client['stats'] = {
        'total_leads': stats[0] or 0,
        'sold': stats[1] or 0,
        'appointments': stats[2] or 0
    }
    
    # Get this month's cost
    c.execute('''SELECT COALESCE(SUM(total_cost), 0) FROM client_costs 
                 WHERE client_id = ? AND date >= date('now', '-30 days')''', (client_id,))
    client['monthly_cost'] = c.fetchone()[0]
    
    conn.close()
    return client

def get_client_by_uuid(uuid):
    """Get client by UUID (for API access)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM clients WHERE uuid = ?', (uuid,))
    columns = [desc[0] for desc in c.description]
    row = c.fetchone()
    conn.close()
    return dict(zip(columns, row)) if row else None

# ============================================
# CLIENT INTEGRATION FUNCTIONS
# ============================================

def add_client_integration(client_id, integration_type, api_key=None, api_secret=None, 
                           webhook_url=None, phone_number=None, agent_id=None, settings=None):
    """Add integration for a client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''INSERT INTO client_integrations 
                 (client_id, integration_type, api_key, api_secret, webhook_url, phone_number, agent_id, settings)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (client_id, integration_type, api_key, api_secret, webhook_url, phone_number, agent_id,
               json.dumps(settings) if settings else None))
    
    conn.commit()
    conn.close()
    return True

def get_client_integration(client_id, integration_type):
    """Get specific integration for client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT * FROM client_integrations 
                 WHERE client_id = ? AND integration_type = ? AND is_active = 1''',
              (client_id, integration_type))
    
    columns = [desc[0] for desc in c.description]
    row = c.fetchone()
    conn.close()
    
    if row:
        result = dict(zip(columns, row))
        if result.get('settings'):
            result['settings'] = json.loads(result['settings'])
        return result
    return None

# ============================================
# CLIENT COST TRACKING FUNCTIONS
# ============================================

def log_client_cost(client_id, cost_type, quantity, unit_cost, description=None, call_id=None):
    """Log a cost for a client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    total_cost = quantity * unit_cost
    today = datetime.now().strftime('%Y-%m-%d')
    
    c.execute('''INSERT INTO client_costs 
                 (client_id, date, cost_type, quantity, unit_cost, total_cost, description, call_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (client_id, today, cost_type, quantity, unit_cost, total_cost, description, call_id))
    
    conn.commit()
    conn.close()
    return total_cost

def get_client_costs(client_id, days=30):
    """Get client costs for period"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT date, cost_type, SUM(quantity) as quantity, SUM(total_cost) as total
                 FROM client_costs 
                 WHERE client_id = ? AND date >= date('now', ?)
                 GROUP BY date, cost_type
                 ORDER BY date DESC''', (client_id, f'-{days} days'))
    
    columns = ['date', 'cost_type', 'quantity', 'total']
    costs = [dict(zip(columns, row)) for row in c.fetchall()]
    
    # Get totals by type
    c.execute('''SELECT cost_type, SUM(total_cost) as total
                 FROM client_costs 
                 WHERE client_id = ? AND date >= date('now', ?)
                 GROUP BY cost_type''', (client_id, f'-{days} days'))
    
    totals = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    return {'daily': costs, 'totals': totals, 'grand_total': sum(totals.values())}

def get_client_dashboard_stats(client_id):
    """Get all dashboard stats for a client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    stats = {}
    
    # Lead stats
    c.execute('''SELECT 
                 COUNT(*) as total,
                 SUM(CASE WHEN created_at >= date('now', '-7 days') THEN 1 ELSE 0 END) as this_week,
                 SUM(CASE WHEN created_at >= date('now', '-30 days') THEN 1 ELSE 0 END) as this_month
                 FROM leads WHERE client_id = ?''', (client_id,))
    row = c.fetchone()
    stats['leads'] = {'total': row[0], 'this_week': row[1], 'this_month': row[2]}
    
    # Call stats
    c.execute('''SELECT 
                 COUNT(*) as total,
                 SUM(CASE WHEN created_at >= date('now', '-7 days') THEN 1 ELSE 0 END) as this_week,
                 SUM(CASE WHEN created_at >= date('now', '-30 days') THEN 1 ELSE 0 END) as this_month
                 FROM call_log WHERE client_id = ?''', (client_id,))
    row = c.fetchone()
    stats['calls'] = {'total': row[0], 'this_week': row[1], 'this_month': row[2]}
    
    # Conversion stats
    c.execute('''SELECT 
                 SUM(CASE WHEN status = 'appointment_set' THEN 1 ELSE 0 END) as appointments,
                 SUM(CASE WHEN status = 'sold' THEN 1 ELSE 0 END) as sold
                 FROM leads WHERE client_id = ?''', (client_id,))
    row = c.fetchone()
    stats['conversions'] = {'appointments': row[0] or 0, 'sold': row[1] or 0}
    
    # Cost stats
    c.execute('''SELECT COALESCE(SUM(total_cost), 0) FROM client_costs 
                 WHERE client_id = ? AND date >= date('now', '-30 days')''', (client_id,))
    stats['monthly_cost'] = c.fetchone()[0]
    
    # Pipeline breakdown
    c.execute('''SELECT status, COUNT(*) as count FROM leads 
                 WHERE client_id = ? GROUP BY status''', (client_id,))
    stats['pipeline'] = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    return stats

# ============================================
# CLIENT-SPECIFIC CALL FUNCTION
# ============================================

def make_client_call(client_id, phone, name="there", agent_type="roofing", is_inbound=False):
    """Make a call using client's own integrations"""
    
    # Get client's Retell integration
    retell_integration = get_client_integration(client_id, 'retell')
    
    if not retell_integration:
        return {'error': 'No Retell integration configured', 'success': False}
    
    api_key = retell_integration.get('api_key')
    phone_number = retell_integration.get('phone_number')
    agent_id = retell_integration.get('agent_id')
    
    if not all([api_key, phone_number, agent_id]):
        return {'error': 'Incomplete Retell configuration', 'success': False}
    
    # Get client info for dynamic variables
    client = get_client(client_id)
    company_name = client.get('company_name', 'Our Company')
    industry = client.get('industry', agent_type)
    
    try:
        response = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "agent_id": agent_id,
                "from_number": phone_number,
                "to_number": phone,
                "retell_llm_dynamic_variables": {
                    "company_name": company_name,
                    "industry": industry,
                    "customer_name": name
                }
            },
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            call_id = data.get('call_id', '')
            
            # Log cost for this client
            log_client_cost(client_id, 'retell_call', 1, 0.10, f'Call to {phone}', call_id)
            
            return {"success": True, "call_id": call_id}
        else:
            return {"error": response.text, "success": False}
            
    except Exception as e:
        return {"error": str(e), "success": False}
