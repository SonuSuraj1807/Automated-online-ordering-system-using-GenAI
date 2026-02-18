from abc import ABC, abstractmethod

class CommerceAgent(ABC):
    def __init__(self, page):
        self.page = page

    @abstractmethod
    async def search(self, query):
        pass

    @abstractmethod
    async def get_visible_products(self):
        pass

    @abstractmethod
    async def click_product(self, product_element):
        pass

    @abstractmethod
    async def add_to_cart(self):
        pass

    @abstractmethod
    async def checkout(self):
        pass
