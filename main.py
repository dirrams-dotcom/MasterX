
# Run this once in your python console or temporarily in main.py



from kivy.config import Config

# Set the window size to a standard mobile resolution (e.g., 360x640)
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0') # Prevents resizing the window

from email_utils import resend_verification_code_async







from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.image import Image as CoreImage
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
import os, shutil, random, string, webbrowser, qrcode
from io import BytesIO
from kivy.config import Config
from kivy.properties import ObjectProperty
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
# Standard Kivy Layouts/Widgets
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView  # <--- MAKE SURE THIS IS HERE
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout

# KivyMD Components (Since you are building ManaGuru)
from kivymd.app import MDApp
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from kivy.uix.image import Image



# --- MOBILE WINDOW CONFIG ---
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', False)

# CHANGE THIS: Use MDApp instead of App
from kivymd.app import MDApp
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDTextButton
from kivymd.uix.textfield import MDTextField

# Keep your other standard Kivy imports
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, InstructionGroup
from database import Database
from email_utils import send_verification_email_safe, generate_verification_code

db = Database()

def set_rounded_panel(instance, color=(1, 1, 1, 1), radius=15):
    with instance.canvas.before:
        Color(*color) # This is where it was crashing
        instance.rect = RoundedRectangle(
            pos=instance.pos,
            size=instance.size,
            radius=[radius,]
        )
    instance.bind(pos=update_rect, size=update_rect)

def update_rect(instance, value):
    instance.rect.pos = instance.pos
    instance.rect.size = instance.size





# --- THEME COLORS ---
BG = (0.95, 0.96, 0.99, 1)
PRIMARY = (0.1, 0.5, 0.8, 1)
PURPLE = (0.5, 0.3, 0.8, 1)
SUCCESS = (0.0, 0.65, 0.35, 1)
DANGER = (0.8, 0.2, 0.2, 1)
TEXT = (0.1, 0.1, 0.1, 1)
MUTED = (0.45, 0.45, 0.45, 1)

Window.clearcolor = BG

# --- KEYBOARD FIX FOR ANDROID ---
if platform == 'android':
    from jnius import autoclass
    from android import activity

    Window.softinput_mode = 'below_target'  # App moves UP when typing
else:
    autoclass = None


# --- MODERN UI HELPERS ---
def themed_input(hint, pwd=False):
    return TextInput(
        hint_text=hint, password=pwd, multiline=False,
        size_hint_y=None, height=dp(50), font_size='16sp',
        padding=[dp(12), dp(14), dp(12), dp(12)]
    )


def themed_button(text, color=PRIMARY, h=55):
    btn = Button(text=text, size_hint_y=None, height=dp(h), background_normal="", background_color=(0, 0, 0, 0),
                 color=(1, 1, 1, 1), bold=True, font_size='16sp')
    with btn.canvas.before:
        Color(*color)
        btn.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12), ])
    btn.bind(pos=lambda i, v: setattr(btn.rect, 'pos', i.pos), size=lambda i, v: setattr(btn.rect, 'size', i.size))
    return btn


def set_rounded_panel(widget, color=(1, 1, 1, 1), r=15):
    with widget.canvas.before:
        Color(*color)
        widget.bg_rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(r), ])
    widget.bind(pos=lambda i, v: setattr(widget.bg_rect, 'pos', i.pos),
                size=lambda i, v: setattr(widget.bg_rect, 'size', i.size))


def show_popup(title, message):
    c = BoxLayout(orientation='vertical', padding=20, spacing=15);
    set_rounded_panel(c)
    c.add_widget(Label(text=message, color=(0, 0, 0, 1), halign='center', markup=True, text_size=(dp(280), None),
                       font_size='16sp'))
    ok = themed_button("OK", PRIMARY, 50);
    ok.bind(on_press=lambda x: p.dismiss());
    c.add_widget(ok)
    p = Popup(title=title, content=c, size_hint=(0.85, 0.5));
    p.open()


# ==========================================
# 1. BASE CLASSES (Parent logic)
# ==========================================

class BaseForm(Screen):
    user_email = ""
    aadhar_path = ""

    def trigger_picker(self, _instance):
        if platform == 'android':
            try:
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("*/*");
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                activity.bind(on_activity_result=self.on_file_result)
                autoclass('org.kivy.android.PythonActivity').mActivity.startActivityForResult(intent, 1001)
            except Exception as e:
                show_popup("Error", str(e))
        else:
            from kivy.uix.filechooser import FileChooserIconView
            c = BoxLayout(orientation='vertical', padding=10);
            fc = FileChooserIconView(path=os.path.expanduser("~"), filters=['*.jpg', '*.pdf', '*.png'])
            btn = themed_button("SELECT FILE", SUCCESS);
            c.add_widget(fc);
            c.add_widget(btn)
            p = Popup(title="Choose File", content=c, size_hint=(0.9, 0.9));
            btn.bind(on_press=lambda x: [self.handle_pc_file(fc.selection), p.dismiss()]);
            p.open()

    def on_file_result(self, req, res, intent):
        if req != 1001 or not intent: return
        try:
            uri = intent.getData();
            dest_dir = os.path.join(App.get_running_app().user_data_dir, "uploads")
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)
            path = os.path.join(dest_dir, f"id_{random.randint(100, 999)}.pdf")
            stream = autoclass('org.kivy.android.PythonActivity').mActivity.getContentResolver().openInputStream(uri)
            with open(path, 'wb') as f:
                buf = bytearray(1024 * 1024)
                while True:
                    read = stream.read(buf);
                    if read <= 0: break
                    f.write(buf[:read])
            stream.close();
            self.aadhar_path = path;
            self.doc_lbl.text = "✓ ID Loaded";
            self.doc_lbl.color = SUCCESS
        except:
            show_popup("Error", "Could not load file.")

    def handle_pc_file(self, sel):
        if sel:
            dest = os.path.join(os.getcwd(), "uploads")
            if not os.path.exists(dest): os.makedirs(dest)
            path = os.path.join(dest, os.path.basename(sel[0]));
            shutil.copy2(sel[0], path)
            self.aadhar_path = path;
            self.doc_lbl.text = "✓ ID Loaded";
            self.doc_lbl.color = SUCCESS


