class Sections:
    def __init__(self):
        
        self.POPULARP_PRODUCTS = "Popular Products"
        self.RECOMMENDATIOS = "Recomendations"
        self.EXPLORE = "Explore"

        self.CURRENT_SECTION = self.POPULARP_PRODUCTS

    def getSections(self):
        sections = list(self.__dict__.values())

        sections.remove(getattr(self, "CURRENT_SECTION"))

        sections.sort()
        return sections
    
    def updataSection(self, sectionName):
        self.CURRENT_SECTION = sectionName


PopularBooks = ["The Fountainhead", "Principles of software development",  "The 3 Mistakes of My Life", "12 rules for life"]
PopularCoverIdxs = [1, 4, 1, 1]

nextPopularBooks = ["12 more rules for life", "Atlas shrugged", "Rich dad poor dad"]

nextNextPopularBooks = ["gulliver's travells", 'merchant of the venice', 'macbeth']