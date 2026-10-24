# Matematik Labirenti v2

Pygame ile tek oyunculu matematik labirenti. Üç zorluk ve üç tema içerir.

## Kurulum

Python 3.10+ ve grafik ekranı gerekir.

```sh
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python labirent.py
```

## Kontroller

- WASD / yön tuşları: hareket.
- Enter: soruyu cevapla; ekrandaki PAS butonu: pas kullan.
- ESC: oyunda duraklat / devam et.
- R: oyun veya sonuç ekranından yeniden başlat.

`?` matematik sorusu, `P` ek pas, `S` çift puan, `X` çıkıştır.
Basit/orta doğru cevap 20, zor doğru cevap 40 puandır; yanlış cevap 15 puan düşürür.
Çıkışta kazanmak için 200 puan gerekir. Labirentte 10 soru vardır; böylece
çift puan bonusuna bağımlı olmadan bütün zorluklarda hedefe ulaşılabilir.
Basit/orta/zor süreleri 120/90/75 saniyedir; soru ekranında süre işlemeye devam eder.

En iyi 5 skor, uygulama dosyasının yanındaki `skorlar.json` içinde tutulur.
Bozuk kayıtlar filtrelenir. Skor her kazanılan oyun için yalnızca bir kez kaydedilir.

## Dosyalar

`labirent.py`: uygulama; `requirements.txt`: bağımlılık; kökteki Word/PowerPoint
belgeleri: mevcut proje materyalleri (bu bakımda içerikleri değiştirilmedi).
