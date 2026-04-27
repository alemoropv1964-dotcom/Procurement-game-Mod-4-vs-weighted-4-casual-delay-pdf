import streamlit as st
import random
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------
# TITOLO E INTRODUZIONE
# ---------------------------------------------------------
st.title("🔄 Simulatore di Procurement – Mod(4) + Modello Pesato + Modelli di Ritardo")
st.write("""
Simulatore unico con tre modalità selezionabili:

### 🔵 Modalità 1 — Mod(4) puro
Assegnazione deterministica con fallback ciclico:
F1 → F2 → F3 → F4 → F1

### 🟣 Modalità 2 — Modello Pesato
Scelta ottimizzata basata su penalità:
penalità = w_LT * LT_eff + w_C * Costo_totale

### 🏁 Modalità 3 — Competizione
Confronto statistico tra Mod(4) e Modello Pesato su n tentativi.

Entrambe le modalità usano 4 modelli di ritardo:
1) Bernoulliano  
2) Proporzionale  
3) Esponenziale  
4) Con memoria  
""")

# ---------------------------------------------------------
# SELETTORE DI MODALITÀ
# ---------------------------------------------------------
modalita = st.radio(
    "Seleziona la modalità di simulazione:",
    ["Mod(4) puro", "Modello Pesato", "Competizione"]
)

# ---------------------------------------------------------
# PARAMETRI FORNITORI
# ---------------------------------------------------------
st.header("📦 Parametri dei 4 Fornitori")

MODELLI_RITARDO = [
    "Bernoulliano",
    "Proporzionale",
    "Esponenziale",
    "Con memoria"
]

fornitori = []
for i in range(4):
    st.subheader(f"Fornitore F{i+1}")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        costo = st.number_input(f"Costo F{i+1}", 1, 100, 10)

    with col2:
        lt = st.number_input(f"Lead Time F{i+1}", 1, 60, 5)

    with col3:
        prob = st.slider(f"Prob. Ritardo F{i+1}", 0.0, 1.0, 0.10)

    with col4:
        cap = st.number_input(f"Capacità F{i+1}", 1, 500, 100)

    with col5:
        modello = st.selectbox(
            f"Modello ritardo F{i+1}",
            MODELLI_RITARDO,
            index=0
        )

    fornitori.append({
        "costo": costo,
        "lead_time": lt,
        "prob_ritardo": prob,
        "capacita": cap,
        "modello_ritardo": modello
    })

# ---------------------------------------------------------
# PARAMETRI PROCUREMENT
# ---------------------------------------------------------
st.header("📝 Parametri Procurement")

colA, colB, colC, colD = st.columns(4)

with colA:
    q1 = st.number_input("Ordine 1", 0, 500, 50)
with colB:
    q2 = st.number_input("Ordine 2", 0, 500, 40)
with colC:
    q3 = st.number_input("Ordine 3", 0, 500, 70)
with colD:
    q4 = st.number_input("Ordine 4", 0, 500, 30)

ordini = [q1, q2, q3, q4]

lead_time_max = st.number_input("Lead Time massimo accettabile", 1, 60, 10)

# ---------------------------------------------------------
# PESI PER LA FUNZIONE DI SCELTA (solo per modello pesato / competizione)
# ---------------------------------------------------------
if modalita in ["Modello Pesato", "Competizione"]:
    st.header("⚖️ Pesi per la funzione di scelta (somma = 1)")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        peso_lt = st.slider("Peso Lead Time", 0.0, 1.0, 0.5)

    with col_p2:
        peso_costo = 1 - peso_lt

    st.write(f"Peso costo totale = **{peso_costo:.2f}**")
else:
    peso_lt = 0
    peso_costo = 0

# ---------------------------------------------------------
# FUNZIONI
# ---------------------------------------------------------
def ciclo_mod4(i):
    return (i + 1) % 4

def penalita(lead_time, costo_totale, w_lt, w_c):
    return w_lt * lead_time + w_c * costo_totale

