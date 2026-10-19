import pandas as pd
import streamlit as st
from supabase import create_client

# Configuración de la página
st.set_page_config(
    page_title="Mi Lista de Supermercado", page_icon="🛒", layout="centered"
)


# Inicializar conexión a Supabase usando st.secrets
@st.cache_resource
def init_connection():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_connection()

st.title("🛒 Lista de Supermercado Inteligente")
st.write(
    "Gestiona los productos que necesitas comprar, sus cantidades y precios."
)

# ---------------------------------------------------------
# FORMULARIO PARA AGREGAR NUEVO ITEM
# ---------------------------------------------------------
with st.form("add_item_form", clear_on_submit=True):
  st.subheader("Agregar nuevo producto")
  col1, col2, col3 = st.columns([3, 1, 1])

  with col1:
    item_name = st.text_input("Producto", placeholder="Ej: Leche, Pan, Manzanas")
  with col2:
    quantity = st.number_input(
        "Cantidad", min_value=0.1, step=1.0, value=1.0
    )
  with col3:
    price = st.number_input(
        "Precio unitario ($)", min_value=0.0, step=100.0, value=0.0
    )

  submitted = st.form_submit_button("Añadir a la lista")

  if submitted:
    if item_name.strip() != "":
      try:
        response = supabase.table("supermarket_list").insert({
            "item": item_name,
            "quantity": quantity,
            "price": price,
            "purchased": False,
        }).execute()
        st.success(f"¡'{item_name}' agregado con éxito!")
        st.rerun()
      except Exception as e:
        st.error(f"Error al guardar en Supabase: {e}")
    else:
      st.warning("Por favor ingresa el nombre del producto.")

# ---------------------------------------------------------
# OBTENER Y MOSTRAR DATOS DE SUPABASE
# ---------------------------------------------------------
try:
  data = (
      supabase.table("supermarket_list")
      .select("*")
      .order("id", desc=False)
      .execute()
  )
  items = data.data
except Exception as e:
  st.error(f"Error al cargar los datos: {e}")
  items = []

if items:
  st.divider()
  st.subheader("Tu Lista Actual")

  # Convertir a DataFrame para calcular totales y mostrar
  df = pd.DataFrame(items)
  df["Total Parcial"] = df["quantity"] * df["price"]

  # Métricas superiores
  total_gasto = df[df["purchased"] == True]["Total Parcial"].sum()
  total_estimado = df["Total Parcial"].sum()

  col_m1, col_m2 = st.columns(2)
  col_m1.metric("Gasto Acumulado (Comprado)", f"${total_gasto:,.0f}")
  col_m2.metric("Costo Total Estimado", f"${total_estimado:,.0f}")

  st.markdown("### Detalle de Productos")

  for index, row in df.iterrows():
    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns([0.5, 3, 1.5, 1.5, 1])

    # Checkbox para marcar como comprado
    with col_c1:
      purchased_status = st.checkbox(
          "Comprado",
          value=row["purchased"],
          key=f"check_{row['id']}",
          label_visibility="collapsed",
      )
      if purchased_status != row["purchased"]:
        supabase.table("supermarket_list").update(
            {"purchased": purchased_status}
        ).eq("id", row["id"]).execute()
        st.rerun()

    # Nombre del producto (tachado si está comprado)
    with col_c2:
      if row["purchased"]:
        st.markdown(f"~~{row['item']}~~")
      else:
        st.markdown(f"**{row['item']}**")

    # Cantidad y Precio
    with col_c3:
      st.text(f"Cant: {row['quantity']}")
    with col_c4:
      st.text(f"${row['Total Parcial']:,.0f}")

    # Botón de eliminar
    with col_c5:
      if st.button("🗑️", key=f"del_{row['id']}"):
        supabase.table("supermarket_list").delete().eq(
            "id", row["id"]
        ).execute()
        st.rerun()

  # Botón para limpiar los comprados
  st.divider()
  if st.button("Eliminar todos los productos comprados"):
    supabase.table("supermarket_list").delete().eq(
        "purchased", True
    ).execute()
    st.rerun()

else:
  st.info(
      "Tu lista está vacía. ¡Agrega tu primer producto usando el formulario de"
      " arriba!"
  )
