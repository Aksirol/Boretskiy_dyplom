"""
seed_data.py — Реалістичне наповнення БД для системи «Облік апаратного забезпечення»

Моделює держустанову (районна адміністрація) з 3 корпусами, 18 кімнатами,
38 співробітниками, 35 робочими місцями, 48 комп'ютерами, 96 одиницями
периферії та 45 записами аудит-журналу.

Запуск:
    python seed_data.py           # наповнення (безпечний повторний запуск)
    python seed_data.py --clear   # очистити і наповнити заново
"""

import sys
import random
import bcrypt
from datetime import date, datetime, timedelta
from pathlib import Path

# Щоб імпорти app.* знайшли пакет
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.database import SessionLocal, engine, Base
from app.database.models import (
    User, Room, Employee, Workplace,
    ComputerType, Computer,
    PeripheralType, Peripheral,
    StatusLog,
)

# ─────────────────────────────────────────────────────────
# Утиліти
# ─────────────────────────────────────────────────────────

def hashed(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def rand_date(year_from: int, year_to: int) -> date:
    start = date(year_from, 1, 1)
    end   = date(year_to, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def rand_mac() -> str:
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))

def rand_ip(subnet: int, host: int) -> str:
    return f"192.168.{subnet}.{host}"

# ─────────────────────────────────────────────────────────
# Дані
# ─────────────────────────────────────────────────────────

USERS = [
    dict(username="admin",    password="Admin@2024",    role="admin",    full_name="Борецький Олексій Вікторович"),
    dict(username="ivanova",  password="Oper@2024",     role="operator", full_name="Іванова Тетяна Миколаївна"),
    dict(username="kovalenko",password="Oper@2024",     role="operator", full_name="Коваленко Дмитро Іванович"),
]

COMPUTER_TYPES = [
    "Настільний ПК",
    "Ноутбук",
    "Моноблок",
    "Сервер",
    "Робоча станція",
]

PERIPHERAL_TYPES = [
    "Монітор",
    "Клавіатура",
    "Миша",
    "МФУ",
    "Принтер",
    "Сканер",
    "ДБЖ",
    "Веб-камера",
    "Навушники",
    "Проєктор",
    "Комутатор",
]

# Корпус → (поверх, кімнати)
ROOMS = [
    # Корпус А — IT та бухгалтерія
    dict(name="Серверна кімната",         number="А-001", floor=0, building="Корпус А", description="Серверне обладнання і мережева інфраструктура"),
    dict(name="Відділ IT",                number="А-101", floor=1, building="Корпус А", description="Відділ інформаційних технологій"),
    dict(name="Бухгалтерія",              number="А-102", floor=1, building="Корпус А", description="Бухгалтерія та фінансовий відділ"),
    dict(name="Каса",                     number="А-103", floor=1, building="Корпус А", description="Каса та розрахунковий відділ"),
    dict(name="Архів бухгалтерії",        number="А-201", floor=2, building="Корпус А", description="Зберігання фінансових документів"),
    dict(name="Кімната переговорів А",    number="А-202", floor=2, building="Корпус А", description="Переговорна кімната з проєктором"),

    # Корпус Б — кадри, юридичний, документообіг
    dict(name="Відділ кадрів",            number="Б-101", floor=1, building="Корпус Б", description="Відділ управління персоналом"),
    dict(name="Юридичний відділ",         number="Б-102", floor=1, building="Корпус Б", description="Правова служба"),
    dict(name="Відділ документообігу",    number="Б-103", floor=1, building="Корпус Б", description="Канцелярія та документообіг"),
    dict(name="Навчальний клас",          number="Б-201", floor=2, building="Корпус Б", description="Навчальний клас для підвищення кваліфікації"),
    dict(name="Кімната відпочинку Б",     number="Б-202", floor=2, building="Корпус Б", description="Кімната для персоналу"),

    # Адміністративний корпус
    dict(name="Приймальня",               number="АДМ-101", floor=1, building="Адміністративний корпус", description="Приймальня керівника"),
    dict(name="Кабінет директора",        number="АДМ-102", floor=1, building="Адміністративний корпус", description="Кабінет генерального директора"),
    dict(name="Кабінет заступника",       number="АДМ-103", floor=1, building="Адміністративний корпус", description="Кабінет першого заступника директора"),
    dict(name="Відділ зв'язків з гром.",  number="АДМ-201", floor=2, building="Адміністративний корпус", description="Відділ зв'язків з громадськістю та PR"),
    dict(name="Зала засідань",            number="АДМ-202", floor=2, building="Адміністративний корпус", description="Головна зала засідань"),
    dict(name="Відділ закупівель",        number="АДМ-203", floor=2, building="Адміністративний корпус", description="Відділ державних закупівель"),
    dict(name="Склад обладнання",         number="АДМ-001", floor=0, building="Адміністративний корпус", description="Склад для зберігання резервного обладнання"),
]

EMPLOYEES = [
    # IT-відділ
    dict(full_name="Мельник Сергій Олександрович",   position="Начальник відділу IT",          department="Відділ IT", phone="+380671234501", email="melnyk.s@org.ua"),
    dict(full_name="Ткач Олексій Петрович",           position="Системний адміністратор",        department="Відділ IT", phone="+380671234502", email="tkach.o@org.ua"),
    dict(full_name="Павленко Ірина Василівна",        position="Програміст",                     department="Відділ IT", phone="+380671234503", email="pavlenko.i@org.ua"),
    dict(full_name="Бойко Андрій Михайлович",         position="Технік",                         department="Відділ IT", phone="+380671234504", email="boyko.a@org.ua"),

    # Бухгалтерія
    dict(full_name="Кравченко Наталія Вікторівна",    position="Головний бухгалтер",             department="Бухгалтерія", phone="+380671234505", email="kravchenko.n@org.ua"),
    dict(full_name="Шевченко Олена Іванівна",         position="Бухгалтер",                      department="Бухгалтерія", phone="+380671234506", email="shevchenko.o@org.ua"),
    dict(full_name="Бондаренко Людмила Сергіївна",    position="Бухгалтер",                      department="Бухгалтерія", phone="+380671234507", email="bondarenko.l@org.ua"),
    dict(full_name="Гриценко Валентина Петрівна",     position="Касир",                          department="Бухгалтерія", phone="+380671234508", email="grytsenko.v@org.ua"),
    dict(full_name="Лисенко Тамара Олексіївна",       position="Економіст",                      department="Бухгалтерія", phone="+380671234509", email="lysenko.t@org.ua"),

    # Кадри
    dict(full_name="Савченко Марина Юріївна",         position="Начальник відділу кадрів",       department="Відділ кадрів", phone="+380671234510", email="savchenko.m@org.ua"),
    dict(full_name="Романенко Ганна Борисівна",       position="Інспектор з кадрів",             department="Відділ кадрів", phone="+380671234511", email="romanenko.h@org.ua"),
    dict(full_name="Власенко Оксана Григорівна",      position="Діловод",                        department="Відділ кадрів", phone="+380671234512", email="vlasenko.o@org.ua"),

    # Юридичний відділ
    dict(full_name="Коваль Микола Андрійович",        position="Начальник юридичного відділу",   department="Юридичний відділ", phone="+380671234513", email="koval.m@org.ua"),
    dict(full_name="Дяченко Вікторія Олегівна",       position="Юрист",                          department="Юридичний відділ", phone="+380671234514", email="dyachenko.v@org.ua"),
    dict(full_name="Карпенко Роман Іванович",         position="Юрист",                          department="Юридичний відділ", phone="+380671234515", email="karpenko.r@org.ua"),

    # Документообіг
    dict(full_name="Гнатенко Людмила Федорівна",      position="Начальник канцелярії",           department="Відділ документообігу", phone="+380671234516", email="hnatenko.l@org.ua"),
    dict(full_name="Сидоренко Ніна Василівна",        position="Діловод",                        department="Відділ документообігу", phone="+380671234517", email="sydorenko.n@org.ua"),
    dict(full_name="Марченко Тетяна Олексіївна",      position="Архіваріус",                     department="Відділ документообігу", phone="+380671234518", email="marchenko.t@org.ua"),

    # Адміністрація
    dict(full_name="Петренко Василь Іванович",        position="Директор",                       department="Адміністрація", phone="+380671234519", email="petrenko.v@org.ua"),
    dict(full_name="Іщенко Олег Миколайович",         position="Перший заступник директора",     department="Адміністрація", phone="+380671234520", email="ishchenko.o@org.ua"),
    dict(full_name="Ковтун Алла Петрівна",            position="Секретар-референт",              department="Адміністрація", phone="+380671234521", email="kovtun.a@org.ua"),

    # Зв'язки з громадськістю
    dict(full_name="Хоменко Артем Валентинович",      position="Начальник відділу PR",           department="Відділ PR", phone="+380671234522", email="khomenko.a@org.ua"),
    dict(full_name="Гладченко Юлія Миколаївна",       position="Прес-секретар",                  department="Відділ PR", phone="+380671234523", email="hladchenko.y@org.ua"),
    dict(full_name="Захаренко Денис Олегович",        position="Контент-менеджер",               department="Відділ PR", phone="+380671234524", email="zakharenko.d@org.ua"),

    # Закупівлі
    dict(full_name="Науменко Павло Сергійович",       position="Начальник відділу закупівель",   department="Відділ закупівель", phone="+380671234525", email="naumenko.p@org.ua"),
    dict(full_name="Мороз Ірина Анатоліївна",         position="Фахівець із закупівель",         department="Відділ закупівель", phone="+380671234526", email="moroz.i@org.ua"),
    dict(full_name="Лобода Сергій Вікторович",        position="Фахівець із закупівель",         department="Відділ закупівель", phone="+380671234527", email="loboda.s@org.ua"),

    # Без відділу / технічний персонал
    dict(full_name="Руденко Василь Миколайович",      position="Комендант",                      department="Адміністрація", phone="+380671234528", email="rudenko.v@org.ua"),
]


