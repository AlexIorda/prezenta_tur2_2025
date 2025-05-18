import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from datetime import timedelta, datetime
import os
import matplotlib
matplotlib.use('Agg')

def e_data_valida(data_str, ora_str):
    dt_str = f"{data_str} {ora_str.replace('-', ':')}"
    dt_format = "%Y-%m-%d %H:%M"

    dt = datetime.strptime(dt_str, dt_format)
    acum = datetime.now() + timedelta(hours=2)

    return dt <= acum


def descarca_csv_ora(scrutin_str, data_str, ora_str):
    if not e_data_valida(data_str, ora_str):
        print(f"Sar peste data {data_str} ora {ora_str} pentru că este în viitor.")
        return False

    download_dir = os.path.abspath(f"./data_total/{scrutin_str}/")
    options = Options()
    options.headless = True
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    base_url = f"https://prezenta.roaep.ro/prezidentiale{scrutin_str}//data/csv/simpv/"
    filename = f"presence_{data_str}_{ora_str}.csv"
    url = base_url + filename

    if os.path.exists(os.path.join(download_dir, filename)):
        print(f"Fișierul {filename} există deja. Sar peste descărcare.")
        return True
    
    driver = webdriver.Chrome(options=options)
    # Enable downloads via DevTools protocol
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })

    print(f"Descarc: {url}")
    try:
        driver.get(url)
        time.sleep(6)  # Așteaptă descărcarea fișierului
    except Exception as e:
        print(f"Eroare la încărcarea URL-ului {url}: {e}")
    finally:
        driver.quit()
        return True

# Scrutinul 2025 tur 2

scrutin = "18052025"
date = ['2025-05-16', '2025-05-17', '2025-05-18']
ore = [f"{h:02d}-00" for h in range(8, 24)]

timpi = []
for data in date:
    for ora in ore:
        timpi.append((data, ora))

for data, ora in timpi[:-2]:
    if not descarca_csv_ora(scrutin, data, ora):
        break
    print(f"Fișierul pentru data {data} ora {ora} a fost descărcat.")

# Scrutinul 2025 tur 1

scrutin = "04052025"
date = ['2025-05-02', '2025-05-03', '2025-05-04']
ore = [f"{h:02d}-00" for h in range(8, 24)]

timpi = []
for data in date:
    for ora in ore:
        timpi.append((data, ora))

for data, ora in timpi[:-2]:
    if not descarca_csv_ora(scrutin, data, ora):
        break
    print(f"Fișierul pentru data {data} ora {ora} a fost descărcat.")

# Analiza
import os
import polars as pl

def listeaza_csv_din_folder(folder_path):
    """
    Returnează o listă cu toate fișierele .csv dintr-un folder dat.

    :param folder_path: Calea către folderul de interes
    :return: Listă de fișiere .csv
    """
    return [
        f for f in os.listdir(folder_path)
        if f.endswith('.csv') and os.path.isfile(os.path.join(folder_path, f))
    ]

import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pathlib import Path

def extract_time(paths):
    return [path.split('.')[0].split('_')[2] for path in paths]

def read_votes(paths, date_folder, judet=None, uat=None, localitate=None):
    results = []
    for path in paths:
        df = pl.read_csv(f'./data_total/{date_folder}/{path}')
        if judet:
            if judet == 'RO':
                df = df.filter(pl.col('Judet') != 'SR')
            else:
                df = df.filter(pl.col('Judet') == judet)
        if uat:
            df = df.filter(pl.col('UAT') == uat)
        if judet == 'SR' and uat is None:
            df = df  # Diaspora
        elif judet != 'SR' and judet is not None:
            df = df.filter(pl.col('Judet') != 'SR')
        if localitate:
            df = df.filter(pl.col('Localitate').str.contains(localitate))
        results.append(df['LT'].sum())
    return results

def mil_formatter(x, pos):
    val = x / 1_000_000
    return f"{val:.2f} mil" if val % 1 else f"{int(val)} mil"

