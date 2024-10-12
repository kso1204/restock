import requests
from bs4 import BeautifulSoup
import time
import json
import threading
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(filename='restock_monitoring.log', level=logging.INFO)
logging.info("재고 모니터링 시작")

load_dotenv()

# Webhook URL을 여기에 입력합니다.
webhook_url = os.getenv('SLACK_WEBHOOK_URL')

# 슬랙 메시지 전송 함수 (Slack Webhook URL필요)
def send_slack_message(message):
    
    send_message = {
        'text': message
    }
    
    response = requests.post(
        webhook_url, 
        data=json.dumps(send_message), 
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print('메시지가 성공적으로 전송되었습니다.')
    else:
        print(f'메시지 전송에 실패했습니다. 상태 코드: {response.status_code}')

# 식탁의자 화이트워시 페이지 크롤링 함수
def check_stock():
    url = 'http://fnnk.co.kr/goods/goods_view.php?goodsNo=1000000938'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # "화이트워시(S)" 옵션 찾기
        options_div = soup.find('div', class_=['item_add_option_box'])
        select = options_div.find('select', class_='chosen-select')
        options = select.find_all('option')
        
        # 각 옵션을 순회하며 품절 여부를 확인
        for option in options:
            option_text = option.text.strip()
            if '화이트워시(S)' in option_text and 'disabled' not in option.attrs:
                print("화이트워시(S) is available.")
                return True
            
    return False  # 품절 상태


# 뉴본 신생아 세트 재고 페이지 크롤링 함수
def check_stock2():
    url = 'http://fnnk.co.kr/goods/goods_view.php?goodsNo=1000000935'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 뉴본 구매불가 해제 찾기
        sold_out_button = soup.find('button', class_='btn_add_soldout')
        
        if sold_out_button is not None:  # sold_out_button이 None이 아닐 때만 체크
            if 'disabled' in sold_out_button.attrs:
                print("상품은 품절입니다.")
                return False  # 품절 상태
            else:
                print("뉴본 신생아 세트 구매 가능한지 확인해보세요")
                return True  # 구매 가능 상태
        else:
            print("뉴본 신생아 세트 상품의 구매 여부를 확인할 수 없는 상황인데, 구매 가능하지 않을까?")
            return True  # 품절 여부 확인 실패
        
    return False  # 품절 상태

def monitor_stock1():
    while True:
        logging.info("화이트워시 재고 확인 중")
        in_stock = check_stock()
        if in_stock:
            send_slack_message("화이트워시(S) 재고가 다시 들어왔습니다!")
            break  # 조건에 맞으면 루프 종료
        else:
            print("화이트워시(S) 재고 없음, 다시 확인 중...")
        time.sleep(60)  # 60초 후 다시 확인

def monitor_stock2():
    while True:
        logging.info("뉴본 재고 확인중")
        in_stock = check_stock2()
        if in_stock:
            send_slack_message("뉴본 신생아 세트 재고가 다시 들어왔습니다!")
            break  # 조건에 맞으면 루프 종료
        else:
            print("뉴본 신생아 세트 재고 없음, 다시 확인 중...")
        time.sleep(60)  # 60초 후 다시 확인

# 실행
if __name__ == '__main__':
    
    # 각 모니터링 함수를 스레드로 실행
    thread1 = threading.Thread(target=monitor_stock1)
    thread2 = threading.Thread(target=monitor_stock2)

    thread1.start()  # 화이트워시(S) 재고 확인 시작
    thread2.start()  # 뉴본 신생아 세트 재고 확인 시작

    thread1.join()  # 스레드1 종료 대기
    thread2.join()  # 스레드2 종료 대기
    
    
    print("모든 재고 확인이 완료되었습니다.")  # 두 스레드가 종료된 후 메시지 출력
