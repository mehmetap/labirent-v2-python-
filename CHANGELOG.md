# Güncelleme notları

## 2.1.0 — 31 Ekim 2026

Bu sürüm yerelde hazırlanmıştır; GitHub yayını henüz tamamlanmamıştır.

### Eklenenler

- Her oyun sonunda seçili zorluğun en iyi beş kaydı sonuç ekranında gösterilir.
- Kazanma, düşük puan ve süre bitişi sonuçları için tek kayıt girişimi yapılır.
- Zorluklara göre ayrı skor grupları, oyuncu adı girişi ve T süre bonusları.
- Puan, pas ve süre için doğrulamalı metotlar ve salt okunur özellikler.
- Kurulum bağımlılıkları, Türkçe README ve tekrar çalıştırılabilir testler.
- Menü ve pencere başlığında 2.1.0 sürüm bilgisi.

### Düzeltilenler

- Eski fare tıklamasının ekran değişince başka düğmeyi tetiklemesi.
- Süre dolduktan sonra doğrudan soru çözümünün puan vermesi.
- Eksik cevap, bozuk soru türü veya hatalı matris içeriğinin çizimi çökertmesi.
- Aynı hücreden birden fazla puan kazanılması.
- Yanlış cevap veya pasın çift puan bonusunu tüketmesi.
- Kayıt başarısızken bellekte kaydedilmiş gibi görünmesi.
- Negatif/geçersiz skor girdileri ve zorluk kayıtlarının birbirini silmesi.
- Sonuç ekranlarında R kısayolu ve soru ekranından duraklatmaya dönüş.

### Korunan kurallar

- Tek dosyalı Pygame oyunu, mevcut temalar ve üç zorluk korunur.
- Pas soruyu değiştirir; çözülmüş saymaz.
- Minimum puan BASIT/ORTA için 100, ZOR için 200'dür.
- Her zorluk için yalnızca en iyi beş skor saklanır; tam oyun geçmişi tutulmaz.
- Eski sunum ve Word dosyaları değiştirilmemiştir; güncel kurallar için README geçerlidir.

### Doğrulama

Python 3.12.14 / Pygame 2.6.1 sanal ekran ortamında 7 otomatik test geçti. Labirent testi üç zorlukta toplam 300 harita üretir. Diğer kontroller: bozuk soru çizimi, süresi bitmiş çözüm, yanlış/doğru cevap ve bonus, eski fare olayı, kayıt hatası ve üç sonuç türünde tek kayıt.

Gerçek masaüstünde görsel kontrol yapılmadı. Python 3.13 ve Windows üzerinde bu ortamda doğrulama yapılmadı. Minimum puan koşulu nedeniyle cezalar telafi edilmezse tüm sorular çözülse bile kazanılamayabilir.