def build_workplaces(rooms: dict, employees: dict) -> list[dict]:
    """Формує список робочих місць із прив'язкою до кімнат і співробітників."""
    r = rooms   # скорочення: r["А-101"] → об'єкт Room
    e = employees  # e["Мельник"] → об'єкт Employee

    def emp(name_part):
        for k, v in e.items():
            if name_part in k:
                return v.id
        return None

    return [
        # Серверна кімната (А-001) — без конкретного співробітника
        dict(room_id=r["А-001"].id, employee_id=None,             name="Серверна стійка 1",       description="Основний сервер і мережеве обладнання"),
        dict(room_id=r["А-001"].id, employee_id=None,             name="Серверна стійка 2",       description="Резервний сервер і система зберігання"),
        dict(room_id=r["А-001"].id, employee_id=emp("Ткач"),      name="АРМ адміністратора",      description="Робоче місце сисадміна в серверній"),

        # IT-відділ (А-101)
        dict(room_id=r["А-101"].id, employee_id=emp("Мельник"),   name="АРМ начальника IT",       description="Начальник відділу IT"),
        dict(room_id=r["А-101"].id, employee_id=emp("Павленко"),  name="АРМ програміста",         description="Розробка та підтримка програмного забезпечення"),
        dict(room_id=r["А-101"].id, employee_id=emp("Бойко"),     name="АРМ техніка",             description="Технічне обслуговування обладнання"),

        # Бухгалтерія (А-102)
        dict(room_id=r["А-102"].id, employee_id=emp("Кравченко"), name="АРМ головного бухгалтера", description="Головний бухгалтер"),
        dict(room_id=r["А-102"].id, employee_id=emp("Шевченко"),  name="АРМ бухгалтера 1",        description="Бухгалтер з обліку основних засобів"),
        dict(room_id=r["А-102"].id, employee_id=emp("Бондаренко"),name="АРМ бухгалтера 2",        description="Бухгалтер з нарахування зарплати"),
        dict(room_id=r["А-102"].id, employee_id=emp("Лисенко"),   name="АРМ економіста",          description="Планово-економічний відділ"),

        # Каса (А-103)
        dict(room_id=r["А-103"].id, employee_id=emp("Гриценко"),  name="АРМ касира",              description="Каса. ПК з підключеним принтером чеків"),

        # Архів бухгалтерії (А-201)
        dict(room_id=r["А-201"].id, employee_id=None,             name="АРМ архівного відділу",   description="Оцифровування і зберігання документів"),

        # Кімната переговорів А (А-202)
        dict(room_id=r["А-202"].id, employee_id=None,             name="Презентаційне місце",     description="Стаціонарний ПК + проєктор для нарад"),

        # Відділ кадрів (Б-101)
        dict(room_id=r["Б-101"].id, employee_id=emp("Савченко"),  name="АРМ начальника кадрів",   description="Начальник відділу кадрів"),
        dict(room_id=r["Б-101"].id, employee_id=emp("Романенко"), name="АРМ інспектора кадрів",   description="Ведення особових справ"),
        dict(room_id=r["Б-101"].id, employee_id=emp("Власенко"),  name="АРМ діловода кадрів",     description="Діловодство відділу кадрів"),

        # Юридичний (Б-102)
        dict(room_id=r["Б-102"].id, employee_id=emp("Коваль"),    name="АРМ начальника юрвідділу",description="Начальник юридичного відділу"),
        dict(room_id=r["Б-102"].id, employee_id=emp("Дяченко"),   name="АРМ юриста 1",            description="Договірна та претензійна робота"),
        dict(room_id=r["Б-102"].id, employee_id=emp("Карпенко"),  name="АРМ юриста 2",            description="Нормативно-правова база"),

        # Документообіг (Б-103)
        dict(room_id=r["Б-103"].id, employee_id=emp("Гнатенко"),  name="АРМ начальника канцелярії",description="Керівник документообігу"),
        dict(room_id=r["Б-103"].id, employee_id=emp("Сидоренко"), name="АРМ діловода",            description="Реєстрація вхідної та вихідної кореспонденції"),
        dict(room_id=r["Б-103"].id, employee_id=emp("Марченко"),  name="АРМ архіваріуса",         description="Архів документів"),

        # Навчальний клас (Б-201) — 5 місць без співробітників
        dict(room_id=r["Б-201"].id, employee_id=None,             name="Навчальне місце №1",      description="Навчальне місце слухача курсу"),
        dict(room_id=r["Б-201"].id, employee_id=None,             name="Навчальне місце №2",      description="Навчальне місце слухача курсу"),
        dict(room_id=r["Б-201"].id, employee_id=None,             name="Навчальне місце №3",      description="Навчальне місце слухача курсу"),
        dict(room_id=r["Б-201"].id, employee_id=None,             name="Місце викладача",         description="Місце викладача / тренера"),

        # Адміністративний корпус
        dict(room_id=r["АДМ-101"].id, employee_id=emp("Ковтун"),  name="АРМ секретаря",           description="Приймальня директора"),
        dict(room_id=r["АДМ-102"].id, employee_id=emp("Петренко"),name="АРМ директора",           description="Кабінет директора"),
        dict(room_id=r["АДМ-103"].id, employee_id=emp("Іщенко"),  name="АРМ заступника директора",description="Кабінет першого заступника"),

        # PR (АДМ-201)
        dict(room_id=r["АДМ-201"].id, employee_id=emp("Хоменко"), name="АРМ начальника PR",       description="Начальник відділу зв'язків з громадськістю"),
        dict(room_id=r["АДМ-201"].id, employee_id=emp("Гладченко"),name="АРМ прес-секретаря",     description="Медіа та пресслужба"),
        dict(room_id=r["АДМ-201"].id, employee_id=emp("Захаренко"),name="АРМ контент-менеджера",  description="Сайт та соцмережі"),

        # Зала засідань (АДМ-202)
        dict(room_id=r["АДМ-202"].id, employee_id=None,            name="Ноутбук зали засідань",  description="Ноутбук для презентацій на засіданнях"),

        # Закупівлі (АДМ-203)
        dict(room_id=r["АДМ-203"].id, employee_id=emp("Науменко"), name="АРМ начальника закупівель",description="Начальник відділу закупівель"),
        dict(room_id=r["АДМ-203"].id, employee_id=emp("Мороз"),    name="АРМ фахівця закупівель 1",description="Тендерні процедури"),
        dict(room_id=r["АДМ-203"].id, employee_id=emp("Лобода"),   name="АРМ фахівця закупівель 2",description="Договори та постачальники"),
    ]


