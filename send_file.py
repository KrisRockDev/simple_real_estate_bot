import os
import asyncio  # <--- Import asyncio
import aiohttp
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID_STR = os.getenv("CHAT_ID")  # строка, можно привести к int при необходимости

# It's a good idea to check if your environment variables loaded correctly
if not BOT_TOKEN:
    raise ValueError("TOKEN environment variable not set. Please check your .env file or environment.")
if not ADMIN_CHAT_ID_STR:
    raise ValueError("CHAT_ID environment variable not set. Please check your .env file or environment.")


async def send_file_to_telegram(file_path: str, caption: str = None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

    async with aiohttp.ClientSession() as session:
        # It's good practice to rename the file variable inside 'with open'
        # to avoid confusion with the 'file' parameter name if you had one,
        # or the built-in 'file' type (though 'file' is not a built-in in Py3).
        # Here, using 'f' or 'file_obj'.
        with open(file_path, 'rb') as file_obj:
            data_payload = {
                # Renamed 'data' to 'data_payload' to avoid conflict if 'data' was a kwarg for session.post
                'chat_id': ADMIN_CHAT_ID_STR,
            }
            if caption:  # Only add caption if it's not None
                data_payload['caption'] = caption

            # The 'files' dictionary way is typically for the 'requests' library.
            # For aiohttp with FormData, you add fields one by one.
            # files = {
            # 'document': file_obj
            # } # This 'files' variable is not used with FormData in this manner

            form = aiohttp.FormData()
            for key, value in data_payload.items():
                if value is not None:
                    form.add_field(key, str(value))  # Ensure value is a string for form data

            # Add the file field
            # 'file_obj' here is the opened file stream
            form.add_field('document',
                           file_obj,
                           filename=os.path.basename(file_path),
                           content_type='application/octet-stream')  # Explicitly set content type

            # Use 'data=form' for sending FormData
            async with session.post(url, data=form) as resp:
                response_text = await resp.text()  # Get text first for robust error reporting
                if resp.status != 200:
                    raise Exception(f"Failed to send file: {resp.status}, Response: {response_text}")
                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    # Handle cases where response is not JSON but status is 200 (though unlikely for Telegram API)
                    print(f"Warning: Response status is 200 but content is not JSON. Response text: {response_text}")
                    return {"ok": True, "result": "Non-JSON success response", "raw_text": response_text}


if __name__ == "__main__":
    # Ensure this file path is correct and the file exists
    file_path_to_send = r"E:\py\main\simple_real_estate_bot\downloads\317286992\kriss_real_estate_bot_20250511181047.json"

    # For testing, you might want to create a dummy file to ensure the script runs
    # test_file_path = "test_upload.txt"
    # with open(test_file_path, "w") as f:
    #     f.write("This is a test file for Telegram upload.")
    # file_path_to_send = test_file_path # Use this for testing if the original path is problematic

    caption_text = "Описание из скрипта"

    # --- Crucial Change: Use asyncio.run() ---
    try:
        if not os.path.exists(file_path_to_send):
            print(f"Error: File not found at {file_path_to_send}")
        else:
            print(f"Attempting to send file: {file_path_to_send} with caption: '{caption_text}'")
            result = asyncio.run(send_file_to_telegram(file_path_to_send, caption_text))
            print("Telegram API Response:")
            print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up the dummy test file if you created it
        # if 'test_file_path' in locals() and os.path.exists(test_file_path):
        #     os.remove(test_file_path)
        pass