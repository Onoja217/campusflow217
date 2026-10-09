"""Browser-based CampusFlow dashboard served at http://localhost:3000.

Uses only the Python standard library and reuses the existing ticket business
rules and JSON persistence layer.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from .persistence import (
    DEFAULT_TICKETS_PATH,
    TicketPersistenceError,
    load_tickets,
    save_tickets,
)
from .priority_queue import prioritized_tickets
from .tickets import (
    Ticket,
    TicketValidationError,
    assign_ticket,
    change_ticket_status,
    create_ticket,
    reopen_ticket,
)

HOST = "127.0.0.1"
PORT = 3000

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CampusFlow · Helpdesk</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2d;--panel2:#17223a;--line:#263450;--text:#edf3ff;--muted:#91a1bd;--blue:#7397ff;--cyan:#61d6d0;--red:#ff7b8b;--amber:#f4c66a;--green:#69d9a2}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 10% 0%,#17264a 0,transparent 42%),var(--bg);color:var(--text);font:14px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
button,input,select{font:inherit}button{cursor:pointer;border:0;border-radius:10px;padding:10px 14px;font-weight:650;transition:transform .15s,opacity .15s}button:hover{transform:translateY(-1px)}button:disabled{opacity:.5;cursor:not-allowed}
.shell{max-width:1400px;margin:auto;padding:28px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:30px}.brand{display:flex;align-items:center;gap:13px}.logo{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#7598ff,#56d9d0);display:grid;place-items:center;color:#091326;font-size:22px;font-weight:900;box-shadow:0 8px 30px #5f8cff30}.brand h1{font-size:20px;letter-spacing:-.5px;margin:0}.brand p{margin:2px 0 0;color:var(--muted);font-size:12px}.top-actions{display:flex;align-items:center;gap:10px}.status-live{color:var(--green);font-size:12px;display:flex;align-items:center;gap:7px}.dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 10px #69d9a2}
.primary{background:var(--blue);color:#071126}.secondary{background:#23314e;color:var(--text);border:1px solid #334464}.layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:22px;align-items:start}.heading{margin-bottom:18px}.eyebrow{text-transform:uppercase;letter-spacing:1.8px;font-size:10px;font-weight:800;color:var(--cyan)}h2{font-size:26px;letter-spacing:-.8px;margin:5px 0}.sub{color:var(--muted);margin:0}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin:22px 0}.stat,.panel{background:linear-gradient(145deg,#151f35ee,#10182aee);border:1px solid var(--line);border-radius:16px;box-shadow:0 12px 35px #00000013}.stat{padding:17px}.stat-label{color:var(--muted);font-size:12px}.stat-value{font-size:28px;font-weight:750;letter-spacing:-1px;margin-top:6px}.stat-foot{font-size:11px;color:var(--muted);margin-top:2px}.stat .mini{float:right;width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:#7598ff1b;color:var(--blue);font-size:16px}
.panel{padding:19px}.panel-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:16px}.panel h3{margin:0;font-size:15px}.count{font-size:11px;background:#263552;color:#bdccef;border-radius:7px;padding:4px 8px}
.toolbar{display:flex;gap:10px;align-items:center;margin:20px 0 12px}.search{flex:1;min-width:100px}.field{width:100%;background:#0c1426;color:var(--text);border:1px solid #30405d;border-radius:10px;padding:11px 12px;outline:none}.field:focus{border-color:var(--blue);box-shadow:0 0 0 3px #7397ff20}.toolbar select{width:145px}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:650px}th{text-align:left;text-transform:uppercase;letter-spacing:1px;font-size:10px;color:var(--muted);font-weight:750;padding:12px 10px;border-bottom:1px solid var(--line)}td{padding:15px 10px;border-bottom:1px solid #202d45;vertical-align:middle}tbody tr:last-child td{border-bottom:0}.ticket-title{font-weight:650;max-width:250px}.ticket-id{color:var(--muted);font-size:11px;margin-top:3px}.pill{display:inline-flex;align-items:center;gap:5px;border-radius:7px;padding:4px 8px;font-size:11px;font-weight:750;white-space:nowrap}.critical{background:#522735;color:#ff9ba9}.high{background:#4c3423;color:#ffbd83}.medium{background:#4a4127;color:#f5d57f}.low{background:#1e3e3d;color:#7de0d1}.open{background:#203b65;color:#a6c6ff}.in_progress{background:#3a2d60;color:#c6b4ff}.resolved{background:#1c4034;color:#8ce9b8}.assignee{color:#bdc8dd}.row-actions{display:flex;gap:6px}.small-btn{padding:7px 9px;font-size:11px;background:#243452;color:#dce7ff;border:1px solid #344968}.empty{padding:35px 15px;text-align:center;color:var(--muted)}.empty strong{display:block;color:var(--text);margin-bottom:5px}
.side{display:flex;flex-direction:column;gap:18px}.form-grid{display:grid;gap:13px}.form-field label{display:block;font-size:12px;color:#c3cee2;margin-bottom:6px}.form-grid .two{display:grid;grid-template-columns:1fr 1fr;gap:10px}.hint{font-size:11px;color:var(--muted);margin-top:5px}.form-submit{width:100%;margin-top:4px}.queue-list{display:grid;gap:10px}.queue-item{display:flex;align-items:center;gap:10px;background:#0e1729;border:1px solid #25334e;border-radius:11px;padding:11px}.queue-rank{width:29px;height:29px;display:grid;place-items:center;border-radius:8px;background:#263654;color:#c9d8fa;font-weight:800;font-size:11px}.queue-meta{min-width:0;flex:1}.queue-meta strong{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px}.queue-meta span{color:var(--muted);font-size:11px}.toast{position:fixed;right:24px;bottom:24px;max-width:360px;background:#1b2b43;border:1px solid #405a7c;border-radius:12px;padding:13px 16px;box-shadow:0 15px 45px #0008;z-index:5}.toast.error{border-color:#a44b60}.footer{color:#61718e;text-align:center;font-size:11px;margin-top:24px}
@media(max-width:1050px){.layout{grid-template-columns:1fr}.side{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){.shell{padding:16px}.topbar{align-items:flex-start}.top-actions{flex-direction:column;align-items:flex-end}.brand h1{font-size:17px}.stats{gap:9px}.stat{padding:13px}.stat-value{font-size:24px}.side{display:flex}.toolbar{flex-wrap:wrap}.toolbar select{flex:1}.heading h2{font-size:23px}}
</style>
</head>
<body>
<div class="shell">
<header class="topbar">
  <div class="brand"><div class="logo">C</div><div><h1>CampusFlow</h1><p>Helpdesk operations workspace</p></div></div>
  <div class="top-actions"><span class="status-live"><i class="dot"></i> Local workspace</span><button class="primary" onclick="document.querySelector('#ticket-title').focus()">＋ New ticket</button></div>
</header>
<div class="heading"><div class="eyebrow">Support overview</div><h2>Ticket dashboard</h2><p class="sub">Triage requests, track ownership, and keep campus support moving.</p></div>
<section class="stats">
  <div class="stat"><span class="mini">▤</span><div class="stat-label">All tickets</div><div class="stat-value" id="stat-total">—</div><div class="stat-foot">Every recorded request</div></div>
  <div class="stat"><span class="mini">◷</span><div class="stat-label">Open</div><div class="stat-value" id="stat-open">—</div><div class="stat-foot">Awaiting action</div></div>
  <div class="stat"><span class="mini">↗</span><div class="stat-label">In progress</div><div class="stat-value" id="stat-progress">—</div><div class="stat-foot">Currently being handled</div></div>
  <div class="stat"><span class="mini">✓</span><div class="stat-label">Resolved</div><div class="stat-value" id="stat-resolved">—</div><div class="stat-foot">Completed requests</div></div>
</section>
<div class="layout">
<main>
<section class="panel">
  <div class="panel-head"><h3>All tickets</h3><span class="count" id="ticket-count">0 records</span></div>
  <div class="toolbar"><input class="field search" id="search" placeholder="Search title, ID, or assignee…" oninput="render()"><select class="field" id="filter" onchange="render()"><option value="all">All statuses</option><option value="open">Open</option><option value="in_progress">In progress</option><option value="resolved">Resolved</option></select></div>
  <div class="table-wrap"><table><thead><tr><th>Ticket</th><th>Priority</th><th>Status</th><th>Assignee</th><th>Actions</th></tr></thead><tbody id="ticket-rows"></tbody></table></div>
  <div class="empty" id="ticket-empty" hidden><strong>No tickets to show</strong>Create a ticket or adjust your filters.</div>
</section>
</main>
<aside class="side">
<section class="panel">
  <div class="panel-head"><h3>Create a ticket</h3><span class="count">NEW</span></div>
  <form class="form-grid" id="create-form">
    <div class="form-field"><label for="ticket-title">Ticket title</label><input class="field" id="ticket-title" name="title" placeholder="e.g. Wi-Fi unavailable in Block B" required></div>
    <div class="form-grid two">
      <div class="form-field"><label for="category">Category</label><select class="field" id="category" name="category"><option>Network</option><option>Hardware</option><option>Software</option><option>Other</option></select></div>
      <div class="form-field"><label for="urgency">Urgency</label><select class="field" id="urgency" name="urgency"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option></select></div>
    </div>
    <div class="form-field"><label for="affected">Affected users</label><input class="field" id="affected" name="affected_users" type="number" min="1" step="1" value="1" required><div class="hint">Priority is calculated automatically from urgency and impact.</div></div>
    <button class="primary form-submit" type="submit">Create ticket →</button>
  </form>
</section>
<section class="panel">
  <div class="panel-head"><h3>Priority queue</h3><span class="count" id="queue-count">0 pending</span></div>
  <div class="queue-list" id="queue-list"></div>
  <div class="hint" style="margin-top:12px">Unresolved tickets sorted by critical → high → medium → low.</div>
</section>
</aside>
</div>
<div class="footer">CampusFlow · Local development · Changes save to data/tickets.json</div>
</div>
<div id="toast" class="toast" hidden></div>
<script>
let tickets = [];
const priorityOrder = {critical:0, high:1, medium:2, low:3};
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty = value => String(value || '').replace('_',' ').replace(/\b\w/g, c=>c.toUpperCase());
function notify(message, error=false){const el=document.querySelector('#toast');el.textContent=message;el.classList.toggle('error',error);el.hidden=false;clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>el.hidden=true,3200)}
async function api(path, options={}){const response=await fetch('/api'+path,{headers:{'Content-Type':'application/json'},...options});const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');return data}
function pill(value){return '<span class="pill '+esc(value)+'">'+esc(pretty(value))+'</span>'}
function render(){
 const total=tickets.length, open=tickets.filter(t=>t.status==='open').length, progress=tickets.filter(t=>t.status==='in_progress').length, resolved=tickets.filter(t=>t.status==='resolved').length;
 document.querySelector('#stat-total').textContent=total;document.querySelector('#stat-open').textContent=open;document.querySelector('#stat-progress').textContent=progress;document.querySelector('#stat-resolved').textContent=resolved;
 const term=document.querySelector('#search').value.trim().toLowerCase(), filter=document.querySelector('#filter').value;
 const visible=tickets.filter(t=>(filter==='all'||t.status===filter)&&[t.id,t.title,t.assigned_to,t.category].some(v=>String(v||'').toLowerCase().includes(term)));
 document.querySelector('#ticket-count').textContent=visible.length+' record'+(visible.length===1?'':'s');
 document.querySelector('#ticket-empty').hidden=visible.length!==0;
 document.querySelector('#ticket-rows').innerHTML=visible.map(t=>{
 let action=t.status==='open'?(t.assigned_to?'<button class="small-btn" onclick="changeStatus(\''+esc(t.id)+'\',\'in_progress\')">Start</button>':'<button class="small-btn" onclick="assign(\''+esc(t.id)+'\')">Assign</button>') : t.status==='in_progress'?'<button class="small-btn" onclick="changeStatus(\''+esc(t.id)+'\',\'resolved\')">Resolve</button>':'<button class="small-btn" onclick="reopen(\''+esc(t.id)+'\')">Reopen</button>';
 if(t.status!=='resolved') action+='<button class="small-btn" onclick="assign(\''+esc(t.id)+'\')">↗</button>';
 return '<tr><td><div class="ticket-title">'+esc(t.title)+'</div><div class="ticket-id">'+esc(t.id)+' · '+esc(t.category)+' · '+esc(t.affected_users)+' users</div></td><td>'+pill(t.priority)+'</td><td>'+pill(t.status)+'</td><td class="assignee">'+esc(t.assigned_to||'Unassigned')+'</td><td><div class="row-actions">'+action+'</div></td></tr>'
 }).join('');
 const queue=tickets.filter(t=>t.status!=='resolved').sort((a,b)=>(priorityOrder[a.priority]??9)-(priorityOrder[b.priority]??9)||Number(a.id.slice(1))-Number(b.id.slice(1)));
 document.querySelector('#queue-count').textContent=queue.length+' pending';
 document.querySelector('#queue-list').innerHTML=queue.slice(0,5).map((t,i)=>'<div class="queue-item"><div class="queue-rank">'+String(i+1).padStart(2,'0')+'</div><div class="queue-meta"><strong>'+esc(t.title)+'</strong><span>'+esc(t.id)+' · '+esc(t.priority)+' priority</span></div>'+pill(t.priority)+'</div>').join('') || '<div class="empty">No unresolved tickets.</div>';
}
async function refresh(){try{const data=await api('/tickets');tickets=data.tickets;render()}catch(e){notify(e.message,true)}}
document.querySelector('#create-form').addEventListener('submit',async e=>{e.preventDefault();const formElement=e.currentTarget;const form=new FormData(formElement);const payload=Object.fromEntries(form.entries());payload.affected_users=Number(payload.affected_users);try{const data=await api('/tickets',{method:'POST',body:JSON.stringify(payload)});tickets=data.tickets;formElement.reset();document.querySelector('#affected').value=1;document.querySelector('#urgency').value='medium';render();notify('Created '+data.ticket.id+' · '+data.ticket.priority+' priority')}catch(err){notify(err.message,true)}});
async function assign(id){const assignee=prompt('Assign '+id+' to (person or team):');if(assignee===null)return;try{const data=await api('/tickets/'+encodeURIComponent(id)+'/assign',{method:'POST',body:JSON.stringify({assignee})});tickets=data.tickets;render();notify(id+' assigned to '+assignee.trim())}catch(e){notify(e.message,true)}}
async function changeStatus(id,status){try{const data=await api('/tickets/'+encodeURIComponent(id)+'/status',{method:'POST',body:JSON.stringify({status})});tickets=data.tickets;render();notify(id+' moved to '+pretty(status))}catch(e){notify(e.message,true)}}
async function reopen(id){try{const data=await api('/tickets/'+encodeURIComponent(id)+'/reopen',{method:'POST',body:'{}'});tickets=data.tickets;render();notify(id+' reopened')}catch(e){notify(e.message,true)}}
refresh();
</script>
</body>
</html>"""


