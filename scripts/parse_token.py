# Author: SANJAY KR
import sys
import json

def extract_token(json_str):
    try:
        data = json.loads(json_str)
        return data.get('access_token', '')
    except json.JSONDecodeError:
        return ''

if __name__ == '__main__':
    json_str = sys.stdin.read()
    print(extract_token(json_str))
