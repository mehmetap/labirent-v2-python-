import math
import json
import os
import random
import time
from collections import deque

import pygame

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

# --- Zorluk ayarları (tek kaynak) ---
BOYUTLAR = {"BASIT": 15, "ORTA": 21, "ZOR": 25}
SURELER = {"BASIT": 120, "ORTA": 90, "ZOR": 75}

VERSION = "2.1.0"

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
FPS = 60
TILE_SIZE = 50

BASLANGIC_PAS = 3
MAX_CEVAP_UZUNLUGU = 6
MAX_ISIM_UZUNLUGU = 16
MAX_URETIM_DENEME = 30
YANLIS_CEZA = 15
BILDIRIM_SURESI = 2.0
VARSAYILAN_ISIM = "Oyuncu"
BELIRTILMEMIS = "Belirtilmemiş"
SKOR_GRUPLARI = tuple(BOYUTLAR) + (BELIRTILMEMIS,)
GRUP_ETIKETLERI = {"BASIT": "BASİT", "ORTA": "ORTA", "ZOR": "ZOR", BELIRTILMEMIS: "BELİRTİLMEMİŞ"}
GRUP_KAYIT_SAYISI = 5
ISIM_KUTU_GENISLIGI = 480
ISIM_IC_BOSLUK = 20
MAX_BONUS_DENEME = 25
MAX_SAPMA = 4  # P/T bonusları zorunlu yola en fazla bu kadar hücre uzaklıkta olur
YENIDEN_BASLATMA_DURUMLARI = ("PLAYING", "QUESTION", "PAUSE", "WIN_SCREEN", "LOSE_SCREEN")


