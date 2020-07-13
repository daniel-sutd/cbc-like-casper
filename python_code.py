BLOCK_REWARD = 10;
ATTESTATION_REWARD = 1;

class Block:
     def __init__(self, name, previous, proposer, slot, committee, attestations, deltas):
        self.name = name
        self.previous = previous
        self.proposer = proposer
        self.slot = slot
        self.committee = []
        for member in committee:
            self.committee.append(member)
        self.attestations = []
        for attestation in attestations:
            self.attestations.append(attestation)
        self.deltas = []
        for delta in deltas:
            self.deltas.append(delta)

        if previous is None:
            self.height = 0
        else:
            self.height = previous.height + 1

class Attestation:
    def __init__(self, validator, slot, targetblock):
        self.validator = validator
        self.slot = slot
        self.targetblock = targetblock

class Delta:
    def __init__(self, validator, size):
        self.validator = validator
        self.size = size

class FinalityGadget:
    def __init__(self, genesis, validators, deposits):
        self.g = genesis
        self.B = [genesis]
        self.S = {}
        self.S_max = {}
        self.D = {}
        self.L = {}
        self.S[genesis] = 0
        self.S_max[genesis] = 0
        for i in range(len(validators)):
            v = validators[i]
            d = deposits[i]
            self.D[v] = d
            self.L[v] = genesis
            self.S[genesis] += d
            self.S_max[genesis] += d

    def validateBlock(self, b):
        return True

    def isSlashable(self, b1, b2):
        return False

    def slash(self, v):
        return None

    def getBlocksBetween(self, b, lastBlock):
        c = b
        blocks = []
        while c.height > lastBlock.height:
            blocks.append(c)
            c = c.previous
        return blocks;

    def findLastCommonAncestor(self, b1, b2):
        c1 = b1
        c2 = b2
        while c1.height > c2.height:
            c1 = c1.previous;
        while c1.height < c2.height:
            c2 = c2.previous;
        while c1 != c2:
            c1 = c1.previous;
            c2 = c2.previous;
        return c1;

    def getLastAttestedBlock(self, blocks, v):
        for b in blocks:
            if v == b.proposer:
                return b
            for a in b.attestations:
                if v == a.validator:
                    return b
        if len(blocks) > 0:
            return blocks[len(blocks)-1]
        return None

    def processConflict(self, v, newBlock, lastBlock):
        slashable = self.isSlashable(newBlock, lastBlock)
        if slashable:
            self.slash(v)
        else:
            c = self.findLastCommonAncestor(newBlock, lastBlock)
            oldChain = self.getBlocksBetween(lastBlock, c)
            newChain = self.getBlocksBetween(newBlock, c)
            l = self.getLastAttestedBlock(newChain, v)
            newChainPre = self.getBlocksBetween(l.previous, c)
            newChainPost = self.getBlocksBetween(newBlock, l.previous)
            self.updateDeposits(oldChain, v, -1)
            self.updateDeposits(newChainPre, v, 1)
            self.processForward(newChainPost, v)

    def processForward(self, blocks, v):
        for b in reversed(blocks):
            self.updateDeposit(b, v, 1)
            self.S[b] += self.D[v]

    def updateDeposits(self, blocks, v, multiplier):
        for b in blocks:
            self.updateDeposit(b, v, multiplier)

    def updateDeposit(self, b, v, multiplier):
        for a in b.attestations:
            if v == a.validator:
                self.D[v] += multiplier * ATTESTATION_REWARD
        for delta in b.deltas:
            if v == delta.validator:
                self.D[v] += multiplier * delta.size
        if v == b.proposer:
            self.D[v] +=  multiplier * BLOCK_REWARD

    def processAttestation(self, v, b):
        lastBlock = self.L[v]
        blocks = self.getBlocksBetween(b, lastBlock)
        if len(blocks) == 0 and b != lastBlock or len(blocks) > 0 and blocks[len(blocks)-1].previous != lastBlock:
            print("conflict! "+v+": new = "+b.name+", last = "+lastBlock.name)
            self.processConflict(v, b, lastBlock)
        else:
            self.processForward(blocks, v)
        self.L[v] = b

    def processBlock(self, b):
        isValid = self.validateBlock(b)
        if isValid:
            self.B.append(b)
            self.S[b] = 0
            self.S_max[b] = self.S_max[b.previous] + BLOCK_REWARD
            for attestation in b.attestations:
                v = attestation.validator
                t = attestation.targetblock
                self.processAttestation(v, t)
                self.S_max[b] += ATTESTATION_REWARD
            for delta in b.deltas:
                z = delta.size
                self.S_max[b] += z
            self.processAttestation(b.proposer, b)

    def printDeposits(self):
        print("Deposits:");
        for v in self.D:
            print(" "+v+": "+str(self.D[v]))

    def printSupport(self):
        print("Support:")
        for b in self.B:
            print(" "+b.name+": "+str(self.S[b])+"/"+str(self.S_max[b]))

