"""Phase 3 Group 2 exact curveball and regression tests."""
import unittest
from inventory import LibraryInventory
from models import Book

class Phase3Tests(unittest.TestCase):
    def setUp(self):
        self.inv = LibraryInventory()
        for id_, qty in [('B2',0),('A1',0),('B1',3),('Z1',1),('C1',8),('A2',1)]:
            self.inv.add_book(Book(id=id_, title=f'Guide {id_}', author='Author', category='Genre', year=2020, quantity=qty))

    def test_top_k_scarce_order_and_tie(self):
        self.assertEqual([b.id for b in self.inv.top_k_scarce(3)], ['A2','Z1','B1'])
        self.assertTrue(all(b.quantity > 0 for b in self.inv.top_k_scarce(100)))

    def test_zero_and_large_k(self):
        self.assertEqual(self.inv.top_k_scarce(0), [])
        self.assertEqual(len(self.inv.top_k_scarce(100)), 4)

    def test_invalid_k(self):
        for k in [-1, 1.1, '2', True, None]:
            with self.subTest(k=k), self.assertRaises(ValueError):
                self.inv.top_k_scarce(k)

    def test_read_only(self):
        before = dict(self.inv.books)
        stocks = (set(self.inv.in_stock), set(self.inv.out_of_stock))
        self.inv.top_k_scarce(3)
        self.assertEqual(self.inv.books, before)
        self.assertEqual((self.inv.in_stock, self.inv.out_of_stock), stocks)

    def test_updates_change_scarce_results(self):
        self.inv.update_quantity('B1', 0)
        self.assertEqual([b.id for b in self.inv.top_k_scarce(4)], ['A2','Z1','C1'])
        self.inv.update_quantity('A1', 1)
        self.assertEqual([b.id for b in self.inv.top_k_scarce(3)], ['A1','A2','Z1'])
        self.inv.remove_book('A2')
        self.assertEqual([b.id for b in self.inv.top_k_scarce(3)], ['A1','Z1','C1'])

    def test_empty_and_only_out_of_stock(self):
        fresh = LibraryInventory()
        self.assertEqual(fresh.top_k_scarce(10), [])
        fresh.add_book(Book(id='ZERO', title='Zero', author='A', category='C', year=2020, quantity=0))
        self.assertEqual(fresh.top_k_scarce(10), [])

    def test_trie_prefix_after_removal(self):
        self.assertEqual(len(self.inv.search_title('Guide')), 6)
        self.inv.remove_book('Z1')
        self.assertEqual(len(self.inv.search_title('Guide')), 5)

    def test_trie_result_independent_of_index(self):
        result = self.inv.title_trie.search_prefix('guide')
        result.clear()
        self.assertEqual(len(self.inv.search_title('guide')), 6)

if __name__ == '__main__':
    unittest.main()
