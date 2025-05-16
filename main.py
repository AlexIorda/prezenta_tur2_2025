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

tur1_2025 = listeaza_csv_din_folder('./data_total/04052025')
tur2_2025 = listeaza_csv_din_folder('./data_total/18052025')

# Total

votanti_04052025 = []
timp_04052025 = [path.split('.')[0].split('_')[2] for path in tur1_2025]

for path in tur1_2025:
    df = pl.read_csv(f'./data_total/04052025/{path}')
    votanti_04052025.append(df['LT'].sum())

votanti_18052025 = []
timp_18052025 = [path.split('.')[0].split('_')[2] for path in tur2_2025]

for path in tur2_2025:
    df = pl.read_csv(f'./data_total/18052025/{path}')
    votanti_18052025.append(df['LT'].sum())

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

fig, ax = plt.subplots(figsize=(20, 10))

# Plotezi liniile complet
ax.plot(votanti_04052025, label='Tur 1 - 2025', color='blue')
ax.plot(votanti_18052025, label='Tur 2 - 2025', color='orange')

# Setezi xticks pentru întreaga lungime a axei X (maxim lungimea turului 1)
ax.set_xticks(range(len(timp_04052025)))
ax.set_xticklabels(timp_04052025, rotation=45)

max_v = max(max(votanti_04052025), max(votanti_18052025))
yticks = np.arange(0, max_v + 500_000, 500_000)
ax.set_yticks(yticks)

def mil_formatter(x, pos):
    val = x / 1_000_000
    if val == int(val):
        return f"{int(val)} mil"
    else:
        return f"{val:.1f} mil"

ax.yaxis.set_major_formatter(FuncFormatter(mil_formatter))

ax.set_xlabel("Ora")
ax.set_ylabel("Număr votanți")
ax.set_title("Prezența la vot - 04 vs 18 Mai 2025")
ax.legend()
ax.grid(True)

# Calculezi procentajele doar pe intervalul comun (min_len)
min_len = min(len(votanti_04052025), len(votanti_18052025))
vot1_trim = np.array(votanti_04052025[:min_len])
vot2_trim = np.array(votanti_18052025[:min_len])
timp_trim = timp_04052025[:min_len]

procent = (vot2_trim - vot1_trim) / vot1_trim * 100

# Afișezi procentajele doar pentru punctele din intervalul comun
for i, (x, y, p) in enumerate(zip(range(min_len), vot2_trim, procent)):
    ax.text(x, y, f"{p:.0f}%", color='darkorange', fontsize=9, ha='center', va='bottom')

plt.tight_layout()
plt.savefig('votanti_2025.png', dpi=300, bbox_inches='tight')
plt.clf()

# Diaspora

# diaspora = 'SR'

votanti_04052025 = []
timp_04052025 = [path.split('.')[0].split('_')[2] for path in tur1_2025]

for path in tur1_2025:
    df = pl.read_csv(f'./data_total/04052025/{path}')
    votanti_04052025.append(df.filter(pl.col('Judet') == 'SR')['LT'].sum())

votanti_18052025 = []
timp_18052025 = [path.split('.')[0].split('_')[2] for path in tur2_2025]

for path in tur2_2025:
    df = pl.read_csv(f'./data_total/18052025/{path}')
    votanti_18052025.append(df.filter(pl.col('Judet') == 'SR')['LT'].sum())

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

fig, ax = plt.subplots(figsize=(20, 10))

# Plotezi liniile complet
ax.plot(votanti_04052025, label='Tur 1 - 2025', color='blue')
ax.plot(votanti_18052025, label='Tur 2 - 2025', color='orange')

# Setezi xticks pentru întreaga lungime a axei X (maxim lungimea turului 1)
ax.set_xticks(range(len(timp_04052025)))
ax.set_xticklabels(timp_04052025, rotation=45)

max_v = max(max(votanti_04052025), max(votanti_18052025))
yticks = np.arange(0, max_v + 500_000, 500_000)
ax.set_yticks(yticks)

def mil_formatter(x, pos):
    val = x / 1_000_000
    if val == int(val):
        return f"{int(val)} mil"
    else:
        return f"{val:.1f} mil"

