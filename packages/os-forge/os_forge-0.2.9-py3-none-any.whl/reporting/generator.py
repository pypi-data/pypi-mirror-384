"""
Report Generation Module

Handles HTML and PDF report generation for compliance reporting.
"""

from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

# Note: Avoid importing database models here to keep this module reusable.
# The report generator accepts either dict-like results (as returned by the API)
# or ORM objects exposing attribute access with similar field names.


class ReportGenerator:
    """
    Generate compliance reports in HTML and PDF formats
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_html_report(self, results: List[Any], os_info: str) -> str:
        """
        Generate HTML compliance report
        
        Args:
            results: List of hardening results
            os_info: Operating system information
            
        Returns:
            str: HTML report content
        """
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>OS Forge Compliance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
                .rule {{ margin-bottom: 15px; padding: 15px; border-left: 4px solid #ddd; }}
                .pass {{ border-left-color: #4CAF50; background: #f1f8e9; }}
                .fail {{ border-left-color: #f44336; background: #ffebee; }}
                .error {{ border-left-color: #ff9800; background: #fff3e0; }}
                .severity-high {{ font-weight: bold; color: #d32f2f; }}
                .severity-medium {{ color: #f57c00; }}
                .severity-low {{ color: #388e3c; }}
                .severity-critical {{ font-weight: bold; color: #b71c1c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>OS Forge Compliance Report</h1>
                <p>Generated: {timestamp}</p>
                <p>System: {os_info}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Checks:</strong> {total}</p>
                <p><strong>Passed:</strong> {passed}</p>
                <p><strong>Failed:</strong> {failed}</p>
                <p><strong>Errors:</strong> {errors}</p>
                <p><strong>Compliance Score:</strong> {score:.1f}%</p>
            </div>
            
            <div class="results">
                <h2>Detailed Results</h2>
                {results_html}
            </div>
        </body>
        </html>
        """
        
        # Access helpers to support both dicts and objects
        def get_field(item: Any, name: str, default: Any = None) -> Any:
            if isinstance(item, dict):
                return item.get(name, default)
            return getattr(item, name, default)

        # Calculate summary with proper status handling
        total = len(results)
        passed = 0
        failed = 0
        errors = 0
        
        for r in results:
            status = get_field(r, "status", "")
            # Handle both string and enum values
            if hasattr(status, 'value'):
                status_str = str(status.value).lower()
            else:
                status_str = str(status).lower()
            
            if status_str == "pass":
                passed += 1
            elif status_str == "fail":
                failed += 1
            elif status_str == "error":
                errors += 1
        
        score = (passed / total * 100) if total > 0 else 0
        
        # Generate results HTML
        results_html = ""
        for result in results:
            status = get_field(result, "status", "")
            # Handle both string and enum values
            if hasattr(status, 'value'):
                status_str = str(status.value).lower()
            else:
                status_str = str(status).lower()
            
            severity = get_field(result, "severity", "")
            # Handle both string and enum values
            if hasattr(severity, 'value'):
                severity_str = str(severity.value).lower()
            else:
                severity_str = str(severity).lower()
            
            status_class = status_str
            severity_class = f"severity-{severity_str}"
            rule_id = get_field(result, "rule_id", "")
            description = get_field(result, "description", "")
            timestamp_val = get_field(result, "timestamp", "")
            # Render timestamp safely
            try:
                from datetime import datetime as _dt
                if isinstance(timestamp_val, _dt):
                    ts_str = timestamp_val.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    ts_str = str(timestamp_val)
            except Exception:
                ts_str = str(timestamp_val)
            old_value = get_field(result, "old_value", None)
            new_value = get_field(result, "new_value", None)
            
            results_html += f"""
            <div class="rule {status_class}">
                <h3>{rule_id}: {description}</h3>
                <p><strong>Severity:</strong> <span class="{severity_class}">{severity_str.upper()}</span></p>
                <p><strong>Status:</strong> {status_str.upper()}</p>
                <p><strong>Timestamp:</strong> {ts_str}</p>
                {f'<p><strong>Current Value:</strong> {old_value}</p>' if old_value else ''}
                {f'<p><strong>New Value:</strong> {new_value}</p>' if new_value and new_value != old_value else ''}
            </div>
            """
        
        return html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            os_info=os_info,
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            score=score,
            results_html=results_html
        )
    
    def generate_pdf_report(self, results: List[Any], os_info: str) -> BytesIO:
        """
        Generate PDF compliance report
        
        Args:
            results: List of hardening results
            os_info: Operating system information
            
        Returns:
            BytesIO: PDF report data
        """
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("OS Forge Compliance Report", title_style))
        story.append(Spacer(1, 20))
        
        # Metadata
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(Paragraph(f"<b>System:</b> {os_info}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Access helpers to support both dicts and objects
        def get_field(item: Any, name: str, default: Any = None) -> Any:
            if isinstance(item, dict):
                return item.get(name, default)
            return getattr(item, name, default)

        # Summary with proper status handling
        total = len(results)
        passed = 0
        failed = 0
        errors = 0
        
        for r in results:
            status = get_field(r, "status", "")
            # Handle both string and enum values
            if hasattr(status, 'value'):
                status_str = str(status.value).lower()
            else:
                status_str = str(status).lower()
            
            if status_str == "pass":
                passed += 1
            elif status_str == "fail":
                failed += 1
            elif status_str == "error":
                errors += 1
        
        score = (passed / total * 100) if total > 0 else 0
        
        story.append(Paragraph("Executive Summary", self.styles['Heading2']))
        
        # Summary table
        summary_data = [
            ['Metric', 'Count', 'Percentage'],
            ['Total Checks', str(total), '100%'],
            ['Passed', str(passed), f'{passed/total*100:.1f}%' if total > 0 else '0%'],
            ['Failed', str(failed), f'{failed/total*100:.1f}%' if total > 0 else '0%'],
            ['Errors', str(errors), f'{errors/total*100:.1f}%' if total > 0 else '0%'],
            ['Compliance Score', f'{score:.1f}%', '']
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Detailed results
        story.append(Paragraph("Detailed Results", self.styles['Heading2']))
        
        if results:
            # Results table
            results_data = [['Rule ID', 'Description', 'Severity', 'Status', 'Timestamp']]
            
            for result in results[:20]:  # Limit to first 20 for PDF
                rule_id = get_field(result, "rule_id", "")
                description = get_field(result, "description", "")
                
                # Handle severity properly
                severity_val = get_field(result, "severity", "")
                if hasattr(severity_val, 'value'):
                    severity_str = str(severity_val.value).upper()
                else:
                    severity_str = str(severity_val).upper()
                
                # Handle status properly
                status_val = get_field(result, "status", "")
                if hasattr(status_val, 'value'):
                    status_str = str(status_val.value).upper()
                else:
                    status_str = str(status_val).upper()
                
                timestamp_val = get_field(result, "timestamp", "")
                try:
                    from datetime import datetime as _dt
                    ts_str = timestamp_val.strftime('%Y-%m-%d %H:%M') if isinstance(timestamp_val, _dt) else str(timestamp_val)
                except Exception:
                    ts_str = str(timestamp_val)

                results_data.append([
                    rule_id,
                    (description[:50] + "...") if isinstance(description, str) and len(description) > 50 else description,
                    severity_str,
                    status_str,
                    ts_str
                ])
            
            results_table = Table(results_data, colWidths=[1*inch, 3*inch, 1*inch, 1*inch, 1.5*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(results_table)
        else:
            story.append(Paragraph("No results available. Run a security check first.", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer

