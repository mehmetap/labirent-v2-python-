# Matematik Labirenti Pro

Python ve Pygame ile geliştirilmiş, matematik sorularını çözerek çıkışa ulaşılan masaüstü labirent oyunu.

## Kurulum

Python 3.12 ve Pygame 2.6.1 ile sanal ekran ortamında test edilmiştir.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
source .venv/bin/activate
```

```bash
python -m pip install -r requirements.txt
python "labirent v2.py"
```

## Oynanış

Tema ve zorluk seçip başlangıçtan finale ilerle. Zorunlu yoldaki beş soruyu çöz, süre bitmeden çıkışa ulaş ve minimum puanı karşıla.

| Seviye | Sorular | Süre | Doğru cevap | Minimum puan |
| --- | --- | --- | --- | --- |
| Basit | Toplama ve çıkarma | 120 sn | 20 | 100 |
| Orta | Çarpma | 90 sn | 20 | 100 |
| Zor | 2×2 determinant | 75 sn | 40 | 200 |

Yanlış cevap mevcut puandan en fazla 15 puan düşürür. Bütün soruları çözmek tek başına kazanmayı garanti etmez; puan kaybını bonuslarla telafi etmek gerekebilir.

## Kontroller

| Tuş | İşlem |
| --- | --- |
| Yön tuşları / WASD | Hareket |
| Enter | Cevabı gönder |
| Backspace | Karakter sil |
| ESC | Duraklat / devam et |
| R | Oyun ve sonuç ekranlarında yeniden başlat |

## Bonuslar ve kayıtlar

- **P:** Bir pas hakkı ekler. Pas soruyu değiştirir; çözülmüş saymaz.
- **S:** Sonraki doğru cevaba çift puan verir. Yanlış cevap ve pas bonusu tüketmez.
- **T:** Bir kez +5 veya +10 saniye kazandırır.
- Temalar: Buz Diyarı, Nemrut ve AHEP Kampüs.
- Her tamamlanan oyunun sonucu bir kez işlenir. Her zorluk için en iyi beş skor saklanır ve sonuç ekranında gösterilir.
- Eski, zorluğu bilinmeyen kayıtlar ayrı grupta korunur.
- Kayıtlar kodun yanındaki `skorlar.json` dosyasındadır. Bu klasör yazılabilir olmalıdır. Kişisel skorlar Git'e gönderilmez.

## Kod yapısı

`labirent v2.py` tek dosyalı oyun girişidir. Puan, pas ve süre işlemleri kontrollü metotlarla yönetilir; salt okunur property'ler kullanılır. Bozuk soru verisi, süre bitişi ve dosya yazma hataları için korumalar bulunur.

Depodaki önceki sunum ve belge dosyaları korunmuştur.

## Doğrulama

Geliştirme sırasında sanal ekranla 300 labirent üretimi, tuş olaylarıyla uçtan uca oyunlar, soru/pas/bonus, duraklatma ve skor kaydı senaryoları kontrol edildi. Son kayıt ekranı değişikliğinde kazanma, düşük puan, süre bitişi ve kayıt hatası senaryoları geçti. Gerçek masaüstünde elle oynama ve görsel kontrol yapılmadı.

## Güncel sürüm ve testler

Sürüm: **2.1.0**. Ayrıntılar: [Güncelleme notları](CHANGELOG.md).

```bash
python -m unittest discover -s tests -v
```

Testler geçici skor dosyaları kullanır; oyuncunun kayıtlarını değiştirmez.

## Eski belge ve sunumlar

`LABİRENT V2 metin.docx`, `labirent oyunu.pptx` ve `Matematiksel labirent oyunu.pptx` önceki geliştirme aşamalarına aittir. İçerikleri metin düzeyinde incelendi, dosyalar korunmuştur; görsel düzenleri doğrulanmadı.

Eski belgelerdeki “pas soruyu atlatır”, “yanlış cevap başlangıca döndürür” ve “tüm seviyelerde 200 puan gerekir” açıklamaları güncel oyunu tanımlamaz. Geçerli kurallar bu README'dedir.