ax.yaxis.set_major_formatter(FuncFormatter(mil_formatter))

ax.set_xlabel("Ora")
ax.set_ylabel("Număr votanți")
ax.set_title("Prezența la vot in Diaspora - 04 vs 18 Mai 2025")
ax.legend()
ax.grid(True)

# Calculezi procentajele doar pe intervalul comun (min_len)
min_len = min(len(votanti_04052025), len(votanti_18052025))
vot1_trim = np.array(votanti_04052025[:min_len])
vot2_trim = np.array(votanti_18052025[:min_len])
timp_trim = timp_04052025[:min_len]

procent = (vot2_trim - vot1_trim) / vot1_trim * 100

# Afișezi procentajele doar pentru punctele din intervalul comun
for i, (x, y, p) in enumerate(zip(range(min_len), vot2_trim, procent)):
    ax.text(x, y, f"{p:.0f}%", color='darkorange', fontsize=9, ha='center', va='bottom')

plt.tight_layout()
plt.savefig('votanti_diaspora_2025.png', dpi=300, bbox_inches='tight')
plt.clf()

# Romania

# diaspora = 'SR'

votanti_04052025 = []
timp_04052025 = [path.split('.')[0].split('_')[2] for path in tur1_2025]

for path in tur1_2025:
    df = pl.read_csv(f'./data_total/04052025/{path}')
    votanti_04052025.append(df.filter(pl.col('Judet') != 'SR')['LT'].sum())

while len(votanti_04052025) > 0 and votanti_04052025[0] == 0:
    votanti_04052025.pop(0)
    timp_04052025.pop(0)

votanti_18052025 = []
timp_18052025 = [path.split('.')[0].split('_')[2] for path in tur2_2025]

for path in tur2_2025:
    df = pl.read_csv(f'./data_total/18052025/{path}')
    votanti_18052025.append(df.filter(pl.col('Judet') != 'SR')['LT'].sum())

while len(votanti_18052025) > 0 and votanti_18052025[0] == 0:
    votanti_18052025.pop(0)
    timp_18052025.pop(0)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

fig, ax = plt.subplots(figsize=(20, 10))

# Plotezi liniile complet
ax.plot(votanti_04052025, label='Tur 1 - 2025', color='blue')
ax.plot(votanti_18052025, label='Tur 2 - 2025', color='orange')

# Setezi xticks pentru întreaga lungime a axei X (maxim lungimea turului 1)
ax.set_xticks(range(len(timp_04052025)))
ax.set_xticklabels(timp_04052025, rotation=45)

all_vals = [v for v in votanti_04052025 + votanti_18052025 if v is not None]
max_v = max(all_vals) if all_vals else 0
yticks = np.arange(0, max_v + 500_000, 500_000)
ax.set_yticks(yticks)

def mil_formatter(x, pos):
    val = x / 1_000_000
    if val == int(val):
        return f"{int(val)} mil"
    else:
        return f"{val:.1f} mil"

ax.yaxis.set_major_formatter(FuncFormatter(mil_formatter))

ax.set_xlabel("Ora")
ax.set_ylabel("Număr votanți")
ax.set_title("Prezența la vot in Romania - 04 vs 18 Mai 2025")
ax.legend()
ax.grid(True)

# Calculezi procentajele doar pe intervalul comun (min_len)
min_len = min(len(votanti_04052025), len(votanti_18052025))
vot1_trim = np.array(votanti_04052025[:min_len])
vot2_trim = np.array(votanti_18052025[:min_len])
timp_trim = timp_04052025[:min_len]

procent = (vot2_trim - vot1_trim) / vot1_trim * 100

# Afișezi procentajele doar pentru punctele din intervalul comun
for i, (x, y, p) in enumerate(zip(range(min_len), vot2_trim, procent)):
    ax.text(x, y, f"{p:.0f}%", color='darkorange', fontsize=9, ha='center', va='bottom')

plt.tight_layout()
plt.savefig('votanti_romania_2025.png', dpi=300, bbox_inches='tight')
plt.clf()