def processBlocks(gadget, blocks):
    for b in blocks:
        gadget.processBlock(b)
    gadget.printDeposits()
    gadget.printSupport()

g = Block("genesis", None, None, 0, [], [], [])

print("--- simple example ---")

gadget = FinalityGadget(g, ["v1", "v2", "v3", "v4", "v5"], [10, 15, 20, 25, 30])

b1 = Block("b1", g,  "v1", 1, ["v3", "v4"], [], [])
b2 = Block("b2", b1, "v2", 2, ["v4", "v5"], [Attestation("v4", 1, b1)], [])
b3 = Block("b3", b2, "v3", 3, ["v1", "v2"], [Attestation("v3", 1, b1), Attestation("v4", 2, b1), Attestation("v5", 2, b2)], [])
b4 = Block("b4", b3, "v5", 4, ["v1", "v5"], [Attestation("v1", 3, b3), Attestation("v2", 3, b2)], [])
b5 = Block("b5", b4, "v4", 5, ["v2", "v5"], [Attestation("v1", 4, b3), Attestation("v5", 4, b4)], [])
b6 = Block("b6", b5, "v3", 6, ["v1", "v3"], [Attestation("v2", 5, b5), Attestation("v5", 5, b5)], [])
b7 = Block("b7", b6, "v5", 7, ["v1", "v2"], [Attestation("v1", 6, b6), Attestation("v3", 6, b6)], [])

gadget.processBlock(b1)
gadget.processBlock(b2)
gadget.processBlock(b3)
gadget.processBlock(b4)
gadget.processBlock(b5)
gadget.processBlock(b6)
gadget.processBlock(b7)
gadget.printDeposits()
gadget.printSupport()

print("--- fork example ---")

gadget = FinalityGadget(g, ["v1", "v2", "v3", "v4", "v5"], [10, 15, 20, 25, 30])

blocks = []

blocks.append(Block("b1",g, "v1", 1, ["v3", "v4"], [], []))
blocks.append(Block("b2",blocks[0], "v2", 2, ["v4", "v5"], [Attestation("v4",1,blocks[0])], []))
blocks.append(Block("b3",blocks[1], "v3", 3, ["v1", "v2"], [Attestation("v3",1,blocks[0]), Attestation("v4",2,blocks[0]), Attestation("v5",2,blocks[1])], []))
blocks.append(Block("b4",blocks[1], "v5", 4, ["v1", "v5"], [Attestation("v1",3,blocks[1]), Attestation("v2",3,blocks[1])], []))
blocks.append(Block("b5",blocks[3], "v4", 5, ["v2", "v5"], [Attestation("v1",4,blocks[1]), Attestation("v5",4,blocks[3])], []))
blocks.append(Block("b6",blocks[4], "v3", 6, ["v1", "v4"], [Attestation("v2",5,blocks[4]), Attestation("v5",5,blocks[4])], [Delta("v1",50), Delta("v2",-20)]))
blocks.append(Block("b7",blocks[5], "v5", 7, ["v1", "v3"], [Attestation("v1",6,blocks[5]), Attestation("v4",6,blocks[5])], []))
blocks.append(Block("b8",blocks[6], "v1", 8, ["v4", "v5"], [Attestation("v1",7,blocks[6]), Attestation("v3",7,blocks[6])], []))
blocks.append(Block("b9",blocks[7], "v2", 9, ["v1", "v2"], [Attestation("v4",8,blocks[7]), Attestation("v5",8,blocks[7])], []))
blocks.append(Block("b10",blocks[8], "v3", 10, ["v4", "v5"], [Attestation("v1",9,blocks[8]), Attestation("v2",9,blocks[8])], []))
blocks.append(Block("b11",blocks[9], "v4", 11, ["v1", "v3"], [Attestation("v4",10,blocks[9]), Attestation("v5",10,blocks[9])], []))
blocks.append(Block("b12",blocks[10], "v3", 12, ["v4", "v5"], [Attestation("v1",11,blocks[10]), Attestation("v3",11,blocks[10])], []))
blocks.append(Block("b13",blocks[9], "v1", 13, ["v2", "v3"], [Attestation("v5",12,blocks[9])], []))
blocks.append(Block("b14",blocks[12], "v1", 14, ["v3", "v5"], [Attestation("v2",13,blocks[12]), Attestation("v3",13,blocks[12])], []))
blocks.append(Block("b15",blocks[13], "v2", 15, ["v3", "v4"], [Attestation("v3",14,blocks[13]), Attestation("v5",14,blocks[13])], []))
blocks.append(Block("b16",blocks[14], "v5", 16, ["v1", "v2"], [Attestation("v3",15,blocks[14]), Attestation("v4",15,blocks[14])], []))

processBlocks(gadget,blocks)