class MatematikLabirentPro:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"Alanya Lider Robotik - Matematik Labirenti Pro {VERSION}")
        self.clock = pygame.time.Clock()

        # Türkçe karakter destekleyen font; bulunamazsa pygame varsayılanı.
        self._font_yolu = pygame.font.match_font(
            "segoeui,arial,dejavusans,liberationsans,freesans,verdana,calibri")
        self.font_huge = self._font_yukle(90)
        self.font_large = self._font_yukle(60)
        self.font_main = self._font_yukle(42)
        self.font_sub = self._font_yukle(30)
        self.font_small = self._font_yukle(24)
        self.font_tiny = self._font_yukle(19)
        self._harf_onbellek = {}

        # Değişmeyen gradyan arka plan bir kez oluşturulur.
        self._arka_plan = self._arka_plan_olustur()

        self._state = "MENU"
        self._ekran_no = 0   # her ekran değişiminde artar (bkz. state setter)
        self.running = True

        # NOT: Python'da "_alan" yalnızca "iç kullanım" niyetini belirtir;
        # erişimi teknik olarak engellemez. Bu yüzden yalnızca verisi
        # doğrulama gerektiren alanlar "_" ile saklanır.
        self._zorluk = "ORTA"
        self._tema = "BUZ DIYARI"
        self._oyun_devam = False

        self.hover_scale = {}
        self._tik = None  # (konum, ekran_no): bu karedeki fare tıklaması ve ait olduğu ekran

        # Skor dosyası çalışma klasöründen bağımsız: kodun yanında.
        self.skorlar_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "skorlar.json")
        self._yuksek_skorlar = []

        self.feedback_text = ""
        self.feedback_time = 0.0

        self.player_name = VARSAYILAN_ISIM
        self._isim_giris = VARSAYILAN_ISIM
        self._isim_uyari = ""
        self._skor_zorluk = "ORTA"

        # Oyun alanları (oyunu_sifirla() bunları yeniden kurar)
        self.boyut = BOYUTLAR[self._zorluk]
        self.toplam_soru = 5
        self.labirent = []
        self._puan = 0
        self._pas_gec_hakki = BASLANGIC_PAS
        self._cozulen_soru = 0
        self._cozulen_hucreler = set()
        self._soru_hucreleri = frozenset()
        self._cift_puan_aktif = False
        self._sorular = {}
        self._sure_bonuslari = {}
        self.toplam_sure = SURELER[self._zorluk]
        self._bitis_zamani = 0.0
        self._duraklatma_baslangic = None
        self._duraklatma_oncesi_durum = None
        self.oyuncu_x, self.oyuncu_y = 1, 1
        self.camera_x, self.camera_y = 0, 0
        self.user_input = ""
        self.current_question = None
        self.soru_konumu = (0, 0)
        self.puan_siniri = 100
        self.skor_kaydedildi = False
        self._kazandi = False
        self._skor_mesaji = ""
        self._skor_basarili = False

        self.yukle_skorlar()

    # ---------------------------
    # FONT / ARKA PLAN
    # ---------------------------
    def _font_yukle(self, boyut):
        if self._font_yolu:
            return pygame.font.Font(self._font_yolu, int(boyut * 0.8))
        return pygame.font.Font(None, boyut)

    @staticmethod
    def _arka_plan_olustur():
        yuzey = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            v = 20 + int((y / SCREEN_HEIGHT) * 30)
            pygame.draw.line(yuzey, (v, v, v + 10), (0, y), (SCREEN_WIDTH, y))
        return yuzey

    # ---------------------------
    # KAPSÜLLENMİŞ ÖZELLİKLER (salt okunur erişim)
    # ---------------------------
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, yeni):
        # Ekran değişince sayaç artar; eski ekrana ait bekleyen tıklama geçersiz olur.
        if yeni != self._state:
            self._state = yeni
            self._ekran_no += 1

    @property
    def difficulty(self):
        return self._zorluk

    @property
    def current_theme(self):
        return self._tema

    @property
    def puan(self):
        return self._puan

    @property
    def pas_gec_hakki(self):
        return self._pas_gec_hakki

    @property
    def cozulen_soru(self):
        return self._cozulen_soru

    @property
    def tum_sorular_cozuldu(self):
        return self._cozulen_soru >= self.toplam_soru

    @property
    def cift_puan_aktif(self):
        return self._cift_puan_aktif

    @property
    def kalan_sure(self):
        """Kalan süre için tek kaynak. Duraklatmada saat 'dondurulur'."""
        simdi = (self._duraklatma_baslangic
                 if self._duraklatma_baslangic is not None else time.monotonic())
        return max(0.0, self._bitis_zamani - simdi)

    @property
    def yuksek_skorlar(self):
        """Dışarıya liste ve içindeki sözlüklerin kopyası verilir."""
        return [dict(k) for k in self._yuksek_skorlar]

    # ---------------------------
    # DOĞRULAMALI DEĞİŞTİRİCİ METOTLAR
    # ---------------------------
    @staticmethod
    def _miktar_dogrula(miktar):
        if isinstance(miktar, bool) or not isinstance(miktar, int):
            raise TypeError("Miktar tam sayı olmalıdır.")
        if miktar < 0:
            raise ValueError("Miktar negatif olamaz.")
        return miktar

    def puan_ekle(self, miktar):
        self._puan += self._miktar_dogrula(miktar)

    def puan_dusur(self, miktar):
        """Puanı düşürür; 0'ın altına inmez. Gerçekten düşen miktarı döndürür."""
        miktar = self._miktar_dogrula(miktar)
        dusen = min(miktar, self._puan)
        self._puan -= dusen
        return dusen

    def puan_sifirla(self):
        self._puan = 0

    def pas_ekle(self, miktar=1):
        self._pas_gec_hakki += self._miktar_dogrula(miktar)

    def pas_kullan(self):
        if self._pas_gec_hakki <= 0:
            return False
        self._pas_gec_hakki -= 1
        return True

    def _cozulen_say(self, konum):
        """Yalnızca daha önce çözülmemiş gerçek bir soru hücresi için sayacı artırır."""
        if konum not in self._soru_hucreleri or konum in self._cozulen_hucreler:
            return False
        self._cozulen_hucreler.add(konum)
        self._cozulen_soru = len(self._cozulen_hucreler)
        return True

    def zorluk_ayarla(self, zorluk):
        if zorluk not in BOYUTLAR:
            raise ValueError(f"Geçersiz zorluk: {zorluk!r}. Geçerli: {list(BOYUTLAR)}")
        if self._oyun_devam:
            raise RuntimeError("Devam eden oyunun zorluğu değiştirilemez.")
        self._zorluk = zorluk

    def tema_ayarla(self, tema):
        if tema not in TEMALAR:
            raise ValueError(f"Geçersiz tema: {tema!r}. Geçerli: {list(TEMALAR)}")
        self._tema = tema

    def sure_ekle(self, saniye):
        """Devam eden ve süresi dolmamış oyuna süre ekler; eklenirse True döner.
        Geçersiz değer programlama hatasıdır (TypeError/ValueError).
        Kural: PLAYING, QUESTION ve PAUSE'da izin var; PAUSE'da kalan süre donmuş
        saate göre hesaplandığı için ekleme tutarlıdır. Menü, sonuç ekranı ve
        süresi dolmuş oyunda False döner (kaybedilmiş oyun canlandırılamaz)."""
        self._miktar_dogrula(saniye)
        if (not self._oyun_devam
                or self.state not in ("PLAYING", "QUESTION", "PAUSE")
                or self.kalan_sure <= 0):
            return False
        self._bitis_zamani += saniye
        return True

    def cift_puan_etkinlestir(self):
        self._cift_puan_aktif = True

    def cift_puan_tuket(self):
        """Çarpanı döndürür ve bonusu kapatır. Tüketim yalnızca burada olur."""
        katsayi = 2 if self._cift_puan_aktif else 1
        self._cift_puan_aktif = False
        return katsayi

    def oyuncu_adi_ayarla(self, isim):
        isim = str(isim).strip()[:MAX_ISIM_UZUNLUGU].strip()
        self.player_name = isim if isim else VARSAYILAN_ISIM

    def bildirim(self, metin):
        self.feedback_text = metin
        self.feedback_time = time.monotonic()

    # ---------------------------
    # KAYIT / SKOR
    # ---------------------------
    @staticmethod
    def _kayit_dogrula(isim, puan, zorluk, yukleme=False):
        """Skor doğrulaması için tek nokta. Programlama hatalarında TypeError/ValueError.
        yukleme=True: dosyadaki eksik/geçersiz zorluk 'Belirtilmemiş' olur (tahmin edilmez)."""
        if not isinstance(isim, str):
            raise TypeError("İsim metin olmalıdır.")
        if isinstance(puan, bool) or not isinstance(puan, int):
            raise TypeError("Puan tam sayı olmalıdır.")
        if puan < 0:
            raise ValueError("Puan negatif olamaz.")
        if not (isinstance(zorluk, str) and zorluk in BOYUTLAR):
            if not yukleme:
                raise ValueError(f"Geçersiz zorluk: {zorluk!r}")
            zorluk = BELIRTILMEMIS
        isim = isim.strip()[:MAX_ISIM_UZUNLUGU].strip() or VARSAYILAN_ISIM
        return {"isim": isim, "puan": puan, "zorluk": zorluk}

    @staticmethod
    def _gruplari_sinirla(kayitlar):
        """Her zorluk grubu için ayrı ilk GRUP_KAYIT_SAYISI kaydı tutar."""
        sonuc = []
        for grup in SKOR_GRUPLARI:
            uyeler = sorted((k for k in kayitlar if k["zorluk"] == grup),
                            key=lambda k: k["puan"], reverse=True)
            sonuc.extend(uyeler[:GRUP_KAYIT_SAYISI])
        return sonuc

    def yukle_skorlar(self):
        self._yuksek_skorlar = []
        if not os.path.exists(self.skorlar_file):
            return
        try:
            with open(self.skorlar_file, "r", encoding="utf-8") as f:
                veri = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(veri, list):
            return
        kayitlar = []
        for k in veri:
            if not isinstance(k, dict):
                continue
            try:
                kayitlar.append(self._kayit_dogrula(
                    k.get("isim"), k.get("puan"), k.get("zorluk"), yukleme=True))
            except (TypeError, ValueError):
                continue  # geçersiz kayıt atlanır
        self._yuksek_skorlar = self._gruplari_sinirla(kayitlar)

    @staticmethod
    def _gecici_dosyayi_sil(yol):
        try:
            os.remove(yol)
        except OSError:
            pass  # temizlik hatası asıl hatayı gölgelemez

    def _skorlari_yaz(self, kayitlar):
        """Verilen (zaten doğrulanmış) listeyi atomik yazar. Yalnızca dosya hatası → False."""
        gecici = self.skorlar_file + ".tmp"
        try:
            with open(gecici, "w", encoding="utf-8") as f:
                json.dump(kayitlar, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(gecici, self.skorlar_file)
            return True
        except OSError:
            self._gecici_dosyayi_sil(gecici)
            return False

    def skor_kaydet(self, isim, puan, zorluk=None):
        """Geçersiz girdi → TypeError/ValueError (hiçbir şey değişmez).
        Dosya hatası → False (bellek ve önceki dosya aynen kalır). Başarı → True."""
        kayit = self._kayit_dogrula(isim, puan, self._zorluk if zorluk is None else zorluk)
        aday = self._gruplari_sinirla([dict(k) for k in self._yuksek_skorlar] + [kayit])
        if not self._skorlari_yaz(aday):
            return False
        self._yuksek_skorlar = aday  # yalnızca yazma başarılıysa
        return True

    def skorlari_getir(self, zorluk):
        """Bir zorluk grubunun skorlarının (sıralı) kopyasını verir."""
        if zorluk not in SKOR_GRUPLARI:
            raise ValueError(f"Geçersiz skor grubu: {zorluk!r}")
        return sorted((dict(k) for k in self._yuksek_skorlar if k["zorluk"] == zorluk),
                      key=lambda k: k["puan"], reverse=True)

    # ---------------------------
    # OYUN BAŞLATMA
    # ---------------------------
    def oyunu_sifirla(self):
        self._oyun_devam = True
        self.boyut = BOYUTLAR[self._zorluk]
        self.toplam_soru = 5
        self._sorular = {}          # önceki haritanın soruları silinir
        self._sure_bonuslari = {}
        self.labirent = self.labirent_olustur()
        self._soru_hucreleri = frozenset(
            (x, y) for y, satir in enumerate(self.labirent)
            for x, c in enumerate(satir) if c == "?")
        self._cozulen_soru = 0
        self._cozulen_hucreler = set()
        self.skor_kaydedildi = False
        self._kazandi = False
        self._skor_mesaji = ""
        self._skor_basarili = False

        self.oyuncu_x, self.oyuncu_y = 1, 1
        self.puan_sifirla()
        self._pas_gec_hakki = BASLANGIC_PAS
        self._cift_puan_aktif = False
        self.camera_x, self.camera_y = 0, 0

        self.user_input = ""
        self.current_question = None
        self.soru_konumu = (0, 0)

        self.feedback_text = ""
        self.feedback_time = 0.0

        self._duraklatma_baslangic = None
        self._duraklatma_oncesi_durum = None

        self.toplam_sure = SURELER[self._zorluk]
        self.puan_siniri = 200 if self._zorluk == "ZOR" else 100
        self._bitis_zamani = time.monotonic() + self.toplam_sure

    def yeniden_baslat(self):
        self.oyunu_sifirla()
        self.state = "PLAYING"

    def ana_menuye_don(self):
        self._oyun_devam = False
        self._duraklatma_baslangic = None
        self._duraklatma_oncesi_durum = None
        self.state = "MENU"

    # ---------------------------
    # LABİRENT
    # ---------------------------
    def hedef_yolu(self, lab):
        """Başlangıçtan finale ulaşan yolu bul; yol üzerindeki sorular atlanamaz."""
        baslangic = (1, 1)
        hedef = (self.boyut - 2, self.boyut - 2)
        kuyruk = deque([baslangic])
        onceki = {baslangic: None}
        while kuyruk:
            x, y = kuyruk.popleft()
            if (x, y) == hedef:
                yol = []
                nokta = (x, y)
                while nokta is not None:
                    yol.append(nokta)
                    nokta = onceki[nokta]
                return yol[::-1]
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nokta = (x + dx, y + dy)
                nx, ny = nokta
                if (0 <= nx < self.boyut and 0 <= ny < self.boyut
                        and lab[ny][nx] != "#" and nokta not in onceki):
                    onceki[nokta] = (x, y)
                    kuyruk.append(nokta)
        return []


    def _erisim_kumesi(self, lab, engel=frozenset()):
        """Başlangıçtan ulaşılabilen hücreler; duvarlar ve 'engel' kümesi geçilemez.
        Labirenti değiştirmez."""
        baslangic = (1, 1)
        if baslangic in engel or lab[1][1] == "#":
            return set()
        gorulen = {baslangic}
        kuyruk = deque([baslangic])
        while kuyruk:
            x, y = kuyruk.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                n = (x + dx, y + dy)
                if (0 <= n[0] < self.boyut and 0 <= n[1] < self.boyut
                        and lab[n[1]][n[0]] != "#" and n not in engel and n not in gorulen):
                    gorulen.add(n)
                    kuyruk.append(n)
        return gorulen

    def _yol_uzakliklari(self, lab, yol):
        """{hücre: (zorunlu yola uzaklık, en yakın yol hücresinin sırası)}"""
        bilgi = {h: (0, i) for i, h in enumerate(yol)}
        kuyruk = deque(yol)
        while kuyruk:
            x, y = kuyruk.popleft()
            d, i = bilgi[(x, y)]
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                n = (x + dx, y + dy)
                if (0 <= n[0] < self.boyut and 0 <= n[1] < self.boyut
                        and lab[n[1]][n[0]] != "#" and n not in bilgi):
                    bilgi[n] = (d + 1, i)
                    kuyruk.append(n)
        return bilgi

    def _bonus_yerlestir(self, lab, yol):
        """Bonus konumlarını [(harf, (x, y)), ...] olarak seçer; labirenti DEĞİŞTİRMEZ.
        S: tüm sorular engelliyken bile ulaşılabilen bölgeden (ilk sorudan önce),
        mümkünse yol dışı kısa bir sapmada.
        P ve T: yola en fazla MAX_SAPMA uzaklıkta, yolun üç diliminin her birinden biri;
        en az biri yolun dışında. Olmazsa None."""
        sorular = {(x, y) for y in range(self.boyut) for x in range(self.boyut)
                   if lab[y][x] == "?"}

        def bos(h):
            return lab[h[1]][h[0]] == " " and h != (1, 1)

        ilk_bolge = [h for h in self._erisim_kumesi(lab, engel=sorular) if bos(h)]
        if not ilk_bolge:
            return None
        bilgi = self._yol_uzakliklari(lab, yol)
        # Keşif hissi için S, ilk bölgede yol dışı (yakın) bir hücre varsa oradan seçilir.
        s_adaylari = [h for h in ilk_bolge if 1 <= bilgi[h][0] <= MAX_SAPMA] or ilk_bolge
        dilimler = {0: [], 1: [], 2: []}
        for h, (d, i) in bilgi.items():
            if d <= MAX_SAPMA and bos(h):
                dilimler[min(2, i * 3 // len(yol))].append(h)
        if any(not v for v in dilimler.values()):
            return None
        for _ in range(MAX_BONUS_DENEME):
            s_konum = random.choice(s_adaylari)
            sira = random.sample([0, 1, 2], 3)
            secilen = []
            for harf, dilim in zip(("P", "T", "T"), sira):
                adaylar = [h for h in dilimler[dilim]
                           if h != s_konum and h not in [k for _, k in secilen]]
                if not adaylar:
                    break
                secilen.append((harf, random.choice(adaylar)))
            if len(secilen) == 3 and any(bilgi[k][0] >= 1 for _, k in secilen):
                return [("S", s_konum)] + secilen
        return None

    def labirent_dogrula(self, lab):
        """Salt okunur doğrulama; labirenti ve bonus verilerini değiştirmez."""
        b = self.boyut
        son = (b - 2, b - 2)
        if lab[1][1] != " " or lab[son[1]][son[0]] != "X":
            return False
        yol = self.hedef_yolu(lab)
        if not yol or yol[0] != (1, 1) or yol[-1] != son:
            return False
        hucreler = [(x, y) for y in range(b) for x in range(b)]
        sorular = {(x, y) for x, y in hucreler if lab[y][x] == "?"}
        if len(sorular) != self.toplam_soru or (1, 1) in sorular or son in sorular:
            return False
        # Her soru zorunlu olmalı: tek başına engellenince final erişilemez olmalı.
        for soru in sorular:
            if son in self._erisim_kumesi(lab, engel={soru}):
                return False
        sayim = {"P": 0, "S": 0, "T": 0}
        for x, y in hucreler:
            if lab[y][x] in sayim:
                sayim[lab[y][x]] += 1
        if sayim != {"P": 1, "S": 1, "T": 2}:
            return False
        if {(x, y) for x, y in hucreler if lab[y][x] == "T"} != set(self._sure_bonuslari):
            return False
        s_konum = next((x, y) for x, y in hucreler if lab[y][x] == "S")
        if s_konum not in self._erisim_kumesi(lab, engel=sorular):
            return False
        bilgi = self._yol_uzakliklari(lab, yol)
        pt = [(x, y) for x, y in hucreler if lab[y][x] in ("P", "T")]
        if any(bilgi.get(h, (99, 0))[0] > MAX_SAPMA for h in pt):
            return False
        return not all(bilgi[h][0] == 0 for h in pt)

    def labirent_olustur(self):
        for _ in range(MAX_URETIM_DENEME):
            lab = [["#" for _ in range(self.boyut)] for _ in range(self.boyut)]

            def kaz(x, y):
                yonler = [(0, 2), (2, 0), (0, -2), (-2, 0)]
                random.shuffle(yonler)
                for dx, dy in yonler:
                    nx, ny = x + dx, y + dy
                    if (0 < nx < self.boyut - 1 and 0 < ny < self.boyut - 1
                            and lab[ny][nx] == "#"):
                        lab[y + dy // 2][x + dx // 2] = " "
                        lab[ny][nx] = " "
                        kaz(nx, ny)

            lab[1][1] = " "
            kaz(1, 1)
            yol = self.hedef_yolu(lab)
            if len(yol) < self.toplam_soru + 2:
                continue

            # Sorular finalin zorunlu yolunda ve birbirinden ayrı hücrelerde.
            ara_noktalar = yol[1:-1]
            bolen = self.toplam_soru + 1
            for i in range(1, self.toplam_soru + 1):
                x, y = ara_noktalar[(i * len(ara_noktalar)) // bolen]
                lab[y][x] = "?"
            lab[self.boyut - 2][self.boyut - 2] = "X"

            # Bonuslar: 1 S (ilk sorudan önce), 1 P, 2 T (yola yakın, dağıtılmış)
            yerler = self._bonus_yerlestir(lab, yol)
            if yerler is None:
                continue
            self._sure_bonuslari = {}
            for harf, (x, y) in yerler:
                lab[y][x] = harf
                if harf == "T":
                    self._sure_bonuslari[(x, y)] = random.choice((5, 10))

            if self.labirent_dogrula(lab):
                return lab
        raise RuntimeError("Geçerli labirent üretilemedi.")

    # ---------------------------
    # SORULAR
    # ---------------------------
    def soru_olustur(self):
        if self._zorluk == "BASIT":
            a, b = random.randint(1, 20), random.randint(1, 20)
            op = random.choice(["+", "-"])
            cevap = a + b if op == "+" else a - b
            return {"soru": f"{a} {op} {b} = ?", "cevap": cevap, "tip": "normal"}

        elif self._zorluk == "ORTA":
            a, b = random.randint(10, 50), random.randint(2, 12)
            return {"soru": f"{a} x {b} = ?", "cevap": a * b, "tip": "normal"}

        else:
            a, b, c, d = [random.randint(1, 9) for _ in range(4)]
            return {"soru": [a, b, c, d], "cevap": (a * d) - (b * c), "tip": "matris"}

    def soruyu_ac(self, x, y):
        """Soru ilk karşılaşmada üretilir; aynı hücre aynı soruyu açar."""
        if (x, y) not in self._sorular:
            self._sorular[(x, y)] = self.soru_olustur()
        self.current_question = self._sorular[(x, y)]
        self.soru_konumu = (x, y)
        self.user_input = ""
        self.state = "QUESTION"

    def _soru_konumu_gecerli(self, konum):
        """Soru çözme işleminin TÜM ön koşulları; hiçbir şeyi değiştirmez."""
        if not (isinstance(konum, tuple) and len(konum) == 2
                and all(isinstance(v, int) and not isinstance(v, bool) for v in konum)):
            return False
        x, y = konum
        return (self.state == "QUESTION"
                and self._oyun_devam and self.kalan_sure > 0   # aktif oyun ve süre
                and 0 <= x < self.boyut and 0 <= y < self.boyut
                and konum in self._soru_hucreleri
                and konum not in self._cozulen_hucreler
                and self.labirent[y][x] == "?"
                and self._sorular.get(konum) is not None
                and self._sorular.get(konum) is self.current_question)

    def _soruyu_coz(self, konum):
        """Aktif oyun ve süre dahil tüm ön koşulları kendisi doğrular. Doğrula, sonra puan, bonus tüketimi, sayaç, hücre ve oyuncu konumunu tek
        işlem olarak uygula. Başarıda kazanılan puanı, doğrulama hatasında None döner
        (bu durumda puan ve bonus hiç değişmez)."""
        if (not self._soru_konumu_gecerli(konum)
                or not isinstance(self.current_question, dict)
                or type(self.current_question.get("cevap")) is not int):
            return None
        x, y = konum
        kazanilan = (40 if self._zorluk == "ZOR" else 20) * self.cift_puan_tuket()
        self.puan_ekle(kazanilan)
        self._cozulen_say(konum)
        self.labirent[y][x] = " "
        self._sorular.pop(konum, None)
        self.oyuncu_x, self.oyuncu_y = x, y
        self.current_question = None
        self.user_input = ""
        self.state = "PLAYING"
        return kazanilan

    def _yanlis_cevap_isle(self):
        kesinti = self.puan_dusur(YANLIS_CEZA)
        self.user_input = ""
        self.bildirim(f"Yanlış cevap, tekrar dene. -{kesinti} puan.")

    def _soru_verisi_yok_mu(self):
        """Bozuk aktif soruyu puan veya bonus değiştirmeden güvenle kapatır."""
        if self.state != "QUESTION":
            return False
        soru = self.current_question
        gecerli = (
            isinstance(soru, dict)
            and isinstance(soru.get("cevap"), int)
            and not isinstance(soru.get("cevap"), bool)
            and soru.get("tip") in ("normal", "matris")
            and ((soru.get("tip") == "normal" and isinstance(soru.get("soru"), str))
                 or (soru.get("tip") == "matris"
                     and isinstance(soru.get("soru"), (list, tuple))
                     and len(soru["soru"]) == 4
                     and all(type(v) is int for v in soru["soru"])))
            and self._soru_konumu_gecerli(self.soru_konumu)
        )
        if gecerli:
            return False
        # Bozuk önbellek kaydı, aynı hücreye gelince tekrar kullanılmasın.
        konum = self.soru_konumu
        if (isinstance(konum, tuple) and len(konum) == 2
                and all(type(v) is int for v in konum)):
            self._sorular.pop(konum, None)
        self.current_question = None
        self.user_input = ""
        self.state = "PLAYING"
        self.bildirim("Aktif soru verisi geçersiz. Soruyu yeniden açabilirsin.")
        return True

    def soru_cevapla(self):
        if self.state != "QUESTION" or self.sure_kontrol() or self._soru_verisi_yok_mu():
            return
        if self.user_input in ("", "-"):
            self.bildirim("Önce bir tam sayı yaz.")
            return
        try:
            val = int(self.user_input)
        except ValueError:
            self.user_input = ""
            self.bildirim("Geçersiz cevap, tekrar dene.")
            return
        if val != self.current_question["cevap"]:
            self._yanlis_cevap_isle()
            return
        kazanilan = self._soruyu_coz(self.soru_konumu)
        if kazanilan is None:
            # Tutarsız durum: puan/bonus değişmedi; oyuncu oyuna döndürülür.
            self.current_question = None
            self.user_input = ""
            self.state = "PLAYING"
            self.bildirim("Bu soru zaten çözülmüş.")
        else:
            self.bildirim(f"Doğru cevap! +{kazanilan} puan")

    def soru_degistir(self):
        """Pas: yalnızca soruyu değiştirir; hücre, puan ve bonus etkilenmez."""
        if self.state != "QUESTION" or self.sure_kontrol() or self._soru_verisi_yok_mu():
            return
        if not self.pas_kullan():
            self.bildirim("Pas hakkın kalmadı!")
            return
        eski = self.current_question
        yeni = self.soru_olustur()
        for _ in range(20):
            if yeni["soru"] != eski["soru"]:
                break
            yeni = self.soru_olustur()
        self._sorular[self.soru_konumu] = yeni
        self.current_question = yeni
        self.user_input = ""
        self.bildirim("Soru değişti. 1 pas harcandı.")

    # ---------------------------
    # SÜRE / DURAKLATMA / SONUÇ
    # ---------------------------
    def sure_kontrol(self):
        """Aktif oyunda süre bittiyse oyunu kaybettirir; bittiyse True döner."""
        if self.state in ("PLAYING", "QUESTION") and self.kalan_sure <= 0:
            self._oyun_devam = False
            self._duraklatma_baslangic = None
            self._kazandi = False
            self.state = "LOSE_SCREEN"
            self._sonuc_skorunu_kaydet()
            return True
        return False

    def duraklat(self):
        if self.state not in ("PLAYING", "QUESTION") or self.sure_kontrol():
            return
        self._duraklatma_oncesi_durum = self.state
        self._duraklatma_baslangic = time.monotonic()
        self.state = "PAUSE"

    def devam_et(self):
        if self.state != "PAUSE" or self._duraklatma_baslangic is None:
            return
        self._bitis_zamani += time.monotonic() - self._duraklatma_baslangic
        self._duraklatma_baslangic = None
        self.state = self._duraklatma_oncesi_durum or "PLAYING"
        self._duraklatma_oncesi_durum = None

    def _final_ac(self):
        self._oyun_devam = False
        self.state = "WIN_SCREEN"
        self._kazandi = self._puan >= self.puan_siniri
        self._sonuc_skorunu_kaydet()

    def _sonuc_skorunu_kaydet(self):
        """Her tamamlanan oyun için yalnızca bir kayıt girişimi yapar."""
        if not self.skor_kaydedildi:
            self.skor_kaydedildi = True  # başarısız olsa da tekrar denenmez
            self._skor_basarili = self.skor_kaydet(self.player_name, self._puan)
            if self._skor_basarili:
                self._skor_mesaji = "Sonucun işlendi. Bu zorlukta en iyi 5 skor saklanır."
            else:
                self._skor_mesaji = "Skor dosyasına yazılamadı; skor kaydedilemedi."

    # ---------------------------
    # BUTON
    # ---------------------------
    def animasyonlu_buton(self, text, center_pos, color_theme=WHITE, size=(320, 65)):
        mx, my = pygame.mouse.get_pos()
        scale = self.hover_scale.get(text, 1.0)

        rect = pygame.Rect(0, 0, int(size[0] * scale), int(size[1] * scale))
        rect.center = center_pos
        is_hover = rect.collidepoint(mx, my)

        scale = min(scale + 0.05, 1.08) if is_hover else max(scale - 0.05, 1.0)
        self.hover_scale[text] = scale

        # Görünen alan = tıklama alanı
        rect = pygame.Rect(0, 0, int(size[0] * scale), int(size[1] * scale))
        rect.center = center_pos
        draw_color = GOLD if is_hover else color_theme

        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (40, 40, 40, 235), surf.get_rect(), border_radius=18)
        pygame.draw.rect(surf, draw_color, surf.get_rect(), 3, border_radius=18)
        txt_surf = self.font_sub.render(text, True, draw_color)
        surf.blit(txt_surf, txt_surf.get_rect(center=surf.get_rect().center))
        self.screen.blit(surf, rect)

        # Tıklama yalnızca ait olduğu ekranda (aynı _ekran_no) ve bir kez işlenir.
        if (self._tik is not None and self._tik[1] == self._ekran_no
                and rect.collidepoint(self._tik[0])):
            self._tik = None
            return True
        return False

    # ---------------------------
    # ÇİZİM YARDIMCILARI
    # ---------------------------
    def draw_background_gradient(self):
        self.screen.blit(self._arka_plan, (0, 0))

    def draw_center_text(self, text, font, color, y):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))

    @staticmethod
    def metni_satirlara_bol(text, font, max_width):
        satirlar, mevcut = [], ""
        for kelime in text.split():
            deneme = (mevcut + " " + kelime).strip()
            if font.size(deneme)[0] <= max_width or not mevcut:
                mevcut = deneme
            else:
                satirlar.append(mevcut)
                mevcut = kelime
        if mevcut:
            satirlar.append(mevcut)
        return satirlar

    def draw_wrapped_center(self, text, font, color, y, max_width=900):
        """Uzun metni satırlara böler; sonraki satırın y değerini döndürür."""
        for satir in self.metni_satirlara_bol(text, font, max_width):
            self.draw_center_text(satir, font, color, y)
            y += font.get_linesize()
        return y


    @staticmethod
    def metni_sigdir(metin, font, max_genislik):
        """Metin sığmıyorsa sonuna '...' koyarak kısaltır."""
        if font.size(metin)[0] <= max_genislik:
            return metin
        while metin and font.size(metin + "...")[0] > max_genislik:
            metin = metin[:-1]
        return metin.rstrip() + "..."

    def show_feedback(self):
        if self.feedback_text and time.monotonic() - self.feedback_time < BILDIRIM_SURESI:
            txt = self.font_sub.render(self.feedback_text, True, YELLOW)
            rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
            zemin = rect.inflate(30, 14)
            pygame.draw.rect(self.screen, (30, 30, 30), zemin, border_radius=10)
            pygame.draw.rect(self.screen, YELLOW, zemin, 2, border_radius=10)
            self.screen.blit(txt, rect)

    def _isaret_ciz(self, harf, merkez, zemin, yaricap, yazi=WHITE):
        pygame.draw.circle(self.screen, zemin, merkez, yaricap)
        pygame.draw.circle(self.screen, BLACK, merkez, yaricap, 2)
        anahtar = (harf, yazi)
        if anahtar not in self._harf_onbellek:
            self._harf_onbellek[anahtar] = self.font_tiny.render(harf, True, yazi)
        yuzey = self._harf_onbellek[anahtar]
        self.screen.blit(yuzey, yuzey.get_rect(center=merkez))

    # ---------------------------
    # OYUN ÇİZİMİ
    # ---------------------------
    def kamerayi_guncelle(self):
        tx = (SCREEN_WIDTH // 2) - (self.oyuncu_x * TILE_SIZE)
        ty = (SCREEN_HEIGHT // 2) - (self.oyuncu_y * TILE_SIZE)
        self.camera_x += (tx - self.camera_x) * 0.1
        self.camera_y += (ty - self.camera_y) * 0.1

    def dunya_ciz(self):
        tema = TEMALAR[self._tema]
        for y in range(self.boyut):
            py = y * TILE_SIZE + self.camera_y
            if py < -TILE_SIZE or py > SCREEN_HEIGHT:
                continue
            for x in range(self.boyut):
                px = x * TILE_SIZE + self.camera_x
                if px < -TILE_SIZE or px > SCREEN_WIDTH:
                    continue
                c = self.labirent[y][x]
                ix, iy = int(px), int(py)

                if c == "#":
                    pygame.draw.rect(self.screen, tema["wall"],
                                     (ix, iy, TILE_SIZE - 2, TILE_SIZE - 2), border_radius=8)
                    continue

                pygame.draw.rect(self.screen, tema["floor"], (ix, iy, TILE_SIZE, TILE_SIZE))
                merkez = (ix + 25, iy + 25)
                if c == "X":
                    acik = self.tum_sorular_cozuldu
                    renk = tema["target"] if acik else GRAY
                    kutu = pygame.Rect(ix + 4, iy + 4, 42, 42)
                    pygame.draw.rect(self.screen, renk, kutu, border_radius=6)
                    pygame.draw.rect(self.screen, GOLD if acik else BLACK, kutu, 3, border_radius=6)
                    etiket = "AÇIK" if acik else "KİLİT"
                    anahtar = (etiket, BLACK)
                    if anahtar not in self._harf_onbellek:
                        self._harf_onbellek[anahtar] = self.font_tiny.render(etiket, True, BLACK)
                    yuzey = self._harf_onbellek[anahtar]
                    self.screen.blit(yuzey, yuzey.get_rect(center=merkez))
                elif c == "?":
                    self._isaret_ciz("?", merkez, GOLD, 15, BLACK)
                elif c == "P":
                    self._isaret_ciz("P", merkez, GREEN, 13)
                elif c == "S":
                    self._isaret_ciz("S", merkez, PURPLE, 13)
                elif c == "T":
                    self._isaret_ciz("T", merkez, CYAN, 13)

        pygame.draw.circle(
            self.screen, tema["player"],
            (int(self.oyuncu_x * TILE_SIZE + self.camera_x + 25),
             int(self.oyuncu_y * TILE_SIZE + self.camera_y + 25)),
            18)

    def hud_ciz(self):
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, SCREEN_WIDTH, 70))
        pygame.draw.line(self.screen, GOLD, (0, 70), (SCREEN_WIDTH, 70), 2)

        sure = math.ceil(self.kalan_sure)
        alanlar = [
            ("SORU", f"{self._cozulen_soru}/{self.toplam_soru}", WHITE, 140),
            ("SÜRE", f"{sure} sn", RED if sure <= 10 else WHITE, 140),
            ("PUAN", str(self._puan), WHITE, 130),
            ("PAS", str(self._pas_gec_hakki), WHITE, 100),
            ("TEMA", self._tema, WHITE, 250),
            ("BONUS", "ÇİFT PUAN" if self._cift_puan_aktif else "-",
             PURPLE if self._cift_puan_aktif else GRAY, 200),
        ]
        x = 20
        for etiket, deger, renk, genislik in alanlar:
            self.screen.blit(self.font_tiny.render(etiket, True, GRAY), (x, 9))
            self.screen.blit(self.font_sub.render(deger, True, renk), (x, 32))
            x += genislik
            pygame.draw.line(self.screen, (70, 70, 70), (x - 12, 12), (x - 12, 58), 1)

    def kontrol_aciklamasi_ciz(self):
        txt = self.font_tiny.render(
            "Yön tuşları / WASD: hareket   •   ESC: duraklat   •   R: yeniden başlat",
            True, WHITE)
        rect = txt.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 6))
        zemin = pygame.Surface((rect.width + 20, rect.height + 6), pygame.SRCALPHA)
        zemin.fill((0, 0, 0, 150))
        self.screen.blit(zemin, (rect.x - 10, rect.y - 3))
        self.screen.blit(txt, rect)

    def oyun_cizim(self):
        self.dunya_ciz()
        self.hud_ciz()
        self.kontrol_aciklamasi_ciz()

    def soru_paneli_ciz(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(250, 140, 500, 430)
        pygame.draw.rect(self.screen, WHITE, panel, border_radius=20)
        pygame.draw.rect(self.screen, BLUE, panel, 3, border_radius=20)

        self.draw_center_text("SORUYU ÇÖZ", self.font_large, BLACK, 190)

        if self.current_question["tip"] == "normal":
            self.draw_center_text(self.current_question["soru"], self.font_main, BLACK, 270)
        else:
            m = self.current_question["soru"]
            self.draw_center_text(f"| {m[0]}   {m[1]} |", self.font_main, BLACK, 235)
            self.draw_center_text(f"| {m[2]}   {m[3]} |", self.font_main, BLACK, 280)
            self.draw_center_text("Determinantı hesapla", self.font_sub, GRAY, 322)

        kutu = pygame.Rect(0, 0, 300, 60)
        kutu.center = (500, 395)
        pygame.draw.rect(self.screen, (235, 245, 255), kutu, border_radius=12)
        pygame.draw.rect(self.screen, BLUE, kutu, 3, border_radius=12)
        self.draw_center_text(self.user_input + "_", self.font_large, BLUE, 395)

        self.draw_center_text("Enter ile gönder   •   Negatif için başa - yaz",
                              self.font_small, GRAY, 450)
        self.draw_center_text(f"Kalan pas hakkı: {self._pas_gec_hakki}",
                              self.font_small, GRAY, 478)

        if self.animasyonlu_buton("SORUYU DEĞİŞTİR — 1 PAS", (500, 528), CYAN, (340, 48)):
            self.soru_degistir()

    # ---------------------------
    # OLAYLAR
    # ---------------------------
    def hareket_et(self, dx, dy):
        if self.state != "PLAYING" or self.sure_kontrol():
            return
        nx, ny = self.oyuncu_x + dx, self.oyuncu_y + dy
        if not (0 <= nx < self.boyut and 0 <= ny < self.boyut):
            return

        cell = self.labirent[ny][nx]
        if cell == "#":
            return
        if cell == "?":
            self.soruyu_ac(nx, ny)
            return

        self.oyuncu_x, self.oyuncu_y = nx, ny
        if cell == "P":
            self.labirent[ny][nx] = " "
            self.pas_ekle()
            self.bildirim("+1 Pas Hakkı Kazandın!")
        elif cell == "S":
            self.labirent[ny][nx] = " "
            self.cift_puan_etkinlestir()
            self.bildirim("Çift Puan Aktif!")
        elif cell == "T":
            saniye = self._sure_bonuslari.get((nx, ny), 0)
            if saniye and self.sure_ekle(saniye):
                del self._sure_bonuslari[(nx, ny)]
                self.labirent[ny][nx] = " "
                self.bildirim(f"+{saniye} saniye")
        elif cell == "X":
            if self.tum_sorular_cozuldu:
                self._final_ac()
            else:
                self.bildirim(f"Önce tüm soruları çöz: {self._cozulen_soru}/{self.toplam_soru}")

    def soru_tusu_isle(self, event):
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.soru_cevapla()
        elif event.key == pygame.K_BACKSPACE:
            self.user_input = self.user_input[:-1]
        else:
            ch = event.unicode
            if len(ch) != 1 or len(self.user_input) >= MAX_CEVAP_UZUNLUGU:
                return
            if ch in "0123456789" or (ch == "-" and not self.user_input):
                self.user_input += ch

    def oyun_tusu_isle(self, event):
        dx, dy = 0, 0
        if event.key in (pygame.K_UP, pygame.K_w):
            dy = -1
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            dy = 1
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            dx = -1
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            dx = 1
        if dx != 0 or dy != 0:
            self.hareket_et(dx, dy)

    def isim_onayla(self):
        self.oyuncu_adi_ayarla(self._isim_giris)
        self._isim_giris = self.player_name
        self.state = "DIFF_SELECT"

    def isim_tusu_isle(self, event):
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.isim_onayla()
        elif event.key == pygame.K_BACKSPACE:
            self._isim_giris = self._isim_giris[:-1]
            self._isim_uyari = ""
        else:
            ch = event.unicode
            if not (len(ch) == 1 and (ch.isalnum() or ch in " -_.")):
                return
            aday = self._isim_giris + ch
            if len(aday) > MAX_ISIM_UZUNLUGU:
                self._isim_uyari = f"En fazla {MAX_ISIM_UZUNLUGU} karakter."
            elif (self.font_main.size(aday + "_")[0]
                  > ISIM_KUTU_GENISLIGI - 2 * ISIM_IC_BOSLUK):
                self._isim_uyari = "Bu isim kutuya sığmıyor."
            else:
                self._isim_giris = aday
                self._isim_uyari = ""

    def olay_isle(self, event):
        """Her olay, başladığı ekran durumuna göre en fazla bir kez işlenir."""
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Aynı karede birden fazla basış varsa sonuncusu geçerlidir.
                self._tik = (event.pos, self._ekran_no)
            return
        if event.type != pygame.KEYDOWN:
            return

        self.sure_kontrol()          # süre bittiyse eylem kabul edilmeden önce durum güncellenir
        durum = self.state

        if event.key == pygame.K_r and durum in YENIDEN_BASLATMA_DURUMLARI:
            self.yeniden_baslat()
        elif event.key == pygame.K_ESCAPE and durum in ("PLAYING", "QUESTION"):
            self.duraklat()
        elif event.key == pygame.K_ESCAPE and durum == "PAUSE":
            self.devam_et()
        elif durum == "QUESTION":
            self.soru_tusu_isle(event)
        elif durum == "PLAYING":
            self.oyun_tusu_isle(event)
        elif durum == "NAME_ENTRY":
            self.isim_tusu_isle(event)

    # ---------------------------
    # EKRANLAR
    # ---------------------------
    def ekrani_ciz(self):
        self.draw_background_gradient()
        durum = self.state

        if durum == "MENU":
            self.draw_center_text(f"MATEMATİK LABİRENTİ {VERSION}", self.font_large, BLUE, 120)
            self.draw_center_text("Akıllı labirent, soru çöz, hedefe ulaş!", self.font_sub, GRAY, 170)
            if self.animasyonlu_buton("OYUNA BAŞLA", (500, 300), WHITE):
                self._isim_giris = self.player_name
                self._isim_uyari = ""
                self.state = "NAME_ENTRY"
            if self.animasyonlu_buton("SKORLAR", (500, 400), WHITE):
                self._skor_zorluk = self._zorluk
                self.state = "LEADERBOARD"
            if self.animasyonlu_buton("ÇIKIŞ", (500, 500), RED):
                self.running = False

        elif durum == "NAME_ENTRY":
            self.draw_center_text("Oyuncu Adı", self.font_large, GOLD, 150)
            kutu = pygame.Rect(0, 0, ISIM_KUTU_GENISLIGI, 70)
            kutu.center = (500, 260)
            pygame.draw.rect(self.screen, (40, 40, 40), kutu, border_radius=14)
            pygame.draw.rect(self.screen, BLUE, kutu, 3, border_radius=14)
            self.draw_center_text(self._isim_giris + "_", self.font_main, WHITE, 260)
            self.draw_center_text(f"En fazla {MAX_ISIM_UZUNLUGU} karakter. Boş bırakırsan "
                                  f"\"{VARSAYILAN_ISIM}\" kullanılır.", self.font_small, GRAY, 320)
            if self._isim_uyari:
                self.draw_center_text(self._isim_uyari, self.font_small, YELLOW, 350)
            if self.animasyonlu_buton("DEVAM", (500, 440), GREEN):
                self.isim_onayla()
            elif self.animasyonlu_buton("GERİ", (500, 540), CYAN, (200, 50)):
                self.state = "MENU"

        elif durum == "DIFF_SELECT":
            self.draw_center_text("Zorluk Seç", self.font_large, GOLD, 130)
            self.draw_center_text(
                self.metni_sigdir(f"Oyuncu: {self.player_name}", self.font_small, 800),
                self.font_small, GRAY, 180)
            for etiket, zorluk, renk, y in (("BASİT", "BASIT", GREEN, 260),
                                           ("ORTA", "ORTA", GOLD, 360),
                                           ("ZOR", "ZOR", RED, 460)):
                if self.animasyonlu_buton(etiket, (500, y), renk):
                    self.zorluk_ayarla(zorluk)
                    self.state = "THEME_SELECT"
            if self.state == "DIFF_SELECT" and self.animasyonlu_buton("GERİ", (500, 610), CYAN, (200, 50)):
                self.state = "MENU"

        elif durum == "THEME_SELECT":
            self.draw_center_text("Tema Seç", self.font_large, CYAN, 130)
            y = 260
            for t in TEMALAR:
                if self.animasyonlu_buton(t, (500, y), WHITE):
                    self.tema_ayarla(t)
                    self.oyunu_sifirla()
                    self.state = "PLAYING"
                y += 100
            if self.state == "THEME_SELECT" and self.animasyonlu_buton("GERİ", (500, 620), CYAN, (200, 50)):
                self.state = "DIFF_SELECT"

        elif durum in ("PLAYING", "QUESTION"):
            self.kamerayi_guncelle()
            self.oyun_cizim()
            if durum == "QUESTION" and not self._soru_verisi_yok_mu():
                self.soru_paneli_ciz()
            self.show_feedback()   # karartma katmanının üstünde

        elif durum == "PAUSE":
            self.oyun_cizim()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 185))
            self.screen.blit(overlay, (0, 0))
            self.draw_center_text("DURAKLATILDI", self.font_huge, WHITE, 220)
            if self.animasyonlu_buton("DEVAM ET", (500, 390), GREEN):
                self.devam_et()
            elif self.animasyonlu_buton("ANA MENÜ", (500, 490), CYAN):
                self.ana_menuye_don()

        elif durum in ("WIN_SCREEN", "LOSE_SCREEN"):
            self.screen.fill(BLACK)
            if durum == "WIN_SCREEN":
                if self._kazandi:
                    txt, clr = "TEBRİKLER! KAZANDIN", GREEN
                else:
                    txt, clr = "HEDEFE ULAŞTIN AMA PUAN YETERSİZ", RED
            else:
                txt, clr = "ZAMAN BİTTİ!", RED

            self.draw_wrapped_center(txt, self.font_main, clr, 70)
            self.draw_center_text(f"{self.player_name} — Skor: {self._puan}",
                                  self.font_sub, WHITE, 165)
            self.draw_center_text(f"Gerekli minimum puan: {self.puan_siniri}",
                                  self.font_small, GRAY, 205)
            if self._skor_mesaji:
                self.draw_wrapped_center(self._skor_mesaji, self.font_small,
                    GREEN if self._skor_basarili else YELLOW, 245)
            self.draw_center_text(f"{GRUP_ETIKETLERI[self._zorluk]} — EN İYİ 5 KAYIT",
                                  self.font_sub, GOLD, 310)
            kayitlar = self.skorlari_getir(self._zorluk)
            if not kayitlar:
                self.draw_center_text("Henüz kayıtlı skor yok.", self.font_small, GRAY, 365)
            for i, kayit in enumerate(kayitlar):
                y = 360 + i * 42
                isim = self.metni_sigdir(kayit["isim"], self.font_sub, 420)
                metin = self.font_sub.render(f"{i + 1}. {isim}", True, WHITE)
                self.screen.blit(metin, (230, y))
                puan = self.font_sub.render(str(kayit["puan"]), True, GOLD)
                self.screen.blit(puan, puan.get_rect(topright=(770, y)))
            self.draw_center_text("R ile yeniden başlat", self.font_small, GRAY, 590)
            if self.animasyonlu_buton("ANA MENÜ", (330, 660), CYAN, (270, 55)):
                self.ana_menuye_don()
            elif self.animasyonlu_buton("ÇIKIŞ", (670, 660), RED, (270, 55)):
                self.running = False

        elif durum == "LEADERBOARD":
            self.draw_center_text("TOP 5 SKOR", self.font_large, GOLD, 100)
            gruplar = [g for g in SKOR_GRUPLARI
                       if g != BELIRTILMEMIS
                       or any(k["zorluk"] == BELIRTILMEMIS for k in self._yuksek_skorlar)]
            if self._skor_zorluk not in gruplar:
                self._skor_zorluk = "ORTA"
            for n, g in enumerate(gruplar):
                x = 500 + int((n - (len(gruplar) - 1) / 2) * 215)
                secili = g == self._skor_zorluk
                if self.animasyonlu_buton(GRUP_ETIKETLERI[g], (x, 180),
                                          GOLD if secili else WHITE, (200, 44)):
                    self._skor_zorluk = g
                if secili:
                    pygame.draw.rect(self.screen, GOLD, (x - 80, 206, 160, 4))
            satirlar = self.skorlari_getir(self._skor_zorluk)
            if not satirlar:
                self.draw_center_text("Bu zorlukta henüz kayıtlı skor yok.",
                                      self.font_main, WHITE, 330)
            for i, k in enumerate(satirlar):
                y = 280 + i * 62
                sira = self.font_main.render(f"{i + 1}.", True, WHITE)
                self.screen.blit(sira, sira.get_rect(midleft=(170, y)))
                isim = self.metni_sigdir(k["isim"], self.font_main, 400)
                yuzey = self.font_main.render(isim, True, WHITE)
                self.screen.blit(yuzey, yuzey.get_rect(midleft=(250, y)))
                puan = self.font_main.render(str(k["puan"]), True, GOLD)
                self.screen.blit(puan, puan.get_rect(midright=(830, y)))
            if self.animasyonlu_buton("GERİ", (500, 650), CYAN, (200, 50)):
                self.state = "MENU"

    # ---------------------------
    # ANA DÖNGÜ
    # ---------------------------
    def run(self):
        while self.running:
            self._tik = None
            for event in pygame.event.get():
                self.olay_isle(event)
            self.sure_kontrol()
            self.ekrani_ciz()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == '__main__':
    MatematikLabirentPro().run()