def calcola_lt_eff(f, last_ritardo_flag):
    base_lt = f["lead_time"]
    p = f["prob_ritardo"]
    modello = f["modello_ritardo"]

    lt_eff = base_lt
    ritardo = False
    nuovo_flag = last_ritardo_flag

    # 1) Bernoulliano
    if modello == "Bernoulliano":
        if random.random() < p:
            ritardo = True
            lt_eff = base_lt * (1 + random.random())
        nuovo_flag = ritardo

    # 2) Proporzionale
    elif modello == "Proporzionale":
        fattore = 1 + p * random.random()
        lt_eff = base_lt * fattore
        ritardo = fattore > 1
        nuovo_flag = ritardo

    # 3) Esponenziale
    elif modello == "Esponenziale":
        scale = max(base_lt * p, 0.1)
        extra = np.random.exponential(scale=scale)
        lt_eff = base_lt + extra
        ritardo = extra > 0
        nuovo_flag = ritardo

    # 4) Con memoria
    elif modello == "Con memoria":
        delta = 0.2
        p_eff = p + (delta if last_ritardo_flag else -delta)
        p_eff = max(0.0, min(1.0, p_eff))
        if random.random() < p_eff:
            ritardo = True
            lt_eff = base_lt * (1 + random.random())
        nuovo_flag = ritardo

    return lt_eff, ritardo, nuovo_flag

# ---------------------------------------------------------
# MODALITÀ COMPETIZIONE — VERSIONE DEFINITIVA
# ---------------------------------------------------------
if modalita == "Competizione":

    st.header("🏁 Competizione Mod(4) vs Modello Pesato")

    # Numero tentativi
    n_tentativi = st.number_input(
        "Numero tentativi (minimo 10)",
        min_value=10,
        max_value=500,
        value=50
    )

    # Toggle tie-breaking
    criterio = st.selectbox(
        "Criterio tie-breaking (penalità uguali):",
        [
            "A) Indice fornitore (deterministico)",
            "B) Costo minore",
            "C) Lead time effettivo minore",
            "D) Casuale (seed controllato)"
        ]
    )

    # Seed per criterio D
    if criterio == "D) Casuale (seed controllato)":
        random.seed(12345)

    st.write("Ogni tentativo usa gli stessi ordini e gli stessi fornitori.")

    # ---------------------------------------------------------
    # FUNZIONE TIE-BREAKING
    # ---------------------------------------------------------
    def tie_break(lista):
        """
        lista = [(idx, penalità, lt_eff, costo_totale)]
        ritorna lista ordinata secondo il criterio scelto
        """

        if criterio.startswith("A"):
            # Ordina per penalità, poi per indice fornitore
            return sorted(lista, key=lambda x: (x[1], x[0]))

        elif criterio.startswith("B"):
            # Ordina per penalità, poi per costo totale
            return sorted(lista, key=lambda x: (x[1], x[3]))

        elif criterio.startswith("C"):
            # Ordina per penalità, poi per lead time effettivo
            return sorted(lista, key=lambda x: (x[1], x[2]))

        elif criterio.startswith("D"):
            # Ordina per penalità, poi casuale
            penalita_min = min(x[1] for x in lista)
            pari = [x for x in lista if x[1] == penalita_min]
            altri = [x for x in lista if x[1] != penalita_min]
            random.shuffle(pari)
            return pari + sorted(altri, key=lambda x: x[1])

    # ---------------------------------------------------------
    # AVVIO COMPETIZIONE
    # ---------------------------------------------------------
    if st.button("Avvia Competizione"):

        vittorie_mod4 = [0, 0, 0, 0]
        vittorie_pesato = [0, 0, 0, 0]

        quantita_mod4 = [0, 0, 0, 0]
        quantita_pesato = [0, 0, 0, 0]

        secondi_mod4 = [0, 0, 0, 0]
        secondi_pesato = [0, 0, 0, 0]

        penalita_secondi_pesato = []

        # >>> contatori ritardi
        ritardi_mod4 = [0, 0, 0, 0]
        ritardi_pesato = [0, 0, 0, 0]

        for t in range(n_tentativi):

            last_ritardo_mod4 = [False] * 4
            last_ritardo_pesato = [False] * 4

            # ---------------------------------------------------------
            # MOD(4)
            # ---------------------------------------------------------
            for i, quantita in enumerate(ordini):

                ordine_fornitori = [
                    i,
                    ciclo_mod4(i),
                    ciclo_mod4(ciclo_mod4(i)),
                    ciclo_mod4(ciclo_mod4(ciclo_mod4(i)))
                ]

                validi = []

                for idx in ordine_fornitori:
                    f = fornitori[idx]

                    if quantita > f["capacita"]:
                        continue

                    lt_eff, ritardo, new_flag = calcola_lt_eff(f, last_ritardo_mod4[idx])
                    last_ritardo_mod4[idx] = new_flag

                    # >>> conteggio ritardi Mod(4)
                    if ritardo:
                        ritardi_mod4[idx] += 1

                    if lt_eff <= lead_time_max:
                        validi.append((idx, lt_eff))

                if len(validi) > 0:
                    # Prima classificata
                    best_idx = validi[0][0]
                    vittorie_mod4[best_idx] += 1
                    quantita_mod4[best_idx] += quantita

                    # Seconda classificata
                    if len(validi) > 1:
                        second_idx = validi[1][0]
                        secondi_mod4[second_idx] += 1

            # ---------------------------------------------------------
            # PESATO
            # ---------------------------------------------------------
            for i, quantita in enumerate(ordini):

                valutazioni = []

                for idx, f in enumerate(fornitori):

                    if quantita > f["capacita"]:
                        continue

                    lt_eff, ritardo, new_flag = calcola_lt_eff(f, last_ritardo_pesato[idx])
                    last_ritardo_pesato[idx] = new_flag

                    # >>> conteggio ritardi Pesato
                    if ritardo:
                        ritardi_pesato[idx] += 1

                    if lt_eff <= lead_time_max:
                        costo_totale = quantita * f["costo"]
                        pen = penalita(lt_eff, costo_totale, peso_lt, peso_costo)
                        valutazioni.append((idx, pen, lt_eff, costo_totale))

                if len(valutazioni) > 0:

                    # Ordina con tie-breaking
                    ordinati = tie_break(valutazioni)

                    # Prima classificata
                    best_idx = ordinati[0][0]
                    vittorie_pesato[best_idx] += 1
                    quantita_pesato[best_idx] += quantita

                    # Seconda classificata
                    if len(ordinati) > 1:
                        sec_idx = ordinati[1][0]
                        secondi_pesato[sec_idx] += 1
                        penalita_secondi_pesato.append(ordinati[1][1])

        # ---------------------------------------------------------
        # RISULTATI FINALI
        # ---------------------------------------------------------
        st.subheader("📊 Risultati Competizione")

        tabella = {
            "Fornitore": [f"F{i+1}" for i in range(4)],
            "Vittorie Mod(4)": vittorie_mod4,
            "Vittorie Pesato": vittorie_pesato,
            "Quantità Mod(4)": quantita_mod4,
            "Quantità Pesato": quantita_pesato,
            "Secondo Mod(4)": secondi_mod4,
            "Secondo Pesato": secondi_pesato,
            "Ritardi Mod(4)": ritardi_mod4,
            "Ritardi Pesato": ritardi_pesato
        }

        st.write("### 🏆 Tabella Comparativa")
        st.dataframe(tabella, use_container_width=True)

        # Overflow diagnostico
        st.write("### ⚠️ Overflow capacità (diagnostico)")

        overflow = []
        for i in range(4):
            overflow.append({
                "Fornitore": f"F{i+1}",
                "Capacità": fornitori[i]["capacita"],
                "Quantità Mod(4)": quantita_mod4[i],
                "Overflow Mod(4)": "❌" if quantita_mod4[i] > fornitori[i]["capacita"] else "✔",
                "Quantità Pesato": quantita_pesato[i],
                "Overflow Pesato": "❌" if quantita_pesato[i] > fornitori[i]["capacita"] else "✔"
            })

        st.dataframe(overflow, use_container_width=True)

        # Grafico vittorie
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.arange(4)
        ax.bar(x - 0.15, vittorie_mod4, width=0.3, label="Mod(4)")
        ax.bar(x + 0.15, vittorie_pesato, width=0.3, label="Pesato")
        ax.set_xticks(x)
        ax.set_xticklabels([f"F{i+1}" for i in range(4)])
        ax.set_title("Confronto Vittorie")
        ax.legend()
        st.pyplot(fig)

