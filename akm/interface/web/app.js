// akm/interface/web/app.js

// 🔥 CORRECCIÓN CRÍTICA: Detectar puerto automáticamente
// Esto tomará "http://localhost:8082" si estás en el Nodo Ligero,
// o "http://localhost:8081" si estás en el Minero.
const API_URL = window.location.origin;
let currentAddress = null;

console.log(`🔌 Conectando a la API en: ${API_URL}`);

// --- UI HELPER: Barra de Carga ---
function setLoading(isLoading) {
    const bar = document.getElementById('loading-bar');
    if (!bar) return;
    bar.style.width = isLoading ? '70%' : '100%';
    if (!isLoading) setTimeout(() => bar.style.width = '0%', 300);
}

// --- API CORE ---
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
            if (!res.ok) throw new Error(`Error del servidor (${res.status})`);
        }

        if (!res.ok) throw new Error(data?.detail || 'Error desconocido');
        return data;
    } catch (error) {
        console.error(error);
        alert("❌ Error: " + error.message);
        throw error;
    } finally {
        setLoading(false);
    }
}

// --- LOGIC ---
async function createWallet() {
    // Usamos prompt simple o tomamos del input si existe en el HTML
    // Para compatibilidad con tu HTML, buscamos el input por ID
    const pwdInput = document.getElementById('create-password');
    const pwd = pwdInput ? pwdInput.value : prompt("Crea una contraseña:");

    if (!pwd) return alert("La contraseña es obligatoria");

    const data = await apiCall('/wallet/create', 'POST', { password: pwd });
    loginSuccess(data);

    if (data.mnemonic) {
        const alertBox = document.getElementById('mnemonic-alert');
        if (alertBox) {
            alertBox.classList.remove('hidden');
            document.getElementById('mnemonic-words').innerText = data.mnemonic;
        } else {
            alert(`GUARDA ESTO: ${data.mnemonic}`);
        }
    }
}

async function loadWallet() {
    const pwdInput = document.getElementById('login-password');
    const pwd = pwdInput ? pwdInput.value : prompt("Contraseña:");

    if (!pwd) return alert("Ingresa tu contraseña");

    const data = await apiCall('/wallet/load', 'POST', { password: pwd });
    loginSuccess(data);
}

async function refreshBalance() {
    if (!currentAddress) return;
    try {
        const data = await apiCall(`/balance/${currentAddress}`);

        // data.balance ya viene en formato decimal desde el backend
        // Aseguramos 8 decimales visuales
        const bal = parseFloat(data.balance);

        const balElement = document.getElementById('balance-amount');
        if (balElement) balElement.innerText = bal.toFixed(8);

        const utxoElement = document.getElementById('utxo-count');
        if (utxoElement) utxoElement.innerText = data.utxo_count;

    } catch (e) {
        console.log("Esperando sincronización de saldo...");
    }
}

async function sendTransaction() {
    const toInput = document.getElementById('tx-to');
    const amountInput = document.getElementById('tx-amount');

    // Si no hay inputs en el HTML (diseño móvil), usamos prompts
    const to = toInput ? toInput.value : prompt("Destinatario:");
    const amountVal = amountInput ? amountInput.value : prompt("Monto:");
    const amount = parseFloat(amountVal);

    if (!amount || amount <= 0) return alert("Ingresa un monto válido");

    if (!confirm(`¿Estás seguro de enviar ${amount} AKM?`)) return;

    const data = await apiCall('/transactions', 'POST', {
        recipient_address: to,
        amount: amount,
        fee: 0.00001
    });

    alert(`✅ Transacción Exitosa\nHash: ${data.tx_hash}`);

    if (amountInput) amountInput.value = '';

    setTimeout(refreshBalance, 2000);
}

function loginSuccess(data) {
    currentAddress = data.address;

    const addrElement = document.getElementById('my-address');
    if (addrElement) addrElement.innerText = currentAddress;

    const loginView = document.getElementById('view-login');
    const dashView = document.getElementById('view-dashboard');

    if (loginView && dashView) {
        loginView.classList.add('hidden');
        dashView.classList.remove('hidden');
    }

    refreshBalance();
    setInterval(refreshBalance, 5000);
}

function copyAddress() {
    const text = document.getElementById('my-address').innerText;
    navigator.clipboard.writeText(text);
    alert("Dirección copiada al portapapeles");
}

async function checkNode() {
    try {
        const data = await apiCall('/status');
        const badge = document.getElementById('node-status');

        if (badge) {
            // Mostramos si es Light o Full para claridad
            const role = data.environment === "SPV_MOBILE" ? "Light" : "Full";
            badge.innerHTML = `<i class="bi bi-hdd-network-fill"></i> ${role}: #${data.height}`;
            badge.className = "badge bg-success d-flex align-items-center gap-2 px-3 py-2 rounded-pill";
        }
    } catch (e) {
        const badge = document.getElementById('node-status');
        if (badge) {
            badge.innerHTML = `<i class="bi bi-wifi-off"></i> Offline`;
            badge.className = "badge bg-danger d-flex align-items-center gap-2 px-3 py-2 rounded-pill";
        }
    }
}

// Iniciar chequeo de estado
checkNode();
setInterval(checkNode, 3000);