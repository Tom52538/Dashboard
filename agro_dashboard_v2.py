"""
Finale Fix: Ersetzt df_base durch df in Zeilen 368-376
Erstellt die korrigierte Datei
"""

import os
import shutil

def apply_fix():
    input_file = r"K:\Umsatz pro Maschine Dashboard\agro_dashboard_v2.py"
    output_file = r"K:\Umsatz pro Maschine Dashboard\agro_dashboard_v2_FIXED.py"
    backup_file = r"K:\Umsatz pro Maschine Dashboard\agro_dashboard_v2_backup_before_final_fix.py"
    
    print("="*80)
    print("🔧 FINALE FIX - df_base Scope Problem")
    print("="*80)
    print()
    
    # Datei lesen
    print(f"📖 Lese: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Fehler beim Lesen: {e}")
        return False
    
    print(f"   ✓ {len(lines)} Zeilen geladen\n")
    
    # Backup erstellen
    print(f"💾 Erstelle Backup: {backup_file}")
    try:
        shutil.copy2(input_file, backup_file)
        print(f"   ✓ Backup erstellt\n")
    except Exception as e:
        print(f"   ⚠️  Backup-Warnung: {e}\n")
    
    # Zeige Original-Code
    print("📄 ORIGINAL CODE (Zeilen 368-376):")
    print("-"*80)
    for i in range(367, min(377, len(lines))):
        print(f"{i+1:4d}: {lines[i].rstrip()}")
    print()
    
    # Änderungen durchführen
    print("🔧 Führe Änderungen durch...\n")
    
    changes_made = False
    
    # Suche nach dem spezifischen Block
    for i in range(len(lines)):
        line = lines[i]
        
        # Zeile 369: len(df_base) -> len(df)
        if 'Datensatz: {len(df_base)} Maschinen' in line:
            old_line = line
            new_line = line.replace('len(df_base)', 'len(df)')
            lines[i] = new_line
            print(f"✓ Zeile {i+1}: len(df_base) → len(df)")
            changes_made = True
        
        # Zeilen 370-373: Entferne YTD Zeilen
        if 'YTD Umsätze: €{ytd_umsaetze' in line:
            lines[i] = ''  # Leere Zeile
            print(f"✓ Zeile {i+1}: YTD Umsätze Zeile entfernt")
            changes_made = True
        
        if 'YTD DB: €{ytd_db' in line:
            lines[i] = ''  # Leere Zeile
            print(f"✓ Zeile {i+1}: YTD DB Zeile entfernt")
            changes_made = True
        
        if 'YTD Marge: {ytd_marge' in line:
            lines[i] = ''  # Leere Zeile
            print(f"✓ Zeile {i+1}: YTD Marge Zeile entfernt")
            changes_made = True
        
        # Zeile 376: df_base -> df im ask_gemini Aufruf
        if 'ask_gemini(user_question, df_base)' in line:
            old_line = line
            new_line = line.replace('df_base', 'df')
            lines[i] = new_line
            print(f"✓ Zeile {i+1}: ask_gemini(..., df_base) → ask_gemini(..., df)")
            changes_made = True
    
    if not changes_made:
        print("⚠️  Keine Änderungen durchgeführt - Pattern nicht gefunden!")
        print("   Möglicherweise wurde die Datei bereits geändert.")
        return False
    
    print()
    
    # Entferne leere Zeilen (wo wir YTD Zeilen gelöscht haben)
    lines = [line for line in lines if line.strip() != '' or not line == '']
    
    # Zeige neuen Code
    print("📄 NEUER CODE (Zeilen 368-376 Bereich):")
    print("-"*80)
    # Finde den data_summary Block im neuen Code
    for i in range(len(lines)):
        if 'data_summary = f"""' in lines[i]:
            for j in range(i, min(i+15, len(lines))):
                print(f"{j+1:4d}: {lines[j].rstrip()}")
            break
    print()
    
    # Speichere neue Datei
    print(f"💾 Speichere korrigierte Datei: {output_file}\n")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ ERFOLGREICH GESPEICHERT!\n")
    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")
        return False
    
    # Zusammenfassung
    print("="*80)
    print("📊 ZUSAMMENFASSUNG")
    print("="*80)
    print()
    print(f"✅ Original:     {input_file}")
    print(f"✅ Backup:       {backup_file}")
    print(f"✅ Korrigiert:   {output_file}")
    print()
    print("🔧 Durchgeführte Änderungen:")
    print("   1. len(df_base) → len(df)")
    print("   2. YTD Umsätze Zeile entfernt")
    print("   3. YTD DB Zeile entfernt")
    print("   4. YTD Marge Zeile entfernt")
    print("   5. ask_gemini(..., df_base) → ask_gemini(..., df)")
    print()
    print("="*80)
    print("📝 NÄCHSTE SCHRITTE:")
    print("="*80)
    print()
    print("1. PRÜFE die neue Datei:")
    print(f"   {output_file}")
    print()
    print("2. Falls alles OK, ersetze das Original:")
    print(f"   copy /Y \"{output_file}\" \"{input_file}\"")
    print()
    print("3. Git Push:")
    print("   git add agro_dashboard_v2.py")
    print("   git commit -m \"Fix: Use df instead of df_base in chat (scope issue)\"")
    print("   git push")
    print()
    print("4. Streamlit Reboot:")
    print("   https://share.streamlit.io/ → App finden → Reboot")
    print()
    print("5. Testen:")
    print("   Strg+Shift+R → Chat testen")
    print()
    
    # Erstelle auch Copy-Paste Ready Inhalt
    copy_paste_file = r"K:\Umsatz pro Maschine Dashboard\KOPIERE_DIESEN_CODE.txt"
    print(f"📋 Erstelle Copy-Paste Datei: {copy_paste_file}\n")
    
    try:
        with open(copy_paste_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("KORRIGIERTE agro_dashboard_v2.py - KOMPLETTER INHALT\n")
            f.write("="*80 + "\n\n")
            f.writelines(lines)
        print("✅ Copy-Paste Datei erstellt!\n")
    except Exception as e:
        print(f"⚠️  Copy-Paste Datei Warnung: {e}\n")
    
    return True


if __name__ == "__main__":
    success = apply_fix()
    
    if success:
        print("🎉 FERTIG! Die korrigierte Datei ist bereit!")
    else:
        print("❌ Fix fehlgeschlagen - siehe Fehler oben")
    
    input("\nDrücke Enter zum Beenden...")
