import os
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    @staticmethod
    def generate_report(transactions_list, summary_data, category_spending, health_data, goals_list, file_path="finance_report.pdf"):
        """
        Generates a beautiful multi-page PDF finance report.
        """
        # 1. Generate a temporary chart image using Matplotlib
        chart_path = "temp_pdf_chart.png"
        has_chart = PDFReportGenerator._create_chart(category_spending, chart_path)

        # 2. Setup document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        # Define custom styles
        primary_color = colors.HexColor("#1e1e24")
        accent_color = colors.HexColor("#00adb5")
        text_color = colors.HexColor("#2d3748")
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=primary_color,
            spaceAfter=6
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#718096"),
            spaceAfter=20
        )
        
        section_heading = ParagraphStyle(
            'SectionHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=primary_color,
            spaceBefore=15,
            spaceAfter=8,
            borderPadding=4
        )
        
        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=text_color,
            leading=14
        )
        
        bold_body_style = ParagraphStyle(
            'BoldBodyTextCustom',
            parent=body_style,
            fontName='Helvetica-Bold'
        )

        table_header_style = ParagraphStyle(
            'TableHeaderText',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.white
        )

        story = []

        # --- Header Section ---
        story.append(Paragraph("Smart Finance Management System", title_style))
        report_month = datetime.now().strftime("%B %Y")
        generated_on = datetime.now().strftime("%d %b %Y, %I:%M %p")
        story.append(Paragraph(f"Financial Health Report & Monthly Statement — {report_month} | Generated on {generated_on}", subtitle_style))
        story.append(Spacer(1, 10))

        # --- Executive Summary Cards ---
        story.append(Paragraph("Executive Summary", section_heading))
        
        # Grid of stats
        health_score_str = f"{health_data['score']}/100 ({health_data['status']})"
        summary_table_data = [
            [
                Paragraph("<b>Total Income:</b>", body_style), Paragraph(f"₹{summary_data['income']:,.2f}", bold_body_style),
                Paragraph("<b>Financial Health Score:</b>", body_style), Paragraph(health_score_str, bold_body_style)
            ],
            [
                Paragraph("<b>Total Expenses:</b>", body_style), Paragraph(f"₹{summary_data['expense']:,.2f}", bold_body_style),
                Paragraph("<b>Savings Rate:</b>", body_style), Paragraph(f"{summary_data['savings_rate']}%", bold_body_style)
            ],
            [
                Paragraph("<b>Net Savings:</b>", body_style), Paragraph(f"₹{summary_data['savings']:,.2f}", bold_body_style),
                Paragraph("<b>Current Status:</b>", body_style), Paragraph(health_data['status'], bold_body_style)
            ]
        ]
        
        summary_table = Table(summary_table_data, colWidths=[100, 160, 140, 140])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f7fafc")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#edf2f7")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))

        # --- Category Breakdown and Chart ---
        story.append(Paragraph("Spending by Category", section_heading))
        
        # Create category spending table data
        cat_rows = [[Paragraph("Category", table_header_style), Paragraph("Total Amount Spent (₹)", table_header_style), Paragraph("Percentage of Expenses", table_header_style)]]
        total_exp = max(summary_data['expense'], 1)
        for cat, amt in category_spending.items():
            pct = (amt / total_exp) * 100
            cat_rows.append([
                Paragraph(cat, body_style),
                Paragraph(f"₹{amt:,.2f}", body_style),
                Paragraph(f"{pct:.1f}%", body_style)
            ])
            
        if not category_spending:
            cat_rows.append([Paragraph("No expenses recorded.", body_style), Paragraph("-", body_style), Paragraph("-", body_style)])

        cat_table = Table(cat_rows, colWidths=[110, 100, 90])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f7fafc")]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        # Embed chart side-by-side or stacked
        if has_chart:
            # Table layout to put text on left, chart on right
            chart_img = Image(chart_path, width=220, height=140)
            vis_table_data = [[cat_table, chart_img]]
            vis_table = Table(vis_table_data, colWidths=[310, 230])
            vis_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (1,0), (1,0), 10),
            ]))
            story.append(vis_table)
        else:
            story.append(cat_table)
            
        story.append(Spacer(1, 15))

        # --- Saving Goals Section ---
        if goals_list:
            story.append(Paragraph("Saving Goals Progress", section_heading))
            goal_rows = [[
                Paragraph("Goal Name", table_header_style), 
                Paragraph("Target (₹)", table_header_style), 
                Paragraph("Current Savings (₹)", table_header_style), 
                Paragraph("Progress", table_header_style)
            ]]
            for g in goals_list:
                goal_rows.append([
                    Paragraph(g.name, body_style),
                    Paragraph(f"₹{g.target_amount:,.2f}", body_style),
                    Paragraph(f"₹{g.current_savings:,.2f}", body_style),
                    Paragraph(f"{g.progress_percentage}%", bold_body_style)
                ])
            goal_table = Table(goal_rows, colWidths=[150, 130, 130, 130])
            goal_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), primary_color),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f7fafc")]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(goal_table)
            story.append(Spacer(1, 15))

        # --- Recent Transactions Section (Keep together to avoid orphan tables)
        trans_elements = []
        trans_elements.append(Paragraph("Recent Transactions Ledger", section_heading))
        
        tx_rows = [[
            Paragraph("Date", table_header_style),
            Paragraph("Type", table_header_style),
            Paragraph("Category", table_header_style),
            Paragraph("Amount (₹)", table_header_style),
            Paragraph("Notes", table_header_style)
        ]]
        
        # Limit to last 20 transactions in the report
        for t in transactions_list[:20]:
            type_color = "#10b981" if t.type == "Income" else "#ef4444"
            tx_rows.append([
                Paragraph(t.date, body_style),
                Paragraph(f"<font color='{type_color}'><b>{t.type}</b></font>", body_style),
                Paragraph(t.category, body_style),
                Paragraph(f"₹{t.amount:,.2f}", body_style),
                Paragraph(t.notes if t.notes else "-", body_style)
            ])
            
        if not transactions_list:
            tx_rows.append([Paragraph("No transactions recorded.", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style)])
            
        tx_table = Table(tx_rows, colWidths=[80, 70, 100, 100, 190])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f7fafc")]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        trans_elements.append(tx_table)
        story.append(KeepTogether(trans_elements))

        # Build PDF
        doc.build(story)
        
        # Clean up temporary chart file
        if os.path.exists(chart_path):
            try:
                os.remove(chart_path)
            except Exception:
                pass

    @staticmethod
    def _create_chart(category_spending, file_path):
        """
        Creates a clean pie chart of expense categories for the PDF report.
        """
        if not category_spending:
            return False
            
        try:
            plt.figure(figsize=(4, 2.5), dpi=150)
            categories = list(category_spending.keys())
            amounts = list(category_spending.values())
            
            # Palette
            colors_list = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#6b7280']
            colors_subset = colors_list[:len(categories)]
            
            plt.pie(
                amounts, 
                labels=categories, 
                autopct='%1.1f%%', 
                startangle=140, 
                colors=colors_subset,
                textprops={'fontsize': 6}
            )
            plt.axis('equal')
            plt.tight_layout()
            plt.savefig(file_path, bbox_inches='tight', transparent=True)
            plt.close()
            return True
        except Exception as e:
            print("Error generating PDF chart:", e)
            return False

    @staticmethod
    def generate_invoice(customer_name, product_name, price, gst_rate, payment_method, file_path="invoice.pdf"):
        """
        Generates a beautiful PDF invoice using ReportLab.
        """
        # Calculate pricing
        gst_pct = float(gst_rate.replace("%", "").strip())
        gst_amount = price * (gst_pct / 100.0)
        grand_total = price + gst_amount
        
        # --- Generate temporary pie chart ---
        import tempfile
        temp_dir = tempfile.gettempdir()
        chart_img_path = os.path.join(temp_dir, f"invoice_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        has_chart = False
        
        try:
            fig, ax = plt.subplots(figsize=(2.8, 1.6), dpi=150)
            fig.patch.set_facecolor('white')
            
            if gst_amount == 0:
                labels = ['Base Price (Tax Free)']
                sizes = [price]
                colors_list = ['#10b981']
            else:
                labels = ['Base Price', 'GST Amount']
                sizes = [price, gst_amount]
                colors_list = ['#3b82f6', '#f59e0b']
                
            ax.pie(
                sizes, 
                labels=labels, 
                autopct='%1.1f%%' if gst_amount > 0 else '', 
                startangle=90, 
                colors=colors_list,
                textprops={'fontsize': 6, 'color': '#2d3748', 'weight': 'bold'}
            )
            ax.axis('equal')
            ax.set_title("Value Breakdown", fontsize=7, fontweight='bold', color='#1e1e24')
            plt.tight_layout()
            plt.savefig(chart_img_path, bbox_inches='tight', transparent=True)
            plt.close()
            has_chart = True
        except Exception as e:
            print("Error generating invoice chart:", e)
            has_chart = False
            
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#1e1e24")
        accent_color = colors.HexColor("#00adb5")
        text_color = colors.HexColor("#2d3748")
        
        title_style = ParagraphStyle(
            'InvTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=primary_color,
            spaceAfter=4
        )
        
        meta_style = ParagraphStyle(
            'InvMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4a5568")
        )
        
        section_heading = ParagraphStyle(
            'InvSecHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=primary_color,
            spaceBefore=15,
            spaceAfter=8
        )
        
        body_style = ParagraphStyle(
            'InvBodyText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=text_color,
            leading=14
        )
        
        bold_body_style = ParagraphStyle(
            'InvBoldBodyText',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        table_header_style = ParagraphStyle(
            'InvTableHeaderText',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.white
        )
        
        story = []
        
        # --- Header (Business Logo/Name + Invoice Title) ---
        header_data = [
            [
                Paragraph("<b>SMART RETAIL VENTURES</b><br/>123 Business Hub, MG Road<br/>New Delhi, India<br/>GSTIN: 07TAXIN8429A1Z1", meta_style),
                Paragraph("<b>TAX INVOICE</b><br/>Invoice No: INV-" + datetime.now().strftime("%Y%m%d%H%M") + "<br/>Date: " + datetime.now().strftime("%d %b %Y"), meta_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[270, 270])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # --- Bill To ---
        story.append(Paragraph("<b>BILLED TO:</b>", section_heading))
        bill_to_data = [
            [Paragraph("<b>Customer Name:</b>", body_style), Paragraph(customer_name, body_style)],
            [Paragraph("<b>Payment Method:</b>", body_style), Paragraph(payment_method, body_style)]
        ]
        bill_to_table = Table(bill_to_data, colWidths=[120, 420])
        bill_to_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(bill_to_table)
        story.append(Spacer(1, 20))
        
        # --- Particulars Table ---
        particulars_rows = [
            [
                Paragraph("Item / Description", table_header_style), 
                Paragraph("Rate (₹)", table_header_style), 
                Paragraph("GST Rate", table_header_style), 
                Paragraph("GST Amount (₹)", table_header_style), 
                Paragraph("Total Amount (₹)", table_header_style)
            ],
            [
                Paragraph(product_name, body_style),
                Paragraph(f"₹{price:,.2f}", body_style),
                Paragraph(f"{gst_pct}%", body_style),
                Paragraph(f"₹{gst_amount:,.2f}", body_style),
                Paragraph(f"₹{grand_total:,.2f}", bold_body_style)
            ]
        ]
        part_table = Table(particulars_rows, colWidths=[200, 85, 75, 90, 90])
        part_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e0")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(part_table)
        story.append(Spacer(1, 20))
        
        # --- Totals Box ---
        totals_data = [
            [Paragraph("<b>Sub-Total (Excl. GST):</b>", body_style), Paragraph(f"₹{price:,.2f}", body_style)],
            [Paragraph("<b>CGST + SGST Amount:</b>", body_style), Paragraph(f"₹{gst_amount:,.2f}", body_style)],
            [Paragraph("<b>Grand Total (Incl. GST):</b>", bold_body_style), Paragraph(f"₹{grand_total:,.2f}", bold_body_style)]
        ]
        totals_table = Table(totals_data, colWidths=[150, 100])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#edf2f7")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        
        # Wrap in a side-by-side layout (push totals to the right, chart on the left)
        chart_flowable = Spacer(1, 1)
        if has_chart:
            chart_flowable = Image(chart_img_path, width=180, height=103)
            
        outer_totals_data = [[chart_flowable, totals_table]]
        outer_totals_table = Table(outer_totals_data, colWidths=[290, 250])
        story.append(outer_totals_table)
        story.append(Spacer(1, 40))
        
        # --- Terms and Signature ---
        sig_data = [
            [
                Paragraph("<b>Terms & Conditions:</b><br/>1. Goods once sold will not be taken back.<br/>2. Payment is due immediately.<br/>3. Subject to local jurisdiction.", meta_style),
                Paragraph("For <b>Smart Retail Ventures</b><br/><br/><br/>Authorized Signatory", ParagraphStyle('Sig', parent=meta_style, alignment=2))
            ]
        ]
        sig_table = Table(sig_data, colWidths=[300, 240])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ]))
        story.append(sig_table)
        
        # Build Document
        doc.build(story)
        
        # Clean up chart image
        if has_chart and os.path.exists(chart_img_path):
            try:
                os.remove(chart_img_path)
            except Exception:
                pass
