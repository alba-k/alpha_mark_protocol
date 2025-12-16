# 🔱 Alpha Mark Protocol (AKM)

![Alpha Mark Protocol Logo Placeholder](https://img.shields.io/badge/Alpha%20Mark%20Protocol-AKM-0077B6?style=for-the-badge&logo=python)

**Slogan:** Blockchain Pura para la Programación Superior.

**Descripción:** AKM es una implementación completa de una red de criptomoneda de baja capa (Layer-1) diseñada para demostrar los principios de la programación distribuida y el consenso. El protocolo utiliza un robusto **modelo UTXO** (Unspent Transaction Output) y un mecanismo de **Proof-of-Work (PoW)** con dificultad dinámica para garantizar la seguridad y la inmutabilidad de la cadena.

## 📋 Tabla de Contenido

1. [⚙️ Características Principales](#️-características-principales)
2. [🏛️ Arquitectura y Stack](#️-arquitectura-y-stack)
3. [🚀 Guía de Instalación y Uso](#-guía-de-instalación-y-uso)
    * [Paso 1: Instalación de Dependencias](#paso-1-instalación-de-dependencias)
    * [Paso 2: Configuración de Red (Seeds)](#paso-2-configuración-de-red-seeds)
    * [Paso 3: Arranque de Nodos](#paso-3-arranque-de-nodos)
4. [📚 Uso Avanzado y API](#-uso-avanzado-y-api)
5. [🧑‍💻 Desarrollo y Contribución](#-desarrollo-y-contribución)
6. [📜 Licencia y Contacto](#-licencia-y-contacto)

---

## ⚙️ Características Principales

El Alpha Mark Protocol está diseñado para ser una blockchain educativa pero funcional, cubriendo los siguientes aspectos:

* **Modelo de Transacción UTXO:** Utiliza el modelo de Salidas de Transacción No Gastadas, gestionado por el `UTXOSet`, previniendo el doble gasto de forma determinística.
* **Proof-of-Work (PoW):** Implementa un proceso de minería completo que busca un `nonce` para validar el `block_hash` contra un objetivo de dificultad.
* **Dificultad Dinámica:** La dificultad de minería se ajusta para mantener constante el tiempo de generación de bloques, asegurando la estabilidad del protocolo.
* **Criptografía Estándar:** Utiliza la curva **SECP256k1** con el algoritmo **ECDSA** para la firma de transacciones, y codificación **Base58Check** para las direcciones.
* **Billeteras Cifradas:** El almacén de claves (`wallet.dat`) se cifra utilizando **Fernet (AES)** con una contraseña reforzada por **PBKDF2HMAC** para protección física.

---

## 🏛️ Arquitectura y Stack

### Stack Tecnológico

| Componente | Herramienta/Librería | Razón |
| :--- | :--- | :--- |
| **Lenguaje** | Python 3.10+ | Lenguaje principal del proyecto. |
| **API** | FastAPI / Uvicorn | Servidor REST de alto rendimiento para la comunicación SPV y el *gossip* de red. |
| **Criptografía** | `ecdsa`, `cryptography`, `pycryptodome` | Implementaciones robustas para hashing, curvas elípticas y gestión de firmas. |
| **Base de Datos** | SQLite 3 | Utilizada para la persistencia del `BlockchainRepository` (cadena inmutable) y el `UTXORepository` (estado mutable). |

### Roles de Nodos

| Rol | Archivo de Config. | Puerto P2P | Función Principal |
| :--- | :--- | :--- | :--- |
| **FULL_NODE** | `fullnode.json` | 6000 | Sincroniza, valida y almacena la cadena completa. Es el punto de inicio de la red. |
| **MINER** | `miner.json` | 6001 | Ejecuta el PoW y recibe la recompensa. |
| **SPV_NODE** | `spv.json`, `recipient.json` | 0 | Billetera ligera. Proporciona una API para firmar transacciones localmente y consulta saldos. |

---

## 🚀 Guía de Instalación y Uso

### Paso 1: Instalación de Dependencias

1.  Cree y active su entorno virtual (`venv`):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    source venv/bin/activate # Linux/macOS o Git Bash
    ```
2.  Instale todas las dependencias necesarias:
    ```bash
    pip install -r requirements.txt
    ```

### Paso 2: Configuración de Red (Seeds)

**CRÍTICO:** Asumiendo que el Full Node (Maestro) está en `172.21.16.1`, actualice el campo `"seeds"` a **`["172.21.16.1:6000"]`** en `config/miner.json`, `config/spv.json` y `config/recipient.json`.

### Paso 3: Arranque de Nodos

#### 3.1. Generación de Billeteras (Identidad)

Este paso crea las identidades (`wallet.dat`) y las direcciones públicas. Detenga cada nodo con `CTRL+C` una vez iniciado:

```bash
# Billetera del Minero (Tu Laptop): Genera el wallet.dat para recibir recompensas.
python main.py config/spv.json --name billetera_minero_gasto --api 8085 
# (Copie la dirección pública generada y péguela en "miner_address" de config/miner.json)

# Billetera Principal (Laptop 1)
python main.py config/spv.json --name billetera_akm --api 8080 

# Billetera Destinatario (Laptop 1)
python main.py config/recipient.json --name billetera_destinatario --api 8081