class BasePortal(Screen):
    user_email = ""

    def update_credits(self):
        u = db.query("SELECT credits FROM users WHERE email=?", (self.user_email,), True)
        if hasattr(self, 'c_lbl'): self.c_lbl.text = f"{u['credits'] if u else 0}"

    def handle_req(self, t):
        u = db.query("SELECT credits FROM users WHERE email=?", (self.user_email,), True)
        if u and u['credits'] > 0:
            db.query("UPDATE users SET credits = credits - 1 WHERE email=?", (self.user_email,))
            db.query("INSERT INTO credit_usage_log (user_email, target_name) VALUES (?,?)",
                     (self.user_email, t['name']))
            show_popup("Unlocked", f"[b]CONTACT INFO[/b]\nName: {t['name'].upper()}\nPhone: {t.get('phone', 'N/A')}");
            self.update_credits()
        else:
            self.show_pay(t['name'])

    def show_pay(self, name):
        # Main container for the payment popup
        c = MDBoxLayout(orientation='vertical', padding="20dp", spacing="15dp")

        # Text instruction
        c.add_widget(MDLabel(
            text=f"Scan to Pay Rs.100 for {name.upper()}",
            halign='center',
            font_style="Subtitle1"
        ))

        # QR Code logic (Keeping your existing logic)
        upi_data = "upi://pay?pa=dir.rams@ybl&pn=MyTutorApp&am=100&cu=INR"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(upi_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to texture (Your existing method)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        core_img = CoreImage(buffer, ext='png')
        qr_widget = Image(texture=core_img.texture, size_hint_y=None, height="200dp")
        c.add_widget(qr_widget)

        # Input for Transaction ID
        self.txn = MDTextField(
            hint_text="Enter Transaction ID",
            mode="rectangle"  # <--- Use this for KivyMD 1.2.0
        )

        # Action Buttons
        layout = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        # 2. Add the elements in order
        layout.add_widget(MDLabel(text=f"Scan to Pay Rs.100 for {name}", halign="center"))

        # Add the QR Image
        qr_widget = Image(texture=core_img.texture, size_hint_y=None, height="200dp")
        layout.add_widget(qr_widget)

        # 3. Create AND ADD the text field
        self.txn = MDTextField(
            hint_text="Enter Transaction ID",
            mode="rectangle"  # Fixed from 'outline'
        )
        layout.add_widget(self.txn)  # <--- THIS IS THE MISSING STEP

        # 4. Open the Dialog
        self.dialog = MDDialog(
            title="Secure Payment",
            type="custom",
            content_cls=layout,  # This tells the dialog to show your layout
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="I HAVE PAID", on_release=self.verify_pay)
            ],
        )
        self.dialog.open()

    def verify_pay(self, instance):  # Changed name to match your button and added 'instance'
        utr_number = self.txn.text.strip()

        if len(utr_number) < 5:
            # Using a simple print or your show_popup utility
            print("Error: Please enter a valid Transaction ID")
            return

        # 1. Save to Local SQLite (tutor_ap1.db)
        # This keeps a record on the user's phone
        db.query("INSERT INTO credit_purchases (user_email, amount, status) VALUES (?, 100, ?)",
                 (self.user_email, utr_number))

        # 2. SAVE TO FIREBASE (Cloud Sync)
        # This allows the Admin to see the 'pending' status in their dashboard
        request_data = {
            "email": self.user_email,
            "utr": utr_number,
            "status": "pending"
        }

        try:
            # Your existing cloud save logic...
            cloud_key = self.user_email.replace('.', '_')
            db.save_to_cloud("credit_purchases", cloud_key, request_data)

            # 1. Dismiss the payment dialog first
            self.dialog.dismiss()

            # 2. Show the Success Confirmation
            self.success_dialog = MDDialog(
                title="Request Sent",
                text="Your payment details have been submitted successfully! The admin will verify your transaction and update your credits shortly.",
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        on_release=lambda x: self.success_dialog.dismiss()
                    )
                ],
            )
            self.success_dialog.open()

        except Exception as e:
            # Show an error dialog if sync fails
            self.error_dialog = MDDialog(
                title="Sync Error",
                text=f"Failed to reach the cloud: {str(e)}\nPlease check your internet connection.",
                buttons=[MDFlatButton(text="RETRY", on_release=lambda x: self.error_dialog.dismiss())],
            )
            self.error_dialog.open()

    def process_pay_req(self, popup):
        if not self.txn.text: return
        db.query("INSERT INTO credit_purchases (user_email, amount, status) VALUES (?,100,?)",
                 (self.user_email, self.txn.text))
        popup.dismiss();
        show_popup("Sent", "Admin will approve soon")

    def show_messages(self):
        c = BoxLayout(orientation='vertical', padding=15, spacing=10);
        set_rounded_panel(c)
        gl = GridLayout(cols=1, spacing=10, size_hint_y=None);
        gl.bind(minimum_height=gl.setter('height'))
        logs = db.query("SELECT * FROM credit_usage_log WHERE user_email=? ORDER BY date DESC", (self.user_email,))
        if logs:
            for l in logs:
                row = BoxLayout(size_hint_y=None, height=dp(60), padding=5);
                set_rounded_panel(row, (0.9, 1, 0.9, 1))
                row.add_widget(Label(text=f"Unlocked: {l['target_name']}\nDate: {l['date'][:10]}", color=(0, 0, 0, 1)));
                gl.add_widget(row)
        else:
            gl.add_widget(Label(text="No history found.", color=MUTED))
        sc = ScrollView();
        sc.add_widget(gl);
        c.add_widget(sc)
        btn = themed_button("CLOSE", DANGER, 45);
        p = Popup(title="Unlocked Contacts", content=c, size_hint=(0.9, 0.8))
        btn.bind(on_press=p.dismiss);
        c.add_widget(btn);
        p.open()

    def show_offers(self, r):
        c = BoxLayout(orientation='vertical', padding=15, spacing=10);
        set_rounded_panel(c)
        gl = GridLayout(cols=1, spacing=10, size_hint_y=None);
        gl.bind(minimum_height=gl.setter('height'))
        msgs = db.query("SELECT * FROM admin_broadcasts WHERE target_role=? ORDER BY created_at DESC", (r,))
        if msgs:
            for m in msgs:
                row = BoxLayout(size_hint_y=None, height=dp(80), padding=10);
                set_rounded_panel(row, (0.9, 0.9, 1, 1))
                row.add_widget(Label(text=m['message_text'], color=(0, 0, 0, 1), text_size=(dp(250), None)));
                gl.add_widget(row)
        else:
            gl.add_widget(Label(text="No announcements.", color=MUTED))
        sc = ScrollView();
        sc.add_widget(gl);
        c.add_widget(sc)
        btn = themed_button("CLOSE", DANGER, 45);
        p = Popup(title="Admin Offers", content=c, size_hint=(0.9, 0.8))
        btn.bind(on_press=p.dismiss);
        c.add_widget(btn);
        p.open()


