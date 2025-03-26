import pandas as pd
import streamlit as st

# Título de la aplicación
st.title("Procesamiento y Cruce de Archivos")

# Expander para mostrar estructura esperada del CSV
with st.expander("📄 Estructura esperada del archivo CSV (EXTRACTO BANCARIO)"):
    st.write("El archivo CSV debe contener los siguientes campos:")
    st.code("""
CUENTA, SUCURSAL, (Columna vacía), FECHA, (Columna vacía), VALOR, CODIGO, DESCRIPCION, (Columna vacía)
236-000019-82, 700, , 20250131, , 218500.00, 4511, CONSIGNACION CORRESPONSAL CB, 0
236-000019-82, 236, , 20250131, , 13950.00, 1167, PAGO QR ANA L. M., 0
236-000019-82, 236, , 20250131, , 9300.00, 1481, PAGO QR ERIKA PATRICIA VILLA V, 0
    """, language="csv")

# Expander para mostrar estructura esperada del Excel
with st.expander("📊 Estructura esperada del archivo Excel (AUXILIAR CONTABLE)"):
    st.write("El archivo Excel debe contener las siguientes columnas:")
    st.code("""
Fecha, Cuenta, Nombre, Debito, Credito, Observaciones
2025-01-31, 110505, Banco XYZ, 50000.00, 0.00, Pago factura
2025-01-31, 220505, Cliente ABC, 0.00, 50000.00, Abono cliente
    """, language="plaintext")
    
# Expander para mostrar estructura esperada del Excel
with st.expander("📊 Estructura esperada del archivo Excel (MEDIOS DE PAGO)"):
    st.write("El archivo Excel debe contener las siguientes columnas:")
    st.code("""
Fecha, Cuenta, Nombre, Debito, Credito, Observaciones
2025-01-31, 110505, Banco XYZ, 50000.00, 0.00, Pago factura
2025-01-31, 220505, Cliente ABC, 0.00, 50000.00, Abono cliente
    """, language="plaintext")


# Función para formatear la moneda en pesos colombianos
def format_colombian_currency(value):
    # Convierte el valor numérico a formato de pesos colombianos
    return f"${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Cargar archivo de medios de pago
file_medios_pago = st.file_uploader("Cargar archivo de MEDIOS DE PAGO (Excel)", type=["xlsx"])
file_auxiliar = st.file_uploader("Cargar archivo AUXILIAR (Excel)", type=["xlsx"])
file_csv = st.file_uploader("Cargar archivo EXTRACTO(csv)", type=["csv"])

