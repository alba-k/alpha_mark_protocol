# akm/core/validators/transaction_rules_validator.py
import logging

from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.managers.utxo_set import UTXOSet
from akm.core.validators.transaction_validator import TransactionValidator
from akm.infra.identity.address_factory import AddressFactory
from akm.core.services.transaction_hasher import TransactionHasher

logging.basicConfig(level=logging.INFO, format='[TxRulesValidator] %(message)s')

class TransactionRulesValidator:

    def __init__(self, utxo_set: UTXOSet):
        self._utxo_set = utxo_set

    def validate(self, tx: Transaction) -> bool:
        # 1. Coinbase se valida aparte
        if tx.is_coinbase:
            return True

        # 2. Integridad básica
        if not TransactionValidator.verify_integrity(tx):
            logging.error(f"TX {tx.tx_hash[:8]}: Fallo de integridad hash.")
            return False

        # 3. Validar firmas y fondos
        try:
            input_sum = self._validate_inputs_and_signatures(tx)
        except ValueError as e:
            logging.error(f"TX {tx.tx_hash[:8]} RECHAZADA: {e}")
            return False

        # 4. Balance (No crear dinero de la nada)
        output_sum = sum(out.value_alba for out in tx.outputs)

        if output_sum > input_sum:
            logging.error(f"TX {tx.tx_hash[:8]}: Salida ({output_sum}) excede Entrada ({input_sum}).")
            return False

        return True

    def _validate_inputs_and_signatures(self, tx: Transaction) -> int:
        # --- PASO CRÍTICO: CALCULAR EL SIGHASH ---
        
        # 1. Crear copias de los inputs limpias
        clean_inputs = [
            TxInput(inp.previous_tx_hash, inp.output_index, script_sig="") 
            for inp in tx.inputs
        ]
        
        # 2. Transacción temporal para firmar
        signing_tx = Transaction(
            tx_hash="",
            timestamp=tx.timestamp,
            inputs=clean_inputs,
            outputs=tx.outputs,
            fee=tx.fee
        )
        
        # 3. Hash de Firma (SigHash)
        sighash = TransactionHasher.calculate(signing_tx)

        # --- VALIDACIÓN ---
        total_in = 0

        for index, inp in enumerate(tx.inputs):
            # Ignorar input nulo de Coinbase/Génesis
            if inp.previous_tx_hash == "0" * 64:
                 continue

            # A. Buscar UTXO
            utxo = self._utxo_set.get_utxo_by_reference(inp.previous_tx_hash, inp.output_index)
            if not utxo:
                raise ValueError(f"Input #{index}: UTXO no encontrado o ya gastado.")
            
            # B. Desempaquetar P2PKH (Firma + Clave Pública)
            try:
                # ⚡ CORRECCIÓN: Decodificar bytes a string antes de hacer split
                script_data = inp.script_sig
                if isinstance(script_data, bytes):
                    # Intentamos utf-8, si falla (datos binarios raros) usamos latin-1
                    try:
                        script_str = script_data.decode('utf-8')
                    except UnicodeDecodeError:
                        script_str = script_data.decode('latin-1')
                else:
                    script_str = str(script_data)

                parts = script_str.split(" ")
                
                if len(parts) != 2:
                    # Intento de fallback: A veces se unen sin espacio si la codificación falló
                    raise ValueError("Formato incorrecto (Esperado: 'Firma PubKey')")
                
                signature_hex = parts[0]
                public_key_hex = parts[1]
                
            except Exception as e:
                raise ValueError(f"Input #{index}: ScriptSig malformado ({e}).")

            # C. Verificar Propiedad
            # Aseguramos que script_pubkey del UTXO también se trate como string para comparar
            utxo_addr = utxo.script_pubkey
            if isinstance(utxo_addr, bytes):
                utxo_addr = utxo_addr.decode('utf-8')

            derived_address = AddressFactory.create_from_public_key(public_key_hex)
            
            if derived_address != utxo_addr:
                raise ValueError(f"Input #{index}: Clave pública no corresponde al dueño.")

            # D. VERIFICAR FIRMA
            is_valid_sig = TransactionValidator.verify_signature(
                public_key_hex=public_key_hex,
                tx_hash=sighash, 
                signature_hex=signature_hex
            )

            if not is_valid_sig:
                raise ValueError(f"Input #{index}: Firma criptográfica inválida.")

            total_in += utxo.value_alba

        return total_in