# ==========================================
# 2. CHILD PORTALS
# ==========================================

class StudentPortal(BasePortal):
    c_lbl = ObjectProperty(None)
    name_lbl = ObjectProperty(None)

    def __init__(self, **kwargs):
        # 1. Initialize labels BEFORE super() so the .kv file can find them immediately
        self.name_lbl = Label(text="Welcome")
        self.c_lbl = Label(text="0")

        # 2. Now call super(), which triggers the .kv file loading
        super().__init__(**kwargs)

        # 3. Main Layout Setup
        self.l = BoxLayout(orientation='vertical', padding=10, spacing=10)
        set_rounded_panel(self.l, BG, 0)

        # 4. Header Card (Profile/Credits Area)
        h_card = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(10), spacing=dp(10))
        set_rounded_panel(h_card)

        # 5. Apply styling to the already created Name Label
        self.name_lbl.color = TEXT
        self.name_lbl.bold = True
        self.name_lbl.font_size = '14sp'
        self.name_lbl.halign = 'left'
        self.name_lbl.bind(size=lambda i, v: setattr(self.name_lbl, 'text_size', i.size))

        # 6. Apply styling to the already created Credit Label
        self.c_lbl.color = (1, 1, 1, 1)
        self.c_lbl.bold = True
        self.c_lbl.size_hint_x = None
        self.c_lbl.width = dp(40)

        with self.c_lbl.canvas.before:
            Color(*SUCCESS)
            self.c_lbl.bg = RoundedRectangle(
                pos=self.c_lbl.pos,
                size=self.c_lbl.size,
                radius=[20, ]
            )

        # Bind the background to follow the label's position and size
        self.c_lbl.bind(
            pos=lambda i, v: setattr(self.c_lbl.bg, 'pos', i.pos),
            size=lambda i, v: setattr(self.c_lbl.bg, 'size', i.size)
        )

        # 7. Assemble Header Card
        h_card.add_widget(self.name_lbl)
        h_card.add_widget(Label(text="Credits:", color=MUTED, size_hint_x=None, width=50))
        h_card.add_widget(self.c_lbl)

        # Logout Button
        lo = themed_button("Out", DANGER, 35)
        lo.size_hint_x = None
        lo.width = 60
        lo.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        h_card.add_widget(lo)

        self.l.add_widget(h_card)

        # 8. Action Buttons (Messages/Offers)
        btns = GridLayout(cols=2, size_hint_y=None, height=dp(55), spacing=5)
        m_b = themed_button("MESSAGES", PRIMARY, 50)
        o_b = themed_button("OFFERS", PURPLE, 50)

        m_b.bind(on_press=lambda x: self.show_messages())
        o_b.bind(on_press=lambda x: self.show_offers("student"))

        btns.add_widget(m_b)
        btns.add_widget(o_b)
        self.l.add_widget(btns)

        # 9. Search and Content Area
        self.srch = themed_input("Search Area")
        self.srch.bind(text=lambda i, v: self.load(v.lower()))
        self.l.add_widget(self.srch)

        # Scrollable Grid for dynamic content
        self.gl = GridLayout(cols=1, spacing=12, size_hint_y=None)
        self.gl.bind(minimum_height=self.gl.setter('height'))

        s = ScrollView()
        s.add_widget(self.gl)
        self.l.add_widget(s)

        # Add the main vertical box to the Screen
        self.add_widget(self.l)

    def on_enter(self):
        r = db.query("SELECT name FROM student_profiles WHERE email=?", (self.user_email,), True)
        self.name_lbl.text = f"Welcome, [b]{r['name'].upper() if r else 'GUEST'}[/b]";
        self.name_lbl.markup = True;
        self.update_credits();
        self.load()

    def load(self, q=""):
        self.gl.clear_widgets()
        # Querying the tutor profiles for the student to see
        sql = "SELECT * FROM tutor_profiles WHERE status='approved'"
        p = ()
        if q:
            sql += " AND (LOWER(area) LIKE ? OR LOWER(city) LIKE ?)"
            p = (f"%{q}%", f"%{q}%")

        for s in db.query(sql, p):
            c = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(160), padding=dp(15), spacing=5)
            set_rounded_panel(c)

            # UPDATE THIS LINE BELOW:
            c.add_widget(Label(
                text=f"[color=1A73E8][b]TUTOR: {s['name'].upper()}[/b][/color]\n📖 {s.get('subject', 'N/A')}\n📍 Area: {s['area']}, {s['city']}",
                markup=True,
                color=TEXT,
                halign='left',
                text_size=(Window.width - 80, None)
            ))

            b = themed_button("UNLOCK", SUCCESS, 45)
            b.bind(on_press=lambda x, d=s: self.handle_req(d))
            c.add_widget(b)
            self.gl.add_widget(c)