if file_medios_pago and file_auxiliar and file_csv:
    # Procesar el archivo de medios de pago
    df_medios_pago = pd.read_excel(file_medios_pago)
    st.write(f"Total de registros en Medios de Pago: {len(df_medios_pago)}")
    st.dataframe(df_medios_pago)

    # Definir las columnas a revisar para asignar el "Medio de pago"
    payment_columns = ['AM - AMERICAN TC', 'E - EFECTIVO', 'GR - GASTOS DE REPRESENTACION', 
                       'MT - MASTECARD TC', 'N - NOMINA', 'QR - CODIGO QR', 
                       'TD - TARJETA DEBITO', 'VI - VISA TC']
    
    # Crear la columna "Medio de pago"
    def assign_payment_method(row):
        for col in payment_columns:
            if pd.notnull(row.get(col)) and row[col] != 0:
                return col
        return None
    
    df_medios_pago['Medio de pago'] = df_medios_pago.apply(assign_payment_method, axis=1)
    df_medios_pago.rename(columns={'Numero': 'Numero documento'}, inplace=True)
    
    # Cargar el archivo auxiliar
    df_auxiliar = pd.read_excel(file_auxiliar, sheet_name='WAUXILIARCTA')
    
    # Cruzar el auxiliar con medios de pago para agregar la columna "Medio de pago"
    df_auxiliar = df_auxiliar.merge(df_medios_pago[['Numero documento', 'Medio de pago']], on='Numero documento', how='left')
    
    # Convertir Debito y Credito a numéricos, reemplazando punto por coma
    def convertir_a_numero(valor):
        if isinstance(valor, str):
            valor = valor.replace('.', '')  # Eliminar puntos como separadores de miles
            valor = valor.replace(',', '.')  # Reemplazar comas por puntos para el formato decimal
        return pd.to_numeric(valor, errors='coerce')

    # Aplicar la conversión a las columnas Debito y Credito en el auxiliar
    df_auxiliar['Debito'] = df_auxiliar['Debito'].apply(convertir_a_numero)
    df_auxiliar['Credito'] = df_auxiliar['Credito'].apply(convertir_a_numero)
    
    # Procesar el archivo CSV
    df_csv = pd.read_csv(file_csv, header=None, encoding='ISO-8859-1')
    df_csv.columns = ['CUENTA', 'SUCURSAL', 'Vacio', 'FECHA', 'Vacio2', 'VALOR', 'CODIGO', 'DESCRIPCION', 'ceros', 'extra']
    df_csv = df_csv.drop(columns=['Vacio', 'Vacio2', 'ceros', 'extra'], errors='ignore')
    df_csv['FECHA'] = pd.to_datetime(df_csv['FECHA'], format='%Y%m%d', errors='coerce')
    
    # Convertir VALOR a numérico, reemplazando punto por coma, y crear Entradas y Salidas
    def convertir_valor_csv(valor):
        if isinstance(valor, str):
            valor = valor.replace('.', '')  # Eliminar puntos como separadores de miles
            valor = valor.replace(',', '.')  # Reemplazar comas por puntos para el formato decimal
        return pd.to_numeric(valor, errors='coerce')

    # Aplicar la conversión a la columna VALOR en el CSV
    df_csv['VALOR'] = df_csv['VALOR'].apply(convertir_valor_csv)
    df_csv['Entradas'] = df_csv['VALOR'].apply(lambda x: x if x > 0 else 0)
    df_csv['Salidas'] = df_csv['VALOR'].apply(lambda x: -x if x < 0 else 0)
    
    st.write(f"Total de registros en CSV: {len(df_csv)}")
    st.dataframe(df_csv)
    
    # Realizar el cruce entre CSV y auxiliar
    df_auxiliar['cruzado'] = False  # Marcar registros del auxiliar
    registros_cruzados = []
    registros_no_cruzados = []
    
    # Primer cruce directo
    for idx_csv, row_csv in df_csv.iterrows():
        if row_csv['Entradas'] > 0:  # Buscar cruce en Debitos
            cruce_entrada = df_auxiliar[(df_auxiliar['Debito'] == row_csv['Entradas']) & (~df_auxiliar['cruzado'])]
            if not cruce_entrada.empty:
                registro_excel = cruce_entrada.iloc[0]
                registros_cruzados.append(pd.concat([row_csv, registro_excel], axis=0))
                df_auxiliar.at[registro_excel.name, 'cruzado'] = True
            else:
                registros_no_cruzados.append(row_csv)
        elif row_csv['Salidas'] > 0:  # Buscar cruce en Creditos
            cruce_salida = df_auxiliar[(df_auxiliar['Credito'] == row_csv['Salidas']) & (~df_auxiliar['cruzado'])]
            if not cruce_salida.empty:
                registro_excel = cruce_salida.iloc[0]
                registros_cruzados.append(pd.concat([row_csv, registro_excel], axis=0))
                df_auxiliar.at[registro_excel.name, 'cruzado'] = True
            else:
                registros_no_cruzados.append(row_csv)

    # Mostrar registros cruzados y no cruzados después del primer cruce
    df_cruzados = pd.DataFrame(registros_cruzados)
    df_csv_no_cruzados = pd.DataFrame(registros_no_cruzados)
    df_auxiliar_no_cruzados = df_auxiliar[~df_auxiliar['cruzado']].copy()

    st.write(f"Total de registros cruzados después del cruce directo: {len(df_cruzados)}")
    st.dataframe(df_cruzados)
    
    st.write(f"Total de registros no cruzados en el EXTRACTO después del cruce directo: {len(df_csv_no_cruzados)}")
    st.dataframe(df_csv_no_cruzados)
    
    st.write(f"Total de registros no cruzados en el AUXILIAR después del cruce directo: {len(df_auxiliar_no_cruzados)}")
    st.dataframe(df_auxiliar_no_cruzados)
    
    # Primer cruce por agrupación (ABONO INTERESES AHORROS)
    abono_intereses = df_csv_no_cruzados[df_csv_no_cruzados['DESCRIPCION'].str.contains('ABONO INTERESES AHORROS', na=False)]
    suma_abono = abono_intereses['Entradas'].sum()
    
    st.write("Registros en el EXTRACTO con 'ABONO INTERESES AHORROS':")
    st.dataframe(abono_intereses)
    
    aux_abono_cruce = df_auxiliar_no_cruzados[df_auxiliar_no_cruzados['Observaciones'].str.contains('ING.*INT BANCARIO', na=False)]
    
    st.write("Registros en el AUXILIAR con 'ING X INT BANCARIO' o similar en Observaciones:")
    st.dataframe(aux_abono_cruce)
    
    suma_abono_formateada = format_colombian_currency(suma_abono)
    st.write(f"Suma de las entradas con la descripción 'ABONO INTERESES AHORROS': {suma_abono_formateada}")
    
    if not aux_cruce.empty and suma_salidas > 0:
    # Tomamos el valor de 'Debito' para la resta
        aux_valor = aux_cruce.iloc[0]['Debito']  # Cambié 'Credito' por 'Debito'
    diferencia = suma_salidas - aux_valor
    diferencia_formateada = format_colombian_currency(diferencia)
    
    st.write(f"Diferencia entre la suma de salidas agrupadas y el valor de Débito en el auxiliar: {diferencia_formateada}")
    
    registros_cruzados.append(pd.concat([registros_agrupados.iloc[0], aux_cruce.iloc[0]], axis=0))
    df_auxiliar.at[aux_cruce.index[0], 'cruzado'] = True
    df_csv_no_cruzados = df_csv_no_cruzados.drop(registros_agrupados.index)

    # Mostrar los registros cruzados y no cruzados después del primer cruce por agrupación
    df_cruzados_agrupados = pd.DataFrame(registros_cruzados)
    df_auxiliar_no_cruzados_agrupados = df_auxiliar[~df_auxiliar['cruzado']].copy()
    
    st.write(f"Cantidad de registros cruzados después de la agrupación (ABONO INTERESES AHORROS): {len(df_cruzados_agrupados)}")
    st.dataframe(df_cruzados_agrupados)
    
    st.write(f"Cantidad de registros no cruzados en el EXTRACTO después de la agrupación: {len(df_csv_no_cruzados)}")
    st.dataframe(df_csv_no_cruzados)
    
    st.write(f"Cantidad de registros no cruzados en el AUXILIAR  después de la agrupación: {len(df_auxiliar_no_cruzados_agrupados)}")
    st.dataframe(df_auxiliar_no_cruzados_agrupados)

   # Segundo cruce por agrupación (COMISIONES, IMPUESTOS, etc.)
