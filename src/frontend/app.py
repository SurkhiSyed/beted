import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Multipage App",
    page_icon="🧊",
)



html_content = """
    <html>
        <head>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="h-screen flex items-center justify-center bg-100">
            <div class="bg-blue-500 text-white p-4 rounded-xl w-full max-w-md sm:max-w-lg md:max-w-xl lg:max-w-2xl xl:max-w-4xl">
                Hello, Streamlit with Tailwind CSS!
            </div>
        </body>
    </html>
"""


components.html(html_content)
st.sidebar.success("Select a page above.")
