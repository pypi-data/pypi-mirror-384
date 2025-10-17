import base64
import os
import subprocess
from tempfile import NamedTemporaryFile

from django.conf import settings
from markdown import markdown


def _html_to_pdf(html_content, output_pdf_path):
    try:
        process = subprocess.Popen(
            [
                "wkhtmltopdf",
                "-",
                output_pdf_path,
            ],  # '-' tells wkhtmltopdf to read from stdin
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(input=html_content.encode("utf-8"))
        if process.returncode != 0:
            print("Error:", stderr.decode("utf-8"))
        else:
            print(f"PDF successfully created at: {output_pdf_path}")
    except FileNotFoundError:
        print("Error: wkhtmltopdf not found. Ensure it is installed and in your PATH.")
    except Exception as e:
        print(f"An error occurred: {e}")


def _generate_pdf_from_methodo(indicator, output_path):
    html = markdown(indicator.methodo)
    relative_logo_path = "whitenoise_root/ministere_logo.png"
    logo_path = os.path.join(settings.BASE_DIR, relative_logo_path)
    with open(logo_path, "rb") as fd:
        encoded_logo = base64.b64encode(fd.read()).decode("utf-8")
    html = (
        """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Accents Test</title>
        <style>
            body {
                font-family: Tahoma, Arial, sans-serif;
            }
        </style>
    </head>
    <body>
    <header>
        <table>
            <tr>
                <td>
                """
        + f'<img width="150px" src="data:image/png;base64,{encoded_logo}"/>'
        + """
                </td>
                <td style="padding-left: 64px;">
                    <div style="font-size: 30px; font-weight: 600; margin-bottom: 8px;">Tableau de bord des mobilités durables</div>
                    <div>Fiche méthodologique</div>
                </td>
            </tr>
        </table>
    </header>
    <main>
    """
        + f"<h1>{indicator.title}</h1>"
        + f"<p>Thématique : {indicator.sub_theme.theme.title} / {indicator.sub_theme.title}</p>"
        + html
        + """
    </main>
    </body>
    </html>
    """
    )
    _html_to_pdf(html, output_path)


def reset_methodo_file(indicator):
    # Create a temporary file for the PDF
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        pdf_path = temp_file.name

    # Generate the PDF
    _generate_pdf_from_methodo(indicator, pdf_path)

    # Read the binary content of the generated PDF file
    with open(pdf_path, "rb") as pdf_file:
        pdf_content = pdf_file.read()

    # Save the binary content to the BinaryField
    indicator.methodo_file = pdf_content
    indicator.save()

    # Clean up temporary file
    os.remove(pdf_path)