descripciones_buscar = ['COMISION AMEX', 'COMISION MASTER', 'COMISION VISA', 'IMPTO GOBIERNO 4X1000', 
                        'COMIS CONSIGNACION CB', 'VALOR IVA', 'RTE IVA VISA', 'COMISION TRASL SUC VIRTUAL', 
                        'IVA COMIS TRASL SUC VIRTUAL']
    
# Filtrar registros del CSV con las descripciones seleccionadas
registros_agrupados = df_csv_no_cruzados[df_csv_no_cruzados['DESCRIPCION'].str.contains('|'.join(descripciones_buscar), na=False)]
suma_salidas = registros_agrupados['Salidas'].sum()
suma_salidas_formateada = format_colombian_currency(suma_salidas)

st.write(f"Registros agrupados con descripciones seleccionadas en el EXTRACTO:")
st.dataframe(registros_agrupados)

# Buscar los registros correspondientes en el auxiliar con 'GASTOS BANCARIOS TIENDA CAFE'
aux_cruce = df_auxiliar_no_cruzados[df_auxiliar_no_cruzados['Observaciones'].str.contains('GASTOS BANCARIOS TIENDA CAFE', na=False)]

st.write("Registro en el Auxiliar con 'GASTOS BANCARIOS TIENDA CAFE' en Observaciones:")
st.dataframe(aux_cruce)

if not aux_cruce.empty and suma_salidas > 0:
    # Tomamos el valor de 'Debito' para la resta
    aux_valor = aux_cruce.iloc[0]['Debito']  # Cambié 'Credito' por 'Debito'
    diferencia = suma_salidas - aux_valor
    diferencia_formateada = format_colombian_currency(diferencia)
    
    # Mostrar la diferencia
    st.write(f"Suma de las salidas para completar los gastos bancarios: {suma_salidas_formateada}")


    st.write(f"Diferencia entre la suma de salidas agrupadas y el valor de Débito en el auxiliar: {diferencia_formateada}")
    
    # Realizar el cruce con los registros agrupados y el auxiliar
    registros_cruzados.append(pd.concat([registros_agrupados.iloc[0], aux_cruce.iloc[0]], axis=0))
    df_auxiliar.at[aux_cruce.index[0], 'cruzado'] = True
    df_csv_no_cruzados = df_csv_no_cruzados.drop(registros_agrupados.index)

# Mostrar los registros cruzados y no cruzados después del cruce
df_cruzados_agrupados = pd.DataFrame(registros_cruzados)
df_auxiliar_no_cruzados_agrupados = df_auxiliar[~df_auxiliar['cruzado']].copy()

st.write(f"Cantidad de registros cruzados después del nuevo cruce agrupado: {len(df_cruzados_agrupados)}")
st.dataframe(df_cruzados_agrupados)

st.write(f"Cantidad de registros no cruzados en el EXTRACTO después del nuevo cruce agrupado: {len(df_csv_no_cruzados)}")
st.dataframe(df_csv_no_cruzados)

st.write(f"Cantidad de registros no cruzados en el AUXILIAR después del nuevo cruce agrupado: {len(df_auxiliar_no_cruzados_agrupados)}")
st.dataframe(df_auxiliar_no_cruzados_agrupados)
