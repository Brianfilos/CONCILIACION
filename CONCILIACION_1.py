import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="CONCILIACION 2 ARCHIVOS (AUXILIAR Y EXTRACTO)", layout="wide")

st.title("Cargar y procesar AUXILIAR CONTABLE(EXCEL)  Y EXTRACTO BANCARIO (CSV)")
# Cargar archivo CSV sin nombres de columna
csv_file = st.file_uploader("Cargar archivo CSV (EXTRACTO)", type=["csv"])
if csv_file is not None:
    # Leer el archivo CSV sin encabezado
    df_csv = pd.read_csv(csv_file, header=None, encoding='ISO-8859-1')
    
    # Asignar nombres de columnas según las detectadas
    column_names = ['CUENTA', 'SUCURSAL', 'Vacio', 'FECHA', 'Vacio2', 'VALOR', 'CODIGO', 'DESCRIPCION', 'ceros', 'extra']
    df_csv.columns = column_names[:df_csv.shape[1]]
    
    # Eliminar columnas innecesarias
    df_csv = df_csv.drop(columns=['Vacio', 'Vacio2', 'ceros', 'extra'], errors='ignore')
    
    # Convertir la columna FECHA a formato de fecha
    df_csv['FECHA'] = pd.to_datetime(df_csv['FECHA'], format='%Y%m%d', errors='coerce')
    # Separar VALOR en Entradas y Salidas
    df_csv['Entradas'] = df_csv['VALOR'].apply(lambda x: x if x > 0 else 0)
    df_csv['Salidas'] = df_csv['VALOR'].apply(lambda x: -x if x < 0 else 0)
    # Convertir las columnas Entradas y Salidas a tipo float
    df_csv['Entradas'] = pd.to_numeric(df_csv['Entradas'], errors='coerce')
    df_csv['Salidas'] = pd.to_numeric(df_csv['Salidas'], errors='coerce')
    st.write("Datos del EXTRACTO BANCARIO:")
    st.write(f"Total de registros en EXTRACTO BANCARIO: {df_csv.shape[0]}")
    st.dataframe(df_csv)