def plot_votes(timp, vot1, vot2, titlu, filename, step_y=500_000):

    begin_x = 0
    while begin_x < len(vot1) and begin_x < len(vot2) and vot1[begin_x] == vot2[begin_x] == 0:
        begin_x += 1

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.plot(vot1[begin_x:], label='Tur 1 - 2025', color='blue')
    ax.plot(vot2[begin_x:], label='Tur 2 - 2025', color='orange')

    ax.set_xticks(range(len(timp[begin_x:])))
    ax.set_xticklabels(timp[begin_x:], rotation=45)

    all_vals = [v for v in vot1[begin_x:] + vot2[begin_x:] if v is not None]
    max_v = max(all_vals) if all_vals else 0
    ax.set_yticks(np.arange(0, max_v + step_y, step_y))
    ax.yaxis.set_major_formatter(FuncFormatter(mil_formatter))

    ax.set_xlabel("Ora")
    ax.set_ylabel("Număr votanți")
    ax.set_title(titlu)
    ax.legend()
    ax.grid(True)

    # Calculezi procentajele doar pe intervalul comun (min_len)
    min_len = min(len(vot1[begin_x:]), len(vot2[begin_x:]))
    vot1_trim = np.array(vot1[begin_x:begin_x+min_len])
    vot2_trim = np.array(vot2[begin_x:begin_x+min_len])
    procent = (vot2_trim - vot1_trim) / (vot1_trim + 0.000001) * 100

    # Afișezi procentajele doar pentru punctele din intervalul comun
    for i, (x, y, p) in enumerate(zip(range(min_len), vot2_trim, procent)):
        ax.text(x, y, f"{p:.0f}%", color='darkorange', fontsize=9, ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

# === MAIN ===

tur1_2025 = listeaza_csv_din_folder('./data_total/04052025')
tur2_2025 = listeaza_csv_din_folder('./data_total/18052025')
timp = extract_time(tur1_2025)

# 1. Total
vot1_total = read_votes(tur1_2025, '04052025')
vot2_total = read_votes(tur2_2025, '18052025')
plot_votes(timp, vot1_total, vot2_total, "Prezența la vot - 04 vs 18 Mai 2025", "votanti_2025.png")

# 2. Diaspora
vot1_diaspora = read_votes(tur1_2025, '04052025', judet='SR')
vot2_diaspora = read_votes(tur2_2025, '18052025', judet='SR')
plot_votes(timp, vot1_diaspora, vot2_diaspora, "Prezența la vot în Diaspora - 04 vs 18 Mai 2025", "votanti_diaspora_2025.png", step_y=100_000)

# 3. România (fără diaspora)
vot1_ro = read_votes(tur1_2025, '04052025', judet='RO')  # intern
vot2_ro = read_votes(tur2_2025, '18052025', judet='RO')
plot_votes(timp, vot1_ro, vot2_ro, "Prezența la vot în România - 04 vs 18 Mai 2025", "votanti_romania_2025.png")

# 4. Moldova
vot1_md = read_votes(tur1_2025, '04052025', judet='SR', uat="REPUBLICA MOLDOVA")
vot2_md = read_votes(tur2_2025, '18052025', judet='SR', uat="REPUBLICA MOLDOVA")
plot_votes(timp, vot1_md, vot2_md, "Prezența la vot în Moldova - 04 vs 18 Mai 2025", "votanti_moldova_2025.png", step_y=10_000)

# 5. UK
vot1_uk = read_votes(tur1_2025, '04052025', judet='SR', uat="REGATUL UNIT AL MARII BRITANII ȘI AL IRLANDEI DE NORD")
vot2_uk = read_votes(tur2_2025, '18052025', judet='SR', uat="REGATUL UNIT AL MARII BRITANII ȘI AL IRLANDEI DE NORD")
plot_votes(timp, vot1_uk, vot2_uk, "Prezența la vot în UK - 04 vs 18 Mai 2025", "votanti_uk_2025.png", step_y=10_000)

# 6. Italia
vot1_it = read_votes(tur1_2025, '04052025', judet='SR', uat="ITALIA")
vot2_it = read_votes(tur2_2025, '18052025', judet='SR', uat="ITALIA")
plot_votes(timp, vot1_it, vot2_it, "Prezența la vot în Italia - 04 vs 18 Mai 2025", "votanti_italia_2025.png", step_y=10_000)

# 7. Spania
vot1_es = read_votes(tur1_2025, '04052025', judet='SR', uat="SPANIA")
vot2_es = read_votes(tur2_2025, '18052025', judet='SR', uat="SPANIA")
plot_votes(timp, vot1_es, vot2_es, "Prezența la vot în Spania - 04 vs 18 Mai 2025", "votanti_spania_2025.png", step_y=10_000)

# 8. Germania
vot1_de = read_votes(tur1_2025, '04052025', judet='SR', uat="GERMANIA")
vot2_de = read_votes(tur2_2025, '18052025', judet='SR', uat="GERMANIA")
plot_votes(timp, vot1_de, vot2_de, "Prezența la vot în Germania - 04 vs 18 Mai 2025", "votanti_germania_2025.png", step_y=10_000)

# 9. Franța
vot1_fr = read_votes(tur1_2025, '04052025', judet='SR', uat="FRANȚA")
vot2_fr = read_votes(tur2_2025, '18052025', judet='SR', uat="FRANȚA")
plot_votes(timp, vot1_fr, vot2_fr, "Prezența la vot în Franța - 04 vs 18 Mai 2025", "votanti_franta_2025.png", step_y=10_000)

# 10. Bucuresti
vot1_fr = read_votes(tur1_2025, '04052025', judet='B', localitate="BUCUREŞTI SECTOR")
vot2_fr = read_votes(tur2_2025, '18052025', judet='B', localitate="BUCUREŞTI SECTOR")
plot_votes(timp, vot1_fr, vot2_fr, "Prezența la vot în Bucuresti - 04 vs 18 Mai 2025", "votanti_franta_2025.png", step_y=10_000)

# 11. Cluj
vot1_fr = read_votes(tur1_2025, '04052025', judet='CJ', localitate="CLUJ-NAPOCA")
vot2_fr = read_votes(tur2_2025, '18052025', judet='CJ', localitate="CLUJ-NAPOCA")
plot_votes(timp, vot1_fr, vot2_fr, "Prezența la vot în Cluj-Napoca - 04 vs 18 Mai 2025", "votanti_cluj_2025.png", step_y=10_000)

# 12. Timisoara
vot1_fr = read_votes(tur1_2025, '04052025', judet='TM', localitate="TIMIŞOARA")
vot2_fr = read_votes(tur2_2025, '18052025', judet='TM', localitate="TIMIŞOARA")
plot_votes(timp, vot1_fr, vot2_fr, "Prezența la vot în Timisoara - 04 vs 18 Mai 2025", "votanti_timisoara_2025.png", step_y=10_000)

# 13. Iasi
vot1_fr = read_votes(tur1_2025, '04052025', judet='IS', localitate="IAŞI")
vot2_fr = read_votes(tur2_2025, '18052025', judet='IS', localitate="IAŞI")
plot_votes(timp, vot1_fr, vot2_fr, "Prezența la vot în Iasi - 04 vs 18 Mai 2025", "votanti_iasi_2025.png", step_y=10_000)

# 14. Brasov
vot1_fr = read_votes(tur1_2025, '04052025', judet='BV', localitate="BRAŞOV")
vot2_fr = read_votes(tur2_2025, '18052025', judet='BV', localitate="BRAŞOV")
plot_votes(timp, vot1_fr, vot2_fr, "Prezența la vot în Brasov - 04 vs 18 Mai 2025", "votanti_brasov_2025.png", step_y=10_000)

# 15. Sibiu
vot1_fr = read_votes(tur1_2025, '04052025', judet='SB', localitate="SIBIU")
vot2_fr = read_votes(tur2_2025, '18052025', judet='SB', localitate="SIBIU")
plot_votes(timp, vot1_fr, vot2_fr, "Prezența la vot în Sibiu - 04 vs 18 Mai 2025", "votanti_sibiu_2025.png", step_y=10_000)