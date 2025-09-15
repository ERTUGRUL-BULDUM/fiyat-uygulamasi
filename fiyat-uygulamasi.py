import streamlit as st
import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import io
import base64

# Türkçe karakter dönüşüm fonksiyonu
def fix_turkish_chars(text):
    """Türkçe karakterleri düzelt"""
    replacements = {
        'ç': 'c', 'Ç': 'C',
        'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'I': 'I', 
        'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U'
    }
    for tr_char, en_char in replacements.items():
        text = text.replace(tr_char, en_char)
    return text

# Sayfa ayarları
st.set_page_config(
    page_title="Buldumlar Biber & Baharat - Fiyat Teklifi",
    page_icon="🌶️",
    layout="wide"
)

# CSS stil
st.markdown("""
<style>
    .main-header {
        background-color: #2c1810;
        color: #dc3545;
        padding: 20px;
        text-align: center;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .stButton>button {
        background-color: #dc3545;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Başlık
st.markdown('<div class="main-header"><h1>🌶️ FIYAT TEKLIFI OLUSTURUCU</h1><p>Buldumlar Biber & Baharat Entegre Tesisleri</p></div>', unsafe_allow_html=True)

# Session state başlatma
if 'products' not in st.session_state:
    st.session_state.products = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# Sidebar
with st.sidebar:
    st.header("📋 Islemler")
    if st.button("🗑️ Tum Urunleri Temizle"):
        if st.session_state.products:
            st.session_state.products.clear()
            st.session_state.editing_index = None
            st.success("Tum urunler silindi!")
        else:
            st.info("Zaten hic urun yok!")

# Ana içerik
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("👥 Musteri Bilgileri")
    customer_company = st.text_input("Musteri Firma Adi", placeholder="Ornek: Saloon Burger")
    contact_person = st.text_input("Ilgili Kisi", placeholder="Ornek: Mehmet Yilmaz")
    
    st.subheader("🛒 Urun Ekle/Duzenle")
    
    # Düzenleme kontrolü
    if st.session_state.editing_index is not None:
        editing_product = st.session_state.products[st.session_state.editing_index]
        default_name = editing_product['name']
        default_price = editing_product['unit_price']
        default_vat = editing_product['vat_rate']
        button_text = "✏️ Urunu Guncelle"
        button_color = "secondary"
    else:
        default_name = ""
        default_price = 0.0
        default_vat = 20.0
        button_text = "➕ Urun Ekle"
        button_color = "primary"
    
    product_name = st.text_input("Urun Adi", value=default_name, placeholder="Ornek: Karabiber")
    
    col_price, col_vat = st.columns([2, 1])
    with col_price:
        unit_price = st.number_input("Kilogram Fiyati (KDV Haric)", value=default_price, min_value=0.0, step=0.01)
    with col_vat:
        vat_rate = st.number_input("KDV (%)", value=default_vat, min_value=0.0, max_value=100.0, step=1.0)
    
    # Butonlar
    col_btn1, col_btn2 = st.columns([1, 1])
    
    with col_btn1:
        if st.button(button_text, type=button_color):
            if product_name.strip():
                vat_price = unit_price * (1 + vat_rate / 100)
                
                product = {
                    'name': product_name.strip(),
                    'unit_price': unit_price,
                    'vat_rate': vat_rate,
                    'vat_price': vat_price
                }
                
                if st.session_state.editing_index is not None:
                    st.session_state.products[st.session_state.editing_index] = product
                    st.session_state.editing_index = None
                    st.success(f"'{product_name}' guncellendi!")
                    st.rerun()
                else:
                    st.session_state.products.append(product)
                    st.rerun()
            else:
                st.error("Urun adi bos olamaz!")
    
    with col_btn2:
        if st.session_state.editing_index is not None:
            if st.button("❌ Iptal"):
                st.session_state.editing_index = None
                st.rerun()

with col2:
    st.subheader("📦 Eklenen Urunler")
    
    if st.session_state.products:
        # DataFrame gösterimi
        df_data = []
        for i, product in enumerate(st.session_state.products):
            df_data.append({
                'No': i + 1,
                'Urun Adi': product['name'],
                'KDV Haric (TL/kg)': f"{product['unit_price']:.2f}",
                'KDV %': f"{product['vat_rate']:.0f}",
                'KDV Dahil (TL/kg)': f"{product['vat_price']:.2f}"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # İşlem butonları
        st.write("**Islemler:**")
        for i, product in enumerate(st.session_state.products):
            col_edit, col_delete, col_info = st.columns([1, 1, 3])
            
            with col_edit:
                if st.button(f"✏️", key=f"edit_{i}", help="Duzenle"):
                    st.session_state.editing_index = i
                    st.rerun()
            
            with col_delete:
                if st.button(f"🗑️", key=f"delete_{i}", help="Sil"):
                    deleted_name = st.session_state.products[i]['name']
                    st.session_state.products.pop(i)
                    if st.session_state.editing_index == i:
                        st.session_state.editing_index = None
                    elif st.session_state.editing_index is not None and st.session_state.editing_index > i:
                        st.session_state.editing_index -= 1
                    st.success(f"'{deleted_name}' silindi!")
                    st.rerun()
            
            with col_info:
                st.write(f"{i+1}. {product['name']}")
        
        st.write(f"**Toplam: {len(st.session_state.products)} urun**")
    else:
        st.info("Henuz urun eklenmemis. Soldan urun bilgilerini doldurup 'Urun Ekle' butonuna tiklayin.")

# PDF Oluşturma Bölümü
st.divider()
st.subheader("📄 PDF Olustur")

if st.session_state.products and customer_company.strip():
    if st.button("📋 PDF TEKLIFI OLUSTUR", type="primary", use_container_width=True):
        try:
            # Logo watermark fonksiyonu
            def create_watermark_logo():
                logo_files = ['logo.png', 'logo.jpg', 'logo.jpeg', 'Logo.png', 'LOGO.png']
                for logo_file in logo_files:
                    if os.path.exists(logo_file):
                        try:
                            with PILImage.open(logo_file) as img:
                                if img.mode != 'RGBA':
                                    img = img.convert('RGBA')
                                
                                img.thumbnail((350, 350), PILImage.Resampling.LANCZOS)
                                canvas = PILImage.new('RGBA', (400, 400), (0, 0, 0, 0))
                                x = (400 - img.size[0]) // 2
                                y = (400 - img.size[1]) // 2
                                canvas.paste(img, (x, y), img)
                                
                                # Şeffaflık
                                pixels = canvas.load()
                                for i in range(canvas.size[0]):
                                    for j in range(canvas.size[1]):
                                        r, g, b, a = pixels[i, j]
                                        pixels[i, j] = (r, g, b, int(a * 0.25))
                                
                                temp_path = "temp_watermark.png"
                                canvas.save(temp_path, 'PNG')
                                return temp_path
                        except:
                            continue
                return None
            
            # PDF oluştur
            filename = f"fiyat_teklifi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
            story = []
            
            # Stiller
            company_style = ParagraphStyle('CompanyStyle', fontName='Helvetica-Bold', fontSize=16,
                                          spaceAfter=25, alignment=TA_CENTER,
                                          textColor=colors.Color(0.86, 0.24, 0.26))
            
            title_style = ParagraphStyle('TitleStyle', fontName='Helvetica-Bold', fontSize=18,
                                        spaceAfter=20, alignment=TA_CENTER,
                                        textColor=colors.Color(0.86, 0.24, 0.26))
            
            left_style = ParagraphStyle('LeftStyle', fontName='Helvetica', fontSize=10,
                                       spaceAfter=4, alignment=TA_LEFT, leftIndent=0)
            
            heading_style = ParagraphStyle('HeadingStyle', fontName='Helvetica-Bold', fontSize=12,
                                          spaceAfter=8, textColor=colors.Color(0.86, 0.24, 0.26))
            
            normal_style = ParagraphStyle('NormalStyle', fontName='Helvetica', fontSize=10, spaceAfter=6)
            
            contact_style = ParagraphStyle('ContactStyle', fontName='Helvetica-Bold', fontSize=11,
                                         spaceAfter=8, alignment=TA_LEFT,
                                         textColor=colors.Color(0.86, 0.24, 0.26))
            
            # İçerik oluştur
            company_name = fix_turkish_chars("BULDUMLAR BİBER & BAHARAT ENTEGRE TESİSLERİ")
            story.append(Paragraph(company_name, company_style))
            story.append(Paragraph(fix_turkish_chars("FİYAT TEKLİFİ"), title_style))
            story.append(Spacer(1, 15))
            
            today = datetime.now()
            story.append(Paragraph(f"<b>Tarih:</b> {today.strftime('%d/%m/%Y')}", left_style))
            story.append(Paragraph(f"<b>Teklif No:</b> BLD-{today.strftime('%Y%m%d')}-{today.strftime('%H%M')}", left_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph("SAYIN", heading_style))
            customer_info = fix_turkish_chars(customer_company)
            if contact_person.strip():
                customer_info += f"<br/>Att: {fix_turkish_chars(contact_person)}"
            story.append(Paragraph(customer_info, normal_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph(fix_turkish_chars("FIYAT LISTESI (Kilogram Bazinda)"), heading_style))
            story.append(Spacer(1, 10))
            
            # Tablo
            table_headers = [
                fix_turkish_chars('Urun Adi'), 
                fix_turkish_chars('Birim Fiyat\n(KDV Haric)'), 
                'KDV %', 
                fix_turkish_chars('Birim Fiyat\n(KDV Dahil)')
            ]
            table_data = [table_headers]
            
            for product in st.session_state.products:
                table_data.append([
                    fix_turkish_chars(product['name']),
                    f"{product['unit_price']:.2f} TL/kg",
                    f"%{product['vat_rate']:.0f}",
                    f"{product['vat_price']:.2f} TL/kg"
                ])
            
            product_table = Table(table_data, colWidths=[6*cm, 3.5*cm, 2*cm, 3.5*cm])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.86, 0.24, 0.26)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.Color(1, 0.95, 0.95), colors.white]),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(product_table)
            story.append(Spacer(1, 25))
            
            # Notlar
            notes = f"""<b>{fix_turkish_chars('NOTLAR:')}</b><br/>
            {fix_turkish_chars('• Fiyatlar Turk Lirasi cinsindendir.')}<br/>
            {fix_turkish_chars('• Fiyatlar kilogram bazinda verilmistir.')}<br/>
            {fix_turkish_chars('• Minimum siparis miktarlari icin ayrica bilgi verilecektir.')}<br/>
            {fix_turkish_chars('• Teslim suresi siparis onayindan sonra belirlenecektir.')}"""
            
            story.append(Paragraph(notes, normal_style))
            story.append(Spacer(1, 30))
            
            # İLETİŞİM BİLGİLERİ - MUTLAKA GÖRÜNECEK
            story.append(Paragraph(fix_turkish_chars("TEKLIF VEREN:"), contact_style))
            story.append(Paragraph(f"<b>{fix_turkish_chars('Ertugrul BULDUM')}</b>", normal_style))
            story.append(Paragraph(fix_turkish_chars("Satis Direktoru"), normal_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>İletisim:</b> +90 530 078 06 46", normal_style))
            story.append(Paragraph("E-mail: info@buldumlarbiber.com", normal_style))
            
            # Logo ekleme fonksiyonu
            def add_logo_watermark(canvas, doc):
                temp_logo = create_watermark_logo()
                if temp_logo and os.path.exists(temp_logo):
                    try:
                        page_width, page_height = A4
                        logo_size = 400
                        x = (page_width - logo_size) / 2
                        y = (page_height - logo_size) / 2
                        canvas.drawImage(temp_logo, x, y, width=logo_size, height=logo_size, 
                                       mask='auto', preserveAspectRatio=True)
                        os.remove(temp_logo)
                    except:
                        pass
            
            # PDF'i oluştur
            doc.build(story, onFirstPage=add_logo_watermark, onLaterPages=add_logo_watermark)
            
            # PDF'i session state'e kaydet
            with open(filename, "rb") as pdf_file:
                st.session_state.pdf_data = pdf_file.read()
                st.session_state.pdf_filename = filename
            
            st.success("PDF basariyla olusturuldu!")
            
            # Temizlik
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            st.error(f"PDF olusturma hatasi: {str(e)}")

# PDF kontrolleri
if st.session_state.pdf_data:
    st.subheader("📄 PDF Kontrolleri")
    
    col_download, col_print, col_share = st.columns([1, 1, 1])
    
    with col_download:
        st.download_button(
            label="📥 PDF Indir",
            data=st.session_state.pdf_data,
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            use_container_width=True
        )
    
    with col_print:
        # Yazdırma butonu
        print_button_html = f"""
        <button onclick="printPDF()" style="
            background-color: #28a745; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            width: 100%;
            font-weight: bold;
        ">🖨️ PDF Yazdir</button>
        
        <script>
        function printPDF() {{
            const pdfData = {list(st.session_state.pdf_data)};
            const pdfBlob = new Blob([new Uint8Array(pdfData)], {{type: 'application/pdf'}});
            const pdfUrl = URL.createObjectURL(pdfBlob);
            const printWindow = window.open(pdfUrl);
            printWindow.onload = function() {{
                printWindow.print();
            }};
        }}
        </script>
        """
        st.components.v1.html(print_button_html, height=50)
    
    with col_share:
        share_text = f"Fiyat Teklifi: {customer_company} - {len(st.session_state.products)} urun"
        share_url = f"https://wa.me/?text={share_text.replace(' ', '%20')}"
        
        st.markdown(f"""
        <a href="{share_url}" target="_blank" style="
            display: inline-block; 
            background-color: #25d366; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
            text-align: center; 
            width: 100%;
            font-weight: bold;
            box-sizing: border-box;
        ">📱 WhatsApp Paylas</a>
        """, unsafe_allow_html=True)
    
    # PDF Görüntüleme
    if st.button("👁️ PDF Goruntule", use_container_width=True):
        b64_pdf = base64.b64encode(st.session_state.pdf_data).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

elif not st.session_state.products:
    st.warning("PDF olusturmak icin en az bir urun ekleyin.")
elif not customer_company.strip():
    st.warning("PDF olusturmak icin musteri firma adini girin.")