# ---------------------------------------------------------
# SIMULAZIONE SINGOLA (Mod(4) / Pesato)
# ---------------------------------------------------------
st.header("🚀 Esegui Simulazione")

if st.button("Simula"):

    st.subheader("📊 Risultati")
    risultati_radar = []
    last_ritardo = [False] * 4

    for i, quantita in enumerate(ordini):
        st.write(f"## 🔹 Ordine {i+1}: {quantita} unità")

        confronto = []
        penalita_fornitori = []

        # MODALITÀ 1 — MOD(4) PURO
        if modalita == "Mod(4) puro":

            ordine_fornitori = [
                i,
                ciclo_mod4(i),
                ciclo_mod4(ciclo_mod4(i)),
                ciclo_mod4(ciclo_mod4(ciclo_mod4(i)))
            ]

            best = None

            for idx in ordine_fornitori:
                f = fornitori[idx]

                if quantita > f["capacita"]:
                    stato = "Scartato: capacità"
                    lt_eff = f["lead_time"]
                    ritardo = False
                else:
                    lt_eff, ritardo, new_flag = calcola_lt_eff(f, last_ritardo[idx])
                    last_ritardo[idx] = new_flag

                    if lt_eff > lead_time_max:
                        stato = "Scartato: lead time"
                    else:
                        stato = "OK"
                        best = {
                            "fornitore": idx + 1,
                            "costo": quantita * f["costo"],
                            "lead_time": lt_eff,
                            "penalita": None
                        }
                        break

                confronto.append({
                    "Fornitore": f"F{idx+1}",
                    "Modello ritardo": f["modello_ritardo"],
                    "LT effettivo": round(lt_eff, 2),
                    "Stato": stato
                })

            st.write("### 📋 Tabella comparativa fornitori")
            st.dataframe(confronto, use_container_width=True)

            if best is None:
                st.error("❌ Nessun fornitore disponibile per questo ordine.")
                continue

            st.success(
                f"🏆 Fornitore selezionato: **F{best['fornitore']}** "
                f"(Costo totale: {best['costo']}, LT eff.: {best['lead_time']:.2f})"
            )

            risultati_radar.append({
                "ordine": i+1,
                "fornitore": f"F{best['fornitore']}",
                "costo": best["costo"],
                "lead_time": best["lead_time"],
                "penalita": best["lead_time"]
            })

        # MODALITÀ 2 — MODELLO PESATO
        elif modalita == "Modello Pesato":

            for idx, f in enumerate(fornitori):

                costo_totale = quantita * f["costo"]
                stato = "OK"
                pen = None

                if quantita > f["capacita"]:
                    stato = "Scartato: capacità"
                    lt_eff = f["lead_time"]
                    ritardo = False
                else:
                    lt_eff, ritardo, new_flag = calcola_lt_eff(f, last_ritardo[idx])
                    last_ritardo[idx] = new_flag

                    if lt_eff > lead_time_max:
                        stato = "Scartato: lead time"
                    else:
                        pen = penalita(lt_eff, costo_totale, peso_lt, peso_costo)
                        penalita_fornitori.append({
                            "fornitore": idx + 1,
                            "costo": costo_totale,
                            "lead_time": lt_eff,
                            "penalita": pen
                        })

                confronto.append({
                    "Fornitore": f"F{idx+1}",
                    "Modello ritardo": f["modello_ritardo"],
                    "LT effettivo": round(lt_eff, 2),
                    "Costo Totale": costo_totale,
                    "Penalità": round(pen, 2) if pen else "-",
                    "Stato": stato
                })

            st.write("### 📋 Tabella comparativa fornitori")
            st.dataframe(confronto, use_container_width=True)

            if len(penalita_fornitori) == 0:
                st.error("❌ Nessun fornitore disponibile per questo ordine.")
                continue

            best = min(penalita_fornitori, key=lambda x: x["penalita"])

            st.success(
                f"🏆 Fornitore selezionato: **F{best['fornitore']}** "
                f"(Costo totale: {best['costo']}, LT eff.: {best['lead_time']:.2f}, Penalità: {best['penalita']:.2f})"
            )

            risultati_radar.append({
                "ordine": i+1,
                "fornitore": f"F{best['fornitore']}",
                "costo": best["costo"],
                "lead_time": best["lead_time"],
                "penalita": best["penalita"]
            })

    # ---------------------------------------------------------
    # GRAFICO RADAR
    # ---------------------------------------------------------
    st.header("📈 Grafico Radar – Confronto Fornitori Vincitori")

    if len(risultati_radar) > 0:

        costi = np.array([r["costo"] for r in risultati_radar])
        lts = np.array([r["lead_time"] for r in risultati_radar])
        pens = np.array([r["penalita"] for r in risultati_radar])

        costi_norm = costi / costi.max() if costi.max() > 0 else costi
        lts_norm = lts / lts.max() if lts.max() > 0 else lts
        pens_norm = pens / pens.max() if pens.max() > 0 else pens

        labels = ["Costo", "Lead Time", "Penalità"]
        num_vars = len(labels)

        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, polar=True)

        for idx, r in enumerate(risultati_radar):
            valori = [costi_norm[idx], lts_norm[idx], pens_norm[idx]]
            valori += valori[:1]

            angoli = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            angoli += angoli[:1]

            ax.plot(angoli, valori, label=f"Ordine {r['ordine']} – {r['fornitore']}")
            ax.fill(angoli, valori, alpha=0.1)

        ax.set_xticks(angoli[:-1])
        ax.set_xticklabels(labels)
        ax.set_title("Confronto tra i fornitori vincitori (valori normalizzati)")
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

        st.pyplot(fig)

    else:
        st.info("Nessun ordine assegnato, impossibile generare il grafico radar.")