class TutorPortal(BasePortal):
    # Ensure these properties are declared at the class level
    c_lbl = ObjectProperty(None)
    name_lbl = ObjectProperty(None)

    def __init__(self, **kwargs):
        # 1. Initialize labels BEFORE super() so the .kv file can find them
        self.name_lbl = Label(text="Welcome")
        self.c_lbl = Label(text="0")

        # 2. Call super() to load the .kv rules
        super().__init__(**kwargs)

        # 3. Main Layout Setup
        self.l = BoxLayout(orientation='vertical', padding=10, spacing=10)
        set_rounded_panel(self.l, BG, 0)

        # 4. Header Card Setup
        h_card = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(10), spacing=dp(10))
        set_rounded_panel(h_card)

        # 5. Apply styling to the Name Label
        self.name_lbl.color = TEXT
        self.name_lbl.bold = True
        self.name_lbl.font_size = '14sp'
        self.name_lbl.halign = 'left'
        self.name_lbl.bind(size=lambda i, v: setattr(self.name_lbl, 'text_size', i.size))

        # 6. Apply styling to the Credit Label
        self.c_lbl.color = (1, 1, 1, 1)
        self.c_lbl.bold = True
        self.c_lbl.size_hint_x = None
        self.c_lbl.width = dp(40)

        with self.c_lbl.canvas.before:
            Color(*SUCCESS)
            self.c_lbl.bg = RoundedRectangle(
                pos=self.c_lbl.pos,
                size=self.c_lbl.size,
                radius=[20, ]
            )

        self.c_lbl.bind(
            pos=lambda i, v: setattr(self.c_lbl.bg, 'pos', i.pos),
            size=lambda i, v: setattr(self.c_lbl.bg, 'size', i.size)
        )

        # 7. Assemble Header Card
        h_card.add_widget(self.name_lbl)
        h_card.add_widget(Label(text="Credits:", color=MUTED, size_hint_x=None, width=50))
        h_card.add_widget(self.c_lbl)

        # Logout Button
        lo = themed_button("Out", DANGER, 35)
        lo.size_hint_x = None
        lo.width = 80
        lo.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        h_card.add_widget(lo)

        self.l.add_widget(h_card)

        # 8. Action Buttons (Tutor specific: connects to "tutor" offers)
        btns = GridLayout(cols=2, size_hint_y=None, height=dp(55), spacing=5)
        m_b = themed_button("MESSAGES", PRIMARY, 50)
        o_b = themed_button("OFFERS", PURPLE, 50)

        m_b.bind(on_press=lambda x: self.show_messages())
        o_b.bind(on_press=lambda x: self.show_offers("tutor"))

        btns.add_widget(m_b)
        btns.add_widget(o_b)
        self.l.add_widget(btns)

        # 9. Search and Content Area
        self.srch = themed_input("Search Area")
        self.srch.bind(text=lambda i, v: self.load(v.lower()))
        self.l.add_widget(self.srch)

        # Scrollable Grid for dynamic student content
        self.gl = GridLayout(cols=1, spacing=12, size_hint_y=None)
        self.gl.bind(minimum_height=self.gl.setter('height'))

        s = ScrollView()
        s.add_widget(self.gl)
        self.l.add_widget(s)

        # Add the main vertical box to the Screen
        self.add_widget(self.l)

    def on_enter(self):
        # Fetches the tutor name from the tutor_profiles table
        r = db.query("SELECT name FROM tutor_profiles WHERE email=?", (self.user_email,), True)
        self.name_lbl.text = f"Welcome, [b]{r['name'].upper() if r else 'GUEST'}[/b]"
        self.name_lbl.markup = True
        self.update_credits()
        self.load()

    def load(self, q=""):
        self.gl.clear_widgets()
        sql = "SELECT * FROM student_profiles WHERE status='approved'"
        p = ()
        if q:
            sql += " AND (LOWER(area) LIKE ? OR LOWER(city) LIKE ?)"
            p = (f"%{q}%", f"%{q}%")

        for s in db.query(sql, p):
            c = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(160), padding=dp(15), spacing=5)
            set_rounded_panel(c)
            c.add_widget(Label(
                text=f"[color=1A73E8][b]STUDENT: {s['name'].upper()}[/b][/color]\n📖 Class {s.get('class', 'N/A')}\n📍 Area: {s['area']}",
                markup=True, color=TEXT, halign='left', text_size=(Window.width - 80, None)))

            b = themed_button("GET CONTACT", SUCCESS, 45)
            b.bind(on_press=lambda x, d=s: self.handle_req(d))
            c.add_widget(b)
            self.gl.add_widget(c)


# ==========================================
# 3. FORMS & LOGIN
# ==========================================

from kivy.properties import ObjectProperty, StringProperty


