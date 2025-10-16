class Lineage:
    def __init__(self, lineage: str, ranks: str):
        self.pairs = []

        nodes_list = lineage.split(";")
        ranks_list = ranks.split(";")
        for i, (node, rank) in enumerate(zip(nodes_list, ranks_list)):
            self.pairs.append((node, rank))

    def __iter__(self):
        self.pos = len(self.pairs) - 1
        return self

    def __next__(self):
        if self.pos > 0:
            node, rank = self.pairs[self.pos]
            self.pos -= 1
            return (node, rank)
        else:
            raise StopIteration


class LineageRankPair():
    def __init__(self, lineage, rank):
        self.lineage = lineage
        self.rank = rank
