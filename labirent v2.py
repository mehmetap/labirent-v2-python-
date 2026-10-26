import pygame
import math
import random
import time
import json
import os

# --- Renkler ---
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (120, 120, 120)
GOLD = (255, 215, 0)
BLUE = (52, 152, 219)
RED = (231, 76, 60)
GREEN = (46, 204, 113)
PURPLE = (155, 89, 182)
CYAN = (26, 188, 156)
YELLOW = (255, 235, 59)

# --- Temalar ---
TEMALAR = {
    "BUZ DIYARI": {
        "wall": (200, 230, 255),
        "floor": (240, 250, 255),
        "player": (0, 100, 200),
        "target": (255, 255, 255)
    },
    "NEMRUT": {
        "wall": (139, 69, 19),
        "floor": (210, 180, 140),
        "player": (255, 255, 255),
        "target": (255, 140, 0)
    },
    "AHEP KAMPUS": {
        "wall": (255, 120, 0),
        "floor": (230, 230, 230),
        "player": (50, 50, 50),
        "target": (0, 150, 0)
    }
}

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
FPS = 60
TILE_SIZE = 50


class MatematikLabirentPro:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Alanya Lider Robotik - Matematik Labirenti Pro")
        self.clock = pygame.time.Clock()

        self.font_huge = pygame.font.Font(None, 90)
        self.font_large = pygame.font.Font(None, 60)
        self.font_main = pygame.font.Font(None, 42)
        self.font_sub = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 24)

        self.state = "MENU"
        self.difficulty = "ORTA"
        self.current_theme = "BUZ DIYARI"
        self.running = True

        self.hover_scale = {}
        self.clicked_last_frame = False

        self.skorlar_file = "skorlar.json"
        self.puan_siniri = 100

        self.feedback_text = ""
        self.feedback_time = 0

        self.player_name = "Mehmetcan"

        self.yukle_skorlar()

    # ---------------------------
    # KAYIT / SKOR
    # ---------------------------
    def yukle_skorlar(self):
        if os.path.exists(self.skorlar_file):
            try:
                with open(self.skorlar_file, "r", encoding="utf-8") as f:
                    self.yuksek_skorlar = json.load(f)
            except Exception:
                self.yuksek_skorlar = []
        else:
            self.yuksek_skorlar = []

    def skor_kaydet(self, isim, puan):
        self.yuksek_skorlar.append({"isim": isim, "puan": puan})
        self.yuksek_skorlar = sorted(
            self.yuksek_skorlar,
            key=lambda x: x["puan"],
            reverse=True
        )[:5]

        with open(self.skorlar_file, "w", encoding="utf-8") as f:
            json.dump(self.yuksek_skorlar, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # OYUN BAŞLATMA
    # ---------------------------
    def oyunu_sifirla(self):
        self.boyut = 15 if self.difficulty == "BASIT" else (21 if self.difficulty == "ORTA" else 25)
        self.labirent = self.labirent_olustur()

        self.oyuncu_x, self.oyuncu_y = 1, 1
        self.puan = 0
        self.skor_kaydedildi = False
        self.pas_gec_hakki = 3
        self.cift_puan_aktif = False
        self.camera_x, self.camera_y = 0, 0

        self.user_input = ""
        self.current_question = None
        self.soru_konumu = (0, 0)

        self.feedback_text = ""
        self.feedback_time = 0

        sureler = {
            "BASIT": 120,
            "ORTA": 90,
            "ZOR": 75
        }
        self.toplam_sure = sureler[self.difficulty]
        self.kalan_sure = self.toplam_sure
        self.baslangic_zamani = time.time()

    # ---------------------------
    # LABİRENT
    # ---------------------------
    def labirent_olustur(self):
        lab = [["#" for _ in range(self.boyut)] for _ in range(self.boyut)]

        def kaz(x, y):
            yonler = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(yonler)

            for dx, dy in yonler:
                nx, ny = x + dx, y + dy
                if 0 < nx < self.boyut - 1 and 0 < ny < self.boyut - 1 and lab[ny][nx] == "#":
                    lab[y + dy // 2][x + dx // 2] = " "
                    lab[ny][nx] = " "
                    kaz(nx, ny)

        lab[1][1] = " "
        kaz(1, 1)
        lab[self.boyut - 2][self.boyut - 2] = "X"

        for item in ["?", "?", "?", "?", "?", "P", "S"]:
            while True:
                rx = random.randint(1, self.boyut - 2)
                ry = random.randint(1, self.boyut - 2)
                if lab[ry][rx] == " " and (rx, ry) != (1, 1) and (rx, ry) != (self.boyut - 2, self.boyut - 2):
                    lab[ry][rx] = item
                    break

        return lab

    # ---------------------------
    # SORULAR
    # ---------------------------
    def soru_olustur(self):
        if self.difficulty == "BASIT":
            a, b = random.randint(1, 20), random.randint(1, 20)
            op = random.choice(["+", "-"])
            cevap = a + b if op == "+" else a - b
            return {"soru": f"{a} {op} {b} = ?", "cevap": cevap, "tip": "normal"}

        elif self.difficulty == "ORTA":
            a, b = random.randint(10, 50), random.randint(2, 12)
            return {"soru": f"{a} x {b} = ?", "cevap": a * b, "tip": "normal"}

        else:
            a, b, c, d = [random.randint(1, 9) for _ in range(4)]
            return {"soru": [a, b, c, d], "cevap": (a * d) - (b * c), "tip": "matris"}

    # ---------------------------
    # BUTON
    # ---------------------------
    def animasyonlu_buton(self, text, center_pos, color_theme=WHITE, size=(320, 65)):
        mx, my = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        rect = pygame.Rect(0, 0, size[0], size[1])
        rect.center = center_pos
        is_hover = rect.collidepoint(mx, my)

        scale = self.hover_scale.get(text, 1.0)
        if is_hover:
            scale = min(scale + 0.05, 1.08)
        else:
            scale = max(scale - 0.05, 1.0)
        self.hover_scale[text] = scale

        draw_color = GOLD if is_hover else color_theme

        surf = pygame.Surface((int(rect.width * scale), int(rect.height * scale)), pygame.SRCALPHA)
        pygame.draw.rect(surf, (40, 40, 40, 235), surf.get_rect(), border_radius=18)
        pygame.draw.rect(surf, draw_color, surf.get_rect(), 3, border_radius=18)

        txt_surf = self.font_sub.render(text, True, draw_color)
        txt_rect = txt_surf.get_rect(center=(surf.get_width() // 2, surf.get_height() // 2))
        surf.blit(txt_surf, txt_rect)

        self.screen.blit(surf, surf.get_rect(center=center_pos))

        tiklandi = is_hover and mouse_pressed and not self.clicked_last_frame
        return tiklandi

    # ---------------------------
    # ÇİZİM
    # ---------------------------
    def draw_background_gradient(self):
        for y in range(SCREEN_HEIGHT):
            color_value = 20 + int((y / SCREEN_HEIGHT) * 30)
            pygame.draw.line(self.screen, (color_value, color_value, color_value + 10), (0, y), (SCREEN_WIDTH, y))

    def draw_center_text(self, text, font, color, y):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
        self.screen.blit(surf, rect)

    def show_feedback(self):
        if self.feedback_text and time.time() - self.feedback_time < 1.5:
            txt = self.font_sub.render(self.feedback_text, True, YELLOW)
            rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
            self.screen.blit(txt, rect)

    # ---------------------------
    # OLAYLAR
    # ---------------------------
    def hareket_et(self, dx, dy):
        nx, ny = self.oyuncu_x + dx, self.oyuncu_y + dy

        if not (0 <= nx < self.boyut and 0 <= ny < self.boyut):
            return

        cell = self.labirent[ny][nx]

        if cell == "#":
            return
        elif cell == "?":
            self.current_question = self.soru_olustur()
            self.soru_konumu = (nx, ny)
            self.state = "QUESTION"
        else:
            self.oyuncu_x, self.oyuncu_y = nx, ny

            if cell == "P":
                self.pas_gec_hakki += 1
                self.labirent[ny][nx] = " "
                self.feedback_text = "+1 Pas Hakkı Kazandın!"
                self.feedback_time = time.time()

            elif cell == "S":
                self.cift_puan_aktif = True
                self.labirent[ny][nx] = " "
                self.feedback_text = "Çift Puan Aktif!"
                self.feedback_time = time.time()

            elif cell == "X":
                self.state = "WIN_SCREEN"

    def soru_cevapla(self):
        try:
            val = int(self.user_input)
            if val == self.current_question["cevap"]:
                katsayi = 2 if self.cift_puan_aktif else 1
                ek_puan = 40 if self.difficulty == "ZOR" else 20
                self.puan += ek_puan * katsayi

                qx, qy = self.soru_konumu
                self.labirent[qy][qx] = " "
                self.feedback_text = "Doğru Cevap!"
                self.feedback_time = time.time()
            else:
                self.puan = max(0, self.puan - 15)
                self.feedback_text = "Yanlış Cevap! -15 Puan"
                self.feedback_time = time.time()

            self.state = "PLAYING"
            self.user_input = ""
            self.cift_puan_aktif = False

        except ValueError:
            self.user_input = ""

    # ---------------------------
    # ANA DÖNGÜ
    # ---------------------------
    def run(self):
        while self.running:
            self.draw_background_gradient()
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    # Genel kısayol
                    if event.key == pygame.K_r and self.state in ["PLAYING", "QUESTION", "PAUSE", "WIN_SCREEN", "LOSE_SCREEN"]:
                        self.oyunu_sifirla()
                        self.state = "PLAYING"

                    # ESC ile duraklat/devam
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "PLAYING":
                            self.state = "PAUSE"
                            self.duraklatma_baslangic = time.time()
                        elif self.state == "PAUSE":
                            self.state = "PLAYING"
                            self.baslangic_zamani += (time.time() - self.duraklatma_baslangic)

                # Soru ekranı
                if self.state == "QUESTION" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.user_input:
                        self.soru_cevapla()

                    elif event.key == pygame.K_BACKSPACE:
                        self.user_input = self.user_input[:-1]

                    elif event.unicode.isdigit() or (event.unicode == "-" and not self.user_input):
                        self.user_input += event.unicode

                # Oyun ekranı
                if self.state == "PLAYING" and event.type == pygame.KEYDOWN:
                    dx, dy = 0, 0

                    if event.key in [pygame.K_UP, pygame.K_w]:
                        dy = -1
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        dy = 1
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        dx = -1
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        dx = 1

                    if dx != 0 or dy != 0:
                        self.hareket_et(dx, dy)

            # ---------------------------
            # EKRANLAR
            # ---------------------------
            if self.state == "MENU":
                self.draw_center_text("MATEMATİK LABİRENTİ v2", self.font_large, BLUE, 120)
                self.draw_center_text("Akıllı labirent, soru çöz, hedefe ulaş!", self.font_sub, GRAY, 170)

                if self.animasyonlu_buton("OYUNA BAŞLA", (500, 300), WHITE):
                    self.state = "DIFF_SELECT"
                if self.animasyonlu_buton("SKORLAR", (500, 400), WHITE):
                    self.state = "LEADERBOARD"
                if self.animasyonlu_buton("ÇIKIŞ", (500, 500), RED):
                    self.running = False

            elif self.state == "DIFF_SELECT":
                self.draw_center_text("Zorluk Seç", self.font_large, GOLD, 130)

                if self.animasyonlu_buton("BASİT", (500, 260), GREEN):
                    self.difficulty = "BASIT"
                    self.state = "THEME_SELECT"

                if self.animasyonlu_buton("ORTA", (500, 360), GOLD):
                    self.difficulty = "ORTA"
                    self.state = "THEME_SELECT"

                if self.animasyonlu_buton("ZOR", (500, 460), RED):
                    self.difficulty = "ZOR"
                    self.state = "THEME_SELECT"

                if self.animasyonlu_buton("GERİ", (500, 610), CYAN, (200, 50)):
                    self.state = "MENU"

            elif self.state == "THEME_SELECT":
                self.draw_center_text("Tema Seç", self.font_large, CYAN, 130)

                y = 260
                for t in TEMALAR.keys():
                    if self.animasyonlu_buton(t, (500, y), WHITE):
                        self.current_theme = t
                        self.oyunu_sifirla()
                        self.state = "PLAYING"
                    y += 100

                if self.animasyonlu_buton("GERİ", (500, 620), CYAN, (200, 50)):
                    self.state = "DIFF_SELECT"

            elif self.state == "PLAYING" or self.state == "QUESTION":
                self.kalan_sure = max(0, self.toplam_sure - (time.time() - self.baslangic_zamani))
                if self.kalan_sure <= 0:
                    self.state = "LOSE_SCREEN"

                tema = TEMALAR[self.current_theme]

                tx = (SCREEN_WIDTH // 2) - (self.oyuncu_x * TILE_SIZE)
                ty = (SCREEN_HEIGHT // 2) - (self.oyuncu_y * TILE_SIZE)
                self.camera_x += (tx - self.camera_x) * 0.1
                self.camera_y += (ty - self.camera_y) * 0.1

                for y in range(self.boyut):
                    for x in range(self.boyut):
                        px = x * TILE_SIZE + self.camera_x
                        py = y * TILE_SIZE + self.camera_y
                        c = self.labirent[y][x]

                        if c == "#":
                            pygame.draw.rect(self.screen, tema["wall"], (px, py, TILE_SIZE - 2, TILE_SIZE - 2), border_radius=8)
                        else:
                            pygame.draw.rect(self.screen, tema["floor"], (px, py, TILE_SIZE, TILE_SIZE))

                            if c == "X":
                                pygame.draw.rect(self.screen, tema["target"], (px + 10, py + 10, 30, 30), border_radius=6)
                            elif c == "?":
                                pygame.draw.circle(self.screen, GOLD, (int(px + 25), int(py + 25)), 14)
                            elif c == "P":
                                pygame.draw.circle(self.screen, GREEN, (int(px + 25), int(py + 25)), 10)
                            elif c == "S":
                                pygame.draw.circle(self.screen, PURPLE, (int(px + 25), int(py + 25)), 10)

                pygame.draw.circle(
                    self.screen,
                    tema["player"],
                    (int(self.oyuncu_x * TILE_SIZE + self.camera_x + 25),
                     int(self.oyuncu_y * TILE_SIZE + self.camera_y + 25)),
                    18
                )

                # HUD
                pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, SCREEN_WIDTH, 70))
                pygame.draw.line(self.screen, GOLD, (0, 70), (SCREEN_WIDTH, 70), 2)

                hud_text = (
                    f"SÜRE: {int(self.kalan_sure)} sn   |   "
                    f"PUAN: {self.puan}   |   "
                    f"PAS: {self.pas_gec_hakki}   |   "
                    f"TEMA: {self.current_theme}"
                )
                self.screen.blit(self.font_sub.render(hud_text, True, WHITE), (20, 18))

                if self.cift_puan_aktif:
                    self.screen.blit(self.font_small.render("BONUS: ÇİFT PUAN AKTİF", True, PURPLE), (20, 45))

                self.show_feedback()

                if self.state == "QUESTION":
                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 200))
                    self.screen.blit(overlay, (0, 0))

                    pygame.draw.rect(self.screen, WHITE, (250, 150, 500, 400), border_radius=20)
                    pygame.draw.rect(self.screen, BLUE, (250, 150, 500, 400), 3, border_radius=20)

                    self.draw_center_text("SORUYU ÇÖZ", self.font_large, BLACK, 190)

                    if self.current_question["tip"] == "normal":
                        q_txt = self.font_main.render(self.current_question["soru"], True, BLACK)
                        self.screen.blit(q_txt, q_txt.get_rect(center=(500, 270)))
                    else:
                        m = self.current_question["soru"]
                        self.draw_center_text(f"| {m[0]}   {m[1]} |", self.font_main, BLACK, 245)
                        self.draw_center_text(f"| {m[2]}   {m[3]} |", self.font_main, BLACK, 295)
                        self.draw_center_text("Determinantı hesapla", self.font_sub, GRAY, 345)

                    input_text = self.user_input + "_"
                    self.draw_center_text(input_text, self.font_large, BLUE, 430)

                    self.draw_center_text("Enter ile gönder", self.font_small, GRAY, 470)

                    if self.animasyonlu_buton("PAS KULLAN", (500, 530), CYAN, (220, 48)):
                        if self.pas_gec_hakki > 0:
                            self.pas_gec_hakki -= 1
                            qx, qy = self.soru_konumu
                            self.labirent[qy][qx] = " "
                            self.user_input = ""
                            self.state = "PLAYING"
                            self.feedback_text = "Soru pas geçildi."
                            self.feedback_time = time.time()
                        else:
                            self.feedback_text = "Pas hakkın kalmadı!"
                            self.feedback_time = time.time()

            elif self.state == "PAUSE":
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 185))
                self.screen.blit(overlay, (0, 0))

                self.draw_center_text("DURAKLATILDI", self.font_huge, WHITE, 220)

                if self.animasyonlu_buton("DEVAM ET", (500, 390), GREEN):
                    self.state = "PLAYING"
                    self.baslangic_zamani += (time.time() - self.duraklatma_baslangic)

                if self.animasyonlu_buton("ANA MENÜ", (500, 490), CYAN):
                    self.state = "MENU"

            elif self.state in ["WIN_SCREEN", "LOSE_SCREEN"]:
                self.screen.fill(BLACK)

                if self.state == "WIN_SCREEN":
                    if self.puan >= self.puan_siniri:
                        txt = "TEBRİKLER! KAZANDIN"
                        clr = GREEN
                        if not self.skor_kaydedildi:
                            self.skor_kaydet(self.player_name, self.puan)
                            self.skor_kaydedildi = True
                    else:
                        txt = "HEDEFE ULAŞTIN AMA PUAN YETERSİZ"
                        clr = RED
                else:
                    txt = "ZAMAN BİTTİ!"
                    clr = RED

                self.draw_center_text(txt, self.font_large, clr, 200)
                self.draw_center_text(f"Final Skorun: {self.puan}", self.font_main, WHITE, 300)
                self.draw_center_text(f"Gerekli Minimum Puan: {self.puan_siniri}", self.font_sub, GRAY, 350)
                self.draw_center_text("R ile yeniden başlatabilirsin", self.font_small, GOLD, 390)

                if self.animasyonlu_buton("ANA MENÜ", (500, 480), CYAN):
                    self.state = "MENU"

                if self.animasyonlu_buton("ÇIKIŞ", (500, 570), RED):
                    self.running = False

            elif self.state == "LEADERBOARD":
                self.draw_center_text("TOP 5 SKOR", self.font_large, GOLD, 110)

                if not self.yuksek_skorlar:
                    self.draw_center_text("Henüz kayıtlı skor yok.", self.font_main, WHITE, 260)
                else:
                    for i, s in enumerate(self.yuksek_skorlar):
                        satir = f"{i + 1}. {s['isim']} - {s['puan']}"
                        self.draw_center_text(satir, self.font_main, WHITE, 220 + i * 65)

                if self.animasyonlu_buton("GERİ", (500, 630), CYAN, (200, 50)):
                    self.state = "MENU"

            pygame.display.flip()
            self.clicked_last_frame = pygame.mouse.get_pressed()[0]
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    MatematikLabirentPro().run()
