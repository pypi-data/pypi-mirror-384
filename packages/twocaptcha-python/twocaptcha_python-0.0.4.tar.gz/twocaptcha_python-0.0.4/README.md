[![PyPI version](https://badge.fury.io/py/twocaptcha-python.svg)](https://badge.fury.io/py/twocaptcha-python)
[![Python Versions](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue)](https://pypi.org/project/twocaptcha-python/)
[![Downloads](https://static.pepy.tech/badge/twocaptcha-python)](https://pepy.tech/project/twocaptcha-python)
[![Downloads](https://static.pepy.tech/badge/twocaptcha-python/month)](https://pepy.tech/project/twocaptcha-python)
[![Downloads](https://static.pepy.tech/badge/twocaptcha-python/week)](https://pepy.tech/project/twocaptcha-python)

# TwoCaptcha Python Library

A simple 2captcha Python client for the [2captcha solving service](https://2captcha.com/api-docs) - Bypass reCAPTCHA, Cloudflare Turnstile, FunCaptcha, GeeTest and solve any other captchas.

## Installation

- Using pip

```bash
pip install twocaptcha-python -U
```

- Using uv

```bash
uv add twocaptcha-python -U
```

**Note**: You can use any task configuration directly from the [2Captcha API documentation](https://2captcha.com/api-docs). Just copy the task object from their examples and pass it to `solve_captcha()`.

## Supported Captcha Types

- **Normal CAPTCHA** - `ImageToTextTask`
- **reCAPTCHA V2** - `RecaptchaV2TaskProxyless`, `RecaptchaV2Task`
- **reCAPTCHA V3** - `RecaptchaV3TaskProxyless`, `RecaptchaV3Task`
- **reCAPTCHA Enterprise** - `RecaptchaV2EnterpriseTaskProxyless`, `RecaptchaV3EnterpriseTaskProxyless`
- **Arkose Labs CAPTCHA** - `FunCaptchaTaskProxyless`, `FunCaptchaTask`
- **GeeTest CAPTCHA** - `GeeTestTaskProxyless`, `GeeTestTask`
- **Cloudflare Turnstile** - `TurnstileTaskProxyless`, `TurnstileTask`
- **Capy Puzzle CAPTCHA** - `CapyTaskProxyless`, `CapyTask`
- **Lemin CAPTCHA** - `LeminTaskProxyless`, `LeminTask`
- **Amazon CAPTCHA** - `AmazonTaskProxyless`, `AmazonTask`
- **Text CAPTCHA** - `TextCaptchaTask`
- **Rotate CAPTCHA** - `RotateTask`
- **Click CAPTCHA** - `CoordinatesTask`
- **Draw Around** - `DrawAroundTask`
- **Grid CAPTCHA** - `GridTask`
- **Audio CAPTCHA** - `AudioTask`
- **MTCaptcha** - `MtCaptchaTaskProxyless`, `MtCaptchaTask`
- **DataDome CAPTCHA** - `DataDomeTaskProxyless`, `DataDomeTask`
- **Friendly Captcha** - `FriendlyCaptchaTaskProxyless`, `FriendlyCaptchaTask`
- **Bounding box** - `BoundingBoxTask`
- **Cutcaptcha** - `CutCaptchaTaskProxyless`, `CutCaptchaTask`
- **atbCAPTCHA** - `AtbCaptchaTaskProxyless`, `AtbCaptchaTask`
- **Tencent** - `TencentTaskProxyless`, `TencentTask`
- **Prosopo Procaptcha** - `ProsopoTaskProxyless`, `ProsopoTask`
- **CaptchaFox** - `CaptchaFoxTaskProxyless`, `CaptchaFoxTask`
- **VK Captcha** - `VKTaskProxyless`, `VKTask`
- **Temu Captcha** - `TemuTaskProxyless`, `TemuTask`

## Usage Examples

### Synchronous Client

#### Auto solve captcha sync

```python
from TwoCaptcha import SyncTwoCaptcha, TwoCaptchaError

client = SyncTwoCaptcha(api_key="YOUR_API_KEY")

def auto_solve_captcha():
    """Auto solve captcha using 2captcha api."""
    try:
        task = {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": "https://2captcha.com/demo/recaptcha-v2",
            "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
        }
        balance = client.balance()
        print(f"Balance: {balance}")
        result = client.solve_captcha(task)
        print(f"Result: {result}")

    except TwoCaptchaError as e:
        print(f"TwoCaptcha Error: {e}")
auto_solve_captcha()
```

#### Manual solve captcha sync

```python
from TwoCaptcha import SyncTwoCaptcha, TwoCaptchaError

client = SyncTwoCaptcha(api_key="YOUR_API_KEY")

def manual_solve_captcha(task_id=None):
    """Manual solve captcha using 2captcha api."""
    try:
        task = {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": "https://2captcha.com/demo/recaptcha-v2",
            "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
        }

        create_result = client.create_task(task)
        task_id = create_result["taskId"]
        print(f"Created task with ID: {task_id}")

        task_result = client.get_task_result(task_id)
        print(f"Task result: {task_result}")

    except TwoCaptchaError as e:
        print(f"TwoCaptcha Error: {e}")

manual_solve_captcha()
```

### Asynchronous Client

#### Auto solve captcha Async

```python
from TwoCaptcha import AsyncTwoCaptcha, TwoCaptchaError
import asyncio

async def auto_solve_captcha():
    """Auto solve captcha using 2captcha api."""
    client = AsyncTwoCaptcha(api_key="YOUR_API_KEY")
    try:
        task = {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": "https://2captcha.com/demo/recaptcha-v2",
            "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
        }
        balance = await client.balance()
        print(f"Balance: {balance}")
        result = await client.solve_captcha(task)
        print(f"Result: {result}")

    except TwoCaptchaError as e:
        print(f"TwoCaptcha Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(auto_solve_captcha())
```

#### Manual solve captcha Async

```python
from TwoCaptcha import AsyncTwoCaptcha, TwoCaptchaError
import asyncio

async def manual_solve_captcha():
    """Manual solve captcha using 2captcha api."""
    client = AsyncTwoCaptcha(api_key="YOUR_API_KEY")
    try:
        task = {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": "https://2captcha.com/demo/recaptcha-v2",
            "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
        }

        create_result = await client.create_task(task)
        task_id = create_result["taskId"]
        print(f"Created task with ID: {task_id}")

        task_result = await client.get_task_result(task_id)
        print(f"Task result: {task_result}")

    except TwoCaptchaError as e:
        print(f"TwoCaptcha Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(manual_solve_captcha())
```

#### Solve captcha using async context manager

```python
from TwoCaptcha import AsyncTwoCaptcha, TwoCaptchaError
import asyncio

async def context_manager_example():
    """Context manager example."""
    async with AsyncTwoCaptcha(api_key="YOUR_API_KEY") as client:
        balance = await client.balance()
        print(f"Context manager balance: {balance}")

if __name__ == "__main__":
    asyncio.run(context_manager_example())
```

#### Async multiple captcha solver

```python
from TwoCaptcha import AsyncTwoCaptcha, TwoCaptchaError
import asyncio

async def multiple_tasks_example():
    """Multiple tasks example."""
    client = AsyncTwoCaptcha(api_key="YOUR_API_KEY")
    try:
        tasks = [
            {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": "https://2captcha.com/demo/recaptcha-v2",
                "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
            },
            {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": "https://2captcha.com/demo/recaptcha-v2",
                "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
            },
        ]

        print("Solving multiple captchas concurrently...")
        results = await asyncio.gather(
            *[client.solve_captcha(task) for task in tasks], return_exceptions=True
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i+1} failed: {result}")
            else:
                print(f"Task {i+1} solved: {result['solution']['gRecaptchaResponse'][:30]}...")

    except Exception as e:
        print(f"Error in multiple tasks: {e}")
    finally:
        await client.close()
if __name__ == "__main__":
    asyncio.run(multiple_tasks_example())
```

### Different Captcha Types

#### reCAPTCHA v2 (Proxyless)

```python
task = {
    "type": "RecaptchaV2TaskProxyless",
    "websiteURL": "https://example.com",
    "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u"
}
result = client.solve_captcha(task)
```

#### reCAPTCHA v2 (With Proxy)

```python
task = {
    "type": "RecaptchaV2Task",
    "websiteURL": "https://example.com",
    "websiteKey": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
    "proxyType": "http",
    "proxyAddress": "1.2.3.4",
    "proxyPort": "8080",
    "proxyLogin": "user",
    "proxyPassword": "pass"
}
result = client.solve_captcha(task)
```

#### reCAPTCHA v3

```python
task = {
    "type": "RecaptchaV3TaskProxyless",
    "websiteURL": "https://example.com",
    "websiteKey": "6LfB5_IbAAAAAMCtsjEHEHKqcB9iQocwwxTiihJu",
    "minScore": 0.9,
    "pageAction": "submit"
}
result = client.solve_captcha(task)
```

#### Normal Image Captcha

```python
task = {
    "type": "ImageToTextTask",
    "body": "base64_encoded_image_data"
}
result = client.solve_captcha(task)
```

#### Check Balance

```python
balance = client.balance()
print(f"Balance: ${balance['balance']}")
```

## Response Format

```json
{
  "errorId": 0,
  "status": "ready",
  "solution": {
    "gRecaptchaResponse": "03ADUVZw...UWxTAe6ncIa",
    "token": "03ADUVZw...UWxTAe6ncIa"
  },
  "cost": "0.00299",
  "ip": "1.2.3.4",
  "createTime": 1692863536,
  "endTime": 1692863556,
  "solveCount": 1
}
```

## Error Handling

```python
from twocaptcha import TwoCaptchaError

try:
    result = client.solve_captcha(task)
except TwoCaptchaError as e:
    print(f"Error: {e}")
```

## API Methods

- `client.solve_captcha(task)` - Solve captcha and wait for result
- `client.balance()` - Check account balance
- `client.create_task.create_task(task)` - Create task only
- `client.get_task_result.get_task_result(task_id)` - Get task result
- `client.get_balance.get_balance()` - Check account balance (alternative)

## Configuration

```python
client = TwoCaptcha(
    api_key="YOUR_API_KEY",
    timeout=120,        # Max wait time in seconds
    polling_interval=5  # Check interval in seconds
)
```

## Documentation

For complete API documentation and task parameters, visit [2captcha.com/api-docs](https://2captcha.com/api-docs).

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=SSujitX/twocaptcha-python&type=date&legend=top-left)](https://www.star-history.com/#SSujitX/twocaptcha-python&type=date&legend=top-left)

![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FSSujitX%2Ftwocaptcha-python&countColor=%23263759&labelStyle=upper)
