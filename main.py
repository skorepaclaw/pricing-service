from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
import asyncio
import os
import random
import httpx

app = FastAPI(title="Pricing Service")

ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK", "http://host.docker.internal:8099/webhook/slow-response")

async def notify_slow_response():
    """Notify monitoring system about slow response"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(ALERT_WEBHOOK, timeout=2.0)
    except:
        pass  # Don't fail if webhook is unavailable

# SLOW MODE - when enabled, service responds slowly (simulating performance issue)
SLOW_MODE = os.getenv("SLOW_MODE", "true").lower() == "true"
SLOW_DELAY = float(os.getenv("SLOW_DELAY", "4.5"))  # seconds

# Fake pricing data
MODELS = [
    {"id": "fabia", "name": "Fabia", "base_price": 419900, "image": "🚗"},
    {"id": "scala", "name": "Scala", "base_price": 519900, "image": "🚙"},
    {"id": "octavia", "name": "Octavia", "base_price": 689900, "image": "🚘"},
    {"id": "superb", "name": "Superb", "base_price": 949900, "image": "🚖"},
    {"id": "kamiq", "name": "Kamiq", "base_price": 569900, "image": "🚐"},
    {"id": "karoq", "name": "Karoq", "base_price": 749900, "image": "🚙"},
    {"id": "kodiaq", "name": "Kodiaq", "base_price": 979900, "image": "🚐"},
    {"id": "enyaq", "name": "Enyaq iV", "base_price": 1149900, "image": "⚡"},
]

EXTRAS = [
    {"id": "nav", "name": "Navigace Columbus", "price": 35000},
    {"id": "leather", "name": "Kožené sedačky", "price": 65000},
    {"id": "sunroof", "name": "Panoramatická střecha", "price": 45000},
    {"id": "sound", "name": "Canton Sound System", "price": 28000},
    {"id": "assist", "name": "Travel Assist", "price": 32000},
    {"id": "matrix", "name": "Matrix LED světla", "price": 25000},
]

HTML = """
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ŠKODA Pricing Calculator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f2f5; }
        .header { background: linear-gradient(135deg, #4ba82e 0%, #3d8c27 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; font-weight: 500; }
        .header .logo { font-weight: bold; font-size: 28px; }
        .status-indicator { display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #86efac; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .container { max-width: 1200px; margin: 0 auto; padding: 30px; display: grid; grid-template-columns: 1fr 400px; gap: 30px; }
        .models { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .model-card { background: white; padding: 25px; border-radius: 16px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 3px solid transparent; }
        .model-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
        .model-card.selected { border-color: #4ba82e; background: #f0fdf4; }
        .model-card .icon { font-size: 48px; margin-bottom: 15px; }
        .model-card .name { font-size: 20px; font-weight: 600; color: #1a1a1a; }
        .model-card .price { font-size: 18px; color: #4ba82e; font-weight: 500; margin-top: 8px; }
        .sidebar { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); height: fit-content; position: sticky; top: 30px; }
        .sidebar h2 { font-size: 20px; margin-bottom: 20px; color: #1a1a1a; }
        .extra-item { display: flex; align-items: center; padding: 15px; border: 1px solid #e5e7eb; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; }
        .extra-item:hover { border-color: #4ba82e; }
        .extra-item.selected { background: #f0fdf4; border-color: #4ba82e; }
        .extra-item input { margin-right: 12px; width: 18px; height: 18px; accent-color: #4ba82e; }
        .extra-item .info { flex: 1; }
        .extra-item .name { font-weight: 500; }
        .extra-item .price { color: #666; font-size: 14px; }
        .total-section { margin-top: 30px; padding-top: 20px; border-top: 2px solid #e5e7eb; }
        .total-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .total-row.final { font-size: 24px; font-weight: 700; color: #4ba82e; margin-top: 15px; }
        .calculate-btn { width: 100%; background: #4ba82e; color: white; border: none; padding: 16px; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 20px; transition: all 0.2s; }
        .calculate-btn:hover { background: #3d8c27; }
        .calculate-btn:disabled { background: #9ca3af; cursor: not-allowed; }
        .loading { display: none; text-align: center; padding: 20px; }
        .loading.active { display: block; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #4ba82e; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .response-time { text-align: center; margin-top: 15px; padding: 10px; background: #fef3c7; border-radius: 8px; color: #92400e; font-size: 13px; display: none; }
        .response-time.slow { background: #fef2f2; color: #991b1b; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">ŠKODA</div>
        <h1>Konfigurátor & Ceník</h1>
        <div class="status-indicator">
            <div class="status-dot" id="status-dot"></div>
            <span id="status-text">Online</span>
        </div>
    </div>
    <div class="container">
        <div>
            <h2 style="margin-bottom: 20px; font-size: 18px; color: #666;">Vyberte model</h2>
            <div class="models" id="models-grid"></div>
        </div>
        <div class="sidebar">
            <h2>Příplatkové výbavy</h2>
            <div id="extras-list"></div>
            <div class="total-section">
                <div class="total-row">
                    <span>Základní cena</span>
                    <span id="base-price">-</span>
                </div>
                <div class="total-row">
                    <span>Příplatky</span>
                    <span id="extras-price">0 Kč</span>
                </div>
                <div class="total-row final">
                    <span>Celkem</span>
                    <span id="total-price">-</span>
                </div>
            </div>
            <button class="calculate-btn" onclick="calculate()" id="calc-btn">Vypočítat cenu</button>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>Počítám slevy a dostupnost...</div>
            </div>
            <div class="response-time" id="response-time"></div>
        </div>
    </div>
    <script>
        const models = MODELS_DATA;
        const extras = EXTRAS_DATA;
        let selectedModel = null;
        let selectedExtras = new Set();
        
        function formatPrice(p) { return p.toLocaleString('cs-CZ') + ' Kč'; }
        
        function renderModels() {
            document.getElementById('models-grid').innerHTML = models.map(m => `
                <div class="model-card ${selectedModel?.id === m.id ? 'selected' : ''}" onclick="selectModel('${m.id}')">
                    <div class="icon">${m.image}</div>
                    <div class="name">${m.name}</div>
                    <div class="price">od ${formatPrice(m.base_price)}</div>
                </div>
            `).join('');
        }
        
        function renderExtras() {
            document.getElementById('extras-list').innerHTML = extras.map(e => `
                <div class="extra-item ${selectedExtras.has(e.id) ? 'selected' : ''}" onclick="toggleExtra('${e.id}')">
                    <input type="checkbox" ${selectedExtras.has(e.id) ? 'checked' : ''}>
                    <div class="info">
                        <div class="name">${e.name}</div>
                        <div class="price">+ ${formatPrice(e.price)}</div>
                    </div>
                </div>
            `).join('');
        }
        
        function selectModel(id) {
            selectedModel = models.find(m => m.id === id);
            renderModels();
            updatePrices();
        }
        
        function toggleExtra(id) {
            if (selectedExtras.has(id)) selectedExtras.delete(id);
            else selectedExtras.add(id);
            renderExtras();
            updatePrices();
        }
        
        function updatePrices() {
            const base = selectedModel?.base_price || 0;
            const extrasTotal = [...selectedExtras].reduce((sum, id) => sum + extras.find(e => e.id === id).price, 0);
            document.getElementById('base-price').textContent = base ? formatPrice(base) : '-';
            document.getElementById('extras-price').textContent = formatPrice(extrasTotal);
            document.getElementById('total-price').textContent = base ? formatPrice(base + extrasTotal) : '-';
        }
        
        async function calculate() {
            if (!selectedModel) { alert('Vyberte model'); return; }
            
            const btn = document.getElementById('calc-btn');
            const loading = document.getElementById('loading');
            const responseTime = document.getElementById('response-time');
            
            btn.disabled = true;
            loading.classList.add('active');
            responseTime.style.display = 'none';
            
            const startTime = Date.now();
            
            try {
                const res = await fetch('/api/calculate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: selectedModel.id, extras: [...selectedExtras] })
                });
                const data = await res.json();
                const elapsed = Date.now() - startTime;
                
                responseTime.textContent = `Response time: ${elapsed}ms` + (elapsed > 2000 ? ' ⚠️ SLOW' : '');
                responseTime.className = 'response-time' + (elapsed > 2000 ? ' slow' : '');
                responseTime.style.display = 'block';
                
                if (elapsed > 2000) {
                    document.getElementById('status-dot').style.background = '#fbbf24';
                    document.getElementById('status-text').textContent = 'Degraded';
                }
            } catch (e) {
                responseTime.textContent = 'Error: ' + e.message;
                responseTime.className = 'response-time slow';
                responseTime.style.display = 'block';
            }
            
            btn.disabled = false;
            loading.classList.remove('active');
        }
        
        renderModels();
        renderExtras();
    </script>
</body>
</html>
""".replace('MODELS_DATA', str(MODELS)).replace('EXTRAS_DATA', str(EXTRAS))

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML

@app.get("/health")
async def health():
    if SLOW_MODE:
        await asyncio.sleep(SLOW_DELAY)
        return {"status": "degraded", "service": "pricing-service", "response_time_ms": int(SLOW_DELAY * 1000), "issue": "high_latency"}
    return {"status": "healthy", "service": "pricing-service", "response_time_ms": random.randint(20, 50)}

@app.post("/api/calculate")
async def calculate(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    # Simulate slow calculation when SLOW_MODE is enabled
    if SLOW_MODE:
        await asyncio.sleep(SLOW_DELAY)
        background_tasks.add_task(notify_slow_response)
    
    model = next((m for m in MODELS if m["id"] == data.get("model")), None)
    if not model:
        return {"error": "Model not found"}
    
    extras_total = sum(e["price"] for e in EXTRAS if e["id"] in data.get("extras", []))
    
    return {
        "model": model["name"],
        "base_price": model["base_price"],
        "extras_total": extras_total,
        "total": model["base_price"] + extras_total,
        "discount": 0,
        "final_price": model["base_price"] + extras_total
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
