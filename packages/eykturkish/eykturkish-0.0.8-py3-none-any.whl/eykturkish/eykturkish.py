# -*- coding: utf-8 -*-
# Bu dosya, temel Python yardımcı fonksiyonlarını, Türkçe dil desteğini ve
# çeşitli sistem işlemlerini içeren genişletilmiş bir kütüphanedir.
# Kod, okunabilirlik ve işlevsellik açısından detaylı bir şekilde yorumlanmıştır.
# Dosyanın toplam satır sayısı 500'ü geçmeyecek şekilde ayarlanmıştır.
# Lisans bilgileri projenin ana dizinindeki LICENSE.md dosyasında bulunabilir.
# Bu kod, Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)
# lisansı altında yayınlanmıştır.

import os
import sys
import time
import json
import datetime
import random
import socket
import threading
import string
import re
import math
import shutil
from collections import Counter
from typing import List, Dict, Any, Union, Tuple, Set

# ==============================================================================
# Hata ve Durum Bildirim Sınıfı (Logger)
# ==============================================================================
# Uygulama genelinde standartlaştırılmış ve bilgilendirici mesajlar sağlamak için
# bu sınıf kullanılır. Her fonksiyon, durumunu veya karşılaştığı sorunları
# bu sınıf aracılığıyla bildirebilir.

class Logger:
    """
    Basit bir konsol günlükleme (logging) sınıfı.
    `info`, `warning` ve `error` seviyelerinde mesajlar sağlar.
    """
    @staticmethod
    def _get_timestamp() -> str:
        """Mevcut zamanı formatlı bir string olarak döndürür."""
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def info(message: str) -> None:
        """Bilgilendirme mesajı yazdırır."""
        print(f"[INFO] {Logger._get_timestamp()} - {message}")

    @staticmethod
    def warning(message: str) -> None:
        """Uyarı mesajı yazdırır."""
        print(f"[UYARI] {Logger._get_timestamp()} - {message}")

    @staticmethod
    def error(message: str) -> None:
        """Hata mesajı yazdırır."""
        print(f"[HATA] {Logger._get_timestamp()} - {message}")

# ==============================================================================
# Metin İşleme ve Türkçe Karakter Desteği
# ==============================================================================
# Bu bölümde, metinler üzerinde çeşitli dönüştürme ve analiz işlemleri yapılır.
# Özellikle Türkçe karakterlerle ilgili özel durumlar ele alınmıştır.