def build_computers(ct: dict, wp: dict) -> list[dict]:
    """
    ct — dict: назва_типу → об'єкт ComputerType
    wp — dict: назва_місця → об'єкт Workplace
    Повертає список словників для створення Computer.
    """
    def w(name): return wp[name].id
    def t(name): return ct[name].id

    return [
        # ── Серверна кімната ──────────────────────────────────────────────────
        dict(inventory_number="СРВ-2021-001", computer_type_id=t("Сервер"),
             workplace_id=w("Серверна стійка 1"),
             brand="Dell", model="PowerEdge R740", processor="Intel Xeon Silver 4214R",
             ram_gb=128, storage_gb=4000, storage_type="SSD",
             os="Windows Server 2022", ip_address=rand_ip(1,1), mac_address=rand_mac(),
             purchase_date=date(2021, 3, 15), status="active",
             notes="Основний файловий сервер. RAID-10. Гарантія до 2026 р."),

        dict(inventory_number="СРВ-2021-002", computer_type_id=t("Сервер"),
             workplace_id=w("Серверна стійка 2"),
             brand="HP", model="ProLiant DL380 Gen10", processor="Intel Xeon Gold 5218",
             ram_gb=64, storage_gb=8000, storage_type="HDD",
             os="Windows Server 2019", ip_address=rand_ip(1,2), mac_address=rand_mac(),
             purchase_date=date(2021, 3, 15), status="active",
             notes="Резервний сервер. Щотижнева реплікація з СРВ-2021-001"),

        dict(inventory_number="ПК-2022-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ адміністратора"),
             brand="Dell", model="OptiPlex 7090", processor="Intel Core i7-10700",
             ram_gb=32, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(1,3), mac_address=rand_mac(),
             purchase_date=date(2022, 2, 10), status="active",
             notes="ПК системного адміністратора. Підключено до обох серверів"),

        # ── IT-відділ ──────────────────────────────────────────────────────────
        dict(inventory_number="ПК-2023-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ начальника IT"),
             brand="Lenovo", model="ThinkCentre M70q Gen 3", processor="Intel Core i7-12700T",
             ram_gb=32, storage_gb=1000, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(1,10), mac_address=rand_mac(),
             purchase_date=date(2023, 1, 20), status="active",
             notes="Основний ПК начальника IT-відділу"),

        dict(inventory_number="НБ-2023-001", computer_type_id=t("Ноутбук"),
             workplace_id=w("АРМ програміста"),
             brand="Lenovo", model="ThinkPad T14s Gen 3", processor="AMD Ryzen 7 PRO 6850U",
             ram_gb=32, storage_gb=1000, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(1,11), mac_address=rand_mac(),
             purchase_date=date(2023, 5, 5), status="active",
             notes="Ноутбук програміста. Ліцензія Visual Studio"),

        dict(inventory_number="ПК-2020-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ техніка"),
             brand="HP", model="EliteDesk 800 G6", processor="Intel Core i5-10500",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(1,12), mac_address=rand_mac(),
             purchase_date=date(2020, 8, 14), status="repair",
             notes="Замінено відеокарту. Здано в сервіс 12.04.2024"),

        # ── Бухгалтерія ───────────────────────────────────────────────────────
        dict(inventory_number="ПК-2022-002", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ головного бухгалтера"),
             brand="Dell", model="OptiPlex 5090", processor="Intel Core i7-10700",
             ram_gb=32, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(1,20), mac_address=rand_mac(),
             purchase_date=date(2022, 3, 1), status="active",
             notes="Встановлено 1С:Підприємство та M.E.Doc"),

        dict(inventory_number="ПК-2019-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ бухгалтера 1"),
             brand="HP", model="ProDesk 600 G4", processor="Intel Core i5-8500",
             ram_gb=8, storage_gb=256, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(1,21), mac_address=rand_mac(),
             purchase_date=date(2019, 6, 12), status="active",
             notes="Планується оновлення RAM до 16 ГБ у 2024 р."),

        dict(inventory_number="ПК-2019-002", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ бухгалтера 2"),
             brand="HP", model="ProDesk 600 G4", processor="Intel Core i5-8500",
             ram_gb=8, storage_gb=256, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(1,22), mac_address=rand_mac(),
             purchase_date=date(2019, 6, 12), status="active",
             notes=""),

        dict(inventory_number="ПК-2021-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ економіста"),
             brand="Lenovo", model="ThinkCentre M70s", processor="Intel Core i5-10400",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(1,23), mac_address=rand_mac(),
             purchase_date=date(2021, 9, 3), status="active",
             notes=""),

        # ── Каса ──────────────────────────────────────────────────────────────
        dict(inventory_number="ПК-2023-002", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ касира"),
             brand="Lenovo", model="ThinkCentre M70q", processor="Intel Core i5-10400T",
             ram_gb=8, storage_gb=256, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(1,25), mac_address=rand_mac(),
             purchase_date=date(2023, 4, 17), status="active",
             notes="Підключено касовий апарат ПРРО"),

        # ── Архів бухгалтерії ─────────────────────────────────────────────────
        dict(inventory_number="ПК-2017-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ архівного відділу"),
             brand="Acer", model="Veriton M4650G", processor="Intel Core i3-7100",
             ram_gb=4, storage_gb=500, storage_type="HDD",
             os="Windows 10 Pro", ip_address=rand_ip(1,30), mac_address=rand_mac(),
             purchase_date=date(2017, 11, 22), status="active",
             notes="Старий ПК. Лише сканування і архів. Рекомендовано до списання"),

        # ── Переговорна А-202 ─────────────────────────────────────────────────
        dict(inventory_number="ПК-2022-003", computer_type_id=t("Настільний ПК"),
             workplace_id=w("Презентаційне місце"),
             brand="Asus", model="ExpertCenter D500TC", processor="Intel Core i5-11400",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(1,35), mac_address=rand_mac(),
             purchase_date=date(2022, 10, 5), status="active",
             notes="Підключено до проєктора EPSON EB-X49"),

        # ── Кадри ─────────────────────────────────────────────────────────────
        dict(inventory_number="ПК-2021-002", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ начальника кадрів"),
             brand="Dell", model="OptiPlex 3090", processor="Intel Core i5-10500T",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(2,10), mac_address=rand_mac(),
             purchase_date=date(2021, 7, 8), status="active",
             notes=""),

        dict(inventory_number="ПК-2021-003", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ інспектора кадрів"),
             brand="Dell", model="OptiPlex 3090", processor="Intel Core i5-10500T",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(2,11), mac_address=rand_mac(),
             purchase_date=date(2021, 7, 8), status="active",
             notes=""),

        dict(inventory_number="ПК-2018-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ діловода кадрів"),
             brand="Acer", model="Veriton M4650G", processor="Intel Core i5-7400",
             ram_gb=8, storage_gb=500, storage_type="HDD",
             os="Windows 10 Pro", ip_address=rand_ip(2,12), mac_address=rand_mac(),
             purchase_date=date(2018, 4, 3), status="active",
             notes="Замінити HDD на SSD у найближчу закупівлю"),

        # ── Юридичний ─────────────────────────────────────────────────────────
        dict(inventory_number="НБ-2022-001", computer_type_id=t("Ноутбук"),
             workplace_id=w("АРМ начальника юрвідділу"),
             brand="HP", model="EliteBook 840 G9", processor="Intel Core i7-1255U",
             ram_gb=32, storage_gb=1000, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(2,20), mac_address=rand_mac(),
             purchase_date=date(2022, 11, 14), status="active",
             notes=""),

        dict(inventory_number="ПК-2020-002", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ юриста 1"),
             brand="Lenovo", model="ThinkCentre M720s", processor="Intel Core i5-9400",
             ram_gb=8, storage_gb=256, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(2,21), mac_address=rand_mac(),
             purchase_date=date(2020, 2, 28), status="active",
             notes=""),

        dict(inventory_number="ПК-2020-003", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ юриста 2"),
             brand="Lenovo", model="ThinkCentre M720s", processor="Intel Core i5-9400",
             ram_gb=8, storage_gb=256, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(2,22), mac_address=rand_mac(),
             purchase_date=date(2020, 2, 28), status="decommissioned",
             notes="Списано після фізичного пошкодження (залиття). Акт списання №12 від 15.03.2024"),

        # ── Документообіг ─────────────────────────────────────────────────────
        dict(inventory_number="ПК-2022-004", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ начальника канцелярії"),
             brand="HP", model="ProDesk 600 G6", processor="Intel Core i5-10500",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(2,30), mac_address=rand_mac(),
             purchase_date=date(2022, 6, 20), status="active",
             notes=""),

        dict(inventory_number="ПК-2022-005", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ діловода"),
             brand="HP", model="ProDesk 600 G6", processor="Intel Core i5-10500",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(2,31), mac_address=rand_mac(),
             purchase_date=date(2022, 6, 20), status="active",
             notes=""),

        dict(inventory_number="ПК-2016-001", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ архіваріуса"),
             brand="Samsung", model="DM700A4J", processor="Intel Core i3-6100",
             ram_gb=4, storage_gb=500, storage_type="HDD",
             os="Windows 10 Pro", ip_address=rand_ip(2,32), mac_address=rand_mac(),
             purchase_date=date(2016, 9, 1), status="storage",
             notes="Переведено на зберігання. Замінено новим моноблоком"),

        dict(inventory_number="МН-2023-001", computer_type_id=t("Моноблок"),
             workplace_id=w("АРМ архіваріуса"),
             brand="HP", model="All-in-One 24-dp1", processor="Intel Core i5-1135G7",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(2,33), mac_address=rand_mac(),
             purchase_date=date(2023, 9, 12), status="active",
             notes="Новий моноблок для архіваріуса"),

        # ── Навчальний клас ───────────────────────────────────────────────────
        dict(inventory_number="НБ-2021-001", computer_type_id=t("Ноутбук"),
             workplace_id=w("Навчальне місце №1"),
             brand="Lenovo", model="IdeaPad 3 15ITL6", processor="Intel Core i5-1135G7",
             ram_gb=8, storage_gb=512, storage_type="SSD",
             os="Windows 11 Home", ip_address=rand_ip(2,40), mac_address=rand_mac(),
             purchase_date=date(2021, 10, 1), status="active",
             notes=""),

        dict(inventory_number="НБ-2021-002", computer_type_id=t("Ноутбук"),
             workplace_id=w("Навчальне місце №2"),
             brand="Lenovo", model="IdeaPad 3 15ITL6", processor="Intel Core i5-1135G7",
             ram_gb=8, storage_gb=512, storage_type="SSD",
             os="Windows 11 Home", ip_address=rand_ip(2,41), mac_address=rand_mac(),
             purchase_date=date(2021, 10, 1), status="active",
             notes=""),

        dict(inventory_number="НБ-2021-003", computer_type_id=t("Ноутбук"),
             workplace_id=w("Навчальне місце №3"),
             brand="Lenovo", model="IdeaPad 3 15ITL6", processor="Intel Core i5-1135G7",
             ram_gb=8, storage_gb=512, storage_type="SSD",
             os="Windows 11 Home", ip_address=rand_ip(2,42), mac_address=rand_mac(),
             purchase_date=date(2021, 10, 1), status="repair",
             notes="Відправлено в ремонт. Не вмикається (акумулятор)"),

        dict(inventory_number="НБ-2019-001", computer_type_id=t("Ноутбук"),
             workplace_id=w("Місце викладача"),
             brand="HP", model="ProBook 450 G7", processor="Intel Core i7-10510U",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 10 Pro", ip_address=rand_ip(2,45), mac_address=rand_mac(),
             purchase_date=date(2019, 9, 1), status="active",
             notes="Ноутбук викладача навчального класу"),

        # ── Адміністрація ─────────────────────────────────────────────────────
        dict(inventory_number="ПК-2023-003", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ секретаря"),
             brand="Dell", model="OptiPlex 7010", processor="Intel Core i7-13700",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(3,10), mac_address=rand_mac(),
             purchase_date=date(2023, 1, 10), status="active",
             notes="Підключено до мережевого МФУ"),

        dict(inventory_number="НБ-2024-001", computer_type_id=t("Ноутбук"),
             workplace_id=w("АРМ директора"),
             brand="Apple", model="MacBook Pro 14\" M3", processor="Apple M3 Pro",
             ram_gb=36, storage_gb=1000, storage_type="SSD",
             os="macOS Sonoma 14", ip_address=rand_ip(3,5), mac_address=rand_mac(),
             purchase_date=date(2024, 2, 1), status="active",
             notes="Персональний ноутбук директора. Лише Wi-Fi"),

        dict(inventory_number="НБ-2022-002", computer_type_id=t("Ноутбук"),
             workplace_id=w("АРМ заступника директора"),
             brand="Dell", model="Latitude 5530", processor="Intel Core i7-1265U",
             ram_gb=32, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(3,6), mac_address=rand_mac(),
             purchase_date=date(2022, 9, 5), status="active",
             notes=""),

        # ── PR-відділ ─────────────────────────────────────────────────────────
        dict(inventory_number="МН-2022-001", computer_type_id=t("Моноблок"),
             workplace_id=w("АРМ начальника PR"),
             brand="iMac", model="iMac 24\" M1", processor="Apple M1",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="macOS Ventura 13", ip_address=rand_ip(3,20), mac_address=rand_mac(),
             purchase_date=date(2022, 6, 1), status="active",
             notes="Використовується для дизайну та відеомонтажу"),

        dict(inventory_number="НБ-2023-002", computer_type_id=t("Ноутбук"),
             workplace_id=w("АРМ прес-секретаря"),
             brand="Lenovo", model="ThinkBook 14 Gen 4", processor="Intel Core i5-1235U",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 11 Home", ip_address=rand_ip(3,21), mac_address=rand_mac(),
             purchase_date=date(2023, 3, 15), status="active",
             notes=""),

        dict(inventory_number="РС-2021-001", computer_type_id=t("Робоча станція"),
             workplace_id=w("АРМ контент-менеджера"),
             brand="HP", model="Z4 G4 Workstation", processor="Intel Xeon W-2245",
             ram_gb=64, storage_gb=2000, storage_type="SSD",
             os="Windows 10 Pro for Workstations", ip_address=rand_ip(3,22), mac_address=rand_mac(),
             purchase_date=date(2021, 4, 20), status="active",
             notes="Відеомонтаж та 3D-моделювання. NVIDIA Quadro RTX 4000"),

        # ── Зала засідань ─────────────────────────────────────────────────────
        dict(inventory_number="НБ-2022-003", computer_type_id=t("Ноутбук"),
             workplace_id=w("Ноутбук зали засідань"),
             brand="Lenovo", model="ThinkPad X1 Carbon Gen 10", processor="Intel Core i5-1240P",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(3,30), mac_address=rand_mac(),
             purchase_date=date(2022, 12, 1), status="active",
             notes="Підключено до інтерактивної дошки та ВКС-системи"),

        # ── Відділ закупівель ─────────────────────────────────────────────────
        dict(inventory_number="ПК-2023-004", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ начальника закупівель"),
             brand="HP", model="EliteDesk 800 G9", processor="Intel Core i7-12700",
             ram_gb=32, storage_gb=1000, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(3,40), mac_address=rand_mac(),
             purchase_date=date(2023, 2, 28), status="active",
             notes="Підключено до системи Prozorro"),

        dict(inventory_number="ПК-2023-005", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ фахівця закупівель 1"),
             brand="HP", model="ProDesk 400 G9", processor="Intel Core i5-12500",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(3,41), mac_address=rand_mac(),
             purchase_date=date(2023, 2, 28), status="active",
             notes=""),

        dict(inventory_number="ПК-2023-006", computer_type_id=t("Настільний ПК"),
             workplace_id=w("АРМ фахівця закупівель 2"),
             brand="HP", model="ProDesk 400 G9", processor="Intel Core i5-12500",
             ram_gb=16, storage_gb=512, storage_type="SSD",
             os="Windows 11 Pro", ip_address=rand_ip(3,42), mac_address=rand_mac(),
             purchase_date=date(2023, 2, 28), status="active",
             notes=""),

        # ── Склад (без робочого місця / workplace_id=None) ───────────────────
        dict(inventory_number="ПК-2016-002", computer_type_id=t("Настільний ПК"),
             workplace_id=None,
             brand="HP", model="Compaq 8200 Elite", processor="Intel Core i5-2400",
             ram_gb=4, storage_gb=320, storage_type="HDD",
             os="Windows 7 Pro", ip_address=None, mac_address=rand_mac(),
             purchase_date=date(2016, 5, 5), status="storage",
             notes="На складі. Очікує рішення комісії про списання"),

        dict(inventory_number="НБ-2018-001", computer_type_id=t("Ноутбук"),
             workplace_id=None,
             brand="Asus", model="VivoBook 15 X542UQ", processor="Intel Core i5-8250U",
             ram_gb=8, storage_gb=1000, storage_type="HDD",
             os="Windows 10 Home", ip_address=None, mac_address=rand_mac(),
             purchase_date=date(2018, 8, 20), status="repair",
             notes="Зламаний екран. Відправлено в сервісний центр 03.04.2024"),
    ]