# Cargar archivo Excel
excel_file = st.file_uploader("Cargar archivo Excel(AUXILIAR CONTABLE)", type=["xlsx"])
if excel_file is not None:
    sheet_names = pd.ExcelFile(excel_file).sheet_names
    selected_sheet = st.selectbox("Selecciona la hoja de Excel", sheet_names)
    df_excel = pd.read_excel(excel_file, sheet_name=selected_sheet)
    # Convertir columnas Debito y Credito a tipo float
    df_excel['Debito'] = df_excel['Debito'].astype(float)
    df_excel['Credito'] = df_excel['Credito'].astype(float)
    # Inicializar listas para los registros cruzados y no cruzados
    registros_cruzados = []
    registros_no_cruzados = []
    # Marcar cada registro del Excel para uso único
    df_excel['cruzado'] = False
    st.write("Datos del AUXILIAR CONTABLE:")
    st.write(f"Total de registros en AUXILIAR CONTABLE: {df_excel.shape[0]}")
    st.dataframe(df_excel)
    # Primer cruce directo entre CSV y Excel
    for idx_csv, row_csv in df_csv.iterrows():
        if row_csv['Entradas'] > 0:  # Buscar cruce en Debitos
            cruce_entrada = df_excel[(df_excel['Debito'] == row_csv['Entradas']) & (~df_excel['cruzado'])]
            if not cruce_entrada.empty:
                registro_excel = cruce_entrada.iloc[0]
                registros_cruzados.append(pd.concat([row_csv, registro_excel], axis=0))
                df_excel.at[registro_excel.name, 'cruzado'] = True
            else:
                registros_no_cruzados.append(row_csv)
        elif row_csv['Salidas'] > 0:  # Buscar cruce en Creditos
            cruce_salida = df_excel[(df_excel['Credito'] == row_csv['Salidas']) & (~df_excel['cruzado'])]
            if not cruce_salida.empty:
                registro_excel = cruce_salida.iloc[0]
                registros_cruzados.append(pd.concat([row_csv, registro_excel], axis=0))
                df_excel.at[registro_excel.name, 'cruzado'] = True
            else:
                registros_no_cruzados.append(row_csv)
    # Registros cruzados
    df_cruzados = pd.DataFrame(registros_cruzados)
    st.write("Registros cruzados (desde EXTRACTO hacia EL AUXILIAR ):")
    st.write(f"Cantidad de registros cruzados: {len(df_cruzados)}")
    st.dataframe(df_cruzados)
    # Registros no cruzados en el CSV
    df_csv_no_cruzados = pd.DataFrame(registros_no_cruzados)
    st.write("Registros no cruzados en el EXTRACTO :")
    st.write(f"Cantidad de registros que no cruzaron en el EXTRACTO: {len(df_csv_no_cruzados)}")
    st.dataframe(df_csv_no_cruzados)
    # Cruces desde la perspectiva del Excel
    excel_perspective_cruces = []
    for cruzado in registros_cruzados:
        registro_csv = cruzado.iloc[:len(df_csv.columns)]
        registro_excel = cruzado.iloc[len(df_csv.columns):]
        combined_record = pd.concat([registro_excel, registro_csv], axis=0)
        excel_perspective_cruces.append(combined_record)
    df_excel_perspective_cruces = pd.DataFrame(excel_perspective_cruces)
    st.write("Cruces desde la perspectiva del AUXILIAR:")
    st.write(f"Cantidad de registros cruzados desde el AUXILIAR: {len(df_excel_perspective_cruces)}")
    st.dataframe(df_excel_perspective_cruces)
    # Registros sin cruzar en el Excel
    df_excel_no_cruzados = df_excel[~df_excel['cruzado']].copy()
    st.write("Registros del AUXILIAR sin cruzar:")
    st.write(f"Cantidad de registros sin cruzar en AUXILIAR : {len(df_excel_no_cruzados)}")
    st.dataframe(df_excel_no_cruzados)
    # Nuevo cruce con gastos bancarios
    # Definir las descripciones a filtrar para el cruce adicional
    descripciones_filtro = [
        "COMISION PAGO A OTROS BANCOS",
        "COBRO IVA PAGOS AUTOMATICOS",
        "IVA COMIS TRASL SUC VIRTUAL",
        "COMISION TRASL SUC VIRTUAL",
        "COMISION PAGO A PROVEEDORES",
        "COMISION PAGO DE NOMINA",
        "CUOTA MANEJO TARJETA PREPAGO",
        "IVA POR COMISIONES CORRIENTE",
        "CUOTA MANEJO SUC VIRT EMPRESA",
        "IVA CUOTA MANEJO SUC VIRT EMP"
    ]
    # Eliminar espacios adicionales en DESCRIPCION para asegurar la búsqueda correcta
    df_csv_no_cruzados['DESCRIPCION'] = df_csv_no_cruzados['DESCRIPCION'].str.strip()
    # Añadir una columna temporal para marcar los registros utilizados en el cruce de gastos bancarios en el CSV
    df_csv_no_cruzados['Usado_en_cruce_gastos'] = False  # Nueva columna para marcar el uso en cruce adicional
    suma_salidas_filtro = 0  # Inicializar la suma
    # Filtrar y sumar los valores de Salidas que coinciden con las descripciones, y marcar los registros como usados
    for idx, row in df_csv_no_cruzados.iterrows():
        if row['DESCRIPCION'] in descripciones_filtro:
            suma_salidas_filtro += row['Salidas']
            df_csv_no_cruzados.at[idx, 'Usado_en_cruce_gastos'] = True  # Marcar como usado
    # Mostrar los registros utilizados del CSV para la suma
    df_registros_usados_csv = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_gastos']]
    st.write("Registros utilizados del EXTRACTO para la suma de gastos bancarios:")
    st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_csv)}")
    st.dataframe(df_registros_usados_csv)
    st.write(f"Suma total de Salidas utilizadas: {suma_salidas_filtro}")
    # Buscar un registro en los no cruzados del Excel que contenga "GASTOS BANCARIOS CUENTA" en Observaciones
    registro_gastos_bancarios = df_excel_no_cruzados[
        df_excel_no_cruzados['Observaciones'].str.contains("GASTOS BANCARIOS CUENTA", case=False, na=False) &
        (df_excel_no_cruzados['Credito'] > 0)
    ]
    if not registro_gastos_bancarios.empty:
        registro_gastos = registro_gastos_bancarios.iloc[0]
        diferencia = registro_gastos['Credito'] - suma_salidas_filtro
        cruce_gastos = pd.concat([registro_gastos, df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_gastos']].sum(numeric_only=True)], axis=0)
        cruce_gastos['Diferencia'] = diferencia
        cruce_gastos['Nota'] = f"Cruce parcial con diferencia de {diferencia:.2f}. Registros EXTRACTO usados: {df_csv_no_cruzados['Usado_en_cruce_gastos'].sum()}"
        # Marcar como cruzado en el Excel y actualizar no cruzados del CSV
        df_excel.at[registro_gastos.name, 'cruzado'] = True
        registros_cruzados.append(cruce_gastos)
        # Mostrar el resultado del cruce de gastos bancarios
        st.write("Resultado del cruce de gastos bancarios:")
        st.write("Registro del AUXILIAR con el que se cruzó:")
        st.dataframe(registro_gastos.to_frame().T)
        st.write(f"Diferencia entre la suma del EXTRACTO y el registro del AUXILIAR: {diferencia}")
    # Excluir los registros marcados del DataFrame final de no cruzados
    df_csv_no_cruzados_final = df_csv_no_cruzados[~df_csv_no_cruzados['Usado_en_cruce_gastos']].drop(columns=['Usado_en_cruce_gastos'])

    # Nuevo cruce con servicios públicos e internet
    # Definir las descripciones para filtrar en el CSV
    descripciones_servicios = [
        "PAGO PSE UNE - EPM Telecomuni",
        "PAGO SV TIGO SERVICIOS HOGAR"
    ]

    # Eliminar espacios adicionales en DESCRIPCION para asegurar la búsqueda correcta
    df_csv_no_cruzados['DESCRIPCION'] = df_csv_no_cruzados['DESCRIPCION'].str.strip()

    # Añadir una columna temporal para marcar los registros utilizados en el cruce de servicios públicos
    df_csv_no_cruzados['Usado_en_cruce_servicios'] = False  # Nueva columna para marcar el uso en cruce adicional
    suma_salidas_servicios = 0  # Inicializar la suma

    # Filtrar y sumar los valores de Salidas que coinciden con las descripciones de servicios, y marcar los registros como usados
    for idx, row in df_csv_no_cruzados.iterrows():
        if row['DESCRIPCION'] in descripciones_servicios:
            suma_salidas_servicios += row['Salidas']
            df_csv_no_cruzados.at[idx, 'Usado_en_cruce_servicios'] = True  # Marcar como usado

    # Mostrar los registros utilizados del CSV para la suma de servicios
    df_registros_usados_servicios = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_servicios']]
    st.write("Registros utilizados del CSV para la suma de servicios públicos e internet:")
    st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_servicios)}")
    st.dataframe(df_registros_usados_servicios)
    st.write(f"Suma total de Salidas utilizadas para servicios públicos e internet: {suma_salidas_servicios}")

    # Buscar un registro en los no cruzados del Excel que contenga "SERVICIOS PUBLICOS INTERNET" en Observaciones
    registro_servicios_excel = df_excel_no_cruzados[
        df_excel_no_cruzados['Observaciones'].str.contains("SERVICIOS PUBLICOS INTERNET", case=False, na=False) &
        (df_excel_no_cruzados['Credito'] > 0)
    ]

    if not registro_servicios_excel.empty:
        registro_servicio = registro_servicios_excel.iloc[0]
        diferencia_servicios = registro_servicio['Credito'] - suma_salidas_servicios
        cruce_servicios = pd.concat([registro_servicio, df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_servicios']].sum(numeric_only=True)], axis=0)
        cruce_servicios['Diferencia'] = diferencia_servicios
        cruce_servicios['Nota'] = f"Cruce parcial con diferencia de {diferencia_servicios:.2f}. Registros EXTRACTO usados: {df_csv_no_cruzados['Usado_en_cruce_servicios'].sum()}"
        
        # Marcar como cruzado en el Excel y actualizar no cruzados del CSV
        df_excel.at[registro_servicio.name, 'cruzado'] = True
        registros_cruzados.append(cruce_servicios)
        
        # Mostrar el resultado del cruce de servicios públicos e internet
        st.write("Resultado del cruce de servicios públicos e internet:")
        st.write("Registro del AUXILIAR con el que se cruzó:")
        st.dataframe(registro_servicio.to_frame().T)
        st.write(f"Diferencia entre la suma del EXTRACTO y el registro del AUXILIAR: {diferencia_servicios}")

# Excluir los registros marcados del DataFrame final de no cruzados
    df_csv_no_cruzados_final = df_csv_no_cruzados[~df_csv_no_cruzados['Usado_en_cruce_gastos'] & ~df_csv_no_cruzados['Usado_en_cruce_servicios']].drop(columns=['Usado_en_cruce_gastos', 'Usado_en_cruce_servicios'])

    # Actualizar los DataFrames finales y visualización
    df_cruzados = pd.DataFrame(registros_cruzados)
    st.write("Registros cruzados (con cruces adicionales de gastos y servicios):")
    st.write(f"Cantidad de registros cruzados (total): {len(df_cruzados)}")
    st.dataframe(df_cruzados)
    st.write("Registros no cruzados en el EXTRACTO (final):")
    st.write(f"Cantidad de registros no cruzados en EXTRACTO (final): {len(df_csv_no_cruzados_final)}")
    st.dataframe(df_csv_no_cruzados_final)
    st.write("Registros del AUXILIAR sin cruzar (actualizado):")
    st.write(f"Cantidad de registros sin cruzar en AUXILIAR (actualizado): {len(df_excel[~df_excel['cruzado']])}")
    st.dataframe(df_excel[~df_excel['cruzado']])








    