def turkce_karakterleri_ascii_yap(metin: str) -> str:
    """
    Türkçe özel karakterleri (ş, ç, ğ, ö, ü, ı) ASCII eşdeğerleriyle değiştirir.
    Örnek: "ışİğüç" -> "isIguc"

    Args:
        metin (str): Dönüştürülecek metin.

    Returns:
        str: ASCII'ye dönüştürülmüş metin.
    """
    turkce_karakterler_map = {
        'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    yeni_metin = ""
    for karakter in metin:
        yeni_metin += turkce_karakterler_map.get(karakter, karakter)
    return yeni_metin

def buyuk_harflere_cevir(metin: str) -> str:
    """
    Verilen metnin tamamını Türkçe dil kurallarına uygun olarak büyük harfe dönüştürür.
    "i" harfini "İ" yerine "I"ya dönüştürür.

    Args:
        metin (str): Dönüştürülecek metin.

    Returns:
        str: Büyük harflere dönüştürülmüş metin.
    """
    return metin.upper().replace("İ", "I").replace("i", "I")

def kucuk_harflere_cevir(metin: str) -> str:
    """
    Verilen metnin tamamını Türkçe dil kurallarına uygun olarak küçük harfe dönüştürür.
    "I" harfini "ı"ya dönüştürür.

    Args:
        metin (str): Dönüştürülecek metin.

    Returns:
        str: Küçük harflere dönüştürülmüş metin.
    """
    return metin.lower().replace("I", "ı").replace("İ", "i")

def turkce_ingilizce_sozluk(kelime: str) -> str:
    """
    Basit bir Türkçe kelimeyi İngilizce'ye çevirir. Kapsamı sınırlıdır.

    Args:
        kelime (str): Çevrilecek Türkçe kelime.

    Returns:
        str: İngilizce karşılığı veya bulunamadığına dair bir mesaj.
    """
    sozluk = {
        "merhaba": "hello", "nasılsın": "how are you", "teşekkürler": "thank you",
        "evet": "yes", "hayır": "no", "elma": "apple",
        "bilgisayar": "computer", "kitap": "book", "kedi": "cat",
        "köpek": "dog", "su": "water", "hava": "air", "masa": "table",
        "sandalye": "chair", "güneş": "sun", "ay": "moon", "yıldız": "star",
        "telefon": "phone", "ekran": "screen", "klavye": "keyboard", "fare": "mouse",
        "şişe": "bottle", "bardak": "glass", "kaşık": "spoon", "çatal": "fork",
        "bıçak": "knife", "yemek": "food", "içecek": "drink", "araba": "car",
        "bisiklet": "bicycle", "uçak": "plane", "gem": "ship", "tren": "train"
    }
    return sozluk.get(kucuk_harflere_cevir(kelime), "Bu kelime sözlükte bulunmuyor.")

def kelime_sayaci(metin: str) -> Dict[str, int]:
    """
    Verilen metindeki her kelimenin kaç defa geçtiğini sayar.
    Noktalama işaretleri ve büyük/küçük harf duyarlılığı göz ardı edilir.

    Args:
        metin (str): Analiz edilecek metin.

    Returns:
        Dict[str, int]: Her kelimenin frekansını içeren bir sözlük.
    """
    metin = metin.lower()
    metin = re.sub(r'[^\w\s]', '', metin)
    kelimeler = metin.split()
    return dict(Counter(kelimeler))

def metinden_noktalama_isaretlerini_kaldir(metin: str) -> str:
    """
    Verilen metinden tüm noktalama işaretlerini kaldırır.

    Args:
        metin (str): İşlenecek metin.

    Returns:
        str: Noktalama işaretleri kaldırılmış metin.
    """
    return metin.translate(str.maketrans('', '', string.punctuation))

def metni_satirlara_bol(metin: str, satir_uzunlugu: int = 80) -> List[str]:
    """
    Bir metni belirtilen satır uzunluğuna göre parçalara ayırır.

    Args:
        metin (str): Bölünecek metin.
        satir_uzunlugu (int): Her bir satırın maksimum uzunluğu.

    Returns:
        List[str]: Parçalanmış satırların listesi.
    """
    satirlar = []
    while metin:
        if len(metin) <= satir_uzunlugu:
            satirlar.append(metin)
            break
        
        kesme_noktasi = metin.rfind(' ', 0, satir_uzunlugu)
        if kesme_noktasi == -1:
            kesme_noktasi = satir_uzunlugu
        
        satirlar.append(metin[:kesme_noktasi].strip())
        metin = metin[kesme_noktasi:].strip()
    return satirlar

def metinden_sayilari_cikar(metin: str) -> List[Union[int, float]]:
    """
    Metindeki tüm sayıları (tam sayı veya ondalıklı) bir liste olarak döndürür.

    Args:
        metin (str): Sayıların aranacağı metin.

    Returns:
        List[Union[int, float]]: Bulunan sayıların listesi.
    """
    sayilar = re.findall(r'\b\d+(?:\.\d+)?\b', metin)
    return [float(s) if '.' in s else int(s) for s in sayilar]

def metni_tokenize_et(metin: str) -> List[str]:
    """
    Bir metni kelimelere ve noktalama işaretlerine ayırır.

    Args:
        metin (str): Tokenize edilecek metin.

    Returns:
        List[str]: Tokenlerin listesi.
    """
    return re.findall(r'\b\w+\b|\S', metin)

# ==============================================================================
# Dosya Sistemi ve Veri İşleme
# ==============================================================================
# Dosya okuma, yazma, JSON işlemleri ve diğer veri yapılarıyla ilgili işlevler.

def dosya_oku(dosya_yolu: str) -> str:
    """
    Belirtilen dosya yolundaki metin içeriğini okur ve döndürür.
    Dosya bulunamazsa veya okuma hatası oluşursa boş string döndürür.

    Args:
        dosya_yolu (str): Okunacak dosyanın yolu.

    Returns:
        str: Dosyanın içeriği.
    """
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        Logger.error(f"Dosya bulunamadı: {dosya_yolu}")
    except Exception as e:
        Logger.error(f"Dosya okuma hatası: {e}")
    return ""

def dosya_yaz(dosya_yolu: str, icerik: str) -> bool:
    """
    Verilen içeriği belirtilen dosya yoluna yazar.

    Args:
        dosya_yolu (str): Yazılacak dosyanın yolu.
        icerik (str): Dosyaya yazılacak metin.

    Returns:
        bool: İşlem başarılıysa True, aksi halde False.
    """
    try:
        with open(dosya_yolu, "w", encoding="utf-8") as f:
            f.write(icerik)
        Logger.info(f"İçerik '{dosya_yolu}' dosyasına başarıyla yazıldı.")
        return True
    except Exception as e:
        Logger.error(f"Dosya yazma hatası: {e}")
    return False

def json_dosya_oku(dosya_yolu: str) -> Any:
    """
    Belirtilen JSON dosyasını okur ve Python nesnesine dönüştürür.

    Args:
        dosya_yolu (str): Okunacak JSON dosyasının yolu.

    Returns:
        Any: JSON içeriği veya hata durumunda None.
    """
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        Logger.error(f"JSON dosyası bulunamadı: {dosya_yolu}")
    except json.JSONDecodeError:
        Logger.error(f"JSON dosyasının formatı bozuk: {dosya_yolu}")
    except Exception as e:
        Logger.error(f"JSON okuma hatası: {e}")
    return None

def json_dosya_yaz(dosya_yolu: str, veri: Any) -> bool:
    """
    Bir Python nesnesini belirtilen JSON dosyasına yazar.

    Args:
        dosya_yolu (str): Yazılacak JSON dosyasının yolu.
        veri (Any): Dosyaya yazılacak Python nesnesi.

    Returns:
        bool: İşlem başarılıysa True, aksi halde False.
    """
    try:
        with open(dosya_yolu, "w", encoding="utf-8") as f:
            json.dump(veri, f, indent=4)
        Logger.info(f"Veri '{dosya_yolu}' dosyasına başarıyla yazıldı.")
        return True
    except Exception as e:
        Logger.error(f"JSON yazma hatası: {e}")
    return False

def dosya_mevcut_mu(dosya_yolu: str) -> bool:
    """
    Belirtilen dosya yolunun mevcut olup olmadığını kontrol eder.

    Args:
        dosya_yolu (str): Kontrol edilecek dosyanın yolu.

    Returns:
        bool: Dosya mevcutsa True, aksi halde False.
    """
    return os.path.exists(dosya_yolu) and os.path.isfile(dosya_yolu)

def dizin_olustur(dizin_yolu: str) -> bool:
    """
    Belirtilen dizin yolunu, eğer mevcut değilse, oluşturur.

    Args:
        dizin_yolu (str): Oluşturulacak dizinin yolu.

    Returns:
        bool: İşlem başarılıysa True, aksi halde False.
    """
    try:
        os.makedirs(dizin_yolu, exist_ok=True)
        Logger.info(f"Dizin başarıyla oluşturuldu veya zaten mevcuttu: {dizin_yolu}")
        return True
    except Exception as e:
        Logger.error(f"Dizin oluşturma hatası: {e}")
    return False

def dosya_listele(dizin_yolu: str) -> List[str]:
    """
    Belirtilen dizindeki tüm dosya ve dizinleri listeler.

    Args:
        dizin_yolu (str): Listelenecek dizinin yolu.

    Returns:
        List[str]: İçeriklerin listesi. Hata durumunda boş liste.
    """
    try:
        return os.listdir(dizin_yolu)
    except FileNotFoundError:
        Logger.error(f"Dizin bulunamadı: {dizin_yolu}")
    except Exception as e:
        Logger.error(f"Dizin listeleme hatası: {e}")
    return []

def dosya_uzantisi_al(dosya_adi: str) -> str:
    """
    Bir dosya adının uzantısını döndürür.

    Args:
        dosya_adi (str): Uzantısı alınacak dosyanın adı.

    Returns:
        str: Dosya uzantısı (nokta olmadan).
    """
    return os.path.splitext(dosya_adi)[1].lstrip('.')

# ==============================================================================
# Matematiksel ve Veri Manipülasyonu
# ==============================================================================
# Sayısal veriler üzerinde temel hesaplamalar ve listeler üzerinde işlemler.

def fibonacci_serisi(n: int) -> List[int]:
    """
    İlk n adet Fibonacci sayısını içeren bir liste döndürür.

    Args:
        n (int): Üretilecek Fibonacci sayılarının adedi.

    Returns:
        List[int]: Fibonacci serisi.
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    seri = [0, 1]
    while len(seri) < n:
        seri.append(seri[-1] + seri[-2])
    return seri

def asal_sayi_mi(sayi: int) -> bool:
    """
    Bir sayının asal olup olmadığını kontrol eder.

    Args:
        sayi (int): Kontrol edilecek sayı.

    Returns:
        bool: Sayı asalsa True, aksi halde False.
    """
    if sayi < 2:
        return False
    if sayi == 2:
        return True
    if sayi % 2 == 0:
        return False
    
    for i in range(3, int(math.sqrt(sayi)) + 1, 2):
        if sayi % i == 0:
            return False
    return True

def faktoriyel(n: int) -> int:
    """
    Bir sayının faktöriyelini hesaplar.

    Args:
        n (int): Faktöriyeli hesaplanacak sayı.

    Returns:
        int: Sayının faktöriyeli. Negatif sayılar için 1 döndürür.
    """
    if n < 0:
        return 1
    if n == 0:
        return 1
    
    sonuc = 1
    for i in range(1, n + 1):
        sonuc *= i
    return sonuc

def listeyi_ters_cevir(liste: List[Any]) -> List[Any]:
    """
    Bir listeyi tersine çevirir.

    Args:
        liste (List[Any]): Ters çevrilecek liste.

    Returns:
        List[Any]: Ters çevrilmiş liste.
    """
    return liste[::-1]

def listeden_tekrarli_elemanlari_kaldir(liste: List[Any]) -> List[Any]:
    """
    Bir listedeki tekrarlı elemanları kaldırır ve orijinal sırayı korur.

    Args:
        liste (List[Any]): İşlenecek liste.

    Returns:
        List[Any]: Tekrarlı elemanları kaldırılmış liste.
    """
    gorulenler = set()
    yeni_liste = []
    for eleman in liste:
        if eleman not in gorulenler:
            yeni_liste.append(eleman)
            gorulenler.add(eleman)
    return yeni_liste

# ==============================================================================
# Ağ (Networking) ve Bağlantı İşlevleri
# ==============================================================================
# İnternet bağlantı durumu ve sunucu/istemci iletişimini simüle eden fonksiyonlar.
# Bu fonksiyonlar, gerçek bir ağ ortamında daha karmaşık güvenlik ve hata yönetimi
# gerektirebilir.

def internet_baglantisi_var_mi(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """
    Bir DNS sunucusuna bağlanarak internet bağlantısını kontrol eder.
    Varsayılan: Google DNS.

    Args:
        host (str): Kontrol edilecek sunucu adresi (varsayılan: Google DNS).
        port (int): Sunucunun bağlantı noktası (varsayılan: DNS için 53).
        timeout (int): Bağlantı zaman aşımı (saniye).

    Returns:
        bool: Bağlantı mevcutsa True, aksi halde False.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        Logger.info("İnternet bağlantısı mevcut.")
        return True
    except socket.error as ex:
        Logger.error(f"İnternet bağlantısı yok: {ex}")
    return False

def sunucu_baglantisi_kur(host: str, port: int) -> Union[socket.socket, None]:
    """
    Belirtilen ana bilgisayara (host) ve bağlantı noktasına (port) bir TCP bağlantısı kurar.

    Args:
        host (str): Bağlanılacak ana bilgisayarın IP adresi veya alan adı.
        port (int): Bağlanılacak bağlantı noktası numarası.

    Returns:
        Union[socket.socket, None]: Başarılı olursa bağlantı nesnesi, aksi takdirde None.
    """
    try:
        sock = socket.create_connection((host, port), timeout=5)
        Logger.info(f"{host}:{port} adresine bağlantı başarılı.")
        return sock
    except socket.error as ex:
        Logger.error(f"{host}:{port} adresine bağlanılamadı: {ex}")
    return None

def veri_gonder(soket: socket.socket, veri: str) -> bool:
    """
    Bir soket üzerinden veri gönderir.

    Args:
        soket (socket.socket): Verinin gönderileceği soket nesnesi.
        veri (str): Gönderilecek metin verisi.

    Returns:
        bool: Gönderme başarılıysa True, aksi halde False.
    """
    try:
        soket.sendall(veri.encode('utf-8'))
        return True
    except socket.error as ex:
        Logger.error(f"Veri gönderme hatası: {ex}")
    return False

def veri_al(soket: socket.socket, tampon_boyutu: int = 4096) -> str:
    """
    Bir soketten veri alır.

    Args:
        soket (socket.socket): Verinin alınacağı soket nesnesi.
        tampon_boyutu (int): Alınacak veri paketi boyutu.

    Returns:
        str: Alınan veri veya hata durumunda boş string.
    """
    try:
        veri = soket.recv(tampon_boyutu)
        return veri.decode('utf-8')
    except socket.timeout:
        Logger.warning("Veri alımı zaman aşımına uğradı.")
    except socket.error as ex:
        Logger.error(f"Veri alımı hatası: {ex}")
    return ""

# ==============================================================================
# Yardımcı Fonksiyonlar ve Rastgele İşlemler
# ==============================================================================
# Şifre oluşturma, e-posta doğrulama gibi pratik yardımcı fonksiyonlar.

def rastgele_sifre_olustur(uzunluk: int = 12) -> str:
    """
    Belirtilen uzunlukta rastgele bir alfanümerik şifre oluşturur.
    Şifre, harf (büyük/küçük), rakam ve noktalama işaretlerini içerir.

    Args:
        uzunluk (int): Oluşturulacak şifrenin uzunluğu.

    Returns:
        str: Rastgele oluşturulmuş şifre.
    """
    if uzunluk <= 0:
        return ""
    
    karakterler = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(karakterler) for _ in range(uzunluk))

