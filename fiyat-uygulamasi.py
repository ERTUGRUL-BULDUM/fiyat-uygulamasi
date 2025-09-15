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
import urllib.request

# Türkçe destekli font yükleme
@st.cache_resource
def load_turkish_font():
    """Türkçe karakterleri destekleyen font yükle"""
    try:
        # DejaVu Sans fontunu indir ve yükle (Türkçe karakterler desteklenir)
        font_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
        bold_font_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf"
        
        # Fontları indir
        urllib.request.urlretrieve(font_url, "DejaVuSans.ttf")
        urllib.request.urlretrieve(bold_font_url, "DejaVuSans-Bold.ttf")
        
        # ReportLab'a kaydet
        pdfmetrics.registerFont(TTFont('TurkishFont', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('TurkishFont-Bold', 'DejaVuSans-Bold.ttf'))
        
        return 'TurkishFont', 'TurkishFont-Bold'
        
    except Exception as e:
        st.warning(f"Türkçe font yüklenemedi: {e}. Standart font kullanılacak.")
        return 'Helvetica', 'Helvetica-Bold'

# Font yükle
FONT_NORMAL, FONT_BOLD = load_turkish_font()

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
    .quick-product-btn {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 8px 12px !important;
        font-size: 12px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# Başlık
st.markdown('<div class="main-header"><h1>🌶️ FİYAT TEKLİFİ OLUŞTURUCU</h1><p>Buldumlar Biber & Baharat Entegre Tesisleri</p></div>', unsafe_allow_html=True)

# Session state başlatma
if 'products' not in st.session_state:
    st.session_state.products = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'quick_product' not in st.session_state:
    st.session_state.quick_product = ""

# Sidebar
with st.sidebar:
    st.header("📋 İşlemler")
    if st.button("🗑️ Tüm Ürünleri Temizle"):
        if st.session_state.products:
            st.session_state.products.clear()
            st.session_state.editing_index = None
            st.success("Tüm ürünler silindi!")
        else:
            st.info("Zaten hiç ürün yok!")

# Ana içerik
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("👥 Müşteri Bilgileri")
    customer_company = st.text_input("Müşteri Firma Adı", placeholder="Örnek: Saloon Burger")
    contact_person = st.text_input("İlgili Kişi", placeholder="Örnek: Mehmet Yılmaz")
    
    st.subheader("🛒 Ürün Ekle/Düzenle")
    
    # HIZLI ÜRÜN BUTONLARI
    st.write("**⚡ Hızlı Ürün Seçimi:**")
    
    # İlk sıra - Biber ürünleri
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        if st.button("🌶️ Yağlı Pul Biber", use_container_width=True, key="yagli_pul"):
            st.session_state.quick_product = "Yağlı Pul Biber"
            st.rerun()
    
    with col_p2:
        if st.button("🌶️ İpek Pul Biber", use_container_width=True, key="ipek_pul"):
            st.session_state.quick_product = "İpek Pul Biber"
            st.rerun()
    
    with col_p3:
        if st.button("🌶️ Halis Pul Biber", use_container_width=True, key="halis_pul"):
            st.session_state.quick_product = "Halis Pul Biber"
            st.rerun()
    
    # İkinci sıra - Diğer ürünler
    col_p4, col_p5, col_p6 = st.columns(3)
    
    with col_p4:
        if st.button("🌿 İsot", use_container_width=True, key="isot"):
            st.session_state.quick_product = "İsot"
            st.rerun()
    
    with col_p5:
        if st.button("🌿 Kekik", use_container_width=True, key="kekik"):
            st.session_state.quick_product = "Kekik"
            st.rerun()
    
    with col_p6:
        if st.button("🌿 Köri", use_container_width=True, key="kori"):
            st.session_state.quick_product = "Köri"
            st.rerun()
    
    st.divider()
    
    # Form alanları
    # Düzenleme kontrolü
    if st.session_state.editing_index is not None:
        editing_product = st.session_state.products[st.session_state.editing_index]
        default_name = editing_product['name']
        default_price = editing_product['unit_price']
        default_vat = editing_product['vat_rate']
        button_text = "✏️ Ürünü Güncelle"
        button_color = "secondary"
    else:
        # Hızlı ürün seçimi kontrolü
        if st.session_state.quick_product:
            default_name = st.session_state.quick_product
            st.session_state.quick_product = ""  # Temizle
        else:
            default_name = ""
        default_price = 0.0
        default_vat = 1.0  # KDV varsayılan %1
        button_text = "➕ Ürün Ekle"
        button_color = "primary"
    
    product_name = st.text_input("Ürün Adı", value=default_name, placeholder="Örnek: Karabiber")
    
    col_price, col_vat = st.columns([2, 1])
    with col_price:
        unit_price = st.number_input("Kilogram Fiyatı (KDV Hariç)", value=default_price, min_value=0.0, step=0.01)
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
                    st.success(f"'{product_name}' güncellendi!")
                    st.rerun()
                else:
                    st.session_state.products.append(product)
                    st.rerun()
            else:
                st.error("Ürün adı boş olamaz!")
    
    with col_btn2:
        if st.session_state.editing_index is not None:
            if st.button("❌ İptal"):
                st.session_state.editing_index = None
                st.rerun()

with col2:
    st.subheader("📦 Eklenen Ürünler")
    
    if st.session_state.products:
        # DataFrame gösterimi
        df_data = []
        for i, product in enumerate(st.session_state.products):
            df_data.append({
                'No': i + 1,
                'Ürün Adı': product['name'],
                'KDV Hariç (TL/kg)': f"{product['unit_price']:.2f}",
                'KDV %': f"{product['vat_rate']:.0f}",
                'KDV Dahil (TL/kg)': f"{product['vat_price']:.2f}"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # İşlem butonları
        st.write("**İşlemler:**")
        for i, product in enumerate(st.session_state.products):
            col_edit, col_delete, col_info = st.columns([1, 1, 3])
            
            with col_edit:
                if st.button(f"✏️", key=f"edit_{i}", help="Düzenle"):
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
        
        st.write(f"**Toplam: {len(st.session_state.products)} ürün**")
    else:
        st.info("Henüz ürün eklenmemiş. Soldan ürün bilgilerini doldurup 'Ürün Ekle' butonuna tıklayın.")

# PDF Oluşturma Bölümü
st.divider()
st.subheader("📄 PDF Oluştur")

if st.session_state.products and customer_company.strip():
    if st.button("📋 PDF TEKLİFİ OLUŞTUR", type="primary", use_container_width=True):
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
            company_style = ParagraphStyle('CompanyStyle', fontName=FONT_BOLD, fontSize=16,
                                          spaceAfter=25, alignment=TA_CENTER,
                                          textColor=colors.Color(0.86, 0.24, 0.26))
            
            title_style = ParagraphStyle('TitleStyle', fontName=FONT_BOLD, fontSize=18,
                                        spaceAfter=20, alignment=TA_CENTER,
                                        textColor=colors.Color(0.86, 0.24, 0.26))
            
            left_style = ParagraphStyle('LeftStyle', fontName=FONT_NORMAL, fontSize=10,
                                       spaceAfter=4, alignment=TA_LEFT, leftIndent=0)
            
            heading_style = ParagraphStyle('HeadingStyle', fontName=FONT_BOLD, fontSize=12,
                                          spaceAfter=8, textColor=colors.Color(0.86, 0.24, 0.26))
            
            normal_style = ParagraphStyle('NormalStyle', fontName=FONT_NORMAL, fontSize=10, spaceAfter=6)
            
            contact_style = ParagraphStyle('ContactStyle', fontName=FONT_BOLD, fontSize=11,
                                         spaceAfter=8, alignment=TA_LEFT,
                                         textColor=colors.Color(0.86, 0.24, 0.26))
            
            # İçerik oluştur - Gerçek Türkçe karakterlerle
            company_name = "BULDUMLAR BİBER & BAHARAT ENT. TESİSLERİ"
            story.append(Paragraph(company_name, company_style))
            story.append(Paragraph("FİYAT TEKLİFİ", title_style))
            story.append(Spacer(1, 15))
            
            today = datetime.now()
            story.append(Paragraph(f"<b>Tarih:</b> {today.strftime('%d/%m/%Y')}", left_style))
            story.append(Paragraph(f"<b>Teklif No:</b> BLD-{today.strftime('%Y%m%d')}-{today.strftime('%H%M')}", left_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph("SAYIN", heading_style))
            customer_info = customer_company
            if contact_person.strip():
                customer_info += f"<br/>Att: {contact_person}"
            story.append(Paragraph(customer_info, normal_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph("FİYAT LİSTESİ (Kilogram Bazında)", heading_style))
            story.append(Spacer(1, 10))
            
            # Tablo - Türkçe karakterlerle
            table_headers = ['Ürün Adı', 'Birim Fiyat\n(KDV Hariç)', 'KDV %', 'Birim Fiyat\n(KDV Dahil)']
            table_data = [table_headers]
            
            for product in st.session_state.products:
                table_data.append([
                    product['name'],
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
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NORMAL),
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
            
            # Notlar - Gerçek Türkçe karakterlerle
            notes = """<b>NOTLAR:</b><br/>
            • Fiyatlar Türk Lirası cinsindendir.<br/>
            • Fiyatlar kilogram bazında verilmiştir.<br/>
            • Minimum sipariş miktarları için ayrıca bilgi verilecektir.<br/>
            • Teslim süresi sipariş onayından sonra belirlenecektir."""
            
            story.append(Paragraph(notes, normal_style))
            story.append(Spacer(1, 30))
            
            # İLETİŞİM BİLGİLERİ - Gerçek Türkçe karakterlerle
            story.append(Paragraph("TEKLİF VEREN:", contact_style))
            story.append(Paragraph("<b>Ertuğrul BULDUM</b>", normal_style))
            story.append(Paragraph("Satış Direktörü", normal_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>İletişim:</b> +90 530 078 06 46", normal_style))
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
            
            st.success("PDF başarıyla oluşturuldu!")
            
            # Temizlik
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            st.error(f"PDF oluşturma hatası: {str(e)}")

# PDF kontrolleri
if st.session_state.pdf_data:
    st.subheader("📄 PDF Kontrolleri")
    
    col_download, col_print, col_share = st.columns([1, 1, 1])
    
    with col_download:
        st.download_button(
            label="📥 PDF İndir",
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
        ">🖨️ PDF Yazdır</button>
        
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
        share_text = f"Fiyat Teklifi: {customer_company} - {len(st.session_state.products)} ürün"
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
        ">📱 WhatsApp Paylaş</a>
        """, unsafe_allow_html=True)
    
    # PDF Görüntüleme
    if st.button("👁️ PDF Görüntüle", use_container_width=True):
        b64_pdf = base64.b64encode(st.session_state.pdf_data).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

elif not st.session_state.products:
    st.warning("PDF oluşturmak için en az bir ürün ekleyin.")
elif not customer_company.strip():
    st.warning("PDF oluşturmak için müşteri firma adını girin.")
