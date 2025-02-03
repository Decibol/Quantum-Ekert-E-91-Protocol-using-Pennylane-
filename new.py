import pennylane as qml
from pennylane import numpy as np
import random
from math import pi

n = 100

np.random.seed(seed=13)
alice_bases = np.random.randint(3, size=n)
print("Alice's bases:", alice_bases)

np.random.seed(seed=15)
bob_bases = np.random.randint(3, size=n)
print("Bob's bases:", bob_bases)

def measure_pairs(alice_bases, bob_bases, eve_bits=None):
    measurements = []
    for q in range(n):
        eve_measure = eve_bits is not None and q in eve_bits
        dev = qml.device('default.qubit', wires=2, shots=1)
        
        @qml.qnode(dev)
        def circuit():
            # Create EPR pair (|11> -> H on 0 -> CNOT -> (|00> - |11>)/√2)
            qml.PauliX(0)
            qml.PauliX(1)
            qml.Hadamard(0)
            qml.CNOT(wires=[0, 1])
            
            # Eve's measurement on Bob's qubit
            if eve_measure:
                qml.measure(1)
            
            # Alice's operations
            if alice_bases[q] == 1:
                qml.RZ(pi/2, wires=0)
            elif alice_bases[q] == 2:
                qml.RZ(pi/4, wires=0)
            qml.Hadamard(0)
            
            # Bob's operations
            if bob_bases[q] == 1:
                qml.RZ(-pi/4, wires=1)
            elif bob_bases[q] == 2:
                qml.RZ(pi/4, wires=1)
            qml.Hadamard(1)
            
            return qml.sample(wires=0), qml.sample(wires=1)
        
        alice_result, bob_result = circuit()
        measurements.append([int(alice_result), int(bob_result)])
    return measurements

def create_sifted_key(measurement, alice, bob):
    sifted_key = []
    not_entangled = 0
    for i in range(n):
        if (alice[i] == bob[i] == 0) or (alice[i] == bob[i] == 2):
            sifted_key.append((measurement[i][0], measurement[i][1]))
            if measurement[i][0] == measurement[i][1]:
                not_entangled += 1
    return (sifted_key, f"Sifted key length: {len(sifted_key)}, Non-entangled bits: {not_entangled}")

def expected_value(measurements, alice, bob, a_setting, b_setting):
    pp = mm = pm = mp = 0
    for i in range(n):
        if alice[i] == a_setting and bob[i] == b_setting:
            a, b = measurements[i]
            if a == 1 and b == 1: pp += 1
            elif a == 0 and b == 0: mm += 1
            elif a == 1 and b == 0: pm += 1
            elif a == 0 and b == 1: mp += 1
    total = pp + mm + pm + mp
    return (pp - pm - mp + mm) / total if total else 0.0

def CHSH_calc(measurements, alice, bob):
    S = (expected_value(measurements, alice, bob, 0, 2) +
         expected_value(measurements, alice, bob, 0, 1) +
         expected_value(measurements, alice, bob, 1, 2) -
         expected_value(measurements, alice, bob, 1, 1))
    return abs(S)

eve_bits = random.sample(range(n), n//4)
eve_bits.sort()
print("Eve's bits:", eve_bits)

def eve_detected(s_value):
    if s_value > 2.8:
        print("Eve undetected")
    elif 2.5 < s_value <= 2.8:
        print("Possible eavesdropping (could be noise)")
    elif 2 < s_value <= 2.5:
        print("Likely eavesdropping")
    else:
        print("Eve detected!")

# Main execution
output = measure_pairs(alice_bases, bob_bases, eve_bits)
sifted_key, key_info = create_sifted_key(output, alice_bases, bob_bases)
s = CHSH_calc(output, alice_bases, bob_bases)

print("\nResults:")
print(key_info)
print(f"CHSH value: {s:.4f}")
eve_detected(s)