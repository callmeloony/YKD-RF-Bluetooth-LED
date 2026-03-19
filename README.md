# 💡 YKD-RF Bluetooth LED Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg?style=for-the-badge&logo=home-assistant)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

Ця користувацька інтеграція дозволяє підключити бюджетні Bluetooth одноколірні LED-стрічки (моделі **YKD-RF** та аналоги) безпосередньо до вашого Home Assistant. Жодних хмарних сервісів чи сторонніх хабів — повний локальний контроль.

---

## ✨ Основні можливості

| Функція | Опис |
| :--- | :--- |
| **🚀 Fast Response** | Технологія **Keep-Alive** утримує сесію відкритою 60 секунд. Команди виконуються миттєво без повторного "рукостискання". |
| **🔆 Brightness** | Плавне регулювання яскравості від 1% до 100% за допомогою прямих HEX-команд. |
| **🎭 Effects** | Підтримка режимів: `Strobe`, `Fade`, `Jump`, `Slow Flash`. Повернення до статичного світла через пункт **"None"**. |
| **🔋 Energy Saving** | Автоматичне розірвання з'єднання після 1 хв бездіяльності для звільнення Bluetooth-адаптера. |
| **🔒 100% Local** | Робота без інтернету через бібліотеку `Bleak`. Ваші дані не залишають локальної мережі. |

---

## 🛠 Технічні деталі
* **Протокол:** Bluetooth Low Energy (BLE).
* **UUID Характеристики:** `0000ffd9-0000-1000-8000-00805f9b34fb`.
* **Сумісність:** Тестовано на контролерах з MAC-префіксом `02:05:11`.

---

## 🚀 Встановлення

### Спосіб 1: Через HACS (Рекомендовано)
1. Відкрийте **HACS** у вашому Home Assistant.
2. Натисніть на три крапки (**⋮**) у верхньому правому куті -> **Custom repositories**.
3. Вставте посилання: `https://github.com/callmeloony/YKD-RF-Bluetooth-LED`
4. Оберіть категорію **Integration**.
5. Натисніть **Add**, знайдіть **YKD-RF Bluetooth LED** та натисніть **Download**.
6. **Перезавантажте** Home Assistant.

### Спосіб 2: Вручну
1. Завантажте цей репозиторій.
2. Скопіюйте папку `ykd_led` у директорію `/config/custom_components/`.
3. **Перезавантажте** Home Assistant.

---

## ⚙️ Налаштування

1. Перейдіть у **Налаштування** -> **Пристрої та служби**.
2. Натисніть **Додати інтеграцію** -> пошук за назвою **YKD-RF Bluetooth LED**.
3. Вкажіть назву пристрою та його **MAC-адресу**.
4. Насолоджуйтесь миттєвим керуванням! ⚡



---
*Розроблено спеціально для ентузіастів розумного дому. Зроблено в Україні 🇺🇦*
