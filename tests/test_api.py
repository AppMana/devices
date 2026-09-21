import unittest
from device_dimensions import find_device,get_table,pixels_per_inch,mm_to_native_pixels,mm_to_viewport_pixels
class PhysicalGeometry(unittest.TestCase):
    def test_physical_scale(self):
        self.assertAlmostEqual(mm_to_native_pixels('iPad16,5',199.14),2064)
        self.assertAlmostEqual(pixels_per_inch('iPad16,5')['x'],263.260018,places=5)
        self.assertEqual(mm_to_viewport_pixels('iPad16,5',265.19,1376,'landscape'),1376)
    def test_errors(self):
        with self.assertRaises(ValueError):pixels_per_inch('iphone-4')
        with self.assertRaises(ValueError):mm_to_native_pixels('iPad16,5',float('nan'))
    def test_data_isolation_and_identity(self):
        d=find_device('iPad16,5');d['display']['activeMm']['width']=1
        self.assertEqual(find_device('iPad16,5')['display']['activeMm']['width'],199.14)
        self.assertEqual(find_device('iPhone10,3')['display']['nativePixels']['width'],1125)
        self.assertEqual(find_device('iPhone11,8')['display']['nativePixels']['width'],828)
if __name__=='__main__':unittest.main()
