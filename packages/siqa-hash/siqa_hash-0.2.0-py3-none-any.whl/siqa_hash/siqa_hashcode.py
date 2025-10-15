from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import Aer
from qiskit.quantum_info import random_unitary
import numpy as np
from itertools import product
from math import pi, ceil, log2
import hashlib

#siqa hash (simplified quantum hash)



def binary_blocks_for_walk(message: str, block_size: int = 2):
    message_bytes = message.encode("utf-8")
    binary_str = ''.join(format(byte, '08b') for byte in message_bytes)
    blocks = [binary_str[i:i+block_size] for i in range(0, len(binary_str), block_size)]
    if len(blocks[-1]) < block_size:
        blocks[-1] = blocks[-1].ljust(block_size, '0')
    return blocks


def quantum_walk_cycle(message: str, hash_bits: int = 8):
    block_size = 2
    walkblocks = binary_blocks_for_walk(message, block_size)
    n_pos = ceil(log2(hash_bits))
    pos = QuantumRegister(n_pos, "pos")
    coin = QuantumRegister(1, "coin")
    qc = QuantumCircuit(pos, coin, name="QW_cycle")

    theta_map = {"00": pi/3, "01": pi/6, "10": 4*pi/9, "11": pi/8}

    def controlled_increment():
        for i in range(n_pos):
            qc.x(coin[0])
            qc.mcx([coin[0]] + list(pos[:i]), pos[i])
            qc.x(coin[0])

    def controlled_decrement():
        for i in reversed(range(n_pos)):
            qc.mcx([coin[0]] + list(pos[:i]), pos[i])

    for block in walkblocks:
        theta = theta_map.get(block, pi/4)
        qc.ry(theta, coin[0])
        controlled_increment()
        controlled_decrement()

    return qc, pos, coin


def qft(ckt, qubits):
    n = len(qubits)
    for j in range(n):
        ckt.h(qubits[j])
        for k in range(j+1, n):
            angle = np.pi / (2 ** (k-j))
            ckt.cp(angle, qubits[k], qubits[j])


def siqahash(msg):
    hash_bits = 8
    n_anc = 5
    shots = 1024
    n_pos = ceil(log2(hash_bits))

    qc, pos, coin = quantum_walk_cycle(msg, hash_bits)
    qft(qc, pos)

    anc = QuantumRegister(n_anc, 'anc')
    cr_anc = ClassicalRegister(n_anc, 'c_anc')
    qc.add_register(anc)
    qc.add_register(cr_anc)

    qc.h(anc)

    from qiskit.circuit.library import UnitaryGate
    for i in range(n_anc):
        msg_seed = int(hashlib.sha256((msg + str(i)).encode()).hexdigest(), 16) % (2**32 - 1)
        U = random_unitary(2**n_pos, seed=msg_seed).data
        u_gate = UnitaryGate(U)
        qc.append(u_gate.control(1), [anc[i]] + list(pos))

    qc.measure(anc, cr_anc)

    simulator = Aer.get_backend('qasm_simulator')
    transpiled_ckt = transpile(qc, simulator)
    job = simulator.run(transpiled_ckt, shots=shots)
    result = job.result()
    counts = result.get_counts(qc)

    if not counts:
        counts = {'0' * n_anc: shots}

    counts_str = ''.join(f"{k}:{counts.get(k,0)};" for k in sorted(counts.keys()))
    digest_hex = hashlib.sha256(counts_str.encode()).hexdigest()
    digest_bin = bin(int(digest_hex, 16))[2:].zfill(256)

    desired_len = n_anc * (2 ** n_pos)
    final_hash = digest_bin[:desired_len]

    print(f"Hash output ({len(final_hash)} bits):", final_hash)
    return final_hash

def main():
    user_input = input("Enter the message to hash using SIQA: ")
    print("\nRunning quantum hash... Please wait.\n")
    final_output = siqahash(user_input)
    print("\nFinal SIQA hash for your input:")
    print(final_output)
    

if __name__ == "__main__":
    main()
    