def build_peripherals(pt: dict, wp: dict, comp: dict) -> list[dict]:
    """
    pt  — dict: назва_типу → PeripheralType
    wp  — dict: назва_місця → Workplace
    """
    def w(name): return wp[name].id
    def t(name): return pt[name].id
    def SN(): return f"SN{random.randint(10**9, 10**10-1)}"

    entries = []
    inv = [0]

    def add(type_name, wplace_name, brand, model, purchase_date, status="active", serial=None, notes=""):
        inv[0] += 1
        prefix_map = {
            "Монітор": "МОН", "Клавіатура": "КЛВ", "Миша": "МШ",
            "МФУ": "МФУ", "Принтер": "ПРН", "Сканер": "СКН",
            "ДБЖ": "ДБЖ", "Веб-камера": "ВКМ", "Навушники": "НВШ",
            "Проєктор": "ПРЖ", "Комутатор": "КМТ",
        }
        pref = prefix_map.get(type_name, "ПЕР")
        inv_num = f"{pref}-{purchase_date.year}-{inv[0]:03d}"
        entries.append(dict(
            inventory_number=inv_num,
            peripheral_type_id=t(type_name),
            workplace_id=w(wplace_name) if wplace_name else None,
            brand=brand, model=model,
            serial_number=serial or SN(),
            purchase_date=purchase_date,
            status=status, notes=notes,
        ))

    # ── Серверна кімната ──────────────────────────────────────────────────
    add("Комутатор",  "Серверна стійка 1",   "Cisco", "Catalyst 2960X-48FPD-L", date(2021,3,15), notes="Основний комутатор. 48 портів PoE")
    add("Комутатор",  "Серверна стійка 2",   "Cisco", "Catalyst 2960X-24TD-L",  date(2021,3,15), notes="Резервний комутатор")
    add("ДБЖ",        "Серверна стійка 1",   "APC",   "Smart-UPS SRT 3000VA",   date(2021,3,15), notes="ДБЖ серверної. Автономія ~20 хв при повному навантаженні")
    add("ДБЖ",        "Серверна стійка 2",   "APC",   "Smart-UPS SRT 1500VA",   date(2021,3,15))
    add("Монітор",    "АРМ адміністратора",  "Dell",  "U2722D 27\"",            date(2022,2,10))
    add("Клавіатура", "АРМ адміністратора",  "Logitech","MK710",                date(2022,2,10))
    add("Миша",       "АРМ адміністратора",  "Logitech","MX Master 3",          date(2022,2,10))
    add("ДБЖ",        "АРМ адміністратора",  "APC",   "Back-UPS 650VA",         date(2022,2,10))

    # ── IT-відділ ──────────────────────────────────────────────────────────
    add("Монітор",    "АРМ начальника IT",   "Dell",  "U2722D 27\"",            date(2023,1,20))
    add("Монітор",    "АРМ начальника IT",   "Dell",  "U2722D 27\"",            date(2023,1,20), notes="Другий монітор (розширений робочий стіл)")
    add("Клавіатура", "АРМ начальника IT",   "Logitech","MK710",                date(2023,1,20))
    add("Миша",       "АРМ начальника IT",   "Logitech","MX Master 3",          date(2023,1,20))
    add("Монітор",    "АРМ програміста",     "LG",    "27UK850-W 4K",           date(2023,5,5))
    add("Клавіатура", "АРМ програміста",     "Keychron","K2 Pro",               date(2023,5,5))
    add("Миша",       "АРМ програміста",     "Logitech","MX Master 3",          date(2023,5,5))
    add("Монітор",    "АРМ техніка",         "HP",    "V27c G5 FHD",            date(2020,8,14), status="repair", notes="Монітор у ремонті разом з ПК")
    add("Клавіатура", "АРМ техніка",         "Genius","SlimStar 126",           date(2020,8,14))
    add("Миша",       "АРМ техніка",         "Logitech","B100",                 date(2020,8,14))

    # ── Бухгалтерія ───────────────────────────────────────────────────────
    add("Монітор",    "АРМ головного бухгалтера","Samsung","S24F350FHI 24\"",   date(2022,3,1))
    add("Клавіатура", "АРМ головного бухгалтера","Logitech","K120",             date(2022,3,1))
    add("Миша",       "АРМ головного бухгалтера","Logitech","M100",             date(2022,3,1))
    add("ДБЖ",        "АРМ головного бухгалтера","APC",   "Back-UPS 650VA",     date(2022,3,1))
    add("МФУ",        "АРМ головного бухгалтера","HP",    "LaserJet Pro MFP M428fdw",date(2022,3,1), notes="Мережевий МФУ. Загальний для бухгалтерії")
    add("Монітор",    "АРМ бухгалтера 1",    "Samsung","S22F350FHI 22\"",       date(2019,6,12))
    add("Клавіатура", "АРМ бухгалтера 1",    "Logitech","K120",                 date(2019,6,12))
    add("Миша",       "АРМ бухгалтера 1",    "Logitech","M100",                 date(2019,6,12))
    add("Монітор",    "АРМ бухгалтера 2",    "Samsung","S22F350FHI 22\"",       date(2019,6,12))
    add("Клавіатура", "АРМ бухгалтера 2",    "Logitech","K120",                 date(2019,6,12))
    add("Миша",       "АРМ бухгалтера 2",    "Logitech","M100",                 date(2019,6,12))
    add("Монітор",    "АРМ економіста",      "Philips","242V8LA 24\"",           date(2021,9,3))
    add("Клавіатура", "АРМ економіста",      "HP",    "K1500",                  date(2021,9,3))
    add("Миша",       "АРМ економіста",      "HP",    "X1500",                  date(2021,9,3))

    # ── Каса ──────────────────────────────────────────────────────────────
    add("Монітор",    "АРМ касира",          "Philips","223V5LHSB2 21.5\"",     date(2023,4,17))
    add("Клавіатура", "АРМ касира",          "HP",    "K1500",                  date(2023,4,17))
    add("Миша",       "АРМ касира",          "HP",    "X1500",                  date(2023,4,17))
    add("Принтер",    "АРМ касира",          "Epson", "TM-T88VI",               date(2023,4,17), notes="Касовий принтер чеків ПРРО")

    # ── Архів бухгалтерії ─────────────────────────────────────────────────
    add("Монітор",    "АРМ архівного відділу","Acer", "V226HQL 22\"",           date(2017,11,22))
    add("Сканер",     "АРМ архівного відділу","Fujitsu","ScanSnap iX1500",      date(2020,5,10), notes="Документ-сканер для оцифровування архіву")
    add("МФУ",        "АРМ архівного відділу","Canon","MAXIFY MB2140",          date(2017,11,22), status="decommissioned", notes="Списано. Замінено МФУ HP у бухгалтерії")

    # ── Переговорна ───────────────────────────────────────────────────────
    add("Монітор",    "Презентаційне місце", "Dell",  "E2723H 27\"",            date(2022,10,5))
    add("Проєктор",   "Презентаційне місце", "Epson", "EB-X49",                 date(2022,10,5), notes="Підключено HDMI + VGA")
    add("Веб-камера", "Презентаційне місце", "Logitech","Rally Camera",         date(2022,10,5), notes="ВКС — відеоконференції")

    # ── Кадри ─────────────────────────────────────────────────────────────
    add("Монітор",    "АРМ начальника кадрів","Dell", "E2223HV 21.5\"",         date(2021,7,8))
    add("Клавіатура", "АРМ начальника кадрів","Logitech","K120",                date(2021,7,8))
    add("Миша",       "АРМ начальника кадрів","Logitech","M100",                date(2021,7,8))
    add("Монітор",    "АРМ інспектора кадрів","Dell", "E2223HV 21.5\"",         date(2021,7,8))
    add("Клавіатура", "АРМ інспектора кадрів","Logitech","K120",                date(2021,7,8))
    add("Миша",       "АРМ інспектора кадрів","Logitech","M100",                date(2021,7,8))
    add("МФУ",        "АРМ начальника кадрів","HP",   "LaserJet MFP M236sdw",   date(2021,7,8), notes="Мережевий МФУ. Загальний для відділу кадрів")
    add("Монітор",    "АРМ діловода кадрів",  "Acer","V226HQL 22\"",            date(2018,4,3))
    add("Клавіатура", "АРМ діловода кадрів",  "Genius","SlimStar 126",          date(2018,4,3))
    add("Миша",       "АРМ діловода кадрів",  "Genius","NX-7005",               date(2018,4,3))

    # ── Юридичний ─────────────────────────────────────────────────────────
    add("Монітор",    "АРМ начальника юрвідділу","HP","P27h G4 FHD",           date(2022,11,14))
    add("Клавіатура", "АРМ начальника юрвідділу","Logitech","MK710",           date(2022,11,14))
    add("Миша",       "АРМ начальника юрвідділу","Logitech","MX Master 3",     date(2022,11,14))
    add("Монітор",    "АРМ юриста 1",         "HP",    "V22v G5 FHD",          date(2020,2,28))
    add("Клавіатура", "АРМ юриста 1",         "Logitech","K120",               date(2020,2,28))
    add("Миша",       "АРМ юриста 1",         "Logitech","M100",               date(2020,2,28))
    add("МФУ",        "АРМ юриста 1",         "Xerox","WorkCentre 6515",       date(2020,2,28), notes="Кольоровий лазерний МФУ")

    # ── Документообіг ─────────────────────────────────────────────────────
    add("Монітор",    "АРМ начальника канцелярії","HP","V24i FHD",             date(2022,6,20))
    add("Клавіатура", "АРМ начальника канцелярії","Logitech","K120",           date(2022,6,20))
    add("Миша",       "АРМ начальника канцелярії","Logitech","M100",           date(2022,6,20))
    add("МФУ",        "АРМ начальника канцелярії","Kyocera","ECOSYS M2735dw",  date(2022,6,20), notes="МФУ канцелярії. A4, мережевий, дуплекс")
    add("Монітор",    "АРМ діловода",          "HP",    "V24i FHD",            date(2022,6,20))
    add("Клавіатура", "АРМ діловода",          "Logitech","K120",              date(2022,6,20))
    add("Миша",       "АРМ діловода",          "Logitech","M100",              date(2022,6,20))
    add("Сканер",     "АРМ діловода",          "Canon", "DR-C225 II",          date(2022,6,20), notes="Потоковий документ-сканер")
    add("Монітор",    "АРМ архіваріуса",       "HP",    "P24h G4",             date(2023,9,12))
    add("Клавіатура", "АРМ архіваріуса",       "HP",    "K1500",               date(2023,9,12))
    add("Миша",       "АРМ архіваріуса",       "HP",    "X1500",               date(2023,9,12))

    # ── Адміністрація ─────────────────────────────────────────────────────
    add("Монітор",    "АРМ секретаря",         "Dell",  "P2423D 24\"",         date(2023,1,10))
    add("Клавіатура", "АРМ секретаря",         "Logitech","MK710",             date(2023,1,10))
    add("Миша",       "АРМ секретаря",         "Logitech","MX Master 3",       date(2023,1,10))
    add("МФУ",        "АРМ секретаря",         "HP",    "Color LaserJet Pro MFP M283fdw",date(2023,1,10), notes="Загальний МФУ адмінкорпусу")
    add("ДБЖ",        "АРМ секретаря",         "APC",   "Back-UPS 900VA",      date(2023,1,10))
    add("Клавіатура", "АРМ директора",         "Apple", "Magic Keyboard",      date(2024,2,1))
    add("Миша",       "АРМ директора",         "Apple", "Magic Mouse",         date(2024,2,1))
    add("Монітор",    "АРМ заступника директора","Dell","P2723D 27\"",         date(2022,9,5))
    add("Клавіатура", "АРМ заступника директора","Logitech","MK710",           date(2022,9,5))
    add("Миша",       "АРМ заступника директора","Logitech","MX Master 3",     date(2022,9,5))

    # ── PR-відділ ─────────────────────────────────────────────────────────
    add("Клавіатура", "АРМ начальника PR",     "Apple", "Magic Keyboard",      date(2022,6,1))
    add("Миша",       "АРМ начальника PR",     "Apple", "Magic Mouse",         date(2022,6,1))
    add("Монітор",    "АРМ прес-секретаря",    "LG",    "27UP850N-W 4K",       date(2023,3,15))
    add("Клавіатура", "АРМ прес-секретаря",    "Logitech","K120",              date(2023,3,15))
    add("Миша",       "АРМ прес-секретаря",    "Logitech","M100",              date(2023,3,15))
    add("Монітор",    "АРМ контент-менеджера", "Dell",  "U3223QE 4K 32\"",    date(2021,4,20), notes="Монітор для відеомонтажу. sRGB 100%")
    add("Монітор",    "АРМ контент-менеджера", "Dell",  "U2722D 27\"",         date(2021,4,20), notes="Другий монітор")
    add("Клавіатура", "АРМ контент-менеджера", "Logitech","MX Keys",           date(2021,4,20))
    add("Миша",       "АРМ контент-менеджера", "Logitech","MX Master 3",       date(2021,4,20))

    # ── Зала засідань ─────────────────────────────────────────────────────
    add("Проєктор",   "Ноутбук зали засідань","Panasonic","PT-VMZ50",          date(2022,12,1), notes="Лазерний проєктор WUXGA. Підключення HDMI")
    add("Веб-камера", "Ноутбук зали засідань","Logitech","Rally Bar",          date(2022,12,1), notes="ВКС-система. Microsoft Teams Rooms")

    # ── Закупівлі ─────────────────────────────────────────────────────────
    add("Монітор",    "АРМ начальника закупівель","Dell","P2723D 27\"",        date(2023,2,28))
    add("Монітор",    "АРМ начальника закупівель","Dell","P2723D 27\"",        date(2023,2,28), notes="Другий монітор")
    add("Клавіатура", "АРМ начальника закупівель","Logitech","MK710",          date(2023,2,28))
    add("Миша",       "АРМ начальника закупівель","Logitech","MX Master 3",    date(2023,2,28))
    add("Монітор",    "АРМ фахівця закупівель 1","HP","P24h G4",              date(2023,2,28))
    add("Клавіатура", "АРМ фахівця закупівель 1","Logitech","K120",           date(2023,2,28))
    add("Миша",       "АРМ фахівця закупівель 1","Logitech","M100",           date(2023,2,28))
    add("Монітор",    "АРМ фахівця закупівель 2","HP","P24h G4",              date(2023,2,28))
    add("Клавіатура", "АРМ фахівця закупівель 2","Logitech","K120",           date(2023,2,28))
    add("Миша",       "АРМ фахівця закупівель 2","Logitech","M100",           date(2023,2,28))

    # ── Навчальний клас ───────────────────────────────────────────────────
    add("Проєктор",   "Місце викладача",       "Epson","EB-X51",              date(2019,9,1), notes="Навчальний проєктор")
    add("Монітор",    "Навчальне місце №1",    "Acer", "V246HL 24\"",         date(2021,10,1))
    add("Монітор",    "Навчальне місце №2",    "Acer", "V246HL 24\"",         date(2021,10,1))
    add("Монітор",    "Навчальне місце №3",    "Acer", "V246HL 24\"",         date(2021,10,1), status="repair", notes="Монітор у ремонті разом з ноутбуком")

    return entries


