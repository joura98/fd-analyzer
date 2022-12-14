
import json
import os
import consul
import time
import logging
import requests

CFG = {}

CONSUL_CLIENT = None

CONFIG_FILE = '/home/config/config.json'


def load_local_cfg(path=CONFIG_FILE):
    global CFG
    if os.path.exists(path):
        with open(path, "r") as f:
            CFG = json.load(f)
    else:
        raise RuntimeError(f"Not find config file,the path is {path}")


def get_consul_client(host):
    if host:
        c = consul.Consul(host=host)
    else:
        c = consul.Consul()

    while True:
        try:
            c.catalog.nodes()
        except :
            logging.critical("Connect consul error, retry: ", exc_info=True)
            time.sleep(10)
            continue
        else:
            logging.info('connect consul OK')
            break

    return c


def update_consul_client():
    global CONSUL_CLIENT
    CONSUL_CLIENT = consul.Consul(host=os.getenv('CONSULSRV_IP', None))
    return None


def get_elasticsearch_address():
    index, ip_data = CONSUL_CLIENT.kv.get('elk/esIP')
    index, port_data = CONSUL_CLIENT.kv.get('elk/esPort')
    if ip_data and port_data:
        return ip_data.get('Value', b'').decode(), port_data.get('Value', b'').decode()
    else:
        return None, None


def get_kafka_address():
    index, ip_data = CONSUL_CLIENT.kv.get('kafka/broker_ip')
    index, port_data = CONSUL_CLIENT.kv.get('kafka/broker_port')
    if ip_data and port_data:
        return ip_data.get('Value', b'').decode(), port_data.get('Value', b'').decode()
    else:
        return None, None

def download_config():
    # 国家电网 福建电力 数据源
    # 先检查服务端已导出 Navicat mongodb 数据库，需本地手动导入
    # http://pmos.fj.sgcc.com.cn:8081
    url = "http://58.22.2.49:8081/upload/navicat_config.ncx"
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.error(f'download mongo config error, status code {resp.status_code}')
        return False
    save_file = '/home/data/mongo.ncx'
    with open(save_file, 'w') as f:
        f.write(resp.text)
    logging.info(f'downloaded database config, you can import it manually')


def cfg_init(path=CONFIG_FILE):

    global CONSUL_CLIENT
    download_config()
    load_local_cfg(path)

    CFG['host_ip'] = os.getenv('HOST_IP', None)
    if CFG['host_ip'] is None:
        raise RuntimeError(f"Not find environment: 'HOST_IP' ")

    consulsrv_ip = os.getenv('CONSULSRV_IP', None)
    if not consulsrv_ip:
        raise RuntimeError(f" CONSULSRV_IP not exist")

    CONSUL_CLIENT = get_consul_client(consulsrv_ip)
