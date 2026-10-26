# Matematik Labirenti v2

Python + Pygame ile soru çözerek çıkışa ulaşma oyunu.

```sh
python -m pip install -r requirements.txt
python "labirent v2.py"
```

Python 3.10+ ve grafik ekran gerekir. Oklar/WASD: hareket; Enter: cevap; R: yeniden başlat; ESC: duraklat/devam.
Üç zorluk ve üç tema bulunur. P pas hakkı, S çift puan verir. Skorlar çalışma klasöründeki skorlar.json dosyasına yazılır.

## Düzeltmeler

- Eksik pygame içe aktarımı, __init__ ve __main__ yazımları düzeltildi.
- Kazanma ekranında skorun her karede tekrar kaydı engellendi.
- Final ekranında R kısayolu etkinleştirildi.
- Beş sorulu haritada erişilemeyen 200 puan eşiği, beş normal cevabın toplamı olan 100 puana indirildi.

Otomatik kontroller başlangıç, üç zorlukta çıkışa erişim ve tek seferlik skor kaydını kapsar. Gerçek ekranda görsel kullanım ayrıca denenmelidir.
