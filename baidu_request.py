import requests

def main():
    url = 'https://www.baidu.com'
    print(f'正在请求: {url}')

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        print(f'状态码: {response.status_code}')
        print(f'编码: {response.encoding}')
        print('响应头:')
        for key, value in response.headers.items():
            print(f'  {key}: {value}')

        print(f'\n响应内容啿度: {len(response.text)} 字符')
        print('\n响应内容前500字符:')
        print(response.text[:500])

    except requests.exceptions.Timeout:
        print('请求超时，请检查网络连接')
    except requests.exceptions.ConnectionError:
        print('连接错误，请检查网络是否可达')
    except requests.exceptions.RequestException as e:
        print(f'请求异常: {e}')

if __name__ == '__main__':
    main()