class StudentForm(BasePortal):
    # Declare these at the top of the class, OUTSIDE __init__
    c_lbl = ObjectProperty(None)
    name_lbl = ObjectProperty(None)

    def __init__(self, **kwargs):
        # 1. Create the label objects BEFORE calling super()
        # This ensures they exist when .kv looks for them
        self.name_lbl = Label(text="Welcome")
        self.c_lbl = Label(text="0")

        super().__init__(**kwargs)
        # Main Layout
        root = BoxLayout(orientation='vertical', padding=10, spacing=10);
        set_rounded_panel(root, BG, 0)
        root.add_widget(Label(text="STUDENT REGISTRATION", font_size='22sp', bold=True, color=PRIMARY, size_hint_y=None,
                              height=dp(60)))

        # THE SCROLLVIEW FIX: Put all inputs inside here
        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=10);
        grid.bind(minimum_height=grid.setter('height'))

        self.name_in = themed_input("Full Name");
        self.phone_in = themed_input("Phone")
        self.hno_in = themed_input("House No");
        self.strt_in = themed_input("Street")
        self.land_in = themed_input("Landmark");
        self.area_in = themed_input("Area")
        self.city_in = themed_input("City");
        self.pin_in = themed_input("Pin")
        self.cls_in = themed_input("Class");
        self.sub_in = themed_input("Subjects")

        self.doc_lbl = Label(text="No ID Uploaded", color=MUTED, size_hint_y=None, height=25)
        u_btn = themed_button("Upload ID", PRIMARY, 45);
        u_btn.bind(on_press=self.trigger_picker)
        s_btn = themed_button("SUBMIT", SUCCESS, 55);
        s_btn.bind(on_press=self.save)

        for w in [self.name_in, self.phone_in, self.hno_in, self.strt_in, self.land_in, self.area_in, self.city_in,
                  self.pin_in, self.cls_in, self.sub_in, self.doc_lbl, u_btn, s_btn]: grid.add_widget(w)
        scroll.add_widget(grid);
        root.add_widget(scroll);
        self.add_widget(root)

    def save(self, *args):
        # 1. Validation: Ensure required fields are not empty
        if not all([self.name_in.text, self.phone_in.text, self.aadhar_path]):
            show_popup("Error", "Please fill all fields and upload ID")
            return

        # 2. Create the data dictionary for Firebase
        # This must include the same fields you have in your SQLite table
        student_data = {
            "email": self.user_email,
            "name": self.name_in.text,
            "phone": self.phone_in.text,
            "area": self.area_in.text,
            "city": self.city_in.text,
            "landmark": self.land_in.text,
            "house_no": self.hno_in.text,
            "street": self.strt_in.text,
            "pincode": self.pin_in.text,
            "class": self.cls_in.text,
            "subjects": self.sub_in.text,
            "aadhar_path": self.aadhar_path,
            "status": "pending"  # Admin's load_v looks for this status
        }

        # 3. Save locally to SQLite (Your existing code)
        db.query(
            "INSERT INTO student_profiles (email, name, phone, area, city, landmark, house_no, street, pincode, class, subjects, aadhar_path, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'pending')",
            (self.user_email, self.name_in.text, self.phone_in.text, self.area_in.text, self.city_in.text,
             self.land_in.text, self.hno_in.text, self.strt_in.text, self.pin_in.text, self.cls_in.text,
             self.sub_in.text, self.aadhar_path))

        # 4. Save to the Cloud (The "Bridge" to other mobiles)
        # This sends the data to the 'student_profiles' folder in your Firebase URL
        cloud_success = db.save_to_cloud("student_profiles", self.user_email, student_data)

        if cloud_success:
            show_popup("Done", "Wait for Admin Approval")
            self.manager.current = 'login'
        else:
            # If internet fails, it's still saved locally, but warn the user
            show_popup("Sync Issue", "Saved locally, but could not reach cloud. Check internet.")

    def trigger_picker(self, instance):
        # This will be called when you press the upload button
        print("Triggering File Picker...")

        # If you are on Android, you'll eventually use 'plyer' or 'filechooser'
        # For now, let's just show a simple notification
        try:
            from kivymd.toast import toast
            toast("File picker coming soon!")
        except:
            print("Toast not available, but button is working!")


class TutorForm(BaseForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=10, spacing=10);
        set_rounded_panel(root, BG, 0)
        root.add_widget(Label(text="TUTOR REGISTRATION", font_size='22sp', bold=True, color=PRIMARY, size_hint_y=None,
                              height=dp(60)))
        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=10);
        grid.bind(minimum_height=grid.setter('height'))
        self.name_in = themed_input("Full Name");
        self.phone_in = themed_input("Phone")
        self.hno_in = themed_input("House No");
        self.strt_in = themed_input("Street")
        self.land_in = themed_input("Landmark");
        self.area_in = themed_input("Area")
        self.city_in = themed_input("City");
        self.pin_in = themed_input("Pin")
        self.sub_in = themed_input("Subjects");
        self.qual_in = themed_input("Qualification")
        self.exp_in = themed_input("Experience");
        self.mode_in = themed_input("Tuition Mode")
        self.doc_lbl = Label(text="No ID Uploaded", color=MUTED, size_hint_y=None, height=25)
        u_btn = themed_button("Upload ID", PRIMARY, 45);
        u_btn.bind(on_press=self.trigger_picker)
        s_btn = themed_button("SUBMIT", SUCCESS, 55);
        s_btn.bind(on_press=self.save)
        for w in [self.name_in, self.phone_in, self.hno_in, self.strt_in, self.land_in, self.area_in, self.city_in,
                  self.pin_in, self.sub_in, self.qual_in, self.exp_in, self.mode_in, self.doc_lbl, u_btn,
                  s_btn]: grid.add_widget(w)
        scroll.add_widget(grid);
        root.add_widget(scroll);
        self.add_widget(root)

    def save(self, *args):
        # 1. Validation check
        if not all([self.name_in.text, self.phone_in.text, self.aadhar_path]):
            show_popup("Error", "Please fill all fields and upload ID")
            return

        # 2. Prepare the data dictionary for the Cloud
        # This matches the structure your Admin Dashboard expects to read
        tutor_data = {
            "email": self.user_email,
            "name": self.name_in.text,
            "phone": self.phone_in.text,
            "area": self.area_in.text,
            "city": self.city_in.text,
            "landmark": self.land_in.text,
            "house_no": self.hno_in.text,
            "street": self.strt_in.text,
            "pincode": self.pin_in.text,
            "subjects": self.sub_in.text,
            "qualification": self.qual_in.text,
            "experience": self.exp_in.text,
            "tuition_mode": self.mode_in.text,
            "aadhar_path": self.aadhar_path,
            "status": "pending"  # Crucial: This marks it for the Admin's "pending" list
        }

        # 3. Save to LOCAL Database (Your existing code)
        db.query(
            "INSERT INTO tutor_profiles (email, name, phone, area, city, landmark, house_no, street, pincode, subjects, qualification, experience, tuition_mode, aadhar_path, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'pending')",
            (self.user_email, self.name_in.text, self.phone_in.text, self.area_in.text, self.city_in.text,
             self.land_in.text, self.hno_in.text, self.strt_in.text, self.pin_in.text, self.sub_in.text,
             self.qual_in.text, self.exp_in.text, self.mode_in.text, self.aadhar_path))

        # 4. Save to CLOUD Database (The new critical step!)
        # This pushes the data to the Firebase URL so other phones can see it
        cloud_success = db.save_to_cloud("tutor_profiles", self.user_email, tutor_data)

        if cloud_success:
            show_popup("Done", "Wait for Admin Approval")
            self.manager.current = 'login'
        else:
            show_popup("Network Error", "Saved locally, but could not sync to cloud. Check internet.")


