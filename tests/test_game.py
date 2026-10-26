import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
spec = importlib.util.spec_from_file_location('maze', Path(__file__).resolve().parents[1] / 'labirent v2.py')
maze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maze)

class GameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = os.getcwd()
        os.chdir(self.temp.name)
        self.game = maze.MatematikLabirentPro()
    def tearDown(self):
        maze.pygame.quit()
        os.chdir(self.old)
        self.temp.cleanup()
    def test_start_and_reachable_exit(self):
        self.assertEqual(self.game.state, 'MENU')
        for difficulty in ('BASIT', 'ORTA', 'ZOR'):
            self.game.difficulty = difficulty
            self.game.oyunu_sifirla()
            seen = {(1, 1)}
            pending = [(1, 1)]
            while pending:
                x, y = pending.pop()
                for dx, dy in ((0,1),(1,0),(0,-1),(-1,0)):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < self.game.boyut and 0 <= ny < self.game.boyut and self.game.labirent[ny][nx] != '#' and (nx,ny) not in seen:
                        seen.add((nx,ny)); pending.append((nx,ny))
            self.assertIn((self.game.boyut-2, self.game.boyut-2), seen)
    def test_win_saves_once_across_frames(self):
        self.game.oyunu_sifirla()
        self.game.state = 'WIN_SCREEN'
        self.game.puan = 100
        def button(label, *args):
            if label == 'ÇIKIŞ':
                button.frames += 1
                return button.frames >= 3
            return False
        button.frames = 0
        with patch.object(self.game, 'animasyonlu_buton', side_effect=button), patch.object(self.game, 'skor_kaydet', wraps=self.game.skor_kaydet) as save:
            self.game.run()
            self.assertEqual(save.call_count, 1)
        self.assertEqual(len(self.game.yuksek_skorlar), 1)
    def test_final_restart(self):
        self.game.oyunu_sifirla()
        self.game.state = 'LOSE_SCREEN'
        maze.pygame.event.post(maze.pygame.event.Event(maze.pygame.KEYDOWN, key=maze.pygame.K_r, unicode='r'))
        maze.pygame.event.post(maze.pygame.event.Event(maze.pygame.QUIT))
        self.game.run()
        self.assertEqual(self.game.state, 'PLAYING')

if __name__ == '__main__': unittest.main()
