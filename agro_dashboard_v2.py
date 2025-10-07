                # Daten-Kontext (anonymisiert)
                data_summary = f"""
                Datensatz: {len(df)} Maschinen
                Filter: {master_nl_filter}
                """
                
                response = ask_gemini(user_question, df)