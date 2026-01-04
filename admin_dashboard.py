"""
ADMIN DASHBOARD - Add to voice_app.py
=====================================
Paste this HTML into your app to get the admin panel
"""

ADMIN_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOICE Admin - Client Management</title>
<style>
:root{--bg:#0a0a0f;--card:#12121a;--border:#1e1e2e;--cyan:#00d1ff;--green:#10b981;--red:#ef4444;--yellow:#f59e0b;--gray:#6b7280;--text:#f5f5f5}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}

/* Sidebar */
.admin-layout{display:flex;min-height:100vh}
.sidebar{width:260px;background:var(--card);border-right:1px solid var(--border);padding:24px 0;position:fixed;height:100vh;overflow-y:auto}
.sidebar-logo{padding:0 24px 32px;font-size:24px;font-weight:700;color:var(--cyan);display:flex;align-items:center;gap:12px}
.sidebar-logo svg{width:32px;height:32px}
.sidebar-section{padding:8px 16px;font-size:11px;color:var(--gray);text-transform:uppercase;letter-spacing:1px;margin-top:16px}
.sidebar-item{display:flex;align-items:center;gap:12px;padding:12px 24px;color:var(--gray);text-decoration:none;transition:all .2s;cursor:pointer}
.sidebar-item:hover{background:rgba(0,209,255,0.05);color:var(--text)}
.sidebar-item.active{background:rgba(0,209,255,0.1);color:var(--cyan);border-right:3px solid var(--cyan)}
.sidebar-item-icon{font-size:18px}

/* Main Content */
.main-content{flex:1;margin-left:260px;padding:32px}
.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px}
.page-title{font-size:28px;font-weight:700}
.header-actions{display:flex;gap:12px}

/* Cards */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:32px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px}
.stat-card-label{font-size:13px;color:var(--gray);margin-bottom:8px}
.stat-card-value{font-size:32px;font-weight:700}
.stat-card-change{font-size:12px;margin-top:8px}
.stat-card-change.up{color:var(--green)}
.stat-card-change.down{color:var(--red)}

