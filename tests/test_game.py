import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

GAME = runpy.run_path(str(Path(__file__).resolve().parents[1] / "labirent v2.py"))

class GameTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.game = GAME["MatematikLabirentPro"]()
        self.game.skorlar_file = str(Path(self.folder.name) / "skorlar.json")
        self.game.oyunu_sifirla()
        self.game.state = "PLAYING"

    def tearDown(self):
        GAME["pygame"].quit()
        self.folder.cleanup()

    def question(self):
        self.game.soruyu_ac(*next(iter(self.game._soru_hucreleri)))

    def test_maze_generation(self):
        for difficulty in GAME["BOYUTLAR"]:
            self.game.ana_menuye_don()
            self.game.zorluk_ayarla(difficulty)
            for _ in range(100):
                self.game.oyunu_sifirla()
                self.assertTrue(self.game.labirent_dogrula(self.game.labirent))

    def test_expired_solver(self):
        self.question()
        self.game.cift_puan_etkinlestir()
        self.game._bitis_zamani = 0
        self.assertIsNone(self.game._soruyu_coz(self.game.soru_konumu))
        self.assertEqual(self.game.puan, 0)
        self.assertTrue(self.game.cift_puan_aktif)

    def test_bad_question_render(self):
        for bad in [None, {}, {"cevap": 1}, {"cevap": 1, "tip": "matris", "soru": []}]:
            self.question()
            self.game.current_question = bad
            self.game.ekrani_ciz()
            self.assertEqual(self.game.state, "PLAYING")
            self.assertEqual(self.game.puan, 0)

    def test_wrong_then_correct(self):
        self.question()
        self.game.cift_puan_etkinlestir()
        self.game.user_input = str(self.game.current_question["cevap"] + 1)
        self.game.soru_cevapla()
        self.assertEqual(self.game.state, "QUESTION")
        self.assertTrue(self.game.cift_puan_aktif)
        self.game.user_input = str(self.game.current_question["cevap"])
        self.game.soru_cevapla()
        self.assertEqual(self.game.puan, 40)
        self.assertEqual(self.game.cozulen_soru, 1)

    def test_stale_click(self):
        pg = GAME["pygame"]
        self.game.olay_isle(pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=(500,490)))
        self.game.olay_isle(pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE, unicode=""))
        self.game.ekrani_ciz()
        self.assertEqual(self.game.state, "PAUSE")

    def test_save_failure(self):
        before = self.game.yuksek_skorlar
        with patch.object(GAME["os"], "replace", side_effect=OSError("test")):
            self.assertFalse(self.game.skor_kaydet("Test", 100))
        self.assertEqual(self.game.yuksek_skorlar, before)

    def test_each_result_saved_once(self):
        for outcome in ("win", "low", "timeout"):
            self.game.oyunu_sifirla()
            self.game.state = "PLAYING"
            self.game.puan_ekle(100 if outcome == "win" else 20)
            with patch.object(self.game, "skor_kaydet", wraps=self.game.skor_kaydet) as save:
                if outcome == "timeout":
                    self.game._bitis_zamani = 0
                    self.game.sure_kontrol()
                else:
                    self.game._final_ac()
                for _ in range(3):
                    self.game.ekrani_ciz()
                self.assertEqual(save.call_count, 1)

if __name__ == "__main__":
    unittest.main()
