import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as ReportLabImage, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from image_processing import detect_changes, create_overlay_image, generate_change_visualization

def generate_pdf_report(image_filenames, polygon_coords, start_date, end_date, folder_name):
    if not image_filenames or len(image_filenames) < 4:
        print("❌ Not enough images to generate a report")
        return None

    # Sort image filenames to ensure they are in order
    image_filenames.sort()

    # Define the paths for the images and analysis
    first_image_path = os.path.join(folder_name, image_filenames[0])
    last_image_path = os.path.join(folder_name, image_filenames[-1])
    analysis_path = os.path.join(folder_name, "change_analysis.png")

    # Generate the change visualization
    generate_change_visualization(first_image_path, last_image_path, analysis_path)

    # Select images for the report
    middle_idx = len(image_filenames) // 2
    second_image = image_filenames[middle_idx // 2]
    third_image = image_filenames[middle_idx]
    fourth_image = image_filenames[-1]

    # Detect changes between images
    first_middle_mask = detect_changes(
        os.path.join(folder_name, image_filenames[0]),
        os.path.join(folder_name, third_image)
    )
    middle_last_mask = detect_changes(
        os.path.join(folder_name, third_image),
        os.path.join(folder_name, fourth_image)
    )

    # Create overlay images
    overlay1_path = os.path.join(folder_name, "overlay1.png")
    overlay2_path = os.path.join(folder_name, "overlay2.png")
    create_overlay_image(
        os.path.join(folder_name, third_image),
        first_middle_mask,
        overlay1_path
    )
    create_overlay_image(
        os.path.join(folder_name, fourth_image),
        middle_last_mask,
        overlay2_path
    )

    # Define the path for the PDF report
    report_path = os.path.join(folder_name, "satellite_report.pdf")

    # Create the PDF document
    doc = SimpleDocTemplate(
        report_path,
        pagesize=landscape(letter),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    # Define styles for the PDF content
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1
    subtitle_style = styles['Heading2']
    subtitle_style.alignment = 1
    normal_style = styles['Normal']
    arabic_style = ParagraphStyle(
        'ArabicStyle',
        parent=styles['Normal'],
        alignment=2,
        fontName='Helvetica-Bold',
        fontSize=12
    )
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray
    )

    # Create the content for the PDF
    content = []
    content.append(Paragraph("Satellite Imagery Change Analysis Report", title_style))
    content.append(Spacer(1, 0.25*inch))

    # Add report generation date and analysis period
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_data = [
        ["Report Generated:", report_date, "Analysis Period:", f"{start_date} to {end_date}"],
        ["Location:", f"Coordinates: {polygon_coords[0][0]}", "Analysis Type:", "Vegetation, Urban, Water Changes"],
        ["Satellite/Sensor:", "Sentinel-2", "Cloud Cover:", "Less than 10%"]
    ]
    header_table = Table(header_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
    ]))
    content.append(header_table)
    content.append(Spacer(1, 0.5*inch))

    # Add the analysis overview
    content.append(Paragraph("Satellite Image Change Analysis Overview", subtitle_style))
    content.append(Spacer(1, 0.25*inch))
    if os.path.exists(analysis_path):
        analysis_img = ReportLabImage(analysis_path, width=8*inch, height=2.5*inch)
        content.append(analysis_img)
    else:
        content.append(Paragraph("Analysis visualization could not be generated", normal_style))
    content.append(Spacer(1, 0.5*inch))

    # Add detailed change analysis
    content.append(Paragraph("Detailed Change Analysis", subtitle_style))
    content.append(Spacer(1, 0.25*inch))
    image_table_data = [
        [Paragraph(f"Base Image ({image_filenames[0].replace('.png', '')})", normal_style),
         Paragraph(f"Mid-Period Changes ({third_image.replace('.png', '')})", normal_style)],
        [ReportLabImage(first_image_path, width=4*inch, height=3*inch),
         ReportLabImage(overlay1_path, width=4*inch, height=3*inch)],
        [Paragraph(f"Mid-Period Image ({third_image.replace('.png', '')})", normal_style),
         Paragraph(f"Latest Period Changes ({fourth_image.replace('.png', '')})", normal_style)],
        [ReportLabImage(os.path.join(folder_name, third_image), width=4*inch, height=3*inch),
         ReportLabImage(overlay2_path, width=4*inch, height=3*inch)]
    ]
    image_table = Table(image_table_data, colWidths=[4.5*inch, 4.5*inch])
    image_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
    ]))
    content.append(image_table)
    content.append(Spacer(1, 0.5*inch))

    # Add change analysis legend
    content.append(Paragraph("Change Analysis Legend", subtitle_style))
    legend_data = [
        ["Color", "Change Type", "Description"],
        ["Green", "Vegetation Changes", "Areas where vegetation has increased or decreased"],
        ["Red", "Urban Development", "New construction, buildings, or infrastructure"],
        ["Blue", "Water Bodies", "Changes in water levels, reservoirs, or water features"]
    ]
    legend_table = Table(legend_data, colWidths=[1*inch, 2*inch, 6*inch])
    legend_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, 1), colors.green),
        ('BACKGROUND', (0, 2), (0, 2), colors.red),
        ('BACKGROUND', (0, 3), (0, 3), colors.blue),
    ]))
    content.append(legend_table)

    # Add disclaimer and footer
    disclaimer_text = "Disclaimer: This is not an official map. The satellite imagery and analysis are for informational purposes only."
    footer_text = f"{disclaimer_text} | Generated using Sentinel-2 imagery | Analysis period: {start_date} to {end_date}"
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(inch, 0.5*inch, footer_text)
        canvas.restoreState()

    # Build the PDF document
    doc.build(content, onFirstPage=add_footer, onLaterPages=add_footer)
    print(f"✅ PDF report generated: {report_path}")
    return report_path