def eposta_dogrula(eposta: str) -> bool:
    """
    Basit bir regex deseni kullanarak e-posta adresinin geçerliliğini doğrular.
    Bu doğrulama tam bir garanti vermez, sadece temel formatı kontrol eder.

    Args:
        eposta (str): Doğrulanacak e-posta adresi.

    Returns:
        bool: E-posta formatı uygunsa True, aksi halde False.
    """
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return re.search(regex, eposta) is not None

def tarih_formatla(tarih: datetime.datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Bir datetime nesnesini belirtilen formatta stringe dönüştürür.

    Args:
        tarih (datetime.datetime): Formatlanacak tarih nesnesi.
        format_str (str): Tarih formatı stringi.

    Returns:
        str: Formatlanmış tarih stringi.
    """
    try:
        return tarih.strftime(format_str)
    except Exception as e:
        Logger.error(f"Tarih formatlama hatası: {e}")
    return ""

def sure_hesapla(baslangic_zaman: float, bitis_zaman: float) -> str:
    """
    İki zaman damgası arasındaki süreyi okunabilir bir formatta döndürür.

    Args:
        baslangic_zaman (float): Başlangıç zaman damgası (saniye).
        bitis_zaman (float): Bitiş zaman damgası (saniye).

    Returns:
        str: Hesaplanan süre ("X saniye" formatında).
    """
    fark = bitis_zaman - baslangic_zaman
    return f"{fark:.2f} saniye"

# ==============================================================================
# Fonksiyonların Daha Kapsamlı Kullanımı ve Ek İşlevler
# ==============================================================================

# Örnek bir veri seti
dummy_data = {
    "kullanicilar": [
        {"id": 1, "ad": "Ahmet", "soyad": "Yılmaz", "eposta": "ahmet@mail.com"},
        {"id": 2, "ad": "Ayşe", "soyad": "Kara", "eposta": "ayse@mail.com"},
        {"id": 3, "ad": "Mehmet", "soyad": "Demir", "eposta": "mehmet@mail.com"}
    ],
    "urunler": [
        {"id": 101, "ad": "Bilgisayar", "fiyat": 15000, "stok": 50},
        {"id": 102, "ad": "Telefon", "fiyat": 8000, "stok": 120},
        {"id": 103, "ad": "Klavye", "fiyat": 750, "stok": 200}
    ]
}

def kullanici_bul(veri_seti: Dict, kullanici_id: int) -> Union[Dict, None]:
    """
    Verilen veri setinde bir kullanıcıyı ID'sine göre arar.

    Args:
        veri_seti (Dict): Arama yapılacak veri seti.
        kullanici_id (int): Aranan kullanıcının ID'si.

    Returns:
        Union[Dict, None]: Bulunursa kullanıcı sözlüğü, aksi halde None.
    """
    for kullanici in veri_seti.get("kullanicilar", []):
        if kullanici["id"] == kullanici_id:
            return kullanici
    return None

def urun_fiyat_guncelle(veri_seti: Dict, urun_id: int, yeni_fiyat: float) -> bool:
    """
    Bir ürünün fiyatını ID'sine göre günceller.

    Args:
        veri_seti (Dict): Güncelleme yapılacak veri seti.
        urun_id (int): Fiyatı güncellenecek ürünün ID'si.
        yeni_fiyat (float): Ürünün yeni fiyatı.

    Returns:
        bool: Güncelleme başarılıysa True, aksi halde False.
    """
    for urun in veri_seti.get("urunler", []):
        if urun["id"] == urun_id:
            urun["fiyat"] = yeni_fiyat
            return True
    return False

def ortalama_fiyat_hesapla(veri_seti: Dict) -> float:
    """
    Veri setindeki tüm ürünlerin ortalama fiyatını hesaplar.

    Args:
        veri_seti (Dict): Hesaplama yapılacak veri seti.

    Returns:
        float: Ürünlerin ortalama fiyatı.
    """
    urunler = veri_seti.get("urunler", [])
    if not urunler:
        return 0.0
    
    toplam_fiyat = sum(urun["fiyat"] for urun in urunler)
    return toplam_fiyat / len(urunler)

def en_pahali_urun_bul(veri_seti: Dict) -> Union[Dict, None]:
    """
    Veri setindeki en pahalı ürünü bulur.

    Args:
        veri_seti (Dict): Arama yapılacak veri seti.

    Returns:
        Union[Dict, None]: En pahalı ürünün sözlüğü veya None.
    """
    urunler = veri_seti.get("urunler", [])
    if not urunler:
        return None
    
    en_pahali = max(urunler, key=lambda urun: urun["fiyat"])
    return en_pahali

def en_ucuz_urun_bul(veri_seti: Dict) -> Union[Dict, None]:
    """
    Veri setindeki en ucuz ürünü bulur.

    Args:
        veri_seti (Dict): Arama yapılacak veri seti.

    Returns:
        Union[Dict, None]: En ucuz ürünün sözlüğü veya None.
    """
    urunler = veri_seti.get("urunler", [])
    if not urunler:
        return None
    
    en_ucuz = min(urunler, key=lambda urun: urun["fiyat"])
    return en_ucuz

def toplam_stok_hesapla(veri_seti: Dict) -> int:
    """
    Veri setindeki tüm ürünlerin toplam stok sayısını hesaplar.

    Args:
        veri_seti (Dict): Hesaplama yapılacak veri seti.

    Returns:
        int: Toplam stok sayısı.
    """
    return sum(urun["stok"] for urun in veri_seti.get("urunler", []))

# ==============================================================================
# Ek Uygulamalar ve Veri İşleme
# ==============================================================================

def dosya_buyuklugu_getir(dosya_yolu: str) -> int:
    """
    Belirtilen dosyanın boyutunu bayt cinsinden döndürür.
    Dosya yoksa -1 döndürür.

    Args:
        dosya_yolu (str): Boyutu öğrenilecek dosyanın yolu.

    Returns:
        int: Dosya boyutu veya -1.
    """
    try:
        return os.path.getsize(dosya_yolu)
    except FileNotFoundError:
        Logger.error(f"Dosya bulunamadı: {dosya_yolu}")
        return -1
    except Exception as e:
        Logger.error(f"Dosya boyutu getirme hatası: {e}")
        return -1

def gecen_sureyi_goster(fonksiyon):
    """
    Bir fonksiyonun çalışma süresini ölçen bir dekoratör.

    Args:
        fonksiyon (Callable): Süresi ölçülecek fonksiyon.

    Returns:
        Callable: Dekorasyonlu fonksiyon.
    """
    def sarmal_fonksiyon(*args, **kwargs):
        baslangic = time.time()
        sonuc = fonksiyon(*args, **kwargs)
        bitis = time.time()
        Logger.info(f"'{fonksiyon.__name__}' fonksiyonu {bitis - baslangic:.4f} saniyede çalıştı.")
        return sonuc
    return sarmal_fonksiyon

# @gecen_sureyi_goster
# def yavas_calisan_fonksiyon():
#     time.sleep(2)
#     return "İşlem tamamlandı."

def listeyi_karistir(liste: List[Any]) -> None:
    """
    Bir listeyi yerinde (in-place) rastgele karıştırır.

    Args:
        liste (List[Any]): Karıştırılacak liste.
    """
    random.shuffle(liste)

def rastgele_sayi_liste_olustur(adet: int, alt: int, ust: int) -> List[int]:
    """
    Belirtilen aralıkta ve adette rastgele sayılardan oluşan bir liste oluşturur.

    Args:
        adet (int): Oluşturulacak sayı adedi.
        alt (int): Alt sınır.
        ust (int): Üst sınır.

    Returns:
        List[int]: Rastgele sayılar listesi.
    """
    return [random.randint(alt, ust) for _ in range(adet)]

def sistem_bilgisini_getir() -> Dict[str, str]:
    """
    Sistemle ilgili temel bilgileri bir sözlük olarak döndürür.

    Returns:
        Dict[str, str]: Sistem bilgileri.
    """
    return {
        "platform": sys.platform,
        "python_versiyon": sys.version,
        "isletim_sistemi": os.name,
        "aktif_dizin": os.getcwd()
    }

def buyuk_sayi_formatla(sayi: int) -> str:
    """
    Büyük sayıları okunabilir bir formata dönüştürür (örneğin: 1.2M, 1.5K).

    Args:
        sayi (int): Formatlanacak sayı.

    Returns:
        str: Formatlanmış sayı stringi.
    """
    if sayi >= 1_000_000_000:
        return f"{sayi / 1_000_000_000:.1f}B"
    elif sayi >= 1_000_000:
        return f"{sayi / 1_000_000:.1f}M"
    elif sayi >= 1_000:
        return f"{sayi / 1_000:.1f}K"
    else:
        return str(sayi)

def metin_tersine_cevir(metin: str) -> str:
    """
    Verilen metni tersine çevirir.

    Args:
        metin (str): Ters çevrilecek metin.

    Returns:
        str: Tersine çevrilmiş metin.
    """
    return metin[::-1]

def kelimeleri_ayir(metin: str) -> List[str]:
    """
    Bir metni kelimelere ayırır ve bir liste olarak döndürür.

    Args:
        metin (str): Kelimelere ayrılacak metin.

    Returns:
        List[str]: Kelimelerin listesi.
    """
    return re.findall(r'\b\w+\b', metin)

def en_sik_kullanilan_kelimeyi_bul(metin: str) -> Union[Tuple[str, int], None]:
    """
    Bir metindeki en sık kullanılan kelimeyi ve kullanım sayısını bulur.

    Args:
        metin (str): Analiz edilecek metin.

    Returns:
        Union[Tuple[str, int], None]: En sık kullanılan kelime ve sayısının
                                       (kelime, sayı) olarak bir tuple'ı,
                                       metin boşsa None.
    """
    kelime_frekanslari = kelime_sayaci(metin)
    if not kelime_frekanslari:
        return None
    
    en_sik_kelime = max(kelime_frekanslari, key=kelime_frekanslari.get)
    return (en_sik_kelime, kelime_frekanslari[en_sik_kelime])

def metni_sifrele(metin: str, anahtar: int) -> str:
    """
    Bir metni basit bir sezarsal şifreleme ile şifreler.

    Args:
        metin (str): Şifrelenecek metin.
        anahtar (int): Şifreleme anahtarı.

    Returns:
        str: Şifrelenmiş metin.
    """
    sifrelenmis_metin = ""
    for karakter in metin:
        if 'a' <= karakter.lower() <= 'z':
            start = ord('a') if 'a' <= karakter <= 'z' else ord('A')
            offset = (ord(karakter) - start + anahtar) % 26
            sifrelenmis_metin += chr(start + offset)
        else:
            sifrelenmis_metin += karakter
    return sifrelenmis_metin

def metni_sifreyi_coz(metin: str, anahtar: int) -> str:
    """
    Basit bir sezarsal şifrelemeden metni çözer.

    Args:
        metin (str): Şifresi çözülecek metin.
        anahtar (int): Şifreleme anahtarı.

    Returns:
        str: Şifresi çözülmüş metin.
    """
    return metni_sifrele(metin, -anahtar)

def is_palindrome(metin: str) -> bool:
    """
    Verilen metnin palindrom (tersiyle aynı) olup olmadığını kontrol eder.
    Büyük/küçük harf ve noktalama işaretlerini göz ardı eder.

    Args:
        metin (str): Kontrol edilecek metin.

    Returns:
        bool: Metin palindromsa True, aksi halde False.
    """
    temizlenmis_metin = re.sub(r'[\W_]', '', metin).lower()
    return temizlenmis_metin == temizlenmis_metin[::-1]

def metnin_ozetini_cikar(metin: str, kelime_sayisi: int) -> str:
    """
    Bir metnin ilk birkaç cümlesinden bir özet çıkarır.

    Args:
        metin (str): Özetlenecek metin.
        kelime_sayisi (int): Özette bulunacak yaklaşık kelime sayısı.

    Returns:
        str: Metnin özeti.
    """
    cumleler = re.split(r'(?<=[.!?])\s+', metin)
    ozet_cumleler = []
    toplam_kelime = 0
    for cumle in cumleler:
        kelimeler = cumle.split()
        toplam_kelime += len(kelimeler)
        ozet_cumleler.append(cumle)
        if toplam_kelime >= kelime_sayisi:
            break
    
    ozet = " ".join(ozet_cumleler)
    if ozet and not ozet.endswith(('.', '!', '?')):
        ozet += "."
    return ozet

def dosya_temizle(dosya_yolu: str) -> bool:
    """
    Bir dosyanın içeriğini siler.

    Args:
        dosya_yolu (str): İçeriği silinecek dosya.

    Returns:
        bool: İşlem başarılıysa True, aksi halde False.
    """
    try:
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            f.write('')
        Logger.info(f"Dosya içeriği temizlendi: {dosya_yolu}")
        return True
    except FileNotFoundError:
        Logger.error(f"Dosya bulunamadı: {dosya_yolu}")
    except Exception as e:
        Logger.error(f"Dosya temizleme hatası: {e}")
    return False

def dosya_kopyala(kaynak: str, hedef: str) -> bool:
    """
    Bir dosyayı bir yerden başka bir yere kopyalar.

    Args:
        kaynak (str): Kopyalanacak dosya.
        hedef (str): Dosyanın kopyalanacağı yer.

    Returns:
        bool: Kopyalama başarılıysa True, aksi halde False.
    """
    try:
        shutil.copy2(kaynak, hedef)
        Logger.info(f"Dosya kopyalandı: {kaynak} -> {hedef}")
        return True
    except FileNotFoundError:
        Logger.error("Dosya bulunamadı.")
    except Exception as e:
        Logger.error(f"Dosya kopyalama hatası: {e}")
    return False