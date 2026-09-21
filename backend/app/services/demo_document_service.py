import os
import fitz  # PyMuPDF
from app.core.logging import logger

SAMPLE_DOC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/demo"))
SAMPLE_PDF_PATH = os.path.join(SAMPLE_DOC_DIR, "sample_rental_agreement.pdf")

RENTAL_AGREEMENT_PAGES = [
    # Page 1
    (
        "SAMPLE RESIDENTIAL RENTAL AGREEMENT — FICTIONAL DEMO\n\n"
        "DISCLAIMER: Fictional demonstration document. Not actual legal advice or a real legal agreement.\n"
        "This agreement is created strictly for non-confidential software testing and algorithmic evaluation.\n\n"
        "PARTIES & PREMISES:\n"
        "This Residential Rental Agreement (\"Agreement\") is made on September 1, 2026, by and between\n"
        "Metropolis Property Holdings LLC (\"Landlord\") and Jonathan Vance (\"Tenant\"). Landlord leases\n"
        "to Tenant the property at 452 Lexington Avenue, Apt 4B, New York, NY 10017 (\"Premises\").\n\n"
        "ARTICLE 1: TERM OF LEASE\n"
        "Section 1.1: Initial Term. The term of this lease shall commence on October 1, 2026, and shall\n"
        "terminate at 11:59 PM on September 30, 2027 (the \"Initial Term\"), unless terminated earlier.\n"
        "Section 1.2: Renewal Conditions. Tenant shall have the option to renew this Agreement for an\n"
        "additional twelve (12) month term, provided that:\n"
        "  (a) Tenant provides written notice of intent to renew at least forty-five (45) days prior to\n"
        "      expiration of the Initial Term; and\n"
        "  (b) Tenant is not in material breach or default of any covenant or obligation under this Agreement.\n\n"
        "ARTICLE 2: RENT AND PAYMENT TERMS\n"
        "Section 2.1: Monthly Rent. Tenant agrees to pay base monthly rent of Two Thousand Five Hundred\n"
        "Dollars ($2,500.00) USD per month (\"Monthly Rent\").\n"
        "Section 2.2: Payment Deadline. Monthly Rent is due and payable on or before the first (1st)\n"
        "calendar day of each month (\"Payment Deadline\") via electronic transfer.\n"
        "Section 2.3: Late Payment Penalty. If Monthly Rent is not received by 11:59 PM on the fifth (5th)\n"
        "calendar day of the month, a late fee of One Hundred Dollars ($100.00) USD shall be assessed.\n"
    ),

    # Page 2
    (
        "SAMPLE RESIDENTIAL RENTAL AGREEMENT — FICTIONAL DEMO (PAGE 2)\n\n"
        "ARTICLE 3: SECURITY DEPOSIT\n"
        "Section 3.1: Security Deposit Amount. Upon signing, Tenant shall deposit Two Thousand Five Hundred\n"
        "Dollars ($2,500.00) USD as a security deposit (\"Security Deposit\").\n"
        "Section 3.2: Use and Return. Held in an interest-bearing escrow account in New York. Returned within\n"
        "thirty (30) days following surrender of the Premises, less lawful deductions for damage or unpaid rent.\n\n"
        "ARTICLE 4: MAINTENANCE AND REPAIRS\n"
        "Section 4.1: Tenant Maintenance Responsibilities. Tenant shall keep the interior clean and is\n"
        "responsible for minor repairs costing under One Hundred Dollars ($100.00) USD.\n"
        "Section 4.2: Landlord Maintenance Responsibilities. Landlord shall maintain building systems, including\n"
        "structural foundations, roof, plumbing, heating, electrical, and HVAC.\n"
        "Section 4.3: Exceptions and Habitability. Provided that in cases of emergency affecting health\n"
        "and safety (such as loss of heat or active water flooding), Landlord shall initiate corrective repairs\n"
        "within twenty-four (24) hours of notice.\n\n"
        "ARTICLE 5: TERMINATION AND NOTICE\n"
        "Section 5.1: Termination Notice Period. Either party may terminate this Agreement by serving a minimum\n"
        "of sixty (60) days prior written notice (\"Termination Notice\") upon the other party.\n"
        "Section 5.2: Early Termination. If Tenant vacates early without consent, Tenant remains liable for rent\n"
        "until Premises are re-leased or term expires, subject to Landlord's duty to mitigate.\n"
    ),

    # Page 3
    (
        "SAMPLE RESIDENTIAL RENTAL AGREEMENT — FICTIONAL DEMO (PAGE 3)\n\n"
        "ARTICLE 6: DISPUTE RESOLUTION AND GOVERNING LAW\n"
        "Section 6.1: Informal Negotiation. Parties agree to first engage in good faith informal negotiation\n"
        "for not less than thirty (30) consecutive calendar days prior to legal proceedings.\n"
        "Section 6.2: Binding Arbitration. If informal negotiation fails, disputes shall be settled by binding\n"
        "arbitration administered by the American Arbitration Association (AAA) in New York, New York.\n"
        "Section 6.3: Governing Law. This Agreement shall be governed by the laws of the State of New York.\n\n"
        "ARTICLE 7: MISCELLANEOUS PROVISIONS\n"
        "Section 7.1: Entire Agreement. Contains the entire understanding and supersedes all prior agreements.\n"
        "Section 7.2: Amendments. No amendment is effective unless made in writing and signed by both parties.\n\n"
        "IN WITNESS WHEREOF, the parties hereto have executed this Agreement.\n"
        "LANDLORD: Metropolis Property Holdings LLC\n"
        "TENANT: Jonathan Vance\n"
    )
]


def generate_sample_rental_agreement_pdf(destination_path: str = SAMPLE_PDF_PATH) -> str:
    """
    Generate a clean multi-page synthetic rental agreement PDF for demo & evaluation.
    Returns the absolute path to the generated PDF.
    """
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    doc = fitz.open()

    for page_text in RENTAL_AGREEMENT_PAGES:
        page = doc.new_page(width=612, height=792)  # Standard Letter size: 8.5 x 11 inches
        rect = fitz.Rect(54, 54, 558, 738)  # 0.75-inch margins
        page.insert_textbox(
            rect,
            page_text,
            fontsize=10,
            fontname="helv",
            color=(0.1, 0.1, 0.12),
            align=fitz.TEXT_ALIGN_LEFT
        )

    doc.save(destination_path)
    doc.close()
    logger.info(f"Synthetic demo rental agreement generated at: {destination_path}")
    return destination_path


def get_sample_rental_agreement_bytes() -> bytes:
    """Read or generate the synthetic rental agreement PDF bytes."""
    if not os.path.exists(SAMPLE_PDF_PATH):
        generate_sample_rental_agreement_pdf(SAMPLE_PDF_PATH)
    with open(SAMPLE_PDF_PATH, "rb") as f:
        return f.read()