/* Table */
.data-table{width:100%;background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.data-table th,.data-table td{padding:16px;text-align:left;border-bottom:1px solid var(--border)}
.data-table th{background:rgba(0,0,0,0.3);font-size:12px;text-transform:uppercase;color:var(--gray);letter-spacing:0.5px}
.data-table tr:hover{background:rgba(0,209,255,0.02)}
.data-table tr:last-child td{border-bottom:none}

/* Status Badges */
.badge{padding:4px 12px;border-radius:100px;font-size:12px;font-weight:500}
.badge-active{background:rgba(16,185,129,0.1);color:var(--green)}
.badge-paused{background:rgba(245,158,11,0.1);color:var(--yellow)}
.badge-inactive{background:rgba(239,68,68,0.1);color:var(--red)}

/* Buttons */
.btn{padding:10px 20px;border-radius:8px;font-size:14px;font-weight:500;cursor:pointer;transition:all .2s;border:none}
.btn-primary{background:var(--cyan);color:#000}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,209,255,0.3)}
.btn-secondary{background:transparent;border:1px solid var(--border);color:var(--text)}
.btn-secondary:hover{border-color:var(--cyan)}
.btn-sm{padding:6px 12px;font-size:12px}
.btn-icon{width:32px;height:32px;padding:0;display:flex;align-items:center;justify-content:center;border-radius:8px;background:transparent;border:1px solid var(--border);color:var(--gray);cursor:pointer}
.btn-icon:hover{border-color:var(--cyan);color:var(--cyan)}

/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.8);display:none;align-items:center;justify-content:center;z-index:1000}
.modal-overlay.active{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:16px;width:90%;max-width:600px;max-height:90vh;overflow-y:auto}
.modal-header{padding:24px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.modal-title{font-size:20px;font-weight:600}
.modal-close{background:none;border:none;color:var(--gray);font-size:24px;cursor:pointer}
.modal-body{padding:24px}
.modal-footer{padding:24px;border-top:1px solid var(--border);display:flex;justify-content:flex-end;gap:12px}

/* Forms */
.form-group{margin-bottom:20px}
.form-label{display:block;font-size:13px;color:var(--gray);margin-bottom:8px}
.form-input{width:100%;padding:12px 16px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:14px}
.form-input:focus{outline:none;border-color:var(--cyan)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}

/* Client Card (for detailed view) */
.client-header{display:flex;align-items:center;gap:24px;padding:24px;background:var(--card);border:1px solid var(--border);border-radius:16px;margin-bottom:24px}
.client-avatar{width:80px;height:80px;background:linear-gradient(135deg,var(--cyan),#0066ff);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:700}
.client-info h2{font-size:24px;margin-bottom:4px}
.client-info p{color:var(--gray)}
.client-meta{display:flex;gap:24px;margin-top:12px}
.client-meta-item{font-size:13px;color:var(--gray)}
.client-meta-item span{color:var(--text);font-weight:500}

/* Tabs */
.tabs{display:flex;gap:4px;background:var(--card);padding:4px;border-radius:12px;margin-bottom:24px;width:fit-content}
.tab{padding:10px 20px;border-radius:8px;font-size:14px;color:var(--gray);cursor:pointer;transition:all .2s}
.tab:hover{color:var(--text)}
.tab.active{background:var(--cyan);color:#000}

/* Cost Breakdown */
.cost-breakdown{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px}
.cost-item{background:var(--bg);padding:16px;border-radius:8px;text-align:center}
.cost-item-value{font-size:24px;font-weight:700;color:var(--cyan)}
.cost-item-label{font-size:12px;color:var(--gray);margin-top:4px}

/* Integration Cards */
.integrations-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.integration-card{background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:20px}
.integration-header{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.integration-icon{width:40px;height:40px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:20px}
.integration-icon.retell{background:rgba(0,209,255,0.1)}
.integration-icon.twilio{background:rgba(239,68,68,0.1)}
.integration-icon.ghl{background:rgba(16,185,129,0.1)}
.integration-name{font-weight:600}
.integration-status{font-size:12px;color:var(--gray)}
.integration-status.connected{color:var(--green)}

/* Search */
.search-box{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 16px;width:300px}
.search-box input{background:none;border:none;color:var(--text);flex:1;font-size:14px}
.search-box input:focus{outline:none}
.search-icon{color:var(--gray)}

/* Responsive */
@media(max-width:1024px){
    .sidebar{width:80px;padding:16px 0}
    .sidebar-logo span,.sidebar-section,.sidebar-item span{display:none}
    .sidebar-item{justify-content:center;padding:12px}
    .main-content{margin-left:80px}
}
@media(max-width:768px){
    .sidebar{display:none}
    .main-content{margin-left:0}
    .form-row{grid-template-columns:1fr}
    .stats-grid{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>

<div class="admin-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-logo">
            <svg viewBox="0 0 512 512"><circle cx="256" cy="256" r="180" stroke="#00D1FF" stroke-width="24" fill="none"/></svg>
            <span>VOICE Admin</span>
        </div>
        
        <div class="sidebar-section">Overview</div>
        <a class="sidebar-item active" onclick="showPage('dashboard')">
            <span class="sidebar-item-icon">📊</span>
            <span>Dashboard</span>
        </a>
        
        <div class="sidebar-section">Clients</div>
        <a class="sidebar-item" onclick="showPage('clients')">
            <span class="sidebar-item-icon">👥</span>
            <span>All Clients</span>
        </a>
        <a class="sidebar-item" onclick="showPage('add-client')">
            <span class="sidebar-item-icon">➕</span>
            <span>Add Client</span>
        </a>
        
        <div class="sidebar-section">Analytics</div>
        <a class="sidebar-item" onclick="showPage('costs')">
            <span class="sidebar-item-icon">💰</span>
            <span>Cost Tracking</span>
        </a>
        <a class="sidebar-item" onclick="showPage('reports')">
            <span class="sidebar-item-icon">📈</span>
            <span>Reports</span>
        </a>
        
        <div class="sidebar-section">System</div>
        <a class="sidebar-item" onclick="showPage('settings')">
            <span class="sidebar-item-icon">⚙️</span>
            <span>Settings</span>
        </a>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
        
        <!-- Dashboard Page -->
        <div id="page-dashboard" class="page active">
            <div class="page-header">
                <h1 class="page-title">Dashboard</h1>
                <div class="header-actions">
                    <button class="btn btn-primary" onclick="openModal('add-client-modal')">+ Add Client</button>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-label">Total Clients</div>
                    <div class="stat-card-value" id="stat-clients">0</div>
                    <div class="stat-card-change up">↑ 12% this month</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Active Calls Today</div>
                    <div class="stat-card-value" id="stat-calls">0</div>
                    <div class="stat-card-change up">↑ 8% vs yesterday</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Total Revenue (MTD)</div>
                    <div class="stat-card-value" id="stat-revenue">$0</div>
                    <div class="stat-card-change up">↑ 23% vs last month</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Platform Costs (MTD)</div>
                    <div class="stat-card-value" id="stat-costs">$0</div>
                    <div class="stat-card-change down">↑ 5% vs last month</div>
                </div>
            </div>
            
            <h3 style="margin-bottom:16px">Recent Clients</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Client</th>
                        <th>Industry</th>
                        <th>Plan</th>
                        <th>Leads</th>
                        <th>Calls</th>
                        <th>Cost (30d)</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="clients-table-body">
                    <tr><td colspan="8" style="text-align:center;color:var(--gray)">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        
        <!-- Clients Page -->
        <div id="page-clients" class="page" style="display:none">
            <div class="page-header">
                <h1 class="page-title">All Clients</h1>
                <div class="header-actions">
                    <div class="search-box">
                        <span class="search-icon">🔍</span>
                        <input type="text" placeholder="Search clients..." id="client-search">
                    </div>
                    <button class="btn btn-primary" onclick="openModal('add-client-modal')">+ Add Client</button>
                </div>
            </div>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Client</th>
                        <th>Contact</th>
                        <th>Industry</th>
                        <th>Plan</th>
                        <th>Leads</th>
                        <th>Calls</th>
                        <th>Cost (30d)</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="all-clients-table">
                    <tr><td colspan="9" style="text-align:center;color:var(--gray)">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        
        <!-- Client Detail Page -->
        <div id="page-client-detail" class="page" style="display:none">
            <div class="page-header">
                <h1 class="page-title">← <a href="#" onclick="showPage('clients');return false" style="color:inherit;text-decoration:none">Back to Clients</a></h1>
            </div>
            
            <div class="client-header">
                <div class="client-avatar" id="client-avatar">A</div>
                <div class="client-info">
                    <h2 id="client-name">Acme Roofing</h2>
                    <p id="client-email">contact@acmeroofing.com</p>
                    <div class="client-meta">
                        <div class="client-meta-item">Industry: <span id="client-industry">Roofing</span></div>
                        <div class="client-meta-item">Plan: <span id="client-plan">Professional</span></div>
                        <div class="client-meta-item">Since: <span id="client-since">Jan 2026</span></div>
                    </div>
                </div>
                <div style="margin-left:auto;display:flex;gap:12px">
                    <button class="btn btn-secondary" onclick="openModal('edit-client-modal')">Edit</button>
                    <button class="btn btn-primary">View CRM →</button>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-label">Total Leads</div>
                    <div class="stat-card-value" id="client-leads">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Total Calls</div>
                    <div class="stat-card-value" id="client-calls">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Appointments</div>
                    <div class="stat-card-value" id="client-appointments">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Cost (30 days)</div>
                    <div class="stat-card-value" id="client-cost">$0</div>
                </div>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="switchClientTab('integrations')">Integrations</div>
                <div class="tab" onclick="switchClientTab('costs')">Cost Breakdown</div>
                <div class="tab" onclick="switchClientTab('activity')">Activity</div>
            </div>
            
            <div id="client-tab-integrations">
                <h3 style="margin-bottom:16px">Integrations</h3>
                <div class="integrations-grid" id="client-integrations">
                    <!-- Populated by JS -->
                </div>
                <button class="btn btn-secondary" style="margin-top:16px" onclick="openModal('add-integration-modal')">+ Add Integration</button>
            </div>
            
            <div id="client-tab-costs" style="display:none">
                <h3 style="margin-bottom:16px">Cost Breakdown (Last 30 Days)</h3>
                <div class="cost-breakdown" id="client-cost-breakdown">
                    <!-- Populated by JS -->
                </div>
            </div>
            
            <div id="client-tab-activity" style="display:none">
                <h3 style="margin-bottom:16px">Recent Activity</h3>
                <table class="data-table">
                    <thead><tr><th>Date</th><th>Type</th><th>Details</th><th>Cost</th></tr></thead>
                    <tbody id="client-activity-table"></tbody>
                </table>
            </div>
        </div>
        
    </main>
</div>

<!-- Add Client Modal -->
<div class="modal-overlay" id="add-client-modal">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Add New Client</h3>
            <button class="modal-close" onclick="closeModal('add-client-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Company Name *</label>
                    <input type="text" class="form-input" id="new-client-company" placeholder="Acme Roofing">
                </div>
                <div class="form-group">
                    <label class="form-label">Contact Name</label>
                    <input type="text" class="form-input" id="new-client-contact" placeholder="John Smith">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Email *</label>
                    <input type="email" class="form-input" id="new-client-email" placeholder="john@acmeroofing.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Phone</label>
                    <input type="tel" class="form-input" id="new-client-phone" placeholder="(555) 123-4567">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Industry *</label>
                    <select class="form-input" id="new-client-industry">
                        <option value="roofing">Roofing</option>
                        <option value="solar">Solar</option>
                        <option value="hvac">HVAC</option>
                        <option value="plumbing">Plumbing</option>
                        <option value="electrical">Electrical</option>
                        <option value="insurance">Insurance</option>
                        <option value="real_estate">Real Estate</option>
                        <option value="auto">Auto Sales</option>
                        <option value="dental">Dental</option>
                        <option value="legal">Legal</option>
                        <option value="medical">Medical</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Plan</label>
                    <select class="form-input" id="new-client-plan">
                        <option value="starter">Starter ($297/mo)</option>
                        <option value="professional">Professional ($497/mo)</option>
                        <option value="enterprise">Enterprise ($997/mo)</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Monthly Budget</label>
                <input type="number" class="form-input" id="new-client-budget" placeholder="500" value="500">
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('add-client-modal')">Cancel</button>
            <button class="btn btn-primary" onclick="createClient()">Create Client</button>
        </div>
    </div>
</div>

<!-- Add Integration Modal -->
<div class="modal-overlay" id="add-integration-modal">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Add Integration</h3>
            <button class="modal-close" onclick="closeModal('add-integration-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <label class="form-label">Integration Type</label>
                <select class="form-input" id="integration-type" onchange="showIntegrationFields()">
                    <option value="retell">Retell AI</option>
                    <option value="twilio">Twilio</option>
                    <option value="ghl">GoHighLevel</option>
                    <option value="zapier">Zapier</option>
                </select>
            </div>
            <div id="retell-fields">
                <div class="form-group">
                    <label class="form-label">Retell API Key</label>
                    <input type="text" class="form-input" id="integration-api-key" placeholder="key_xxxxx">
                </div>
                <div class="form-group">
                    <label class="form-label">Phone Number</label>
                    <input type="tel" class="form-input" id="integration-phone" placeholder="+17201234567">
                </div>
                <div class="form-group">
                    <label class="form-label">Agent ID</label>
                    <input type="text" class="form-input" id="integration-agent-id" placeholder="agent_xxxxx">
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('add-integration-modal')">Cancel</button>
            <button class="btn btn-primary" onclick="saveIntegration()">Save Integration</button>
        </div>
    </div>
</div>

<script>
let currentClientId = null;
let clients = [];

// Page Navigation
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
    
    const pageEl = document.getElementById('page-' + page);
    if (pageEl) pageEl.style.display = 'block';
    
    event?.target?.classList?.add('active');
    
    if (page === 'dashboard' || page === 'clients') loadClients();
}

// Modal Functions
function openModal(id) {
    document.getElementById(id).classList.add('active');
}
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Load Clients
async function loadClients() {
    try {
        const response = await fetch('/api/admin/clients');
        clients = await response.json();
        renderClientsTable();
        updateDashboardStats();
    } catch (e) {
        console.error('Error loading clients:', e);
    }
}

function renderClientsTable() {
    const html = clients.map(c => `
        <tr>
            <td>
                <div style="display:flex;align-items:center;gap:12px">
                    <div style="width:36px;height:36px;background:linear-gradient(135deg,var(--cyan),#0066ff);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:600">${c.company_name?.charAt(0) || '?'}</div>
                    <div>
                        <div style="font-weight:500">${c.company_name}</div>
                        <div style="font-size:12px;color:var(--gray)">${c.email || ''}</div>
                    </div>
                </div>
            </td>
            <td>${c.contact_name || '-'}</td>
            <td>${c.industry || '-'}</td>
            <td><span class="badge badge-active">${c.plan || 'starter'}</span></td>
            <td>${c.lead_count || 0}</td>
            <td>${c.call_count || 0}</td>
            <td>$${(c.monthly_cost || 0).toFixed(2)}</td>
            <td><span class="badge badge-${c.status === 'active' ? 'active' : 'paused'}">${c.status}</span></td>
            <td>
                <button class="btn-icon" onclick="viewClient(${c.id})" title="View">👁️</button>
                <button class="btn-icon" onclick="editClient(${c.id})" title="Edit">✏️</button>
            </td>
        </tr>
    `).join('');
    
    document.getElementById('clients-table-body').innerHTML = html || '<tr><td colspan="8" style="text-align:center;color:var(--gray)">No clients yet</td></tr>';
    document.getElementById('all-clients-table').innerHTML = html || '<tr><td colspan="9" style="text-align:center;color:var(--gray)">No clients yet</td></tr>';
}

function updateDashboardStats() {
    document.getElementById('stat-clients').textContent = clients.length;
    document.getElementById('stat-calls').textContent = clients.reduce((sum, c) => sum + (c.call_count || 0), 0);
    document.getElementById('stat-costs').textContent = '$' + clients.reduce((sum, c) => sum + (c.monthly_cost || 0), 0).toFixed(2);
    // Revenue would come from plan pricing * clients
    const revenueMap = {starter: 297, professional: 497, enterprise: 997};
    const revenue = clients.reduce((sum, c) => sum + (revenueMap[c.plan] || 297), 0);
    document.getElementById('stat-revenue').textContent = '$' + revenue.toLocaleString();
}

// Create Client
async function createClient() {
    const data = {
        company_name: document.getElementById('new-client-company').value,
        contact_name: document.getElementById('new-client-contact').value,
        email: document.getElementById('new-client-email').value,
        phone: document.getElementById('new-client-phone').value,
        industry: document.getElementById('new-client-industry').value,
        plan: document.getElementById('new-client-plan').value,
        monthly_budget: document.getElementById('new-client-budget').value
    };
    
    if (!data.company_name || !data.email) {
        alert('Company name and email are required');
        return;
    }
    
    try {
        const response = await fetch('/api/admin/clients', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            closeModal('add-client-modal');
            loadClients();
            // Clear form
            document.getElementById('new-client-company').value = '';
            document.getElementById('new-client-contact').value = '';
            document.getElementById('new-client-email').value = '';
            document.getElementById('new-client-phone').value = '';
        } else {
            alert(result.error || 'Failed to create client');
        }
    } catch (e) {
        alert('Error creating client');
    }
}

// View Client Detail
async function viewClient(id) {
    currentClientId = id;
    
    try {
        const response = await fetch(`/api/admin/clients/${id}`);
        const client = await response.json();
        
        document.getElementById('client-avatar').textContent = client.company_name?.charAt(0) || '?';
        document.getElementById('client-name').textContent = client.company_name;
        document.getElementById('client-email').textContent = client.email || '';
        document.getElementById('client-industry').textContent = client.industry || '-';
        document.getElementById('client-plan').textContent = client.plan || 'starter';
        document.getElementById('client-since').textContent = new Date(client.created_at).toLocaleDateString('en-US', {month: 'short', year: 'numeric'});
        
        document.getElementById('client-leads').textContent = client.stats?.total_leads || 0;
        document.getElementById('client-calls').textContent = client.stats?.appointments || 0;
        document.getElementById('client-appointments').textContent = client.stats?.appointments || 0;
        document.getElementById('client-cost').textContent = '$' + (client.monthly_cost || 0).toFixed(2);
        
        // Render integrations
        const integrationsHtml = (client.integrations || []).map(i => `
            <div class="integration-card">
                <div class="integration-header">
                    <div class="integration-icon ${i.integration_type}">${i.integration_type === 'retell' ? '📞' : i.integration_type === 'twilio' ? '💬' : '🔗'}</div>
                    <div>
                        <div class="integration-name">${i.integration_type.charAt(0).toUpperCase() + i.integration_type.slice(1)}</div>
                        <div class="integration-status ${i.is_active ? 'connected' : ''}">${i.is_active ? '● Connected' : '○ Disconnected'}</div>
                    </div>
                </div>
                <div style="font-size:12px;color:var(--gray)">
                    ${i.phone_number ? 'Phone: ' + i.phone_number : ''}
                    ${i.agent_id ? '<br>Agent: ' + i.agent_id : ''}
                </div>
            </div>
        `).join('') || '<p style="color:var(--gray)">No integrations configured</p>';
        document.getElementById('client-integrations').innerHTML = integrationsHtml;
        
        showPage('client-detail');
    } catch (e) {
        console.error('Error loading client:', e);
    }
}

function switchClientTab(tab) {
    document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    document.querySelectorAll('[id^="client-tab-"]').forEach(t => t.style.display = 'none');
    document.getElementById('client-tab-' + tab).style.display = 'block';
}

// Save Integration
async function saveIntegration() {
    if (!currentClientId) return;
    
    const data = {
        integration_type: document.getElementById('integration-type').value,
        api_key: document.getElementById('integration-api-key').value,
        phone_number: document.getElementById('integration-phone').value,
        agent_id: document.getElementById('integration-agent-id').value
    };
    
    try {
        const response = await fetch(`/api/admin/clients/${currentClientId}/integrations`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            closeModal('add-integration-modal');
            viewClient(currentClientId);
        } else {
            alert(result.error || 'Failed to save integration');
        }
    } catch (e) {
        alert('Error saving integration');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
});
</script>
</body>
</html>
'''

# Add these API endpoints to your do_POST handler:
"""
        # Admin API endpoints
        elif path == '/api/admin/clients':
            if self.command == 'GET':
                clients = get_all_clients()
                self.send_json(clients)
            elif self.command == 'POST':
                result = create_client(
                    d.get('company_name'),
                    d.get('contact_name'),
                    d.get('email'),
                    d.get('phone'),
                    d.get('industry'),
                    d.get('plan', 'starter')
                )
                self.send_json({'success': True, **result})
                
        elif path.startswith('/api/admin/clients/') and '/integrations' in path:
            client_id = int(path.split('/')[4])
            add_client_integration(
                client_id,
                d.get('integration_type'),
                d.get('api_key'),
                d.get('api_secret'),
                d.get('webhook_url'),
                d.get('phone_number'),
                d.get('agent_id')
            )
            self.send_json({'success': True})
            
        elif path.startswith('/api/admin/clients/'):
            client_id = int(path.split('/')[-1])
            client = get_client(client_id)
            self.send_json(client)
"""