class Login(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Main Layout
        l = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(30))
        set_rounded_panel(l, BG, 0)

        # Header
        l.add_widget(Label(
            text="MY TUTOR LOGIN",
            font_size='24sp',
            bold=True,
            color=PRIMARY,
            size_hint_y=None,
            height=dp(80)
        ))

        # Inputs
        self.e_in = themed_input("Email")
        self.p_in = themed_input("Password", pwd=True)
        l.add_widget(self.e_in)
        l.add_widget(self.p_in)

        # Login Button
        btn = themed_button("LOGIN", PRIMARY, 60)
        btn.bind(on_press=self.do_login)
        l.add_widget(btn)

        # Sign Up Link
        s = Button(
            text="Sign Up",
            color=PRIMARY,
            background_color=(0, 0, 0, 0),
            font_size='18sp',
            underline=True
        )
        s.bind(on_press=lambda x: setattr(self.manager, 'current', 'signup'))
        l.add_widget(s)

        self.add_widget(l)

    def do_login(self, *args):
        email = self.e_in.text.strip().lower()
        password = self.p_in.text

        # 1. Authenticate user credentials
        u = db.query("SELECT * FROM users WHERE email=? AND password=?", (email, password), True)

        if u:
            role = str(u['role']).lower().strip()  # Force lowercase to avoid 'Student' vs 'student' bugs
            print(f"DEBUG: User found with role: {role}")

            # 2. Admin Check
            if role == 'admin':
                self.manager.current = 'admin_screen'
                return

            # 3. Verification Check
            if not u.get('is_verified', 1):  # Default to 1 if column missing
                self.manager.temp_email = email
                self.manager.current = 'verify_email'
                return

            # 4. Profile Check: Form vs Portal
            table = "tutor_profiles" if role == 'tutor' else "student_profiles"
            p = db.query(f"SELECT email FROM {table} WHERE email=?", (email,), True)

            print(f"DEBUG: Checking {table} for {email}. Result: {p}")

            if not p:
                # User hasn't filled out the profile form yet
                target = f"{role}_form"
                print(f"DEBUG: Redirecting to Form: {target}")
                self.manager.get_screen(target).user_email = email
                self.manager.current = target
            else:
                # User already exists in profiles, go to Dashboard
                target = f"{role}_portal"
                print(f"DEBUG: Redirecting to Portal: {target}")
                self.manager.get_screen(target).user_email = email
                self.manager.current = target
        else:
            show_popup("Error", "Invalid Email or Password")


from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp


class Signup(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Main Container
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)

        # 1. Background/Watermark Logic
        self._set_watermark(layout)

        # 2. Header
        layout.add_widget(Label(
            text="SIGN UP",
            font_size=30,
            bold=True,
            color=TEXT if 'TEXT' in globals() else (1, 1, 1, 1)
        ))

        # 3. Input Fields
        self.email = themed_input("Email")
        self.pwd = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(45)
        )

        # 4. Role Selection (Toggle Buttons)
        role_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
        self.s_btn = ToggleButton(text='Student', group='role', state='down')
        self.t_btn = ToggleButton(text='Tutor', group='role')
        role_layout.add_widget(self.s_btn)
        role_layout.add_widget(self.t_btn)

        # 5. Buttons
        reg_btn = themed_button("REGISTER", SUCCESS, dp(50))
        reg_btn.bind(on_press=self.do_signup)

        back_btn = Button(
            text="Back to Login",
            background_color=(0, 0, 0, 0),
            color=PRIMARY if 'PRIMARY' in globals() else (0.2, 0.6, 1, 1),
            size_hint_y=None,
            height=dp(40)
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))

        # 6. Status Message Label
        self.msg = Label(
            text="",
            color=DANGER if 'DANGER' in globals() else (1, 0, 0, 1),
            size_hint_y=None,
            height=dp(28)
        )

        # Adding widgets to layout in order
        layout.add_widget(self.email)
        layout.add_widget(self.pwd)
        layout.add_widget(role_layout)
        layout.add_widget(reg_btn)
        layout.add_widget(back_btn)
        layout.add_widget(self.msg)

        self.add_widget(layout)

    def _set_watermark(self, layout):
        """Internal helper to prevent NameErrors if external function is missing."""
        try:
            # Try to call the global function if it exists
            if 'set_watermark' in globals():
                set_watermark(layout)
            else:
                # Fallback: Add a simple background color or logo here if needed
                print("Note: 'set_watermark' function not found, skipping background setup.")
        except Exception as e:
            print(f"Watermark error: {e}")

    def do_signup(self, _instance):
        from email_utils import send_verification_email_safe, generate_verification_code

        role = 'student' if self.s_btn.state == 'down' else 'tutor'
        email = self.email.text.strip()
        password = self.pwd.text

        if not (email and password):
            self.msg.text = "Please fill all fields"
            return

        # Database Check
        existing = db.query("SELECT email FROM users WHERE email=?", (email,), fetchone=True)
        if existing:
            self.msg.text = "Email already registered!"
            return

        verification_code = generate_verification_code()

        # Database Insert (Initial)
        ok = db.query(
            "INSERT INTO users (email, password, role, is_verified, verification_code) VALUES (?, ?, ?, 0, ?)",
            (email, password, role, verification_code)
        )

        if ok:
            # Loading UI
            content = BoxLayout(orientation='vertical', padding=20, spacing=10)
            content.add_widget(Label(text="Sending verification email...", color=(1, 1, 1, 1)))
            loading_popup = Popup(title="Please Wait", content=content, size_hint=(0.7, 0.3), auto_dismiss=False)
            loading_popup.open()

            def after_email_sent(success):
                loading_popup.dismiss()
                if success:
                    # Pass data to Manager
                    self.manager.temp_email = email
                    self.manager.temp_role = role
                    self.manager.temp_password = password

                    self.manager.current = 'verify_email'
                    self.msg.text = ""
                else:
                    # Rollback if email fails
                    db.query("DELETE FROM users WHERE email=?", (email,))
                    self.msg.text = "Email failed. Check your connection."
                    self.pwd.text = ""  # Security: clear password

            # Trigger Async Email
            send_verification_email_safe(email, verification_code, after_email_sent)
        else:
            self.msg.text = "Database error. Please try again."


from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from email_utils import resend_verification_code_async  #


