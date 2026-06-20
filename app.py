# MRI Brain Analysis Web App
# Stage 5 - Kuljit Singh

import streamlit as st
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from sklearn.cluster import KMeans
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import tempfile
import os
import io

# Page configuration
st.set_page_config(
    page_title="MRI Brain Analysis",
    page_icon="🧠",
    layout="wide"
)

# Title and header
st.title("🧠 MRI Brain Tissue Analysis")
st.markdown("**Developed by Kuljit Singh | Otto Von Guericke University, Magdeburg**")
st.markdown("---")

# Sidebar
st.sidebar.title("⚙️ Settings")
st.sidebar.markdown("Upload an MRI scan and configure analysis settings.")

# File upload
uploaded_file = st.sidebar.file_uploader(
    "Upload MRI Scan (.nii or .nii.gz)",
    type=['nii', 'gz'],
    help="Upload a NIfTI format MRI brain scan"
)

# Function to load MRI
@st.cache_data
def load_mri(file_bytes, filename):
    """Load MRI from uploaded file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz' if filename.endswith('.gz') else '.nii') as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    img = nib.load(tmp_path)
    data = img.get_fdata()
    os.unlink(tmp_path)
    return data

# Function to segment slice
def segment_slice(brain_slice, n_clusters=3):
    """Segment MRI slice using K-means"""
    pixels = brain_slice.flatten().reshape(-1, 1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(pixels)
    labels = kmeans.labels_.reshape(brain_slice.shape)
    centers = kmeans.cluster_centers_.flatten()
    order = np.argsort(centers)
    sorted_labels = np.zeros_like(labels)
    for new_label, old_label in enumerate(order):
        sorted_labels[labels == old_label] = new_label
    return sorted_labels

# Function to measure tissues
def measure_tissues(brain_slice, segmented, tissue_names):
    """Measure tissue properties"""
    total_pixels = segmented.size
    measurements = []
    for i, name in enumerate(tissue_names):
        count = int(np.sum(segmented == i))
        percentage = round((count / total_pixels) * 100, 2)
        avg_brightness = round(float(np.mean(brain_slice[segmented == i])), 2)
        measurements.append({
            'Tissue Type': name,
            'Voxel Count': count,
            'Percentage (%)': percentage,
            'Avg Brightness': avg_brightness
        })
    return measurements

# Main app
if uploaded_file is not None:
    st.success(f"✅ File uploaded: {uploaded_file.name}")

    # Load MRI
    with st.spinner("Loading MRI scan..."):
        file_bytes = uploaded_file.read()
        data = load_mri(file_bytes, uploaded_file.name)

    st.info(f"📊 Scan dimensions: {data.shape[0]} x {data.shape[1]} x {data.shape[2]} voxels")

    # Slice selector
    st.markdown("---")
    st.subheader("🔍 Brain Slice Viewer")
    total_slices = data.shape[2]
    slice_idx = st.slider(
        "Select Brain Slice",
        min_value=0,
        max_value=total_slices - 1,
        value=total_slices // 2,
        help="Slide to navigate through brain slices"
    )

    brain_slice = data[:, :, slice_idx]

    # Show original slice
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original MRI Slice**")
        fig, ax = plt.subplots(figsize=(5, 5))
        fig.patch.set_facecolor('#0a0a0a')
        ax.imshow(brain_slice.T, cmap='gray', origin='lower')
        ax.axis('off')
        ax.set_title(f'Slice {slice_idx}/{total_slices}', color='white')
        st.pyplot(fig)
        plt.close()

    # Segmentation
    tissue_names = ['Background', 'Grey Matter', 'White Matter']
    tissue_colors = ['#1a1aff', '#ff4444', '#ffff00']
    cmap = ListedColormap(tissue_colors)

    with col2:
        st.markdown("**Segmented Tissues**")
        with st.spinner("Segmenting..."):
            segmented = segment_slice(brain_slice)
        fig, ax = plt.subplots(figsize=(5, 5))
        fig.patch.set_facecolor('#0a0a0a')
        ax.imshow(segmented.T, cmap=cmap, origin='lower', vmin=0, vmax=2)
        ax.axis('off')
        patches = [mpatches.Patch(color=tissue_colors[i], label=tissue_names[i]) for i in range(3)]
        ax.legend(handles=patches, loc='lower center', fontsize=8,
                 facecolor='#1a1a1a', labelcolor='white')
        st.pyplot(fig)
        plt.close()

    # Measurements
    st.markdown("---")
    st.subheader("📊 Tissue Measurements")
    measurements = measure_tissues(brain_slice, segmented, tissue_names)
    df = pd.DataFrame(measurements)
    st.dataframe(df, use_container_width=True)

    # Pie chart
    st.subheader("🥧 Tissue Distribution")
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#0a0a0a')
    percentages = [m['Percentage (%)'] for m in measurements]
    ax.pie(percentages, labels=tissue_names, colors=tissue_colors,
           autopct='%1.1f%%', textprops={'color': 'white'})
    ax.set_facecolor('#0a0a0a')
    st.pyplot(fig)
    plt.close()

    # PDF Report generation
    st.markdown("---")
    st.subheader("📄 Generate PDF Report")

    if st.button("🖨️ Generate PDF Report"):
        with st.spinner("Generating report..."):

            # Save chart for PDF
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            fig.patch.set_facecolor('#0a0a0a')
            axes[0].imshow(brain_slice.T, cmap='gray', origin='lower')
            axes[0].set_title('Original MRI', color='white')
            axes[0].axis('off')
            axes[1].imshow(segmented.T, cmap=cmap, origin='lower', vmin=0, vmax=2)
            axes[1].set_title('Segmented', color='white')
            axes[1].axis('off')
            axes[2].pie(percentages, labels=tissue_names, colors=tissue_colors,
                       autopct='%1.1f%%', textprops={'color': 'white'})
            axes[2].set_title('Distribution', color='white')
            plt.tight_layout()
            chart_path = 'temp_chart.png'
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='#0a0a0a')
            plt.close()

            # Generate PDF
            pdf_path = 'MRI_Analysis_Report.pdf'
            doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                   leftMargin=2*cm, rightMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', fontSize=18, fontName='Helvetica-Bold',
                                        alignment=TA_CENTER, spaceAfter=6,
                                        textColor=colors.HexColor('#1a1a2e'))
            subtitle_style = ParagraphStyle('Subtitle', fontSize=11, fontName='Helvetica',
                                           alignment=TA_CENTER, spaceAfter=20,
                                           textColor=colors.HexColor('#444444'))
            heading_style = ParagraphStyle('Heading', fontSize=13, fontName='Helvetica-Bold',
                                          spaceBefore=12, spaceAfter=6,
                                          textColor=colors.HexColor('#1a1a2e'))
            body_style = ParagraphStyle('Body', fontSize=10, fontName='Helvetica',
                                       spaceAfter=6, leading=14)
            story = []
            story.append(Paragraph("MRI Brain Tissue Analysis Report", title_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", subtitle_style))
            story.append(Paragraph("Analyst: Kuljit Singh | Otto Von Guericke University, Magdeburg", subtitle_style))
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("1. Visualisation", heading_style))
            story.append(Image(chart_path, width=16*cm, height=5.5*cm))
            story.append(Paragraph("2. Tissue Measurements", heading_style))
            table_data = [['Tissue Type', 'Voxel Count', 'Percentage (%)', 'Avg Brightness']]
            for m in measurements:
                table_data.append([m['Tissue Type'], f"{m['Voxel Count']:,}",
                                  f"{m['Percentage (%)']:.2f}%", f"{m['Avg Brightness']:.2f}"])
            table = Table(table_data, colWidths=[4.5*cm, 3.5*cm, 4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f5f5f5'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(table)
            doc.build(story)

            # Download button
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            os.unlink(chart_path)

        st.success("✅ Report generated!")
        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"MRI_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )

else:
    # Welcome screen
    st.markdown("## 👋 Welcome to MRI Brain Analysis Tool")
    st.markdown("""
    ### How to use:
    1. 📁 Upload an MRI scan file (**.nii** or **.nii.gz**) using the sidebar
    2. 🔍 Use the slider to navigate through brain slices
    3. 🤖 View automatic tissue segmentation
    4. 📊 See tissue measurements and distribution
    5. 📄 Generate and download a PDF report

    ### Supported formats:
    - NIfTI (.nii)
    - Compressed NIfTI (.nii.gz)

    ### About
    This tool uses **K-means clustering** to automatically segment brain tissue into:
    - 🔵 Background
    - 🔴 Grey Matter
    - 🟡 White Matter
    """)
    st.info("👈 Upload an MRI file in the sidebar to get started!")