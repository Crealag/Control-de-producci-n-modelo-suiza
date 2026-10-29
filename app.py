elif menu_seleccionado == "📄 Generador de Remisiones":
    st.subheader("Generador de Remisiones Oficiales - Formato Original Crealag")
    df_oc_rem = df[df["orden_compra"] == oc_actual] if not df.empty else pd.DataFrame()
    piezas_producidas_total = df_oc_rem["piezas_producidas"].sum() if not df_oc_rem.empty else 0
    piezas_almacen_rem = max(0, piezas_producidas_total - entregadas_actual)
    
    st.info(f"📦 **Estado de Almacén para `{oc_actual}`:** Total Producido: **{piezas_producidas_total} pzas** | Ya Entregadas: **{entregadas_actual} pzas** | Disponibles: **{piezas_almacen_rem} pzas**")

    with st.form("form_remision"):
        col1, col2 = st.columns(2)
        with col1:
            atencion = st.text_input("Atención", "Ing. Laura Zamora")
            compania = st.text_input("Compañía", "Herwong")
            puesto = st.text_input("Puesto", "Compras")
            email = st.text_input("Email", "compras.herwong@gmail.com")
            cel = st.text_input("Cel", "871-1442234")
        with col2:
            referencia = st.text_input("Referencia", "Respaldos sillas modelo Suiza")
            fecha_remision = st.date_input("Fecha de emisión", datetime.now())
            cantidad_piezas_entrega = st.number_input(
                "Cantidad de piezas a entregar en esta remisión", 
                min_value=1, 
                value=max(1, int(piezas_almacen_rem))
            )

        # Diccionario para convertir el número del mes a su nombre en español
        meses_es = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        # Genera automáticamente el texto con base en la fecha de emisión seleccionada
        fecha_sugerida = f"{fecha_remision.day} de {meses_es[fecha_remision.month]} de {fecha_remision.year}"

        fecha_recibido_str = st.text_input("Fecha de pedido recibido (Texto)", value=fecha_sugerida)
        sumar_a_entregadas = st.checkbox(" Descontar estas piezas de Almacén al generar remisión", value=True)
        submit_pdf = st.form_submit_button("Generar PDF de Remisión Original", type="primary")

    if submit_pdf:
        if sumar_a_entregadas:
            registrar_entrega_piezas(oc_actual, cantidad_piezas_entrega)
        pdf_buffer = generar_pdf_original(atencion, compania, puesto, email, cel, referencia, oc_actual, fecha_remision, cantidad_piezas_entrega, fecha_recibido_str)
        st.success(f"¡Remisión por {cantidad_piezas_entrega} piezas generada con éxito y descontada del almacén!")
        st.download_button(label="📥 Descargar Remisión en PDF", data=pdf_buffer, file_name="Remision.pdf", mime="application/pdf")