class CampusFlowHandler(BaseHTTPRequestHandler):
    tickets_path = DEFAULT_TICKETS_PATH

    def log_message(self, format: str, *args: object) -> None:
        print(f"[CampusFlow] {args[0]}")

    def _send(self, status: int, payload: object, content_type: str = "application/json; charset=utf-8") -> None:
        body = payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                raise ValueError("Request body is empty or too large.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Request must contain a valid JSON object.") from error
        if not isinstance(payload, dict):
            raise ValueError("Request must contain a JSON object.")
        return payload

    def _tickets(self) -> list[Ticket]:
        return load_tickets(self.tickets_path)

    def _snapshot(self, tickets: list[Ticket]) -> dict[str, object]:
        return {"tickets": [ticket.to_dict() for ticket in tickets]}

    def _persist(self, tickets: list[Ticket], previous: list[Ticket]) -> None:
        try:
            save_tickets(tickets, self.tickets_path)
        except TicketPersistenceError:
            tickets[:] = previous
            raise

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
            return
        if path == "/api/tickets":
            try:
                tickets = self._tickets()
                self._send(200, self._snapshot(tickets))
            except TicketPersistenceError as error:
                self._send(500, {"error": str(error)})
            return
        if path == "/favicon.ico":
            self._send(204, "")
            return
        self._send(404, {"error": "Not found."})

    def do_POST(self) -> None:
        path = unquote(urlparse(self.path).path)
        try:
            payload = self._body()
            tickets = self._tickets()
            previous = list(tickets)
            if path == "/api/tickets":
                ticket = create_ticket(
                    tickets,
                    title=payload.get("title"),
                    category=payload.get("category"),
                    urgency=payload.get("urgency"),
                    affected_users=payload.get("affected_users"),
                )
            elif path.startswith("/api/tickets/"):
                pieces = path.strip("/").split("/")
                if len(pieces) != 4 or pieces[2] not in {ticket.id for ticket in tickets}:
                    self._send(404, {"error": "Ticket not found."})
                    return
                ticket_id, action = pieces[2], pieces[3]
                if action == "assign":
                    ticket = assign_ticket(tickets, ticket_id, payload.get("assignee"))
                elif action == "status":
                    ticket = change_ticket_status(tickets, ticket_id, payload.get("status"))
                elif action == "reopen":
                    ticket = reopen_ticket(tickets, ticket_id)
                else:
                    self._send(404, {"error": "Unknown ticket action."})
                    return
            else:
                self._send(404, {"error": "Not found."})
                return
            self._persist(tickets, previous)
            response = self._snapshot(tickets)
            response["ticket"] = ticket.to_dict() if isinstance(ticket, Ticket) else dict(ticket)
            self._send(201 if path == "/api/tickets" else 200, response)
        except (ValueError, TicketValidationError) as error:
            self._send(400, {"error": str(error)})
        except TicketPersistenceError as error:
            self._send(500, {"error": str(error)})
        except Exception as error:
            self._send(500, {"error": f"Unexpected server error: {error}"})

    def do_OPTIONS(self) -> None:
        self._send(204, "")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), CampusFlowHandler)
    print(f"CampusFlow browser UI: http://localhost:{PORT}")
    print(f"Ticket data file: {DEFAULT_TICKETS_PATH}")
    print("Press Ctrl+C to stop the local server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCampusFlow web server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
