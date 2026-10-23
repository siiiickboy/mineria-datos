"""Pruebas del RF1. Ejecutar desde la raíz: pytest"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analisis.validacion import validar_csv  # noqa: E402


def escribir(tmp_path, nombre, contenido: bytes):
    ruta = tmp_path / nombre
    ruta.write_bytes(contenido)
    return str(ruta)


def test_csv_con_coma_utf8(tmp_path):
    r = validar_csv(escribir(tmp_path, "a.csv", "nombre,edad\nAna,20\nLuis,30\n".encode("utf-8")))
    assert r.valido
    assert r.separador == ","
    assert r.dataframe.shape == (2, 2)


def test_csv_punto_y_coma_latin1(tmp_path):
    contenido = "ciudad;año\nConcepción;2020\nTalca;2021\n".encode("latin-1")
    r = validar_csv(escribir(tmp_path, "b.csv", contenido))
    assert r.valido
    assert r.separador == ";"
    assert r.codificacion in ("cp1252", "latin-1")
    assert "año" in r.dataframe.columns


def test_tabulacion(tmp_path):
    r = validar_csv(escribir(tmp_path, "c.csv", b"x\ty\n1\t2\n3\t4\n"))
    assert r.valido and r.separador == "\t"


def test_extension_incorrecta(tmp_path):
    r = validar_csv(escribir(tmp_path, "d.txt", b"a,b\n1,2\n"))
    assert not r.valido


def test_archivo_vacio(tmp_path):
    r = validar_csv(escribir(tmp_path, "e.csv", b""))
    assert not r.valido


def test_archivo_binario(tmp_path):
    r = validar_csv(escribir(tmp_path, "f.csv", b"PK\x03\x04\x00\x00binario"))
    assert not r.valido


def test_solo_encabezado(tmp_path):
    r = validar_csv(escribir(tmp_path, "g.csv", b"a,b,c\n"))
    assert not r.valido


def test_filas_con_columnas_de_mas(tmp_path):
    r = validar_csv(escribir(tmp_path, "h.csv", b"a,b\n1,2\n3,4,5\n6,7\n"))
    assert r.valido
    assert len(r.dataframe) == 2
    assert r.advertencias


def test_vista_previa(tmp_path):
    r = validar_csv(escribir(tmp_path, "i.csv", b"a,b\n1,\n1,\n2,3\n"))
    info = r.resumen()
    assert info["total_nulos"] == 2
    assert info["duplicados"] == 1
    assert info["primeras_filas"][0][1] is None