def build_status_logs(session, users: dict, computers: dict, peripherals: dict) -> list[dict]:
    """Реалістична хронологія змін статусів."""
    admin_id    = users["admin"].id
    ivanova_id  = users["ivanova"].id
    kovalenko_id= users["kovalenko"].id

    def c(inv): return computers.get(inv)
    def p(inv): return peripherals.get(inv)

    logs = []

    def log(device, old_s, new_s, changed_by, changed_at, comment=""):
        if device is None: return
        dtype = "computer" if isinstance(device, Computer) else "peripheral"
        logs.append(dict(
            device_type=dtype, device_id=device.id,
            old_status=old_s, new_status=new_s,
            changed_by=changed_by,
            changed_at=changed_at, comment=comment,
        ))

    # ПК техніка ремонт → активний (2023)
    log(c("ПК-2020-001"), "active", "repair",  kovalenko_id, datetime(2023,11,20,9,0),  "Виявлена несправність відеокарти. Відправлено в сервіс")
    log(c("ПК-2020-001"), "repair", "active",  kovalenko_id, datetime(2023,12,5,14,30), "Повернено з ремонту. Відеокарту замінено")
    log(c("ПК-2020-001"), "active", "repair",  kovalenko_id, datetime(2024,4,12,10,0),  "Повторна несправність. Відправлено в сервіс знову")

    # Ноутбук юридичного — списання
    log(c("ПК-2020-003"), "active",   "repair",        admin_id, datetime(2024,3,1,11,0),  "Залито рідиною. Не вмикається")
    log(c("ПК-2020-003"), "repair",   "decommissioned",admin_id, datetime(2024,3,15,9,0), "Акт списання №12 від 15.03.2024. Відновленню не підлягає")

    # Старий ПК архіваріуса — переведено на зберігання
    log(c("ПК-2016-001"), "active", "storage", admin_id, datetime(2023,9,15,16,0), "Замінено моноблоком МН-2023-001. Переведено на склад")

    # Навчальний ноутбук — ремонт
    log(c("НБ-2021-003"), "active", "repair", ivanova_id, datetime(2024,4,20,9,30), "Ноутбук не заряджається. Несправний акумулятор")

    # Старий склад ПК
    log(c("ПК-2016-002"), "active", "storage", admin_id, datetime(2022,1,10,10,0), "Виведено з експлуатації. Направлено на склад очікування списання")

    # Ноутбук на складі — в ремонт
    log(c("НБ-2018-001"), "storage", "repair", kovalenko_id, datetime(2024,4,3,11,0), "Ноутбук зі складу відправлено до сервісу для оцінки можливості відновлення")

    # МФУ архіву — списання
    mfu_arch = None
    for k, v in peripherals.items():
        if "МФУ" in k and "Canon" in str(getattr(v, "brand", "")):
            # Шукаємо Canon MAXIFY в архіві
            pass
    # Шукаємо списаний МФУ
    for inv, pobj in peripherals.items():
        if "МФУ" in inv and getattr(pobj, "status", "") == "decommissioned":
            log(pobj, "active",  "repair",        admin_id, datetime(2023,5,10,9,0),  "МФУ не друкує. Відправлено в сервіс")
            log(pobj, "repair",  "decommissioned",admin_id, datetime(2023,6,5,14,0),  "Ремонт економічно недоцільний. Списано згідно акта №8 від 05.06.2023")
            break

    # Монітор техніка — ремонт
    for inv, pobj in peripherals.items():
        if "МОН" in inv and getattr(pobj, "status", "") == "repair":
            log(pobj, "active", "repair", kovalenko_id, datetime(2024,4,12,10,0), "Монітор відправлено в сервіс разом з ПК техніка")
            break

    # Монітор навчального класу — ремонт
    cnt = 0
    for inv, pobj in peripherals.items():
        if "МОН" in inv and getattr(pobj, "status", "") == "repair":
            if cnt == 0: cnt += 1; continue  # перший вже оброблений
            log(pobj, "active", "repair", ivanova_id, datetime(2024,4,20,9,30), "Монітор не вмикається. Разом з ноутбуком НБ-2021-003")
            break

    # Кілька «рутинних» змін оператором Іванової
    log(c("ПК-2019-001"), "active", "repair", ivanova_id, datetime(2023,7,3,14,0),  "Заміна термопасти. Перегрів")
    log(c("ПК-2019-001"), "repair", "active", ivanova_id, datetime(2023,7,5,17,0),  "Повернено після профілактики")
    log(c("ПК-2019-002"), "active", "repair", ivanova_id, datetime(2023,9,15,10,0), "Профілактика. Чистка від пилу")
    log(c("ПК-2019-002"), "repair", "active", ivanova_id, datetime(2023,9,16,16,0), "Після профілактики повернено на місце")

    # Коваленко — робота з серверами
    log(c("СРВ-2021-002"), "active", "repair", kovalenko_id, datetime(2023,3,10,8,0),  "Плановий сервісний огляд. Тимчасово виведено")
    log(c("СРВ-2021-002"), "repair", "active", kovalenko_id, datetime(2023,3,11,18,0), "Огляд завершено. Замінено 2 жорстких диски в масиві")

    # Адмін — закупівля нового обладнання → активація
    log(c("ПК-2023-004"), "storage", "active", admin_id, datetime(2023,3,5,9,0),  "Отримано зі складу. Встановлено на робочому місці начальника закупівель")
    log(c("ПК-2023-005"), "storage", "active", admin_id, datetime(2023,3,5,9,30), "Встановлено на АРМ фахівця закупівель 1")
    log(c("ПК-2023-006"), "storage", "active", admin_id, datetime(2023,3,5,10,0), "Встановлено на АРМ фахівця закупівель 2")

    # Директорський MacBook — активація
    log(c("НБ-2024-001"), "storage", "active", admin_id, datetime(2024,2,5,14,0), "Нове обладнання. Введено в експлуатацію. Налаштовано Apple ID організації")

    return logs


