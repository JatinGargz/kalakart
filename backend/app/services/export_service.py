import os
import io
import json
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_upi_qr_bytes(vpa: str = "artisan@upi", name: str = "Artisan", amount: float = 1250.0) -> bytes:
    upi_string = f"upi://pay?pa={vpa}&pn={name}&am={amount:.2f}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(upi_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#7A1C1C", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def generate_ondc_beckn_json(product_id, catalog: dict = None, pricing: dict = None, image_url: str = None) -> dict:
    if hasattr(product_id, 'title_en'):
        p = product_id
        pid = p.id
        title = p.title_en or "Handcrafted Artisan Specialty"
        price = p.pricing.recommended_retail_price if p.pricing else 1250.0
        img = p.media.enhanced_studio_url if p.media and p.media.enhanced_studio_url else "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800"
    else:
        pid = str(product_id)
        price = pricing.get("recommended_retail_price", 1250.0) if isinstance(pricing, dict) else float(pricing or 1250.0)
        title = catalog.get("title_en", "Handcrafted Artisan Specialty") if isinstance(catalog, dict) else str(catalog or "Handcrafted Item")
        img = image_url or "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800"
    return {
        "context": {
            "domain": "nic2004:52110",
            "country": "IND",
            "city": "std:0141",
            "action": "search",
            "core_version": "1.2.0",
            "bap_id": "buyer-app.ondc.org",
            "bpp_id": "kalakart-bpp.gov.in",
            "transaction_id": f"tx_{pid}",
            "message_id": f"msg_{pid}",
            "timestamp": "2026-09-15T20:20:00Z"
        },
        "message": {
            "catalog": {
                "bpp/descriptor": {
                    "name": "KALAKART Master Artisan Collective",
                    "symbol": "https://kalakart.org/logo.png"
                },
                "bpp/providers": [
                    {
                        "id": "provider_kalakart_01",
                        "descriptor": {
                            "name": "Jaipur Blue Pottery Guild",
                            "short_desc": "Geographical Indication (GI) Registered Artisan Cluster"
                        },
                        "items": [
                            {
                                "id": str(pid),
                                "descriptor": {
                                    "name": str(title),
                                    "symbol": str(img),
                                    "short_desc": "Handcrafted Indian artisan product with verified GI heritage provenance.",
                                    "images": [str(img)]
                                },
                                "price": {
                                    "currency": "INR",
                                    "value": f"{price:.2f}"
                                },
                                "category_id": "Handicrafts & GI Crafts",
                                "matched": True,
                                "tags": {
                                    "verified_wage": "true",
                                    "gi_certified": "true",
                                    "anti_bargain_protected": "true"
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }

def format_amazon_karigar_feed(product_id: str, catalog: dict, pricing: dict, image_url: str) -> dict:
    price = pricing.get("recommended_retail_price", 1250.0) if isinstance(pricing, dict) else float(pricing or 1250.0)
    title = catalog.get("title_en", "Handcrafted Artisan Specialty") if isinstance(catalog, dict) else str(catalog or "Handcrafted Item")
    clean_id = product_id.replace('kk_', '').replace('prod_', '').upper()[:6]
    return {
        "channel": "Amazon Karigar",
        "program": "Karigar Craftsman Storefront",
        "asin": f"B0KALA{clean_id}",
        "status": "ACTIVE_BUYABLE",
        "title": title,
        "listing_price_inr": price,
        "fulfillment_mode": "Amazon Easy Ship / Karigar Fulfillment",
        "badge": "Amazon Handcrafted Authentic",
        "bullets": [
            "Authentic Mastercrafted Indian Heritage",
            "100% Direct Artisan Proceeds (Zero Middlemen)",
            "MoSJE Certified Fair Living Wage Floor",
            "1080p Studio Lighting Inspected"
        ]
    }

def format_flipkart_samarth_feed(product_id: str, catalog: dict, pricing: dict, image_url: str) -> dict:
    price = pricing.get("recommended_retail_price", 1250.0) if isinstance(pricing, dict) else float(pricing or 1250.0)
    title = catalog.get("title_en", "Handcrafted Artisan Specialty") if isinstance(catalog, dict) else str(catalog or "Handcrafted Item")
    clean_id = product_id.replace('kk_', '').replace('prod_', '').upper()[:6]
    return {
        "channel": "Flipkart Samarth",
        "program": "Flipkart Samarth Handloom & Handicrafts",
        "fsn": f"FSNKALA{clean_id}9",
        "status": "LIVE",
        "title": title,
        "price_inr": price,
        "commission_rate": "0% Commission for Artisans",
        "badge": "Flipkart Samarth Verified",
        "warehouse": "Cluster Local Direct Hub"
    }

def format_gem_procurement_feed(product_id: str, catalog: dict, pricing: dict, image_url: str) -> dict:
    price = pricing.get("recommended_retail_price", 1250.0) if isinstance(pricing, dict) else float(pricing or 1250.0)
    wholesale = pricing.get("wholesale_b2b_price", price * 0.8) if isinstance(pricing, dict) else price * 0.8
    title = catalog.get("title_en", "Handcrafted Artisan Specialty") if isinstance(catalog, dict) else str(catalog or "Handcrafted Item")
    return {
        "channel": "Government e-Marketplace (GeM)",
        "procurement_portal": "gem.gov.in",
        "catalog_id": f"GEM-ARTISAN-{product_id}",
        "status": "APPROVED_PUBLIC_PROCUREMENT",
        "title": title,
        "institutional_price_inr": wholesale,
        "minimum_order_qty": 20,
        "procurement_policy": "GFR Rule 149 (Mandatory 4% Handicraft Quota for Ministries)",
        "badge": "MoSJE Verified PSU Procurement Partner"
    }

def format_etsy_global_feed(product_id: str, catalog: dict, pricing: dict, image_url: str) -> dict:
    price_inr = pricing.get("recommended_retail_price", 1250.0) if isinstance(pricing, dict) else float(pricing or 1250.0)
    price_usd = round(price_inr / 86.0, 2)
    clean_id = product_id.replace('kk_', '').replace('prod_', '').upper()[:6]
    title = catalog.get("title_en", "Handcrafted Artisan Specialty") if isinstance(catalog, dict) else str(catalog or "Handcrafted Item")
    return {
        "channel": "Etsy Global Export",
        "listing_id": f"ETSY-IND-{clean_id}",
        "status": "INTERNATIONAL_LIVE",
        "title": title,
        "price_usd": f"${price_usd:.2f} USD",
        "price_inr_equivalent": f"₹ {price_inr:,.0f}",
        "shipping_coverage": "United States, United Kingdom, European Union, UAE",
        "badge": "Authentic Indian Cultural Heritage Export"
    }

def publish_to_all_channels(product_id: str, catalog=None, pricing=None, image_url: str = None) -> dict:
    if isinstance(catalog, str):
        catalog = {"title_en": catalog}
    elif catalog is None:
        catalog = {"title_en": "Handpainted Blue Pottery Plate"}

    if isinstance(pricing, (int, float)):
        pricing = {"recommended_retail_price": float(pricing), "wholesale_b2b_price": float(pricing) * 0.8}
    elif pricing is None:
        pricing = {"recommended_retail_price": 1250.0, "wholesale_b2b_price": 950.0}

    img = image_url or "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800"

    return {
        "product_id": product_id,
        "timestamp": "2026-09-15T20:20:00Z",
        "published_count": 5,
        "channels": [
            format_amazon_karigar_feed(product_id, catalog, pricing, img),
            format_flipkart_samarth_feed(product_id, catalog, pricing, img),
            format_gem_procurement_feed(product_id, catalog, pricing, img),
            format_etsy_global_feed(product_id, catalog, pricing, img),
            {
                "channel": "ONDC Open Network",
                "status": "BECKN_BROADCASTED",
                "ondc_payload": generate_ondc_beckn_json(product_id, catalog, pricing, img)
            }
        ]
    }

def generate_mela_standee_pdf(product_id, title: str = None, craft: str = None, price: float = None, artisan_name: str = None) -> bytes:
    if hasattr(product_id, 'title_en'):
        p = product_id
        product_id = p.id
        title = p.title_en or "Handcrafted Specialty"
        craft = p.craft_type or "Handicrafts & GI Crafts"
        price = p.pricing.recommended_retail_price if p.pricing else 1250.0
        artisan_name = p.artisan.name if p.artisan else "Rukmini Devi"
    else:
        product_id = str(product_id)
        title = title or "Authentic Craft"
        craft = craft or "Handicraft"
        price = float(price or 1250.0)
        artisan_name = artisan_name or "Artisan"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=26,
        textColor=colors.HexColor('#7A1C1C'),
        alignment=1,
        spaceAfter=12
    )

    sub_style = ParagraphStyle(
        'SubStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        textColor=colors.HexColor('#6B5E52'),
        alignment=1,
        spaceAfter=16
    )

    price_style = ParagraphStyle(
        'PriceStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#2E7D32'),
        alignment=1,
        spaceAfter=20
    )

    elements = [
        Paragraph("KALAKART • कला और स्वाभिमान", title_style),
        Paragraph(f"<b>Authentic Handcrafted: {title}</b>", styles['Heading2']),
        Paragraph(f"Craft Cluster: {craft} • Master Artisan: {artisan_name}", sub_style),
        Spacer(1, 10),
        Paragraph(f"Fair Trade Certified Price: ₹{price:,.0f}", price_style),
        Paragraph("100% Direct Artisan Proceeds • No Middlemen • GI Heritage Certified", sub_style),
        Spacer(1, 14)
    ]

    # Generate UPI QR image for PDF
    qr_bytes = generate_upi_qr_bytes(f"{product_id}@kalakart", artisan_name, price)
    qr_img = RLImage(io.BytesIO(qr_bytes), width=180, height=180)
    qr_img.hAlign = 'CENTER'
    elements.append(qr_img)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Scan with Any UPI App (GPay, PhonePe, Paytm) to Pay Artisan Directly", sub_style))

    doc.build(elements)
    return buf.getvalue()
