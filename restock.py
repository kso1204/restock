import requests
from bs4 import BeautifulSoup
import time
import json
import threading
import os
from dotenv import load_dotenv
import logging
import sys

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(filename='restock_monitoring.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S',
                    encoding='utf-8')
                    

logging.info("재고 모니터링 시작")

load_dotenv()
# Webhook URL을 여기에 입력합니다.
webhook_url = os.getenv('SLACK_WEBHOOK_URL')

# 슬랙 메시지 전송 함수 (Slack Webhook URL필요)

class StockMonitor:
    def __init__(self, url, option_text, slack_message):
        self.url = url
        self.option_text = option_text
        self.slack_message = slack_message
        self.last_slack_time = 0

    def send_slack_message(self, message):
        send_message = {'text': message}
        response = requests.post(
            webhook_url,
            data=json.dumps(send_message),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            print('메시지가 성공적으로 전송되었습니다.')
        else:
            print(f'메시지 전송에 실패했습니다. 상태 코드: {response.status_code}')

    def check_stock(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            options_div = soup.find('div', class_=['item_add_option_box'])
            if options_div:
                select = options_div.find('select', class_='chosen-select')
                if select:
                    options = select.find_all('option')
                    for index, option in enumerate(options):
                        value = option.get('value')
                        text = option.get_text(strip=True)
                        logging.info(f"Option {index}: Text: {text}, Value: {value}")
                        if self.option_text in text and 'disabled' not in option.attrs:
                            print(f"{self.option_text} is available.")
                            return True
                        else:
                            print(f"{self.option_text} is not available.")
                else:
                    print("Select element with class 'chosen-select' not found.")
            else:
                print("Div with class 'item_add_option_box' not found.")
        return False
    
    def monitor_stock(self):
        while True:
            logging.info(f"{self.option_text} 재고 확인 중")
            in_stock = self.check_stock()
            current_time = time.time()
            if in_stock:
                self.send_slack_message(f"{self.option_text} 재고가 다시 들어왔습니다!")
                break
            else:
                logging.info(f"{self.option_text} 재고 없음, 다시 확인 중...")
                if current_time - self.last_slack_time >= 10800:
                    self.send_slack_message(f"{self.option_text} 모니터링 중입니다. 아직 재고가 없습니다.")
                    self.last_slack_time = current_time
            time.sleep(60)

class StockMonitor2(StockMonitor):
    def check_stock(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            sold_out_button = soup.find('button', class_='btn_add_soldout')
            if sold_out_button is not None:
                if 'disabled' in sold_out_button.attrs:
                    print("상품은 품절입니다.")
                    logging.info(f"{self.option_text} 품절 상태")
                    return False
                else:
                    print(f"{self.option_text} 구매 가능한지 확인해보세요")
                    logging.info(f"{self.option_text} 구매 가능 상태")
                    return True
            else:
                print(f"{self.option_text} 상품의 구매 여부를 확인할 수 없는 상황인데, 구매 가능하지 않을까?")
                logging.info(f"{self.option_text} 품절 여부 확인 실패")
                return True
        return False

# 실행
if __name__ == '__main__':
    monitors = [
        StockMonitor('http://fnnk.co.kr/goods/goods_view.php?goodsNo=1000000938', '화이트워시(S)', '화이트워시(S) 재고가 다시 들어왔습니다!'),
        StockMonitor2('http://fnnk.co.kr/goods/goods_view.php?goodsNo=1000000935', '뉴본 신생아 세트', '뉴본 신생아 세트 재고가 다시 들어왔습니다!'),
        StockMonitor('http://fnnk.co.kr/goods/goods_view.php?goodsNo=1000000795', '트립트랩 베이비세트 화이트(S)', '트립트랩 베이비세트 재고가 다시 들어왔습니다!')
    ]

    threads = []
    for monitor in monitors:
        thread = threading.Thread(target=monitor.monitor_stock)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("모든 재고 확인이 완료되었습니다.")