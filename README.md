# A CBC-like Finality Gadget for Ethereum

The following is joint work with Stefanos Leonardos, BarnabÃ© Monnot, and Georgios Piliouras.

We propose a CBC-like finality gadget that can be overlaid onto a longest-chain proof-of-stake protocol like LMD GHOST. Our main design goal is that, as in CBC Casper, each user $i$ is free to set her own security threshold that represents the highest attacker-controlled stake fraction that she is willing to tolerate. We achieve this without additional message complexity -€“ that is, we completely piggyback on the underlying proof-of-stake algorithm.