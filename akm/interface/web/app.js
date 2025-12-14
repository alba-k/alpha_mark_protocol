// akm/interface/web/app.js

/**
 * CONFIGURACIÓN DE CONEXIÓN
 * Detecta si estamos corriendo vía servidor (FastAPI) o archivo local.
 */
const getApiUrl = () => {
    // Si la URL es file://, asumimos localhost por defecto para pruebas
    if (window.location.protocol === 'file:') {
        return 'http://localhost:8000'; // Ajusta el puerto si tu uvicorn usa otro
    }
    // Si es http/https, usamos el origen actual (la API sirve el frontend)
    return window.location.origin;
};

const API_URL = getApiUrl();
let currentAddress = null;

console.log(`🔌 Conectando a la API en: ${API_URL}`);

// --- UI HELPER: Barra de Carga ---
function setLoading(isLoading) {
    const bar = document.getElementById('loading-bar');
    if (!bar) return;
    bar.style.width = isLoading ? '70%' : '100%';
    if (!isLoading) {
        setTimeout(() => bar.style.width = '0%', 300);
    } else {
        bar.style.display = 'block';
    }
}

// --- API CORE (Wrapper Fetch) ---
async function apiCall(endpoint, method = 'GET', body = null) {
    setLoading(true);
    try {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) options.body = JSON.stringify(body);

        const res = await fetch(`${API_URL}${endpoint}`, options);

        // Manejo robusto de errores HTTP
        let data;
        try {
            data = await res.json();
        } catch (e) {
            // Si no es JSON pero falló
            if (!res.ok) throw new Error(`Error del servidor (${res.status})`);
        }

        if (!res.ok) throw new Error(data?.detail || `Error ${res.status}: Fallo desconocido`);
        return data;
    } catch (error) {
        console.error("API Error:", error);
        alert(`❌ Error de Conexión:\n${error.message}`);
        throw error;
    } finally {
        setLoading(false);
    }
}

// --- LÓGICA DE BILLETERA ---

async function createWallet() {
    const pwdInput = document.getElementById('create-password');
    const pwd = pwdInput ? pwdInput.value : null;

    if (!pwd) return alert("La contraseña es obligatoria");

    try {
        // NOTA: Requiere que implementes @app.post("/wallet/create") en server.py
        const data = await apiCall('/wallet/create', 'POST', { password: pwd });

        // Mostrar mnemónica si existe
        if (data.mnemonic) {
            const alertBox = document.getElementById('mnemonic-alert');
            const wordBox = document.getElementById('mnemonic-words');
            if (alertBox && wordBox) {
                alertBox.classList.remove('hidden');
                wordBox.innerText = data.mnemonic;
            }
        }

        loginSuccess(data);
    } catch (e) {
        // Error ya manejado en apiCall
    }
}

async function loadWallet() {
    const pwdInput = document.getElementById('login-password');
    const pwd = pwdInput ? pwdInput.value : null;

    if (!pwd) return alert("Ingresa tu contraseña");

    try {
        // NOTA: Requiere que implementes @app.post("/wallet/load") en server.py
        const data = await apiCall('/wallet/load', 'POST', { password: pwd });
        loginSuccess(data);
    } catch (e) {
        // Error ya manejado
    }
}

function loginSuccess(data) {
    currentAddress = data.address;

    // Actualizar UI
    const addrElement = document.getElementById('my-address');
    if (addrElement) addrElement.innerText = currentAddress;

    // Cambiar vista
    const loginView = document.getElementById('view-login');
    const dashView = document.getElementById('view-dashboard');

    if (loginView && dashView) {
        loginView.classList.add('hidden');
        dashView.classList.remove('hidden');
    }

    // Iniciar polling de saldo
    refreshBalance();
    setInterval(refreshBalance, 10000); // Cada 10s
}

// --- OPERACIONES ---

async function refreshBalance() {
    if (!currentAddress) return;
    try {
        const data = await apiCall(`/balance/${currentAddress}`);

        const balElement = document.getElementById('balance-amount');
        if (balElement) {
            // Animación simple de actualización visual
            balElement.style.opacity = '0.5';
            setTimeout(() => {
                // Formatear a 8 decimales fijos
                balElement.innerText = parseFloat(data.balance).toFixed(8);
                balElement.style.opacity = '1';
            }, 200);
        }

        const utxoElement = document.getElementById('utxo-count');
        if (utxoElement) utxoElement.innerText = data.utxo_count;

    } catch (e) {
        console.warn("Fallo silencioso al actualizar saldo:", e.message);
    }
}

async function sendTransaction() {
    const toInput = document.getElementById('tx-to');
    const amountInput = document.getElementById('tx-amount');

    const to = toInput.value.trim();
    const amount = parseFloat(amountInput.value);

    if (!to) return alert("Falta la dirección de destino");
    if (!amount || amount <= 0) return alert("Ingresa un monto válido");

    if (!confirm(`⚠️ ¿Estás seguro de enviar ${amount} AKM a:\n${to}?`)) return;

    try {
        const data = await apiCall('/transactions', 'POST', {
            recipient_address: to,
            amount: amount,
            fee: 0.00001 // Tarifa fija por defecto
        });

        alert(`✅ Transacción Enviada con Éxito!\nHash: ${data.tx_hash}`);

        // Limpiar formulario
        toInput.value = '';
        amountInput.value = '';

        // Actualizar saldo (aunque tomará tiempo confirmarse)
        setTimeout(refreshBalance, 2000);
    } catch (e) {
        // Error manejado en apiCall
    }
}

// --- UTILIDADES ---

function copyAddress() {
    const text = document.getElementById('my-address').innerText;
    if (text === 'Cargando...' || text === '...') return;

    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector('button[onclick="copyAddress()"]');
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2"></i>';
        btn.classList.replace('btn-dark', 'btn-success');

        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.replace('btn-success', 'btn-dark');
        }, 1500);
    }).catch(err => {
        alert("Error al copiar: " + err);
    });
}

async function checkNode() {
    try {
        const data = await apiCall('/status');
        const badge = document.getElementById('node-status');

        if (badge) {
            const role = data.environment === "SPV_CLIENT" ? "SPV Móvil" : "Full Node";
            const colorClass = data.peers_count > 0 ? "bg-success" : "bg-warning";

            badge.innerHTML = `<i class="bi bi-hdd-network-fill"></i> ${role}: #${data.height} (${data.peers_count} pares)`;
            badge.className = `badge ${colorClass} d-flex align-items-center gap-2 px-3 py-2 rounded-pill shadow-sm`;
        }
    } catch (e) {
        const badge = document.getElementById('node-status');
        if (badge) {
            badge.innerHTML = `<i class="bi bi-wifi-off"></i> Desconectado`;
            badge.className = "badge bg-danger d-flex align-items-center gap-2 px-3 py-2 rounded-pill shadow-sm";
        }
    }
}

// Iniciar chequeo de estado inmediatamente
checkNode();
setInterval(checkNode, 5000);