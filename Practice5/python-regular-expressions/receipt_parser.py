import re
import json

# читаем файл
with open("raw.txt", "r", encoding="utf-8") as f:
    text = f.read()
# 1. извлечь названия товаров
products = re.findall(r'\d+\.\n(.+)', text)

# 2. извлечь цены товаров (последнее число после количества)
prices_raw = re.findall(r'\n([\d\s]+,\d{2})\nСтоимость', text)

# преобразуем цены в числа
prices = [float(p.replace(" ", "").replace(",", ".")) for p in prices_raw]

# 3. посчитать сумму
total = sum(prices)

# 4. найти дату и время
datetime_match = re.search(r'\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2}:\d{2}', text)
datetime = datetime_match.group() if datetime_match else None

# 5. найти способ оплаты
payment_match = re.search(r'Банковская карта', text)
payment_method = payment_match.group() if payment_match else None

# 6. сделать структурированный результат
result = {
    "products": products,
    "prices": prices,
    "total_amount": total,
    "date_time": datetime,
    "payment_method": payment_method
}

# вывод JSON
print(json.dumps(result, indent=4, ensure_ascii=False))