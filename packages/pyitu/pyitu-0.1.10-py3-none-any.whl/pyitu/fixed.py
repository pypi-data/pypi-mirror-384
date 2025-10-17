lic_ = """
   Copyright 2025 Richard Tjörnhammar

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import numpy as np

__desc__=""" Codes specific to communication or fixed links

def simulate_qam_ber(snr_db, num_symbols, qam=16)
    simulates the SnR Eb/N0 in dB
    - snr_db (array): List of SNR values in dB.
    - num_symbols (int): Number of symbols to transmit per SNR point.
        num_symbols is proportional to the inverse of the wanted BER level

def generate_qam_constellation(M)
    generates the I/Q levels for a modulation order M

def constallation_diagram( qam , bVerbose=False ) 
    generates the I/Q meshgrids and visual boolean constallation diagram at modulation qam
    
"""

def help() :
    print(__desc__)

bin2dec = lambda bits : int(np.sum( [ 2**j * bits[len(bits)-1-j] for j in range(len(bits)) ] , axis=0 ) )
def dec2bin(x):
    return dec2bin(x//2) + [x%2] if x > 1 else [x]

def dec2bin_field(x, bits):
    """Convert int -> list of bits"""
    return np.array(list(np.binary_repr(x, width=bits))).astype(int)

def simulate_qam_ber(snr_db, num_symbols, qam=16):
    """
    Simulates the BER for 16-QAM modulation over an Additive white Gaussian noise (AWGN) channel.

    Parameters:
    - snr_db (array): List of SNR values in dB.
    - num_symbols (int): Number of symbols to transmit per SNR point.

    Returns:
    - ber_list (list): Calculated Bit Error Rates for each SNR value.
    """
    ber_list = []
    nbits = int(np.log2(qam))
    bitlength = nbits // 2

    levels_i, levels_q, bits_i, bits_q = generate_qam_constellation(qam)

    for snr in snr_db:
        tx_bits = np.random.randint(0, 2, num_symbols * nbits)
        tx_bits_reshaped = tx_bits.reshape(-1, nbits)

        # Split bits to I/Q and convert to indices
        i_bits = tx_bits_reshaped[:, :bitlength]
        q_bits = tx_bits_reshaped[:, bitlength:]

        i_index = np.dot(i_bits[:, :bits_i], 2 ** np.arange(bits_i)[::-1])
        q_index = np.dot(q_bits[:, :bits_q], 2 ** np.arange(bits_q)[::-1])

        #tx_symbols = constellation_levels[i_index] + 1j * constellation_levels[q_index]
        tx_symbols = levels_i[i_index] + 1j * levels_q[q_index]

        snr_linear = 10 ** (snr / 10)
        noise_power = 1 / snr_linear
        noise = np.sqrt(noise_power / 2) * (np.random.randn(len(tx_symbols)) + 1j * np.random.randn(len(tx_symbols)))
        rx_symbols = tx_symbols + noise

        # Demodulation
        i_decision = np.argmin(np.abs(rx_symbols.real[:, None] - levels_i), axis=1)
        q_decision = np.argmin(np.abs(rx_symbols.imag[:, None] - levels_q), axis=1)

        rx_i_bits = np.vstack([dec2bin_field(d, bits_i) for d in i_decision])
        rx_q_bits = np.vstack([dec2bin_field(d, bits_q) for d in q_decision])
        rx_bits = np.hstack((rx_i_bits, rx_q_bits)).flatten()

        bit_errors = np.sum(tx_bits != rx_bits)
        ber = bit_errors / (num_symbols * nbits)
        ber_list.append(ber)

    return ber_list


def generate_qam_constellation(M):
    # try to factor into rectangle
    possible = [(i, M//i) for i in range(2, int(np.sqrt(M))+1) if M % i == 0]
    if not possible:
        raise ValueError(f"Cannot form rectangular QAM grid for {M}")
    n_i, n_q = possible[-1]  # pick largest square-like factor
    levels_i = np.arange(-n_i + 1, n_i, 2)*1.0
    levels_q = np.arange(-n_q + 1, n_q, 2)*1.0
    I, Q = np.meshgrid(levels_i, levels_q[::-1])
    avg_power = np.mean(I**2 + Q**2)
    scale = np.sqrt(1 / avg_power)
    levels_i *= scale
    levels_q *= scale
    return levels_i, levels_q, int(np.log2(n_i)), int(np.log2(n_q))

def constallation_diagram( qam , bVerbose=False ) :
    """
    Modulation Bits per symbol Symbol Rate
BPSK 1 1 x bit rate
QPSK 2 1/2 bit rate
8PSK 3 1/3 bit rate
16QAM 4 1/4 bit rate
32QAM 5 1/5 bit rate
64QAM 6 1/6 bit rate
    bin(16) = '0b1000'
    """
    side    = int(np.ceil(np.sqrt(qam)))
    if side%2 !=0 :
        side += 1
    cons1   = np.array([ 2*a - (side+1) for a in range(1,side+1) ])
    cons2   = np.array([ 2*a - (side+1) for a in range(1,side+1) ])
    I,Q     = np.meshgrid(cons1,cons2)
    mask    = np.array([True]*np.prod(np.shape(I))).reshape(np.shape(I))
    correct = side**2 - qam
    if correct > 0 :
        srm     = int( np.floor(np.sqrt(correct/4)) )
        ssrm    = set(cons1[-srm:])
        mask    = np.array([ not ( np.abs(i) in ssrm and np.abs(q) in ssrm) for i,q in  zip(I.reshape(-1),Q.reshape(-1)) ]).reshape(np.shape(I))

    if bVerbose :
        import pandas as pd
        print( "\n", pd.DataFrame(I) ,"\n\n", pd.DataFrame(Q) , "\n\n" , pd.DataFrame(mask) )
        print( np.sum(mask) )
    average_energy = 2 * (np.sum(I[0]**2)) / 4 # FOR NORMALISATION
    return ( I , Q , mask , average_energy )

if __name__ == '__main__':

    import matplotlib.pyplot as plt

    constallation_diagram(16 , bVerbose=True )

    # Example usage and plotting
    snr_db      = np.arange(0, 40, 2) # SNR range from 0 to 20 dB
    num_symbols = 100000 # Increase for smoother curves

    ber_4qam    = simulate_qam_ber( snr_db , num_symbols, qam=  4 )
    ber_16qam   = simulate_qam_ber( snr_db , num_symbols, qam= 16 )
    ber_32qam   = simulate_qam_ber( snr_db , num_symbols, qam= 32 )
    ber_64qam   = simulate_qam_ber( snr_db , num_symbols, qam= 64 )
    ber_256qam  = simulate_qam_ber( snr_db , num_symbols, qam=256 )

    plt.figure()
    plt.semilogy(snr_db, ber_4qam, 'o-' , label='Simulated 4-QAM')
    plt.semilogy(snr_db, ber_16qam, 'x-', label='Simulated 16-QAM')
    plt.semilogy(snr_db, ber_32qam, '-' , label='Simulated 32-QAM')
    plt.semilogy(snr_db, ber_64qam, 'd-', label='Simulated 64-QAM')
    plt.semilogy(snr_db, ber_256qam, 'k', label='Simulated 256-QAM')
    plt.title('16-QAM Bit Error Rate Performance over AWGN')
    plt.xlabel('SNR (Eb/N0) in dB')
    plt.ylabel('Bit Error Rate (BER)')
    plt.grid(True, which="both")
    plt.legend()
    plt.show()
