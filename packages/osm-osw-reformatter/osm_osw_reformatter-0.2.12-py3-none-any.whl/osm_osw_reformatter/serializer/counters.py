import osmium


class WayCounter(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def way(self, w) -> None:
        self.count += 1


class PointCounter(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def node(self, p) -> None:
        self.count += 1


class NodeCounter(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def node(self, n) -> None:
        self.count += 1


class PolygonCounter(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def area(self, n):
        self.count += 1


class ZoneCounter(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def area(self, n):
        self.count += 1


class LineCounter(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def way(self, n):
        self.count += 1