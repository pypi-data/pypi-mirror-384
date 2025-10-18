import math
def mutlak(sayi = int): return abs(sayi)
def topla(sayi,sayie): return sayi + sayie
def cikart(sayi,sayie): return sayi - sayie
def carp(sayi,sayie): return sayi * sayie
def bol(sayi,sayie):
    try:
        sayi / sayie
    except ZeroDivisionError:
        return ZeroDivisionError
    except: # zerodivisiondan başka gelirse diye yedek
        return None
    return sayi / sayie
def negatif(sayi): return 0 - sayi
def kendiylecarp(sayi): return sayi * sayi
def kendiyletopla(sayi): return sayi + sayi
def pi(): return "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"
def sin(sayi):return math.sin(sayi)
def sonsuzluksimge(): return "∞"