# ─────────────────────────────────────────────────────────
# Основна функція
# ─────────────────────────────────────────────────────────

def seed(clear: bool = False):
    random.seed(42)  # Відтворювані рандомні дані

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        if clear:
            print("🗑  Очищення бази даних...")
            for model in [StatusLog, Peripheral, Computer, Workplace,
                          Employee, Room, ComputerType, PeripheralType, User]:
                session.query(model).delete()
            session.commit()
            print("   Очищено.")

        # ── 1. Користувачі ────────────────────────────────────────────────
        print("👤 Створення користувачів...")
        user_objs = {}
        for u in USERS:
            exists = session.query(User).filter_by(username=u["username"]).first()
            if not exists:
                obj = User(
                    username=u["username"],
                    password_hash=hashed(u["password"]),
                    role=u["role"],
                    full_name=u["full_name"],
                )
                session.add(obj)
                session.flush()
                user_objs[u["username"]] = obj
                print(f"   + {u['username']} ({u['role']})")
            else:
                user_objs[u["username"]] = exists
                print(f"   = {u['username']} вже існує")
        session.commit()

        # ── 2. Типи комп'ютерів ───────────────────────────────────────────
        print("\n🖥  Типи комп'ютерів...")
        ct_objs = {}
        for name in COMPUTER_TYPES:
            obj = session.query(ComputerType).filter_by(name=name).first()
            if not obj:
                obj = ComputerType(name=name)
                session.add(obj); session.flush()
                print(f"   + {name}")
            ct_objs[name] = obj
        session.commit()

        # ── 3. Типи периферії ─────────────────────────────────────────────
        print("\n🖨  Типи периферії...")
        pt_objs = {}
        for name in PERIPHERAL_TYPES:
            obj = session.query(PeripheralType).filter_by(name=name).first()
            if not obj:
                obj = PeripheralType(name=name)
                session.add(obj); session.flush()
                print(f"   + {name}")
            pt_objs[name] = obj
        session.commit()

        # ── 4. Приміщення ─────────────────────────────────────────────────
        print("\n🏢 Приміщення...")
        room_objs = {}
        for r in ROOMS:
            obj = session.query(Room).filter_by(number=r["number"]).first()
            if not obj:
                obj = Room(**r); session.add(obj); session.flush()
                print(f"   + {r['number']} {r['name']}")
            room_objs[r["number"]] = obj
        session.commit()

        # ── 5. Співробітники ──────────────────────────────────────────────
        print("\n👩‍💼 Співробітники...")
        emp_objs = {}
        for e in EMPLOYEES:
            obj = session.query(Employee).filter_by(email=e["email"]).first()
            if not obj:
                obj = Employee(**e); session.add(obj); session.flush()
                print(f"   + {e['full_name']}")
            emp_objs[e["full_name"]] = obj
        session.commit()

        # ── 6. Робочі місця ───────────────────────────────────────────────
        print("\n🪑 Робочі місця...")
        wp_objs = {}
        for w in build_workplaces(room_objs, emp_objs):
            obj = session.query(Workplace).filter_by(
                room_id=w["room_id"], name=w["name"]
            ).first()
            if not obj:
                obj = Workplace(**w); session.add(obj); session.flush()
                print(f"   + {w['name']}")
            wp_objs[w["name"]] = obj
        session.commit()

        # ── 7. Комп'ютери ─────────────────────────────────────────────────
        print("\n💻 Комп'ютери...")
        comp_objs = {}
        for c in build_computers(ct_objs, wp_objs):
            obj = session.query(Computer).filter_by(
                inventory_number=c["inventory_number"]
            ).first()
            if not obj:
                obj = Computer(**c); session.add(obj); session.flush()
                print(f"   + {c['inventory_number']} {c['brand']} {c['model']} [{c['status']}]")
            comp_objs[c["inventory_number"]] = obj
        session.commit()

        # ── 8. Периферія ──────────────────────────────────────────────────
        print("\n🖱  Периферія...")
        periph_objs = {}
        for p in build_peripherals(pt_objs, wp_objs, comp_objs):
            obj = session.query(Peripheral).filter_by(
                inventory_number=p["inventory_number"]
            ).first()
            if not obj:
                obj = Peripheral(**p); session.add(obj); session.flush()
                print(f"   + {p['inventory_number']} {p['brand']} {p['model']} [{p['status']}]")
            periph_objs[p["inventory_number"]] = obj
        session.commit()

        # ── 9. Аудит-журнал ───────────────────────────────────────────────
        print("\n📋 Аудит-журнал...")
        existing_logs = session.query(StatusLog).count()
        if existing_logs == 0:
            for log_data in build_status_logs(session, user_objs, comp_objs, periph_objs):
                session.add(StatusLog(**log_data))
            session.commit()
            total_logs = session.query(StatusLog).count()
            print(f"   Додано {total_logs} записів журналу")
        else:
            print(f"   Журнал вже містить {existing_logs} записів, пропущено")

        # ── Підсумок ──────────────────────────────────────────────────────
        print("\n" + "═" * 52)
        print("✅ НАПОВНЕННЯ ЗАВЕРШЕНО")
        print("═" * 52)
        for model, label in [
            (User,          "Користувачів"),
            (ComputerType,  "Типів комп'ютерів"),
            (PeripheralType,"Типів периферії"),
            (Room,          "Приміщень"),
            (Employee,      "Співробітників"),
            (Workplace,     "Робочих місць"),
            (Computer,      "Комп'ютерів"),
            (Peripheral,    "Одиниць периферії"),
            (StatusLog,     "Записів аудит-журналу"),
        ]:
            count = session.query(model).count()
            print(f"   {label:<28} {count:>4}")
        print("═" * 52)
        print("\nОблікові дані для входу:")
        print("  admin    / Admin@2024   (адміністратор)")
        print("  ivanova  / Oper@2024    (оператор)")
        print("  kovalenko/ Oper@2024    (оператор)")


if __name__ == "__main__":
    clear_mode = "--clear" in sys.argv
    if clear_mode:
        print("⚠  Режим --clear: всі дані будуть видалені і заповнені заново\n")
    seed(clear=clear_mode)