class VerifyEmail(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Main layout
        l = BoxLayout(orientation='vertical', padding=50, spacing=20)
        set_rounded_panel(l, BG, 0)

        # Header and Input
        l.add_widget(Label(text="Enter Email Code", color=TEXT, font_size='18sp', bold=True))
        self.c_in = themed_input("6-Digit Code")
        l.add_widget(self.c_in)

        # Verify Button
        b_verify = themed_button("VERIFY", SUCCESS, 55)
        b_verify.bind(on_press=self.verify)
        l.add_widget(b_verify)

        # Resend Button (The new addition)
        # Using a secondary color or smaller height to distinguish it from the main action
        self.b_resend = themed_button("RESEND CODE", "#757575", 45)
        self.b_resend.bind(on_press=self.on_resend_click)
        l.add_widget(self.b_resend)

        self.add_widget(l)

    def verify(self, *args):
        # 1. Get the running app instance correctly
        from kivymd.app import MDApp
        app_instance = MDApp.get_running_app()

        # 2. Retrieve email and code
        e = getattr(self.manager, 'temp_email', '')
        c = self.c_in.text.strip()

        # 3. Use app_instance to reach the db_manager
        user = app_instance.db_manager.query(
            "SELECT * FROM users WHERE email=? AND verification_code=?",
            (e, c),
            fetchone=True
        )

        if user:
            app_instance.db_manager.query("UPDATE users SET is_verified=1 WHERE email=?", (e,))
            show_popup("Account Verified", "You can now login to ManaGuru.")
            self.manager.current = 'login'
        else:
            show_popup("Error", "Invalid code. Please try again.")

    def on_resend_click(self, *args):
        email = getattr(self.manager, 'temp_email', '')
        if not email:
            show_popup("Error", "Email not found. Please sign up again.")
            return

        # Disable button briefly to prevent spamming
        self.b_resend.disabled = True
        self.b_resend.text = "SENDING..."

        # Trigger the background process from email_utils.py
        resend_verification_code_async(
            email,
            app.db_manager,
            callback=self.on_resend_complete
        )

    def on_resend_complete(self, success):
        # Re-enable the button
        self.b_resend.disabled = False
        self.b_resend.text = "RESEND CODE"

        if success:
            show_popup("Sent", "A new 6-digit code has been sent to your email.")
        else:
            show_popup("Failed", "Could not send code. Check your internet connection.")


class AdminDashboard(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.l = BoxLayout(orientation='vertical', padding=10, spacing=10)
        set_rounded_panel(self.l, BG, 0)
        self.l.add_widget(Label(text="ADMIN PANEL", bold=True, color=PRIMARY,
                                size_hint_y=None, height=50, font_size='22sp'))

        self.tp = TabbedPanel(do_default_tab=False)
        self.tp.tab_width = dp(85)

        # --- Tab 1: Manage ---
        self.t1 = TabbedPanelItem(text="Manage")
        self.gl_m = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.gl_m.bind(minimum_height=self.gl_m.setter('height'))
        c1 = BoxLayout(orientation='vertical', padding=5)
        set_rounded_panel(c1, (1, 1, 1, 1))
        self.sb = themed_input("Search User")
        self.sb.bind(text=lambda i, v: self.load_m(v.lower()))
        c1.add_widget(self.sb)
        s1 = ScrollView()
        s1.add_widget(self.gl_m)
        c1.add_widget(s1)
        self.t1.add_widget(c1)

        # --- Tab 2: Verify ---
        self.t2 = TabbedPanelItem(text="Verify")
        self.g2 = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.g2.bind(minimum_height=self.g2.setter('height'))
        c2 = BoxLayout(orientation='vertical', padding=5)
        set_rounded_panel(c2, (1, 1, 1, 1))
        s2 = ScrollView()
        s2.add_widget(self.g2)
        c2.add_widget(s2)
        self.t2.add_widget(c2)

        # --- Tab 3: Credits ---
        self.t3 = TabbedPanelItem(text="Credits")
        self.g3 = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.g3.bind(minimum_height=self.g3.setter('height'))
        c3 = BoxLayout(orientation='vertical', padding=5)
        set_rounded_panel(c3, (1, 1, 1, 1))
        s3 = ScrollView()
        s3.add_widget(self.g3)
        c3.add_widget(s3)
        self.t3.add_widget(c3)

        # --- Tab 4: Offers/Broadcast ---
        self.t4 = TabbedPanelItem(text="Offers")
        c4 = BoxLayout(orientation='vertical', padding=15, spacing=10)
        set_rounded_panel(c4, (0.2, 0.2, 0.2, 1))
        c4.add_widget(Label(text="Broadcast Message", color=(1, 1, 1, 1)))
        self.off_in = TextInput(hint_text="Type message here...", multiline=True)
        c4.add_widget(self.off_in)
        br = BoxLayout(size_hint_y=None, height=50, spacing=10)
        s_b = themed_button("To Students", PRIMARY)
        t_b = themed_button("To Tutors", (0.5, 0.3, 0.8, 1))
        s_b.bind(on_press=lambda x: self.send_b('student'))
        t_b.bind(on_press=lambda x: self.send_b('tutor'))
        br.add_widget(s_b);
        br.add_widget(t_b)
        c4.add_widget(br)
        self.t4.add_widget(c4)

        self.tp.add_widget(self.t1);
        self.tp.add_widget(self.t2)
        self.tp.add_widget(self.t3);
        self.tp.add_widget(self.t4)
        self.l.add_widget(self.tp)

        # Footer
        footer = BoxLayout(size_hint_y=None, height=55, spacing=10)
        ref = themed_button("Refresh All", SUCCESS)
        out = themed_button("Logout", DANGER)
        ref.bind(on_press=lambda x: self.on_enter())
        out.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        footer.add_widget(ref);
        footer.add_widget(out)
        self.l.add_widget(footer)
        self.add_widget(self.l)

    def on_enter(self):
        self.load_m()
        self.load_v()
        self.load_c()

        # --- TAB 3: CREDITS LOGIC (Moved outside on_enter) ---

    def load_c(self):
        self.g3.clear_widgets()
        # Fetch from the exact node name the student app uses
        cloud_requests = db.get_all_from_cloud("credit_purchases")

        # Check your PyCharm terminal for this output!
        print(f"--- ADMIN DEBUG: Firebase says: {cloud_requests}")

        if not cloud_requests or cloud_requests == "null":
            self.g3.add_widget(Label(text="No pending requests", color=(0, 0, 0, 1)))
            return

        for key, data in cloud_requests.items():
            # Case-insensitive check (handles 'pending', 'Pending', etc.)
            status = str(data.get('status', '')).lower()

            if isinstance(data, dict) and status == 'pending':
                user_email = data.get('email', 'Unknown')
                utr_val = data.get('utr', 'N/A')

                row = BoxLayout(size_hint_y=None, height=dp(85), padding=10, spacing=10)
                set_rounded_panel(row, (0.95, 0.95, 0.95, 1))

                row.add_widget(Label(text=f"User: {user_email}\nUTR: {utr_val}",
                                     color=(0, 0, 0, 1), font_size='12sp'))

                btn = themed_button("Approve 10", SUCCESS, 45)
                # Link the specific Firebase key and email to the approval logic
                btn.bind(on_press=lambda x, k=key, e=user_email: self.process_approval(k, e))

                row.add_widget(btn)
                self.g3.add_widget(row)

    def process_approval(self, firebase_key, user_email):
        # Sanitize email for Firebase path (dots to underscores)
        sanitized_email = user_email.replace('.', '_')

        try:
            # 1. Mark the request as approved
            db.save_to_cloud("credit_purchases", firebase_key, {"status": "approved"})

            # 2. Update the specific student's credits in the cloud
            # This will target: student_profiles/ankuramacademy@gmail_com/credits
            db.save_to_cloud(f"student_profiles/{sanitized_email}", "credits", 10)

            # 3. Update local SQLite for offline speed
            db.query("UPDATE users SET credits = credits + 10 WHERE email=?", (user_email,))

            self.load_c()
            show_popup("Success", f"10 Credits added for {user_email}")
        except Exception as e:
            print(f"Sync Error: {e}")

    # --- TAB 1: MANAGE USERS ---
    def load_m(self, q=""):
        self.gl_m.clear_widgets()
        for role, table in [('tutor', 'tutor_profiles'), ('student', 'student_profiles')]:
            sql = f"SELECT * FROM {table}"
            params = ()
            if q:
                sql += " WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ?"
                params = (f"%{q}%", f"%{q}%")

            data = db.query(sql, params)
            for d in data:
                row = BoxLayout(size_hint_y=None, height=dp(75), padding=10, spacing=10)
                set_rounded_panel(row, (0.95, 0.95, 0.95, 1))
                row.add_widget(Label(text=f"{d['name']}\n{role.upper()}\n({d['status']})",
                                     color=(0, 0, 0, 1), font_size='11sp', halign='center'))
                v_btn = themed_button("View", PRIMARY, 40)
                v_btn.bind(
                    on_press=lambda x, dt=d: show_popup("Details", f"Email: {dt['email']}\nPhone: {dt['phone']}"))
                d_btn = themed_button("Del", DANGER, 40)
                d_btn.bind(on_press=lambda x, e=d['email'], t=table: self.delete_user(t, e))
                row.add_widget(v_btn);
                row.add_widget(d_btn)
                self.gl_m.add_widget(row)

    def delete_user(self, table, email):
        db.query(f"DELETE FROM {table} WHERE email=?", (email,))
        self.load_m()

    # --- TAB 2: VERIFY USERS ---
    def load_v(self):
        self.g2.clear_widgets()
        for role, table in [('tutor', 'tutor_profiles'), ('student', 'student_profiles')]:
            data = db.query(f"SELECT * FROM {table} WHERE status='pending'")
            for d in data:
                row = BoxLayout(size_hint_y=None, height=dp(80), padding=10, spacing=10)
                set_rounded_panel(row, (0.9, 0.95, 1, 1))
                row.add_widget(Label(text=f"{d['name']}\n{role.upper()}", color=(0, 0, 0, 1)))
                app_btn = themed_button("APPROVE", SUCCESS, 50)
                app_btn.bind(on_press=lambda x, t=table, e=d['email'], r=role: self.approve_user_now(t, e, r))
                row.add_widget(app_btn)
                self.g2.add_widget(row)

    def approve_user_now(self, table, email, role):
        local_data = db.query(f"SELECT * FROM {table} WHERE email=?", (email,))
        if local_data:
            full_data = dict(local_data[0])
            full_data['status'] = 'approved'
            if db.save_to_cloud(table, email, full_data):
                db.query(f"UPDATE {table} SET status='approved' WHERE email=?", (email,))
                show_popup("Success", f"{email} approved!")
                self.on_enter()
            else:
                show_popup("Error", "Cloud sync failed.")

    # --- TAB 4: BROADCAST ---
    def send_b(self, role):
        txt = self.off_in.text.strip()
        if txt:
            db.query("INSERT INTO admin_broadcasts (target_role, message_text) VALUES (?,?)", (role, txt))
            self.off_in.text = ""
            show_popup("Done", f"Broadcast sent to all {role}s")


import os
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock


class MyTutorApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"

        # 1. Initialize the manager HERE
        # This allows the Database class to call App.get_running_app() successfully
        from database import Database
        self.db_manager = Database()

        sm = ScreenManager()

        # Auth Screens
        sm.add_widget(Login(name='login'))
        sm.add_widget(Signup(name='signup'))
        sm.add_widget(VerifyEmail(name='verify_email'))

        # Registration Forms
        sm.add_widget(StudentForm(name='student_form'))
        sm.add_widget(TutorForm(name='tutor_form'))

        # Portals
        sm.add_widget(StudentPortal(name='student_portal'))
        sm.add_widget(TutorPortal(name='tutor_portal'))

        sm.add_widget(AdminDashboard(name='admin_screen'))
        sm.add_widget(Screen(name='qr_scanner'))

        return sm

    def on_start(self):
        # Using a small delay (0.5) ensures the UI is visible
        # before the heavy database work begins.
        Clock.schedule_once(lambda dt: self.initialize_database(), 0.5)

    def initialize_database(self):
        try:
            # This triggers the path logic we wrote (User Data Dir on Android)
            self.db_manager.setup_db()
            print("--- DATABASE INITIALIZED SUCCESSFULLY ---")
        except Exception as e:
            print(f"--- DATABASE ERROR: {e} ---")


if __name__ == '__main__':
    MyTutorApp().run()