import streamlit as st
import pdfplumber
import PyPDF2
import tempfile
import zipfile
import os
from datetime import datetime

st.set_page_config(page_title="Aggregator Prime", layout="centered")
st.sidebar.title("🔀 Mode Selection")
mode = st.sidebar.radio("Choose Mode", ["📄 Single Report", "📚 Batch Reports"])

# -------------------- UTILITY FUNCTIONS --------------------
def find_pages_with_names(pdf_path, names):
    pages_with_names = set()
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            for name in names:
                if name.upper() in text.upper():
                    pages_with_names.add(i)
    return pages_with_names

def create_pdf_with_pages(source_pdf_path, pages, output_pdf_path):
    pdf_writer = PyPDF2.PdfWriter()
    pdf_reader = PyPDF2.PdfReader(source_pdf_path)
    for page_num in sorted(pages):
        pdf_writer.add_page(pdf_reader.pages[page_num])
    with open(output_pdf_path, 'wb') as out_pdf:
        pdf_writer.write(out_pdf)

# -------------------- SINGLE REPORT MODE --------------------
if mode == "📄 Single Report":
    st.title("🤖 Aggregator Prime")
    st.markdown("Upload a PDF and extract pages that contain any of the names listed.")

    names_input = st.text_area("✍️ Enter Names (one per line):")
    pdf_file = st.file_uploader("📎 Upload Source PDF", type=["pdf"])
    output_name = st.text_input("📁 Output PDF Filename (without .pdf):")

    if st.button("🚀 Create PDF") and pdf_file and output_name and names_input:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_source:
            temp_source.write(pdf_file.read())
            temp_source_path = temp_source.name

        names = [name.strip() for name in names_input.splitlines() if name.strip()]
        pages = find_pages_with_names(temp_source_path, names)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_output:
            output_path = temp_output.name

        create_pdf_with_pages(temp_source_path, pages, output_path)

        st.success(f"✅ PDF created with {len(pages)} page(s) containing specified names.")
        with open(output_path, "rb") as f:
            st.download_button("⬇️ Download Result PDF", f, file_name=f"{output_name}.pdf")

# -------------------- BATCH REPORT MODE --------------------
elif mode == "📚 Batch Reports":
    st.title("📚 Aggregator Prime: Batch Report Generator")

    if "batch_reports" not in st.session_state:
        st.session_state.batch_reports = []

    if "generated_files" not in st.session_state:
        st.session_state.generated_files = []

    if "zip_path" not in st.session_state:
        st.session_state.zip_path = None

    if st.button("➕ Add New Report"):
        st.session_state.batch_reports.append({
            "names": "",
            "output_name": "",
            "pdf": None
        })

    for idx, report in enumerate(st.session_state.batch_reports):
        st.subheader(f"📦 Report {idx+1}")
        st.session_state.batch_reports[idx]["pdf"] = st.file_uploader(
            f"Upload PDF for Report {idx+1}",
            type=["pdf"],
            key=f"pdf_{idx}"
        )
        st.session_state.batch_reports[idx]["names"] = st.text_area(
            f"Enter Names for Report {idx+1}",
            key=f"names_{idx}"
        )
        st.session_state.batch_reports[idx]["output_name"] = st.text_input(
            f"Output Filename for Report {idx+1}",
            key=f"name_{idx}"
        )

    if st.session_state.batch_reports and st.button("🚀 Generate All Reports"):
        st.session_state.generated_files.clear()
        st.session_state.zip_path = None

        for idx, report in enumerate(st.session_state.batch_reports):
            pdf = report["pdf"]
            names_text = report["names"]
            output_name = report["output_name"]

            if pdf and names_text and output_name:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_source:
                    temp_source.write(pdf.read())
                    temp_source_path = temp_source.name

                names = [name.strip() for name in names_text.splitlines() if name.strip()]
                pages = find_pages_with_names(temp_source_path, names)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_output:
                    output_path = temp_output.name

                create_pdf_with_pages(temp_source_path, pages, output_path)

                st.session_state.generated_files.append((f"{output_name}.pdf", output_path))

                st.success(f"✅ Report {idx+1} generated with {len(pages)} pages")

        # Create ZIP file
        if st.session_state.generated_files:
            zip_name = f"Aggregator-{datetime.now().strftime('%Y-%m-%d')}.zip"
            zip_path = os.path.join(tempfile.gettempdir(), zip_name)

            with zipfile.ZipFile(zip_path, "w") as zipf:
                for name, path in st.session_state.generated_files:
                    zipf.write(path, arcname=name)

            st.session_state.zip_path = zip_path
            st.success("📦 All reports zipped and ready to download.")

    # Show Download Buttons
    if st.session_state.generated_files:
        for idx, (name, path) in enumerate(st.session_state.generated_files):
            with open(path, "rb") as f:
                st.download_button(
                    f"⬇️ Download Report {idx+1}: {name}",
                    f,
                    file_name=name,
                    key=f"dl_{idx}"
                )

    if st.session_state.zip_path:
        with open(st.session_state.zip_path, "rb") as zf:
            st.download_button(
                "📦 Download All Reports (ZIP)",
                zf,
                file_name=os.path.basename(st.session_state.zip_path),
                key="zip_dl"
            )
