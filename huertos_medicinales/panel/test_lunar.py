from datetime import date
from django.test import SimpleTestCase
from .lunar import events, phase_on, month_phases

class LunarTests(SimpleTestCase):
    def test_ecuador_date_rollover(self):
        self.assertEqual(phase_on(date(2026,4,1))['name'], 'Luna llena')
        self.assertEqual(phase_on(date(2026,4,1))['time'], '21:12')
        self.assertEqual(phase_on(date(2026,1,25))['name'], 'Cuarto creciente')
        self.assertFalse(phase_on(date(2026,4,2))['primary'])
    def test_full_moon_and_tradition(self):
        self.assertTrue(phase_on(date(2026,11,18))['sow'])
        self.assertFalse(phase_on(date(2026,11,24))['sow'])
        self.assertEqual(phase_on(date(2026,11,24))['time'], '09:53')
    def test_month_and_coverage(self):
        self.assertEqual(len(month_phases(date(2026,11,1))), 4)
        self.assertEqual(len(month_phases(date(2026,5,1))), 5)
        self.assertIsNone(phase_on(date(2031,1,1)))
        self.assertIsNone(phase_on(date(2025,1,1)))
        self.assertEqual(len(events()),297)
